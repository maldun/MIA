"""IF-301 v5, the loader of graphs (A-187, D-473, D-475): the contract suite runs golden examples 32 to 35 against the mock
(tests/helpers/mocks/if_301_graph_tables_v5.py) and the real `load` of the module graph_rule_set of N-3.2. The cases of v1 to v4 stay in their own files,
unchanged (REQ-GTB-060). Expected values are exact (TR-RUN-001); the mock and the real module must agree on every case (TR-RUN-010). networkx is imported
inside the tests, so a module without it still imports (the real side fails on an assertion or NotImplementedError, never on import). Protected after the Plan gate.

Run with: python tests/acceptance/contract/test_if_301_v5_load.py
"""
import copy
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(REPO, "tests", "helpers", "mocks"))

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402
from rules_graphs import connection, converted_skill, data, graph, step, transform   # noqa: E402

IF = "IF-301"


def subject(kind):
    """The provider: the v5 mock, or the real module graph_rule_set loaded from the repository (never a cached module of the same name)."""
    if kind == "mock":
        from if_301_graph_tables_v5 import LoaderV5Mock
        return LoaderV5Mock()
    spec = importlib.util.spec_from_file_location("graph_rule_set_real", os.path.join(REPO, "graph_rule_set.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def golden33():
    """steps d1 (data) and t1 (transform), connections e1 and e2 (as = b), both from d1 to t1"""
    return {"nodes": [{"id": "d1", "data": {"type": "data"}}, {"id": "t1", "data": {"type": "transform", "toolbox_id": "x"}}],
            "edges": [{"id": "e1", "from": "d1", "to": "t1", "data": {}}, {"id": "e2", "from": "d1", "to": "t1", "data": {"as": "b"}}]}


@contract
class LoaderV5Contract(unittest.TestCase):

    @mark.req("IF-301", "REQ-GTB-053", "REQ-GTB-054", "REQ-GTB-055")
    @each_provider(IF, make=subject)
    def test_golden_32_load_review_full(self, rules):
        """TC-IF-301-35: review_full loads to nodes and edge keys equal to its step and connection IDs, with data and position as stored.

        Example: nodes == its 8 step IDs, edge keys == its 7 connection IDs, "step.step" has six incoming edges named question, criteria, ...
        """
        # Given: the stored form of the converted review_full skill
        stored = converted_skill("review_full.md")
        # When: it is loaded
        loaded = rules.load(stored)
        # Then: exactly its steps are nodes and exactly its connections are edge keys
        self.assertEqual(list(loaded.nodes), [s["id"] for s in stored["nodes"]])
        self.assertEqual(sorted(key for _, _, key in loaded.edges(keys=True)), sorted(e["id"] for e in stored["edges"]))
        # And: data is the step's or connection's data and position its index
        for index, s in enumerate(stored["nodes"]):
            self.assertEqual((loaded.nodes[s["id"]]["data"], loaded.nodes[s["id"]]["position"]), (s["data"], index))
        for index, e in enumerate(stored["edges"]):
            attributes = loaded.edges[e["from"], e["to"], e["id"]]
            self.assertEqual((attributes["data"], attributes["position"]), (e["data"], index))
        # And: the step that reads six data steps has six incoming edges with six names
        names = [attributes["data"]["as"] for _, _, attributes in loaded.in_edges("step.step", data=True)]
        self.assertEqual(sorted(names), ["abstract_statement", "conclusion", "criteria", "model", "question", "section_notes"])
        # And: the graph attributes are the header fields, with the kind workflow where the stored form names none
        self.assertEqual(dict(loaded.graph), {**{k: v for k, v in stored.items() if k not in ("nodes", "edges")}, "kind": "workflow"})

    @mark.req("IF-301", "REQ-GTB-053", "REQ-GTB-056")
    @each_provider(IF, make=subject)
    def test_golden_33_parallel_connections(self, rules):
        """TC-IF-301-36: two connections from d1 to t1 give two edges keyed e1 and e2; the graph attribute kind is workflow.

        Example: sorted(G.edges(keys=True)) == [("d1", "t1", "e1"), ("d1", "t1", "e2")].
        """
        # Given: golden 33; When: it is loaded
        loaded = rules.load(golden33())
        # Then: both connections are there, with their data, and the kind is workflow
        self.assertEqual(sorted(loaded.edges(keys=True)), [("d1", "t1", "e1"), ("d1", "t1", "e2")])
        self.assertEqual(loaded.edges["d1", "t1", "e2"]["data"], {"as": "b"})
        self.assertEqual(loaded.graph["kind"], "workflow")

    @mark.req("IF-301", "REQ-GTB-057")
    @each_provider(IF, make=subject)
    def test_golden_34_left_out(self, rules):
        """TC-IF-301-37: malformed items are left out and nothing raises; a non-graph gives an empty graph.

        Example: a step 5 and a step without id are not nodes; "nodes" = "x" gives no nodes.
        """
        # Given: the cases of golden 31 that leave something out, a second step d1, a connection to a step left out, and inputs that are no graph
        cases = [  # label, the input, node IDs, edge keys of the loaded graph
            ("a step that is 5", graph([5, data("a")], []), ["a"], []),
            ("a step without id", graph([{"data": {"type": "data"}}, data("a")], []), ["a"], []),
            ("a connection without from", graph([data("a"), transform("t")], [{"id": "e1", "to": "t", "data": {}}, connection("e2", "a", "t")]), ["a", "t"], ["e2"]),
            ("a second step d1", graph([data("d1"), transform("d1")], []), ["d1"], []),
            ("a connection to a step left out", graph([data("a"), step("", "data")], [connection("e1", "a", "")]), ["a"], []),
            ("nodes is a text", {"id": "g", "nodes": "x", "edges": []}, [], []),
            ("nodes is None", {"id": "g", "nodes": None, "edges": []}, [], []),
            ("the input is None", None, [], []),
        ]
        for label, given, node_ids, edge_keys in cases:
            with self.subTest(case=label):
                # When: it is loaded; Then: no exception, and exactly the well-formed items
                loaded = rules.load(given)
                self.assertEqual(list(loaded.nodes), node_ids)
                self.assertEqual([key for _, _, key in loaded.edges(keys=True)], edge_keys)
        # And: the second d1 is the first one, as stored
        self.assertEqual(rules.load(cases[3][1]).nodes["d1"]["data"], {"type": "data"})
        # And: golden 31's connection with data [] is well-formed: kept, with empty data (D-481)
        listed = rules.load(graph([data("a"), transform("t")], [{"id": "e1", "from": "a", "to": "t", "data": []}]))
        self.assertEqual([(s, e, k, a["data"]) for s, e, k, a in listed.edges(keys=True, data=True)], [("a", "t", "e1", {})])

    @mark.req("IF-301", "REQ-GTB-058")
    @each_provider(IF, make=subject)
    def test_golden_35_copies(self, rules):
        """TC-IF-301-38: a change of the loaded graph leaves the stored form as it was, and the other way round.

        Example: G.nodes["d1"]["data"]["value"] = 9 leaves the stored d1 without "value".
        """
        # Given: golden 33 and a deep copy of it
        stored = golden33()
        before = copy.deepcopy(stored)
        loaded = rules.load(stored)
        # When: the loaded graph is changed; Then: the stored form is as before
        loaded.nodes["d1"]["data"]["value"] = 9
        loaded.edges["d1", "t1", "e2"]["data"]["as"] = "changed"
        self.assertEqual(stored, before)
        # When: the stored form is changed afterwards; Then: the loaded graph is as it was
        stored["nodes"][0]["data"]["type"] = "transform"
        stored["edges"][1]["data"]["as"] = "again"
        self.assertEqual((loaded.nodes["d1"]["data"], loaded.edges["d1", "t1", "e2"]["data"]), ({"type": "data", "value": 9}, {"as": "changed"}))


if __name__ == "__main__":
    unittest.main()
