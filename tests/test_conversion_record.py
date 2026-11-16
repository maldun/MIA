"""
The persistent acceptance record of a converted skill (T-CV-09 part, G-V2.CONVERT, D-256, D-257; REQ-WFM-057, 059, 060): one JSON file per skill, written only after a PASS,
read by SkillConverter at start; tools/accept_conversion.py is the only writer.
Run: python tests/test_conversion_record.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers")):
    sys.path.insert(0, path)

import skill_converter as C                               # noqa: E402

REQUIREMENTS = os.path.join(REPO, "specs", "mia", "nodes", "N-2-backend", "nodes", "N-2.3-workflow-management", "requirements.md")
PIN = {"id": "MP-light", "name": "gemma4:12b-it-qat", "digest": "sha256:x", "seed": 7, "temperature": 0}
GOOD = {"suite": "EV-plans", "run": "plans__converted__x.jsonl", "pins": "MP-light", "verdict": "PASS"}


def write_run(folder, name, suite, right, total=20, pin=PIN):
    path = os.path.join(folder, name)
    with open(path, "w") as fp:
        fp.write(json.dumps({"kind": "header", "suite": suite, "repeats": 3, "cases": total, "pin": pin, "skill": "plan_question", "skill_version": 1, "pipeline": "plan.free@1"}) + "\n")
        for i in range(total):
            for repeat in range(3):
                fp.write(json.dumps({"kind": "record", "case": "c%d" % i, "repeat": repeat, "status": "pass" if i < right else "fail", "truth": True, "tags": ["split:dev"]}) + "\n")
    return path


class Store(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = os.path.join(self.tmp.name, "conversion")

    def test_a_saved_check_comes_back(self):
        """Example: save_check(dir, "plan_question", GOOD) then load_checks(dir) is {"plan_question": GOOD}."""
        # Given a record saved for one skill
        C.save_check(self.folder, "plan_question", GOOD)
        # When the folder is read
        # Then the check is there with the same fields
        self.assertEqual(C.load_checks(self.folder), {"plan_question": GOOD})

    def test_a_missing_folder_has_no_checks(self):
        """Example: a folder that does not exist gives {} (nothing is converted)."""
        self.assertEqual(C.load_checks(os.path.join(self.tmp.name, "none")), {})

    def test_a_check_that_is_no_pass_is_not_saved(self):
        """Example: save_check with verdict FAIL raises ConversionError and writes no file."""
        # Given a failed check
        # When it is saved
        with self.assertRaises(C.ConversionError):
            C.save_check(self.folder, "plan_question", dict(GOOD, verdict="FAIL"))
        # Then nothing was written
        self.assertEqual(C.load_checks(self.folder), {})

    def test_a_skill_name_cannot_leave_the_folder(self):
        """Example: the skill name ../x is refused (the name becomes a file name)."""
        with self.assertRaises(C.ConversionError):
            C.save_check(self.folder, "../x", GOOD)

    def test_a_damaged_or_incomplete_file_counts_as_no_check(self):
        """Example: a file with invalid JSON and a file without a run are ignored, so the skill stays on the old runner."""
        os.makedirs(self.folder)
        with open(os.path.join(self.folder, "a.json"), "w") as fp:
            fp.write("{not json")
        with open(os.path.join(self.folder, "b.json"), "w") as fp:
            json.dump({"suite": "EV-plans", "verdict": "PASS"}, fp)
        self.assertEqual(C.load_checks(self.folder), {})

    def test_the_converter_starts_with_the_recorded_skills_converted(self):
        """Example: with a record for plan_question, state("plan_question") is converted and state("verify_claim") is unconverted."""
        # Given a record for one skill
        C.save_check(self.folder, "plan_question", GOOD)
        # When the converter starts with the folder
        conv = C.SkillConverter(lambda n: ({}, {}), lambda n: ({}, {}), None, records_dir=self.folder)
        # Then only that skill is converted
        self.assertEqual((conv.state("plan_question"), conv.state("verify_claim")), ("converted", "unconverted"))

    def test_the_criterion_line_is_read_from_the_requirement(self):
        """Example: criterion_of("REQ-WFM-111", requirements) is the Eval criterion line of EV-plans with min=0.54."""
        line = C.criterion_of("REQ-WFM-111", REQUIREMENTS)
        self.assertIn("suite=EV-plans", line)
        self.assertIn("min=0.54", line)
        with self.assertRaises(C.ConversionError):
            C.criterion_of("REQ-WFM-999", REQUIREMENTS)


class AcceptScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = os.path.join(self.tmp.name, "conversion")

    def accept(self, run, *more):
        return subprocess.run([sys.executable, os.path.join(REPO, "tools", "accept_conversion.py"), "plan_question", "--run", run, "--out", self.out, *more],
                              capture_output=True, text=True, timeout=90)

    def test_a_passing_run_writes_the_record_with_the_pin(self):
        """Example: 30 of 36 right (0.83, limit 0.54) on EV-plans: exit 0, data/conversion/plan_question.json has verdict PASS, suite EV-plans, pins MP-light and the run file."""
        # Given a passing run of the suite plans
        run = write_run(self.tmp.name, "r.jsonl", "plans", 30, total=36)
        # When the owner accepts it
        done = self.accept(run)
        # Then the record is written
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        check = C.load_checks(self.out)["plan_question"]
        self.assertEqual((check["verdict"], check["suite"], check["pins"]), ("PASS", "EV-plans", "MP-light"))
        self.assertTrue(check["run"].endswith("r.jsonl"))

    def test_a_failing_run_writes_nothing(self):
        """Example: 10 of 36 right: exit 1 and no file."""
        run = write_run(self.tmp.name, "r.jsonl", "plans", 10, total=36)
        done = self.accept(run)
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertEqual(C.load_checks(self.out), {})

    def test_a_skill_without_an_equivalence_requirement_is_refused(self):
        """Example: chat is one of the nine skills that stay on the old runner: exit 2 and no file."""
        run = write_run(self.tmp.name, "r.jsonl", "plans", 30, total=36)
        done = subprocess.run([sys.executable, os.path.join(REPO, "tools", "accept_conversion.py"), "chat", "--run", run, "--out", self.out], capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertEqual(C.load_checks(self.out), {})


if __name__ == "__main__":
    unittest.main()
