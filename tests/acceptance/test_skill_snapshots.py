"""
Acceptance tests of the snapshots of the skill set (G-V2.CONVERT, task T-CV-05): TC-WFM-061 to TC-WFM-066 (REQ-WFM-061 to -066) against SnapshotStore with the
in-memory library and accounts of tests/helpers/snapshot_lab.py. RED until T-CV-05: the stub of snapshot_store.py returns nothing.
Run with: python tests/acceptance/test_skill_snapshots.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                                        # noqa: E402
from snapshot_lab import AccountsLab, LibraryLab, standard_state                # noqa: E402
from snapshot_store import Refused, SnapshotStore                               # noqa: E402

PINS = {"MP-light": "gemma4:12b-it-qat"}


def items_of(lab):
    """the state of the lab in the form of a snapshot's `items`, sorted"""
    out = []
    for kind, i, version, _doc, trust, lifecycle in lab.state():
        item = {"kind": kind, "id": i, "version": version}
        if kind == "transforms":
            item.update(trust=trust, lifecycle=lifecycle)
        out.append(item)
    return sorted(out, key=lambda d: (d["kind"], d["id"]))


def sorted_items(snapshot):
    return sorted(snapshot["items"], key=lambda d: (d["kind"], d["id"]))


def change_four_items(lab):
    """state S2: differs from the standard state in 4 items"""
    lab.save("skills", "research", {"name": "research", "v": 2}, "anna")
    lab.save("workflows", "lookup", {"nodes": ["lookup", "x"], "edges": []}, "anna")
    lab.save("context_graphs", "places", {"nodes": ["places", "y"], "edges": []}, "anna")
    lab.set_lifecycle("t_sum", "retired", "anna")


