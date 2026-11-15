"""
Acceptance test of the fixed fields of a node (N-3.2 Graph tables, G-V2.STORE, A-93): TC-GTB-023 (REQ-GTB-022) through the storage stand-in of
tests/helpers/graph_store_standin.py (which passes the IF-102 suite first, TR-GTB-002). The expected values are written by hand (TR-GTB-001).
Run with: python tests/acceptance/test_graph_node_fields.py
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
from if_102_storage import StorageMock                             # noqa: E402
from graph_store_standin import GraphStoreStandIn                  # noqa: E402
import graph_tables                                                # noqa: E402

STOP = {"max_repetitions": 1}


def node(node_id, type_id, **fields):
    return {"id": node_id, "data": dict({"type": type_id}, **fields)}


class NodeFieldsAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-022")
    def test_a_node_with_an_extra_field_is_refused_on_write_and_on_read(self):
        """TC-GTB-023: a node whose JSON field holds a field its type does not list is refused on write and on read as schema_break naming the field.

        Example: {"id": "d1", "data": {"type": "data", "foo": 1}} -> write refused (schema_break, "foo"); read gives {"refused": schema_break, "foo"}, no exception.
        """
        # Given: one node per type with an extra field `foo`, and a data node with a key `id` inside its JSON field; each case gets its own store with one good node
        cases = [(node("d1", "data", foo=1), "foo"),
                 (node("t1", "transform", toolbox_id="t", foo=1), "foo"),
                 (node("m1", "master", toolbox_id="t", stop=STOP, foo=1), "foo"),
                 (node("d2", "data", id="x"), "id")]
        for record, field in cases:
            with self.subTest(record=record):
                store = GraphStoreStandIn()
                store.put("graph_nodes", "ok", node("ok", "transform", toolbox_id="t"), "anna")
                # When: it is written
                with self.assertRaises(StorageError) as caught:
                    store.put("graph_nodes", record["id"], record, "anna")
                # Then: it is refused as schema_break naming the extra field
                self.assertEqual((caught.exception.code, caught.exception.rule, caught.exception.detail), ("invalid", "schema_break", field))
                # And: nothing is stored under its ID
                self.assertEqual(store.ids("graph_nodes"), ["ok"])
                # When: the same record is already in storage (put past the check, as a record of an older or damaged writer) and is read
                StorageMock.put(store, "graph_nodes", record["id"], record, "anna")
                built = graph_tables.to_object(store.get("graph_nodes", record["id"])["doc"])
                # Then: the read is refused with the same rule and field, and does not raise
                self.assertEqual(built, {"refused": {"rule": "schema_break", "detail": field}})

    @mark.req("REQ-GTB-022")
    def test_the_twins_without_the_extra_field_are_accepted(self):
        """TC-GTB-023 twin: the same three nodes without the extra field are accepted as version 1, and a context-graph node keeps the fields its category allows.

        Example: {"id": "d1", "data": {"type": "data"}} -> version 1; a node of the category entity with a field foo and categories {"entity": {"type": "object"}} -> version 1.
        """
        # Given: an empty store
        store = GraphStoreStandIn()
        # When/Then: the twins differ from the refused nodes only in the broken rule, so each is accepted as version 1
        for record in (node("d1", "data"), node("t1", "transform", toolbox_id="t"), node("m1", "master", toolbox_id="t", stop=STOP)):
            self.assertEqual(store.put("graph_nodes", record["id"], record, "anna"), {"version": 1})
        # And: the schema of a context-graph node comes from its categories, not from the fixed list, so its extra field is not refused here
        categories = {"entity": {"type": "object"}}
        self.assertEqual(store.put("graph_nodes", "c1", node("c1", "entity", foo=1), "anna", categories=categories), {"version": 1})


if __name__ == "__main__":
    unittest.main()
