"""IF-203 workflow library (API, Chat agent and Workflow execution to Workflow management): the contract suite runs against the mock (stage 1)
and the real Workflow management (stage 2, skipped until N-2.3 is integrated). Protected after the Plan gate.
Run with: python tests/acceptance/contract/test_if_203_workflow_library.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ServiceError                             # noqa: E402
from if_203_workflow_library import WorkflowLibraryMock     # noqa: E402

IF = "IF-203"
COSTS = {"search": {"seconds": 2.0, "calls": 0, "tokens": 0}, "judge": {"seconds": 5.0, "calls": 3, "tokens": 1500}}
LOOKUP = {"nodes": [{"id": "question", "kind": "data"}, {"id": "search", "kind": "process"}, {"id": "hits", "kind": "data"},
                    {"id": "judge", "kind": "process"}, {"id": "verdict", "kind": "data"}],
          "edges": [{"from": "question", "to": "search"}, {"from": "search", "to": "hits"}, {"from": "hits", "to": "judge"}, {"from": "judge", "to": "verdict"}]}


def edited(note):
    doc = {"nodes": [dict(n) for n in LOOKUP["nodes"]], "edges": list(LOOKUP["edges"])}
    doc["nodes"][3]["note"] = note
    return doc


def make(kind):
    return WorkflowLibraryMock(costs=COSTS) if kind == "mock" else subject_for(IF, kind, costs=COSTS)


def error_of(call):
    try:
        call()
    except ServiceError as err:
        return err
    raise AssertionError("no ServiceError raised")


@contract
class WorkflowLibraryContract(unittest.TestCase):
    @mark.req("IF-203", "REQ-BE-035")
    @each_provider(IF, make)
    def test_versions_diff_and_restore(self, lib):
        """TC-IF-203-01 golden 1: version 1, an edit as version 2, the diff names the node, restore gives version 3 equal to version 1; status stays draft."""
        self.assertEqual(lib.save("workflows", "lookup", LOOKUP, "anna"), {"version": 1})
        self.assertEqual(lib.save("workflows", "lookup", edited("x"), "ben"), {"version": 2})
        self.assertEqual(lib.diff("workflows", "lookup", 1, 2)["nodes_changed"], ["judge"])
        self.assertEqual(lib.restore("workflows", "lookup", 1, "anna"), {"version": 3})
        entry = lib.read("workflows", "lookup")
        self.assertEqual((entry["doc"], entry["status"]), (LOOKUP, "draft"))
        self.assertEqual([h["author"] for h in lib.history("workflows", "lookup")], ["anna", "ben", "anna"])

    @mark.req("IF-203", "REQ-BE-036", "REQ-BE-037")
    @each_provider(IF, make)
    def test_a_broken_graph_is_refused_with_the_rule(self, lib):
        """TC-IF-203-02: cycle, adjacent data nodes and a session node without stopping criterion are invalid with the rule; nothing is stored."""
        cyc = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
        adj = {"nodes": [{"id": "a", "kind": "data"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}]}
        ses = {"nodes": [{"id": "debate", "kind": "process", "session": True}], "edges": []}
        for doc, rule in ((cyc, "cycle"), (adj, "adjacent_data_nodes"), (ses, "session_stopping_criterion")):
            err = error_of(lambda: lib.save("workflows", "bad", doc, "anna"))
            self.assertEqual((err.code, err.rule), ("invalid", rule))
        self.assertEqual(lib.list_ids("workflows"), [])

    @mark.req("IF-203", "REQ-BE-039")
    @each_provider(IF, make)
    def test_promotion_needs_specification_and_benchmark(self, lib):
        """TC-IF-203-03 golden 2: tested before specification and benchmark are attached is not_promotable and names both; after attaching it works."""
        lib.save("workflows", "lookup", LOOKUP, "anna")
        err = error_of(lambda: lib.set_status("lookup", "tested", "anna"))
        self.assertEqual((err.code, err.detail), ("not_promotable", ["specification", "benchmark"]))
        lib.attach("lookup", "specification", {"inputs": "question"})
        self.assertEqual(error_of(lambda: lib.set_status("lookup", "trusted", "anna")).detail, ["benchmark"])
        lib.attach("lookup", "benchmark", {"suite": "verdicts"})
        self.assertEqual(lib.set_status("lookup", "tested", "anna"), {"status": "tested"})
        self.assertEqual(lib.read("workflows", "lookup")["status"], "tested")

    @mark.req("IF-203", "REQ-BE-042")
    @each_provider(IF, make)
    def test_estimate_order_critical_path_and_session_cycles(self, lib):
        """TC-IF-203-04 golden 3: topological order, critical path, sums from the node costs; a session node counts its maximum cycles."""
        lib.save("workflows", "lookup", LOOKUP, "anna")
        est = lib.estimate("lookup")
        self.assertEqual(est["order"], ["search", "judge"])
        self.assertEqual(est["critical_path"], ["search", "judge"])
        self.assertEqual((est["seconds"], est["calls"], est["tokens"]), (7.0, 3, 1500))
        debate = {"nodes": [dict(n) for n in LOOKUP["nodes"]], "edges": list(LOOKUP["edges"])}
        debate["nodes"][3].update({"session": True, "stop": {"max_cycles": 4}})
        lib.save("workflows", "debate", debate, "anna")
        est = lib.estimate("debate")
        self.assertEqual((est["calls"], est["tokens"], est["seconds"]), (12, 6000, 22.0))


if __name__ == "__main__":
    unittest.main()
