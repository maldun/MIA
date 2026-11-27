"""
Acceptance tests of the copy setting in the backend (group AS of G-V4.GRAPHSTORE.TRANSFER): TC-API-060 to TC-API-064 (REQ-API-060 to 064;
HR-004, HR-006), under TR-TRANSFER-001, -009, -010.
MIA's real web_app runs from a copy of the checkout with its own configuration (`store`, `copy`, `autosync`) in a separate process, started
through `start_backend()` and stopped through `graceful_shutdown(stop_list())` of MIA's `__main__` module, the two functions `python -m MIA`
calls (TR-TRANSFER-009), and asked through Flask's test client. The live store is the data folder of that copy (`store: files`) or, for
TC-API-063, a database address on a port where nothing listens; the copy is a fresh folder. Stores and cases from transfer_stores (AC-006).
Until T-06 builds the copy setting, every case fails by assertion (the start function is missing, or the start stops at the database).
Run with: /home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/test_transfer_backend.py
"""
import json
import os
import socket
import sys
import tempfile
import shutil
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                                     # noqa: E402
from storage import Storage                                                  # noqa: E402
from storage_files import FileBackend                                        # noqa: E402
from graph_model import GraphModel                                           # noqa: E402
import transfer_stores as ts                                                 # noqa: E402
from web_app_probe import checkout_with, data_folder, run_main, last_json   # noqa: E402

KEYS = ("store", "copy", "autosync")

# The script part every case shares: the two stores as plain file backends, anna's account, the test client (TR-TRANSFER-009)
COMMON = """
import transfer_stores as ts
from storage_files import FileBackend
LIVE, COPY = %r, %r
def group(path):
    return ts.graph_group(FileBackend(path))
accounts.create(wa._account_store, "anna", "pw-anna-1", "transfer-tests")
"""
LOGIN = """
web = wa.app.test_client()
out["login"] = web.post("/api/login", json={"user": "anna", "password": "pw-anna-1"}).status_code
def ask(path):
    answer = web.get(path)
    return [answer.status_code, answer.get_json(silent=True)]
"""


def new_copy(test):
    folder = tempfile.mkdtemp(prefix="mia-copy-")
    test.addCleanup(shutil.rmtree, folder, True)
    return folder


def backend_with(test, settings, case=ts.ac006):
    """a checkout copy with `settings` (no other store, copy or autosync key); its data folder is the live store; `case(live, copy)` fills both"""
    copy = new_copy(test)
    folder = checkout_with(dict(settings, copy=copy) if "copy" not in settings else settings, drop=KEYS)
    live = data_folder(folder)
    os.makedirs(live, exist_ok=True)
    case(FileBackend(live), FileBackend(copy))
    return folder, live, copy


def as_json(value):
    return json.loads(json.dumps(value))


