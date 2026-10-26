"""The Storage layer on PostgreSQL (N-3.1 T-06): the behaviour tests of the file backend run unchanged on a throwaway postgres:16 container (data on tmpfs),
plus the shared-database cases: notices between two instances (TC-SLY-006) and the move between files and database (TC-SLY-007).
Skipped, never weakened, where podman, the image or psycopg is missing. Run with the python that has psycopg:  python tests/test_storage_postgres.py"""
import contextlib
import io
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from markers import mark                                  # noqa: E402
from storage import Storage, StorageError                 # noqa: E402
from storage_files import FileBackend                     # noqa: E402
from test_storage import StorageBehaviour, LOOKUP         # noqa: E402
from test_storage_copy import tree                        # noqa: E402

try:
    import psycopg
    from storage_postgres import PostgresBackend
    SKIP = None
except ImportError:
    psycopg, SKIP = None, "psycopg 3 is not installed (requirements-db.txt)"

IMAGE = "docker.io/library/postgres:16"
NAME = "mia-test-postgres-%d" % os.getpid()


def podman(*args):
    return subprocess.run(["podman", *args], capture_output=True, text=True)


def start_database():
    """Returns the connection URL of a fresh database, or raises unittest.SkipTest."""
    if SKIP:
        raise unittest.SkipTest(SKIP)
    if shutil.which("podman") is None:
        raise unittest.SkipTest("podman is not available")
    if podman("image", "exists", IMAGE).returncode != 0 and podman("pull", "-q", IMAGE).returncode != 0:
        raise unittest.SkipTest("the image %s cannot be pulled" % IMAGE)
    run = podman("run", "-d", "--rm", "--name", NAME, "-e", "POSTGRES_PASSWORD=test", "--tmpfs", "/var/lib/postgresql/data", "-p", "127.0.0.1::5432", IMAGE)
    if run.returncode != 0:
        raise unittest.SkipTest("the database container does not start: " + run.stderr.strip()[:100])
    port = podman("port", NAME, "5432").stdout.strip().rsplit(":", 1)[-1]
    url = "postgresql://postgres:test@127.0.0.1:%s/postgres" % port
    for _ in range(60):
        try:
            psycopg.connect(url, connect_timeout=2).close()
            return url
        except psycopg.OperationalError:
            time.sleep(0.5)
    podman("rm", "-f", NAME)
    raise unittest.SkipTest("the database did not become ready in 30 s")


def stop_database():
    podman("rm", "-f", NAME)


class PostgresStorage(StorageBehaviour, unittest.TestCase):
    """TC-SLY-002, -003, -004 and the IF-102 errors on PostgreSQL: the same tests as the file backend."""

    @classmethod
    def setUpClass(cls):
        cls.url = start_database()
        cls.addClassCleanup(stop_database)

    def new_backend(self, label):
        previous = getattr(self, "_previous", None)
        if previous and label != "main":            # the seed test asks for 500 stores one after the other: one connection at a time
            previous.close()
        backend = PostgresBackend(self.url)
        backend._query("TRUNCATE records")
        self._previous = backend
        self.addCleanup(backend.close)
        return backend

    def reopen(self):
        backend = PostgresBackend(self.url)
        self.addCleanup(backend.close)
        return backend


class SharedDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = start_database()
        cls.addClassCleanup(stop_database)

    def setUp(self):
        self.first, self.second = PostgresBackend(self.url), PostgresBackend(self.url)
        self.first._query("TRUNCATE records")
        self.addCleanup(self.first.close)
        self.addCleanup(self.second.close)
        self.a, self.b = Storage(self.first), Storage(self.second)

    @mark.req("REQ-SLY-006")
    def test_a_write_on_one_connection_is_heard_on_the_other_within_2_s(self):
        """TC-SLY-006 (PostgreSQL): 20 writes on the first instance; the second hears each once with table, id, version and author; median and maximum at most 2 s."""
        heard, delays = [], []
        started = {}

        def on_event(event):
            heard.append(event)
            delays.append(time.perf_counter() - started[event["version"]])
        self.b.subscribe("tasks", on_event)
        for n in range(1, 21):
            started[n] = time.perf_counter()
            self.a.put("tasks", "t", {"text": str(n)}, "anna")
            deadline = time.time() + 2.5
            while len(heard) < n and time.time() < deadline:
                time.sleep(0.01)
        self.assertEqual([e["version"] for e in heard], list(range(1, 21)))
        self.assertEqual(heard[0], {"table": "tasks", "id": "t", "version": 1, "author": "anna"})
        self.assertLessEqual(statistics.median(delays), 2)
        self.assertLessEqual(max(delays), 2)

    @mark.req("REQ-SLY-006")
    def test_nothing_arrives_after_unsubscribe_and_other_tables_are_not_heard(self):
        heard = []
        stop = self.b.subscribe("tasks", heard.append)
        self.a.put("memos", "m", {"text": "other table"}, "anna")
        time.sleep(0.5)
        self.assertEqual(heard, [])
        stop()
        self.a.put("tasks", "t", {"text": "x"}, "anna")
        time.sleep(0.5)
        self.assertEqual(heard, [])

    @mark.req("REQ-SLY-003")
    def test_two_instances_writing_the_same_record_never_share_a_version(self):
        """The primary key lets one writer win; the other gets a conflict and no version is written twice."""
        results, errors = [], []

        def write(store, n):
            try:
                results.append(store.put("tasks", "t", {"text": str(n)}, "anna")["version"])
            except StorageError as err:
                errors.append(err.code)
        threads = [threading.Thread(target=write, args=(store, n)) for n, store in enumerate([self.a, self.b] * 5)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(len(results) + len(errors), 10)
        self.assertEqual(sorted(results), sorted(set(results)))
        self.assertEqual(set(errors) - {"conflict"}, set())
        self.assertEqual([h["version"] for h in self.a.history("tasks", "t")], list(range(1, len(results) + 1)))

    @mark.req("REQ-SLY-007")
    def test_files_to_the_database_and_back_give_identical_files(self):
        """TC-SLY-007: the data folder moved with `migrate files-to-db` and back with `db-to-files` is identical file by file."""
        import migrate
        base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, base, True)
        data, back = os.path.join(base, "data"), os.path.join(base, "back")
        files = Storage(FileBackend(data))
        files.put("workflows", "lookup", LOOKUP, "anna")
        files.put("workflows", "lookup", dict(LOOKUP, note="v2"), "ben")
        files.put("memos", "a/b", {"text": "Zoë\n✓"}, "anna")
        files.put("accounts", "anna", {"name": "anna", "hash": "h", "salt": "s"}, "owner")
        for argv in (["files-to-db", "--data", data], ["db-to-files", "--data", back]):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(migrate.main(argv + ["--database-url", self.url]), 0)
        self.assertEqual(tree(back), tree(data))

    @mark.req("REQ-SLY-001")
    def test_the_schema_is_applied_once_and_a_second_start_keeps_the_data(self):
        self.a.put("tasks", "t", {"text": "kept"}, "anna")
        again = PostgresBackend(self.url)
        self.addCleanup(again.close)
        self.assertEqual(Storage(again).get("tasks", "t")["doc"], {"text": "kept"})
        self.assertEqual(self.first._query("SELECT version FROM schema_version"), [(1,)])


if __name__ == "__main__":
    unittest.main()
