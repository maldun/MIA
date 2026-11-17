"""IF-203 v2, the pointer and the snapshots of the workflow library (G-V2.SNAPSHOT, A-121, D-241, D-243): the contract suite runs against the mock (stage 1) and the real Workflow
management (stage 2, red until T-SN-01 of G-V2.SNAPSHOT builds it). Protected after the Plan gate.
Run with: python tests/acceptance/contract/test_if_203_v2_snapshots.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402
from errors import ServiceError                             # noqa: E402
from if_203_snapshots import SnapshotLibraryMock            # noqa: E402

IF = "IF-203"
OWNER, OTHER = "anna", "ben"      # the owner is the account that creates accounts (REQ-WFM-066); OTHER was created by it


def make(kind):
    return SnapshotLibraryMock(owner=OWNER) if kind == "mock" else subject_for(IF, kind)      # the real library of v1 has no pointer and no snapshots: red until T-SN-01


def skill_doc(record_id, n=1):
    """a record of IF-301 v2 (`{"id", "data"}`), valid for the real Storage and the mock alike; `n` changes the content"""
    return {"id": record_id, "data": {"command": "%s%s" % (record_id, n if n > 1 else ""), "workflow_graph_id": "lookup", "context_graph_id": "places"}}


def graph_doc(note=""):
    """a graph that passes the graph rules of IF-102 (data, process, data): valid for the real Storage and the mock alike"""
    return {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process", "note": note}, {"id": "r", "kind": "data"}], "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "r"}]}


def error_of(call):
    try:
        call()
    except ServiceError as err:
        return err
    raise AssertionError("no ServiceError raised")


def standard_state(lib):
    """golden 8: 2 skills, 2 workflow graphs, 1 context graph, 3 transforms (trusted tested, trusted draft, untrusted retired)"""
    for i in ("research", "verify_claim"):
        lib.save("skills", i, skill_doc(i), OWNER)
    for i in ("lookup", "compare"):
        lib.save("workflows", i, graph_doc(i), OWNER)
    lib.save("context_graphs", "places", graph_doc("places"), OWNER)
    for i, trust, lifecycle in (("t_sum", "trusted", "tested"), ("t_draft", "trusted", "draft"), ("t_old", "untrusted", "retired")):
        lib.save("transforms", i, {"id": i, "version": 1, "code": "def run(a):\n    return 1\n"}, OWNER)
        lib.set_trust(i, trust, OWNER)
        lib.set_lifecycle(i, lifecycle, OWNER, evidence="run-1" if lifecycle == "tested" else None)


def state(lib):
    """the skill set as one comparable value: (kind, id, current version, doc, trust, lifecycle) per item"""
    rows = []
    for kind in ("skills", "workflows", "context_graphs", "transforms"):
        for i in lib.list_ids(kind):
            e = lib.read(kind, i)
            rows.append((kind, i, e["version"], repr(e["doc"]), e.get("trust"), e.get("lifecycle")))
    return rows


def versions(lib):
    return {(k, i): [h["version"] for h in lib.history(k, i)] for k in ("skills", "workflows", "context_graphs", "transforms") for i in lib.list_ids(k)}


def change_everything(lib):
    """S2: a skill, a workflow graph, a context graph get a new version, a transform changes its status"""
    lib.save("skills", "research", skill_doc("research", 2), OWNER)
    lib.save("workflows", "lookup", graph_doc("lookup, edited"), OWNER)
    lib.save("context_graphs", "places", graph_doc("places, edited"), OWNER)
    lib.set_trust("t_old", "trusted", OWNER)
    lib.set_lifecycle("t_old", "tested", OWNER, evidence="run-2")


@contract
class SnapshotsContract(unittest.TestCase):
    @mark.req("IF-203", "REQ-WFM-064", "REQ-WFM-065")
    @each_provider(IF, make)
    def test_the_pointer_moves_without_creating_or_deleting_a_version(self, lib):
        """TC-IF-203-10 (v2) D-241 D-b: save writes version 2, read without a version gives the current one; set_current_version(…, 1) makes version 1 current and creates nothing; restore keeps its v0 meaning (a new version with the old content); a save after a pointer move writes max+1 and moves the pointer; expected_version is checked against the current version."""
        lib.save("skills", "s", skill_doc("s", 1), OWNER)
        lib.save("skills", "s", skill_doc("s", 2), OWNER)
        self.assertEqual(lib.read("skills", "s")["version"], 2)
        self.assertEqual(lib.set_current_version("skills", "s", 1, OWNER), {"version": 1})
        self.assertEqual((lib.read("skills", "s")["version"], lib.read("skills", "s")["doc"]), (1, skill_doc("s", 1)))
        self.assertEqual([h["version"] for h in lib.history("skills", "s")], [1, 2])
        self.assertEqual(lib.read("skills", "s", 2)["doc"], skill_doc("s", 2))      # an explicit version still reads its own document
        err = error_of(lambda: lib.save("skills", "s", skill_doc("s", 3), OWNER, expected_version=2))      # the current version is 1, not the newest
        self.assertEqual((err.code, err.detail), ("conflict", {"current": 1}))
        self.assertEqual(lib.save("skills", "s", skill_doc("s", 3), OWNER, expected_version=1), {"version": 3})      # max+1, the pointer follows
        self.assertEqual(lib.read("skills", "s")["version"], 3)
        self.assertEqual(lib.restore("skills", "s", 1, OWNER), {"version": 4})
        self.assertEqual((lib.read("skills", "s")["version"], lib.read("skills", "s")["doc"]), (4, skill_doc("s", 1)))

    @mark.req("IF-203", "REQ-WFM-064")
    @each_provider(IF, make)
    def test_a_pointer_move_to_a_missing_version_or_item_is_refused(self, lib):
        """TC-IF-203-11 (v2): set_current_version to a version that does not exist (0, 3, a boolean, a text) is invalid/schema; an unknown id or kind is not_found; the pointer stays."""
        lib.save("skills", "s", skill_doc("s", 1), OWNER)
        lib.save("skills", "s", skill_doc("s", 2), OWNER)
        for version in (0, 3, True, "1", None):
            err = error_of(lambda: lib.set_current_version("skills", "s", version, OWNER))
            self.assertEqual((err.code, err.rule), ("invalid", "schema"), version)
        for call in (lambda: lib.set_current_version("skills", "none", 1, OWNER), lambda: lib.set_current_version("nothing", "s", 1, OWNER)):
            self.assertEqual(error_of(call).code, "not_found")
        self.assertEqual(lib.read("skills", "s")["version"], 2)

    @mark.req("IF-203", "REQ-WFM-061", "REQ-WFM-066")
    @each_provider(IF, make)
    def test_a_snapshot_holds_every_item_with_version_trust_lifecycle_and_the_pins(self, lib):
        """TC-IF-203-12 (v2) golden 8: with 2 skills, 2 workflow graphs, 1 context graph and 3 transforms, snapshot("before-rework") gives {name, time, author}; read_snapshot has 8 items with versions, the transforms with trust and lifecycle (and only they), and the pin MP-light.
        Hand check: 2 + 2 + 1 + 3 = 8 items; t_sum is trusted and tested, t_old untrusted and retired."""
        standard_state(lib)
        made = lib.snapshot("before-rework", OWNER)
        self.assertEqual(set(made), {"name", "time", "author"})
        self.assertEqual((made["name"], made["author"]), ("before-rework", OWNER))
        shot = lib.read_snapshot("before-rework")
        self.assertEqual(len(shot["items"]), 8)
        by = {(i["kind"], i["id"]): i for i in shot["items"]}
        self.assertEqual({k: v["version"] for k, v in by.items()}, {k: 1 for k in by})
        self.assertEqual((by[("transforms", "t_sum")]["trust"], by[("transforms", "t_sum")]["lifecycle"]), ("trusted", "tested"))
        self.assertEqual((by[("transforms", "t_old")]["trust"], by[("transforms", "t_old")]["lifecycle"]), ("untrusted", "retired"))
        self.assertTrue(all("trust" not in v and "lifecycle" not in v for k, v in by.items() if k[0] != "transforms"))
        self.assertIn("MP-light", shot["pins"])
        self.assertEqual({k: shot[k] for k in ("name", "author")}, {"name": "before-rework", "author": OWNER})

    @mark.req("IF-203", "REQ-WFM-062")
    @each_provider(IF, make)
    def test_snapshots_are_listed_with_exactly_name_time_and_author_oldest_first(self, lib):
        """TC-IF-203-13 (v2): two snapshots taken one after the other are listed oldest first with exactly the three fields; a new snapshot with an existing name is conflict, an empty name is invalid/schema, an unknown name is not_found; nothing is written by a refusal."""
        standard_state(lib)
        lib.snapshot("a", OWNER)
        lib.snapshot("b", OWNER)
        listed = lib.list_snapshots(OWNER)
        self.assertEqual([s["name"] for s in listed], ["a", "b"])
        self.assertTrue(all(set(s) == {"name", "time", "author"} for s in listed))
        self.assertEqual(error_of(lambda: lib.snapshot("a", OWNER)).code, "conflict")
        err = error_of(lambda: lib.snapshot("", OWNER))
        self.assertEqual((err.code, err.rule), ("invalid", "schema"))
        self.assertEqual(error_of(lambda: lib.read_snapshot("none")).code, "not_found")
        self.assertEqual(error_of(lambda: lib.restore_snapshot("none", OWNER)).code, "not_found")
        self.assertEqual([s["name"] for s in lib.list_snapshots(OWNER)], ["a", "b"])

    @mark.req("IF-203", "REQ-WFM-063", "REQ-WFM-064", "REQ-WFM-065")
    @each_provider(IF, make)
    def test_a_restore_keeps_the_former_state_and_gives_version_trust_and_lifecycle_back(self, lib):
        """TC-IF-203-14 (v2) golden 9: state S1 is stored as "a"; a skill, a workflow graph, a context graph and a transform status change (S2); restore_snapshot("a") gives S1 and {"kept_as": "before restore of a"}, that snapshot holds S2 with the owner as author, restore_snapshot of it gives S2 again; restoring "a" a second time stores "before restore of a (2)"; the evidence of the status change is "restore of a"."""
        standard_state(lib)
        s1 = state(lib)
        lib.snapshot("a", OWNER)
        change_everything(lib)
        s2 = state(lib)
        self.assertNotEqual(s1, s2)
        self.assertEqual(lib.restore_snapshot("a", OWNER), {"kept_as": "before restore of a"})
        self.assertEqual(state(lib), s1)
        self.assertEqual(lib.get_meta("t_old")["evidence"], "restore of a")
        kept = lib.read_snapshot("before restore of a")
        self.assertEqual(kept["author"], OWNER)
        self.assertEqual({(i["kind"], i["id"]): i["version"] for i in kept["items"]}[("skills", "research")], 2)
        self.assertEqual(lib.restore_snapshot("before restore of a", OWNER), {"kept_as": "before restore of before restore of a"})
        self.assertEqual(state(lib), s2)
        self.assertEqual(lib.restore_snapshot("a", OWNER), {"kept_as": "before restore of a (2)"})      # the automatic name exists: the suffix counts up
        self.assertEqual(state(lib), s1)

    @mark.req("IF-203", "REQ-WFM-066")
    @each_provider(IF, make)
    def test_only_the_owner_takes_lists_and_restores(self, lib):
        """TC-IF-203-15 (v2) golden 10: a second account created by the owner calls snapshot, list_snapshots and restore_snapshot: all forbidden; the list and the state are unchanged; the owner succeeds."""
        standard_state(lib)
        lib.snapshot("a", OWNER)
        before, listed = state(lib), lib.list_snapshots(OWNER)
        for call in (lambda: lib.snapshot("b", OTHER), lambda: lib.list_snapshots(OTHER), lambda: lib.restore_snapshot("a", OTHER)):
            self.assertEqual(error_of(call).code, "forbidden")
        self.assertEqual((state(lib), lib.list_snapshots(OWNER)), (before, listed))

    @mark.req("IF-203", "REQ-WFM-064", "REQ-WFM-065")
    @each_provider(IF, make)
    def test_an_old_snapshot_restores_without_deleting_a_version_and_an_untrusted_transform_stays_untrusted(self, lib):
        """TC-IF-203-16 (v2) golden 11: the snapshot is older than the last 3 versions of every item; after the restore the version list of every item before the call is a prefix of the list after it; a transform that is untrusted in the snapshot is untrusted after the restore although it was trusted before."""
        standard_state(lib)
        lib.snapshot("old", OWNER)
        for n in range(2, 6):
            lib.save("skills", "research", skill_doc("research", n), OWNER)
            lib.save("workflows", "lookup", graph_doc("edit %d" % n), OWNER)
        lib.set_trust("t_old", "trusted", OWNER)
        before = versions(lib)
        lib.restore_snapshot("old", OWNER)
        after = versions(lib)
        for key, found in before.items():
            self.assertEqual(after[key][:len(found)], found, key)
        self.assertEqual(lib.read("skills", "research")["version"], 1)
        self.assertEqual(lib.get_trust("t_old"), "untrusted")

    @mark.req("IF-203", "REQ-WFM-063", "REQ-WFM-064")
    @each_provider(IF, make)
    def test_a_failure_inside_a_restore_changes_the_items_back_and_keeps_the_automatic_snapshot(self, lib):
        """TC-IF-203-17 (v2) golden 12: the write of the third item fails; the first two are changed back, the state equals the one before the call, "before restore of a" exists, the error is raised.
        Needs the failure seam `fail_set_current_version_at` of the library under test (the mock has it)."""
        if not hasattr(lib, "fail_set_current_version_at"):
            raise unittest.SkipTest("the real library gives no seam to fail the third pointer move; T-SN-01 adds one or proves the rollback another way")
        standard_state(lib)
        lib.snapshot("a", OWNER)
        change_everything(lib)
        before = state(lib)
        lib.fail_set_current_version_at = 3
        with self.assertRaises(ServiceError):
            lib.restore_snapshot("a", OWNER)
        self.assertEqual(state(lib), before)
        self.assertIn("before restore of a", [s["name"] for s in lib.list_snapshots(OWNER)])


if __name__ == "__main__":
    unittest.main()
