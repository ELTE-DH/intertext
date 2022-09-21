import shutil
import sqlite3
from pathlib import Path
from contextlib import closing
from collections import defaultdict

from config import cache_location, row_delimiter, field_delimiter


def clear_db():
    """Clear the extant db"""
    if Path('db').exists():
        shutil.rmtree('db')
    for i in Path('cache').glob('*.db'):
        i.unlink()


def initialize_db(db_name, **kwargs):
    """Run all setup steps to create the database"""
    if kwargs.get('db') == 'sqlite':
        with closing(get_db(db_name, initialize=True, **kwargs)) as db:
            cursor = db.cursor()
            cursor.execute('DROP TABLE IF EXISTS hashbands;')
            cursor.execute('DROP TABLE IF EXISTS candidates;')
            cursor.execute('DROP TABLE IF EXISTS matches;')
            cursor.execute('CREATE TABLE hashbands (hashband TEXT, file_id INTEGER, window_id INTEGER);')
            cursor.execute(
                'CREATE TABLE candidates (file_id_a INTEGER, file_id_b INTEGER, window_id_a INTEGER, window_id_b '
                'INTEGER, UNIQUE(file_id_a, file_id_b, window_id_a, window_id_b));')
            cursor.execute(
                'CREATE TABLE matches (file_id_a INTEGER, file_id_b INTEGER, window_id_a INTEGER, window_id_b '
                'INTEGER, similarity INTEGER);')
    else:
        for i in ('hashbands', 'candidates', 'matches'):
            (Path('db') / i).mkdir(parents=True, exist_ok=True)


def get_db(db_name, initialize=False, **_):
    """Return a Sqlite DB"""
    db_location = cache_location / f'{db_name}.db'
    db = sqlite3.connect(db_location, uri=True, timeout=2 ** 16)
    if initialize:
        db.execute('PRAGMA synchronous = EXTRA;')  # OFF is fastest
        db.execute('PRAGMA journal_mode = DELETE;')  # WAL is fastest
    db.execute('PRAGMA temp_store = 1;')
    db.execute(f'PRAGMA temp_store_directory = "{cache_location}"')
    return db


def write_hashbands(writes, **kwargs):
    """Given a db cursor and list of write operations, insert each"""
    if not writes:
        return []
    if kwargs.get('db') == 'sqlite':
        try:
            if kwargs['verbose']:
                print(' * writing', len(writes), 'hashbands')
            with closing(get_db('hashbands', **kwargs)) as db:
                cursor = db.cursor()
                cursor.executemany('INSERT INTO hashbands (hashband, file_id, window_id) VALUES (?,?,?);', writes)
                db.commit()
        except sqlite3.DatabaseError:
            repair_database(**kwargs)
            return write_hashbands(writes, **kwargs)
    else:
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


def write_candidates(writes, **kwargs):
    """Given a db cursor and list of write operations, insert each"""
    if not writes:
        return
    if kwargs.get('db') == 'sqlite':
        try:
            if kwargs['verbose']:
                print(' * writing', len(writes), 'candidates')
            with closing(get_db('candidates', **kwargs)) as db:
                cursor = db.cursor()
                cursor.executemany(
                    'INSERT OR IGNORE INTO candidates (file_id_a, file_id_b, window_id_a, window_id_b) '
                    'VALUES (?,?,?,?);',
                    writes)
                db.commit()
        except sqlite3.DatabaseError:
            repair_database(**kwargs)
            return write_candidates(writes, **kwargs)
    else:
        d = defaultdict(lambda: defaultdict(list))
        for row in writes:
            file_id_a, file_id_b, window_id_a, window_id_b = row
            d[file_id_a][file_id_b].append([window_id_a, window_id_b])
        for file_id_a in d:
            for file_id_b in d[file_id_a]:
                out_dir = Path('db') / 'candidates' / str(file_id_a)
                write_files(d, file_id_a, file_id_b, out_dir)


def write_files(d, file_id_a, file_id_b, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / str(file_id_b), 'a') as out:
        for row in d[file_id_a][file_id_b]:
            out.write(field_delimiter.join(str(v) for v in row))
            out.write(row_delimiter)


def write_matches(writes, **kwargs):
    """Given a db cursor and list of write operations, insert each"""
    if kwargs.get('db') == 'sqlite':
        try:
            if writes:
                if kwargs['verbose']:
                    print(' * writing', len(writes), 'matches')
                with closing(get_db('matches', **kwargs)) as db:
                    cursor = db.cursor()
                    cursor.executemany(
                        'INSERT INTO matches (file_id_a, file_id_b, window_id_a, window_id_b, similarity) '
                        'VALUES (?,?,?,?,?);',
                        writes)
                    db.commit()
            return []
        except sqlite3.DatabaseError:
            repair_database(**kwargs)
            return write_matches(writes, **kwargs)
    else:
        d = defaultdict(lambda: defaultdict(list))
        for row in writes:
            file_id_a, file_id_b, window_id_a, window_id_b, sim = row
            d[file_id_a][file_id_b].append([window_id_a, window_id_b, sim])
        for file_id_a in d:
            for file_id_b in d[file_id_a]:
                write_files(d, file_id_a, file_id_b, Path('db') / 'matches' / str(file_id_a))


