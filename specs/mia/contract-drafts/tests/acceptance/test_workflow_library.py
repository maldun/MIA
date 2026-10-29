"""
Acceptance tests of the workflow library (N-2.3 T-01): TC-WFM-002, TC-WFM-003, TC-WFM-004 and TC-WFM-026 (REQ-WFM-002, -003, -004, -026) against the real WorkflowLibrary on the real Storage with the file backend.
Run with: python tests/acceptance/test_workflow_library.py
"""

import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                              # noqa: E402
from storage import Storage                                           # noqa: E402
from storage_files import FileBackend                                 # noqa: E402
from workflow_library import WorkflowLibrary, WorkflowLibraryError    # noqa: E402

LOOKUP = {"nodes": [{"id": "question", "kind": "data"}, {"id": "search", "kind": "process"}, {"id": "hits", "kind": "data"},
                    {"id": "judge", "kind": "process"}, {"id": "verdict", "kind": "data"}],
          "edges": [{"from": "question", "to": "search"}, {"from": "search", "to": "hits"}, {"from": "hits", "to": "judge"}, {"from": "judge", "to": "verdict"}]}


def edited(note):
    doc = {"nodes": [dict(n) for n in LOOKUP["nodes"]], "edges": list(LOOKUP["edges"])}
    doc["nodes"][3]["note"] = note
    return doc


def error_of(call):
    try:
        call()
    except WorkflowLibraryError as err:
        return err
    raise AssertionError("no WorkflowLibraryError raised")


class WorkflowLibraryAcceptance(unittest.TestCase):
    def setUp(self):
        self.lib = WorkflowLibrary(Storage(FileBackend(tempfile.mkdtemp())), costs={})

    @mark.req("REQ-WFM-002")
    def test_an_edit_creates_the_next_version_and_leaves_the_old_one_unchanged(self):
        """TC-WFM-002: an edit of a stored workflow creates version n+1 and leaves version n unchanged."""
        self.assertEqual(self.lib.save("workflows", "lookup", LOOKUP, "anna"), {"version": 1})
        self.assertEqual(self.lib.save("workflows", "lookup", edited("x"), "ben"), {"version": 2})
        self.assertEqual(self.lib.read("workflows", "lookup", 1)["doc"], LOOKUP)
        self.assertEqual(self.lib.read("workflows", "lookup", 2)["doc"], edited("x"))
        self.assertEqual([h["author"] for h in self.lib.history("workflows", "lookup")], ["anna", "ben"])

    @mark.req("REQ-WFM-004")
    def test_each_of_the_three_violations_is_refused_with_the_rule_named(self):
        """TC-WFM-004: each of three graph violations is refused with the rule named."""
        cyc = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
        adj = {"nodes": [{"id": "a", "kind": "data"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}]}
        ses = {"nodes": [{"id": "debate", "kind": "process", "session": True}], "edges": []}
        for doc, rule in ((cyc, "cycle"), (adj, "adjacent_data_nodes"), (ses, "session_stopping_criterion")):
            err = error_of(lambda: self.lib.save("workflows", "bad", doc, "anna"))
            self.assertEqual((err.code, err.rule), ("invalid", rule))
        self.assertEqual(self.lib.list_ids("workflows"), [])

    @mark.req("REQ-WFM-003")
    def test_a_cycle_is_refused_with_the_cycle_named_and_every_accepted_graph_has_a_topological_order(self):
        """TC-WFM-003: a workflow with a cycle is refused with the cycle named; on generated graphs every accepted one has a topological order (seeded generator, no statistical check)."""
        cyc = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
        self.assertEqual(error_of(lambda: self.lib.save("workflows", "bad", cyc, "anna")).detail, ["p", "d", "p"])
        rng = random.Random(7)
        accepted = refused = 0
        for n in range(300):
            nodes = [{"id": "n%d" % i, "kind": rng.choice(["process", "data"])} for i in range(rng.randint(2, 8))]
            edges = [{"from": a["id"], "to": b["id"]} for a in nodes for b in nodes if a is not b and a["kind"] != b["kind"] and rng.random() < 0.25]
            try:
                self.lib.save("workflows", "g%d" % n, {"nodes": nodes, "edges": edges}, "anna")
            except WorkflowLibraryError as err:
                self.assertEqual((err.code, err.rule), ("invalid", "cycle"))      # alternating kinds only, so a cycle is the one thing that can break
                refused += 1
                continue
            accepted += 1
            order = self.lib.estimate("g%d" % n)["order"]
            self.assertEqual(sorted(order), sorted(x["id"] for x in nodes if x["kind"] == "process"))
            position = {pid: i for i, pid in enumerate(order)}
            succ = {x["id"]: [e["to"] for e in edges if e["from"] == x["id"]] for x in nodes}
            for p in order:                                  # p -> data -> q: p comes before q
                for d in succ[p]:
                    for q in succ[d]:
                        self.assertLess(position[p], position[q])
        self.assertGreater(accepted, 20)
        self.assertGreater(refused, 20)

    @mark.req("REQ-WFM-026")
    def test_each_of_the_six_operations_works_and_an_invalid_graph_is_refused_with_the_rule(self):
        """TC-WFM-026: on the real storage save, read, list, history, diff and restore work; an invalid graph is refused with the rule named and nothing is stored."""
        lib = self.lib
        self.assertEqual(lib.save("workflows", "lookup", LOOKUP, "anna"), {"version": 1})
        self.assertEqual(lib.save("workflows", "lookup", edited("x"), "ben"), {"version": 2})
        self.assertEqual(lib.read("workflows", "lookup")["doc"], edited("x"))
        self.assertEqual(lib.list_ids("workflows"), ["lookup"])
        self.assertEqual([h["author"] for h in lib.history("workflows", "lookup")], ["anna", "ben"])
        self.assertEqual(lib.diff("workflows", "lookup", 1, 2)["nodes_changed"], ["judge"])
        self.assertEqual(lib.restore("workflows", "lookup", 1, "anna"), {"version": 3})
        self.assertEqual(lib.read("workflows", "lookup")["doc"], LOOKUP)
        cyc = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
        err = error_of(lambda: lib.save("workflows", "bad", cyc, "anna"))
        self.assertEqual((err.code, err.rule), ("invalid", "cycle"))
        self.assertEqual(lib.list_ids("workflows"), ["lookup"])


if __name__ == '__main__':
    unittest.main()
