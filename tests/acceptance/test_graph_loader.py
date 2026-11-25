"""Acceptance tests of the loader and of the rules on the loaded graph (G-V4.GRAPHAPI.RUN, protected after the Plan gate): TC-GTB-048 to TC-GTB-052
(REQ-GTB-053 to REQ-GTB-060, TR-RUN-001 to 004, 008) against `graph_rule_set.load` (IF-301 v5) and the rule set of v4. Expected values are exact.
RED until the loader task: `load` raises NotImplementedError; TC-GTB-052 is green from the start (it guards the change, against the oracle).
Run with: python tests/acceptance/test_graph_loader.py
"""
import copy
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

from markers import mark                                                        # noqa: E402
from rules_graphs import SKILL_COUNT, connection, converted_skills, data, graph, step, transform   # noqa: E402
from run_graphs import random_graphs                                            # noqa: E402
from run_store import oracle                                                    # noqa: E402
import graph_rule_set as rules                                                  # noqa: E402


def golden33():
    """steps d1 (data) and t1 (transform), connections e1 and e2 (as = b), both from d1 to t1"""
    return {"id": "g33", "nodes": [{"id": "d1", "data": {"type": "data"}}, {"id": "t1", "data": {"type": "transform", "toolbox_id": "x"}}],
            "edges": [{"id": "e1", "from": "d1", "to": "t1", "data": {}}, {"id": "e2", "from": "d1", "to": "t1", "data": {"as": "b"}}]}


def skills():
    """the 15 converted skill graphs, built at test time; the check fails with fewer than 15 or without the three named skills (TR-RUN-004)"""
    built = dict(converted_skills())
    assert len(built) >= SKILL_COUNT, "only %d converted skill graphs" % len(built)
    for name in ("review_full.md", "research.md", "verify_computable.md"):
        assert name in built, "the converted skill %s is missing (TR-RUN-004)" % name
    return built


class LoadedGraph(unittest.TestCase):
    @mark.req("REQ-GTB-053")
    def test_one_node_per_step_and_one_edge_per_connection(self):
        """TC-GTB-048: every converted skill graph loads to exactly its step IDs and connection IDs; golden 33 gives two parallel edges.

        Example: golden 33 -> edges [("d1", "t1", "e1"), ("d1", "t1", "e2")].
        """
        # Given: the 15 converted skill graphs and golden 33
        # When: each is loaded
        # Then: the nodes are exactly the step IDs and the edge keys exactly the connection IDs, in the listed order
        for name, stored in skills().items():
            with self.subTest(skill=name):
                loaded = rules.load(stored)
                self.assertEqual(list(loaded.nodes), [s["id"] for s in stored["nodes"]])
                self.assertEqual(sorted(key for _, _, key in loaded.edges(keys=True)), sorted(e["id"] for e in stored["edges"]))
        # And: golden 33 gives two edges from d1 to t1, keyed e1 and e2
        self.assertEqual(sorted(rules.load(golden33()).edges(keys=True)), [("d1", "t1", "e1"), ("d1", "t1", "e2")])

    @mark.req("REQ-GTB-054", "REQ-GTB-055", "REQ-GTB-056")
    def test_everything_the_run_needs_is_on_the_loaded_graph(self):
        """TC-GTB-049: data and position of every step and connection, six names on one step of review_full, the header fields as graph attributes.

        Example: G.graph == {"id": "g1", "description": "test", "kind": "workflow"} for a form without kind.
        """
        # Given: the 15 converted skill graphs; the converted review_full; a stored form with kind, id and description, and the same without kind
        # When: each is loaded
        for name, stored in skills().items():
            with self.subTest(skill=name):
                loaded = rules.load(stored)
                # Then: every step's data and position, every connection's data and position, as stored
                for index, s in enumerate(stored["nodes"]):
                    self.assertEqual((loaded.nodes[s["id"]]["data"], loaded.nodes[s["id"]]["position"]), (s["data"], index))
                for index, e in enumerate(stored["edges"]):
                    attributes = loaded.edges[e["from"], e["to"], e["id"]]
                    self.assertEqual((attributes["data"], attributes["position"]), (e["data"], index))
        # And: the step of review_full that reads six data steps has six incoming edges with six different names
        loaded = rules.load(skills()["review_full.md"])
        names = sorted(a["data"]["as"] for _, _, a in loaded.in_edges("step.step", data=True))
        self.assertEqual(names, ["abstract_statement", "conclusion", "criteria", "model", "question", "section_notes"])
        # And: the graph attributes hold the header fields, with the kind workflow where none is named
        with_kind = {"id": "g1", "kind": "workflow", "description": "test", "nodes": [], "edges": []}
        self.assertEqual(dict(rules.load(with_kind).graph), {"id": "g1", "kind": "workflow", "description": "test"})
        without = {k: v for k, v in with_kind.items() if k != "kind"}
        self.assertEqual(dict(rules.load(without).graph), {"id": "g1", "kind": "workflow", "description": "test"})

    @mark.req("REQ-GTB-057", "REQ-GTB-058")
    def test_malformed_items_are_left_out_and_loading_copies(self):
        """TC-GTB-050: malformed steps and connections are left out and nothing raises; non-graphs give an empty graph; the loaded graph is a copy.

        Example: nodes "x" and nodes None give no nodes; two steps d1 give the first d1 at position 0; setting value 9 on the loaded d1 leaves the stored d1 without it.
        """
        # Given: the malformed graphs of golden 31, a graph with two steps d1, a connection to a step that was left out, inputs that are no graph
        cases = [  # label, the input, node IDs, edge keys
            ("a step that is 5", graph([5, data("a")], []), ["a"], []),
            ("a step without id", graph([{"data": {"type": "data"}}, data("a")], []), ["a"], []),
            ("a connection without from", graph([data("a"), transform("t")], [{"id": "e1", "to": "t", "data": {}}, connection("e2", "a", "t")]), ["a", "t"], ["e2"]),
            ("a second step d1", graph([data("d1"), transform("d1")], []), ["d1"], []),
            ("a connection to the step 5", graph([5, data("a")], [connection("e1", "a", 5)]), ["a"], []),
            ("connection data is a list", graph([data("a"), transform("t")], [{"id": "e1", "from": "a", "to": "t", "data": []}]), ["a", "t"], ["e1"]),
            ("nodes is a text", {"id": "g", "nodes": "x", "edges": []}, [], []),
            ("nodes is None", {"id": "g", "nodes": None, "edges": []}, [], []),
            ("no steps", graph([], []), [], []),
        ]
        for label, given, node_ids, edge_keys in cases:
            with self.subTest(case=label):
                # When: it is loaded; Then: no exception, exactly the well-formed items
                loaded = rules.load(given)
                self.assertEqual(list(loaded.nodes), node_ids)
                self.assertEqual([key for _, _, key in loaded.edges(keys=True)], edge_keys)
        # And: the second d1 is left out, so d1 keeps the first step's data and position 0 (networkx's add_node would overwrite them; A-188, F-1)
        twice = cases[3][1]
        self.assertEqual(dict(rules.load(twice).nodes(data=True)), {"d1": {"data": twice["nodes"][0]["data"], "position": 0}})
        # And: the kept connection with data [] has empty data (D-481)
        self.assertEqual(rules.load(cases[5][1]).edges["a", "t", "e1"]["data"], {})
        # And: a connection to the second d1 points at the first d1 and is kept
        kept = graph([data("d1"), transform("t1"), data("d1")], [connection("e1", "d1", "t1")])
        self.assertEqual(list(rules.load(kept).edges(keys=True)), [("d1", "t1", "e1")])
        # And: a change of the loaded graph leaves the stored form as it was, and the other way round
        stored = golden33()
        before = copy.deepcopy(stored)
        loaded = rules.load(stored)
        loaded.nodes["d1"]["data"]["value"] = 9
        self.assertEqual(stored, before)
        stored["nodes"][0]["data"]["type"] = "transform"
        self.assertEqual(loaded.nodes["d1"]["data"], {"type": "data", "value": 9})


