"""Unit tests of the record checks of the Graph tables (N-3.2, G-V2.STORE T-01) beyond the acceptance tests: edge cases found while writing check_record.
Run with: python tests/test_graph_record_checks.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import graph_tables  # noqa: E402


def master(**fields):
    return {"id": "m1", "data": dict({"type": "master", "toolbox_id": "t"}, **fields)}


class RecordCheckEdges(unittest.TestCase):
    def test_a_number_that_is_not_finite_breaks_the_schema(self):
        """A stopping limit of NaN or infinity is refused like in v1 (A-60) and names its path: JSON has no such number.

        Example: stop {"max_seconds": NaN} -> schema_break "stop.max_seconds"; {"max_seconds": inf} -> the same.
        """
        # Given: master nodes whose limit is NaN or infinity
        for number in (float("nan"), float("inf")):
            with self.subTest(number=number):
                # When: each is checked; Then: refused as schema_break with the path of the limit
                self.assertEqual(graph_tables.check_record("graph_nodes", master(stop={"max_seconds": number})),
                                 {"rule": "schema_break", "detail": "stop.max_seconds"})
        # And: a finite limit is accepted
        self.assertIsNone(graph_tables.check_record("graph_nodes", master(stop={"max_seconds": 0.5})))

    def test_a_boolean_is_not_a_repetition_count(self):
        """True is not an integer limit (as in v1, D-160).

        Example: stop {"max_repetitions": True} -> schema_break "stop.max_repetitions"; 1 is valid.
        """
        # Given/When/Then
        self.assertEqual(graph_tables.check_record("graph_nodes", master(stop={"max_repetitions": True})),
                         {"rule": "schema_break", "detail": "stop.max_repetitions"})
        self.assertIsNone(graph_tables.check_record("graph_nodes", master(stop={"max_repetitions": 1})))

    def test_a_malformed_header_is_named_and_never_raises(self):
        """A header whose members are not objects, or whose kind is unknown, is a schema_break naming the field, not an exception.

        Example: nodes ["n1"] -> schema_break "nodes.0"; kind "x" -> schema_break "kind".
        """
        # Given: two broken headers and the empty store state
        base = {"kind": "workflow", "context_graph_id": "c", "testbench_id": "", "description": "d", "nodes": [], "edges": []}
        stored = {"nodes": {}, "edges": {}}
        # When/Then
        self.assertEqual(graph_tables.check_record("graphs", {"id": "g", "data": dict(base, nodes=["n1"])}, stored=stored),
                         {"rule": "schema_break", "detail": "nodes.0"})
        self.assertEqual(graph_tables.check_record("graphs", {"id": "g", "data": dict(base, kind="x")}, stored=stored),
                         {"rule": "schema_break", "detail": "kind"})

    def test_a_type_that_is_not_text_is_an_unknown_type(self):
        """A type ID that is a list cannot be in the fixed list: unknown_type naming it.

        Example: {"type": ["x"]} -> unknown_type; an empty `categories` makes even "data" unknown (a context graph without that category).
        """
        # Given/When/Then
        self.assertEqual(graph_tables.check_record("graph_nodes", {"id": "a", "data": {"type": ["x"]}})["rule"], "unknown_type")
        self.assertEqual(graph_tables.check_record("graph_nodes", {"id": "a", "data": {"type": "data"}}, categories={}),
                         {"rule": "unknown_type", "detail": "data"})


if __name__ == "__main__":
    unittest.main()
