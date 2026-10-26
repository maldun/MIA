"""The table definitions of the Graph tables (N-3.2 T-02): TC-GTB-001, TC-GTB-004. Run with: python tests/test_graph_tables.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from graph_tables import definitions, validate  # noqa: E402
from markers import mark                        # noqa: E402

GOOD = {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process"}, {"id": "a", "kind": "data"}],
        "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "a"}]}
CYCLE = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}


class GraphTables(unittest.TestCase):
    @mark.req("REQ-GTB-001", "IF-301")
    def test_exactly_two_tables_versioned_and_not_deletable(self):
        """TC-GTB-001: workflows and context_graphs, both versioned, neither deletable."""
        self.assertEqual(definitions(), {"workflows": {"versioned": True, "deletable": False}, "context_graphs": {"versioned": True, "deletable": False}})

    @mark.req("REQ-GTB-001")
    def test_the_definitions_are_a_copy(self):
        """A caller that changes the answer does not change the tables."""
        definitions()["workflows"]["deletable"] = True
        self.assertFalse(definitions()["workflows"]["deletable"])

    @mark.req("REQ-GTB-003", "IF-301")
    def test_context_graphs_are_validated_by_the_graph_rules(self):
        """TC-GTB-004: a valid context graph gives None, a broken one its rule and detail; the same for workflows."""
        for table in ("workflows", "context_graphs"):
            with self.subTest(table=table):
                self.assertIsNone(validate(table, GOOD))
                self.assertEqual(validate(table, CYCLE), {"rule": "cycle", "detail": ["p", "d", "p"]})

    @mark.req("IF-301")
    def test_a_table_that_is_not_a_graph_table_is_a_value_error(self):
        """IF-301: the caller asks IF-302 instead."""
        for table in ("memory", "votes", "", None):
            with self.subTest(table=table), self.assertRaises(ValueError):
                validate(table, GOOD)


if __name__ == "__main__":
    unittest.main()
