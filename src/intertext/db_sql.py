import sqlite3
from contextlib import contextmanager


class SQLCache:
    def __init__(self, db_name, db_dir, initialize=False, verbose=False):
        self._db_name = db_name
        self._db_dir = db_dir
        self._verbose = verbose
        if initialize:
            self._initialize_db_sql()

    def _initialize_db_sql(self):
        """Run all setup steps to create the database"""
        with self._connect() as db:
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

    @contextmanager
    def _connect(self):
        """Return a Sqlite DB"""
        db = sqlite3.connect(self._db_dir / f'{self._db_name}.db', uri=True, timeout=2 ** 16)
        db.execute('PRAGMA synchronous = EXTRA;')  # OFF is fastest
        db.execute('PRAGMA journal_mode = DELETE;')  # WAL is fastest
        db.execute('PRAGMA temp_store = 1;')
        db.execute(f'PRAGMA temp_store_directory = "{self._db_dir}"')
        try:
            yield db
        finally:
            db.close()

    def clear_db_sql(self):
        """Clear the extant db"""
        for i in self._db_dir.glob('*.db'):
            i.unlink()

    def _generic_writer(self, query, writes, msg):
        """Given a db cursor and list of write operations, execute each"""
        if self._verbose:
            print(msg)
        # In case of error raises sqlite3.DatabaseError which of course should not happen
        with self._connect() as db:
            cursor = db.cursor()
            cursor.executemany(query, writes)
            db.commit()

    def write_hashbands(self, writes):
        self._generic_writer('INSERT INTO hashbands (hashband, file_id, window_id) VALUES (?,?,?);', writes,
                             f' * writing {len(writes)} hashbands')

    def write_candidates(self, writes):
        self._generic_writer(
            'INSERT OR IGNORE INTO candidates (file_id_a, file_id_b, window_id_a, window_id_b) VALUES (?,?,?,?);',
            writes, f' * writing {len(writes)} candidates')

    def write_matches(self, writes):
        self._generic_writer(
            'INSERT INTO matches (file_id_a, file_id_b, window_id_a, window_id_b, similarity) VALUES (?,?,?,?,?);',
            writes, f' * writing {len(writes)} matches')

    def delete_matches(self, deletes):
        """Given d[file_id] = [window_id], delete all specified windows"""
        self._generic_writer(
            'DELETE FROM matches WHERE file_id_a = (?) AND window_id_a = (?) OR file_id_b = (?) and window_id_b = (?);',
            deletes, f' * deleting {len(deletes)} matches')

    def _generic_reader(self, query, params, msg):
        if self._verbose:
            print(msg)
        with self._connect() as db:
            cursor = db.cursor()
            for row in cursor.execute(query, params):
                yield row

    def stream_hashbands(self):
        """Stream [hashband, file_id, window_id] sorted by hashband"""
        return self._generic_reader("""WITH file_id_counts AS (SELECT hashband, COUNT(DISTINCT(file_id)) as count
                                                                 FROM hashbands GROUP BY hashband HAVING COUNT > 1
                                                                 ) SELECT hashband, file_id, window_id
                                         FROM hashbands WHERE hashband IN (SELECT hashband from file_id_counts)
                                         ORDER BY hashband;""", (),
                                    ' * querying for hashbands')

    def stream_candidate_file_id_pairs(self):
        """Stream [file_id_a, file_id_b] pairs for files with matching hashbands"""
        return self._generic_reader(
           'SELECT DISTINCT file_id_a, file_id_b FROM candidates ORDER BY file_id_a, file_id_b;', (),
           ' * querying for candidate file id pairs')

    def stream_matching_file_id_pairs(self):
        """Stream [file_id_a, file_id_b] for file ids that have verified matches"""
        return self._generic_reader('SELECT DISTINCT file_id_a, file_id_b FROM matches;', (),
                                    ' * querying for matching file id pairs')

    def stream_matching_candidate_windows(self, file_id_a, file_id_b):
        """Stream [file_id_a, file_id_b, window_id_a, window_id_b] for matching hashbands"""
        return self._generic_reader('SELECT DISTINCT file_id_a, file_id_b, window_id_a, window_id_b FROM candidates '
                                    'WHERE file_id_a = ? AND file_id_b = ? ORDER BY file_id_b;', (file_id_a, file_id_b),
                                    ' * querying for matching candidate windows')

    def stream_file_pair_matches(self, file_id_a, file_id_b):
        """Stream [window_id_a, window_id_b, similarity] for a match pair in file_id_a and file_id_b"""
        return self._generic_reader('SELECT window_id_a, window_id_b, similarity FROM matches '
                                    'WHERE file_id_a = ? AND file_id_b = ?;', (file_id_a, file_id_b),
                                    ' * querying for file pair matches')

    def stream_all_pair_matches(self):
        """Stream [file_id_a, file_id_b, window_id_a, window_id_b, similarity] for all match pairs"""
        return self._generic_reader('SELECT * FROM matches;', (),
                                    ' * querying for file pair matches')
