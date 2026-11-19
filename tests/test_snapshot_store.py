"""SnapshotStore beyond the acceptance tests (T-SN-01): the refusals of A-121 that TC-WFM-061 to 066 do not name.
Run with: python tests/test_snapshot_store.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from snapshot_lab import AccountsLab, LibraryLab, standard_state    # noqa: E402
from snapshot_store import InvalidName, Malformed, NotFound, Refused, SnapshotStore       # noqa: E402


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


class Verify(unittest.TestCase):
    """the findings F-03 and F-04 of the verification of G-V2.SNAPSHOT"""
    def setUp(self):
        self.lab = LibraryLab({"MP-light": "gemma4:12b-it-qat"})
        standard_state(self.lab)

    def test_f03_the_list_is_oldest_first_by_time_not_by_name(self):
        ticks = iter(range(10, 100))
        store = SnapshotStore(self.lab, AccountsLab("anna"), clock=lambda: next(ticks))
        store.snapshot("b", "anna")
        store.snapshot("a", "anna")
        self.assertEqual([s["name"] for s in store.list_snapshots("anna")], ["b", "a"])

    def test_f04_an_empty_name_is_a_name_error_and_only_that(self):
        self.assertTrue(issubclass(InvalidName, ValueError))
        with self.assertRaises(InvalidName):
            SnapshotStore(self.lab, AccountsLab("anna")).snapshot("", "anna")

    def test_f04_a_malformed_stored_snapshot_is_refused_before_anything_is_written(self):
        store = SnapshotStore(self.lab, AccountsLab("anna"))
        store.snapshot("a", "anna")
        doc = store.read_snapshot("a")
        doc["items"] = [dict(i) for i in doc["items"]]
        broken = next(i for i in doc["items"] if i["kind"] == "transforms")
        del broken["trust"]
        self.lab.save("snapshots", "bad", dict(doc, name="bad"), "anna")
        state, names = self.lab.state(), self.lab.list_ids("snapshots")
        with self.assertRaises(Malformed):
            store.restore_snapshot("bad", "anna")
        self.assertEqual((self.lab.state(), self.lab.list_ids("snapshots")), (state, names))      # no "before restore" snapshot, no move

    def test_f04_a_failure_of_the_way_back_does_not_replace_the_original_error(self):
        store = SnapshotStore(self.lab, AccountsLab("anna"))
        store.snapshot("a", "anna")
        self.lab.save("skills", "research", {"id": "research", "data": {"command": "x", "workflow_graph_id": "lookup", "context_graph_id": "places"}}, "anna")
        real, calls = self.lab.set_current_version, []

        def flaky(kind, record_id, version, author):
            calls.append(record_id)
            if len(calls) == 1:
                real(kind, record_id, version, author)
                raise RuntimeError("forward")          # the first item moved, then the failure
            raise OSError("way back")                  # the rollback fails as well
        self.lab.set_current_version = flaky
        with self.assertRaises(RuntimeError) as caught:
            store.restore_snapshot("a", "anna")
        self.assertEqual(str(caught.exception), "forward")


if __name__ == "__main__":
    unittest.main()
