"""
TC-N24-002 (REQ-WFX-005, REQ-TLS-001 AC-2: "in the run log the code checks precede the first model call of each claim"), N-2.4 integration step, D-152 (gap G-4
of the N-2.4.2 verification). The shipped pipelines that verify a claim (library/pipelines/verify.*, latest version, run through the skills verify_claim and
verify_computable) run on the real runner with the real run log (run_log.RunLog, read back from its files) and the real run events (IF-401), with a fake model.
A code check is a node of a `check.*` library entry or a `check_run` event; a model call is a `model_call` event.

The verification styles verify.single, -consistency, -jury, -cops, -trial and verify.computable call the model before any code check: findings of D-152 for the
owner, kept as expected failures (an unexpected pass fails the file). The pipelines are not changed here (a change needs an eval run).
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

    def assert_check_first(self, skill, claim, pipeline=None):
        record, if401 = self.run_claim(skill, claim, pipeline)
        logged = record["events"]
        checks = [i for i, e in enumerate(logged) if str(e.get("library", "")).startswith("check.") or e.get("type") == "check_run"]
        calls = [i for i, e in enumerate(logged) if e.get("type") == "model_call"]
        if calls:
            self.assertTrue(checks and checks[0] < calls[0], "%s: a model call before any code check" % (pipeline or skill))
        if401_calls = [i for i, e in enumerate(if401) if e["type"] == "model_call"]
        self.assertEqual(len(if401_calls), len(calls))                         # IF-401 holds the same model calls

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
        # Then: the code check comes first
        self.assert_check_first("verify_claim", WORDS, self.latest("verify.number_gate"))

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    @unittest.expectedFailure
    def test_verify_single_checks_before_the_model(self):
        """TC-N24-002 (finding of D-152): verify.single@1, the pipeline of the skill verify_claim, has no code check: its one judge is the first step.

        Example: "The tower is 330 m high." -> model_call, no code check before it.
        """
        # Given / When: the shipped skill verify_claim on its own pipeline
        # Then: (expected to fail today) the code check comes first
        self.assert_check_first("verify_claim", NUMBER)

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    @unittest.expectedFailure
    def test_verify_consistency_checks_before_the_model(self):
        """TC-N24-002 (finding of D-152): verify.consistency has no code check before its rounds of judges.

        Example: 3 rounds -> model_call first.
        """
        # Given / When / Then: as above
        self.assert_check_first("verify_claim", dict(NUMBER, rounds=3), self.latest("verify.consistency"))

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    @unittest.expectedFailure
    def test_verify_jury_checks_before_the_model(self):
        """TC-N24-002 (finding of D-152): verify.jury has no code check before its experts.

        Example: one expert -> model_call first.
        """
        # Given / When / Then: as above
        self.assert_check_first("verify_claim", dict(NUMBER, experts=[{"name": "historian", "context": "You are a historian."}]), self.latest("verify.jury"))

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    @unittest.expectedFailure
    def test_verify_cops_checks_before_the_model(self):
        """TC-N24-002 (finding of D-152): verify.cops has no code check before its two sides and the judge.

        Example: -> model_call (argue for) first.
        """
        # Given / When / Then: as above
        self.assert_check_first("verify_claim", NUMBER, self.latest("verify.cops"))

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    @unittest.expectedFailure
    def test_verify_trial_checks_before_the_model(self):
        """TC-N24-002 (finding of D-152): verify.trial has no code check before defence and prosecution.

        Example: -> model_call (defence) first.
        """
        # Given / When / Then: as above
        self.assert_check_first("verify_claim", NUMBER, self.latest("verify.trial"))

    # REQ-WFX-005
    @mark.req("REQ-WFX-005", "REQ-TLS-001")
    @unittest.expectedFailure
    def test_verify_computable_checks_before_the_model(self):
        """TC-N24-002 (finding of D-152): verify.computable lets the model write the check script before check.script runs it (the check is model-written).

        Example: "2 plus 3 is 5" with the data a, b, claimed -> model_call (write) before check.script.
        """
        # Given / When / Then: as above, through the shipped skill verify_computable
        self.assert_check_first("verify_computable", {"claim": "2 plus 3 is 5", "data_description": "a, b, claimed", "data": {"a": 2, "b": 3, "claimed": 5}})

    @staticmethod
    def latest(pipeline):
        versions = [int(name[:-5]) for name in os.listdir(os.path.join(ROOT, "library", "pipelines", pipeline)) if name.endswith(".json")]
        return "%s@%d" % (pipeline, max(versions))


if __name__ == "__main__":
    unittest.main()
