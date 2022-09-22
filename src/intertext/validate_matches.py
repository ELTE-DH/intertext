from difflib import SequenceMatcher

from utils import get_windows, get_cacheable, parallel_map


def validate_all_matches(kwargs):
    """Run match validations and yield [a_file,b_file,a_window,b_window]"""
    pairs = kwargs['db']['functions']['stream_candidate_file_id_pairs']()
    parallel_map(validate_file_matches, pairs, kwargs)


def validate_file_matches(file_args, **kwargs):
    """Validate the matches for a single file pair and return [a_file,b_file,a_window,b_window]"""
    file_id_a, file_id_b = file_args
    matches = []
    for file_id_a, file_id_b, window_id_a, window_id_b \
            in kwargs['db']['functions']['stream_matching_candidate_windows'](file_id_a, file_id_b):
        file_a_windows = list(get_windows(kwargs['infiles'][file_id_a], **get_cacheable(kwargs)))
        file_b_windows = list(get_windows(kwargs['infiles'][file_id_b], **get_cacheable(kwargs)))
        try:
            text_a = file_a_windows[window_id_a]
            text_b = file_b_windows[window_id_b]
        except (IndexError, TypeError):
            print(' * window lookup OOB')
            print(file_id_a, window_id_a, len(file_a_windows), kwargs['infiles'][file_id_a])
            print(file_id_b, window_id_b, len(file_b_windows), kwargs['infiles'][file_id_b])
            continue
        sim = SequenceMatcher(a=text_a, b=text_b, autojunk=False).ratio() * 100
        if sim >= kwargs['min_sim']:
            # remove matches with predominance of single character words
            a_singles = sum(int(len(i) == 1) for i in text_a.split())
            b_singles = sum(int(len(i) == 1) for i in text_b.split())
            if a_singles < (kwargs['window_length'] * 0.75) and b_singles < (kwargs['window_length'] * 0.75):
                matches.append([
                    file_id_a,
                    file_id_b,
                    window_id_a,
                    window_id_b,
                    int(sim),
                ])
    kwargs['db']['functions']['write_matches'](matches)
