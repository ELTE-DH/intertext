from functools import partial
from operator import itemgetter
from multiprocessing import Pool
from itertools import combinations, groupby, chain, islice


# Only this function is public in this file!
def get_all_match_candidates(only_index, cache_db, verbose):
    """Find all hashbands that have multiple distinct file_ids and save as match candidates"""
    # Given a set of hashbands, subdivide into processes to find match candidates for each
    # the hashbands table is our largest data artifact - paginate in blocks of 10^5 elements
    hashbands = chunked_iterator(cache_db.stream_hashbands(), 10 ** 5)
    pool = Pool()
    for writes in pool.map(partial(get_hashband_match_candidates, only_index=only_index), hashbands):
        if verbose:
            print(' * writing a match candidate block into the database')
        # write results in len(candidates)/10^5 chunks into the database which do global deduplication if needed
        cache_db.write_candidates(writes)
    pool.close()
    pool.join()


def get_hashband_match_candidates(args, only_index):
    """Given a hashband, save the file_id, window_id values that contain the hashband (group by hashband)"""
    results = set()
    for k, g in groupby(args, key=itemgetter(0)):
        hashband_values = list(g)
        # all group or any group with a file_id that match if there is only_index to match...
        if only_index is None or any(val[1] == only_index for val in hashband_values):
            for (_, file_id_a, window_id_a), (_, file_id_b, window_id_b) in combinations(hashband_values, 2):
                # all combination or any combination with a file_id that match if there is only_index to match...
                if only_index is None or file_id_a == only_index or file_id_b == only_index:
                    # skip same file matches
                    if file_id_a < file_id_b:
                        results.add((file_id_a, file_id_b, window_id_a, window_id_b))
                    elif file_id_a > file_id_b:
                        results.add((file_id_b, file_id_a, window_id_b, window_id_a))
    return set(results)


def chunked_iterator(iterable, n):
    # Original source:
    # https://stackoverflow.com/questions/8991506/iterate-an-iterator-by-chunks-of-n-in-python/29524877#29524877
    it = iter(iterable)
    try:
        while True:
            yield list(chain((next(it),), islice(it, n-1)))
    except StopIteration:
        return
