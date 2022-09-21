import multiprocessing
from functools import partial
from itertools import combinations

from utils import chunked_iterator
from db import write_candidates, stream_hashbands


def get_all_match_candidates(kwargs):
    """Find all hashbands that have multiple distinct file_ids and save as match candidates"""
    # the hashbands table is our largest data artifact - paginate in blocks
    for chunk in chunked_iterator(stream_hashbands(kwargs), kwargs['batch_size']):
        process_candidate_hashbands(list(chunk), **kwargs)


def process_candidate_hashbands(inp_hashbands, **kwargs):
    """Given a set of hashbands, subdivide into processes to find match candidates for each"""
    if kwargs['verbose']:
        print(' * processing match candidate block')
    pool = multiprocessing.Pool()
    # Subdivide list `l` into units `n` long lists
    hashbands = [list(chunk) for chunk in chunked_iterator(inp_hashbands,
                                                           len(inp_hashbands) // multiprocessing.cpu_count())]
    fun = partial(get_hashband_match_candidates, **kwargs)
    writes = set()
    for idx, i in enumerate(pool.map(fun, hashbands)):
        writes.update(i)
        if len(writes) >= kwargs['write_frequency'] or idx == len(hashbands) - 1:
            write_candidates(writes, **kwargs)
            writes = set()
    if writes:
        write_candidates(writes, **kwargs)
    pool.close()
    pool.join()


def get_hashband_match_candidates(args, **kwargs):
    """Given a hashband, save the file_id, window_id values that contain the hashband"""
    results = []
    last_hashband = args[0][0]
    hashband_values = set()
    for idx, (hashband, file_id, window_id) in enumerate(args):
        tup = (file_id, window_id)
        if hashband == last_hashband:
            hashband_values.add(tup)
        elif hashband != last_hashband or idx == len(args) - 1:
            last_hashband = hashband
            if kwargs.get('only_index') is None or any(i[0] == kwargs['only_index'] for i in hashband_values):
                for a, b in combinations(hashband_values, 2):
                    if kwargs.get('only_index') is None or a[0] == kwargs['only_index'] or b[0] == kwargs['only_index']:
                        # skip same file matches
                        if a[0] < b[0]:
                            results.append((a[0], b[0], a[1], b[1]))
                        elif a[0] > b[0]:
                            results.append((b[0], a[0], b[1], a[1]))
                hashband_values = {tup}
    return set(results)