def delete_matches(banished_dict, **kwargs):
    """Given d[file_id] = [window_id], delete all specified windows"""
    if kwargs.get('db') == 'sqlite':
        deletes = []
        for file_id, window_ids in banished_dict.items():
            deletes += [(file_id, i, file_id, i) for i in window_ids]
        if kwargs['verbose']:
            print(' * deleting', len(deletes), 'matches')
        with closing(get_db('matches', **kwargs)) as db:
            cursor = db.cursor()
            cursor.executemany(
                'DELETE FROM matches WHERE file_id_a = (?) AND window_id_a = (?) OR file_id_b = (?) '
                'and window_id_b = (?) ',
                deletes)
            db.commit()
    else:
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


def repair_database(**_):
    """Attempt to repair the db in a process-safe manner"""
    raise sqlite3.DatabaseError


def stream_hashbands(kwargs):
    """Stream [hashband, file_id, window_id] sorted by hashband"""
    if kwargs.get('verbose'):
        print(' * querying for hashbands')
    if kwargs.get('db') == 'sqlite':
        with closing(get_db('hashbands', **kwargs)) as db:
            cursor = db.cursor()
            for row in cursor.execute("""
        WITH file_id_counts AS (
          SELECT hashband, COUNT(DISTINCT(file_id)) as count
          FROM hashbands
          GROUP BY hashband
          HAVING COUNT > 1
        ) SELECT hashband, file_id, window_id
          FROM hashbands
          WHERE hashband IN (SELECT hashband from file_id_counts)
          ORDER BY hashband
      """):
                yield row
    else:
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


def stream_candidate_file_id_pairs(kwargs):
    """Stream [file_id_a, file_id_b] pairs for files with matching hashbands"""
    if kwargs.get('verbose'):
        print(' * querying for candidate file id pairs')
    if kwargs.get('db') == 'sqlite':
        with closing(get_db('candidates', **kwargs)) as db:
            cursor = db.cursor()
            for row in cursor.execute("""
        SELECT DISTINCT file_id_a, file_id_b
        FROM candidates
        ORDER BY file_id_a, file_id_b
      """):
                yield row
    else:
        for i in (Path('db') / 'candidates').glob('*'):
            file_id_a = i.name
            for j in i.glob('*'):
                file_id_b = j.name
                yield [int(file_id_a), int(file_id_b)]


def stream_matching_file_id_pairs(kwargs):
    """Stream [file_id_a, file_id_b] for file ids that have verified matches"""
    if kwargs.get('db') == 'sqlite':
        with closing(get_db('matches', **kwargs)) as db:
            cursor = db.cursor()
            for i in cursor.execute('SELECT DISTINCT file_id_a, file_id_b FROM matches;'):
                yield i
    else:
        for i in (Path('db') / 'matches').glob('*'):
            file_id_a = i.name
            for j in i.glob('*'):
                file_id_b = j.name
                yield [int(file_id_a), int(file_id_b)]


def stream_matching_candidate_windows(file_id_a, file_id_b, **kwargs):
    """Stream [file_id_a, file_id_b, window_id_a, window_id_b] for matching hashbands"""
    if kwargs.get('verbose'):
        print(' * querying for matching candidate windows')
    if kwargs.get('db') == 'sqlite':
        with closing(get_db('candidates', **kwargs)) as db:
            cursor = db.cursor()
            for i in cursor.execute("""
          SELECT DISTINCT file_id_a, file_id_b, window_id_a, window_id_b
          FROM candidates
          WHERE file_id_a = ? AND file_id_b = ?
          ORDER BY file_id_b
        """, (file_id_a, file_id_b,)):
                yield i
    else:
        with open(Path('db') / 'candidates' / str(file_id_a) / str(file_id_b)) as f:
            f = f.read()
        for row in f.split(row_delimiter):
            if row:
                yield [file_id_a, file_id_b] + [int(i) for i in row.split(field_delimiter)]


def stream_file_pair_matches(file_id_a, file_id_b, **kwargs):
    """Stream [file_id_a, file_id_b, window_id_a, window_id_b, similarity] for a match pair"""
    if kwargs.get('db') == 'sqlite':
        with closing(get_db('matches', **kwargs)) as db:
            cursor = db.cursor()
            for i in cursor.execute('SELECT * FROM matches WHERE file_id_a = ? AND file_id_b = ?',
                                    (file_id_a, file_id_b,)):
                yield i
    else:
        with open(Path('db') / 'matches' / str(file_id_a) / str(file_id_b)) as f:
            f = f.read()
            for row in f.split(row_delimiter):
                if row:
                    yield [int(file_id_a), int(file_id_b)] + [int(j) for j in row.split(field_delimiter)]
