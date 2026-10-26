"""TC-CHA-006 (REQ-CHA-006): the Chat agent regenerates the last answer or speaks any answer again; two requests give a new answer and a new audio stream.
Run with: python tests/test_chat_regenerate_speak.py"""
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
from chat_service import ChatError, ChatService           # noqa: E402
from moods import MoodTracker                             # noqa: E402
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402

FIRST, SECOND = "First try. It has two sentences.", "Second try. And a third sentence. Here."


class RegenerateSpeakTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.events = []
        self.answers = [FIRST, SECOND]
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))
        self.chat = ChatService(lambda event, payload: self.events.append((event, payload)), self.log, MoodTracker(os.path.join(ROOT, "moods.json")),
                                lambda text, on_delta, on_emotion, should_stop: self.answers.pop(0), queue_size=5, user_limit=2, spawn=lambda target: target(),
                                votes=Storage(FileBackend(os.path.join(self.dir, "db"))))

    def sentences(self, message_id):
        """the sentences of the audio_chunk events of one answer, in the order they were sent"""
        return [payload["sentence"] for event, payload in self.events if event == "audio_chunk" and payload["id"] == message_id]

    @mark.req("REQ-CHA-006")
    def test_two_requests_give_a_new_answer_and_a_new_audio_stream(self):
        self.chat.send("hi", author="anna")
        first = self.log.last("assistant")
        self.assertEqual(self.chat.regenerate("anna", first["id"])["position"], 1)
        second = self.log.last("assistant")
        self.assertNotEqual(second["id"], first["id"])
        self.assertEqual((first["text"], second["text"]), (FIRST, SECOND))
        self.events.clear()
        self.assertEqual(self.chat.speak_again(first["id"]), {"sentences": 2})
        self.assertEqual(self.chat.speak_again(second["id"]), {"sentences": 3})
        self.assertEqual(self.sentences(first["id"]), ["First try.", "It has two sentences."])
        self.assertEqual(self.sentences(second["id"]), ["Second try.", "And a third sentence.", "Here."])

    @mark.req("REQ-CHA-006")
    def test_the_old_answer_stays_in_the_log_and_the_question_is_not_stored_again(self):
        self.chat.send("hi", author="anna")
        self.chat.regenerate("anna", self.log.last("assistant")["id"])
        messages = self.log.history(limit=50)[0]
        self.assertEqual([m["text"] for m in messages if m["role"] == "assistant"], [FIRST, SECOND])
        self.assertEqual([m["text"] for m in messages if m["role"] == "user"], ["hi"])

    @mark.req("REQ-CHA-006")
    def test_only_the_last_answer_can_be_regenerated(self):
        self.chat.send("hi", author="anna")
        first = self.log.last("assistant")
        self.chat.regenerate("anna", first["id"])
        for message_id, code in ((first["id"], "not_the_last_answer"), ("nope", "not_found")):
            with self.assertRaises(ChatError) as caught:
                self.chat.regenerate("anna", message_id)
            self.assertEqual(caught.exception.code, code)


if __name__ == "__main__":
    unittest.main()
