"""TC-CHA-009 (REQ-CHA-009): while MIA is idle, thinking, speaking, waiting, greeting a user, reporting an error or offline, she holds the mood the mood map assigns to
the situation, changes it with events and settles it back over time. Run with: python tests/test_moods_situations.py"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
from moods import MoodTracker                             # noqa: E402

SITUATIONS = ("idle", "thinking", "speaking", "waiting", "greeting", "error", "offline")
MOODS = os.path.join(ROOT, "moods.json")


class SituationTest(unittest.TestCase):
    def setUp(self):
        self.now = [1000.0]
        with open(MOODS, encoding="utf-8") as fp:
            self.map = json.load(fp)

    def tracker(self):
        return MoodTracker(MOODS, hold_minutes=10, clock=lambda: self.now[0])

    @mark.req("REQ-CHA-009")
    def test_the_map_names_all_seven_situations(self):
        self.assertEqual(sorted(self.map["situations"]), sorted(SITUATIONS))

    @mark.req("REQ-CHA-009")
    def test_each_situation_holds_the_mood_of_the_map(self):
        for situation in SITUATIONS:
            with self.subTest(situation=situation):
                tracker = self.tracker()
                tracker.set_emotion("sad")
                tracker.set_activity("dreaming")                       # another state first, so that entering has something to change
                tracker.enter(situation)
                entry, status = self.map["situations"][situation], tracker.status()
                if "activity" in entry:
                    self.assertEqual(status["activity"], entry["activity"])
                else:
                    self.assertIsNone(status["activity"])
                    self.assertEqual(status["emotion"], entry["emotion"])

    @mark.req("REQ-CHA-009")
    def test_every_situation_of_the_map_points_at_a_mood_that_exists(self):
        for situation, entry in self.map["situations"].items():
            if "activity" in entry:
                self.assertIn(entry["activity"], self.map["activities"], situation)
            elif entry["emotion"] is not None:
                self.assertIn(entry["emotion"], self.map["emotions"], situation)

    @mark.req("REQ-CHA-009")
    def test_idle_is_the_ready_line_and_the_text_comes_from_the_map(self):
        tracker = self.tracker()
        tracker.set_emotion("sad")
        tracker.enter("idle")
        self.assertIsNone(tracker.status()["emotion"])
        self.assertIn(tracker.status()["text"], self.map["ready"]["texts"])

    @mark.req("REQ-CHA-009")
    def test_waiting_has_a_text_of_its_own(self):
        tracker = self.tracker()
        tracker.enter("waiting")
        self.assertEqual(tracker.status()["text"], self.map["activities"]["waiting"]["texts"][0])

    @mark.req("REQ-CHA-009")
    def test_an_unknown_situation_changes_nothing(self):
        tracker = self.tracker()
        tracker.set_emotion("happy")
        self.assertFalse(tracker.enter("sleeping"))
        self.assertEqual(tracker.status()["emotion"], "happy")

    @mark.req("REQ-CHA-009")
    def test_a_held_emotion_settles_back_over_time(self):
        tracker = self.tracker()
        tracker.enter("greeting")
        self.assertEqual(tracker.status()["emotion"], self.map["situations"]["greeting"]["emotion"])
        self.now[0] += 11 * 60
        self.assertIsNone(tracker.status()["emotion"])


if __name__ == "__main__":
    unittest.main()
