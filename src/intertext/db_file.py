from collections import defaultdict
from pathlib import Path


def clear_db_file():
    pass


def initialize_db_file(_):
    for i in ('hashbands', 'candidates', 'matches'):
        (Path('db') / i).mkdir(parents=True, exist_ok=True)


def write_hashbands_file(writes, verbose=False, row_delimiter='\n', field_delimiter='-'):
    """Given a db cursor and list of write operations, insert each"""
    if verbose:
        print(' * writing', len(writes), 'hashbands')
    d = defaultdict(list)
    for hashband, file_id, window_id in writes:
        d[hashband].append([file_id, window_id])
    for hashband in d:
        out_dir = Path('db') / 'hashbands' / hashband[0:2]
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / hashband[2:4]
        with open(path, 'a') as out:
            s = ''
            for r in d[hashband]:
                s += field_delimiter.join([str(v) for v in [hashband] + r]) + row_delimiter
            out.write(s)


def write_candidates_file(writes, verbose=False, row_delimiter='\n', field_delimiter='-'):
    """Given a db cursor and list of write operations, insert each"""
    if verbose:
        print(' * writing', len(writes), 'candidates')
    d = defaultdict(lambda: defaultdict(list))
    for row in writes:
        file_id_a, file_id_b, window_id_a, window_id_b = row
        d[file_id_a][file_id_b].append([window_id_a, window_id_b])
    for file_id_a in d:
        for file_id_b in d[file_id_a]:
            out_dir = Path('db') / 'candidates' / str(file_id_a)
            write_files(d, file_id_a, file_id_b, out_dir, row_delimiter, field_delimiter)


# Internal helper function
def write_files(d, file_id_a, file_id_b, out_dir, row_delimiter='\n', field_delimiter='-'):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / str(file_id_b), 'a') as out:
        for row in d[file_id_a][file_id_b]:
            out.write(field_delimiter.join(str(v) for v in row))
            out.write(row_delimiter)


def write_matches_file(writes, verbose=False, row_delimiter='\n', field_delimiter='-'):
    """Given a db cursor and list of write operations, insert each"""
    if verbose:
        print(' * writing', len(writes), 'matches')
    d = defaultdict(lambda: defaultdict(list))
    for row in writes:
        file_id_a, file_id_b, window_id_a, window_id_b, sim = row
        d[file_id_a][file_id_b].append([window_id_a, window_id_b, sim])
    for file_id_a in d:
        for file_id_b in d[file_id_a]:
            write_files(d, file_id_a, file_id_b, Path('db') / 'matches' / str(file_id_a), row_delimiter,
                        field_delimiter)


def delete_matches_file(banished_dict, verbose=False, row_delimiter='\n', field_delimiter='-'):
    """Given d[file_id] = [window_id], delete all specified windows"""
    if verbose:
        print(' * deleting', sum(len(window_ids) for window_ids in banished_dict.values()), 'matches')
    for file_id in banished_dict:
        for i in (Path('db') / 'matches' / file_id).glob('*'):
            with open(i) as f:
                lines = []
                for e in f.read().strip().split(row_delimiter):
                    window_id_a, window_id_b, sim = e.split(field_delimiter)
                    if window_id_a not in banished_dict[file_id]:
                        lines.append(e)
            # write the cleaned lines to disk
            with open(i, 'w') as out:
                out.write(row_delimiter.join(lines))


def stream_hashbands_file(verbose=False, row_delimiter='\n', field_delimiter='-'):
    """Stream [hashband, file_id, window_id] sorted by hashband"""
    if verbose:
        print(' * querying for hashbands')
    for i in (Path('db') / 'hashbands').glob('*/*'):
        d = defaultdict(list)
        with open(i) as f:
            f = f.read()
        # accumulate file_id, window id values by hashband to effectively sort by hashband
        for row in f.split(row_delimiter):
            if row:
                hashband, file_id, window_id = row.split(field_delimiter)
                d[hashband].append([int(file_id), int(window_id)])
        for hashband in d:
            file_ids, window_ids = zip(*d[hashband])
            if len(set(file_ids)) > 1:
                for j in d[hashband]:
                    yield [hashband] + j


def stream_candidate_file_id_pairs_file(verbose=False):
    """Stream [file_id_a, file_id_b] pairs for files with matching hashbands"""
    if verbose:
        print(' * querying for candidate file id pairs')
    for i in (Path('db') / 'candidates').glob('*'):
        file_id_a = i.name
        for j in i.glob('*'):
            file_id_b = j.name
            yield [int(file_id_a), int(file_id_b)]


def stream_matching_file_id_pairs_file():
    """Stream [file_id_a, file_id_b] for file ids that have verified matches"""
    for i in (Path('db') / 'matches').glob('*'):
        file_id_a = i.name
        for j in i.glob('*'):
            file_id_b = j.name
            yield [int(file_id_a), int(file_id_b)]


def stream_matching_candidate_windows_file(file_id_a, file_id_b, verbose=False, row_delimiter='\n',
                                           field_delimiter='-'):
    """Stream [file_id_a, file_id_b, window_id_a, window_id_b] for matching hashbands"""
    if verbose:
        print(' * querying for matching candidate windows')
    with open(Path('db') / 'candidates' / str(file_id_a) / str(file_id_b)) as f:
        f = f.read()
    for row in f.split(row_delimiter):
        if row:
            yield [file_id_a, file_id_b] + [int(i) for i in row.split(field_delimiter)]


def stream_file_pair_matches_file(file_id_a, file_id_b, row_delimiter='\n', field_delimiter='-'):
    """Stream [file_id_a, file_id_b, window_id_a, window_id_b, similarity] for a match pair"""
    with open(Path('db') / 'matches' / str(file_id_a) / str(file_id_b)) as f:
        f = f.read()
        for row in f.split(row_delimiter):
            if row:
                yield [int(file_id_a), int(file_id_b)] + [int(j) for j in row.split(field_delimiter)]
