"""Chat agent N-2.2, speak again next to a running answer (A-132, A-133; verification report F2): the status in an overlap (REQ-CHA-035, REQ-CHA-036). The service runs on real threads here, with a blocking fake model and a blocking fake voice (TR-VOICE-001).
Run with: python tests/test_chat_speak_overlap.py"""
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

from markers import mark                                  # noqa: E402
from chat_log import ChatLog                              # noqa: E402
from chat_service import ChatService                      # noqa: E402
from moods import MoodTracker                             # noqa: E402
from test_chat_speak_again import FakeVoice, WAIT         # noqa: E402


def until(condition, seconds=WAIT):
    """polls a condition; True when it became true in time"""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if condition():
            return True
        time.sleep(0.02)
    return condition()


class OverlapTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.events = []
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))
        self.entered = threading.Event()      # the fake model has been asked
        self.release = threading.Event()      # lets the fake model answer
        self.voice = FakeVoice(block=True)
        self.addCleanup(self.release.set)

    def model(self, text, on_delta, on_emotion, should_stop):
        self.entered.set()
        while not self.release.is_set() and not should_stop():
            time.sleep(0.02)
        return "Answer."

    def chat(self):
        self.chat_service = ChatService(lambda event, payload: self.events.append((event, payload)), self.log, MoodTracker(os.path.join(ROOT, "moods.json")),
                                        self.model, queue_size=5, user_limit=2, spawn=lambda target: threading.Thread(target=target, daemon=True).start(),
                                        speak=self.voice)
        self.addCleanup(self.chat_service.stop)
        return self.chat_service

    def stored(self):
        return self.log.append("assistant", "One. Two.")["id"]

    def published(self):
        statuses = [p for event, p in self.events if event == "chat_status"]
        return (statuses[-1]["busy"], statuses[-1]["activity"]) if statuses else None

    def assert_both(self, chat, expected, step):
        """the status of the service and the newest published one say the same"""
        self.assertTrue(until(lambda: self.published() == expected), "%s: published %s, wanted %s" % (step, self.published(), expected))
        now = chat.status()
        self.assertEqual((now["busy"], now["activity"]), expected, step)

    def assert_repeat_over(self, chat, step):
        """not busy, not speaking, in both views"""
        self.assertTrue(until(lambda: not chat.status()["busy"]), step + ": still busy")
        self.assertTrue(until(lambda: self.published() is not None and self.published()[0] is False), step + ": published still busy: %s" % (self.published(),))
        self.assertNotEqual(chat.status()["activity"], "speaking", step)
        self.assertNotEqual(self.published()[1], "speaking", step)

    @mark.req("REQ-CHA-035", "REQ-CHA-036")
    def test_a_repeat_that_runs_when_an_answer_starts_and_ends_keeps_the_status_busy_and_speaking(self):
        """TC-CHA-037 (REQ-CHA-035, 036): repeat first, then an answer starts and ends while the repeat still plays: busy and speaking at every step; after the stop not.
        Example: the fake voice blocks on "One."; "hi" is asked and answered; the status stays (true, speaking) until stop() ends the repeat."""
        # Given a blocked repeat
        chat = self.chat()
        chat.speak_again(self.stored())
        self.assertTrue(self.voice.started.wait(WAIT), "the voice route was not called")
        self.assert_both(chat, (True, "speaking"), "repeat alone")
        # When an answer starts, and when it ends while the repeat plays
        chat.send("hi", author="anna")
        self.assertTrue(self.entered.wait(WAIT), "the model was not asked")
        # Then the status says busy and speaking at both steps
        self.assert_both(chat, (True, "speaking"), "answer running")
        self.release.set()
        self.assertTrue(until(lambda: not chat._running), "the answer did not end")
        self.assert_both(chat, (True, "speaking"), "answer ended, repeat plays")
        # When the repeat is stopped, the status is not busy and not speaking
        chat.stop()
        self.assertTrue(self.voice.stop_seen.wait(1), "the voice route was never told to stop")
        self.assert_repeat_over(chat, "after the stop")

    @mark.req("REQ-CHA-035", "REQ-CHA-036")
    def test_a_repeat_requested_while_an_answer_runs_is_busy_and_speaking_also_after_the_answer_ended(self):
        """TC-CHA-037 (REQ-CHA-035, 036): an answer runs, a repeat is requested, the answer ends first: busy and speaking at every step; after the stop not.
        Example: "hi" blocks in the model; speak again of "One. Two." is asked; the status is (true, speaking) before and after the answer, then (false, not speaking)."""
        # Given an answer that runs
        chat = self.chat()
        answer = self.stored()
        chat.send("hi", author="anna")
        self.assertTrue(self.entered.wait(WAIT), "the model was not asked")
        # When a repeat is requested
        chat.speak_again(answer)
        self.assertTrue(self.voice.started.wait(WAIT), "the voice route was not called")
        # Then the status says busy and speaking while the answer runs
        self.assert_both(chat, (True, "speaking"), "answer running, repeat plays")
        # When the answer ends while the repeat plays, still
        self.release.set()
        self.assertTrue(until(lambda: not chat._running), "the answer did not end")
        self.assert_both(chat, (True, "speaking"), "answer ended, repeat plays")
        # When the repeat ends by a stop, the status is not busy and not speaking
        chat.stop()
        self.assertTrue(self.voice.stop_seen.wait(1), "the voice route was never told to stop")
        self.assert_repeat_over(chat, "after the stop")


if __name__ == "__main__":
    unittest.main()
