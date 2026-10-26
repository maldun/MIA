"""Copying records between backends: library export and seed (N-3.1 T-04, TC-SLY-009) and the migration (T-05, TC-SLY-007, file side). Run with: python tests/test_storage_copy.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from markers import mark                                             # noqa: E402
from storage import Storage, StorageError                            # noqa: E402
from storage_copy import copy_records, export_library, seed_library  # noqa: E402
from storage_files import FileBackend                                # noqa: E402

LOOKUP = {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process"}, {"id": "a", "kind": "data"}],
          "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "a"}]}


def tree(folder):
    """{relative path: canonical JSON} of every file below the folder."""
    out = {}
    for root, _, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as handle:
                out[os.path.relpath(path, folder)] = json.dumps(json.load(handle), sort_keys=True, ensure_ascii=False)
    return out


class Copy(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base, True)
        self.path = lambda name: os.path.join(self.base, name)
        self.store = Storage(FileBackend(self.path("a")))
        self.store.put("workflows", "lookup", LOOKUP, "anna")
        self.store.put("workflows", "lookup", dict(LOOKUP, note="v2"), "ben")
        self.store.put("workflows", "verify", LOOKUP, "anna")
        self.store.put("context_graphs", "chat", LOOKUP, "anna")
        self.store.put("memos", "a/b", {"text": "Zoë\n✓"}, "anna")
        self.store.put("votes", "v1", {"user": "anna", "subject": "m", "category": "service", "value": 1}, "anna")

    @mark.req("REQ-SLY-009")
    def test_export_then_seed_gives_identical_entries(self):
        """TC-SLY-009: ids, versions, authors, times and documents are the same in an empty library."""
        export_library(self.store, self.path("export"))
        fresh = Storage(FileBackend(self.path("b")))
        seed_library(fresh, self.path("export"))
        for table in ("workflows", "context_graphs"):
            self.assertEqual(fresh.ids(table), self.store.ids(table))
            for record_id in fresh.ids(table):
                self.assertEqual(fresh.backend.versions(table, record_id), self.store.backend.versions(table, record_id))
        self.assertEqual(fresh.ids("memos"), [])                                     # only the library travels

    @mark.req("REQ-SLY-009")
    def test_the_seeded_library_keeps_counting_from_the_old_versions(self):
        export_library(self.store, self.path("export"))
        fresh = Storage(FileBackend(self.path("b")))
        seed_library(fresh, self.path("export"))
        self.assertEqual(fresh.put("workflows", "lookup", LOOKUP, "anna"), {"version": 3})

    @mark.req("REQ-SLY-007")
    def test_a_round_trip_through_two_other_folders_is_identical_file_by_file(self):
        """TC-SLY-007 (file side): a to b to c, every file equal in canonical JSON."""
        tables = list(self.store.tables)
        copy_records(self.store.backend, FileBackend(self.path("b")), tables)
        copy_records(FileBackend(self.path("b")), FileBackend(self.path("c")), tables)
        self.assertEqual(tree(self.path("c")), tree(self.path("a")))
        self.assertGreaterEqual(len(tree(self.path("a"))), 5)

    @mark.req("REQ-SLY-007")
    def test_a_second_run_changes_nothing_and_a_longer_source_adds_the_missing_versions(self):
        """Idempotent: the same copy twice is a no-op; a source with more versions appends only those."""
        tables = list(self.store.tables)
        target = FileBackend(self.path("b"))
        self.assertEqual(copy_records(self.store.backend, target, tables)["copied"], 5)       # five records, six versions
        before = tree(self.path("b"))
        self.assertEqual(copy_records(self.store.backend, target, tables), {"copied": 0, "skipped": 5, "added_versions": 0})
        self.assertEqual(tree(self.path("b")), before)
        self.store.put("workflows", "lookup", LOOKUP, "anna")
        self.assertEqual(copy_records(self.store.backend, target, tables)["added_versions"], 1)
        self.assertEqual(Storage(target).get("workflows", "lookup")["version"], 3)

    @mark.req("REQ-SLY-007")
    def test_a_target_with_a_different_history_is_a_conflict_and_nothing_is_written(self):
        other = Storage(FileBackend(self.path("b")))
        other.put("workflows", "lookup", dict(LOOKUP, note="another"), "carl")
        before = tree(self.path("b"))
        with self.assertRaises(StorageError) as caught:
            copy_records(self.store.backend, other.backend, list(self.store.tables))
        self.assertEqual(caught.exception.code, "conflict")
        self.assertEqual(tree(self.path("b")), before)

    @mark.req("REQ-SLY-007")
    def test_an_unknown_table_is_refused(self):
        with self.assertRaises(StorageError):
            copy_records(self.store.backend, FileBackend(self.path("b")), ["nope"])


if __name__ == "__main__":
    unittest.main()
