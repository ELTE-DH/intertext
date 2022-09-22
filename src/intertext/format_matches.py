import json
from uuid import uuid4
from pathlib import Path
from copy import deepcopy
from collections import defaultdict

from utils import get_words, get_windows, get_window_map, parallel_map


# Only this function is public in this file!
def format_all_matches(counts, metadata, infiles, strip_diacritics, display, xml_page_tag,
                       xml_page_attr, slide_length, window_length, max_file_sim, excluded_file_ids, min_sim,
                       output, cache_db):
    """Format the match objects for each infile and store as JSON"""
    pairs = cache_db.stream_matching_file_id_pairs()
    parallel_map(format_file_matches, pairs, counts=counts, metadata=metadata, infiles=infiles,
                 strip_diacritics=strip_diacritics, display=display, xml_page_tag=xml_page_tag,
                 xml_page_attr=xml_page_attr, slide_length=slide_length, window_length=window_length,
                 max_file_sim=max_file_sim, excluded_file_ids=excluded_file_ids, min_sim=min_sim, output=output,
                 cache_db=cache_db)


def format_file_matches(file_args, counts, metadata, infiles, strip_diacritics, display, xml_page_tag, xml_page_attr,
                        slide_length, window_length, max_file_sim, excluded_file_ids, min_sim, output, cache_db):
    """'Format the matches for a single file pair"""
    file_id_a, file_id_b = file_args
    if excluded_file_ids and (file_id_a in excluded_file_ids or file_id_b in excluded_file_ids):
        return
    pair_matches = list(cache_db.stream_file_pair_matches(file_id_a, file_id_b))
    if pair_matches:
        # check to see if this file pair has >= max allowed similarity
        a_windows = get_windows(infiles[file_id_a], strip_diacritics, display, window_length, slide_length)
        b_windows = get_windows(infiles[file_id_b], strip_diacritics, display, window_length, slide_length)
        if max_file_sim and ((len(pair_matches) > len(a_windows) * max_file_sim) or
                             (len(pair_matches) > len(b_windows) * max_file_sim)):
            print(' * file pair', *file_args, 'has >= max_file_sim; skipping!')
            return
        # cluster the matches so sequential matching windows are grouped into a single match
        clusters = []
        _, _, window_a, window_b, sims = zip(*pair_matches)
        d = defaultdict(lambda: {})
        for a, b, sim in zip(window_a, window_b, sims):
            d[a][b] = sim
        for a in get_sequences(window_a):
            for b in get_sequences(window_b):
                cluster = {'a': set(), 'b': set(), 'sim': []}
                for a_i in a:
                    for b_i in b:
                        if d[a_i].get(b_i):
                            cluster['a'].add(a_i)
                            cluster['b'].add(b_i)
                            cluster['sim'].append(d[a_i][b_i])
                if cluster['a'] and cluster['b']:
                    sim = int(sum(cluster['sim']) / len(cluster['sim']))
                    if sim >= min_sim:
                        clusters.append({
                            'a': sorted(cluster['a']),
                            'b': sorted(cluster['b']),
                            'sim': sim,
                        })
        # format the matches, then save into both file_id_a and file_id_b directories
        formatted = format_matches(file_id_a, file_id_b, clusters, counts, metadata,
                                   Path(infiles[file_id_a]), Path(infiles[file_id_b]),
                                   strip_diacritics, xml_page_tag, xml_page_attr, slide_length, window_length)
        for i in (file_id_a, file_id_b):
            out_dir = output / 'api' / 'matches' / str(i)
            with open(out_dir / f'{file_id_a}-{file_id_b}.json', 'w') as out:
                json.dump(formatted, out, ensure_ascii=False)


def format_matches(file_id_a, file_id_b, clusters, counts, metadata, path_a, path_b, strip_diacritics, xml_page_tag,
                   xml_page_attr, slide_length, window_length):
    """Given integer file ids and clusters [{a: [], b: [], sim: []}] format matches for display"""
    bn_a = path_a.name
    bn_b = path_b.name
    a_meta = metadata.get(bn_a, {})
    b_meta = metadata.get(bn_b, {})
    file_id_a, file_id_b, clusters = order_match_pair(file_id_a, file_id_b, clusters, a_meta, b_meta)
    # format the matches
    a_words = get_words(path_a, strip_diacritics, True)
    b_words = get_words(path_b, strip_diacritics, True)
    formatted = []
    # fetch a mapping from window id to $PAGE elements if necessary
    a_windows_to_page = None
    b_windows_to_page = None
    if xml_page_tag:
        try:
            a_windows_to_page = get_window_map(path_a, xml_page_tag, xml_page_attr, slide_length)
            b_windows_to_page = get_window_map(path_b, xml_page_tag, xml_page_attr, slide_length)
        except:
            print(' * unable to retrieve mapping from window to page id')
    # each member c in clusters is a dictionary {a: b: } where values contain the match windows
    for c in clusters:
        a_strings = get_match_strings(a_words, c['a'], slide_length, window_length)
        b_strings = get_match_strings(b_words, c['b'], slide_length, window_length)
        formatted.append({
            '_id': str(uuid4()),
            'similarity': c['sim'],
            'probability': get_string_prob(a_strings['match'], b_strings['match'], counts) if counts else -1,
            'source_file_id': int(file_id_a),
            'target_file_id': int(file_id_b),
            'source_segment_ids': c['a'],
            'target_segment_ids': c['b'],
            'source_filename': bn_a,
            'target_filename': bn_b,
            'source_file_path': str(path_a),
            'target_file_path': str(path_a),
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
            'source_url': get_url(a_meta, a_windows_to_page, c['a'], xml_page_tag),
            'target_url': get_url(b_meta, b_windows_to_page, c['b'], xml_page_tag),
        })
    return formatted


def get_url(meta, windows_to_page, windows, xml_page_tag):
    """Return the url to the first of the current windows"""
    ret = meta.get('url', '')
    if xml_page_tag:
        ret = ret.replace('$PAGE_ID', windows_to_page.get(windows[0], ''))
    return ret


def order_match_pair(file_id_a, file_id_b, clusters, a_meta, b_meta):
    """Set file id a to the previously published file (if relevant)"""
    if a_meta.get('year') and b_meta.get('year') and b_meta.get('year') < a_meta.get('year'):
        return [file_id_b, file_id_a, [{'a': c['b'], 'b': c['a'], 'sim': c['sim']} for c in deepcopy(clusters)]]
    else:
        return [file_id_a, file_id_b, clusters]


def get_match_strings(words, window_ids, slide_length, window_length):
    """Given a list of words and window ids, format prematch, match, and postmatch strings for a match"""
    start = min(window_ids) * slide_length
    end = max(window_ids) * slide_length + window_length
    return {
        'prematch': ' '.join(words[max(0, start - window_length):start]).lstrip('<br/>'),
        'match': ' '.join(words[start:end]),
        'postmatch': ' '.join(words[end:end + window_length]).rstrip('<br/>'),
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


def get_string_prob(a, b, counts):
    """Return the maximum probability of s1 and s2 as a float"""
    probs_a = sum(counts[w] / counts.total() for w in a.split())
    probs_b = sum(counts[w] / counts.total() for w in b.split())
    return round(max(probs_a, probs_b), 3) * 1000
