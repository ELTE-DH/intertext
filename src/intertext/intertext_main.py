import json
from pathlib import Path
from shutil import rmtree, copytree

from bounter import bounter
from networkx import all_pairs_shortest_path_length, Graph
from networkx.algorithms.components.connected import connected_components

from utils import get_words
from db_sql import SQLCache
from config import parse, process_kwargs
from minhash_files import get_all_hashbands
from format_matches import format_all_matches
from json_output import create_all_match_json
from validate_matches import validate_all_matches
from match_candidates import get_all_match_candidates


"""
TODO:
  * add flag to indicate if same-author matches are allowed
  * if resuming, process output/config.json to get the files and file ids
  @PG:
  * Handling words containing punctuations only
"""


# This is main()!
def process_texts(kwargs):
    """Process the user's texts using the specified params"""

    # identify the infiles
    kwargs = process_kwargs(kwargs)

    # get the metadata (if any)
    kwargs['metadata'] = get_metadata(kwargs['infiles'], kwargs['metadata'])

    # create the output directories where results will be stored
    prepare_output_directories(kwargs['output'], kwargs['cache_location'], kwargs['infiles'])

    # update the metadata and exit if requested
    if not kwargs.get('update_metadata'):
        # create the db
        cache_db = SQLCache('cache', initialize=True, db_dir=kwargs['cache_location'], verbose=kwargs['verbose'])

        # minhash files & store hashbands in db
        print(' * creating minhashes')
        get_all_hashbands(kwargs['infiles'], kwargs['cache_location'], kwargs['strip_diacritics'],
                          kwargs['window_length'], kwargs['slide_length'], kwargs['chargram_length'],
                          kwargs['hashband_length'], kwargs['hashband_step'],
                          cache_db)

        # find all hashbands that have multiple distict file_ids
        print(' * identifying match candidates')
        get_all_match_candidates(kwargs['only_index'], kwargs['write_frequency'], cache_db, kwargs['batch_size'],
                                 kwargs['verbose'])

        # validate matches from among the candidates
        print(' * validating matches')
        validate_all_matches(kwargs['infiles'], kwargs['strip_diacritics'], kwargs['window_length'],
                             kwargs['slide_length'], kwargs['min_sim'], cache_db)
    else:
        cache_db = SQLCache('cache', db_dir=kwargs['cache_location'], verbose=kwargs['verbose'])

    # banish matches if necessary
    if kwargs['banished_file_ids']:
        banish_matches(kwargs['banished_file_ids'], kwargs['banish_distance'], cache_db)

    # format matches into JSON for client consumption
    print(' * formatting matches')
    # obtain global counts of terms across corpus
    counts = None
    if kwargs['compute_probabilities']:
        counts = get_word_counts(kwargs['infiles'], kwargs['bounter_size'], kwargs['strip_diacritics'])

    format_all_matches(counts, kwargs['metadata'], kwargs['infiles'],
                       kwargs['strip_diacritics'], kwargs['xml_page_tag'], kwargs['xml_page_attr'],
                       kwargs['window_length'], kwargs['slide_length'], kwargs['max_file_sim'],
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


def get_metadata(infiles, metadata):
    """if the user provided metadata, load it"""
    for infile in infiles:
        basename = infile.name
        if basename not in metadata:
            metadata[basename] = {}
        if not metadata[basename].get('author'):
            metadata[basename]['author'] = 'Unknown'
        if not metadata[basename].get('title'):
            metadata[basename]['title'] = basename
        for j in metadata[basename]:
            if isinstance(metadata[basename][j], str):
                metadata[basename][j] = metadata[basename][j].strip()

    return metadata


def prepare_output_directories(output, cache_location, infiles):
    """Create the folders that store output objects"""
    # Copy the client to the output directory
    if output.exists():
        rmtree(output)
    # copy the `build` directory to the output directory
    copytree(Path(__file__).parent / 'client' / 'build', output)

    for i in ('matches', 'scatterplots', 'indices', 'texts'):
        (output / 'api' / i).mkdir(parents=True, exist_ok=True)

    for i in ('minhashes',):
        (cache_location / i).mkdir(parents=True, exist_ok=True)

    for i in range(len(infiles)):
        (output / 'api' / 'matches' / str(i)).mkdir(parents=True, exist_ok=True)


def banish_matches(banished_file_ids, banish_distance, cache_db):
    """Delete banished matches from the db"""
    print(' * banishing matches')
    g = Graph()
    for file_id_a, file_id_b, window_a, window_b, sim in cache_db.stream_all_pair_matches():
        g.add_edge((file_id_a, window_a), (file_id_b, window_b))  # edges between file_id and windows pairs
    # create list of banished windows to be deleted
    deletes = []
    distances = dict(all_pairs_shortest_path_length(g))
    for graph_component in list(connected_components(g)):
        banished_nodes = [graph_node for graph_node in graph_component if graph_node[0] in banished_file_ids]
        # search up to maximum path length between nodes so nodes linked to a banished node are removed
        for graph_node in graph_component:
            if any(distances[graph_node][banished_node] < banish_distance for banished_node in banished_nodes):
                deletes.append((graph_node[0], graph_node[1], graph_node[0], graph_node[1]))
    # remove the banished file_id, window_id tuples (which matches start or end with) from the db
    cache_db.delete_matches(deletes)


def get_word_counts(infiles, bounter_size, strip_diacritics):
    """Return a bounter.bounter instance if user requested string likelihoods"""
    print(' * computing word counts')
    counts = bounter(size_mb=bounter_size)
    for ifnile in infiles:
        words = get_words(ifnile, strip_diacritics, False)
        counts.update(words)
    print(' * finished computing word counts')
    return counts


def write_config(infiles, inp_metadata, excluded_file_ids, banished_file_ids, output, window_length, slide_length):
    # map each author and title to the files in which that string occurs and save those maps
    metadata = []
    for idx, infile in enumerate(infiles):
        if infile not in excluded_file_ids and infile not in banished_file_ids:
            file_meta = inp_metadata[infile.name]
            metadata.append({'id': idx,
                             'author': file_meta['author'],
                             'title': file_meta['title'],
                             # we need the results here
                             'matches': (output / 'api' / 'matches' / f'{idx}.json').stat().st_size > 2,
                             })
    with open(output / 'api' / 'config.json', 'w', encoding='UTF-8') as out:
        json.dump({'infiles': [str(infile) for infile in infiles],
                   'metadata': metadata,
                   'window_size': window_length,
                   'window_slide': slide_length,
                   }, out, ensure_ascii=False)


def create_reader_data(infiles, strip_diacritics, output):
    """Create the data to be used in the reader view"""
    for idx, infile in enumerate(infiles):
        words = get_words(infile, strip_diacritics, True)
        with open(output / 'api' / 'texts' / f'{idx}.json', 'w', encoding='UTF-8') as out:
            json.dump(words, out, ensure_ascii=False)


if __name__ == '__main__':
    configuration = parse()
    process_texts(configuration)
