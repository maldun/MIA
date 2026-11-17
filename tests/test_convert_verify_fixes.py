"""
Findings of the Verify of G-V2.CONVERT (verification-report.md): each class is the failing test of one finding, written before its fix. No model, no network.
Run: python tests/test_convert_verify_fixes.py
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers")):
    sys.path.insert(0, path)

import common_operations as ops                          # noqa: E402
import skill_converter as C                               # noqa: E402
import plain_modules                                       # noqa: E402
from pipeline import BudgetExceeded                      # noqa: E402

setUpModule, tearDownModule = plain_modules.hooks()      # the package MIA is not importable while this module runs: F-3, tests/plain_modules.py


class F01_RunStateIsPerRun(unittest.TestCase):
    def test_two_runs_in_two_threads_keep_their_own_tool_budget_and_events(self):
        """F-01. Example: run A (tool fa, search_calls 1) and run B (tool fb, search_calls 5) start before either calls a tool; A's second call is over its budget and calls only fa,
        B's two calls are inside theirs and call only fb; each run's events hold only its own calls."""
        started = threading.Barrier(2, timeout=10)
        said, ends, events, errors = [], {}, {}, []

        def run(label, function, limit, calls):
            try:
                ops.reset()
                ops.register_tool("web_search", function)
                ops.register_run(budget={"search_calls": limit}, tool_keys={"web_search": "search_calls"}, run_id=label)
                started.wait()                       # both runs are registered before any call
                for _ in range(calls):
                    try:
                        ops.tool_step({"tool": {"tool": "web_search", "settings": {}}, "query": label})
                    except BudgetExceeded:
                        ends[label] = ops.budget_end()
                events[label] = ops.run_events()
            except Exception as exc:                 # noqa: BLE001 - a failure of a thread must fail the test, not vanish
                errors.append(exc)

        threads = [threading.Thread(target=run, args=("A", lambda query: said.append(("fa", query)), 1, 2)),
                   threading.Thread(target=run, args=("B", lambda query: said.append(("fb", query)), 5, 2))]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(20)
        self.assertEqual(errors, [])
        self.assertEqual(sorted(said), [("fa", "A"), ("fb", "B"), ("fb", "B")])
        self.assertEqual(ends, {"A": "search_calls"})
        self.assertEqual([e["tool"] for e in events["A"] if e["kind"] == "tool_call"], ["web_search"])
        self.assertEqual([e["tool"] for e in events["B"] if e["kind"] == "tool_call"], ["web_search", "web_search"])


def write_run(folder, name, variant, skill="plan_question", suite="plans", right=30, total=36):
    """a saved dev run in the shape of harness.py (header with variant, skill, pin) that passes the criterion of REQ-WFM-111"""
    path = os.path.join(folder, name)
    head = {"kind": "header", "suite": suite, "variant": variant, "repeats": 3, "cases": total, "skill": skill, "skill_version": 1, "pipeline": "plan.free@1",
            "pin": {"id": "MP-light", "name": "gemma4:12b-it-qat", "digest": "sha256:x", "seed": 7, "temperature": 0}}
    with open(path, "w") as fp:
        fp.write(json.dumps(head) + "\n")
        for i in range(total):
            for repeat in range(3):
                fp.write(json.dumps({"kind": "record", "case": "c%d" % i, "repeat": repeat, "status": "pass" if i < right else "fail", "truth": True, "tags": ["split:dev"]}) + "\n")
    return path


class F04_AcceptRefusesAWrongRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = os.path.join(self.tmp.name, "conversion")

    def accept(self, run):
        return subprocess.run([sys.executable, os.path.join(REPO, "tools", "accept_conversion.py"), "plan_question", "--run", run, "--out", self.out],
                              capture_output=True, text=True, timeout=90)

    def test_a_run_of_the_old_runner_is_refused(self):
        """F-04. Example: a passing run whose variant is not converted: exit 1, the message names the variant, no record."""
        done = self.accept(write_run(self.tmp.name, "old.jsonl", {"name": "default"}))
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("converted", done.stdout)
        self.assertEqual(C.load_checks(self.out), {})

    def test_a_run_of_another_skill_is_refused(self):
        """F-04. Example: a converted run of verify_claim offered for plan_question: exit 1, no record."""
        done = self.accept(write_run(self.tmp.name, "other.jsonl", {"name": "converted", "converted": True, "skill": "verify_claim"}, skill="verify_claim"))
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertEqual(C.load_checks(self.out), {})

    def test_a_run_of_another_suite_is_refused(self):
        """F-04. Example: a converted run of the suite verdicts offered for plan_question (EV-plans): exit 1, no record."""
        done = self.accept(write_run(self.tmp.name, "suite.jsonl", {"name": "converted", "converted": True, "skill": "plan_question"}, suite="verdicts"))
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertEqual(C.load_checks(self.out), {})

    def test_the_right_run_is_still_accepted(self):
        """F-04. Example: a converted run of plan_question on the suite plans: exit 0 and the record."""
        done = self.accept(write_run(self.tmp.name, "ok.jsonl", {"name": "converted", "converted": True, "skill": "plan_question"}))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("plan_question", C.load_checks(self.out))


if __name__ == "__main__":
    unittest.main()
