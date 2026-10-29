"""TC-CHA-011c and REQ-CHA-011. Run with: python tests/test_chat_memory.py"""

import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
from task_helper import registry_of                       # noqa: E402
from chat_log import ChatLog                              # noqa: E402
from chat_service import ChatService                      # noqa: E402
from moods import MoodTracker                             # noqa: E402
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402


class MemoryWiringTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.remembered = []
        self.events = []
        self.fail_exchange = False
        self.storage = Storage(FileBackend(os.path.join(self.dir, "db")))
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))

        def exchange(text, on_delta, on_emotion, should_stop):
            if self.fail_exchange:
                raise RuntimeError("no_model")
            return "One. Two."

        def remember(account, message_id, text):
            self.remembered.append((account, message_id, text))
            return []

        self.chat = ChatService(lambda event, payload: self.events.append((event, payload)), self.log, MoodTracker(os.path.join(ROOT, "moods.json")), exchange,
                                queue_size=5, user_limit=2, spawn=lambda target: target(), votes=self.storage,
                                tasks=registry_of(lookup=lambda question, on_delta, on_emotion, should_stop: "An answer."), remember=remember)

    @mark.req('REQ-CHA-011')
    def test_a_plain_chat_turn_hands_the_user_message_to_the_memory(self):
        ack = self.chat.send("I like tea", author="anna")
        self.assertEqual(self.remembered, [("anna", ack["message"]["id"], "I like tea")])

    @mark.req('REQ-CHA-011')
    def test_a_command_a_lookup_and_a_regenerated_answer_are_not_remembered(self):
        self.chat.send("/tasks", author="anna")
        self.chat.send("/lookup how tall is the Eiffel Tower", author="anna")
        self.assertEqual(self.remembered, [])
        self.chat.send("hello", author="anna")
        self.assertEqual(len(self.remembered), 1)
        self.chat.regenerate("anna", self.log.last("assistant")["id"])
        self.assertEqual(len(self.remembered), 1)

    @mark.req('REQ-CHA-011')
    def test_a_failed_turn_is_not_remembered(self):
        self.fail_exchange = True
        self.chat.send("I like tea", author="anna")
        self.assertEqual(self.remembered, [])

    @mark.req('REQ-CHA-011')
    def test_a_memory_that_fails_does_not_break_the_answer(self):
        def broken(account, message_id, text):
            raise RuntimeError("memory down")
        self.chat._remember = broken
        self.chat.send("I like tea", author="anna")
        done = [p for e, p in self.events if e == "chat_done"]
        self.assertEqual((len(done), done[0]["status"]), (1, "done"))

    @mark.req('REQ-CHA-011')
    def test_without_an_account_the_page_is_the_account(self):
        self.chat.send("I like tea")
        self.assertEqual(self.remembered[0][0], "page")


if __name__ == '__main__':
    unittest.main()
