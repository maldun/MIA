"""
Acceptance tests of the context graph tables and of the input that cannot be checked (N-3.2 Graph tables, G-V2.STORE, A-98): TC-GTB-024 to
TC-GTB-028 (REQ-GTB-023 to REQ-GTB-027) through the storage stand-in of tests/helpers/graph_store_standin.py (which passes the IF-102 suite first,
TR-GTB-002). The expected values are written by hand (TR-GTB-001). Run with: python tests/acceptance/test_graph_context_tables.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))
sys.path.append(os.path.join(REPO, "tests", "helpers", "mocks"))   # appended: the mocks have their own graph_rules

from markers import mark                                           # noqa: E402
from errors import StorageError                                    # noqa: E402
from graph_store_standin import GraphStoreStandIn                  # noqa: E402
import graph_tables                                                # noqa: E402

SIX_TABLES = {t: {"versioned": True, "deletable": False}
              for t in ("graph_nodes", "graph_edges", "graphs", "skills", "context_nodes", "context_edges")}
WHO = "anna"


def cnode(node_id, **data):
    return {"id": node_id, "data": dict({"type": "entity"}, **data)}


def cedge(edge_id, start, end):
    return {"id": edge_id, "from": start, "to": end, "data": {}}


def header(graph_id, kind, nodes, edges=()):
    return {"id": graph_id, "data": {"kind": kind, "context_graph_id": "ctx", "testbench_id": "", "description": "a test graph",
                                     "nodes": [{"id": i, "version": 1} for i in nodes], "edges": [{"id": i, "version": 1} for i in edges]}}


def refusal(test, store, table, record_id, record):
    """What put refuses with, as (rule, detail); the store must not change."""
    before = store.ids(table)
    with test.assertRaises(StorageError) as caught:
        store.put(table, record_id, record, WHO)
    test.assertEqual(caught.exception.code, "invalid")
    test.assertEqual(store.ids(table), before)
    return caught.exception.rule, caught.exception.detail


class ContextTablesAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-023")
    def test_the_context_tables_are_versioned_and_never_deleted(self):
        """TC-GTB-024: the Graph tables list context_nodes and context_edges as versioned tables that are never deleted.

        Example: record_definitions() has six tables; a context node written twice has versions [1, 2]; a delete is refused as immutable.
        """
        # Given: the definitions of the Graph tables and an empty store
        self.assertEqual(graph_tables.record_definitions(), SIX_TABLES)
        store = GraphStoreStandIn()
        # When: a context node is written twice, and a context edge once
        first = store.put("context_nodes", "c1", cnode("c1"), WHO)
        second = store.put("context_nodes", "c1", cnode("c1", name="x"), WHO)
        store.put("context_nodes", "c2", cnode("c2"), WHO)
        edge = store.put("context_edges", "e1", cedge("e1", "c1", "c2"), WHO)
        # Then: the versions are 1 and 2, the edge is version 1
        self.assertEqual((first, second, edge), ({"version": 1}, {"version": 2}, {"version": 1}))
        # And: a delete of either is refused as immutable and the records stay
        for table, record_id in (("context_nodes", "c1"), ("context_edges", "e1")):
            with self.assertRaises(StorageError) as caught:
                store.delete(table, record_id, WHO)
            self.assertEqual(caught.exception.code, "immutable")
        self.assertEqual((store.ids("context_nodes"), store.ids("context_edges")), (["c1", "c2"], ["e1"]))

    @mark.req("REQ-GTB-024")
    def test_a_context_record_of_a_bad_shape_is_refused_naming_the_field(self):
        """TC-GTB-025: a context node without a type, without a JSON object or without an ID, and a context edge without an end, are refused naming the field.

        Example: {"id": "c1", "data": {}} -> schema_break "type"; {"id": "c1"} -> schema_break "data"; {"id": "", ...} -> record_identity "id".
        """
        # Given: an empty store and one broken record per rule (the Storage layer checks the shape only, without categories)
        store = GraphStoreStandIn()
        cases = [("context_nodes", "c1", {"id": "c1", "data": {}}, ("schema_break", "type")),
                 ("context_nodes", "c1", {"id": "c1", "data": {"type": 5}}, ("schema_break", "type")),
                 ("context_nodes", "c1", {"id": "c1"}, ("schema_break", "data")),
                 ("context_nodes", "", {"id": "", "data": {"type": "entity"}}, ("record_identity", "id")),
                 ("context_edges", "e1", {"id": "e1", "from": "c1", "data": {}}, ("record_identity", "to")),
                 ("context_edges", "e1", {"id": "e1", "from": "c1", "to": "c2"}, ("schema_break", "data"))]
        for table, record_id, record, expected in cases:
            with self.subTest(record=record):
                # When/Then: the write is refused with the rule and the field, and nothing is stored
                self.assertEqual(refusal(self, store, table, record_id, record), expected)
        # And: the twins are accepted (they differ only in the broken rule)
        self.assertEqual(store.put("context_nodes", "c1", cnode("c1"), WHO), {"version": 1})
        self.assertEqual(store.put("context_nodes", "c2", cnode("c2"), WHO), {"version": 1})
        self.assertEqual(store.put("context_edges", "e1", cedge("e1", "c1", "c2"), WHO), {"version": 1})

    @mark.req("REQ-GTB-025")
    def test_a_context_edge_names_stored_context_nodes(self):
        """TC-GTB-026: a context edge to a stored context node is accepted; to a missing one, or to the ID of a workflow node, it is refused naming the end.

        Example: edge e1 from c1 to c9 with only c1 stored -> unknown_endpoint "c9"; a workflow node named n9 does not count.
        """
        # Given: one stored context node c1 and one stored workflow node n9
        store = GraphStoreStandIn()
        store.put("context_nodes", "c1", cnode("c1"), WHO)
        store.put("graph_nodes", "n9", {"id": "n9", "data": {"type": "data"}}, WHO)
        # When/Then: an end that is not a stored context node is refused naming it, also when a workflow node has that ID
        self.assertEqual(refusal(self, store, "context_edges", "e1", cedge("e1", "c1", "c9")), ("unknown_endpoint", "c9"))
        self.assertEqual(refusal(self, store, "context_edges", "e1", cedge("e1", "c1", "n9")), ("unknown_endpoint", "n9"))
        # And: the twin, an edge between stored context nodes, is accepted
        self.assertEqual(store.put("context_edges", "e1", cedge("e1", "c1", "c1"), WHO), {"version": 1})

    @mark.req("REQ-GTB-026")
    def test_a_context_header_names_stored_context_members(self):
        """TC-GTB-027: a header of kind context naming a stored context node is accepted; a missing one, or a workflow node, is refused as unknown_member.

        Example: header h1 of kind context naming c9 with only c1 stored -> unknown_member "c9"; a workflow header naming c1 -> unknown_member "c1".
        """
        # Given: one stored context node c1
        store = GraphStoreStandIn()
        store.put("context_nodes", "c1", cnode("c1"), WHO)
        # When/Then: a context header naming a missing member, and a workflow header naming the context node, are refused naming the member
        self.assertEqual(refusal(self, store, "graphs", "h1", header("h1", "context", ["c9"])), ("unknown_member", "c9"))
        self.assertEqual(refusal(self, store, "graphs", "h2", header("h2", "workflow", ["c1"])), ("unknown_member", "c1"))
        # And: the twin, a context header naming the stored node, is accepted
        self.assertEqual(store.put("graphs", "h1", header("h1", "context", ["c1"]), WHO), {"version": 1})

    @mark.req("REQ-GTB-027")
    def test_input_that_cannot_be_checked_is_a_schema_break_naming_the_field(self):
        """TC-GTB-028: a record nested deeper than 200 levels is schema_break naming data; a category whose schema is not valid is schema_break naming type; nothing raises.

        Example: a data node whose value is a list nested 300 times -> {"rule": "schema_break", "detail": "data"}; categories {"entity": {"type": 5}} -> detail "type".
        """
        # Given: a data node whose value is nested 300 levels, one nested 150 levels (still checkable), and a category with an invalid schema
        deep, ok = 1, 1
        for _ in range(300):
            deep = [deep]
        for _ in range(150):
            ok = [ok]
        too_deep = {"id": "d1", "data": {"type": "data", "value": deep}}
        deep_enough = {"id": "d1", "data": {"type": "data", "value": ok}}
        # When/Then: the deep record is refused as schema_break naming data, in check_record and in to_object, and does not raise
        refused = {"rule": "schema_break", "detail": "data"}
        self.assertEqual(graph_tables.check_record("graph_nodes", too_deep), refused)
        self.assertEqual(graph_tables.to_object(too_deep), {"refused": refused})
        # And: the twin nested 150 levels is accepted
        self.assertIsNone(graph_tables.check_record("graph_nodes", deep_enough))
        # When/Then: a category whose schema is not valid gives schema_break naming type, for a workflow-table and a context-table record
        bad = {"entity": {"type": 5}}
        broken = {"rule": "schema_break", "detail": "type"}
        self.assertEqual(graph_tables.check_record("graph_nodes", cnode("c1"), categories=bad), broken)
        self.assertEqual(graph_tables.check_record("context_nodes", cnode("c1"), categories=bad), broken)


if __name__ == "__main__":
    unittest.main()
