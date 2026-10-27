"""
REQ-WFM-023 (confidence by code, limits with every result; NFR-4): the result record of the number gate verify.number_gate@5 carries `limits`, a list of {code, text}
made by code (number_gate.limits_of) from what the gate knows: the evidence, the number check and the tally of the voices. The older versions keep their record.
Run with the MIA virtualenv: python tests/test_gate_limits.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from gate_lab import cops_answer, gate_run          # noqa: E402
from markers import mark                            # noqa: E402

GATE5 = "verify.number_gate@5"
TOWER = "The tower is 1,200 m tall."


def codes(answer):
    return [limit["code"] for limit in answer["limits"]]


class GateLimits(unittest.TestCase):
    def run_gate(self, claim, evidence, verdict="supported", pipeline=GATE5):
        result, model = gate_run(cops_answer(verdict), claim, evidence, pipeline=pipeline)
        self.assertEqual(result.status, "done", result.error)
        return result.answer

    @mark.req("REQ-WFM-023")
    def test_every_result_has_limits_with_a_code_and_a_text(self):
        for claim, evidence in ((TOWER, "The tower is 1,020 m tall."), (TOWER, ""), ("The sky is blue.", "On a clear day the sky is blue."), ("The hall is 40 m long.", "The hall has 40 seats.")):
            answer = self.run_gate(claim, evidence)
            self.assertTrue(answer["limits"], claim)
            for limit in answer["limits"]:
                self.assertTrue(limit["code"] and limit["text"], limit)
                self.assertEqual(set(limit), {"code", "text"})

    @mark.req("REQ-WFM-023")
    def test_no_evidence_says_so_and_nothing_was_judged(self):
        self.assertEqual(codes(self.run_gate(TOWER, "")), ["no_evidence"])

    @mark.req("REQ-WFM-023")
    def test_the_verdict_states_what_stands_behind_it(self):
        answer = self.run_gate(TOWER, "The tower is 1,020 m tall.", "supported")
        basis = next(limit for limit in answer["limits"] if limit["code"] == "confidence_basis")
        self.assertIn("one judge", basis["text"])                           # the tally of the cops style is the judge's ruling: no vote count may be claimed
        self.assertIn("no vote count", basis["text"])
        self.assertIn("not calibrated", basis["text"])
        self.assertIn("one model voice", next(l for l in self.run_gate("The sky is blue.", "The sky is blue.")["limits"] if l["code"] == "confidence_basis")["text"])
        self.assertEqual(codes(answer), ["evidence_unchecked", "confidence_basis", "judged_by"])

    @mark.req("REQ-WFM-023")
    def test_a_claim_without_a_number_and_an_open_check_are_named(self):
        self.assertIn("no_number_check", codes(self.run_gate("The sky is blue.", "On a clear day the sky is blue.")))
        self.assertIn("number_check_inconclusive", codes(self.run_gate("The hall is 40 m long.", "The hall has 40 seats.")))
        self.assertNotIn("number_check_inconclusive", codes(self.run_gate(TOWER, "The tower is 1,200 m tall.")))

    @mark.req("REQ-WFM-023")
    def test_cut_evidence_is_named(self):
        long_evidence = "The tower is 1,200 m tall. " + "Filler sentence about the city. " * 200
        self.assertGreater(len(long_evidence), 4000)
        self.assertIn("evidence_cut", codes(self.run_gate(TOWER, long_evidence)))
        self.assertNotIn("evidence_cut", codes(self.run_gate(TOWER, "The tower is 1,200 m tall.")))

    def test_the_older_version_keeps_its_record(self):
        self.assertNotIn("limits", self.run_gate(TOWER, "The tower is 1,020 m tall.", pipeline="verify.number_gate@4"))


if __name__ == "__main__":
    unittest.main()
