"""
Acceptance tests of the measures of G-V4.GRAPHAPI.RULES (high-level spec HR-004 to HR-006): TC-GTB-046, TC-GTB-047 and TC-RUN-040.

- TC-GTB-046 (HR-004, witnesses AC-017): two graphs that break three rules each go through every entry point five times (TR-RULES-006); the rule
  report, the save and the check route are compared item by item, the run by the parts it names (D-424). The check route is the stand-in of IF-104 v2
  and counts as a wiring check only (TR-RULES-007).
- TC-GTB-047 (HR-005): the cases of TC-GTB-002 and the generator of TC-GTB-003 (seeds 1 to 1000), turned into the stored form as prototype round 04
  did (D-424, TR-RULES-003); counts of newly refused graphs are printed, not asserted.
- TC-RUN-040 (HR-006): the 15 converted skills, built at test time (TR-RULES-004), are ready once their open inputs are given.

Run with: python tests/acceptance/test_rules_measures.py
"""

import collections
import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests"))
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                                                       # noqa: E402
from storage import Storage                                                                     # noqa: E402
from graph_model import GraphModel                                                              # noqa: E402
from graph_model_fakes import Script                                                           # noqa: E402
from graph_run import GraphRunner                                                              # noqa: E402
from graph_rules import violation                                                              # noqa: E402
from graph_rule_set import rule_report, run_check                                              # noqa: E402
from core_stores import fresh_backend                                                          # noqa: E402
from rules_graphs import (SKILL_COUNT, ac017, check_route, connection, converted_skills, data, graph, item, old_document_as_graph,  # noqa: E402
                          transform)
from test_graph_rules import LOOKUP, doc, generated                                            # noqa: E402

REPEATS = 5        # HR-004: five times in a row
SEEDS = range(1, 1001)   # HR-005: the seeds of TC-GTB-003, fixed in Plan


