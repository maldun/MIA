"""The loader of graphs (G-V4.GRAPHAPI.RUN T-01, IF-301 v5): edge cases the acceptance checks do not spell out. Run with: python tests/test_graph_loader.py"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from graph_rule_set import load                                              # noqa: E402
from markers import mark                                                     # noqa: E402


def step(step_id, **data):
    return {"id": step_id, "data": data}


def edge(edge_id, start, end, **data):
    return {"id": edge_id, "from": start, "to": end, "data": data}


class LoaderUnit(unittest.TestCase):

    @mark.req("REQ-GTB-057")
    def test_a_second_step_with_a_used_id_leaves_the_first_as_it_was(self):
        """A second step d1 is left out: the first d1 keeps its data and position (networkx would overwrite them on a second add_node).

        Example: data d1 then transform d1 give d1 with type data and position 0.
        """
        # Given: two steps with the ID d1
        stored = {"nodes": [step("d1", type="data"), step("d1", type="transform")], "edges": []}
        # When: it is loaded
        loaded = load(stored)
        # Then: d1 is the first step
        self.assertEqual(dict(loaded.nodes(data=True)), {"d1": {"data": {"type": "data"}, "position": 0}})

    @mark.req("REQ-GTB-057")
    def test_a_second_connection_with_a_used_id_is_left_out(self):
        """Connection IDs are keys: the first connection with an ID is kept, a later one with the same ID is left out, even between other steps.

        Example: e1 d1→t1 and e1 t1→d2 give one edge, d1→t1.
        """
        # Given: two connections with the ID e1
        stored = {"nodes": [step("d1"), step("t1"), step("d2")], "edges": [edge("e1", "d1", "t1"), edge("e1", "t1", "d2")]}
        # When: it is loaded
        loaded = load(stored)
        # Then: only the first is an edge
        self.assertEqual(list(loaded.edges(keys=True)), [("d1", "t1", "e1")])

    @mark.req("REQ-GTB-057")
    def test_a_connection_to_a_step_that_is_not_there_is_left_out(self):
        """A connection whose end names no well-formed step is left out, and no node is made for the missing end.

        Example: e1 d1→ghost gives no edge and the nodes stay [d1].
        """
        # Given: a connection to a step that does not exist
        stored = {"nodes": [step("d1")], "edges": [edge("e1", "d1", "ghost")]}
        # When: it is loaded
        loaded = load(stored)
        # Then: no edge, no extra node
        self.assertEqual((list(loaded.nodes), loaded.number_of_edges()), (["d1"], 0))

    @mark.req("REQ-GTB-056")
    def test_the_graph_fields_are_copies(self):
        """The graph's own fields are copied too: a change of a nested header field of the loaded graph leaves the stored form as it was.

        Example: appending to G.graph["context"]["ids"] leaves the stored ["a"].
        """
        # Given: a stored form with a nested header field
        stored = {"id": "g", "context": {"ids": ["a"]}, "nodes": [], "edges": []}
        # When: it is loaded and the loaded field is changed
        load(stored).graph["context"]["ids"].append("b")
        # Then: the stored form is unchanged
        self.assertEqual(stored["context"], {"ids": ["a"]})

    @mark.req("REQ-GTB-053")
    def test_an_empty_stored_form_gives_an_empty_workflow_graph(self):
        """A graph with no steps loads as an empty graph of kind workflow.

        Example: {} gives no nodes, no edges and kind workflow.
        """
        # Given: an empty stored form
        # When: it is loaded
        loaded = load({})
        # Then: empty, kind workflow
        self.assertEqual((loaded.number_of_nodes(), loaded.number_of_edges(), loaded.graph), (0, 0, {"kind": "workflow"}))


if __name__ == "__main__":
    unittest.main()
