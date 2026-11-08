"""
Acceptance test of the size of a record (N-3.2 Graph tables, G-V2.STORE, A-102): TC-GTB-029 (REQ-GTB-028) through the storage stand-in of
tests/helpers/graph_store_standin.py (which passes the IF-102 suite first, TR-GTB-002). The expected values are written by hand (TR-GTB-001).
Run with: python tests/acceptance/test_graph_document_size.py
"""

import os
import sys
import threading
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

WHO = "anna"
LIMIT_SECONDS = 5


def data_node(node_id, value):
    return {"id": node_id, "data": {"type": "data", "value": value}}


def put_within_limit(store, record):
    """('stored', result) or ('refused', (rule, detail)) or ('no answer', None): put runs in a daemon thread, so a hang fails the test and does not stall the suite."""
    answer = {}

    def run():
        try:
            answer["result"] = ("stored", store.put("graph_nodes", record["id"], record, WHO))
        except StorageError as error:
            answer["result"] = ("refused", (error.rule, error.detail))
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(LIMIT_SECONDS)
    return answer.get("result", ("no answer", None))


class DocumentSizeAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-028")
    def test_a_record_with_too_many_values_is_refused_naming_data(self):
        """TC-GTB-029: a record of 100 001 values, and one that shares sub-objects so that it has 2**30 paths, are refused as schema_break naming data within 5 s; 100 000 values are accepted.

        Example: a data node whose value is a list of 99 995 numbers is stored (100 000 values); one of 99 996 numbers is refused (schema_break, "data").
        """
        # Given: three data nodes. The record, its id, the data object, its type and the value list count 5 values besides the numbers
        at_limit = data_node("d1", [1] * 99995)                  # 5 + 99 995 = 100 000 values
        over_limit = data_node("d2", [1] * 99996)                # 100 001 values
        shared = 1
        for _ in range(30):
            shared = [shared, shared]                           # 31 levels deep, the same child twice per level: 2**30 paths
        many_paths = data_node("d3", shared)
        # When/Then: the record at the limit is stored as version 1
        store = GraphStoreStandIn()
        self.assertEqual(put_within_limit(store, at_limit), ("stored", {"version": 1}))
        # And: the record over the limit is refused as schema_break naming data
        self.assertEqual(put_within_limit(store, over_limit), ("refused", ("schema_break", "data")))
        # And: the record with 2**30 paths is refused the same way within the time limit, not after minutes
        self.assertEqual(put_within_limit(store, many_paths), ("refused", ("schema_break", "data")))
        # And: the refusals stored nothing
        self.assertEqual(store.ids("graph_nodes"), ["d1"])


if __name__ == "__main__":
    unittest.main()
