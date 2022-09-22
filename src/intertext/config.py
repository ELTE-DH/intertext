import glob
import json
import argparse
from pathlib import Path
from shutil import rmtree, copytree

from vminhash import VectorizedMinHash


config = {
    'infile_glob': '',
    'banish_glob': '',
    'exclude_glob': '',
    'output': Path('output'),
    'cache_location': Path('cache'),
    'metadata': {},
    'xml_page_tag': None,
    'xml_page_attr': None,
    'batch_size': 10 ** 5,
    'write_frequency': 10 ** 5,
    'chargram_length': 4,
    'window_length': 14,
    'slide_length': 4,
    'hashband_length': 4,
    'hashband_step': 3,
    'banish_distance': 4,
    'min_sim': 50,
    'excluded_file_ids': tuple(),
    'banish_file_ids': tuple(),
    'banished_file_ids': tuple(),
    'max_file_sim': None,
    'client': '0.0.1a',
    'update_client': False,
    'strip_diacritics': False,
    'db': 'sqlite',
    'only': None,
    'update_metadata': False,
    'verbose': False,
    'compute_probabilities': False,
    'bounter_size': 64,
    'display': False,
    'only_index': None,
}


# This is the module's main function (CLI)
def parse():
    """Parse the command line arguments and initialize text processing"""
    parser = argparse.ArgumentParser(description='Discover and visualize text reuse',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--infiles', '-i', type=str, default=config['infile_glob'], dest='infile_glob',
                        help='path to a glob of text files to process', required=False)
    parser.add_argument('--banish', '-b', type=str, default=config['banish_glob'], dest='banish_glob',
                        help='path to a glob of text files to banish from matches', required=False)
    parser.add_argument('--exclude', type=str, default=config['exclude_glob'], dest='exclude_glob',
                        help='path to a glob of text files to exclude from matches', required=False)
    parser.add_argument('--metadata', '-m', type=Path, default=config['metadata'],
                        help='path to a JSON metadata file (see README)', required=False)
    parser.add_argument('--window_length', '-w', type=int, default=config['window_length'],
                        help='the length of windows when processing files (see README)', required=False)
    parser.add_argument('--hashband_length', '-hb', type=int, default=config['hashband_length'],
                        help='the number of minhash values per hashband', required=False)
    parser.add_argument('--hashband_step', '-hs', type=int, default=config['hashband_step'],
                        help='the number of minhash units to slide hashband windows', required=False)
    parser.add_argument('--chargram_length', '-cl', type=int, default=config['chargram_length'],
                        help='the number of characters per character shingle', required=False)
    parser.add_argument('--write_frequency', '-wf', type=int, default=config['write_frequency'],
                        help='the max number of write operations to store in RAM')
    parser.add_argument('--slide_length', '-l', type=int, default=config['slide_length'],
                        help='the length to slide windows when processing files (see README)', required=False)
    parser.add_argument('--banish_distance', '-bd', type=int, default=config['banish_distance'],
                        help='the graph distance to travel when banishing linked matches', required=False)
    parser.add_argument('--min_sim', '-s', type=int, default=config['min_sim'],
                        help='the minimum similarity of matches to retain)', required=False)
    parser.add_argument('--max_file_sim', '-fs', type=int, default=config['max_file_sim'],
                        help='the maximum similarity between two files such that matches are retained', required=False)
    parser.add_argument('--output', '-o', type=Path, default=config['output'], help='the output location',
                        required=False)
    parser.add_argument('--xml_page_tag', type=str, default=config['xml_page_tag'],
                        help='if specified, urls can reference content within this tag')
    parser.add_argument('--xml_page_attr', type=str, default=config['xml_page_attr'],
                        help='if specified, urls can reference content within this attr of xml_page_tag')
    parser.add_argument('--strip_diacritics', default=config['strip_diacritics'],
                        help='if specified, diacritics will be parsed from texts during processing', required=False,
                        action='store_true')
    parser.add_argument('--verbose', '-v', default=config['verbose'],
                        help='if specified, the intertext process will log more operations', required=False,
                        action='store_true')
    parser.add_argument('--only', default=config['only'],
                        help='only retain matches that include text from the specified file path', required=False)
    parser.add_argument('--update_metadata', default=config['update_metadata'],
                        help='skip all processing and only update the metadata for a plot', action='store_true')
    parser.add_argument('--compute_probabilities', default=config['compute_probabilities'],
                        help='compute the likelihood of strings in the corpus', action='store_true')
    parser.add_argument('--bounter_size', default=config['bounter_size'], help='MB allocated to bounter instance',
                        required=False)
    config.update(vars(parser.parse_args()))
    if config.get('infile_glob'):
        return config


