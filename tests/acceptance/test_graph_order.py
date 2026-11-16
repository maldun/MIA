"""
Acceptance tests of the order rule (G-V2.CONVERT, task T-CV-03c, A-123 P4, A-124, D-251): TC-RUN-035 (REQ-RUN-035) and TC-WFM-122 to TC-WFM-124 (preconditions of REQ-WFM-058).
RED until T-CV-03c: `graph_order.py` is a stub and the runner hands an order edge to the Stage.
What they fix: the old runner runs the steps of a pipeline in the order of the pipeline; a graph orders independent nodes by what they read. To keep the old order, the builder
`graph_order.order_steps(graph_id, steps)` lets each later step read an extra data node written by the step before it, over an edge with `role: "order"`; the runner uses such
an edge for the order only and never hands it to the Stage (REQ-RUN-035). Edges stay between data and transform nodes (no edge joins two process nodes).
A step is {"id", "toolbox_id", "reads": [(data node id, name)], "writes": [(data node id, name)]}; the name is the `as` field of the edge.
Run with: python tests/acceptance/test_graph_order.py
"""
import itertools
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

from markers import mark                                              # noqa: E402
from graph_model import check_graph, order_of                         # noqa: E402
from graph_model_fakes import data_node, make_edge, make_graph, transform_node   # noqa: E402
from graph_run import GraphRunner, Stage                              # noqa: E402
import graph_order                                                    # noqa: E402


def edge(start, end, **data):
    found = make_edge(start, end)
    found["data"] = dict(data)
    return found


STEPS = {
    "S1": {"id": "S1", "toolbox_id": "code.top_urls", "reads": [("DA", "hits")], "writes": [("D1", "out")]},
    "S2": {"id": "S2", "toolbox_id": "code.tally", "reads": [], "writes": [("D2", "out")]},           # reads nothing: ready first in a plain graph
    "S3": {"id": "S3", "toolbox_id": "code.tidy_claims", "reads": [("D1", "one")], "writes": [("D3", "out")]},   # needs the result of S1
    "S4": {"id": "S4", "toolbox_id": "code.apply_rules", "reads": [("DA", "hits")], "writes": [("D4", "out")]},
}


def listings():
    """every listing of the four steps in which S1 comes before S3 (the data flow), each as a list of fresh step dicts"""
    for ids in itertools.permutations(STEPS):
        if ids.index("S1") < ids.index("S3"):
            yield [dict(STEPS[i], reads=list(STEPS[i]["reads"]), writes=list(STEPS[i]["writes"])) for i in ids]


def transform_ids(graph):
    kinds = {n["id"]: n["data"]["type"] for n in graph["nodes"]}
    return [i for i in order_of(graph) if kinds[i] == "transform"]


