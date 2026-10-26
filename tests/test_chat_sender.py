"""TC-CHA-021 and REQ-CHA-008. Run with: python tests/test_chat_sender.py"""

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
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402


class SenderTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.asked = []
        self.storage = Storage(FileBackend(os.path.join(self.dir, "db")))
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))

        def exchange(text, on_delta, on_emotion, should_stop):
            self.asked.append(text)
            return "One. Two."

        self.chat = ChatService(lambda event, payload: None, self.log, MoodTracker(os.path.join(ROOT, "moods.json")), exchange,
                                queue_size=5, user_limit=2, spawn=lambda target: target(), votes=self.storage)

    @mark.req('REQ-CHA-008')
    def test_a_message_of_an_account_reaches_the_model_with_the_name(self):
        self.chat.send("hi MIA", author="anna")
        self.assertEqual(self.asked, ["[anna] hi MIA"])
        stored = [r["text"] for r in self.log.history(limit=10)[0] if r["role"] == "user"]
        self.assertEqual(stored, ["hi MIA"])

    @mark.req('REQ-CHA-008')
    def test_a_message_without_an_account_reaches_the_model_as_it_is(self):
        self.chat.send("hi MIA")
        self.assertEqual(self.asked, ["hi MIA"])

    @mark.req('REQ-CHA-008')
    def test_a_regenerated_answer_names_the_asker_not_the_one_who_clicked(self):
        self.chat.send("hi MIA", author="anna")
        self.chat.regenerate("ben", self.log.last("assistant")["id"])
        self.assertEqual(self.asked, ["[anna] hi MIA", "[anna] hi MIA"])


if __name__ == '__main__':
    unittest.main()