def process_kwargs(kwargs):
    """Return a list of the infiles to be processed"""

    # check xml page kwargs
    if kwargs.get('xml_page_tag') and not kwargs.get('metadata'):
        raise Exception('--xml_page_tag requires --metadata to be provided')

    # typecheck inputs
    assert 1 <= kwargs['min_sim'] <= 100

    # get the list of infiles
    infiles = sorted(glob.glob(kwargs['infile_glob']))
    if len(infiles) == 0:
        raise Exception('No infiles could be found!')

    # identify banished files and add to infiles
    if kwargs['banish_glob']:
        banished_files = sorted(glob.glob(kwargs['banish_glob']))
        infiles += banished_files
        banished_file_set = set(banished_files)
        kwargs['banished_file_ids'] = tuple({file_idx for file_idx, file in enumerate(infiles)
                                             if file in banished_file_set})
    kwargs['infiles'] = infiles

    # identify excluded files and their file ids
    if kwargs['exclude_glob']:
        exclude_set = set(glob.glob(kwargs['exclude_glob']))
        kwargs['excluded_file_ids'] = tuple({file_idx for file_idx, file in enumerate(infiles) if file in exclude_set})

    # get the metadata (if any)
    kwargs['metadata'] = get_metadata(kwargs['infiles'], kwargs['metadata'])

    # get the focal text index number (if any) of the only file from which matches should be retained
    if kwargs.get('only') is not None:
        kwargs['only_index'] = kwargs['infiles'].index(kwargs['only'])

    kwargs['hasher'] = VectorizedMinHash(n_perm=256)

    # Copy the client to the output directory
    if kwargs['output'].exists():
        rmtree(kwargs['output'])
    # copy the `build` directory to the output directory
    copytree(Path(__file__).parent / 'client' / 'build', kwargs['output'])

    # return the processed kwargs
    return kwargs


def get_metadata(infiles, metadata):
    """if the user provided metadata, load it"""
    if metadata:
        with open(metadata) as fh:
            metadata = json.load(fh)
    else:
        metadata = {}
    for i in infiles:
        basename = Path(i).name
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
    for i in ('matches', 'scatterplots', 'indices', 'texts'):
        (output / 'api' / i).mkdir(parents=True, exist_ok=True)

    for i in ('minhashes',):
        (cache_location / i).mkdir(parents=True, exist_ok=True)

    for i in range(len(infiles)):
        (output / 'api' / 'matches' / str(i)).mkdir(parents=True, exist_ok=True)


def write_config(infiles, inp_metadata, excluded_file_ids, banished_file_ids, output, window_length, slide_length):
    # map each author and title to the files in which that string occurs and save those maps
    metadata = []
    for idx, i in enumerate(infiles):
        if i in excluded_file_ids or i in banished_file_ids:
            continue
        file_meta = inp_metadata.get(Path(i).name, {})
        metadata.append({
            'id': idx,
            'author': file_meta['author'],
            'title': file_meta['title'],
            'matches': (output / 'api' / 'matches' / f'{idx}.json').stat().st_size > 2,
        })
    with open(output / 'api' / 'config.json', 'w') as out:
        json.dump({
            'infiles': infiles,
            'metadata': metadata,
            'window_size': window_length,
            'window_slide': slide_length,
        }, out, ensure_ascii=False)
