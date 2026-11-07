"""Graph model of a workflow graph (N-2.3, G-V2.MODEL T-01): STUB, written in Plan step 4 so the red tests import.

Real behaviour comes with plan task T-01 (REQ-WFM-043 to 049). The tests in tests/acceptance/test_graph_model.py fix this interface:
- GraphModel(tables): `tables` has put(table, id, doc) -> version, get(table, id, version=None), versions(table, id).
- save_graph(graph) -> SaveResult(saved, version, named): `named` lists the IDs a refusal names (a node, an edge, a data node, or a cycle as IDs).
- read_graph(graph_id, version=None) -> the stored graph dict.
- topological_order(graph_id) -> the node IDs of a stored graph in an order in which every edge points forward.
"""

from collections import namedtuple

SaveResult = namedtuple("SaveResult", "saved version named")


class GraphModel:
    def __init__(self, tables):
        self.tables = tables

    def save_graph(self, graph):
        return SaveResult(False, None, [])

    def read_graph(self, graph_id, version=None):
        return {}

    def topological_order(self, graph_id):
        return []
