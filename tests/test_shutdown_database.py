"""Orderly shutdown with the database (N-4.2 T-02): TC-OPR-004, REQ-OPR-004. Run with: python tests/test_shutdown_database.py"""

import importlib
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

# the code uses relative imports as package "MIA": make the repository importable under that name
import checkout_copy  # noqa: E402  (MIA from a temporary copy: nothing is written into the checkout, D-169)
_LINK_DIR = checkout_copy.use()

from markers import mark                         # noqa: E402

HISTORY = [{"role": "user", "content": "my door is blue"}, {"role": "assistant", "content": "I will remember the blue door."}]


class FakeBackend:
    """a database backend that only counts close() (the PostgreSQL backend has one, the file backend has none)"""

    def __init__(self):
        self.closed = 0

    def close(self):
        self.closed += 1


class CloseDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sd = importlib.import_module("MIA.shutdown")
        cls.storage = importlib.import_module("MIA.storage")
        cls.files = importlib.import_module("MIA.storage_files")

    @mark.req("REQ-OPR-004")
    def test_the_backend_of_the_database_is_closed_once(self):
        """TC-OPR-004: close_database closes the backend of the database exactly once.

        Example: Storage(FakeBackend()) -> backend.closed == 1.
        """
        # Given: a database whose backend can be closed
        backend = FakeBackend()
        storage = self.storage.Storage(backend)
        # When: the shutdown closes the database
        self.sd.close_database(storage)
        # Then: the backend was closed once
        self.assertEqual(backend.closed, 1)

    @mark.req("REQ-OPR-004")
    def test_a_file_database_and_no_database_need_nothing(self):
        """TC-OPR-004: a file database (no close) and no database at all are left alone without an error.

        Example: Storage(FileBackend(folder)) and None -> None, no exception.
        """
        # Given: a file database and no database
        with tempfile.TemporaryDirectory() as folder:
            storage = self.storage.Storage(self.files.FileBackend(folder))
            # When: the shutdown closes them
            results = [self.sd.close_database(storage), self.sd.close_database(None)]
        # Then: nothing happens
        self.assertEqual(results, [None, None])


class SavedOnEveryStop(unittest.TestCase):
    """the stand-in for MIA's main process (tests/shutdown_harness.py) with a history and a file database, stopped with real signals"""

    def run_harness(self, how, data, pause=0.2):
        log = os.path.join(data, "log.txt")
        harness = subprocess.Popen([sys.executable, os.path.join(HERE, "shutdown_harness.py"), _LINK_DIR, log, str(pause), data],
                                   stdout=subprocess.PIPE, start_new_session=True)
        self.assertEqual(harness.stdout.readline().strip(), b"ready")
        if how == "ctrl-c":     # the terminal sends SIGINT to the whole foreground group of MIA
            os.killpg(harness.pid, signal.SIGINT)
        elif how == "goodnight":    # /goodnight! (after dreaming) and /break! signal only MIA itself
            os.kill(harness.pid, signal.SIGINT)
        elif how == "sigterm":
            os.kill(harness.pid, signal.SIGTERM)
        self.assertEqual(harness.wait(timeout=20), 0)
        harness.stdout.close()
        with open(log) as fp:
            return fp.read()

    def next_start(self, data):
        """what a new start finds: (the saved history, the texts of the memory records in the database)"""
        with open(os.path.join(data, "memories.json")) as fp:
            history = json.load(fp)
        storage = importlib.import_module("MIA.storage").Storage(importlib.import_module("MIA.storage_files").FileBackend(os.path.join(data, "db")))
        texts = [storage.get("memory", record_id)["doc"]["text"] for record_id in storage.ids("memory")]
        return history, texts

    def check_stop(self, how):
        with tempfile.TemporaryDirectory() as data:
            text = self.run_harness(how, data)
            steps = [line.split(" at ")[0] for line in text.splitlines()]
            history, texts = self.next_start(data)
        return steps, history, texts

    @mark.req("REQ-OPR-004")
    def test_sigterm_saves_history_and_memory(self):
        """TC-OPR-004: after SIGTERM the history and the memory record are saved and identical on the next start.

        Example: SIGTERM -> memories.json equals HISTORY, the database holds "the door is blue".
        """
        # Given: a running stand-in of MIA with a history and one memory record
        # When: it gets SIGTERM
        steps, history, texts = self.check_stop("sigterm")
        # Then: history saved, then the database closed, then the helpers stopped; the next start finds the same history and memory
        self.assertEqual(steps[-5:], ["history saved", "database closed", "proxy got SIGTERM", "speech got SIGTERM", "harness done"])
        self.assertEqual(history, HISTORY)
        self.assertEqual(texts, ["the door is blue"])

    @mark.req("REQ-OPR-004")
    def test_ctrl_c_saves_history_and_memory(self):
        """TC-OPR-004: after Ctrl+C in the terminal the history and the memory record are saved and identical on the next start.

        Example: Ctrl+C -> memories.json equals HISTORY, the database holds "the door is blue".
        """
        # Given: a running stand-in of MIA with a history and one memory record
        # When: Ctrl+C reaches its process group
        steps, history, texts = self.check_stop("ctrl-c")
        # Then: history saved, then the database closed, then the helpers stopped; the next start finds the same history and memory
        self.assertEqual(steps[-5:], ["history saved", "database closed", "proxy got SIGTERM", "speech got SIGTERM", "harness done"])
        self.assertEqual(history, HISTORY)
        self.assertEqual(texts, ["the door is blue"])

    @mark.req("REQ-OPR-004")
    def test_goodnight_saves_history_and_memory(self):
        """TC-OPR-004: after /goodnight! (which ends in the same request as /break!) the history and the memory record are saved and identical on the next start.

        Example: /goodnight! -> memories.json equals HISTORY, the database holds "the door is blue".
        """
        # Given: a running stand-in of MIA with a history and one memory record
        # When: /goodnight! asks it to shut down
        steps, history, texts = self.check_stop("goodnight")
        # Then: history saved, then the database closed, then the helpers stopped; the next start finds the same history and memory
        self.assertEqual(steps[-5:], ["history saved", "database closed", "proxy got SIGTERM", "speech got SIGTERM", "harness done"])
        self.assertEqual(history, HISTORY)
        self.assertEqual(texts, ["the door is blue"])

if __name__ == "__main__":
    unittest.main()
