from utils import get_windows, parallel_map
from match_ratio_sandbox import ratio_max_mach, ratio_max_mach_built_in


# Only this function is public in this file!
def validate_all_matches(infiles, strip_diacritics, window_length, slide_length, min_sim, cache_db, match_algo):
    """Run match validations and yield [a_file,b_file,a_window,b_window]"""
    pairs = [(infiles[file_id_a], infiles[file_id_b], file_id_a, file_id_b)
             for file_id_a, file_id_b in cache_db.stream_candidate_file_id_pairs()]
    parallel_map(validate_file_matches, pairs, strip_diacritics=strip_diacritics, min_sim=min_sim, cache_db=cache_db,
                 window_length=window_length, slide_length=slide_length, match_algo=match_algo)


def validate_file_matches(pairs, strip_diacritics, min_sim, cache_db, window_length, slide_length, match_algo):
    """Validate the matches for a single file pair and return [a_file,b_file,a_window,b_window]"""
    file_path_a, file_path_b, file_id_a, file_id_b = pairs
    matches = []
    if match_algo == 'built-in':
        match_fun = ratio_max_mach_built_in
    elif match_algo == 'improved':
        match_fun = ratio_max_mach
    else:
        raise ValueError(f'Invalid value for match_algo (match_algo)')
    for file_id_a, file_id_b, window_id_a, window_id_b \
            in cache_db.stream_matching_candidate_windows(file_id_a, file_id_b):
        file_b_windows = list(get_windows(file_path_b, strip_diacritics, window_length, slide_length))
        file_a_windows = list(get_windows(file_path_a, strip_diacritics, window_length, slide_length))
        try:
            text_a = file_a_windows[window_id_a]
            text_b = file_b_windows[window_id_b]
        except (IndexError, TypeError):
            print(' * window lookup OOB')
            print(file_id_a, window_id_a, len(file_a_windows), file_path_a)
            print(file_id_b, window_id_b, len(file_b_windows), file_path_b)
            continue
        sim = match_fun(text_a, text_b)
        if sim >= min_sim:
            # remove matches with predominance of single character words
            a_singles = sum(int(len(i) == 1) for i in text_a.split())
            b_singles = sum(int(len(i) == 1) for i in text_b.split())
            if a_singles < (window_length * 0.75) and b_singles < (window_length * 0.75):
                matches.append([file_id_a, file_id_b, window_id_a, window_id_b, int(sim)])
    if matches:
        cache_db.write_matches(matches)
