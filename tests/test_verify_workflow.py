"""
The example workflow verify as a library entry (N-2.3 T-04: REQ-WFM-011, -012, -013). The entry is the pipeline verify.number_gate@4, run by the platform over a scripted
model (no Ollama). The acceptance tests of the gate (tests/acceptance/test_number_gate.py, REQ-GATE-*) check the same behaviour on smaller samples; these tests carry the
workflow requirements and the sample sizes of their criteria. Run: python tests/test_verify_workflow.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from gate_lab import GATE, cops_answer, events_of, gate_run, vote   # noqa: E402
from library import Library                                          # noqa: E402
from markers import mark                                             # noqa: E402

NUMBER_CLAIMS = [("The tower is 1,200 m tall.", "The tower is 1,200 m tall."), ("The group sold 4.8 million records.", "The group sold 4.83 million records."),
                 ("The road is 5 km long.", "The road is 3.1 miles long."), ("The hall is 40 m long.", "The hall has 40 seats."),
                 ("The bridge was built in 1937.", "The bridge was built in 1937."), ("The album has 12 tracks.", "The album has 9 tracks."),
                 ("The tower is 1,200 m tall.", "The tower is 1,020 m tall."), ("The video got more than 5 million views.", "The channel has 2 videos."),
                 ("The lake is 90 m deep.", "The lake is 90 metres deep."), ("The village has 300 people.", "The village has 3000 people.")]
NO_EVIDENCE = ["The tower is 1,200 m tall.", "The group sold 4.8 million records.", "The road is 453 kilometres long.", "The bridge was built in 1937.", "The album has 12 tracks.",
               "The lake is 90 m deep.", "The village has 300 people.", "The hall is 40 m long.", "The war ended in 1945.", "The film is 142 minutes long."]


def positions(result, type_, name=None):
    return [i for i, e in enumerate(result.events) if e.get("kind") == "event" and e.get("type") == type_ and (name is None or (e.get("payload") or {}).get("name") == name)]


class VerifyWorkflow(unittest.TestCase):
    @mark.req("REQ-WFM-011")
    def test_verify_is_a_library_entry_that_runs_on_the_platform(self):
        entry = Library(os.path.join(REPO, "library")).resolve(GATE, "pipeline")
        self.assertEqual((entry["id"], entry["version"]), ("verify.number_gate", 4))
        self.assertEqual(entry["_source"], "shipped")                       # its status (draft today) is a decision of a person after the specification and the benchmark exist (root T-10)

    @mark.req("REQ-WFM-011")
    def test_the_code_check_precedes_the_first_model_call_of_each_claim(self):
        for claim, evidence in NUMBER_CLAIMS:
            result, model = gate_run(cops_answer(), claim, evidence)
            self.assertEqual(result.status, "done", result.error)
            check, calls = positions(result, "check_run", "number_check"), positions(result, "model_call")
            self.assertTrue(check and calls, claim)
            self.assertLess(check[0], calls[0], claim)

    @mark.req("REQ-WFM-012")
    def test_ten_number_claims_without_evidence_are_unclear_without_a_model_call(self):
        self.assertEqual(len(NO_EVIDENCE), 10)
        for claim in NO_EVIDENCE:
            result, model = gate_run(cops_answer("supported"), claim, "")
            self.assertEqual(result.status, "done", result.error)
            self.assertEqual((result.answer["verdict"], result.answer["calls"]), ("unclear", 0), claim)
            self.assertEqual((len(model.prompts), positions(result, "model_call")), (0, []), claim)

    @mark.req("REQ-WFM-013")
    def test_a_failed_check_reaches_the_judge_as_a_contradiction_found_by_code(self):
        for judged in ("supported", "refuted", "unclear"):
            result, model = gate_run(cops_answer(judged), "The tower is 1,200 m tall.", "The tower is 1,020 m tall.")
            self.assertEqual(result.status, "done", result.error)
            self.assertIn("Number check: fail", model.prompts[-1])
            self.assertEqual(result.answer["verdict"], judged)               # the verdict is the judge's, not the check's


if __name__ == "__main__":
    unittest.main()
