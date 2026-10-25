"""IF-202 run a workflow (Chat agent and Workflow management to Workflow execution): the contract suite runs against the mock (stage 1) and the
real Workflow execution (stage 2, skipped until N-2.4 is integrated). Protected after the Plan gate.
Run with: python tests/acceptance/contract/test_if_202_run_workflow.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ServiceError               # noqa: E402

IF = "IF-202"


@contract
class RunWorkflowContract(unittest.TestCase):
    @mark.req("IF-202", "REQ-BE-058")
    @each_provider(IF)
    def test_a_run_has_typed_events_with_run_id_and_user(self, runner):
        """TC-IF-202-01 golden 1: done with outputs; run_start first, run_end last, every event has the run id and the starting user."""
        result = runner.run("lookup", 1, {"question": "q"}, {"calls": 15}, "anna")
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["outputs"]["answer"], "42")
        events = result["events"]
        self.assertEqual((events[0]["type"], events[-1]["type"]), ("run_start", "run_end"))
        self.assertTrue(all(e["run_id"] == result["run_id"] and e["user"] == "anna" for e in events))
        self.assertEqual(runner.run("lookup", 1, {}, {}, "ben")["run_id"] != result["run_id"], True)

    @mark.req("IF-202", "REQ-BE-070")
    @each_provider(IF)
    def test_a_run_that_overshoots_ends_with_what_it_has(self, runner):
        """TC-IF-202-02 golden 2: estimated at 2 calls, needs 4, budget 3: budget_exhausted, missing names the budget, partial outputs, run_end written."""
        result = runner.run("drifting", 1, {}, {"calls": 3}, "anna")
        self.assertEqual((result["status"], result["missing"]), ("budget_exhausted", ["calls"]))
        self.assertTrue(result["outputs"])
        self.assertEqual(result["events"][-1]["type"], "run_end")
        self.assertEqual(result["events"][-1]["status"], "budget_exhausted")

    @mark.req("IF-202", "REQ-BE-042")
    @each_provider(IF)
    def test_an_estimate_over_the_budget_is_refused(self, runner):
        """TC-IF-202-03 golden 3: a budget below the estimate is refused before any work; unknown workflow is unknown_workflow."""
        result = runner.run("lookup", 1, {}, {"calls": 1}, "anna")
        self.assertEqual((result["status"], result["outputs"], result["missing"]), ("refused", {}, ["calls"]))
        self.assertEqual([e["type"] for e in result["events"]], ["run_start", "run_end"])
        with self.assertRaises(ServiceError) as caught:
            runner.run("nonsense", 1, {}, {}, "anna")
        self.assertEqual(caught.exception.code, "unknown_workflow")

    @mark.req("IF-202", "REQ-BE-042")
    @each_provider(IF)
    def test_measured_costs_of_a_node(self, runner):
        """TC-IF-202-04: costs of a node that was run are numbers; of an unknown node None (the schedule then marks the estimate incomplete)."""
        costs = runner.costs("lookup", "judge")
        self.assertEqual(set(costs), {"seconds", "calls", "tokens"})
        self.assertGreater(costs["calls"], 0)
        self.assertIsNone(runner.costs("lookup", "no-such-node"))


if __name__ == "__main__":
    unittest.main()
