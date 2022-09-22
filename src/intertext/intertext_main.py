import json
from collections import defaultdict

from bounter import bounter
from networkx import all_pairs_shortest_path_length, Graph
from networkx.algorithms.components.connected import connected_components


from utils import get_words
from minhash_files import get_all_hashbands
from format_matches import format_all_matches
from json_output import create_all_match_json
from validate_matches import validate_all_matches
from match_candidates import get_all_match_candidates
from config import parse, process_kwargs, prepare_output_directories, write_config
from db_sql import SQLCache

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
        # create the db
        cache_db = SQLCache('cache', initialize=True, db_dir=kwargs['cache_location'], verbose=kwargs['verbose'])

        # minhash files & store hashbands in db
        print(' * creating minhashes')
        get_all_hashbands(kwargs['infiles'], kwargs['cache_location'], kwargs['hasher'], kwargs['strip_diacritics'],
                          kwargs['display'], kwargs['window_length'], kwargs['slide_length'], kwargs['chargram_length'],
                          kwargs['hashband_length'], kwargs['hashband_step'],
                          cache_db)

        # find all hashbands that have multiple distict file_ids
        print(' * identifying match candidates')
        get_all_match_candidates(kwargs['only_index'], kwargs['write_frequency'], cache_db, kwargs['batch_size'],
                                 kwargs['verbose'])

        # validate matches from among the candidates
        print(' * validating matches')
        validate_all_matches(kwargs['infiles'], kwargs['strip_diacritics'], kwargs['display'], kwargs['window_length'],
                             kwargs['slide_length'], kwargs['min_sim'], cache_db)
    else:
        cache_db = SQLCache('cache', db_dir=kwargs['cache_location'], verbose=kwargs['verbose'])

    # banish matches if necessary
    if kwargs['banish_glob']:
        banish_matches(kwargs['banish_glob'], kwargs['banished_file_ids'], kwargs['banish_distance'], cache_db)

    # format matches into JSON for client consumption
    print(' * formatting matches')
    # obtain global counts of terms across corpus
    if kwargs['compute_probabilities']:
        counts = get_word_counts(kwargs['infiles'], kwargs['bounter_size'], kwargs['strip_diacritics'],
                                 kwargs['display'])
    else:
        counts = None
    format_all_matches(counts, kwargs['metadata'], kwargs['infiles'],
                       kwargs['strip_diacritics'], kwargs['display'], kwargs['xml_page_tag'], kwargs['xml_page_attr'],
                       kwargs['slide_length'], kwargs['window_length'], kwargs['max_file_sim'],
                       kwargs['excluded_file_ids'], kwargs['min_sim'], kwargs['output'],
                       cache_db)

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


def banish_matches(banish_glob, banished_file_ids, banish_distance, cache_db):
    """Delete banished matches from the db"""
    if banish_glob:
        print(' * banishing matches')
        g = Graph()
        for file_id_a, file_id_b in cache_db.stream_matching_file_id_pairs_fun():
            for _, _, window_a, window_b, sim in cache_db.stream_file_pair_matches(file_id_a, file_id_b):
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
        cache_db.delete_matches(banished_dict)


def get_word_counts(infiles, bounter_size, strip_diacritics, display):
    """Return a bounter.bounter instance if user requested string likelihoods, else None"""
    print(' * computing word counts')
    counts = bounter(size_mb=bounter_size)
    for ifnile in infiles:
        words = get_words(ifnile, strip_diacritics, display)
        counts.update(words)
    print(' * finished computing word counts')
    return counts


if __name__ == '__main__':
    configuration = parse()
    process_texts(configuration)
