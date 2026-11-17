"""SnapshotStore beyond the acceptance tests (T-SN-01): the refusals of A-121 that TC-WFM-061 to 066 do not name.
Run with: python tests/test_snapshot_store.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from snapshot_lab import AccountsLab, LibraryLab, standard_state    # noqa: E402
from snapshot_store import NotFound, Refused, SnapshotStore       # noqa: E402


class Refusals(unittest.TestCase):
    def setUp(self):
        self.lab = LibraryLab({"MP-light": "gemma4:12b-it-qat"})
        standard_state(self.lab)
        self.store = SnapshotStore(self.lab, AccountsLab("anna"))

    def test_an_empty_or_missing_name_is_refused_and_nothing_is_written(self):
        for name in ("", None):
            with self.assertRaises(ValueError):
                self.store.snapshot(name, "anna")
        self.assertEqual(self.lab.list_ids("snapshots"), [])

    def test_an_unknown_snapshot_is_not_found_and_changes_nothing(self):
        state = self.lab.state()
        for call in (lambda: self.store.read_snapshot("none"), lambda: self.store.restore_snapshot("none", "anna")):
            with self.assertRaises(NotFound):
                call()
        self.assertEqual((self.lab.state(), self.lab.list_ids("snapshots")), (state, []))

    def test_the_owner_check_comes_before_anything_is_looked_up(self):
        self.store.snapshot("a", "anna")
        with self.assertRaises(Refused):
            self.store.restore_snapshot("none", "ben")       # a stranger learns nothing about which names exist
        with self.assertRaises(Refused):
            self.store.list_snapshots("ben")


if __name__ == "__main__":
    unittest.main()
