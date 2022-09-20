import functools
import json
import multiprocessing
import uuid
from pathlib import Path
from copy import deepcopy
from collections import defaultdict
from difflib import SequenceMatcher


from bounter import bounter

from utils import get_words, get_windows, get_window_map, get_cacheable
from db import stream_matching_file_id_pairs, stream_file_pair_matches


def format_all_matches(**kwargs):
    """Format the match objects for each infile and store as JSON"""
    pool = multiprocessing.Pool()
    pairs = stream_matching_file_id_pairs(**kwargs)
    # obtain global counts of terms across corpus
    counts = get_word_counts(**kwargs)
    f = functools.partial(format_file_matches, counts, **kwargs)
    for _ in pool.map(f, pairs):
        pass
    pool.close()
    pool.join()


def format_file_matches(counts, file_args, **kwargs):
    """'Format the matches for a single file pair"""
    file_id_a, file_id_b = file_args
    if kwargs.get('excluded_file_ids'):
        if file_id_a in kwargs['excluded_file_ids'] or file_id_b in kwargs['excluded_file_ids']:
            return
    pair_matches = list(stream_file_pair_matches(file_id_a, file_id_b, **kwargs))
    if not pair_matches:
        return
    # check to see if this file pair has >= max allowed similarity
    a_windows = get_windows(kwargs['infiles'][file_id_a], **get_cacheable(kwargs))
    b_windows = get_windows(kwargs['infiles'][file_id_b], **get_cacheable(kwargs))
    if kwargs['max_file_sim']:
        if (len(pair_matches) > len(a_windows) * kwargs['max_file_sim']) or \
                (len(pair_matches) > len(b_windows) * kwargs['max_file_sim']):
            print(' * file pair', *file_args, 'has >= max_file_sim; skipping!')
            return []
    # cluster the matches so sequential matching windows are grouped into a single match
    clusters = []
    _, _, window_a, window_b, sims = zip(*pair_matches)
    d = defaultdict(lambda: defaultdict())
    for a, b, sim in zip(window_a, window_b, sims):
        d[a][b] = sim
    for a in get_sequences(window_a):
        for b in get_sequences(window_b):
            cluster = {'a': set(), 'b': set(), 'sim': []}
            for a_i in a:
                for b_i in b:
                    if d.get(a_i, {}).get(b_i):
                        cluster['a'].add(a_i)
                        cluster['b'].add(b_i)
                        cluster['sim'].append(d[a_i][b_i])
            if cluster['a'] and cluster['b']:
                sim = int(sum(cluster['sim']) / len(cluster['sim']))
                if sim < kwargs['min_sim']:
                    continue
                clusters.append({
                    'a': sorted(cluster['a']),
                    'b': sorted(cluster['b']),
                    'sim': sim,
                })
    # format the matches, then save into both file_id_a and file_id_b directories
    formatted = format_matches(file_id_a, file_id_b, clusters, counts, **kwargs)
    for i in (file_id_a, file_id_b):
        out_dir = kwargs['output'] / 'api' / 'matches' / str(i)
        with open(out_dir / f'{file_id_a}-{file_id_b}.json', 'w') as out:
            json.dump(formatted, out)


