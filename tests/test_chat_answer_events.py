"""Chat agent N-2.2: the events of one live answer (IF-101 v15, IF-201): the last chat_delta equals the text of chat_done even when deltas arrive faster
than the throttle (TC-IF-201-01), and one audio_chunk per sentence follows during the answer (REQ-VOI-001, A-130 step 4.1).
Run with: python tests/test_chat_answer_events.py"""
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


class AnswerEventsTest(unittest.TestCase):
    def run_answer(self, steps, final=None):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        events = []

        def exchange(text, on_delta, on_emotion, should_stop):
            for step in steps:
                on_delta(step)                    # faster than the throttle: the clock does not move
            return final if final is not None else steps[-1]

        chat = ChatService(lambda event, payload: events.append((event, payload)), ChatLog(os.path.join(folder, "log.jsonl")), MoodTracker(os.path.join(ROOT, "moods.json")),
                           exchange, queue_size=5, spawn=lambda target: target(), clock=lambda: 100.0)
        chat.send("hi", sender="anna", author="anna")
        return events

    @mark.req("REQ-CHA-001", "REQ-VOI-001")
    def test_the_last_delta_equals_the_text_of_chat_done(self):
        """Example: deltas "Hello Anna." and "Hello Anna. How are you?" arrive at once -> the page sees both, the last one equals chat_done"""
        events = self.run_answer(["Hello Anna.", "Hello Anna. How are you?"])
        deltas = [p["text"] for e, p in events if e == "chat_delta"]
        done = [p for e, p in events if e == "chat_done"][0]
        self.assertEqual(deltas, ["Hello Anna.", "Hello Anna. How are you?"])
        self.assertEqual(deltas[-1], done["text"])

    @mark.req("REQ-VOI-001")
    def test_one_audio_chunk_per_sentence_during_the_answer(self):
        """Example: "Hello Anna. How are you?" -> audio_chunk index 0 "Hello Anna.", index 1 "How are you?", after the last delta and before chat_done"""
        events = self.run_answer(["Hello Anna.", "Hello Anna. How are you?"])
        names = [e for e, _ in events]
        chunks = [p for e, p in events if e == "audio_chunk"]
        self.assertEqual([(c["index"], c["sentence"]) for c in chunks], [(0, "Hello Anna."), (1, "How are you?")])
        self.assertEqual(len({c["id"] for c in chunks}), 1)
        self.assertLess(max(i for i, n in enumerate(names) if n == "chat_delta"), min(i for i, n in enumerate(names) if n == "audio_chunk"))
        self.assertLess(max(i for i, n in enumerate(names) if n == "audio_chunk"), names.index("chat_done"))

    @mark.req("REQ-VOI-001")
    def test_no_audio_chunk_for_a_stopped_or_empty_answer(self):
        events = self.run_answer([""], final="")
        self.assertEqual([e for e, _ in events if e == "audio_chunk"], [])


if __name__ == "__main__":
    unittest.main()
