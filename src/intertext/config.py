import argparse
import glob
import json
import shutil
from pathlib import Path

from vectorizedMinHash import VectorizedMinHash

try:
    import cupy

    CUDA_AVAILABLE = True
except:
    CUDA_AVAILABLE = False


hasher = VectorizedMinHash(n_perm=256)
source_location = Path(__file__).parent
client_location = source_location / 'client'
cache_location = Path('.') / 'cache'
row_delimiter = '\n'
field_delimiter = '-'

config = {
    'infile_glob': '',
    'banish_glob': '',
    'exclude_glob': '',
    'output': Path('output'),
    'metadata': {},
    'encoding': 'utf8',
    'xml_base_tag': None,
    'xml_remove_tags': tuple(),
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
    parser.add_argument('--encoding', '-e', type=str, default=config['encoding'], help='the encoding of infiles',
                        required=False)
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
    parser.add_argument('--xml_base_tag', type=str, default=config['xml_base_tag'],
                        help='if specified, text within this parent tag will be parsed', required=False)
    parser.add_argument('--xml_remove_tags', default=config['xml_remove_tags'],
                        help='if specified, text within these tags will be removed', nargs='+', required=False)
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
    parser.add_argument('--db', default=config['db'], help='specify sqlite to use a sqlite db', required=False)
    parser.add_argument('--only', default=config['only'],
                        help='only retain matches that include text from the specified file path', required=False)
    parser.add_argument('--update_metadata', default=config['update_metadata'],
                        help='skip all processing and only update the metadata for a plot', action='store_true')
    parser.add_argument('--compute_probabilities', default=config['compute_probabilities'],
                        help='compute the likelihood of strings in the corpus', action='store_true')
    parser.add_argument('--bounter_size', default=config['bounter_size'], help='MB allocated to bounter instance',
                        required=False)
    config.update(vars(parser.parse_args()))
    if config.get('xml_remove_tags'):
        config['xml_remove_tags'] = tuple(config['xml_remove_tags'])
    copy_client(client_location, config['output'])
    if config.get('infile_glob'):
        return config


def copy_client(client_dir, output_dir):
    """Copy the client to the output directory"""
    # copy the `build` directory to the output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    # copy the web client
    shutil.copytree(client_dir / 'build', output_dir)


def process_kwargs(**kwargs):
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
        banished_file_ids = set()
        for file_idx, file in enumerate(infiles):
            if file in banished_file_set:
                banished_file_ids.add(file_idx)
        kwargs['banished_file_ids'] = tuple(banished_file_ids)
    kwargs['infiles'] = infiles

    # identify excluded files and their file ids
    if kwargs['exclude_glob']:
        exclude_set = set(sorted(glob.glob(kwargs['exclude_glob'])))
        excluded_file_ids = set()
        for file_idx, file in enumerate(infiles):
            if file in exclude_set:
                excluded_file_ids.add(file_idx)
        kwargs['excluded_file_ids'] = tuple(excluded_file_ids)

    # get the metadata (if any)
    kwargs['metadata'] = get_metadata(**kwargs)

    # get the focal text index (if any)
    kwargs['only_index'] = get_only_index(**kwargs)

    # return the processed kwargs
    return kwargs


def get_metadata(**kwargs):
    """if the user provided metadata, store it in the kwargs"""
    metadata = json.load(open(kwargs['metadata'])) if kwargs['metadata'] else {}
    for i in kwargs['infiles']:
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


def get_only_index(**kwargs):
    """Return the index number of the only file from which matches should be retained"""
    if kwargs.get('only', None) is not None:
        return kwargs['infiles'].index(kwargs['only'])
    else:
        return None


def prepare_output_directories(**kwargs):
    """Create the folders that store output objects"""
    for i in ('matches', 'scatterplots', 'indices', 'texts'):
        (kwargs['output'] / 'api' / i).mkdir(parents=True, exist_ok=True)

    for i in ('minhashes',):
        (cache_location / i).mkdir(parents=True, exist_ok=True)

    for i in range(len(kwargs['infiles'])):
        (kwargs['output'] / 'api' / 'matches' / str(i)).mkdir(parents=True, exist_ok=True)


def write_config(**kwargs):
    # map each author and title to the files in which that string occurs and save those maps
    metadata = []
    for idx, i in enumerate(kwargs['infiles']):
        if i in kwargs.get('excluded_file_ids', []) or i in kwargs.get('banished_file_ids', []):
            continue
        file_meta = kwargs['metadata'].get(Path(i).name, {})
        metadata.append({
            'id': idx,
            'author': file_meta['author'],
            'title': file_meta['title'],
            'matches': (kwargs['output'] / 'api' / 'matches' / f'{idx}.json').stat().st_size > 2,
        })
    with open(kwargs['output'] / 'api' / 'config.json', 'w') as out:
        json.dump({
            'infiles': kwargs['infiles'],
            'metadata': metadata,
            'window_size': kwargs['window_length'],
            'window_slide': kwargs['slide_length'],
        }, out)
