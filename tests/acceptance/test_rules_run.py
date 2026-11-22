"""
Acceptance tests of the run check before a run (group RR of G-V4.GRAPHAPI.RULES): TC-RUN-036 to TC-RUN-039 (REQ-RUN-036 to REQ-RUN-039).

The runner is `GraphRunner(trust).run(graph, nodes, inputs) -> RunResult(status, named, named_status, values)` (tests/acceptance/test_graph_run.py).
"No step ran" is shown by marker functions that record their calls, and a sound twin in the same check calls each of its markers once (TR-RULES-005).
The graphs are written out here (TR-RULES-002); expected values are exact (TR-RULES-001); the converted chat skill is built at test time (TR-RULES-004).

Run with: python tests/acceptance/test_rules_run.py
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

from markers import mark                                                                       # noqa: E402
from graph_model_fakes import Script                                                           # noqa: E402
from graph_run import GraphRunner, Stage                                                       # noqa: E402
from rules_graphs import connection, converted_skill, data, graph, step, transform             # noqa: E402


def steps_of(g):
    return [n["id"] for n in g["nodes"] if n["data"].get("type") != "data"]


class RulesRunAcceptance(unittest.TestCase):
    def setUp(self):
        self.script = Script()
        self.addCleanup(shutil.rmtree, self.script.folder, True)
        self.status = {}
        self.runner = GraphRunner(lambda node_id: self.status.get(node_id, "trusted"))

    def markers(self, g):
        return {i: self.script.marker_node(i) for i in steps_of(g)}

    @mark.req("REQ-RUN-036")
    def test_no_step_runs_when_the_run_check_refuses(self):
        """TC-RUN-036: for each refusal reason of HR-006 the run ends refused and no marker was called; the sound twin calls its marker once.

        Example: two writers t1 and t2 of d -> refused, script.order == []; the twin d -> t -> out -> done, script.order == ["t"].
        """
        reasons = [  # reason, graph, values of the run
            ("a cycle", graph([data("d1"), transform("t1")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1")]), {}),
            ("two writers", graph([data("a", value=1), transform("t1"), transform("t2"), data("d")],
                                  [connection("e1", "a", "t1"), connection("e2", "a", "t2"), connection("e3", "t1", "d"), connection("e4", "t2", "d")]), {}),
            ("a connection to a missing step", graph([data("a", value=1), transform("t1"), data("out")],
                                                     [connection("e1", "a", "t1"), connection("e2", "t1", "out"), connection("X8>t1", "X8", "t1")]), {}),
            ("two identical connections", graph([data("a", value=1), transform("t1"), data("out")],
                                                [connection("e1", "a", "t1"), connection("e2", "a", "t1"), connection("e3", "t1", "out")]), {}),
            ("an unsupplied input", graph([data("q"), transform("t1"), data("out")], [connection("e1", "q", "t1"), connection("e2", "t1", "out")]), {}),
            ("a context graph", graph([step("c1", "entity"), step("c2", "entity")], [connection("e1", "c1", "c2")], kind="context"), {}),
            ("an unknown kind", graph([data("a", value=1), transform("t1"), data("out")], [connection("e1", "a", "t1"), connection("e2", "t1", "out")],
                                      kind="swarm"), {}),
        ]
        for reason, g, values in reasons:
            with self.subTest(reason=reason):
                # Given: a graph with this refusal reason; every step is a marker that records its call
                self.script.order.clear()
                # When: it is run
                result = self.runner.run(g, self.markers(g), dict(values))
                # Then: the run ends refused and no marker was called
                self.assertEqual(result.status, "refused")
                self.assertEqual(self.script.order, [])
        # And: the sound twin runs and its marker was called once (the markers can fire)
        twin = graph([data("a", value=1), transform("t1"), data("out")], [connection("e1", "a", "t1"), connection("e2", "t1", "out")])
        self.script.order.clear()
        self.assertEqual(self.runner.run(twin, self.markers(twin), {}).status, "done")
        self.assertEqual(self.script.order, ["t1"])

    @mark.req("REQ-RUN-037")
    def test_a_refused_run_names_every_part_with_repeats_kept(self):
        """TC-RUN-037: wf-cycle names D1, T1, D2, T2, D1; a connection from the missing X8 names X8>T1; chat without values names input.text.

        Example: the repeated D1 at the end is kept (the scratch run of 2026-11-22 lost it when repeats were removed).
        """
        cases = [  # label, graph, values, named
            ("wf-cycle", graph([data("D1"), transform("T1"), data("D2"), transform("T2")],
                               [connection("e1", "D1", "T1"), connection("e2", "T1", "D2"), connection("e3", "D2", "T2"), connection("e4", "T2", "D1")]),
             {}, ["D1", "T1", "D2", "T2", "D1"]),
            ("a missing start", graph([data("D1", value=1), transform("T1"), data("D2")],
                                      [connection("e1", "D1", "T1"), connection("e2", "T1", "D2"), connection("X8>T1", "X8", "T1")]), {}, ["X8>T1"]),
            ("chat without values", converted_skill("chat.md"), {}, ["input.text"]),
        ]
        for label, g, values, named in cases:
            with self.subTest(case=label):
                # Given: the graph; every step is a marker
                self.script.order.clear()
                # When: it is run
                result = self.runner.run(g, self.markers(g), dict(values))
                # Then: it is refused naming exactly these parts, in this order
                self.assertEqual((result.status, result.named), ("refused", named))
                self.assertEqual(self.script.order, [])

    @mark.req("REQ-RUN-038")
    def test_trust_is_checked_after_the_run_check(self):
        """TC-RUN-038: a cycle and an untrusted T2 name the cycle without a trust status; without the cycle the run names T2 and `untrusted`.

        Example: ("refused", ["D1", "T1", "D2", "T2", "D1"], None) and then ("refused", ["T2"], "untrusted").
        """
        # Given: a graph with a cycle and an untrusted transform T2, and the same graph without the cycle
        self.status["T2"] = "untrusted"
        nodes = [data("D1"), transform("T1"), data("D2"), transform("T2"), data("D3")]
        with_cycle = graph(nodes, [connection("e1", "D1", "T1"), connection("e2", "T1", "D2"), connection("e3", "D2", "T2"), connection("e4", "T2", "D1")])
        without = graph(nodes, [connection("e1", "D1", "T1"), connection("e2", "T1", "D2"), connection("e3", "D2", "T2"), connection("e4", "T2", "D3")])
        # When: each is run
        first = self.runner.run(with_cycle, self.markers(with_cycle), {})
        second = self.runner.run(without, self.markers(without), {"D1": "s"})
        # Then: the first is refused naming the cycle and no trust status
        self.assertEqual((first.status, first.named, first.named_status), ("refused", ["D1", "T1", "D2", "T2", "D1"], None))
        # And: the second is refused naming T2 and its status untrusted (REQ-RUN-017)
        self.assertEqual((second.status, second.named, second.named_status), ("refused", ["T2"], "untrusted"))
        self.assertEqual(self.script.order, [])

    @mark.req("REQ-RUN-039")
    def test_an_input_a_prepare_function_may_give_is_not_refused(self):
        """TC-RUN-039: DB read by the Stage T with a prepare function that gives nothing runs; with a plain function for T the run is refused naming DB.

        Example: Stage(run, prepare=lambda i, o, n: None) -> "done"; a plain function -> ("refused", ["DB"]) and T was not called.
        """
        # Given: the graph of TC-RUN-034: DB (no value in the graph or the run) -> T -> DO
        g = graph([data("DB"), data("DO"), transform("T")], [connection("e1", "DB", "T", **{"as": "b"}), connection("e2", "T", "DO", **{"as": "store"})])
        calls = []

        def stage(inputs, outputs, node):
            calls.append("stage")
            return {"outputs": {"store": inputs.get("b")}}

        # When: it is run once with a Stage whose prepare function gives nothing, once with a plain function for T
        with_prepare = self.runner.run(g, {"T": Stage(stage, prepare=lambda inputs, outputs, node: None)}, {})
        plain = self.runner.run(g, {"T": self.script.marker_node("T")}, {})
        # Then: the first runs to done (D-418 (1))
        self.assertEqual(with_prepare.status, "done")
        self.assertEqual(calls, ["stage"])
        # And: the second is refused naming DB, and T was not called
        self.assertEqual((plain.status, plain.named), ("refused", ["DB"]))
        self.assertEqual(self.script.order, [])


if __name__ == "__main__":
    unittest.main()
