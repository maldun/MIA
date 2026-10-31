"""The Storage layer on the file backend (N-3.1 T-01, T-02): TC-SLY-002, -003, -004, -006 (files) and the behaviour of IF-102. Run with: python tests/test_storage.py"""
import os
import random
import shutil
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from markers import mark                         # noqa: E402
from storage import Storage, StorageError        # noqa: E402
from storage_files import FileBackend            # noqa: E402

LOOKUP = {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process"}, {"id": "a", "kind": "data"}],
          "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "a"}]}
CYCLE = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
ONE_OF_EACH = {"workflows": LOOKUP, "context_graphs": LOOKUP, "history": {"role": "user", "text": "hi"}, "memory": {"text": "likes tea", "source": "chat"},
               "votes": {"user": "anna", "subject": "m1", "category": "service", "value": -1}, "tasks": {"text": "water the plants"}, "memos": {"text": "x\ty"},
               "accounts": {"name": "anna", "hash": "h"}, "presets": {"name": "calm"}, "gestures": {"name": "wave"},
               "runs": {"workflow": "lookup", "workflow_version": 1, "model_pin": "MP-light", "benchmark_version": "B1"}, "source_trust": {"trust": 0.5}}


def code_of(call):
    try:
        call()
    except StorageError as err:
        return err.code, err.rule
    raise AssertionError("no StorageError raised")


class StorageBehaviour:
    """The behaviour of the Storage layer, the same on every backend. A test class mixes it with unittest.TestCase and says
    new_backend(label): a backend that is empty (a different label is a different, independent store) and reopen(): a new backend on the same data."""

    def setUp(self):
        self.store = Storage(self.new_backend("main"))

    @mark.req("REQ-SLY-002")
    def test_a_record_of_each_table_reads_back_equal(self):
        """TC-SLY-002 (file backend)."""
        for table, doc in ONE_OF_EACH.items():
            self.store.put(table, "k1", doc, "anna")
            entry = self.store.get(table, "k1")
            self.assertEqual((entry["doc"], entry["version"], entry["author"], entry["id"]), (doc, 1, "anna", "k1"), table)

    @mark.req("REQ-SLY-002")
    def test_a_new_storage_on_the_same_folder_sees_the_records(self):
        """The records are on disk, not in memory."""
        self.store.put("memory", "m", {"text": "t", "source": "s"}, "anna")
        again = Storage(self.reopen())
        self.assertEqual(again.ids("memory"), ["m"])
        self.assertEqual(again.get("memory", "m")["doc"], {"text": "t", "source": "s"})

    @mark.req("REQ-SLY-002")
    def test_ids_with_odd_characters_and_text_byte_for_byte(self):
        """An id with a slash, a dot or a non-ASCII letter is a record, not a path; the text comes back unchanged."""
        text = "Call Zoë at 9:00 – bring \"the\" notes\n\tdone ✓"
        for record_id in ("a/b", "..", "ä ö", "x" * 150):
            self.store.put("memos", record_id, {"text": text}, "anna")
            self.assertEqual(self.store.get("memos", record_id)["doc"]["text"], text)
        self.assertEqual(sorted(self.store.ids("memos")), sorted(["a/b", "..", "ä ö", "x" * 150]))

    @mark.req("REQ-SLY-003")
    @mark.statistical
    def test_versions_run_without_gap_and_never_change(self):
        """TC-SLY-003: 500 random sequences (seeds 1 to 500) of put, get(version) and history."""
        for seed in range(1, 501):
            rng = random.Random(seed)
            store = Storage(self.new_backend("s%d" % seed))
            written = {}
            for _ in range(rng.randint(1, 8)):
                rid = rng.choice("abc")
                doc = {"text": "v%d" % rng.randint(0, 99)}
                number = store.put("tasks", rid, doc, rng.choice(("anna", "ben")))["version"]
                written.setdefault(rid, []).append(doc)
                self.assertEqual(number, len(written[rid]), seed)
                for rid_, docs in written.items():
                    self.assertEqual([h["version"] for h in store.history("tasks", rid_)], list(range(1, len(docs) + 1)), seed)
                    for k, expected in enumerate(docs, 1):
                        self.assertEqual(store.get("tasks", rid_, version=k)["doc"], expected, (seed, rid_, k))

    @mark.req("REQ-SLY-003")
    def test_conflict_not_found_and_unknown_table(self):
        """IF-102 errors: nothing changes after a refusal."""
        self.store.put("tasks", "t", {"text": "a"}, "anna")
        self.assertEqual(code_of(lambda: self.store.put("tasks", "t", {"text": "b"}, "anna", expected_version=3))[0], "conflict")
        self.assertEqual(self.store.get("tasks", "t")["version"], 1)
        self.assertEqual(self.store.put("tasks", "new", {"text": "x"}, "anna", expected_version=0), {"version": 1})
        self.assertEqual(code_of(lambda: self.store.get("tasks", "ghost"))[0], "not_found")
        self.assertEqual(code_of(lambda: self.store.get("tasks", "t", version=2))[0], "not_found")
        self.assertEqual(code_of(lambda: self.store.history("tasks", "ghost"))[0], "not_found")
        self.assertEqual(code_of(lambda: self.store.ids("nope"))[0], "unknown_table")
        self.assertEqual(code_of(lambda: self.store.put("nope", "x", {}, "anna"))[0], "unknown_table")

    @mark.req("REQ-SLY-003")
    def test_the_conflict_names_the_current_version(self):
        self.store.put("tasks", "t", {"text": "a"}, "anna")
        try:
            self.store.put("tasks", "t", {"text": "b"}, "anna", expected_version=5)
        except StorageError as err:
            self.assertEqual(err.detail, {"current": 1})

    @mark.req("REQ-SLY-003")
    def test_only_the_tables_that_allow_it_can_be_deleted(self):
        """The definitions of IF-301 and IF-302 decide: memory is deletable, workflows and votes are not."""
        self.store.put("memory", "m", {"text": "t", "source": "s"}, "anna")
        self.store.delete("memory", "m", "anna")
        self.assertEqual(self.store.ids("memory"), [])
        for table in ("workflows", "votes", "accounts"):
            self.store.put(table, "k", ONE_OF_EACH[table], "anna")
            self.assertEqual(code_of(lambda: self.store.delete(table, "k", "anna"))[0], "immutable", table)
            self.assertEqual(self.store.ids(table), ["k"])
        self.assertEqual(code_of(lambda: self.store.delete("memory", "m", "anna"))[0], "not_found")

    @mark.req("REQ-SLY-006")
    def test_a_subscriber_is_told_once_per_write_and_not_after_unsubscribe(self):
        """TC-SLY-006 (files, in process): table, id, version and author; one notice per write."""
        heard = []
        stop = self.store.subscribe("tasks", heard.append)
        self.store.put("tasks", "t", {"text": "a"}, "anna")
        self.store.put("tasks", "t", {"text": "b"}, "ben")
        self.store.put("memos", "m", {"text": "other table"}, "anna")
        self.assertEqual(heard, [{"table": "tasks", "id": "t", "version": 1, "author": "anna"}, {"table": "tasks", "id": "t", "version": 2, "author": "ben"}])
        stop()
        self.store.put("tasks", "t", {"text": "c"}, "anna")
        self.assertEqual(len(heard), 2)

    @mark.req("REQ-SLY-006")
    def test_a_raising_subscriber_does_not_stop_the_others_or_the_write(self):
        """Finding F2 of the verification: one bad subscriber is logged and skipped.
        Example: subscribers [raises, records]; put("tasks", "t") returns version 1 and the second one hears version 1."""
        # Given: a subscriber that raises before one that records
        def broken(event):
            raise RuntimeError("a bad page")
        heard = []
        self.store.subscribe("tasks", broken)
        self.store.subscribe("tasks", heard.append)
        # When: two writes
        with self.assertLogs("storage", "ERROR"):
            first = self.store.put("tasks", "t", {"text": "a"}, "anna")
            self.store.put("tasks", "t", {"text": "b"}, "anna")
        # Then: both writes return and the second subscriber hears both
        self.assertEqual(first, {"version": 1})
        self.assertEqual([e["version"] for e in heard], [1, 2])

    @mark.req("REQ-SLY-006")
    def test_a_delete_is_a_change_and_is_told_with_version_none(self):
        """Finding F7 of the verification, decision D-158: a delete sends a notice, as IF-102 says "after every write".
        Example: delete("memos", "m", "ben") tells a subscriber {"table": "memos", "id": "m", "version": None, "author": "ben"}."""
        # Given: a memo and a subscriber of the memos
        self.store.put("memos", "m", {"text": "x"}, "anna")
        heard = []
        self.store.subscribe("memos", heard.append)
        # When: the memo is deleted, and a refused delete follows
        self.store.delete("memos", "m", "ben")
        code_of(lambda: self.store.delete("memos", "m", "ben"))
        # Then: one notice, for the delete that happened
        self.assertEqual(heard, [{"table": "memos", "id": "m", "version": None, "author": "ben"}])

    @mark.req("REQ-SLY-006")
    def test_a_notice_reaches_a_subscriber_on_another_thread_within_2_s(self):
        """TC-SLY-006: the writer is on one thread, the subscriber's callback runs and is seen from another."""
        got, seen = [], threading.Event()
        self.store.subscribe("tasks", lambda event: (got.append(event), seen.set()))
        started = time.perf_counter()
        threading.Thread(target=lambda: self.store.put("tasks", "t", {"text": "a"}, "anna")).start()
        self.assertTrue(seen.wait(2))
        self.assertLess(time.perf_counter() - started, 2)
        self.assertEqual(got[0]["author"], "anna")

    @mark.req("REQ-SLY-003")
    def test_parallel_writers_never_get_the_same_version(self):
        """Ten threads put to one record: versions 1 to 10 each once."""
        results = []
        threads = [threading.Thread(target=lambda n=n: results.append(self.store.put("tasks", "t", {"text": str(n)}, "anna")["version"])) for n in range(10)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(sorted(results), list(range(1, 11)))

    @mark.req("REQ-SLY-004")
    def test_invalid_documents_are_refused_with_the_rule_and_nothing_is_stored(self):
        """TC-SLY-004: a cycle, two adjacent data nodes and a vote with category mood are refused; the valid workflow is version 1."""
        adjacent = {"nodes": [{"id": "a", "kind": "data"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}]}
        vote = dict(ONE_OF_EACH["votes"], category="mood")
        self.assertEqual(code_of(lambda: self.store.put("workflows", "bad", CYCLE, "anna")), ("invalid", "cycle"))
        self.assertEqual(code_of(lambda: self.store.put("context_graphs", "bad", adjacent, "anna")), ("invalid", "adjacent_data_nodes"))
        self.assertEqual(code_of(lambda: self.store.put("votes", "v", vote, "anna")), ("invalid", "category"))
        self.assertEqual((self.store.ids("workflows"), self.store.ids("context_graphs"), self.store.ids("votes")), ([], [], []))
        self.assertEqual(self.store.put("workflows", "lookup", LOOKUP, "anna"), {"version": 1})

    @mark.req("REQ-SLY-004")
    def test_a_refused_edit_consumes_no_version(self):
        self.store.put("workflows", "w", LOOKUP, "anna")
        code_of(lambda: self.store.put("workflows", "w", CYCLE, "anna"))
        self.assertEqual(self.store.put("workflows", "w", LOOKUP, "ben"), {"version": 2})


class FileStorage(StorageBehaviour, unittest.TestCase):
    def new_backend(self, label):
        if not hasattr(self, "dir"):
            self.dir = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, self.dir, True)
        self.main = FileBackend(os.path.join(self.dir, label))
        return self.main

    def reopen(self):
        return FileBackend(self.main.root)


    @mark.req("REQ-SLY-006")
    def test_a_raising_subscriber_does_not_stop_the_notice_to_the_other_instances(self):
        """Finding F2: put tells the shared channel even when a subscriber of this instance raises.
        Example: a backend with publish() and a raising subscriber; after put the channel got one notice of version 1."""
        # Given: a file backend with a channel, and a raising subscriber
        published = []
        backend = self.new_backend("channel")
        backend.publish = published.append
        store = Storage(backend)
        store.subscribe("tasks", lambda event: 1 / 0)
        # When: one write
        with self.assertLogs("storage", "ERROR"):
            store.put("tasks", "t", {"text": "a"}, "anna")
        # Then: the channel has the notice
        self.assertEqual([(e["id"], e["version"]) for e in published], [("t", 1)])

if __name__ == "__main__":
    unittest.main()
