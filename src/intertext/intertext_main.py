import json
from pathlib import Path
from collections import defaultdict

from networkx import all_pairs_shortest_path_length, Graph
from networkx.algorithms.components.connected import connected_components

from utils import get_words, get_cacheable
from minhash_files import get_all_hashbands
from format_matches import format_all_matches
from json_output import create_all_match_json
from validate_matches import validate_all_matches
from match_candidates import get_all_match_candidates
from config import parse, process_kwargs, prepare_output_directories, write_config
from db import clear_db, initialize_db, delete_matches, stream_matching_file_id_pairs, stream_file_pair_matches

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
    prepare_output_directories(kwargs)

    # update the metadata and exit if requested
    if not kwargs.get('update_metadata'):
        # remove extant db and prepare output directories
        clear_db()

        # create the db
        initialize_db('hashbands', **kwargs)
        initialize_db('candidates', **kwargs)
        initialize_db('matches', **kwargs)

        # minhash files & store hashbands in db
        print(' * creating minhashes')
        get_all_hashbands(kwargs)

        # find all hashbands that have multiple distict file_ids
        print(' * identifying match candidates')
        get_all_match_candidates(kwargs)

        # validate matches from among the candidates
        print(' * validating matches')
        validate_all_matches(kwargs)

    # banish matches if necessary
    if kwargs['banish_glob']:
        banish_matches(kwargs)

    # format matches into JSON for client consumption
    print(' * formatting matches')
    format_all_matches(kwargs)

    # combine all matches into a single match object
    print(' * formatting JSON outputs')
    create_all_match_json(kwargs)

    # write the output config file
    print(' * writing config')
    write_config(kwargs)

    # copy input texts into outputs
    print(' * preparing text reader data')
    create_reader_data(kwargs)


def create_reader_data(kwargs):
    """Create the data to be used in the reader view"""
    for idx, i in enumerate(kwargs['infiles']):
        words = get_words(i, **get_cacheable(kwargs, {'display': True}))
        with open(Path(kwargs['output']) / 'api' / 'texts' / f'{idx}.json', 'w') as out:
            json.dump(words, out, ensure_ascii=False)


def banish_matches(kwargs):
    """Delete banished matches from the db"""
    if kwargs['banish_glob']:
        print(' * banishing matches')
        g = Graph()
        for file_id_a, file_id_b in stream_matching_file_id_pairs(kwargs):
            for _, _, window_a, window_b, sim in stream_file_pair_matches(file_id_a, file_id_b, **kwargs):
                s = f'{file_id_a}.{window_a}'
                t = f'{file_id_b}.{window_b}'
                g.add_edge(s, t)
        # create d[file_id] = [window_id, window_id] of banished windows
        banished_dict = defaultdict(set)
        distances = dict(all_pairs_shortest_path_length(g))
        for i in list(connected_components(g)):
            banished_ids = [j for j in i if int(j.split('.')[0]) in kwargs['banished_file_ids']]
            # search up to maximum path length between nodes so nodes linked to a banished node are removed
            for j in i:
                if any(distances[j][k] < kwargs['banish_distance'] for k in banished_ids):
                    file_id, window_id = j.split('.')
                    banished_dict[file_id].add(window_id)
        # remove the banished file_id, window_id tuples from the db
        delete_matches(banished_dict, **kwargs)


if __name__ == '__main__':
    configuration = parse()
    process_texts(configuration)
