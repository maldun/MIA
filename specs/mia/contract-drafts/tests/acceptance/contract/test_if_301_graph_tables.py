"""IF-301 graph table definitions and validation (Storage layer to Graph tables): the contract suite runs against the mock (stage 1) and the real
Graph tables (stage 2, skipped until N-3.2 is integrated). Protected after the Plan gate.
Run with: python tests/acceptance/contract/test_if_301_graph_tables.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402  (from tests/helpers, shared with the other acceptance tests)

IF = "IF-301"
GOOD = {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process"}, {"id": "a", "kind": "data"}],
        "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "a"}]}


@contract
class GraphTablesContract(unittest.TestCase):
    @mark.req("IF-301", "REQ-DB-011")
    @each_provider(IF)
    def test_both_graph_tables_are_versioned_and_not_deletable(self, tables):
        """TC-IF-301-01: workflows and context_graphs are defined, versioned, not deletable."""
        self.assertEqual(tables.definitions(), {"workflows": {"versioned": True, "deletable": False}, "context_graphs": {"versioned": True, "deletable": False}})

    @mark.req("IF-301", "REQ-DB-004")
    @each_provider(IF)
    def test_a_valid_graph_and_each_broken_rule(self, tables):
        """TC-IF-301-02 golden 1 and 2: a valid graph gives None; each broken rule is named."""
        self.assertIsNone(tables.validate("workflows", GOOD))
        cases = [
            ({"nodes": [{"id": "a", "kind": "data"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}]}, "adjacent_data_nodes"),
            ({"nodes": [{"id": "a", "kind": "process"}, {"id": "b", "kind": "process"}], "edges": [{"from": "a", "to": "b"}]}, "adjacent_process_nodes"),
            ({"nodes": [{"id": "a", "kind": "data"}, {"id": "a", "kind": "data"}], "edges": []}, "node_identity"),
            ({"nodes": [{"id": "s", "kind": "process", "session": True, "stop": {"max_cycles": 0}}], "edges": []}, "session_stopping_criterion"),
        ]
        for doc, rule in cases:
            self.assertEqual(tables.validate("workflows", doc)["rule"], rule)

    @mark.req("IF-301", "REQ-DB-004")
    @each_provider(IF)
    def test_a_cycle_is_named_and_a_foreign_table_is_refused(self, tables):
        """TC-IF-301-03 golden 3: p->d->p is a cycle named as [p, d, p]; a table that is not a graph table is a ValueError."""
        doc = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
        result = tables.validate("context_graphs", doc)
        self.assertEqual(result["rule"], "cycle")
        self.assertEqual((result["detail"][0], result["detail"][-1], set(result["detail"])), ("p", "p", {"p", "d"}))
        with self.assertRaises(ValueError):
            tables.validate("memory", {})

    @mark.req("IF-301", "REQ-DB-004")
    @each_provider(IF)
    def test_a_session_limit_is_a_positive_integer_and_a_malformed_part_is_named(self, tables):
        """TC-IF-301-04 golden 4 (A-60): a limit that is not an integer >= 1 (or is a bool) and a stop that is not an object are
        session_stopping_criterion; an edge endpoint that is not text is node_identity; max_cycles 1 is valid. Nothing raises."""
        session = lambda stop: {"nodes": [{"id": "s", "kind": "process", "session": True, "stop": stop}], "edges": []}
        for stop in ({"max_cycles": -1}, {"max_cycles": "3"}, {"max_cycles": True}, {"max_cycles": 2.5}, {"max_cycles": float("nan")},
                     {"max_cycles": 3, "max_seconds": -1}, "x", [1]):
            with self.subTest(stop=stop):
                self.assertEqual(tables.validate("workflows", session(stop))["rule"], "session_stopping_criterion")
        self.assertIsNone(tables.validate("workflows", session({"max_cycles": 1})))
        self.assertIsNone(tables.validate("workflows", session({"max_cycles": 2, "max_seconds": None})))
        for endpoint in (["q"], {"id": "q"}, 1):
            with self.subTest(endpoint=endpoint):
                doc = {"nodes": GOOD["nodes"], "edges": [{"from": endpoint, "to": "p"}]}
                self.assertEqual(tables.validate("context_graphs", doc)["rule"], "node_identity")


if __name__ == "__main__":
    unittest.main()
