"""TC-CHA-019 (REQ-CHA-019): tasks and memos are recited from their records word for word, on request and at their due time; the model is never asked.
Run with: python tests/test_chat_recitation.py"""

import os
import shutil
import sys
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests', 'helpers'))

from markers import mark
from chat_log import ChatLog
from chat_service import ChatService, ChatError
from moods import MoodTracker
from storage import Storage
from storage_files import FileBackend


ODD = ["line one\nline two", "  leading and trailing blanks  ", "tab\there", "a text with \" and ' and ` in it", "Zoë – ✓ ß 日本語",
       "<b>not html</b> *not markdown* _not either_", "ends with a newline\n", "Call Zoë at 9:00 – bring \"the\" notes"]
START = 1767571200          # 2026-01-05 00:00 UTC
CREATED = "2026-01-05T00:00:00Z"


def iso(seconds):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(seconds))


def odd(i):
    return "%d: %s" % (i, ODD[i % 8])


class RecitationTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.now = START
        self.storage = Storage(FileBackend(os.path.join(self.dir, "db")))
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))

        def exchange(text, on_delta, on_emotion, should_stop):
             raise AssertionError("the model must not be asked")

        self.chat = ChatService(lambda event, payload: None, self.log, MoodTracker(os.path.join(ROOT, "moods.json")), exchange, queue_size=5, user_limit=2,
                                spawn=lambda target: target(), votes=self.storage, wall_clock=lambda: self.now)

    def put(self, kind, i, **fields):
        self.storage.put(kind, "%03d" % i, dict({"text": odd(i), "created": CREATED}, **fields), "anna")

    def posted(self):
        """the texts of the assistant messages in the chat log, oldest first"""
        return [m["text"] for m in self.log.history(limit=200)[0] if m["role"] == "assistant"]

    @mark.req('REQ-CHA-019')
    def test_fifty_items_are_recited_word_for_word_on_request(self):
        for i in range(25):
            self.put('tasks', i)
        for i in range(25, 50):
            self.put('memos', i)
        for i in range(25):
            self.assertEqual(self.chat.recite('tasks', '%03d' % i)['text'], odd(i))
        for i in range(25, 50):
            self.assertEqual(self.chat.recite('memos', '%03d' % i)['text'], odd(i))
        self.assertEqual(self.chat.recite_all('tasks'), 25)
        self.assertEqual(self.chat.recite_all('memos'), 25)
        self.assertEqual(self.posted(), [odd(i) for i in range(50)])

    @mark.req('REQ-CHA-019')
    def test_due_tasks_are_recited_word_for_word_at_their_due_time(self):
        for i in range(50):
            self.put('tasks', i, due=iso(START + 3600))
        self.assertEqual(self.chat.recite_due(), 0)
        self.assertEqual(self.posted(), [])
        self.now += 3600
        self.assertEqual(self.chat.recite_due(), 50)
        self.assertEqual(self.posted(), [odd(i) for i in range(50)])
        self.assertEqual(self.chat.recite_due(), 0)

    @mark.req('REQ-CHA-019')
    def test_a_task_without_due_time_is_not_recited_by_the_clock(self):
        self.put('tasks', 1)
        self.put('memos', 2, due=iso(START - 60))
        self.assertEqual(self.chat.recite_due(), 0)
        self.assertEqual(self.posted(), [])

    @mark.req('REQ-CHA-019')
    def test_the_commands_recite_on_request(self):
        for i in range(3):
            self.put('tasks', i)
        for i in range(3, 5):
            self.put('memos', i)
        self.chat.send('/tasks')
        self.assertEqual(self.posted(), [odd(i) for i in range(3)])
        self.chat.send('/memos')
        self.assertEqual(self.posted(), [odd(i) for i in range(5)])

    @mark.req('REQ-CHA-019')
    def test_unknown_items_are_not_found(self):
        with self.assertRaises(ChatError) as caught:
            self.chat.recite('tasks', 'nope')
        self.assertEqual(caught.exception.code, 'not_found')
        with self.assertRaises(ChatError) as caught:
            self.chat.recite('dreams', '001')
        self.assertEqual(caught.exception.code, 'not_found')

if __name__ == '__main__':
    unittest.main()
