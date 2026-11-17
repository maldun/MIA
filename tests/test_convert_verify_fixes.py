"""
Findings of the Verify of G-V2.CONVERT (verification-report.md): each class is the failing test of one finding, written before its fix. No model, no network.
Run: python tests/test_convert_verify_fixes.py
"""
import os
import sys
import threading
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers")):
    sys.path.insert(0, path)

import common_operations as ops                          # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
