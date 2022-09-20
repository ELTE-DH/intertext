import functools
import multiprocessing

from utils import get_windows, get_cacheable
from format_matches import get_string_sim
from db import write_matches, stream_candidate_file_id_pairs, stream_matching_candidate_windows


def validate_all_matches(**kwargs):
    """Run match validations and yield [a_file,b_file,a_window,b_window]"""
    pool = multiprocessing.Pool()
    pairs = stream_candidate_file_id_pairs(**kwargs)
    f = functools.partial(validate_file_matches, **kwargs)
    for _ in pool.map(f, pairs):
        pass
    pool.close()
    pool.join()


def validate_file_matches(file_args, **kwargs):
    """Validate the matches for a single file pair and return [a_file,b_file,a_window,b_window]"""
    file_id_a, file_id_b = file_args
    matches = []
    for i in stream_matching_candidate_windows(file_id_a, file_id_b, **kwargs):
        file_id_a, file_id_b, window_id_a, window_id_b = i
        file_a_windows = list(get_windows(kwargs['infiles'][file_id_a], **get_cacheable(kwargs)))
        file_b_windows = list(get_windows(kwargs['infiles'][file_id_b], **get_cacheable(kwargs)))
        try:
            text_a = file_a_windows[window_id_a]
            text_b = file_b_windows[window_id_b]
        except:
            print(' * window lookup OOB')
            print(file_id_a, window_id_a, len(file_a_windows), kwargs['infiles'][file_id_a])
            print(file_id_b, window_id_b, len(file_b_windows), kwargs['infiles'][file_id_b])
            continue
        sim = get_string_sim(text_a, text_b, **kwargs)
        if sim >= kwargs['min_sim']:
            # remove matches with predominance of single character words
            a_singles = [i for i in text_a.split() if len(i) == 1]
            b_singles = [i for i in text_b.split() if len(i) == 1]
            if len(a_singles) >= (kwargs['window_length'] * 0.75) or \
                    len(b_singles) >= (kwargs['window_length'] * 0.75):
                continue
            matches.append([
                file_id_a,
                file_id_b,
                window_id_a,
                window_id_b,
                int(sim),
            ])
    write_matches(matches, **kwargs)