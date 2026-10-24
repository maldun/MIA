"""
Acceptance tests of the verification gate (specs/number-gate/requirements.md: REQ-GATE-001 to REQ-GATE-005, IF-003), written before the code (Plan, step 4).
The gate is the library pipeline verify.number_gate@4 under the skill verify_claim: inputs claim, evidence and optionally style ("cops" by default or "single");
the answer is {"verdict": supported | refuted | unclear, "status": pass | fail | inconclusive, "calls": int, "seconds": float, "facts": [...], ...} (IF-003).
The number check is the code of checks.number_check, so the "fake" number check of the requirements is a claim and an evidence text that the real check decides.
Protected after the Plan gate. Run with: python tests/acceptance/test_number_gate.py
"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from gate_lab import GATE, Scripted, cops_answer, events_of, gate_run, vote      # noqa: E402
from markers import mark                                                           # noqa: E402

TOWER = "The tower is 1,200 m tall."


def indexes(result, type_, name=None):
    found = []
    for i, event in enumerate(result.events):
        if event.get("kind") == "event" and event.get("type") == type_ and (name is None or (event.get("payload") or {}).get("name") == name):
            found.append(i)
    return found


class Gate(unittest.TestCase):
    def done(self, result):
        self.assertEqual(result.status, "done", "the pipeline %s must run: %s" % (GATE, result.error))
        return result.answer

    @mark.req("REQ-GATE-001")
    def test_the_number_check_runs_before_the_first_model_call(self):
        """TC-GATE-001: 6 claims with a number and evidence (3 that the check passes, 3 that it leaves open), 2 claims with empty evidence."""
        with_check = [(TOWER, "The tower is 1,200 m tall."), ("The group sold 4.8 million records.", "The group sold 4.83 million records."),
                      ("The road is 5 km long.", "The road is 3.1 miles long."), ("The hall is 40 m long.", "The hall has 40 seats."),
                      ("The hall is 40 m long.", "The hall was built in 1901."), ("The video got more than 5 million views.", "The channel has 2 videos.")]
        for claim, evidence in with_check:
            result, model = gate_run(cops_answer(), claim, evidence)
            self.done(result)
            check = indexes(result, "check_run", "number_check")
            calls = indexes(result, "model_call")
            self.assertTrue(check, "no number check event for: " + claim)
            self.assertTrue(calls, "no model call for: " + claim)
            self.assertLess(check[0], calls[0], claim)
        for claim in (TOWER, "The group sold 4.8 million records."):
            result, model = gate_run(cops_answer(), claim, "")
            self.done(result)
            self.assertEqual(indexes(result, "check_run", "number_check"), [], claim)

    @mark.req("REQ-GATE-002")
    def test_a_failed_check_goes_to_the_judge(self):
        """TC-GATE-002 (A-01): the check says fail; the judge sees the line and decides; the verdict is the judge's."""
        result, model = gate_run(cops_answer("supported"), TOWER, "The tower is 1,020 m tall.")
        answer = self.done(result)
        self.assertEqual(len(model.prompts), 3)
        self.assertIn("Number check: fail", model.prompts[2])
        self.assertEqual((answer["verdict"], answer["status"]), ("supported", "pass"))

    @mark.req("REQ-GATE-006")
    def test_a_number_claim_without_evidence_is_not_decided(self):
        """TC-GATE-006 (A-01): 5 claims with a number and empty evidence: unclear, inconclusive, 0 calls, no facts."""
        for claim in (TOWER, "The group sold 4.8 million records.", "The road is 453 kilometres long.", "The bridge was built in 1937.", "The album has 12 tracks."):
            result, model = gate_run(cops_answer("supported"), claim, "")
            answer = self.done(result)
            self.assertEqual((answer["verdict"], answer["status"], answer["calls"], answer["facts"]), ("unclear", "inconclusive", 0, []), claim)
            self.assertEqual(len(model.prompts), 0, claim)

    @mark.req("REQ-GATE-003")
    def test_a_claim_the_check_leaves_open_goes_to_one_judgement_style(self):
        """TC-GATE-003: cops by default (argue for, argue against, judge, in this order, the judge sees the check line), single when configured."""
        for claim, evidence in ((TOWER, "The tower is 1,200 m tall."), ("The hall is 40 m long.", "The hall has 40 seats.")):
            result, model = gate_run(cops_answer(), claim, evidence)
            self.done(result)
            self.assertEqual(len(model.prompts), 3, (claim, evidence))
            self.assertIn("Your side: for", model.prompts[0])
            self.assertIn("Your side: against", model.prompts[1])
            self.assertNotIn("Your side:", model.prompts[2])
            self.assertIn("Number check:", model.prompts[2])
        result, model = gate_run(lambda p, n: vote("supported"), TOWER, "The tower is 1,200 m tall.", style="single")
        self.done(result)
        self.assertEqual(len(model.prompts), 1)

    @mark.req("REQ-GATE-004")
    def test_claims_without_a_number_take_the_single_voice_as_before(self):
        """TC-GATE-004: the 20 claims without a number of the suite verdicts give the same verdict and the same number of model calls as verify.single@1."""
        suite = os.path.join(REPO, "eval", "suites", "verdicts", "cases.jsonl")
        claims = []
        for line in open(suite, encoding="utf-8"):
            case = json.loads(line)
            if not re.search(r"\d", case["input"]["claim"]):
                claims.append((case["input"]["claim"], case["input"].get("evidence", "")))
        self.assertGreaterEqual(len(claims), 20)
        script = lambda p, n: vote("supported" if n % 2 else "refuted")
        for claim, evidence in claims[:20]:
            reference, ref_model = gate_run(script, claim, evidence, pipeline="verify.single@1")
            gate, gate_model = gate_run(script, claim, evidence)
            self.assertEqual(gate.status, "done", gate.error)
            self.assertEqual(reference.status, "done", reference.error)
            self.assertEqual(gate.answer["verdict"], reference.answer["verdict"], claim)
            self.assertEqual(len(gate_model.prompts), len(ref_model.prompts), claim)

    @mark.req("REQ-GATE-005")
    def test_at_most_4000_characters_of_evidence_reach_each_step(self):
        """TC-GATE-005: evidence of 30000, 4000 and 3999 characters; the evidence is made of numbered tokens of 8 characters, so the characters can be counted."""
        token = re.compile(r"E\d{6}\.")
        for tokens, whole in ((3750, False), (500, True), (499, True)):
            evidence = "".join("E%06d." % i for i in range(tokens))
            result, model = gate_run(cops_answer(), "The hall is 40 m long.", evidence)
            self.done(result)
            self.assertEqual(len(model.prompts), 3)
            for prompt in model.prompts:
                count = len(token.findall(prompt))
                self.assertLessEqual(count * 8, 4000, (tokens, count))
                if whole:
                    self.assertEqual(count, tokens, "evidence of up to 4000 characters must be passed whole")

    @mark.req("IF-003")
    def test_the_result_record_has_verdict_status_calls_seconds_and_facts(self):
        """TC-IF-003 (A-01): calls 0 and no facts for a number claim without evidence; 3 calls when the cops style decides; verdict and status agree."""
        decided, _ = gate_run(cops_answer(), TOWER, "")
        record = self.done(decided)
        for field in ("verdict", "status", "calls", "seconds", "facts"):
            self.assertIn(field, record)
        self.assertEqual((record["calls"], record["facts"]), (0, []))
        mapping = {"supported": "pass", "refuted": "fail", "unclear": "inconclusive"}
        self.assertEqual(mapping[record["verdict"]], record["status"])
        for word in ("supported", "refuted", "unclear"):
            result, model = gate_run(cops_answer(word), "The hall is 40 m long.", "The hall has 40 seats.")
            record = self.done(result)
            self.assertEqual(record["calls"], 3)
            self.assertEqual((record["verdict"], mapping[record["verdict"]] == record["status"]), (word, True))
            self.assertIsInstance(record["seconds"], (int, float))


if __name__ == "__main__":
    unittest.main()