class RulesReadTheLoadedGraph(unittest.TestCase):
    @mark.req("REQ-GTB-059")
    def test_the_rule_set_has_no_view_of_its_own(self):
        """TC-GTB-051 (the search of TR-RUN-008; the checklist is read by a person): no cycle finder or adjacency map in graph_rule_set.py, networkx imported.

        Example: the source has no `def _find_cycle` and no `following = {`; it imports networkx.
        """
        # Given: the source of graph_rule_set.py; When: it is searched; Then: the copies of old views are gone and the loader is the place that builds the graph
        with open(os.path.join(REPO, "graph_rule_set.py"), encoding="utf-8") as fp:
            source = fp.read()
        for forbidden in ("def _find_cycle", "following = {", "waiting = {", "writers = {"):
            self.assertFalse(forbidden in source, "graph_rule_set.py still contains %r" % forbidden)
        self.assertIn("networkx", source)


class AnswersAsBefore(unittest.TestCase):
    @mark.req("REQ-GTB-060", "HR-006")
    def test_every_answer_equals_the_recorded_one(self):
        """TC-GTB-052: rule_report and run_check on the converted skills, the 500 random graphs and the goldens equal the oracle recorded at goal/v4.

        Example: rule_report(research) equals the list recorded for research.md; 0 differences over 15 + 500 graphs.
        """
        # Given: the oracle (its commit an ancestor, its file the committed one) and the same graphs, built now
        recorded = oracle()
        built = skills()
        randoms = random_graphs()
        self.assertEqual(len(randoms), recorded["header"]["random_graphs"])
        self.assertEqual(sorted(built), recorded["header"]["converted_skills"])
        # When: every graph is checked with the changed code
        # Then: no answer differs from the recorded one
        differences = []
        for name, stored in built.items():
            if (rules.rule_report(stored), rules.run_check(stored)) != (recorded["converted"][name]["rule_report"], recorded["converted"][name]["run_check"]):
                differences.append(name)
        for index, (stored, was) in enumerate(zip(randoms, recorded["random"])):
            if (rules.rule_report(stored), rules.run_check(stored)) != (was["rule_report"], was["run_check"]):
                differences.append("random-%03d" % index)
        self.assertEqual(differences, [])

    @mark.req("REQ-GTB-060", "HR-006")
    def test_the_random_graphs_are_those_of_the_oracle(self):
        """TC-GTB-052 (TR-RUN-003): the generator gives 500 graphs, of which as many are acyclic as the oracle says.

        Example: 500 graphs, 159 acyclic (the order_of of the oracle reaches every step).
        """
        # Given: the generator and the oracle; When: the graphs are made; Then: the count and the acyclic count are the recorded ones
        recorded = oracle()
        randoms = random_graphs()
        acyclic = sum(1 for was in recorded["random"] if was["order"] is not None)
        self.assertEqual((len(randoms), acyclic), (500, recorded["header"]["random_acyclic"]))


if __name__ == "__main__":
    unittest.main()