def format_matches(file_id_a, file_id_b, clusters, counts, **kwargs):
    """Given integer file ids and clusters [{a: [], b: [], sim: []}] format matches for display"""
    file_id_a, file_id_b, clusters = order_match_pair(file_id_a, file_id_b, clusters, **kwargs)
    path_a = Path(kwargs['infiles'][file_id_a])
    path_b = Path(kwargs['infiles'][file_id_b])
    bn_a = path_a.name
    bn_b = path_b.name
    a_meta = kwargs.get('metadata', {}).get(bn_a, {})
    b_meta = kwargs.get('metadata', {}).get(bn_b, {})
    # format the matches
    a_words = get_words(path_a, **get_cacheable(kwargs, {'display': True}))
    b_words = get_words(path_b, **get_cacheable(kwargs, {'display': True}))
    formatted = []
    # fetch a mapping from window id to $PAGE elements if necessary
    a_windows_to_page = None
    b_windows_to_page = None
    try:
        a_windows_to_page = get_window_map(path_a, **get_cacheable(kwargs))
        b_windows_to_page = get_window_map(path_b, **get_cacheable(kwargs))
    except:
        print(' * unable to retrieve mapping from window to page id')
    # each member c in clusters is a dictionary {a: b: } where values contain the match windows
    for c in clusters:
        a_strings = get_match_strings(a_words, c['a'], **get_cacheable(kwargs))
        b_strings = get_match_strings(b_words, c['b'], **get_cacheable(kwargs))
        formatted.append({
            '_id': str(uuid.uuid4()),
            'similarity': c['sim'],
            'probability': get_string_prob(a_strings['match'], b_strings['match'], counts),
            'source_file_id': int(file_id_a),
            'target_file_id': int(file_id_b),
            'source_segment_ids': c['a'],
            'target_segment_ids': c['b'],
            'source_filename': bn_a,
            'target_filename': bn_b,
            'source_file_path': kwargs['infiles'][file_id_a],
            'target_file_path': kwargs['infiles'][file_id_b],
            'source_prematch': a_strings['prematch'],
            'target_prematch': b_strings['prematch'],
            'source_match': a_strings['match'],
            'target_match': b_strings['match'],
            'source_postmatch': a_strings['postmatch'],
            'target_postmatch': b_strings['postmatch'],
            'source_year': str(a_meta.get('year', '')),
            'target_year': str(b_meta.get('year', '')),
            'source_author': a_meta.get('author', ''),
            'target_author': b_meta.get('author', ''),
            'source_title': a_meta.get('title', ''),
            'target_title': b_meta.get('title', ''),
            'source_url': get_url(a_meta, a_windows_to_page, c['a'], **kwargs),
            'target_url': get_url(b_meta, b_windows_to_page, c['b'], **kwargs),
        })
    return formatted


def get_url(meta, windows_to_page, windows, **kwargs):
    """Return the url to the first of the current windows"""
    if not kwargs.get('xml_page_tag'):
        return meta.get('url', '')
    return meta.get('url', '').replace('$PAGE_ID', windows_to_page.get(windows[0], ''))


def order_match_pair(file_id_a, file_id_b, clusters, **kwargs):
    """Set file id a to the previously published file (if relevant)"""
    a_meta = kwargs.get('metadata', {}).get(Path(kwargs['infiles'][file_id_a]).name, {})
    b_meta = kwargs.get('metadata', {}).get(Path(kwargs['infiles'][file_id_b]).name, {})
    if a_meta and \
            b_meta and \
            a_meta.get('year') and \
            b_meta.get('year') and \
            b_meta.get('year') < a_meta.get('year'):
        return [
            file_id_b,
            file_id_a,
            [{'a': c['b'], 'b': c['a'], 'sim': c['sim']} for c in deepcopy(clusters)]
        ]
    return [
        file_id_a,
        file_id_b,
        clusters,
    ]


def get_match_strings(words, window_ids, **kwargs):
    """Given a list of words and window ids, format prematch, match, and postmatch strings for a match"""
    start = min(window_ids) * kwargs['slide_length']
    end = max(window_ids) * kwargs['slide_length'] + kwargs['window_length']
    return {
        'prematch': ' '.join(words[max(0, start - kwargs['window_length']):start]).lstrip('<br/>'),
        'match': ' '.join(words[start:end]),
        'postmatch': ' '.join(words[end:end + kwargs['window_length']]).rstrip('<br/>'),
    }


def get_sequences(arg):
    """Given list of ints `l`, return [[integer sequence in l], [integer sequence in l]]"""
    sequences = []
    for i in sorted(set(arg)):
        # check if each is 1 more than the last, as segment ids increment by 1
        if not sequences or sequences[-1][-1] != i - 1:
            sequences.append([])
        sequences[-1].append(i)
    return sequences


def get_word_counts(**kwargs):
    """Return a bounter.bounter instance if user requested string likelihoods, else None"""
    if not kwargs.get('compute_probabilities'):
        return None
    print(' * computing word counts')
    counts = bounter(size_mb=int(kwargs.get('bounter_size')))
    for i in kwargs['infiles']:
        words = get_words(i, **get_cacheable(kwargs))
        counts.update(words)
    print(' * finished computing word counts')
    return counts


def get_string_sim(a, b, **_):
    """Return the similarity between strings a and b"""
    return SequenceMatcher(a=a, b=b, autojunk=False).ratio() * 100


def get_string_prob(a, b, counts):
    """Return the maximum probability of s1 and s2 as a float"""
    if not counts:
        return -1
    probs_a = sum([counts[w] / counts.total() for w in a.split()])
    probs_b = sum([counts[w] / counts.total() for w in b.split()])
    return round(max([probs_a, probs_b]), 3) * 1000
