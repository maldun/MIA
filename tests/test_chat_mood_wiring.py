"""Chat agent N-2.2, TC-CHA-009 (REQ-CHA-009, findings F4 and F5 of the first Verify, D-173): when a user's page connects, MIA holds the greeting mood and the
page hears it, she never breaks off an answer in progress for it, and a crash of the worker puts her in the error mood. Run with: python tests/test_chat_mood_wiring.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
from chat_log import ChatLog                              # noqa: E402
from chat_service import ChatService                      # noqa: E402
from moods import MoodTracker                             # noqa: E402

MOODS = os.path.join(ROOT, "moods.json")


class MoodWiringTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.events = []
        self.mood = MoodTracker(MOODS)
        self.inside = []                                  # what greet() answered and what the mood was while an answer ran

        def exchange(text, on_delta, on_emotion, should_stop):
            self.inside.append((self.chat.greet(), self.mood.status()["emotion"]))
            return "One."

        self.chat = ChatService(lambda event, payload: self.events.append((event, payload)), ChatLog(os.path.join(self.dir, "log.jsonl")), self.mood,
                                exchange, queue_size=5, user_limit=2, spawn=lambda target: target())

    @mark.req("REQ-CHA-009")
    def test_a_connecting_page_makes_her_greet(self):
        """TC-CHA-009 (F4): greet() holds the mood the map assigns to greeting and sends the new status to the pages.

        Example: situations.greeting = {"emotion": "happy"} -> status emotion happy, one more chat_status event.
        """
        # Given: the mood map and an idle MIA
        wanted = json.load(open(MOODS, encoding="utf-8"))["situations"]["greeting"]["emotion"]
        before = len([e for e in self.events if e[0] == "chat_status"])
        # When: a page connects
        changed = self.chat.greet()
        # Then: she greets and the pages hear it
        self.assertTrue(changed)
        self.assertEqual(self.mood.status()["emotion"], wanted)
        self.assertEqual(len([e for e in self.events if e[0] == "chat_status"]), before + 1)

    @mark.req("REQ-CHA-009")
    def test_a_second_connection_keeps_the_greeting_mood(self):
        """TC-CHA-009 (F4): another page connecting while she greets leaves the greeting mood in place (its time starts again, it does not flip).

        Example: greet(), greet() -> the emotion is the greeting emotion both times.
        """
        # Given: she has greeted once
        wanted = json.load(open(MOODS, encoding="utf-8"))["situations"]["greeting"]["emotion"]
        self.chat.greet()
        # When: another page connects
        self.chat.greet()
        # Then: she still greets
        self.assertEqual(self.mood.status()["emotion"], wanted)

    @mark.req("REQ-CHA-009")
    def test_a_connecting_page_does_not_break_off_an_answer_in_progress(self):
        """TC-CHA-009 (F4): while an answer runs, greet() does nothing, so the thinking or speaking mood stays.

        Example: greet() called from inside the running exchange -> False, the emotion is the one before.
        """
        # Given: the mood before any answer
        emotion = self.mood.status()["emotion"]
        # When: a message is answered and a page connects during the answer
        self.chat.send("hi", author="anna")
        # Then: greet() reported no change and the mood was untouched meanwhile
        self.assertEqual(self.inside, [(False, emotion)])


class ErrorMoodTest(unittest.TestCase):
    @mark.req("REQ-CHA-009")
    def test_a_crash_after_the_answer_puts_her_in_the_error_mood(self):
        """TC-CHA-009 (F5): when a step after the exchange raises something unexpected (here the repair of the answer), the worker survives, the page gets
        a chat_error and she holds the mood of the situation error. (A crash of the exchange itself is the offline mood: test_chat_backend.)

        Example: situations.error = {"emotion": "embarrassed"}; the repair raises RuntimeError -> chat_error event, emotion embarrassed.
        """
        # Given: a service whose repair step crashes
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        events, mood = [], MoodTracker(MOODS)

        def repair(text):
            raise RuntimeError("boom")

        chat = ChatService(lambda event, payload: events.append((event, payload)), ChatLog(os.path.join(directory, "log.jsonl")), mood,
                           lambda text, on_delta, on_emotion, should_stop: "One.", queue_size=5, user_limit=2, spawn=lambda target: target(), repair=repair)
        wanted = json.load(open(MOODS, encoding="utf-8"))["situations"]["error"]["emotion"]
        # When: a message is answered
        chat.send("hi", author="anna")
        # Then: the page was told and she holds the error mood
        self.assertIn("chat_error", [name for name, _ in events])
        self.assertEqual(mood.status()["emotion"], wanted)


if __name__ == "__main__":
    unittest.main()
