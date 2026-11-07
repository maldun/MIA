"""
Acceptance tests of the run of a workflow graph (N-2.4.1, G-V2.MODEL): TC-RUN-016 to TC-RUN-019 (REQ-RUN-016 to -019) against GraphRunner with scripted
transforms and a scripted master node, no model server (TR-MODEL-004).
Run with: python tests/acceptance/test_graph_run.py
"""

import os
import shutil
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
from graph_model_fakes import Script, data_node, make_edge, make_graph, master_node, transform_node   # noqa: E402
from graph_run import GraphRunner                                     # noqa: E402


class GraphRunAcceptance(unittest.TestCase):
    def setUp(self):
        self.script = Script()
        self.addCleanup(shutil.rmtree, self.script.folder, True)
        self.status = {}
        self.runner = GraphRunner(lambda node_id: self.status.get(node_id, "trusted"))

    @mark.req("REQ-RUN-016")
    def test_the_nodes_run_in_the_order_of_the_edges_and_the_data_nodes_hold_the_results(self):
        """TC-RUN-016: each transform runs after the nodes it reads; the data nodes hold the results and each transform got its inputs.

        Example: D1="s": T1 gets D1 and writes "T1(s)" to D2; T2 gets D2 and writes "T2(T1(s))" to D3; T3 gets D1 and writes "T3(s)" to D4.
        """
        # Given: a graph D1 -> T1 -> D2 -> T2 -> D3 and D1 -> T3 -> D4, with scripted transforms that append their ID to a list and write a result
        graph = make_graph("wf-order", [data_node(i) for i in ("D1", "D2", "D3", "D4")] + [transform_node(i) for i in ("T1", "T2", "T3")],
                           [make_edge("D1", "T1"), make_edge("T1", "D2"), make_edge("D2", "T2"), make_edge("T2", "D3"),
                            make_edge("D1", "T3"), make_edge("T3", "D4")])
        nodes = {i: self.script.node(i) for i in ("T1", "T2", "T3")}
        # When: the graph is run
        result = self.runner.run(graph, nodes, {"D1": "s"})
        # Then: T1 ran before T2, and each transform ran once
        self.assertEqual(result.status, "done")
        self.assertEqual(sorted(self.script.order), ["T1", "T2", "T3"])
        self.assertLess(self.script.order.index("T1"), self.script.order.index("T2"))
        # And: D2 and D3 hold the results of T1 and T2; D4 holds the result of T3; each transform got the contents of its input data nodes
        self.assertEqual((result.values["D2"], result.values["D3"], result.values["D4"]), ("T1(s)", "T2(T1(s))", "T3(s)"))

    @mark.req("REQ-RUN-017")
    def test_an_untrusted_node_refuses_the_run_before_any_node_ran(self):
        """TC-RUN-017: a graph with an untrusted transform is refused before any node ran, naming it and its status; after the owner trusts it, it runs.

        Example: T9 untrusted -> refused naming ["T9"] and "untrusted", no marker file; T9 trusted -> the marker file T9.marker exists.
        """
        # Given: a graph with a trusted transform and an untrusted transform T9 that writes a marker file when it runs
        graph = make_graph("wf-trust", [data_node("D1"), transform_node("T1"), data_node("D2"), transform_node("T9"), data_node("D3")],
                           [make_edge("D1", "T1"), make_edge("T1", "D2"), make_edge("D2", "T9"), make_edge("T9", "D3")])
        nodes = {"T1": self.script.node("T1"), "T9": self.script.marker_node("T9")}
        self.status["T9"] = "untrusted"
        # When: the graph is run; then the owner sets T9 trusted and it is run again
        first = self.runner.run(graph, nodes, {"D1": "s"})
        marker_after_first = self.script.marker_exists("T9")
        order_after_first = list(self.script.order)
        self.status["T9"] = "trusted"
        second = self.runner.run(graph, nodes, {"D1": "s"})
        # Then: the first run is refused before any node ran, no marker exists and the refusal names T9 and untrusted
        self.assertEqual(first.status, "refused")
        self.assertEqual(order_after_first, [])
        self.assertFalse(marker_after_first)
        self.assertEqual((first.named, first.named_status), (["T9"], "untrusted"))
        # And: the second run writes the marker
        self.assertEqual(second.status, "done")
        self.assertTrue(self.script.marker_exists("T9"))

    @mark.req("REQ-RUN-018")
    def test_a_master_node_runs_once_like_a_transform_and_an_untrusted_one_is_refused(self):
        """TC-RUN-018: a trusted master node runs once like a transform; the same graph with an untrusted master node is refused naming it.

        Example: D1="s" -> M1 (maximum of 3 repetitions) writes "M1(s)" to D2 and ran once; with M1 untrusted the run is refused naming ["M1"], "untrusted".
        """
        # Given: a graph D1 -> M1 -> D2 with a trusted master node M1 (maximum of 3 repetitions) that writes a result; a copy where M1 is untrusted
        graph = make_graph("wf-master", [data_node("D1"), master_node("M1", max_repetitions=3), data_node("D2")],
                           [make_edge("D1", "M1"), make_edge("M1", "D2")])
        nodes = {"M1": self.script.node("M1")}
        # When: each graph is run
        trusted = self.runner.run(graph, nodes, {"D1": "s"})
        ran_in_first = list(self.script.order)
        self.status["M1"] = "untrusted"
        untrusted = self.runner.run(graph, nodes, {"D1": "s"})
        # Then: in the first, M1 ran once and D2 holds its result
        self.assertEqual(trusted.status, "done")
        self.assertEqual(ran_in_first, ["M1"])
        self.assertEqual(trusted.values["D2"], "M1(s)")
        # And: the second is refused naming M1 and untrusted
        self.assertEqual(untrusted.status, "refused")
        self.assertEqual((untrusted.named, untrusted.named_status), (["M1"], "untrusted"))

    @mark.req("REQ-RUN-019")
    def test_a_failed_node_stops_the_run_and_the_result_names_it(self):
        """TC-RUN-019: when T2 of a chain T1 -> T2 -> T3 raises an error, T3 does not run and the run result names T2.

        Example: chain D0 -> T1 -> D1 -> T2 -> D2 -> T3 -> D3 with T2 failing: order ["T1","T2"], status "failed", named ["T2"].
        """
        # Given: a chain T1 -> T2 -> T3 where T2 raises an error
        graph = make_graph("wf-fail", [data_node("D0"), transform_node("T1"), data_node("D1"), transform_node("T2"), data_node("D2"),
                                       transform_node("T3"), data_node("D3")],
                           [make_edge("D0", "T1"), make_edge("T1", "D1"), make_edge("D1", "T2"), make_edge("T2", "D2"),
                            make_edge("D2", "T3"), make_edge("T3", "D3")])
        nodes = {"T1": self.script.node("T1"), "T2": self.script.failing_node("T2"), "T3": self.script.node("T3")}
        # When: the graph is run
        result = self.runner.run(graph, nodes, {"D0": "s"})
        # Then: T3 did not run
        self.assertEqual(self.script.order, ["T1", "T2"])
        # And: the run result names T2
        self.assertEqual((result.status, result.named), ("failed", ["T2"]))


if __name__ == "__main__":
    unittest.main()
