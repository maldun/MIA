"""
TC-N24-002 (REQ-WFX-005, REQ-TLS-001 AC-2 as reworded by D-153: "for a claim that goes through the number gate, in the run log the code checks precede the first
model call of that claim"), N-2.4 integration step (gap G-4 of the N-2.4.2 verification, D-152, D-153). The shipped pipelines that verify a claim
(library/pipelines/verify.*, latest version, through the skills verify_claim and verify_computable) run on the real runner with the real run log (run_log.RunLog,
read back from its files) and the real run events (IF-401), with a fake model. A code check is a node of a `check.*` library entry or a `check_run` event; a
model call is a `model_call` event. The gate must hold; the styles single, consistency, jury, cops, trial stand behind the gate and verify.computable lets the
model write its check: both are pinned as they are, not as failures of AC-2.
Run with: python tests/test_claim_pipelines_check_first.py
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                       # noqa: E402
from core import Core                                          # noqa: E402
from library import Library                                    # noqa: E402
from run_events import RunEvents                               # noqa: E402

NUMBER = {"claim": "The tower is 330 m high.", "evidence": "The tower is 330 m high."}
WORDS = {"claim": "The tower is very tall.", "evidence": "The tower is tall."}


class FakeModel:
    """answers every schema of the verification steps with a valid reply: points for an argue step, a script for a script step, else a vote"""

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        required = (schema or {}).get("required", [])
        if "points" in required:
            return json.dumps({"points": ["a fair point about the claim"]})
        if "script" in required:
            return json.dumps({"script": "verdict(True)", "approach": "recompute it"})
        return json.dumps({"verdict": "supported", "reason": "the evidence says the same", "confidence": 0.8})


class ClaimPipelinesCheckFirst(unittest.TestCase):

    def run_claim(self, skill, claim, pipeline=None):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        events = RunEvents(os.path.join(folder, "events"))
        core = Core(os.path.join(ROOT, "skills"), Library(os.path.join(ROOT, "library")), os.path.join(folder, "runs"), model=FakeModel(), run_events=events)
        result = core.run(skill, claim, **({"pipeline": pipeline} if pipeline else {}))
        self.assertEqual(result.status, "done", result.error)
        [record] = [run for run in core.run_log.read() if run.get("id") == result.run_id]
        return record, events.events(result.run_id)

    @staticmethod
    def positions(logged):
        """(code checks, model calls) as positions in the events of a run record"""
        checks = [i for i, e in enumerate(logged) if str(e.get("library", "")).startswith("check.") or e.get("type") == "check_run"]
        calls = [i for i, e in enumerate(logged) if e.get("type") == "model_call"]
        return checks, calls

    def assert_check_first(self, skill, claim, pipeline=None):
        record, if401 = self.run_claim(skill, claim, pipeline)
        checks, calls = self.positions(record["events"])
        if calls:
            self.assertTrue(checks and checks[0] < calls[0], "%s: a model call before any code check" % (pipeline or skill))
        if401_calls = [i for i, e in enumerate(if401) if e["type"] == "model_call"]
        self.assertEqual(len(if401_calls), len(calls))                         # IF-401 holds the same model calls
        return if401

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    def test_the_number_gate_checks_a_number_claim_before_the_model(self):
        """TC-N24-002: verify.number_gate (latest) runs check.number before its first model call, in the run log.

        Example: "The tower is 330 m high." with the same sentence as evidence -> check.number, then the judges.
        """
        # Given / When: a claim with a number through the gate
        # Then: the code check comes first
        self.assert_check_first("verify_claim", NUMBER, self.latest("verify.number_gate"))

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    def test_the_number_gate_checks_a_claim_without_a_number_before_the_model(self):
        """TC-N24-002: verify.number_gate (latest) runs its code check first also for a claim without a number.

        Example: "The tower is very tall." -> check.number (nothing to compare), then one judge.
        """
        # Given / When: a claim without a number through the gate
        if401 = self.assert_check_first("verify_claim", WORDS, self.latest("verify.number_gate"))
        # Then: the code check comes first, also in IF-401: the check found nothing to compare and says so (D-153)
        checks = [i for i, e in enumerate(if401) if e["type"] == "check_run" and e["payload"]["name"] == "number_check"]
        calls = [i for i, e in enumerate(if401) if e["type"] == "model_call"]
        self.assertTrue(checks and calls and checks[0] < calls[0])
        self.assertEqual(if401[checks[0]]["payload"]["result"], "skipped")

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    def test_the_default_pipeline_of_verify_claim_checks_first(self):
        """TC-N24-002 (D-153): the skill verify_claim on its default pipeline (the number gate) runs a code check before its first model call, with and without a number.

        Example: verify_claim without a variant, "The tower is 330 m high." and "The tower is very tall." -> check.number before the first judge.
        """
        for claim in (NUMBER, WORDS):
            with self.subTest(claim=claim["claim"]):
                # Given / When: the shipped skill without a pipeline variant
                # Then: the code check comes first
                self.assert_check_first("verify_claim", claim)
                self.assertTrue(self.positions(self.run_claim("verify_claim", claim)[0]["events"])[0])

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    def test_the_other_styles_are_styles_behind_the_gate(self):
        """TC-N24-002 (D-153): the styles single, consistency, jury, cops, trial have no code check of their own and judge with the model first; AC-2 does not
        apply to them because they stand behind the gate. Pinned so that a change of this shows here.

        Example: verify.cops@1 alone -> model_call first, no check.* node, no check_run.
        """
        for pipeline, extra in (("verify.single", {}), ("verify.consistency", {"rounds": 3}), ("verify.cops", {}), ("verify.trial", {}),
                                ("verify.jury", {"experts": [{"name": "historian", "context": "You are a historian."}]})):
            with self.subTest(pipeline=pipeline):
                # Given / When: the style run alone on a claim with a number
                record, if401 = self.run_claim("verify_claim", dict(NUMBER, **extra), self.latest(pipeline))
                # Then: it calls the model and runs no code check
                checks, calls = self.positions(record["events"])
                self.assertEqual(checks, [])
                self.assertTrue(calls)

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    def test_verify_computable_lets_the_model_write_its_check(self):
        """TC-N24-002 (D-153): verify.computable, the pipeline of the skill verify_computable, is no number-gate claim: the model writes the check script, then
        check.script runs it. Pinned as it is.

        Example: "2 plus 3 is 5" with the data a, b, claimed -> model_call (write) before check.script.
        """
        # Given / When: the shipped skill verify_computable
        record, if401 = self.run_claim("verify_computable", {"claim": "2 plus 3 is 5", "data_description": "a, b, claimed", "data": {"a": 2, "b": 3, "claimed": 5}})
        # Then: the first model call comes before the code check
        checks, calls = self.positions(record["events"])
        self.assertTrue(checks and calls and calls[0] < checks[0])

    @staticmethod
    def latest(pipeline):
        versions = [int(name[:-5]) for name in os.listdir(os.path.join(ROOT, "library", "pipelines", pipeline)) if name.endswith(".json")]
        return "%s@%d" % (pipeline, max(versions))


if __name__ == "__main__":
    unittest.main()
