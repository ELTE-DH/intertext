import shutil
import sqlite3
from contextlib import closing
from pathlib import Path


def clear_db_sql():
    """Clear the extant db"""
    if Path('db').exists():
        shutil.rmtree('db')
    for i in Path('cache').glob('*.db'):
        i.unlink()


def initialize_db_sql(db_name, cache_location):
    """Run all setup steps to create the database"""
    with closing(get_db(db_name, initialize=True, cache_location=cache_location)) as db:
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


# Internal helper function
def get_db(db_name, initialize=False, cache_location=Path('.') / 'cache'):
    """Return a Sqlite DB"""
    db_location = cache_location / f'{db_name}.db'
    db = sqlite3.connect(db_location, uri=True, timeout=2 ** 16)
    if initialize:
        db.execute('PRAGMA synchronous = EXTRA;')  # OFF is fastest
        db.execute('PRAGMA journal_mode = DELETE;')  # WAL is fastest
    db.execute('PRAGMA temp_store = 1;')
    db.execute(f'PRAGMA temp_store_directory = "{cache_location}"')
    return db


def write_hashbands_sql(writes, verbose=False, cache_location=Path('.') / 'cache'):
    """Given a db cursor and list of write operations, insert each"""
    if writes:
        if verbose:
            print(' * writing', len(writes), 'hashbands')
        try:
            with closing(get_db('hashbands', cache_location=cache_location)) as db:
                cursor = db.cursor()
                cursor.executemany('INSERT INTO hashbands (hashband, file_id, window_id) VALUES (?,?,?);', writes)
                db.commit()
        except sqlite3.DatabaseError:
            # Attempt to repair the db in a process-safe manner
            raise sqlite3.DatabaseError
            # return write_hashbands(writes, **kwargs)


def write_candidates_sql(writes, verbose=False, cache_location=Path('.') / 'cache'):
    """Given a db cursor and list of write operations, insert each"""
    if writes:
        if verbose:
            print(' * writing', len(writes), 'candidates')
        try:
            with closing(get_db('candidates', cache_location=cache_location)) as db:
                cursor = db.cursor()
                cursor.executemany(
                    'INSERT OR IGNORE INTO candidates (file_id_a, file_id_b, window_id_a, window_id_b) '
                    'VALUES (?,?,?,?);',
                    writes)
                db.commit()
        except sqlite3.DatabaseError:
            # Attempt to repair the db in a process-safe manner
            raise sqlite3.DatabaseError
            # return write_candidates(writes, **kwargs)


def write_matches_sql(writes, verbose=False, cache_location=Path('.') / 'cache'):
    """Given a db cursor and list of write operations, insert each"""
    if writes:
        if verbose:
            print(' * writing', len(writes), 'matches')
        try:
            with closing(get_db('matches', cache_location=cache_location)) as db:
                cursor = db.cursor()
                cursor.executemany(
                    'INSERT INTO matches (file_id_a, file_id_b, window_id_a, window_id_b, similarity) '
                    'VALUES (?,?,?,?,?);',
                    writes)
                db.commit()
        except sqlite3.DatabaseError:
            # Attempt to repair the db in a process-safe manner
            raise sqlite3.DatabaseError
            # return write_matches(writes, **kwargs)


def delete_matches_sql(banished_dict, verbose=False, cache_location=Path('.') / 'cache'):
    """Given d[file_id] = [window_id], delete all specified windows"""
    deletes = []
    for file_id, window_ids in banished_dict.items():
        deletes += [(file_id, i, file_id, i) for i in window_ids]
    if verbose:
        print(' * deleting', len(deletes), 'matches')
    with closing(get_db('matches', cache_location=cache_location)) as db:
        cursor = db.cursor()
        cursor.executemany(
            'DELETE FROM matches WHERE file_id_a = (?) AND window_id_a = (?) OR file_id_b = (?) '
            'and window_id_b = (?) ',
            deletes)
        db.commit()


def stream_hashbands_sql(verbose=False, cache_location=Path('.') / 'cache'):
    """Stream [hashband, file_id, window_id] sorted by hashband"""
    if verbose:
        print(' * querying for hashbands')
    with closing(get_db('hashbands', cache_location=cache_location)) as db:
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


def stream_candidate_file_id_pairs_sql(verbose=False, cache_location=Path('.') / 'cache'):
    """Stream [file_id_a, file_id_b] pairs for files with matching hashbands"""
    if verbose:
        print(' * querying for candidate file id pairs')
    with closing(get_db('candidates', cache_location=cache_location)) as db:
        cursor = db.cursor()
        for row in cursor.execute("""
      SELECT DISTINCT file_id_a, file_id_b
      FROM candidates
      ORDER BY file_id_a, file_id_b
    """):
            yield row


def stream_matching_file_id_pairs_sql(cache_location):
    """Stream [file_id_a, file_id_b] for file ids that have verified matches"""
    with closing(get_db('matches', cache_location)) as db:
        cursor = db.cursor()
        for i in cursor.execute('SELECT DISTINCT file_id_a, file_id_b FROM matches;'):
            yield i


def stream_matching_candidate_windows_sql(file_id_a, file_id_b, verbose=False, cache_location=Path('.') / 'cache'):
    """Stream [file_id_a, file_id_b, window_id_a, window_id_b] for matching hashbands"""
    if verbose:
        print(' * querying for matching candidate windows')
    with closing(get_db('candidates', cache_location=cache_location)) as db:
        cursor = db.cursor()
        for i in cursor.execute("""
      SELECT DISTINCT file_id_a, file_id_b, window_id_a, window_id_b
      FROM candidates
      WHERE file_id_a = ? AND file_id_b = ?
      ORDER BY file_id_b
    """, (file_id_a, file_id_b,)):
            yield i


def stream_file_pair_matches_sql(file_id_a, file_id_b, cache_location):
    """Stream [file_id_a, file_id_b, window_id_a, window_id_b, similarity] for a match pair"""
    with closing(get_db('matches', cache_location)) as db:
        cursor = db.cursor()
        for i in cursor.execute('SELECT * FROM matches WHERE file_id_a = ? AND file_id_b = ?',
                                (file_id_a, file_id_b,)):
            yield i
