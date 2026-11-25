"""The loader of graphs (G-V4.GRAPHAPI.RUN T-01, IF-301 v5): edge cases the acceptance checks do not spell out. Run with: python tests/test_graph_loader.py"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from graph_model import order_of                                             # noqa: E402
from graph_rule_set import load, rule_report                                 # noqa: E402
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


class RulesAndOrderOnTheLoadedGraph(unittest.TestCase):
    """T-02: networkx lists edges grouped by their start step; parts and orders must follow the stored order of the connections (REQ-GTB-060)."""

    @mark.req("REQ-GTB-060")
    def test_adjacency_names_connections_in_their_stored_order(self):
        """Connections that join two data steps are named in the order of the stored form, not grouped by their start step.

        Example: e1 b→c listed before e2 a→b gives adjacency ["e1", "e2"].
        """
        # Given: three data steps; the connection from b is listed before the one from a
        stored = {"nodes": [step("a", type="data"), step("b", type="data"), step("c", type="data")],
                  "edges": [edge("e1", "b", "c"), edge("e2", "a", "b")]}
        # When: the rules are asked
        report = rule_report(stored)
        # Then: adjacency names e1 before e2
        self.assertEqual([(i["rule"], i["parts"]) for i in report], [("adjacency", ["e1", "e2"])])

    @mark.req("REQ-GTB-060")
    def test_single_writer_names_data_steps_in_the_order_of_their_first_written_connection(self):
        """A data step written by two steps is named in the order of the first connection into it, as v4 did.

        Example: d2 is written first (e1), d1 later: single_writer ["d2", "d1"].
        """
        # Given: transforms t and u both writing d1 and d2; the first connection listed goes into d2
        stored = {"nodes": [step("d1", type="data"), step("d2", type="data"), step("t", type="transform", toolbox_id="t"),
                            step("u", type="transform", toolbox_id="u")],
                  "edges": [edge("e1", "u", "d2"), edge("e2", "t", "d1"), edge("e3", "t", "d2"), edge("e4", "u", "d1")]}
        # When: the rules are asked
        report = rule_report(stored)
        # Then: d2 before d1
        self.assertEqual([(i["rule"], i["parts"]) for i in report], [("single_writer", ["d2", "d1"])])

    @mark.req("REQ-GTB-059", "REQ-GTB-060")
    def test_settings_connections_into_a_missing_step_are_rule_three_only(self):
        """Two settings connections into a step that does not exist are rule 3; stop_limit reads the loaded graph and no longer names it (D-484).

        Example: e2 s→z and e3 a→z with role settings give [connection_endpoints ["e2", "e3"]], no stop_limit ["z"] as in v4.
        """
        # Given: data steps a and s, a transform t, and two settings connections into the missing step z
        stored = {"nodes": [step("a", type="data"), step("s", type="data"), step("t", type="transform", toolbox_id="t")],
                  "edges": [edge("e1", "a", "t"), edge("e2", "s", "z", role="settings"), edge("e3", "a", "z", role="settings")]}
        # When: the rules are asked
        report = rule_report(stored)
        # Then: rule 3 only
        self.assertEqual([(i["rule"], i["parts"]) for i in report], [("connection_endpoints", ["e2", "e3"])])

    @mark.req("REQ-WFM-167")
    def test_a_step_reached_by_its_last_connection_later_becomes_ready_later(self):
        """Readiness follows the stored order of the connections: v, which also needs the third connection, becomes ready after w.

        Example: e1 u→v, e2 u→w, e3 u→v order u, w, v.
        """
        # Given: u with two connections to v and one to w between them
        stored = {"nodes": [step("u", type="transform"), step("v", type="data"), step("w", type="data")],
                  "edges": [edge("e1", "u", "v"), edge("e2", "u", "w"), edge("e3", "u", "v", **{"as": "again"})]}
        # When: the order is asked
        # Then: w before v
        self.assertEqual(order_of(stored), ["u", "w", "v"])


if __name__ == "__main__":
    unittest.main()
