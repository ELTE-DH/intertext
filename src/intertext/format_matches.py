import json
from uuid import uuid4
from pathlib import Path
from collections import defaultdict

from utils import get_words, get_windows, get_window_map, parallel_map


# Only this function is public in this file!
def format_all_matches(counts, metadata, infiles, strip_diacritics, xml_page_tag, xml_page_attr, window_length,
                       slide_length, min_sim, max_file_sim, excluded_file_ids, output, cache_db):
    """Format the match objects for each infile and store as JSON"""
    pairs = ((file_id_a, file_id_b) for file_id_a, file_id_b in cache_db.stream_matching_file_id_pairs()
             if file_id_a not in excluded_file_ids or file_id_b not in excluded_file_ids)
    parallel_map(format_file_matches, pairs, counts=counts, metadata=metadata, infiles=infiles,
                 strip_diacritics=strip_diacritics, xml_page_tag=xml_page_tag, xml_page_attr=xml_page_attr,
                 window_length=window_length, slide_length=slide_length, min_sim=min_sim, max_file_sim=max_file_sim,
                 output=output, cache_db=cache_db)


def format_file_matches(pairs, counts, metadata, infiles, strip_diacritics, xml_page_tag, xml_page_attr,
                        window_length, slide_length, min_sim, max_file_sim, output, cache_db):
    """'Format the matches for a single file pair"""
    file_id_a, file_id_b = pairs
    pair_matches = list(cache_db.stream_file_pair_matches(file_id_a, file_id_b))
    len_pair_matches = len(pair_matches)
    if len_pair_matches > 0:
        # check to see if this file pair has >= max allowed similarity
        a_windows = get_windows(infiles[file_id_a], strip_diacritics, window_length, slide_length)
        b_windows = get_windows(infiles[file_id_b], strip_diacritics, window_length, slide_length)
        if max_file_sim and ((len_pair_matches > len(a_windows) * max_file_sim) or
                             (len_pair_matches > len(b_windows) * max_file_sim)):
            print(' * file pair', file_id_a, file_id_b, 'has >= max_file_sim; skipping!')
            return
        # cluster the matches so sequential matching windows are grouped into a single match
        clusters = []
        window_a, window_b, sims = zip(*pair_matches)
        d = defaultdict(lambda: {})
        for a, b, sim in pair_matches:
            d[a][b] = sim
        for a in get_sequences(window_a):
            for b in get_sequences(window_b):
                cluster = {'a': set(), 'b': set(), 'sim': []}
                for a_i in a:
                    for b_i in b:
                        sim = d[a_i].get(b_i)
                        if sim is not None:
                            cluster['a'].add(a_i)
                            cluster['b'].add(b_i)
                            cluster['sim'].append(sim)
                if len(cluster['a']) > 0:  # len(cluster['b']) > 0 is also true as they are simultaneously filled
                    sim_avg = int(sum(cluster['sim']) / len(cluster['sim']))
                    if sim_avg >= min_sim:
                        clusters.append({'a': sorted(cluster['a']),
                                         'b': sorted(cluster['b']),
                                         'sim': sim_avg,
                                         })
        # format the matches, then save into both file_id_a and file_id_b directories
        formatted = format_matches(file_id_a, file_id_b, clusters, counts, metadata,
                                   Path(infiles[file_id_a]), Path(infiles[file_id_b]),
                                   strip_diacritics, xml_page_tag, xml_page_attr, window_length, slide_length)
        for curr_file_id in (file_id_a, file_id_b):  # write twice per match
            out_filename = output / 'api' / 'matches' / str(curr_file_id) / f'{file_id_a}-{file_id_b}.json'
            with open(out_filename, 'w', encoding='UTF-8') as out:
                json.dump(formatted, out, ensure_ascii=False)


def format_matches(file_id_a, file_id_b, clusters, counts, metadata, path_a, path_b, strip_diacritics, xml_page_tag,
                   xml_page_attr, window_length, slide_length):
    """Given integer file ids and clusters [{a: [], b: [], sim: []}] format matches for display"""
    bn_a = path_a.name
    bn_b = path_b.name
    a_meta = metadata[bn_a]
    b_meta = metadata[bn_b]
    # set file id a to the previously published file (if relevant)
    if a_meta.get('year') and b_meta.get('year') and b_meta.get('year') < a_meta.get('year'):
        file_id_a, file_id_b, clusters = file_id_b, file_id_a, [{'a': c1['b'], 'b': c1['a'], 'sim': c1['sim']}
                                                                for c1 in clusters]
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
        a_strings = get_match_strings(a_words, c['a'], window_length, slide_length)
        b_strings = get_match_strings(b_words, c['b'], window_length, slide_length)
        if counts:
            # return the maximum probability of s1 and s2 as a float
            probs_a = sum(counts[w] / counts.total() for w in a_strings['match'].split())
            probs_b = sum(counts[w] / counts.total() for w in b_strings['match'].split())
            prob = round(max(probs_a, probs_b), 3) * 1000
        else:
            prob = -1
        formatted.append({'_id': str(uuid4()),
                          'similarity': c['sim'],
                          'probability': prob,
                          'source_file_id': file_id_a,
                          'target_file_id': file_id_b,
                          'source_segment_ids': c['a'],
                          'target_segment_ids': c['b'],
                          'source_filename': bn_a,
                          'target_filename': bn_b,
                          # these are Paths which can not be serialized to JSON without conversion
                          'source_file_path': str(path_a),
                          'target_file_path': str(path_a),
                          'source_prematch': a_strings['prematch'],
                          'target_prematch': b_strings['prematch'],
                          'source_match': a_strings['match'],
                          'target_match': b_strings['match'],
                          'source_postmatch': a_strings['postmatch'],
                          'target_postmatch': b_strings['postmatch'],
                          'source_year': a_meta.get('year', ''),
                          'target_year': b_meta.get('year', ''),
                          'source_author': a_meta['author'],
                          'target_author': b_meta['author'],
                          'source_title': a_meta['title'],
                          'target_title': b_meta['title'],
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


def get_match_strings(words, window_ids, window_length, slide_length):
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