class SnapshotAcceptance(unittest.TestCase):
    def setUp(self):
        self.lab = LibraryLab(PINS)
        self.accounts = AccountsLab("anna")
        self.accounts.create("anna", "ben")
        standard_state(self.lab)
        self.ticks = iter(range(1000, 9000, 1000))
        self.store = SnapshotStore(self.lab, self.accounts, clock=lambda: next(self.ticks))

    @mark.req("REQ-WFM-061")
    def test_a_snapshot_holds_all_eight_items_with_version_trust_lifecycle_and_the_pin(self):
        """TC-WFM-061: 2 skills + 2 workflow graphs + 1 context graph + 3 transforms = 8 items, each with its version, the transforms also trust and lifecycle; the pin."""
        self.store.snapshot("before-rework", "anna")
        snap = self.store.read_snapshot("before-rework")
        self.assertIsNotNone(snap, "the snapshot 'before-rework' was not stored")
        self.assertEqual(len(snap["items"]), 8)
        self.assertEqual(sorted_items(snap), items_of(self.lab))
        transforms = {i["id"]: i for i in snap["items"] if i["kind"] == "transforms"}
        self.assertEqual({k: (v["trust"], v["lifecycle"]) for k, v in transforms.items()},
                         {"t_sum": ("trusted", "tested"), "t_draft": ("trusted", "draft"), "t_old": ("untrusted", "retired")})
        self.assertEqual(snap["pins"], PINS)

    @mark.req("REQ-WFM-062")
    def test_two_snapshots_are_listed_with_name_time_and_author(self):
        """TC-WFM-062: snapshots "a" (time 1000) and "b" (time 2000) by the owner are listed with exactly the three fields name, time, author."""
        self.store.snapshot("a", "anna")
        self.store.snapshot("b", "anna")
        listed = self.store.list_snapshots("anna")
        self.assertIsNotNone(listed, "list_snapshots gave nothing")
        self.assertEqual(listed, [{"name": "a", "time": 1000, "author": "anna"}, {"name": "b", "time": 2000, "author": "anna"}])

    @mark.req("REQ-WFM-063")
    def test_a_restore_first_keeps_the_current_state_as_a_snapshot_of_its_own(self):
        """TC-WFM-063: restoring "a" first creates "before restore of a" with S2 and the owner as author; the state equals S1; restoring that gives S2 again."""
        s1 = self.lab.state()
        self.store.snapshot("a", "anna")
        change_four_items(self.lab)
        s2, s2_items = self.lab.state(), items_of(self.lab)
        self.assertNotEqual(s1, s2)
        self.store.restore_snapshot("a", "anna")
        auto = self.store.read_snapshot("before restore of a")
        self.assertIsNotNone(auto, "no snapshot named 'before restore of a'")
        self.assertEqual(auto["author"], "anna")
        self.assertEqual(sorted_items(auto), s2_items)
        self.assertEqual(self.lab.state(), s1)
        self.store.restore_snapshot("before restore of a", "anna")
        self.assertEqual(self.lab.state(), s2)

    @mark.req("REQ-WFM-064")
    def test_a_restore_gives_back_version_trust_and_lifecycle_of_each_item(self):
        """TC-WFM-064: a skill (v2), a workflow graph, a context graph, a transform set trusted (untrusted in "a") and another retired: all equal "a" after the restore."""
        self.store.snapshot("a", "anna")
        before = self.lab.state()
        self.lab.save("skills", "research", {"name": "research", "v": 2}, "anna")
        self.lab.save("workflows", "lookup", {"nodes": ["lookup", "x"], "edges": []}, "anna")
        self.lab.save("context_graphs", "places", {"nodes": ["places", "y"], "edges": []}, "anna")
        self.lab.set_trust("t_old", "trusted", "anna")
        self.lab.set_lifecycle("t_draft", "retired", "anna")
        self.assertEqual(len([1 for a, b in zip(before, self.lab.state()) if a != b]), 5)
        self.store.restore_snapshot("a", "anna")
        self.assertEqual(self.lab.state(), before)
        self.assertEqual(self.lab.get_trust("t_old"), "untrusted")

    @mark.req("REQ-WFM-065")
    def test_a_restore_deletes_no_version_of_any_item(self):
        """TC-WFM-065: 8 items with 5 versions each, snapshot at version 2 (older than the last 3); after the restore each list of versions before is a prefix of the one after."""
        lab = self.lab
        for kind, i in [(k, i) for (k, i) in lab.version_lists()]:
            lab.save(kind, i, {"again": 2}, "anna")                  # version 2 of every item
        self.store.snapshot("a", "anna")
        for kind, i in [(k, i) for (k, i) in lab.version_lists()]:
            for n in (3, 4, 5):
                lab.save(kind, i, {"again": n}, "anna")
        before = lab.version_lists()
        self.assertEqual(len(before), 8)
        self.assertTrue(all(v == [1, 2, 3, 4, 5] for v in before.values()))
        self.store.restore_snapshot("a", "anna")
        self.assertTrue(all(lab.read(k, i)["version"] == 2 for (k, i) in before), "the restore did not take place")
        after = lab.version_lists()
        for key, versions in before.items():
            self.assertEqual(after[key][:len(versions)], versions, "versions of %s lost" % (key,))

    @mark.req("REQ-WFM-066")
    def test_only_the_owner_takes_and_restores_a_snapshot(self):
        """TC-WFM-066: ben (created by the owner anna) is refused for take and restore, snapshots and state stay; anna succeeds."""
        self.store.snapshot("a", "anna")
        change_four_items(self.lab)
        state, listed = self.lab.state(), self.store.list_snapshots("anna")
        self.assertIsNotNone(listed, "list_snapshots gave nothing")
        self.assertEqual([s["name"] for s in listed], ["a"])
        with self.assertRaises(Refused):
            self.store.snapshot("b", "ben")
        with self.assertRaises(Refused):
            self.store.restore_snapshot("a", "ben")
        self.assertEqual(self.lab.state(), state)
        self.assertEqual(self.store.list_snapshots("anna"), listed)
        self.store.snapshot("b", "anna")
        self.store.restore_snapshot("a", "anna")
        self.assertEqual([s["name"] for s in self.store.list_snapshots("anna")][:2], ["a", "b"])
        self.assertNotEqual(self.lab.state(), state)


if __name__ == "__main__":
    unittest.main()
