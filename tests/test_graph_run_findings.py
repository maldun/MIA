"""
Findings of the first Verify run at the runner (N-2.4.1, G-V2.MODEL T-08): F-05 (REQ-RUN-016, REQ-RUN-017) and the owner's decisions of 2026-11-08 for REQ-RUN-017.
A graph the runner cannot put in an order is refused before any node ran; an unknown trust status is refused; `named_status` is the status of the first refused node.
Run with: python tests/test_graph_run_findings.py
"""

import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                              # noqa: E402
from graph_model_fakes import Script, data_node, make_edge, make_graph, transform_node   # noqa: E402
from graph_run import GraphRunner                                     # noqa: E402
from graph_model import check_graph, find_cycle                       # noqa: E402


class GraphRunFindings(unittest.TestCase):
    def setUp(self):
        self.script = Script()
        self.addCleanup(shutil.rmtree, self.script.folder, True)
        self.status = {}
        self.runner = GraphRunner(lambda node_id: self.status.get(node_id, "trusted"))

    def cyclic_graph(self):
        # D0 -> T0 -> D9 is the acyclic part; D1 -> T1 -> D2 -> T2 -> D1 is the cycle
        return make_graph("wf-cycle", [data_node(i) for i in ("D0", "D9", "D1", "D2")] + [transform_node(i) for i in ("T0", "T1", "T2")],
                          [make_edge("D0", "T0"), make_edge("T0", "D9"), make_edge("D1", "T1"), make_edge("T1", "D2"),
                           make_edge("D2", "T2"), make_edge("T2", "D1")])

    def nodes(self, *ids):
        return {i: self.script.marker_node(i) for i in ids}

    @mark.req("REQ-RUN-016")
    def test_a_graph_with_a_cycle_is_refused_and_no_node_runs(self):
        """F-05 (REQ-RUN-016): a cycle has no order, so the run is refused naming the cycle, not "done"; the acyclic part does not run on partial data.

        Example: D1 -> T1 -> D2 -> T2 -> D1 next to D0 -> T0 -> D9: status "refused", named holds T1 and T2, no marker file, no exception.
        """
        # Given: a graph with a cycle and an independent acyclic part, all nodes trusted
        graph = self.cyclic_graph()
        # When: it is run
        result = self.runner.run(graph, self.nodes("T0", "T1", "T2"), {"D0": "s", "D1": "x"})
        # Then: the run is refused naming the nodes of the cycle, and no node ran
        self.assertEqual(result.status, "refused")
        self.assertTrue({"T1", "T2"} <= set(result.named))
        self.assertFalse(any(self.script.marker_exists(i) for i in ("T0", "T1", "T2")))

    @mark.req("REQ-RUN-017")
    def test_an_untrusted_node_inside_a_cycle_is_refused_without_an_exception(self):
        """F-05 (REQ-RUN-017): an untrusted node inside a cycle gives a refused result, not an IndexError.

        Example: T1 untrusted in the cycle D1 -> T1 -> D2 -> T2 -> D1: status "refused", no marker file.
        """
        # Given: the cyclic graph with T1 untrusted
        self.status["T1"] = "untrusted"
        # When: it is run
        result = self.runner.run(self.cyclic_graph(), self.nodes("T0", "T1", "T2"), {"D0": "s"})
        # Then: refused, and no node ran
        self.assertEqual(result.status, "refused")
        self.assertFalse(any(self.script.marker_exists(i) for i in ("T0", "T1", "T2")))

    @mark.req("REQ-RUN-016")
    def test_an_edge_to_an_unknown_node_is_refused_without_an_exception(self):
        """F-05 (REQ-RUN-016): an edge that ends at, or starts from, a node that is not in the graph gives a refused result naming the edge.

        Example: edge T1>X9 and edge X8>T1 in a graph without X9 and X8: status "refused", named holds "T1>X9" resp. "X8>T1", no marker file.
        """
        for edge in (make_edge("T1", "X9"), make_edge("X8", "T1")):
            with self.subTest(edge=edge["id"]):
                # Given: a graph with an edge to or from an unknown node
                graph = make_graph("wf-unknown", [data_node("D1"), transform_node("T1"), data_node("D2")],
                                   [make_edge("D1", "T1"), make_edge("T1", "D2"), edge])
                # When: it is run
                result = self.runner.run(graph, self.nodes("T1"), {"D1": "s"})
                # Then: refused naming the edge, no node ran
                self.assertEqual((result.status, result.named), ("refused", [edge["id"]]))
                self.assertFalse(self.script.marker_exists("T1"))

    @mark.req("REQ-RUN-017")
    def test_an_unknown_trust_status_is_refused(self):
        """Owner's decision 2026-11-08 (REQ-RUN-017): any status except "trusted" refuses the run (fail safe), also one the runner does not know.

        Example: T9 has the status "revoked": status "refused", named ["T9"], named_status "revoked", no marker file.
        """
        # Given: a graph with a transform whose status is not one of the two defined ones
        graph = make_graph("wf-revoked", [data_node("D1"), transform_node("T9"), data_node("D2")], [make_edge("D1", "T9"), make_edge("T9", "D2")])
        self.status["T9"] = "revoked"
        # When: it is run
        result = self.runner.run(graph, self.nodes("T9"), {"D1": "s"})
        # Then: refused naming T9 and its status; the node did not run
        self.assertEqual((result.status, result.named, result.named_status), ("refused", ["T9"], "revoked"))
        self.assertFalse(self.script.marker_exists("T9"))

    @mark.req("REQ-RUN-017")
    def test_with_several_refused_nodes_named_is_in_run_order_and_the_status_is_the_first_ones(self):
        """Owner's decision 2026-11-08 (REQ-RUN-017): `named_status` stays one value, the status of the first refused node in the order of the run.

        Example: T1 "untrusted" before T2 "revoked" in D1 -> T1 -> D2 -> T2 -> D3: named ["T1", "T2"], named_status "untrusted".
        """
        # Given: two refused transforms with different statuses, T1 before T2
        graph = make_graph("wf-two", [data_node("D1"), transform_node("T1"), data_node("D2"), transform_node("T2"), data_node("D3")],
                           [make_edge("D1", "T1"), make_edge("T1", "D2"), make_edge("D2", "T2"), make_edge("T2", "D3")])
        self.status.update(T1="untrusted", T2="revoked")
        # When: it is run
        result = self.runner.run(graph, self.nodes("T1", "T2"), {"D1": "s"})
        # Then: both are named in the order of the run and the status is the one of T1
        self.assertEqual((result.status, result.named, result.named_status), ("refused", ["T1", "T2"], "untrusted"))

    @mark.req("REQ-RUN-016")
    def test_a_cycle_is_named_with_the_first_id_repeated_at_the_end_as_an_exact_list(self):
        """T-08 test gap (REQ-RUN-016, REQ-WFM-047): the cycle is reported as IDs, the first repeated at the end, compared as a list; `named_status` is None; the trust callback is not asked.

        Example: D1 -> T1 -> D1 gives named ["D1", "T1", "D1"]; the 4-node cycle gives ["D1", "T1", "D2", "T2", "D1"]; named_status None, no trust call.
        """
        asked = []
        runner = GraphRunner(lambda node_id: asked.append(node_id) or "trusted")
        two = make_graph("wf-two-cycle", [data_node("D1"), transform_node("T1")], [make_edge("D1", "T1"), make_edge("T1", "D1")])
        for graph, expected in ((two, ["D1", "T1", "D1"]), (self.cyclic_graph(), ["D1", "T1", "D2", "T2", "D1"])):
            with self.subTest(graph=graph["id"]):
                # Given: a graph with a cycle and a trust callback that records its calls
                # When: it is run
                result = runner.run(graph, self.nodes("T0", "T1", "T2"), {"D0": "s", "D1": "x"})
                # Then: refused, the cycle is the exact list, no status is named, the callback was not asked
                self.assertEqual((result.status, result.named, result.named_status), ("refused", expected, None))
                self.assertEqual(asked, [])

    @mark.req("REQ-RUN-016")
    def test_a_chain_and_a_cycle_of_three_thousand_nodes_do_not_depend_on_the_python_stack(self):
        """F-12 (REQ-RUN-016): the cycle search is iterative; a long chain runs, a long cycle is refused naming it, nothing raises RecursionError.

        Example: D0 -> T0 -> D1 -> ... with 3000 nodes runs to "done"; the same chain closed by an edge back to D0 is "refused" with 3001 IDs, the first repeated at the end.
        """
        # Given: a chain of 3000 nodes of alternating data and transform nodes, and the same chain closed to a cycle
        ids = [("D%d" if i % 2 == 0 else "T%d") % (i // 2) for i in range(3000)]
        kinds = {i: (data_node if i[0] == "D" else transform_node)(i) for i in ids}
        edges = [make_edge(a, b) for a, b in zip(ids, ids[1:])]
        chain = make_graph("wf-chain", list(kinds.values()), edges)
        closed = make_graph("wf-closed", list(kinds.values()), edges + [make_edge(ids[-1], ids[0])])
        # (the last node is a transform, so the closing edge goes transform -> data D0)
        self.assertEqual((len(ids), ids[-1][0]), (3000, "T"))
        scripted = {i: (lambda inputs: "v") for i in ids if i[0] == "T"}
        # When: both are run, and the rules of the model are asked
        done = self.runner.run(chain, scripted, {"D0": "s"})
        refused = self.runner.run(closed, scripted, {"D0": "s"})
        # Then: the chain is done, the cycle is refused with the whole cycle named; the model agrees
        self.assertEqual((done.status, done.named), ("done", []))
        self.assertEqual((refused.status, refused.named_status), ("refused", None))
        self.assertEqual(refused.named, ids + ["D0"])
        self.assertEqual(check_graph(chain), [])
        self.assertEqual(check_graph(closed), ids + ["D0"])
        self.assertEqual(find_cycle(ids, closed["edges"]), ids + ["D0"])


if __name__ == "__main__":
    unittest.main()
