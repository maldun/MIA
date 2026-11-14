"""
Unit test of the run recorder under two threads (F-01 of the first Verify run of G-V3.PANEL, REQ-WFM-133): answers come from the HTTP thread while the skill
thread reports; no answer may get lost. Run with: python tests/test_skill_runs_race.py
"""
import copy
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from skill_runs import SkillRunRecorder                      # noqa: E402
from skill_runs_fakes import FakeClock, FakeSkillRunStorage  # noqa: E402


class SlowStorage(FakeSkillRunStorage):
    """a read takes a moment, as on a file or a database, so load-change-save of two threads overlaps"""
    def get(self, *args, **kwargs):
        row = copy.deepcopy(super().get(*args, **kwargs))      # a real backend returns a copy
        time.sleep(0.003 if threading.current_thread().name == "skill" else 0.0005)
        return row


class TestRecorderRace(unittest.TestCase):
    def test_answers_survive_reports_of_the_skill_thread(self):
        """Example: 30 answers while the skill thread reports 30 times: 30 answers are kept"""
        clock = FakeClock()
        # Given: a recorder on a storage whose reads take a moment, and a skill thread that reports 30 times
        recorder = SkillRunRecorder(SlowStorage(), lambda event, payload: None, clock=clock.monotonic, now=clock.now)
        recorder.start("r1", "review", "1", "carl", phases=("a", "b"))
        reporter = threading.Thread(name="skill", target=lambda: [recorder.report("r1", counts={"n": i}) for i in range(30)])
        # When: the HTTP thread answers 30 times while the skill thread reports
        reporter.start()
        for i in range(30):
            recorder.answer("r1", "answer %d" % i)
        reporter.join()
        # Then: all 30 answers and the last figures are in the record
        record = recorder.record("r1")
        self.assertEqual(len(record["answers"]), 30)
        self.assertEqual(record["counts"], {"n": 29})


if __name__ == "__main__":
    unittest.main()
