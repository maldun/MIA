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
from call_recording import ScriptedModel                 # noqa: E402
from core import Core                                    # noqa: E402
from library import Library                              # noqa: E402
from pipeline import Tool                                # noqa: E402
from tool_calls import ToolCalls, ToolCallError          # noqa: E402
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


SKILLS, LIBRARY = os.path.join(REPO, "skills"), os.path.join(REPO, "library")


class RecordingDoor:
    """a stand-in for ToolCalls.call(run, tool, args) of IF-402 that remembers the run it was called for"""
    def __init__(self):
        self.runs = []

    def call(self, run, name, args):
        self.runs.append(run["id"])
        return {"output": [] if name == "web_search" else {"text": ""}, "trust": "untrusted"}


class F06_TheDoorGetsTheRunLogId(unittest.TestCase):
    def test_the_door_sees_the_run_id_of_the_result(self):
        """F-06. Example: Core.run("research") on the converted path with a recording door: every call of the door names the run id that RunResult.run_id has, so the
        tool_call events of the door tie to the run log record."""
        with tempfile.TemporaryDirectory() as tmp:
            records = os.path.join(tmp, "conversion")
            C.save_check(records, "research", {"suite": "EV-research", "run": "research__x.jsonl", "pins": "MP-light", "verdict": "PASS"})
            door = RecordingDoor()
            core = Core(SKILLS, Library(LIBRARY), os.path.join(tmp, "runs"), model=ScriptedModel(), conversion_dir=records, tool_calls=door,
                        door_tools={"web_search": "search_calls", "fetch_page": "fetch_calls"})
            result = core.run("research", {"question": "When did the Rivertown Bridge open to traffic?"}, started_by="command")
        self.assertTrue(door.runs, "the run made no call through the door")
        self.assertEqual(set(door.runs), {result.run_id})


DOOR_TOOLS = {"web_search": "search_calls", "fetch_page": "fetch_calls"}
SEARCH = {"tool": "web_search", "settings": {}}


class F08_TheRealDoor(unittest.TestCase):
    """the trust boundary for the web tools, tested with the real ToolCalls (IF-402), not a stand-in"""
    def door(self):
        self.asked = []
        return ToolCalls(web_search=lambda query: self.asked.append(query) or {"results": [{"url": "http://example.org/a", "title": "t", "snippet": "s"}]}, fetch_page=lambda url, max_chars=None: {"text": ""})

    def test_a_run_over_its_search_budget_through_the_real_door_ends_with_status_budget(self):
        """F-08. Example: research with search_calls 1 and the real door: the second search ends the run with status budget and the key search_calls, the door counted one search
        (the refused one counts nothing), the search of the run kept the trust label web."""
        door = self.door()
        tools = {name: Tool(None, key) for name, key in DOOR_TOOLS.items()}
        run = C.run_converted("research", {"question": "When did the Rivertown Bridge open to traffic?"}, model=ScriptedModel(), tools=tools, skills_dir=SKILLS, library_dir=LIBRARY,
                              skill_changes={"budget": {"search_calls": 1}}, tool_calls=door, door_tools=DOOR_TOOLS, run_id="R1")
        self.assertEqual(run.status, "budget", run.error)
        self.assertIn("search_calls", run.error)
        self.assertEqual(door.used("R1").get("web_search"), 1)
        self.assertEqual(len(self.asked), 1)
        self.assertIn({"kind": "tool_call", "tool": "web_search", "trust": "web"}, run.events)

    def test_a_call_the_real_door_refuses_for_its_arguments_is_given_back(self):
        """F-08. Example: search_calls 1, a search with a number as query is refused by the door (bad_arguments, nothing counted there): the refusal reaches the caller, and the
        next valid search is still inside the budget of 1."""
        door = self.door()
        ops.reset()
        ops.register_run(budget={"search_calls": 1}, tool_keys={"web_search": "search_calls"}, door=door, door_tools={"web_search": "search_calls"}, run_id="R2")
        with self.assertRaises(ToolCallError) as caught:
            ops.tool_step({"tool": SEARCH, "query": 7})
        self.assertEqual(caught.exception.code, "bad_arguments")
        self.assertEqual(ops.tool_step({"tool": SEARCH, "query": "a"})[0]["url"], "http://example.org/a")
        self.assertEqual(door.used("R2").get("web_search"), 1)
        self.assertIsNone(ops.budget_end())


if __name__ == "__main__":
    unittest.main()