def started(test, folder, live, copy, script, env=None):
    done = run_main(folder, COMMON % (live, copy) + script, env=env)
    test.assertEqual(done.returncode, 0, "the backend did not start, run and stop through __main__ (TR-TRANSFER-009): " + done.stderr[-2000:])
    out = last_json(done)
    test.assertEqual(out.get("login"), 200, out)
    return out


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class CopySetting(unittest.TestCase):

    @mark.req("REQ-API-060")
    def test_TC_API_060_mia_reads_graphs_from_the_copy(self):
        """TC-API-060: with `copy` set, a graph read through the graph interface is the copy's version, not the live store's.

        Example: live cp2.multi at version 6, copy at version 4 -> the read answers version 4 with the copy's graph; the list says 4.
        """
        # Given: the live store on files with cp2.multi at version 6, the copy at version 4 (AC-006), no AutoSync
        folder, live, copy = backend_with(self, {"accounts_enabled": True, "store": "files"})
        wanted = as_json(GraphModel(Storage(FileBackend(copy))).read_graph(ts.MULTI))
        # When: the backend starts and cp2.multi is read and listed through IF-104 v2
        out = started(self, folder, live, copy, """
out = {}
main.start_backend()
""" + LOGIN + """
out["read"] = ask("/api/v2/graphs/cp2.multi")
out["list"] = ask("/api/v2/graphs")
print(json.dumps(out))
""")
        # Then: the answer is the copy's version 4 and its graph
        status, read = out["read"]
        self.assertEqual(status, 200, read)
        self.assertEqual((read["version"], read["current"]), (4, 4))
        self.assertEqual(read["graph"], wanted)
        self.assertEqual([(g["id"], g["version"]) for g in out["list"][1] if g["id"] == ts.MULTI], [(ts.MULTI, 4)])

    @mark.req("REQ-API-061")
    def test_TC_API_061_without_autosync_nothing_is_synced(self):
        """TC-API-061: with `copy` set and no `autosync`, neither the start nor the orderly stop changes the copy.

        Example: copy at version 4, live at 6 -> after the start and after the stop the copy's graph group is entry by entry what it was.
        """
        # Given: `copy` set, no `autosync`; the live store has two newer versions of cp2.multi (AC-006)
        folder, live, copy = backend_with(self, {"accounts_enabled": True, "store": "files"})
        before = as_json(ts.graph_group(FileBackend(copy)))
        # When: the backend starts, answers once and stops in an orderly way
        out = started(self, folder, live, copy, """
out = {}
main.start_backend()
out["after_start"] = group(COPY)
""" + LOGIN + """
out["store"] = ask("/api/v2/store")
main.graceful_shutdown(main.stop_list(), pause=0)
print(json.dumps(out))
""")
        # Then: the copy is unchanged after the start and after the stop
        self.assertEqual(out["after_start"], before)
        self.assertEqual(as_json(ts.graph_group(FileBackend(copy))), before)

    @mark.req("REQ-API-062")
    def test_TC_API_062_autosync_at_start_and_at_an_orderly_stop(self):
        """TC-API-062: with AutoSync on, the copy equals the live store before the first answer and again after the orderly stop.

        Example: live 6, copy 4 -> after the start the copy holds 6 and the read answers 6; version 7 written while running is on the copy after the stop.
        """
        # Given: `copy` set, `autosync` true; the live store has two newer versions of cp2.multi (AC-006)
        folder, live, copy = backend_with(self, {"accounts_enabled": True, "store": "files", "autosync": True})
        live_at_start = as_json(ts.graph_group(FileBackend(live)))
        # When: the backend starts, answers, a new version is written to the live store while it runs, and it stops in an orderly way
        out = started(self, folder, live, copy, """
out = {}
main.start_backend()
out["after_start"] = group(COPY)
""" + LOGIN + """
out["read"] = ask("/api/v2/graphs/cp2.multi")
ts.new_multi_version(FileBackend(LIVE), "c")
main.graceful_shutdown(main.stop_list(), pause=0)
print(json.dumps(out))
""")
        # Then: the newer versions are on the copy before the first answer, and the first read answers version 6
        self.assertEqual(out["after_start"], live_at_start)
        self.assertEqual(out["read"][1]["version"], 6, out["read"])
        # And: the version written while running is on the copy after the stop
        self.assertEqual(len(FileBackend(live).versions("graphs", ts.MULTI)), 7)
        self.assertEqual(as_json(ts.graph_group(FileBackend(copy))), as_json(ts.graph_group(FileBackend(live))))

    @mark.req("REQ-API-063")
    def test_TC_API_063_an_unreachable_live_store_is_reported_not_fatal(self):
        """TC-API-063: with AutoSync on and a live database nobody answers, MIA starts, answers graphs from the copy and logs one line.

        Example: store database at 127.0.0.1:<free port> -> the start goes on, cp2.multi reads version 4 from the copy, one log line names
        127.0.0.1:<port> and "sync not run".
        """
        try:
            import psycopg  # noqa: F401
        except ImportError:
            self.skipTest("psycopg 3 is missing: MIA's database backend cannot be loaded here (requirements-db.txt)")
        # Given: `copy` set (the sample store), `autosync` true, `store` database with an address on a port where nothing listens
        port = free_port()
        folder, live, copy = backend_with(self, {"accounts_enabled": True, "store": "database", "autosync": True},
                                          case=lambda live, copy: ts.sample_store(copy))
        address = "127.0.0.1:%d" % port
        # When: the backend starts and cp2.multi is read
        out = started(self, folder, live, copy, """
out = {}
main.start_backend()
""" + LOGIN + """
out["read"] = ask("/api/v2/graphs/cp2.multi")
print(json.dumps(out))
""", env={"MIA_DATABASE_URL": "postgresql://mia@%s/mia?connect_timeout=3" % address})
        # Then: it starts and answers the graph from the copy
        self.assertEqual(out["read"][0], 200, out["read"])
        self.assertEqual(out["read"][1]["version"], 4)
        # And: its log holds one line naming the live store and "sync not run"
        with open(os.path.join(folder, "MIA", "mia.log"), encoding="utf-8") as f:
            lines = [line for line in f if "sync not run" in line]
        self.assertEqual(len(lines), 1, lines)
        self.assertIn(address, lines[0])

    @mark.req("REQ-API-064")
    def test_TC_API_064_the_store_answer_tells_how_far_the_copy_lags(self):
        """TC-API-064: with `copy` set, GET /api/v2/store answers `shown` copy, the live store reachable, and the lag before and after a sync.

        Example: AC-006 -> before: lag {"graphs": 1, "since": <time of live version 5 of cp2.multi>}; after the sync: {"graphs": 0, "since": null}.
        """
        # Given: the case of AC-006 with `copy` set, no `autosync`
        folder, live, copy = backend_with(self, {"accounts_enabled": True, "store": "files"})
        since = FileBackend(live).versions("graphs", ts.MULTI)[4]["time"]
        # When: GET /api/v2/store is asked before and after a sync of the copy
        out = started(self, folder, live, copy, """
out = {}
main.start_backend()
""" + LOGIN + """
out["before"] = ask("/api/v2/store")
from MIA import graph_store_transfer
from MIA.storage_files import FileBackend as Files
graph_store_transfer.sync_store(Files(LIVE), Files(COPY))
out["after"] = ask("/api/v2/store")
print(json.dumps(out))
""")
        # Then: before: shown copy, live reachable, one graph behind since live version 5 of cp2.multi
        status, before = out["before"]
        self.assertEqual(status, 200, before)
        self.assertEqual((before["shown"], before["live_reachable"], before["lag"]), ("copy", True, {"graphs": 1, "since": since}))
        # And: after: no lag
        status, after = out["after"]
        self.assertEqual(status, 200, after)
        self.assertEqual((after["shown"], after["live_reachable"], after["lag"]), ("copy", True, {"graphs": 0, "since": None}))


if __name__ == "__main__":
    unittest.main()
