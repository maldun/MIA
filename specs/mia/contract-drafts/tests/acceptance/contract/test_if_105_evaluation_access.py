"""IF-105 evaluation access (harness of N-4 to the Backend): the contract suite runs against the mock (stage 1) and the real Backend (stage 2,
skipped until N-2 is integrated). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_105_evaluation_access.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ServiceError               # noqa: E402

IF = "IF-105"
OPTIONS = {"model_pin": "MP-light", "seed": 7, "temperature": 0, "budget": {"calls": 15}}


def code_of(call):
    try:
        call()
    except ServiceError as err:
        return err.code
    raise AssertionError("no ServiceError raised")


@contract
class EvaluationAccessContract(unittest.TestCase):
    @mark.req("IF-105", "REQ-OPS-004")
    @each_provider(IF)
    def test_a_case_runs_with_pin_seed_and_temperature_recorded(self, platform):
        """TC-IF-105-01 golden 1: done; the run_start event carries model pin, seed and temperature; the run is attributed to the user harness; the cost is returned."""
        result = platform.run_case("lookup", 1, {"question": "q"}, OPTIONS)
        self.assertEqual(result["status"], "done")
        start = result["events"][0]
        self.assertEqual((start["type"], start["user"]), ("run_start", "harness"))
        self.assertEqual(start["options"], {"model_pin": "MP-light", "seed": 7, "temperature": 0})
        self.assertEqual(set(result["cost"]), {"steps", "seconds", "calls", "tokens"})
        self.assertEqual(platform.events(result["run_id"]), result["events"])
        self.assertIn("lookup", [w["id"] for w in platform.workflows()])

    @mark.req("IF-105", "REQ-OPS-004")
    @each_provider(IF)
    def test_missing_options_and_unknown_pin_are_refused(self, platform):
        """TC-IF-105-02 golden 2: options without seed are bad_options; the pin MP-huge is pin_unavailable; an unknown workflow is unknown_workflow; nothing runs."""
        self.assertEqual(code_of(lambda: platform.run_case("lookup", 1, {}, {"model_pin": "MP-light", "temperature": 0})), "bad_options")
        self.assertEqual(code_of(lambda: platform.run_case("lookup", 1, {}, dict(OPTIONS, model_pin="MP-huge"))), "pin_unavailable")
        self.assertEqual(code_of(lambda: platform.run_case("nonsense", 1, {}, OPTIONS)), "unknown_workflow")

    @mark.req("IF-105", "REQ-BE-050")
    @each_provider(IF)
    def test_the_same_inputs_and_options_give_the_same_run(self, platform):
        """TC-IF-105-03 golden 3: with a fake model two runs have equal outputs and equal event types and payloads, apart from run id."""
        a = platform.run_case("lookup", 1, {"question": "q"}, OPTIONS)
        b = platform.run_case("lookup", 1, {"question": "q"}, OPTIONS)
        self.assertNotEqual(a["run_id"], b["run_id"])
        self.assertEqual(a["outputs"], b["outputs"])
        strip = lambda events: [{k: v for k, v in e.items() if k != "run_id"} for e in events]
        self.assertEqual(strip(a["events"]), strip(b["events"]))

    @mark.req("IF-105", "REQ-OPS-018")
    @each_provider(IF)
    def test_a_budget_below_the_estimate_is_refused_and_costs_nothing(self, platform):
        """TC-IF-105-04: budget calls 1 is refused with the budget named, outputs empty, cost 0; the case still has its run_start and run_end."""
        result = platform.run_case("lookup", 1, {}, dict(OPTIONS, budget={"calls": 1}))
        self.assertEqual((result["status"], result["outputs"], result["missing"]), ("refused", {}, ["calls"]))
        self.assertEqual(result["cost"], {"steps": 0, "seconds": 0, "calls": 0, "tokens": 0})
        self.assertEqual([e["type"] for e in result["events"]], ["run_start", "run_end"])


if __name__ == "__main__":
    unittest.main()
