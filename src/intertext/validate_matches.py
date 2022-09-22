from difflib import SequenceMatcher

from utils import get_windows, parallel_map_new


def validate_all_matches(infiles, encoding, xml_base_tag, xml_remove_tags, strip_diacritics, display, window_length,
                         slide_length, min_sim, stream_candidate_file_id_pairs_fun,
                         stream_matching_candidate_windows_fun, write_matches_fun):
    """Run match validations and yield [a_file,b_file,a_window,b_window]"""
    pairs = stream_candidate_file_id_pairs_fun()
    parallel_map_new(validate_file_matches, pairs, infiles=infiles, encoding=encoding, xml_base_tag=xml_base_tag,
                     xml_remove_tags=xml_remove_tags, strip_diacritics=strip_diacritics, display=display,
                     window_length=window_length, slide_length=slide_length, min_sim=min_sim,
                     stream_matching_candidate_windows_fun=stream_matching_candidate_windows_fun,
                     write_matches_fun=write_matches_fun)


def validate_file_matches(file_args, infiles, encoding, xml_base_tag, xml_remove_tags, strip_diacritics, display,
                          window_length, slide_length,
                          min_sim, stream_matching_candidate_windows_fun, write_matches_fun):
    """Validate the matches for a single file pair and return [a_file,b_file,a_window,b_window]"""
    file_id_a, file_id_b = file_args
    matches = []
    for file_id_a, file_id_b, window_id_a, window_id_b \
            in stream_matching_candidate_windows_fun(file_id_a, file_id_b):
        file_b_windows = list(get_windows(infiles[file_id_b], encoding, xml_base_tag, xml_remove_tags, strip_diacritics,
                                          display, window_length, slide_length))
        file_a_windows = list(get_windows(infiles[file_id_a], encoding, xml_base_tag, xml_remove_tags, strip_diacritics,
                                          display, window_length, slide_length))
        try:
            text_a = file_a_windows[window_id_a]
            text_b = file_b_windows[window_id_b]
        except (IndexError, TypeError):
            print(' * window lookup OOB')
            print(file_id_a, window_id_a, len(file_a_windows), infiles[file_id_a])
            print(file_id_b, window_id_b, len(file_b_windows), infiles[file_id_b])
            continue
        sim = SequenceMatcher(a=text_a, b=text_b, autojunk=False).ratio() * 100
        if sim >= min_sim:
            # remove matches with predominance of single character words
            a_singles = sum(int(len(i) == 1) for i in text_a.split())
            b_singles = sum(int(len(i) == 1) for i in text_b.split())
            if a_singles < (window_length * 0.75) and b_singles < (window_length * 0.75):
                matches.append([
                    file_id_a,
                    file_id_b,
                    window_id_a,
                    window_id_b,
                    int(sim),
                ])
    write_matches_fun(matches)
