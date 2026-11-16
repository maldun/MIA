"""
The per-suite check runner of the converted skills (T-CV-09, G-V2.CONVERT; TC-WFM-110 to 114 as steps of stage 4): tools/check_conversion.py <skill> runs the dev suite of the skill on the
graph path with the pin and repeats of the requirement's Eval criterion and decides it with eval_decide.py; it never writes an acceptance record (D-257).
Run: python tests/test_check_conversion.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))

import check_conversion as K                                 # noqa: E402

REQUIREMENTS = os.path.join(REPO, "specs", "mia", "nodes", "N-2-backend", "nodes", "N-2.3-workflow-management", "requirements.md")
SCRIPT = os.path.join(REPO, "tools", "check_conversion.py")


def write_run(folder, name, suite, right, total):
    path = os.path.join(folder, name)
    with open(path, "w") as fp:
        fp.write(json.dumps({"kind": "header", "suite": suite, "repeats": 3, "cases": total, "pin": {"id": "MP-light"}}) + "\n")
        for i in range(total):
            for repeat in range(3):
                fp.write(json.dumps({"kind": "record", "case": "c%d" % i, "repeat": repeat, "status": "pass" if i < right else "fail", "truth": True, "tags": ["split:dev"]}) + "\n")
    return path


class Command(unittest.TestCase):
    def test_the_eval_command_uses_the_suite_the_pin_and_the_repeats_of_the_criterion(self):
        """Example: for plan_question the command is eval.py run plans --pin MP-light --repeats 3 --skill plan_question --variant converted --converted --quiet."""
        # Given the criterion line of REQ-WFM-111
        # When the command is built
        command = K.eval_command("plan_question", REQUIREMENTS, results="/r")
        # Then it names the suite folder (EV-plans is plans), the pin and repeats of the line, and the converted variant
        tail = command[command.index("run"):]
        self.assertEqual(tail[:2], ["run", "plans"])
        for pair in (["--pin", "MP-light"], ["--repeats", "3"], ["--skill", "plan_question"], ["--variant", "converted"], ["--results", "/r"]):
            self.assertEqual(tail[tail.index(pair[0]) + 1], pair[1], pair)
        self.assertIn("--converted", tail)

    def test_every_skill_with_a_model_has_a_command_and_the_rule_based_one_has_none(self):
        """Example: research, plan_question, verify_claim, verify_computable and extract_claims give a command; extract_claims_rules raises (it has no model, TC-WFM-115 runs in stage 2)."""
        for skill in ("research", "plan_question", "verify_claim", "verify_computable", "extract_claims"):
            self.assertTrue(K.eval_command(skill, REQUIREMENTS))
        with self.assertRaises(K.CheckError):
            K.eval_command("extract_claims_rules", REQUIREMENTS)


class Deciding(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def check(self, right, *more, suite="plans"):
        run = write_run(self.tmp.name, "r.jsonl", suite, right, 36)
        return subprocess.run([sys.executable, SCRIPT, "plan_question", "--run", run, "--out", self.tmp.name, *more], capture_output=True, text=True, timeout=90)

    def test_a_passing_run_exits_0_and_names_the_criterion(self):
        """Example: 30 of 36 right (0.83, limit 0.54): exit 0 and PASS with the criterion line printed."""
        done = self.check(30)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("PASS", done.stdout)
        self.assertIn("min=0.54", done.stdout)

    def test_a_failing_run_exits_1(self):
        """Example: 10 of 36 right: exit 1 and FAIL; the output says that one re-run is allowed."""
        done = self.check(10)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("re-run", done.stdout)

    def test_a_run_of_another_suite_is_not_decided_and_exits_2(self):
        """Example: a run of the suite verdicts for plan_question: NOT DECIDED, exit 2."""
        self.assertEqual(self.check(30, suite="verdicts").returncode, 2)

    def test_no_acceptance_record_is_written(self):
        """Example: after a PASS the folder of --out has no conversion record (only the owner's accept_conversion.py writes one, D-257)."""
        self.check(30)
        self.assertEqual([f for f in os.listdir(self.tmp.name) if f.endswith(".json") and f != "r.jsonl"], [])

    def test_a_fail_is_decided_again_with_the_rerun_file(self):
        """Example: 10 of 36 in the first and the re-run: FAIL (after the re-run); 30 of 36 in the re-run does not rescue a failed first run silently: the decision names both."""
        rerun = write_run(self.tmp.name, "r2.jsonl", "plans", 10, 36)
        done = self.check(10, "--rerun", rerun)
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertNotIn("a FAIL counts only after one re-run", done.stdout)


if __name__ == "__main__":
    unittest.main()
