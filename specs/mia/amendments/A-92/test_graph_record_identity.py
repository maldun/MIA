"""
Acceptance test of the record identity (N-3.2 Graph tables, G-V2.STORE, A-92): TC-GTB-022 (REQ-GTB-021) through the storage stand-in of
tests/helpers/graph_store_standin.py (which passes the IF-102 suite first, TR-GTB-002). The expected values are written by hand (TR-GTB-001).
Run with: python tests/acceptance/test_graph_record_identity.py
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

RECORD_TABLES = {t: {"versioned": True, "deletable": False} for t in ("graph_nodes", "graph_edges", "graphs", "skills")}


class RecordIdentityAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-021")
    def test_a_record_under_another_id_is_refused(self):
        """TC-GTB-022: a node whose own ID is n1 is accepted under the record ID n1 and refused under the record ID x, naming the field id; nothing is stored under x.

        Example: {"id": "n1", ...} written under "n1" -> version 1; written under "x" -> refused (record_identity, "id"); the store holds only n1.
        """
        # Given: the Graph tables define the record tables, and a node whose own ID is n1
        self.assertEqual(graph_tables.record_definitions(), RECORD_TABLES)
        store = GraphStoreStandIn()
        record = {"id": "n1", "data": {"type": "data"}}
        # When: it is written under the record ID x
        with self.assertRaises(StorageError) as caught:
            store.put("graph_nodes", "x", record, "anna")
        # Then: it is refused, the rule is record_identity and it names the field id
        self.assertEqual((caught.exception.code, caught.exception.rule, caught.exception.detail), ("invalid", "record_identity", "id"))
        # And: nothing is stored under x
        self.assertEqual(store.ids("graph_nodes"), [])
        # When: the same node is written under the record ID n1 (the twin differs only in the broken rule)
        # Then: it is accepted as version 1
        self.assertEqual(store.put("graph_nodes", "n1", record, "anna"), {"version": 1})
        self.assertEqual(store.ids("graph_nodes"), ["n1"])


if __name__ == "__main__":
    unittest.main()
