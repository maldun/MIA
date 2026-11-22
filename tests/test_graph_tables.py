"""The table definitions of the Graph tables (N-3.2 T-02): TC-GTB-001, TC-GTB-004. Run with: python tests/test_graph_tables.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from graph_tables import check_record, definitions, scoped, split_scoped, validate  # noqa: E402
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


def header(graph_id, nodes):
    return {"id": graph_id, "data": {"kind": "workflow", "context_graph_id": "", "testbench_id": "", "description": "d",
                                     "nodes": [{"id": i, "version": 1} for i in nodes], "edges": []}}


class ScopedIds(unittest.TestCase):
    """G-V4.GRAPHSTORE.CORE T-01: the record ID of a step or connection is `<graph id>/<local id>`."""

    @mark.req("REQ-GTB-031")
    def test_the_first_slash_splits_graph_and_local_id(self):
        """scoped joins with a slash; split_scoped cuts at the first slash and rejects an empty part.

        Example: split_scoped("a/b/c") -> ("a", "b/c"); split_scoped("a/") -> None.
        """
        # Given / When / Then
        self.assertEqual(scoped("wf1", "n1"), "wf1/n1")
        self.assertEqual(split_scoped("a/b/c"), ("a", "b/c"))
        for bad in ("chat", "/chat", "lookup/", "", "/"):
            with self.subTest(record_id=bad):
                self.assertIsNone(split_scoped(bad))

    @mark.req("REQ-GTB-029")
    def test_a_step_or_connection_with_a_plain_id_is_unscoped(self):
        """A record of the four step and connection tables needs a scoped ID; graphs and skills do not.

        Example: check_record("graph_nodes", {"id": "chat", ...}) -> unscoped_id naming chat.
        """
        # Given: a valid step, connection and context step under a plain ID
        records = {"graph_nodes": {"id": "chat", "data": {"type": "data"}},
                   "graph_edges": {"id": "e1", "from": "g/a", "to": "g/b", "data": {}},
                   "context_nodes": {"id": "c1", "data": {"type": "entity"}},
                   "context_edges": {"id": "ce", "from": "g/a", "to": "g/b", "data": {}}}
        for table, record in records.items():
            with self.subTest(table=table):
                # When / Then
                self.assertEqual(check_record(table, record), {"rule": "unscoped_id", "detail": record["id"]})
                self.assertIsNone(check_record(table, dict(record, id="g/" + record["id"])))
        self.assertIsNone(check_record("graphs", header("wf1", [])))

    @mark.req("REQ-GTB-029")
    def test_the_empty_id_stays_record_identity(self):
        """D-409: an empty ID is record_identity, and a differing record_id is checked before the scope.

        Example: check_record("graph_nodes", {"id": ""}) -> record_identity naming id.
        """
        # Given / When / Then
        self.assertEqual(check_record("graph_nodes", {"id": "", "data": {"type": "data"}}), {"rule": "record_identity", "detail": "id"})
        self.assertEqual(check_record("graph_nodes", {"id": "chat", "data": {"type": "data"}}, record_id="g/chat"),
                         {"rule": "record_identity", "detail": "id"})

    @mark.req("REQ-GTB-030")
    def test_a_header_names_only_its_own_members(self):
        """A member of another graph or with a plain ID is unscoped_id, checked before unknown_member, with and without stored.

        Example: header wf1 naming wf2/n1 -> unscoped_id naming wf2/n1.
        """
        # Given: what is stored holds every member, so only the scope can refuse
        stored = {"nodes": {"wf1/n1": [1], "wf2/n1": [1], "n1": [1]}, "edges": {}}
        for member in ("wf2/n1", "n1", "wf10/n1"):
            with self.subTest(member=member):
                # When / Then
                self.assertEqual(check_record("graphs", header("wf1", [member]), stored=stored), {"rule": "unscoped_id", "detail": member})
                self.assertEqual(check_record("graphs", header("wf1", [member])), {"rule": "unscoped_id", "detail": member})
        self.assertEqual(check_record("graphs", header("wf1", ["wf2/x"]), stored={"nodes": {}, "edges": {}}),
                         {"rule": "unscoped_id", "detail": "wf2/x"})
        self.assertEqual(check_record("graphs", header("wf1", ["wf1/x"]), stored={"nodes": {}, "edges": {}}),
                         {"rule": "unknown_member", "detail": "wf1/x"})
        self.assertIsNone(check_record("graphs", header("wf1", ["wf1/n1"]), stored=stored))


if __name__ == "__main__":
    unittest.main()
