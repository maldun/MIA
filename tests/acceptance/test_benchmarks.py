"""
Acceptance test of the benchmark definition (specs/number-gate/requirements.md: NFR-BUD-001; BM-GATE-001 in test-spec.md), written before the code (Plan, step 4).
The benchmark itself needs Ollama (benchmarks/bm_gate_001.py); this test checks that its baseline has been measured and that the measured median is inside the budget.
It is red until task T-06 has measured the baseline on the new suites. Protected after the Plan gate. Run with: python tests/acceptance/test_benchmarks.py
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                 # noqa: E402


class Benchmarks(unittest.TestCase):
    @mark.req("NFR-BUD-001")
    def test_the_baseline_of_the_gate_time_is_measured_and_inside_the_budget(self):
        """BM-GATE-001: benchmarks/baseline.json holds the measured median (seconds per claim, MP-light, 100 claims) and it is at most 10 s."""
        entry = json.load(open(os.path.join(REPO, "benchmarks", "baseline.json"), encoding="utf-8"))["BM-GATE-001"]
        self.assertEqual(entry["budget_median_seconds"], 10.0)
        self.assertIsNotNone(entry["median_seconds"], "the baseline is measured at task T-06")
        self.assertLessEqual(entry["median_seconds"], entry["budget_median_seconds"])


if __name__ == "__main__":
    unittest.main()
