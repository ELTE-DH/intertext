import json
import glob
import argparse
from pathlib import Path


config = {
    'infile_glob': '',
    'banish_glob': '',
    'exclude_glob': '',
    'excluded_file_ids': tuple(),
    'banished_file_ids': tuple(),
    'metadata': '',  # file path will be turned to JSON loaded data structure
    'only_index': None,
    'output': Path('output'),
    'cache_location': Path('cache'),
    'xml_page_tag': None,
    'xml_page_attr': None,
    'chargram_length': 4,  # TODO 1,2,4 byte length Non-CLI config to be
    'bounter_size': 64,  # TODO Non-CLI config to be
    'window_length': 14,
    'slide_length': 4,
    'hashband_length': 4,
    'hashband_step': 3,
    'banish_distance': 4,
    'min_sim': 50,
    'max_file_sim': None,
    'strip_diacritics': False,
    'update_metadata': False,
    'verbose': False,
    'compute_probabilities': False,
}


def check_min_sim(string):
    try:
        val = int(string)
    except ValueError:
        val = -1  # Intentionally bad value

    if 1 > val or val > 100:
        raise ValueError(f'{string} should be 1 <= int <= 100!')

    return val


def non_empty_glob(string):
    # get the list of files
    infiles = [Path(file_name) for file_name in sorted(glob.glob(string))]
    if len(infiles) == 0:
        raise ValueError('No files could be found!')
    return infiles


def load_metadata_file(string):
    metadata_path = Path(string)
    if len(string) == 0:
        metadata = {}
    elif not metadata_path.is_file() or not metadata_path.exists():
        raise ValueError('Metadata file should be an existing JSON file!')
    else:
        with open(string, encoding='UTF-8') as fh:
            metadata = json.load(fh)

    return metadata


# This is the module's main function (CLI)
def parse():
    """Parse the command line arguments and initialize text processing"""
    parser = argparse.ArgumentParser(description='Discover and visualize text reuse',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--infiles', '-i', type=non_empty_glob, default=config['infile_glob'],
                        help='path to a glob of text files to process', required=True)
    parser.add_argument('--banish', '-b', type=str, default=config['banish_glob'], dest='banish_glob',
                        help='path to a glob of text files to banish from matches', required=False)
    parser.add_argument('--exclude', type=str, default=config['exclude_glob'], dest='exclude_glob',
                        help='path to a glob of text files to exclude from matches', required=False)
    parser.add_argument('--metadata', '-m', type=load_metadata_file, default=config['metadata'],
                        help='path to a JSON metadata file (see README)', required=False)
    parser.add_argument('--window_length', '-w', type=int, default=config['window_length'],
                        help='the length of windows in words when processing files', required=False)
    parser.add_argument('--slide_length', '-l', type=int, default=config['slide_length'],
                        help='the length to slide windows when processing files', required=False)
    parser.add_argument('--hashband_length', '-hb', type=int, default=config['hashband_length'],
                        help='the number of minhash values per hashband', required=False)
    parser.add_argument('--hashband_step', '-hs', type=int, default=config['hashband_step'],
                        help='the number of minhash units to slide hashband windows', required=False)
    parser.add_argument('--chargram_length', '-cl', type=int, default=config['chargram_length'],
                        help='the number of characters per character shingle', required=False)
    parser.add_argument('--banish_distance', '-bd', type=int, default=config['banish_distance'],
                        help='the graph distance to travel when banishing linked matches', required=False)
    parser.add_argument('--min_sim', '-s', type=check_min_sim, default=config['min_sim'],
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
                        help='if specified, diacritics will be stripped from texts during processing', required=False,
                        action='store_true')
    parser.add_argument('--verbose', '-v', default=config['verbose'],
                        help='if specified, the intertext process will log more operations', required=False,
                        action='store_true')
    parser.add_argument('--only', default=None, dest='only_index',
                        help='only retain matches that include text from the specified file path', required=False)
    parser.add_argument('--update_metadata', default=config['update_metadata'],
                        help='skip all processing and only update the metadata for a plot', action='store_true')
    parser.add_argument('--compute_probabilities', default=config['compute_probabilities'],
                        help='compute the likelihood of strings in the corpus', action='store_true')
    parser.add_argument('--bounter_size', default=config['bounter_size'], help='MB allocated to bounter instance',
                        required=False)

    config.update(vars(parser.parse_args()))

    return config


def process_kwargs(kwargs):
    """Return a list of the infiles to be processed"""

    # check xml page kwargs
    if kwargs.get('xml_page_tag') and not kwargs.get('metadata'):
        raise argparse.ArgumentTypeError('--xml_page_tag requires --metadata to be provided')

    # identify banished files and add to infiles
    if len(kwargs['banish_glob']) > 0:
        banished_files = non_empty_glob(kwargs['banish_glob'])
        kwargs['infiles'] += banished_files
        banished_file_set = set(banished_files)
        kwargs['banished_file_ids'] = tuple({file_idx for file_idx, file_name in enumerate(kwargs['infiles'])
                                             if file_name in banished_file_set})

    # identify excluded files and their file ids
    if len(kwargs['exclude_glob']) > 0:
        exclude_set = set(non_empty_glob(kwargs['exclude_glob']))
        kwargs['excluded_file_ids'] = tuple({file_idx for file_idx, file_name in enumerate(kwargs['infiles'])
                                             if file_name in exclude_set})

    # get the focal text index number (if any) of the only file from which matches should be retained
    if kwargs.get('only_index') is not None:
        kwargs['only_index'] = kwargs['infiles'].index(kwargs['only_index'])

    # return the processed kwargs
    return kwargs
