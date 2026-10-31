"""
TC-EVL-007 (N-4.1 T-05): the latency tool against a fake server that answers after 1.0, 2.0 and 3.0 s (20 runs after 3 warm-up runs, cycling);
the frame-rate tool is tested in tests/js/measure-fps.test.mjs.
Protected since A-63 (D-164). Run: python tests/acceptance/test_measure_latency.py
"""
import os
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

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


class FakeSocket:
    """stands in for the socket.io client of the live mode: after each `chat_send` it sends the first text after 0.1 s and the end of
    the answer after 0.5 s (in real time, from a thread, like the server), so a tool that times the previous answer's end measures ~0.5 s"""

    FIRST, END = 0.1, 0.5

    def __init__(self):
        self.handlers = {}

    def on(self, event, handler):
        self.handlers[event] = handler

    def call(self, event, data, timeout=None):
        threading.Timer(self.FIRST, self.handlers["chat_delta"], args=({"text": "Hi"},)).start()
        threading.Timer(self.END, self.handlers["chat_done"], args=({},)).start()
        return {"ok": True}


class Latency(unittest.TestCase):
    @mark.req("REQ-EVL-007")
    def test_median_of_twenty_runs_after_three_warmups(self):
        """TC-EVL-007: the latency tool reports the median of the timed runs and their number; warm-up runs are made but not timed.

        Example: answers after 1.0, 2.0, 3.0 s cycling, 20 runs after 3 warm-ups -> median 2.0 s, min 1.0, max 3.0, 23 runs made.
        """
        # Given: a fake server on its own clock (no real waiting)
        server = FakeServer()
        # When: 20 runs are timed after 3 warm-ups
        result = ML.measure(server.ask, clock=server.clock, runs=20, warmup=3)
        # Then: 20 timed runs, the median within 0.1 s of 2.0 s
        self.assertEqual(result["runs"], 20)
        self.assertEqual(server.asked, 23)                          # the warm-up runs are made but not counted
        self.assertAlmostEqual(result["median"], 2.0, delta=0.1)
        self.assertEqual((result["min"], result["max"]), (1.0, 3.0))

    @mark.req("REQ-EVL-007")
    def test_a_failing_run_is_counted_not_hidden(self):
        """TC-EVL-007: a run that fails is counted as failed and not timed, so a broken server cannot look fast.

        Example: every second of 4 runs raises -> runs 2, failed 2.
        """
        # Given: a server whose every second answer fails
        calls = {"n": 0}

        def ask():
            calls["n"] += 1
            if calls["n"] % 2 == 0:
                raise RuntimeError("no answer")
        # When: 4 runs are timed
        result = ML.measure(ask, clock=lambda: 0.0, runs=4, warmup=0)
        # Then: two timed, two failed
        self.assertEqual((result["runs"], result["failed"]), (2, 2))


class LiveMode(unittest.TestCase):
    @mark.req("REQ-EVL-007")
    def test_the_clock_starts_after_the_previous_answer_has_ended(self):
        """TC-EVL-007 (regression, Verify F1): the live mode times only the first text of the answer, not the wait for the end of the previous one.

        Example: first text after 0.1 s, end of the answer after 0.5 s, 3 runs -> median about 0.1 s (it was about 0.5 s).
        """
        # Given: the live mode on a fake socket whose answers start after 0.1 s and end after 0.5 s
        prepare, ask = ML.socket_ask(FakeSocket(), "Hello", timeout=5)
        # When: three runs are timed one after the other
        result = ML.measure(ask, prepare=prepare, runs=3, warmup=0)
        # Then: the median is the 0.1 s of the first text; 0.1 s of slack covers the 10 ms polling and a busy test machine
        self.assertEqual(result["runs"], 3)
        self.assertAlmostEqual(result["median"], FakeSocket.FIRST, delta=0.1)


if __name__ == "__main__":
    unittest.main()
