"""
TC-WFM-031 (REQ-WFM-031) and TC-WFM-033 (REQ-WFM-033): the task monitor merges the reports of a task, emits `task_status` at most every half second and once more at the end, and does not count paused time.
Run: python tests/test_task_monitor.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from task_monitor import TaskMonitor  # noqa: E402


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class TaskMonitorTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.events = []
        self.monitor = TaskMonitor(lambda event, payload: self.events.append((event, payload)), "m7", "review", mode="run", clock=self.clock)

    def test_two_reports_within_half_a_second_give_one_update_and_the_merged_figures_stay(self):
        self.monitor.update(phase="searching", counts={"on_list": 3})
        self.clock.now = 0.2
        self.monitor.update(counts={"processed": 1}, budget={"tokens": {"used": 100, "limit": 1000}})
        self.assertEqual(len(self.events), 1)
        self.assertEqual(self.events[0][0], "task_status")
        self.assertEqual(self.events[0][1]["counts"], {"on_list": 3})
        self.assertEqual(self.monitor.state()["counts"], {"on_list": 3, "processed": 1})
        self.clock.now = 0.6
        self.monitor.update(counts={"processed": 2})
        self.assertEqual(len(self.events), 2)
        self.assertEqual(self.events[1][1]["counts"], {"on_list": 3, "processed": 2})
        self.assertEqual(self.events[1][1]["budget"]["tokens"], {"used": 100, "limit": 1000})

    def test_finish_emits_the_final_figures_even_within_the_interval(self):
        self.monitor.update(counts={"included": 1})
        self.clock.now = 0.1
        self.monitor.update(counts={"included": 2})
        self.monitor.finish()
        self.assertEqual(len(self.events), 2)
        self.assertTrue(self.events[-1][1]["done"])
        self.assertEqual(self.events[-1][1]["counts"], {"included": 2})
        self.assertEqual((self.events[-1][1]["id"], self.events[-1][1]["task"], self.events[-1][1]["mode"]), ("m7", "review", "run"))

    def test_seconds_are_counted_by_the_monitor_and_keep_the_limit_that_was_reported(self):
        self.monitor.update(budget={"seconds": {"limit": 60}})
        self.clock.now = 5.0
        self.assertEqual(self.monitor.state()["budget"]["seconds"], {"used": 5.0, "limit": 60})

    def test_paused_time_is_not_counted(self):
        self.clock.now = 10.0
        self.monitor.pause()
        self.assertTrue(self.events[-1][1]["paused"])
        self.clock.now = 20.0
        self.assertEqual(self.monitor.state()["budget"]["seconds"]["used"], 10.0)
        self.monitor.resume()
        self.assertFalse(self.events[-1][1]["paused"])
        self.clock.now = 25.0
        self.assertEqual(self.monitor.state()["budget"]["seconds"]["used"], 15.0)


    def test_time_spent_waiting_for_the_user_is_not_counted(self):
        self.clock.now = 10.0
        self.monitor.begin_wait()
        self.clock.now = 70.0
        self.assertEqual(self.monitor.state()["budget"]["seconds"]["used"], 10.0)
        self.assertFalse(self.monitor.state()["paused"])                          # waiting is not a pause: the card does not say paused
        self.monitor.end_wait()
        self.clock.now = 75.0
        self.assertEqual(self.monitor.state()["budget"]["seconds"]["used"], 15.0)


if __name__ == '__main__':
    unittest.main()
