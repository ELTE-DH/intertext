import json
from collections import defaultdict

from networkx import all_pairs_shortest_path_length, Graph
from networkx.algorithms.components.connected import connected_components


from utils import get_words
from minhash_files import get_all_hashbands
from format_matches import format_all_matches
from json_output import create_all_match_json
from validate_matches import validate_all_matches
from match_candidates import get_all_match_candidates
from config import parse, process_kwargs, prepare_output_directories, write_config

"""
TODO:
  * add flag to indicate if same-author matches are allowed
  * add support for CSV metadata
  * add support for xml + txt in same run
  * add MySQL db backend
  * if resuming, process output/config.json to get the files and file ids
  @PG:
  * Handling words containing punctuations only
"""


# This is main()!
def process_texts(kwargs):
    """Process the user's texts using the specified params"""

    # identify the infiles
    kwargs = process_kwargs(kwargs)

    # create the output directories where results will be stored
    prepare_output_directories(kwargs['output'], kwargs['cache_location'], kwargs['infiles'])

    # update the metadata and exit if requested
    if not kwargs.get('update_metadata'):
        # remove extant db and prepare output directories
        kwargs['db']['functions']['clear_db']()

        # create the db
        kwargs['db']['functions']['initialize_db']('hashbands')
        kwargs['db']['functions']['initialize_db']('candidates')
        kwargs['db']['functions']['initialize_db']('matches')

        # minhash files & store hashbands in db
        print(' * creating minhashes')
        get_all_hashbands(kwargs['infiles'], kwargs['cache_location'], kwargs['hasher'], kwargs['strip_diacritics'],
                          kwargs['display'], kwargs['window_length'], kwargs['slide_length'], kwargs['chargram_length'],
                          kwargs['hashband_length'], kwargs['hashband_step'],
                          kwargs['db']['functions']['write_hashbands'])

        # find all hashbands that have multiple distict file_ids
        print(' * identifying match candidates')
        get_all_match_candidates(kwargs['only_index'], kwargs['write_frequency'],
                                 kwargs['db']['functions']['write_candidates'],
                                 kwargs['db']['functions']['stream_hashbands'], kwargs['batch_size'],
                                 kwargs['verbose'])

        # validate matches from among the candidates
        print(' * validating matches')
        validate_all_matches(kwargs['infiles'], kwargs['strip_diacritics'], kwargs['display'],
                             kwargs['window_length'], kwargs['slide_length'],
                             kwargs['min_sim'],
                             kwargs['db']['functions']['stream_candidate_file_id_pairs'],
                             kwargs['db']['functions']['stream_matching_candidate_windows'],
                             kwargs['db']['functions']['write_matches'])

    # banish matches if necessary
    if kwargs['banish_glob']:
        banish_matches(kwargs['banish_glob'], kwargs['banished_file_ids'], kwargs['banish_distance'],
                       kwargs['delete_matches_fun'], kwargs['stream_file_pair_matches_fun'],
                       kwargs['stream_matching_file_id_pairs_fun'])

    # format matches into JSON for client consumption
    print(' * formatting matches')
    format_all_matches(kwargs['compute_probabilities'], kwargs['bounter_size'], kwargs['metadata'], kwargs['infiles'],
                       kwargs['strip_diacritics'], kwargs['display'], kwargs['xml_page_tag'], kwargs['xml_page_attr'],
                       kwargs['slide_length'], kwargs['window_length'], kwargs['max_file_sim'],
                       kwargs['excluded_file_ids'], kwargs['min_sim'], kwargs['output'],
                       kwargs['db']['functions']['stream_file_pair_matches'],
                       kwargs['db']['functions']['stream_matching_file_id_pairs'])

    # combine all matches into a single match object
    print(' * formatting JSON outputs')
    create_all_match_json(kwargs['output'], kwargs['compute_probabilities'])

    # write the output config file
    print(' * writing config')
    write_config(kwargs['infiles'], kwargs['metadata'], kwargs['excluded_file_ids'], kwargs['banished_file_ids'],
                 kwargs['output'], kwargs['window_length'], kwargs['slide_length'])

    # copy input texts into outputs
    print(' * preparing text reader data')
    create_reader_data(kwargs['infiles'], kwargs['strip_diacritics'], kwargs['output'])


def create_reader_data(infiles, strip_diacritics, output):
    """Create the data to be used in the reader view"""
    for idx, i in enumerate(infiles):
        words = get_words(i, strip_diacritics, True)
        with open(output / 'api' / 'texts' / f'{idx}.json', 'w') as out:
            json.dump(words, out, ensure_ascii=False)


def banish_matches(banish_glob, banished_file_ids, banish_distance, delete_matches_fun, stream_file_pair_matches_fun,
                   stream_matching_file_id_pairs_fun):
    """Delete banished matches from the db"""
    if banish_glob:
        print(' * banishing matches')
        g = Graph()
        for file_id_a, file_id_b in stream_matching_file_id_pairs_fun():
            for _, _, window_a, window_b, sim \
                    in stream_file_pair_matches_fun(file_id_a, file_id_b):
                s = f'{file_id_a}.{window_a}'
                t = f'{file_id_b}.{window_b}'
                g.add_edge(s, t)
        # create d[file_id] = [window_id, window_id] of banished windows
        banished_dict = defaultdict(set)
        distances = dict(all_pairs_shortest_path_length(g))
        for i in list(connected_components(g)):
            banished_ids = [j for j in i if int(j.split('.')[0]) in banished_file_ids]
            # search up to maximum path length between nodes so nodes linked to a banished node are removed
            for j in i:
                if any(distances[j][k] < banish_distance for k in banished_ids):
                    file_id, window_id = j.split('.')
                    banished_dict[file_id].add(window_id)
        # remove the banished file_id, window_id tuples from the db
        delete_matches_fun(banished_dict)


if __name__ == '__main__':
    configuration = parse()
    process_texts(configuration)
