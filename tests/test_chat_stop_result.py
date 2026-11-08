"""Chat agent N-2.2 (A-132; verification report F3): the value of stop() (IF-201 edge: stop with no answer running is stopped false, also when it ended a spoken-again playback).
Real threads, a blocking fake model and a blocking fake voice (TR-VOICE-001). Run with: python tests/test_chat_stop_result.py"""
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


class StopResultTest(unittest.TestCase):
    @mark.req("REQ-CHA-032")
    def test_stop_returns_false_when_it_ended_only_a_repeat_and_true_when_it_stopped_an_answer(self):
        """IF-201 edge: stop() with no answer running is False, also when it ended a repeat; with a running answer it is True.
        Example: stop during a blocked repeat gives False and the repeat ends within 1 s; stop during a running answer gives True."""
        # Given a service on real threads, a voice that blocks and a model that waits for the stop
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        log = ChatLog(os.path.join(directory, "log.jsonl"))
        voice = FakeVoice(block=True)
        entered = threading.Event()

        def model(text, on_delta, on_emotion, should_stop):
            entered.set()
            while not should_stop():
                time.sleep(0.02)
            return "Answer."
        chat = ChatService(lambda event, payload: None, log, MoodTracker(os.path.join(ROOT, "moods.json")), model, queue_size=5, user_limit=2,
                           spawn=lambda target: threading.Thread(target=target, daemon=True).start(), speak=voice)
        self.addCleanup(chat.stop)
        # When a repeat is blocked and no answer runs, and stop is pressed
        chat.speak_again(log.append("assistant", "One. Two.")["id"])
        self.assertTrue(voice.started.wait(WAIT), "the voice route was not called")
        result = chat.stop()
        # Then the value is False and the repeat ends within 1 s
        self.assertIs(result, False)
        self.assertTrue(voice.stop_seen.wait(1), "the repeat did not end within 1 s of the stop")
        # When an answer runs and stop is pressed, the value is True
        end = time.monotonic() + WAIT
        while chat.status()["busy"] and time.monotonic() < end:
            time.sleep(0.02)
        chat.send("hi", author="anna")
        self.assertTrue(entered.wait(WAIT), "the model was not asked")
        self.assertIs(chat.stop(), True)


if __name__ == "__main__":
    unittest.main()