class RulesMeasuresAcceptance(unittest.TestCase):

    @mark.req("REQ-GTB-037", "REQ-WFM-163", "REQ-RUN-037")
    def test_the_same_list_at_every_entry_point(self):
        """TC-GTB-046: two graphs breaking three rules each give the same items through the rule report, the save and the check route, and the run
        names their parts in the same order, five times in a row.

        Example: AC-017 plus a second d1 -> t1 gives [duplicate_connection ["e4"], single_writer ["d1"], cycle ["d1", "t1", "d1"]]; the run names
        ["e4", "d1", "d1", "t1", "d1"]. The second graph is run with a value for d1 (A-170b, D-428), so the run names its three rule items only.
        """
        # Given: the AC-017 graph plus an identical connection, and a graph with a missing start, an identical connection and a data step with session
        first = ac017()
        first["edges"].append(connection("e4", "d1", "t1"))
        second = graph([data("d1", session=True), transform("t1"), data("d2")],
                       [connection("e1", "d1", "t1"), connection("e2", "t1", "d2"), connection("e3", "t1", "d2"), connection("e9", "x8", "t1")])
        expected = {"first": [item("duplicate_connection", ["e4"]), item("single_writer", ["d1"]), item("cycle", ["d1", "t1", "d1"])],
                    "second": [item("connection_endpoints", ["e9"]), item("duplicate_connection", ["e3"]), item("stop_limit", ["d1"])]}
        script = Script()
        self.addCleanup(shutil.rmtree, script.folder, True)
        runner = GraphRunner(lambda node_id: "trusted")
        # the second graph is run with d1 given: d1 has no value and no writer, so without it the run check rightly adds an unsupplied input
        # (REQ-GTB-051) and the run would name one part more than the rule report (A-170b, D-428)
        run_values = {"first": {}, "second": {"d1": "x"}}
        for label, g in (("first", first), ("second", second)):
            for repeat in range(REPEATS):
                with self.subTest(graph=label, repeat=repeat):
                    # When: the graph is checked through the rule report, saved on a fresh files store, sent to the check route and run
                    report = rule_report(g)
                    saved = GraphModel(Storage(fresh_backend("files", self)), author="ann").save_graph(g)
                    routed = check_route(g)
                    ran = runner.run(g, {i["id"]: script.marker_node(i["id"]) for i in g["nodes"] if i["data"]["type"] != "data"}, dict(run_values[label]))
                    # Then: the rule report is the three broken rules of the graph
                    self.assertEqual(report, expected[label])
                    # And: the save and the check route give the same items, the run names the same parts in the same order (0 differences)
                    self.assertEqual(getattr(saved, "rules", None), report)
                    self.assertEqual(routed, report)
                    self.assertEqual((ran.status, ran.named), ("refused", [p for i in report for p in i["parts"]]))
        self.assertEqual(script.order, [])

    @mark.req("REQ-GTB-034")
    def test_no_old_refusal_is_lost(self):
        """TC-GTB-047: no graph that the five older rules refuse is accepted by the eight, except a stop limit REQ-WFM-048 accepts (max_seconds 1.0).

        Example: "a session with max_cycles 0" is refused by the five (session_stopping_criterion) and by the eight (stop_limit naming s).
        """
        # Given: the cases of TC-GTB-002 (written out as in prototype round 04) and the generator of TC-GTB-003, seeds 1 to 1000
        cases = [
            ("a step ID used twice", doc([("a", "data", {}), ("a", "process", {})])),
            ("a connection to a missing step", doc([("a", "data", {})], [("a", "ghost")])),
            ("two data steps joined", doc([("a", "data", {}), ("b", "data", {})], [("a", "b")])),
            ("two processing steps joined", doc([("a", "process", {}), ("b", "process", {})], [("a", "b")])),
            ("a session with max_cycles 0", doc([("s", "process", {"session": True, "stop": {"max_cycles": 0}})])),
            ("a cycle p -> d -> p", doc([("p", "process", {}), ("d", "data", {})], [("p", "d"), ("d", "p")])),
            ("a self-loop of a processing step", doc([("a", "process", {})], [("a", "a")])),
            ("a step of kind tool", {"nodes": [{"id": "a", "kind": "tool"}], "edges": []}),
            ("an empty step ID", {"nodes": [{"id": "", "kind": "data"}], "edges": []}),
            ("a session with max_seconds 1.0", doc([("s", "process", {"session": True, "stop": {"max_seconds": 1.0}})])),
            ("a session with max_cycles True", doc([("s", "process", {"session": True, "stop": {"max_cycles": True}})])),
            ("a session with stop 'x'", doc([("s", "process", {"session": True, "stop": "x"})])),
        ]
        documents = cases + [("seed %d" % seed, generated(seed)[0]) for seed in SEEDS]
        # When: each is checked by the five older rules and by the eight
        lost, newly = [], collections.Counter()
        for label, document in documents:
            old, new = violation(document), rule_report(old_document_as_graph(document))
            if old and not new:
                lost.append(label)
            elif new and not old:
                newly[new[0]["rule"]] += 1
        print("\nTC-GTB-047: refused only by the eight rules, by first rule (reported, not asserted):", dict(newly), "total", sum(newly.values()))
        # Then: none is refused by the five and accepted by the eight, except the stop limit REQ-WFM-048 accepts
        self.assertEqual(lost, ["a session with max_seconds 1.0"])
        # And: the sound lookup graph is accepted by both (the twin: the eight do not refuse everything)
        self.assertEqual((violation(LOOKUP), rule_report(old_document_as_graph(LOOKUP))), (None, []))

    @mark.req("REQ-RUN-036")
    def test_todays_skills_are_ready_once_their_inputs_are_given(self):
        """TC-RUN-040: each of the 15 converted skill graphs breaks no rule and is ready once its open inputs have the value "x".

        Example: chat.md: run_check(g) names only input.text; run_check(g, {"input.text": "x"}) == {"status": "ready", "broken": []}.
        """
        # Given: the 15 converted skill graphs
        skills = converted_skills()
        self.assertEqual(len(skills), SKILL_COUNT)
        for name, g in skills:
            with self.subTest(skill=name):
                # When: each is checked for a run, first without values, then with "x" for each open input
                first = run_check(g)
                given = {b["input"]: "x" for b in first["broken"] if b.get("kind") == "input"}
                # Then: no rule is broken, and with the open inputs given the skill is ready
                self.assertEqual([b for b in first["broken"] if b.get("kind") != "input"], [])
                self.assertEqual(run_check(g, given), {"status": "ready", "broken": []})


if __name__ == "__main__":
    unittest.main()
