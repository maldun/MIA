"""
The current-version pointer of the real workflow library (IF-203 v2, A-121, D-241; REQ-WFM-064, REQ-WFM-065; G-V2.SNAPSHOT, T-SN-01): the table `current_versions` on the
real Storage with the file backend. The documents are real ones (the graph rules of IF-301 apply); the contract suite of IF-203 v2 uses documents of the mock.
Run: python tests/test_library_pointer.py
"""
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from storage import Storage                      # noqa: E402
from storage_files import FileBackend            # noqa: E402
from workflow_library import WorkflowLibrary, WorkflowLibraryError   # noqa: E402
from markers import mark                                  # noqa: E402


def graph(note):
    return {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process", "note": note}, {"id": "r", "kind": "data"}],
            "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "r"}]}


def transform(version, code="def run(a):\n    return 1\n"):
    return {"id": "t.one", "version": version, "inputs": {"type": "object"}, "outputs": {"type": "number"}, "code": code}


def error_of(call):
    try:
        call()
    except WorkflowLibraryError as err:
        return err
    raise AssertionError("no WorkflowLibraryError raised")


class PointerTest(unittest.TestCase):
    def setUp(self):
        self.storage = Storage(FileBackend(tempfile.mkdtemp()))
        self.lib = WorkflowLibrary(self.storage)
        for note in ("one", "two"):
            self.lib.save("workflows", "lookup", graph(note), "anna")

    @mark.req("REQ-WFM-064")
    def test_set_current_version_makes_read_give_that_version_and_creates_nothing(self):
        self.assertEqual(self.lib.read("workflows", "lookup")["version"], 2)
        self.assertEqual(self.lib.set_current_version("workflows", "lookup", 1, "anna"), {"version": 1})
        entry = self.lib.read("workflows", "lookup")
        self.assertEqual((entry["version"], entry["doc"]["nodes"][1]["note"]), (1, "one"))
        self.assertEqual([h["version"] for h in self.lib.history("workflows", "lookup")], [1, 2])
        self.assertEqual(self.lib.read("workflows", "lookup", 2)["doc"]["nodes"][1]["note"], "two")      # an explicit version reads its own document

    @mark.req("REQ-WFM-064")
    def test_every_move_of_the_pointer_is_kept_as_a_version_of_the_pointer_record(self):
        self.lib.set_current_version("workflows", "lookup", 1, "anna")
        self.lib.set_current_version("workflows", "lookup", 2, "ben")
        key = "workflows/lookup"
        moves = [self.storage.get("current_versions", key, v) for v in (1, 2, 3, 4)]
        self.assertEqual([m["doc"]["version"] for m in moves], [1, 2, 1, 2])      # two saves (reason save), then two moves
        self.assertEqual([m["doc"]["reason"] for m in moves], ["save", "save", "set_current_version", "set_current_version"])
        self.assertEqual(moves[3]["author"], "ben")

    @mark.req("REQ-WFM-064")
    def test_a_save_after_a_pointer_move_writes_max_plus_one_and_moves_the_pointer(self):
        self.lib.set_current_version("workflows", "lookup", 1, "anna")
        err = error_of(lambda: self.lib.save("workflows", "lookup", graph("three"), "anna", expected_version=2))      # the current version is 1, not the newest
        self.assertEqual((err.code, err.detail), ("conflict", {"current": 1}))
        self.assertEqual(self.lib.save("workflows", "lookup", graph("three"), "anna", expected_version=1), {"version": 3})
        self.assertEqual(self.lib.read("workflows", "lookup")["version"], 3)
        self.assertEqual(self.lib.restore("workflows", "lookup", 1, "anna"), {"version": 4})      # restore keeps its v0 meaning: a new version with the old content
        self.assertEqual(self.lib.read("workflows", "lookup")["doc"]["nodes"][1]["note"], "one")

    @mark.req("REQ-WFM-064")
    def test_an_item_without_a_pointer_record_reads_as_its_newest_version(self):
        self.storage.put("workflows", "old", graph("x"), "anna")           # data from before v2: written below the library
        self.storage.put("workflows", "old", graph("y"), "anna")
        self.assertEqual(self.lib.read("workflows", "old")["version"], 2)
        self.assertEqual(self.lib.save("workflows", "old", graph("z"), "anna", expected_version=2), {"version": 3})      # expected_version against the implied current version

    @mark.req("REQ-WFM-064")
    def test_a_pointer_to_a_missing_version_or_item_is_refused_and_nothing_moves(self):
        for version in (0, 3, True, "1", None):
            err = error_of(lambda: self.lib.set_current_version("workflows", "lookup", version, "anna"))
            self.assertEqual((err.code, err.rule), ("invalid", "schema"), version)
        for call in (lambda: self.lib.set_current_version("workflows", "none", 1, "anna"), lambda: self.lib.set_current_version("nothing", "lookup", 1, "anna")):
            self.assertEqual(error_of(call).code, "not_found")
        self.assertEqual(self.lib.read("workflows", "lookup")["version"], 2)
        self.assertEqual(len(self.storage.history("current_versions", "workflows/lookup")), 2)      # only the two saves

    @mark.req("REQ-WFM-064", "REQ-WFM-092")
    def test_the_pointer_works_for_transforms_and_keeps_trust_and_lifecycle(self):
        self.lib.save("transforms", "t.one", transform(1), "anna")
        self.lib.set_trust("t.one", "trusted", "anna")
        self.lib.save("transforms", "t.one", transform(2, "def run(a):\n    return 2\n"), "anna")
        self.lib.set_current_version("transforms", "t.one", 1, "anna")
        entry = self.lib.read("transforms", "t.one")
        self.assertEqual((entry["version"], entry["doc"]["version"], entry["trust"]), (1, 1, "trusted"))      # the meta record is not part of the pointer

    @mark.req("REQ-WFM-064")
    def test_the_kind_skills_has_a_pointer_too(self):
        data = {"command": "research", "workflow_graph_id": "lookup", "context_graph_id": "places"}      # a record of IF-301 v2: {"id", "data"}
        self.lib.save("skills", "research", {"id": "research", "data": data}, "anna")
        self.lib.save("skills", "research", {"id": "research", "data": dict(data, command="research2")}, "anna")
        self.lib.set_current_version("skills", "research", 1, "anna")
        self.assertEqual(self.lib.read("skills", "research")["doc"]["data"]["command"], "research")
        self.assertEqual(self.lib.list_ids("skills"), ["research"])


if __name__ == "__main__":
    unittest.main()
