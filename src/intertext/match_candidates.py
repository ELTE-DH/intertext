import functools
import multiprocessing
from itertools import combinations

from db import write_candidates, stream_hashbands


def get_all_match_candidates(**kwargs):
    """Find all hashbands that have multiple distinct file_ids and save as match candidates"""
    rows = []
    for row in stream_hashbands(**kwargs):
        rows.append(row)
        # the hashbands table is our largest data artifact - paginate in blocks
        if len(rows) >= kwargs['batch_size']:
            process_candidate_hashbands(rows, **kwargs)
            rows = []
    process_candidate_hashbands(rows, **kwargs)


def process_candidate_hashbands(hashbands, **kwargs):
    """Given a set of hashbands, subdivide into processes to find match candidates for each"""
    if kwargs['verbose']:
        print(' * processing match candidate block')
    pool = multiprocessing.Pool()
    hashbands = list(subdivide(hashbands, len(hashbands) // multiprocessing.cpu_count()))
    f = functools.partial(get_hashband_match_candidates, **kwargs)
    writes = set()
    for idx, i in enumerate(pool.map(f, hashbands)):
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
    for idx, i in enumerate(args):
        hashband, file_id, window_id = i
        tup = tuple([file_id, window_id])
        if hashband == last_hashband:
            hashband_values.add(tup)
        elif (hashband != last_hashband) or (idx == len(args) - 1):
            last_hashband = hashband
            if kwargs.get('only_index') is not None:
                if not any([i[0] == kwargs['only_index'] for i in hashband_values]):
                    continue
            for a, b in combinations(hashband_values, 2):
                if kwargs.get('only_index') is not None:
                    if a[0] != kwargs['only_index'] and b[0] != kwargs['only_index']:
                        continue
                # skip same file matches
                if a[0] == b[0]:
                    continue
                elif a[0] < b[0]:
                    results.append(tuple([a[0], b[0], a[1], b[1]]))
                else:
                    results.append(tuple([b[0], a[0], b[1], a[1]]))
            hashband_values = {tup}
    return set(results)


def subdivide(inp_list, n):
    """Subdivide list `l` into units `n` long"""
    if not inp_list or not n:
        return inp_list
    for i in range(0, len(inp_list), n):
        yield inp_list[i:i + n]
