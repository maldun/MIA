"""
TC-EVL-007 (N-4.1 T-05): the latency tool against a fake server that answers after 1.0, 2.0 and 3.0 s (20 runs after 3 warm-up runs, cycling);
the frame-rate tool is tested in tests/js/measure-fps.test.mjs.
Run: python tests/test_measure_latency.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
sys.path.insert(0, os.path.join(HERE, "helpers"))

import measure_latency as ML                          # noqa: E402
from markers import mark                              # noqa: E402


class FakeServer:
    """answers after 1.0, 2.0, 3.0, 1.0 ... seconds on a clock that it moves itself, so that the test needs no real time"""

    def __init__(self):
        self.now, self.asked = 0.0, 0

    def clock(self):
        return self.now

    def ask(self):
        self.now += (1.0, 2.0, 3.0)[self.asked % 3]
        self.asked += 1


class Latency(unittest.TestCase):
    @mark.req("REQ-EVL-007")
    def test_median_of_twenty_runs_after_three_warmups(self):
        server = FakeServer()
        result = ML.measure(server.ask, clock=server.clock, runs=20, warmup=3)
        self.assertEqual(result["runs"], 20)
        self.assertEqual(server.asked, 23)                          # the warm-up runs are made but not counted
        self.assertAlmostEqual(result["median"], 2.0, delta=0.1)
        self.assertEqual((result["min"], result["max"]), (1.0, 3.0))

    def test_a_failing_run_is_counted_not_hidden(self):
        calls = {"n": 0}

        def ask():
            calls["n"] += 1
            if calls["n"] % 2 == 0:
                raise RuntimeError("no answer")
        result = ML.measure(ask, clock=lambda: 0.0, runs=4, warmup=0)
        self.assertEqual((result["runs"], result["failed"]), (2, 2))


if __name__ == "__main__":
    unittest.main()
