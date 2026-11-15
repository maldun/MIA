"""
Acceptance tests of the Stage call of the graph runner (N-2.4.1, G-V2.CONVERT, task T-CV-03a, A-124, D-248, D-249): TC-RUN-030 to TC-RUN-033 (REQ-RUN-030 to -033) against
GraphRunner with scripted functions, no model server. RED until T-CV-03a: `Stage` in graph_run.py is a stub the runner does not know.
Conventions under test (A-124 R2): the name of an input or output is the `as` field of its edge, else the data node ID; the settings node is the input data node whose edge
carries `role: "settings"`; all configuration is the value of a data node, given to the run in `inputs` like any starting value (a data node without one holds None).
Run with: python tests/acceptance/test_graph_run_stages.py
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

from markers import mark                                              # noqa: E402
from graph_model_fakes import data_node, make_edge, make_graph, transform_node   # noqa: E402
from graph_run import GraphRunner, Stage                              # noqa: E402


def edge(start, end, **data):
    found = make_edge(start, end)
    found["data"] = dict(data)
    return found


class Recorder:
    """a function that remembers every call and answers with a fixed result"""

    def __init__(self, result=None):
        self.calls, self.result = [], result

    def __call__(self, *args):
        self.calls.append(args)
        return self.result


class StageAcceptance(unittest.TestCase):
    def setUp(self):
        self.runner = GraphRunner(lambda node_id: "trusted")

    @mark.req("REQ-RUN-030")
    def test_a_stage_gets_its_inputs_outputs_and_settings_by_name(self):
        """TC-RUN-030: inputs by name (one renamed by the edge field `as`, one by its node ID), outputs by name, the settings object of the settings node.

        Example: DA=[1, 2] as "hits", DB="x", settings node DC={"n": 2}, output node DO={"store": "db"} as "result".
        """
        graph = make_graph("wf-stage", [data_node(i) for i in ("DA", "DB", "DC", "DO")] + [transform_node("T")],
                           [edge("DA", "T", **{"as": "hits"}), edge("DB", "T"), edge("DC", "T", role="settings"), edge("T", "DO", **{"as": "result"})])
        stage = Recorder("done-value")
        result = self.runner.run(graph, {"T": Stage(stage)}, {"DA": [1, 2], "DB": "x", "DC": {"n": 2}, "DO": {"store": "db"}})
        self.assertEqual(result.status, "done")
        self.assertEqual(stage.calls, [({"hits": [1, 2], "DB": "x"}, {"result": {"store": "db"}}, {"n": 2})])
        # And: without a settings node the settings object is empty, an output node without a starting value is None
        graph = make_graph("wf-plain", [data_node("DA"), data_node("DO"), transform_node("T")], [edge("DA", "T"), edge("T", "DO")])
        stage = Recorder("v")
        self.assertEqual(self.runner.run(graph, {"T": Stage(stage)}, {"DA": 1}).status, "done")
        self.assertEqual(stage.calls, [({"DA": 1}, {"DO": None}, {})])

    @mark.req("REQ-RUN-031")
    def test_a_stage_writes_each_output_by_name_or_one_value_to_all(self):
        """TC-RUN-031: {"outputs": {...}} writes each value to the output node of that name; any other result goes to every output node; an unknown name fails the node."""
        graph = make_graph("wf-out", [data_node("DA"), data_node("D1"), data_node("D2"), transform_node("T")],
                           [edge("DA", "T"), edge("T", "D1", **{"as": "first"}), edge("T", "D2", **{"as": "second"})])
        cases = [("per name", {"outputs": {"first": 1, "second": 2}}, (1, 2)),
                 ("plain value", "v", ("v", "v")),
                 ("outputs beside other keys is an ordinary value", {"outputs": {"first": 1}, "extra": 1}, ({"outputs": {"first": 1}, "extra": 1},) * 2)]
        for label, returned, expected in cases:
            with self.subTest(case=label):
                result = self.runner.run(graph, {"T": Stage(lambda inputs, outputs, node, r=returned: r)}, {"DA": 0})
                self.assertEqual(result.status, "done")
                self.assertEqual((result.values["D1"], result.values["D2"]), expected)
        with self.subTest(case="unknown output name"):
            stage = Recorder({"outputs": {"third": 1}})
            result = self.runner.run(graph, {"T": Stage(stage)}, {"DA": 0})
            self.assertEqual(len(stage.calls), 1, "the Stage was not called")
            self.assertEqual((result.status, result.named), ("failed", ["T"]))

    @mark.req("REQ-RUN-032")
    def test_a_plain_function_runs_as_before_next_to_a_stage(self):
        """TC-RUN-032: a plain function gets {data node id: value} and writes one value; a Stage in the same graph reads that value by its name."""
        graph = make_graph("wf-mixed", [data_node(i) for i in ("D1", "D2", "D3")] + [transform_node("P"), transform_node("S")],
                           [edge("D1", "P"), edge("P", "D2"), edge("D2", "S", **{"as": "text"}), edge("S", "D3")])
        plain = Recorder("from-plain")
        stage = Recorder("from-stage")
        result = self.runner.run(graph, {"P": plain, "S": Stage(stage)}, {"D1": "start"})
        self.assertEqual(result.status, "done")
        self.assertEqual(plain.calls, [({"D1": "start"},)])
        self.assertEqual(stage.calls, [({"text": "from-plain"}, {"D3": None}, {})])
        self.assertEqual((result.values["D2"], result.values["D3"]), ("from-plain", "from-stage"))

    @mark.req("REQ-RUN-033")
    def test_broken_wiring_is_refused_before_any_node_ran(self):
        """TC-RUN-033: two settings edges into one transform, or two outputs with the same name, refuse the run naming the transform; the corrected graph runs."""
        two_settings = make_graph("wf-two", [data_node(i) for i in ("DA", "DS1", "DS2", "DO")] + [transform_node("T")],
                                  [edge("DA", "T"), edge("DS1", "T", role="settings"), edge("DS2", "T", role="settings"), edge("T", "DO")])
        one_setting = make_graph("wf-one", [data_node(i) for i in ("DA", "DS1", "DO")] + [transform_node("T")],
                                 [edge("DA", "T"), edge("DS1", "T", role="settings"), edge("T", "DO")])
        same_name = make_graph("wf-same", [data_node(i) for i in ("DA", "D1", "D2")] + [transform_node("T")],
                               [edge("DA", "T"), edge("T", "D1", **{"as": "r"}), edge("T", "D2", **{"as": "r"})])
        distinct = make_graph("wf-distinct", [data_node(i) for i in ("DA", "D1", "D2")] + [transform_node("T")],
                              [edge("DA", "T"), edge("T", "D1", **{"as": "r"}), edge("T", "D2", **{"as": "s"})])
        for label, broken, fixed, start in (("two settings edges", two_settings, one_setting, {"DA": 1, "DS1": {}, "DS2": {}}),
                                            ("two outputs with one name", same_name, distinct, {"DA": 1})):
            with self.subTest(case=label):
                stage = Recorder("v")
                refused = self.runner.run(broken, {"T": Stage(stage)}, dict(start))
                self.assertEqual((refused.status, refused.named, stage.calls), ("refused", ["T"], []))
                stage = Recorder("v")
                self.assertEqual(self.runner.run(fixed, {"T": Stage(stage)}, {k: v for k, v in start.items() if k != "DS2"}).status, "done")
                self.assertEqual(len(stage.calls), 1)


if __name__ == "__main__":
    unittest.main()
