"""
TC-CHA-010
REQ-CHA-010
python tests/test_mood_score.py
"""

import os, shutil, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))
from markers import mark
from chat_log import ChatLog
from chat_service import ChatService
from moods import MoodTracker
from storage import Storage
from storage_files import FileBackend


MOODS = os.path.join(ROOT, "moods.json")


class ScoreMoodTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.mood = MoodTracker(MOODS)
        self.storage = Storage(FileBackend(os.path.join(self.dir, "db")))
        self.chat = ChatService(lambda event, payload: None, ChatLog(os.path.join(self.dir, "log.jsonl")), self.mood, lambda text, on_delta, on_emotion, should_stop: "Fine.",
                                spawn=lambda target: target(), votes=self.storage, behaviours=lambda: ["wave"])

    def offset(self):
        return self.mood.status()["offset"]

    @mark.req("REQ-CHA-010")
    def test_the_offset_starts_at_zero(self):
        self.assertEqual(self.offset(), 0.0)

    @mark.req("REQ-CHA-010")
    def test_a_plus_moves_the_offset_up_and_a_minus_down(self):
        self.mood.set_score(5)
        self.assertGreater(self.offset(), 0)
        self.mood.set_score(-5)
        self.assertLess(self.offset(), 0)
        self.mood.set_score(0)
        self.assertEqual(self.offset(), 0.0)

    @mark.req("REQ-CHA-010")
    def test_a_bigger_score_moves_it_further(self):
        self.mood.set_score(2)
        a = self.offset()
        self.mood.set_score(10)
        b = self.offset()
        self.assertGreater(b, a)
        self.mood.set_score(-2)
        c = self.offset()
        self.mood.set_score(-10)
        d = self.offset()
        self.assertLess(d, c)

    @mark.req("REQ-CHA-010")
    def test_the_offset_is_kept_between_minus_one_and_one(self):
        self.mood.set_score(1000)
        self.assertEqual(self.offset(), 1.0)
        self.mood.set_score(-1000)
        self.assertEqual(self.offset(), -1.0)

    @mark.req("REQ-CHA-010")
    def test_votes_move_the_offset_of_the_chat(self):
        self.chat.vote("anna", "voice", "service", 1)
        self.chat.vote("ben", "voice", "service", 1)
        self.assertEqual(self.offset(), 0.1)
        self.chat.vote("anna", "voice", "service", -1)
        self.assertEqual(self.offset(), 0.0)
        self.chat.vote("anna", "wave", "character_behaviour", -1)
        self.assertLess(self.offset(), 0)

    @mark.req("REQ-CHA-010")
    def test_the_status_of_the_chat_carries_the_offset(self):
        self.chat.vote("anna", "voice", "service", 1)
        self.assertEqual(self.chat.status()["mood"]["offset"], 0.05)


if __name__ == "__main__":
    unittest.main()
