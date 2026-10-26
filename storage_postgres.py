"""
The PostgreSQL backend of the Storage layer (REQ-SLY-001, REQ-SLY-002, REQ-SLY-003, REQ-SLY-006): the same entries as the file backend, shared by
several instances. Needs psycopg 3 (requirements-db.txt); it is imported only when the storage is `postgres`, so a file-only installation needs
no database driver.

  - the schema is the numbered SQL files in deploy/db/, applied once each at start (table schema_version)
  - two instances writing the same version number: the primary key lets one win, the other gets a conflict and may read and retry
  - notices go through LISTEN/NOTIFY on the channel mia_changes; publish() sends, listen() receives on a connection of its own, so every instance
    hears every write, its own included
"""
import json
import os
import threading

import psycopg

try:
    from .storage import StorageError
except ImportError:  # used as plain script / in tests
    from storage import StorageError

CHANNEL = "mia_changes"
SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deploy", "db")


class PostgresBackend:
    def __init__(self, url, schema_dir=SCHEMA_DIR):
        self.url = url
        self._conn = psycopg.connect(url, autocommit=True)
        self._lock = threading.Lock()            # one connection, used by one thread at a time
        self._stop = threading.Event()
        self._listener = None
        self._apply_schema(schema_dir)

    def _apply_schema(self, schema_dir):
        done = set()
        with self._lock:
            if self._conn.execute("SELECT to_regclass('schema_version')").fetchone()[0]:
                done = {row[0] for row in self._conn.execute("SELECT version FROM schema_version")}
            for name in sorted(os.listdir(schema_dir)):
                number = int(name.split("_")[0]) if name.endswith(".sql") else None
                if number is not None and number not in done:
                    with open(os.path.join(schema_dir, name), encoding="utf-8") as handle:
                        self._conn.execute(handle.read())

    def _query(self, sql, params=()):
        with self._lock:
            cursor = self._conn.execute(sql, params)
            return cursor.fetchall() if cursor.description else []

    def versions(self, table, record_id):
        rows = self._query("SELECT version, author, time, doc FROM records WHERE tbl = %s AND id = %s ORDER BY version", (table, record_id))
        return [{"id": record_id, "version": v, "author": a, "time": t, "doc": d} for v, a, t, d in rows]

    def append(self, table, record_id, entry):
        try:
            with self._lock:
                self._conn.execute("INSERT INTO records (tbl, id, version, author, time, doc) VALUES (%s, %s, %s, %s, %s, %s::jsonb)",
                                   (table, record_id, entry["version"], entry["author"], entry["time"], json.dumps(entry["doc"], ensure_ascii=False)))
        except psycopg.errors.UniqueViolation:
            raise StorageError("conflict", detail={"current": len(self.versions(table, record_id))}) from None

    def ids(self, table):
        return [row[0] for row in self._query("SELECT DISTINCT id FROM records WHERE tbl = %s", (table,))]

    def remove(self, table, record_id):
        self._query("DELETE FROM records WHERE tbl = %s AND id = %s RETURNING 1", (table, record_id))

    def publish(self, event):
        self._query("SELECT pg_notify(%s, %s)", (CHANNEL, json.dumps(event)))

    def listen(self, callback):
        """callback(event) for every notice of any instance, on a thread of its own."""
        if self._listener:
            return
        connection = psycopg.connect(self.url, autocommit=True)
        connection.execute("LISTEN " + CHANNEL)
        ready = threading.Event()

        def loop():
            ready.set()
            try:
                while not self._stop.is_set():
                    for notice in connection.notifies(timeout=0.2):
                        callback(json.loads(notice.payload))
            except psycopg.OperationalError:        # the server went away: the listener ends, a new Storage listens again
                pass
            finally:
                connection.close()
        self._listener = threading.Thread(target=loop, daemon=True, name="storage-listen")
        self._listener.start()
        ready.wait(2)

    def close(self):
        self._stop.set()
        if self._listener:
            self._listener.join(2)
        self._conn.close()