class OrderRule(unittest.TestCase):
    @mark.req("REQ-RUN-035")
    def test_an_order_edge_orders_the_nodes_and_is_not_handed_to_the_stage(self):
        """TC-RUN-035: T reads DA (as "a") and DX over an edge with role order; P writes DX. Without the order edge T would run before P; with it P runs first, and T's
        inputs are {"a": 1} only: DX is neither an input name nor a value."""
        graph = make_graph("wf-order-edge", [data_node(i) for i in ("DA", "DB", "DX", "DO")] + [transform_node("P"), transform_node("T")],
                           [edge("DA", "T", **{"as": "a"}), edge("DB", "P"), edge("P", "DX"), edge("DX", "T", role="order"), edge("T", "DO")])
        seen = []

        def stage(inputs, outputs, node):
            seen.append(("T", dict(inputs)))
            return "t"

        def plain(inputs):
            seen.append(("P", dict(inputs)))
            return "p"

        result = GraphRunner(lambda node_id: "trusted").run(graph, {"P": plain, "T": Stage(stage)}, {"DA": 1, "DB": 2})
        self.assertEqual(result.status, "done")
        self.assertEqual(seen, [("P", {"DB": 2}), ("T", {"a": 1})])

    @mark.req("REQ-WFM-058")
    def test_the_built_graph_runs_the_steps_in_the_listed_order_whatever_they_read(self):
        """TC-WFM-122: for every listing of the four steps in which S1 comes before S3, the transforms of the built graph come in the order of `order_of` exactly as
        listed (S2 reads nothing and would otherwise run first), and the graph keeps the rules (alternation, one writer per data node, no cycle)."""
        count = 0
        for steps in listings():
            count += 1
            with self.subTest(listing=[s["id"] for s in steps]):
                before = [dict(s) for s in steps]
                graph = graph_order.order_steps("wf-steps", steps)
                self.assertIsNotNone(graph, "order_steps gave no graph")
                self.assertEqual(transform_ids(graph), [s["id"] for s in steps])
                self.assertEqual(check_graph(graph), [])
                self.assertEqual(steps, before, "order_steps changed its input")
        self.assertEqual(count, 12)

    @mark.req("REQ-WFM-058")
    def test_the_built_graph_keeps_the_given_edges_and_adds_only_order_edges_through_data_nodes(self):
        """TC-WFM-123: every read and write of a step is an edge with its `as` name; each added edge reads an extra data node with role order and no name; the extra data
        nodes are written by exactly one step; there are at most as many as steps minus one; every transform node carries its toolbox ID."""
        steps = next(iter(listings()))
        graph = graph_order.order_steps("wf-form", steps)
        self.assertIsNotNone(graph, "order_steps gave no graph")
        edges = {(e["from"], e["to"]): e["data"] for e in graph["edges"]}
        kinds = {n["id"]: n["data"]["type"] for n in graph["nodes"]}
        for step in steps:
            for node, name in step["reads"]:
                self.assertEqual(edges.get((node, step["id"])), {"as": name})
            for node, name in step["writes"]:
                self.assertEqual(edges.get((step["id"], node)), {"as": name})
        given = {(n, s["id"]) for s in steps for n, _ in s["reads"]} | {(s["id"], n) for s in steps for n, _ in s["writes"]}
        added = {pair: data for pair, data in edges.items() if pair not in given}
        order_reads = {pair: data for pair, data in added.items() if kinds[pair[1]] == "transform"}
        self.assertTrue(order_reads, "no order edge was added")
        self.assertTrue(all(data == {"role": "order"} for data in order_reads.values()))
        order_nodes = {pair[0] for pair in order_reads}
        self.assertLessEqual(len(order_nodes), len(steps) - 1)
        for node in order_nodes:
            self.assertEqual(len([p for p in added if p[1] == node and kinds[p[0]] == "transform"]), 1, "an order data node has not exactly one writer")
        self.assertEqual({n["id"]: n["data"].get("toolbox_id") for n in graph["nodes"] if n["data"]["type"] == "transform"},
                         {s["id"]: s["toolbox_id"] for s in steps})

    @mark.req("REQ-WFM-058")
    def test_the_built_graph_runs_in_the_listed_order_and_each_step_gets_only_its_own_inputs(self):
        """TC-WFM-124: the graph built for the listing S2, S1, S4, S3 is run with the Stage runner and recording stages: the calls come in that order, S3 reads the result
        of S1 under its name, and no stage sees an order input."""
        steps = [dict(STEPS[i], reads=list(STEPS[i]["reads"]), writes=list(STEPS[i]["writes"])) for i in ("S2", "S1", "S4", "S3")]
        graph = graph_order.order_steps("wf-run", steps)
        self.assertIsNotNone(graph, "order_steps gave no graph")
        calls = []

        def make(step_id):
            def stage(inputs, outputs, node):
                calls.append((step_id, dict(inputs)))
                return "result-of-" + step_id
            return Stage(stage)

        result = GraphRunner(lambda node_id: "trusted").run(graph, {s["id"]: make(s["id"]) for s in steps}, {"DA": ["a"]})
        self.assertEqual(result.status, "done")
        self.assertEqual(calls, [("S2", {}), ("S1", {"hits": ["a"]}), ("S4", {"hits": ["a"]}), ("S3", {"one": "result-of-S1"})])


if __name__ == "__main__":
    unittest.main()
