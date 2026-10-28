"""TC-WFM-019 (REQ-WFM-019), IF-101 (A-20): /review question is a task of the chat; while it waits for an answer, the next message of the same account is the answer and is not queued behind it;
a message of another account is queued as usual; stop and a timeout end the wait with no answer. Run in the image: bash tools/run_in_image.sh tests/test_chat_review.py"""
import importlib
import os
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

MOODS = os.path.join(REPO, "moods.json")


def wait_for(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


class ReviewTask(unittest.TestCase):
    def setUp(self):
        self.chat_log = importlib.import_module("MIA.chat_log")
        self.service_module = importlib.import_module("MIA.chat_service")
        self.moods = importlib.import_module("MIA.moods")
        self.tmp = tempfile.TemporaryDirectory()
        self.log = self.chat_log.ChatLog(os.path.join(self.tmp.name, "log.jsonl"))
        self.events, self.calls, self.answers = [], [], []
        self.release = threading.Event()

    def tearDown(self):
        self.release.set()
        self.tmp.cleanup()

    def make(self, review=True, ask_timeout=30):
        def exchange(text, on_delta, on_emotion, should_stop):
            return "chat"

        def run_review(text, on_delta, on_emotion, should_stop, ask):
            self.calls.append(text)
            self.answers.append(ask("Shall I go on?"))
            self.answers.append(ask("Really?"))
            self.release.wait(5)
            return "the report"
        return self.service_module.ChatService(lambda event, payload: self.events.append((event, payload)), self.log, self.moods.MoodTracker(MOODS), exchange,
                                               model_info=lambda: ("m", "light"), run_lookup=lambda q, d, e, s: "found", run_review=run_review if review else None, review_timeout=ask_timeout, user_limit=2, queue_size=3)

    def idle(self, service):
        return wait_for(lambda: not service.status()["busy"])

    def asked(self, count):
        return wait_for(lambda: len([r for r in self.log.history(limit=50)[0] if r["role"] == "assistant" and r["text"] in ("Shall I go on?", "Really?")]) >= count)

    def test_the_command_runs_the_review_with_the_argument_and_the_report_is_the_answer(self):
        service = self.make()
        self.assertTrue(service.send("/review how to schedule? until 2024-06-30", author="anna")["ok"])
        self.assertTrue(self.asked(1))
        service.send("yes", author="anna")
        self.assertTrue(self.asked(2))
        service.send("no", author="anna")
        self.release.set()
        self.assertTrue(self.idle(service))
        self.assertEqual(self.calls, ["how to schedule? until 2024-06-30"])
        answer = self.log.history(limit=20)[0][-1]
        self.assertEqual((answer["role"], answer["text"], answer["task"]), ("assistant", "the report", "review"))

    def test_the_next_message_of_the_same_account_is_the_answer_and_is_not_queued(self):
        service = self.make()
        service.send("/review how to schedule?", author="anna")
        self.assertTrue(self.asked(1))
        ack = service.send("yes please", author="anna")
        self.assertEqual((ack["ok"], ack["queued"]), (True, False))
        self.assertTrue(wait_for(lambda: self.answers == ["yes please"] or len(self.answers) > 1))
        self.assertEqual(self.answers[0], "yes please")
        texts = [r["text"] for r in self.log.history(limit=20)[0] if r["role"] == "user"]
        self.assertEqual(texts, ["/review how to schedule?", "yes please"])
        self.release.set()

    def test_a_message_of_another_account_waits_in_the_queue_and_is_no_answer(self):
        service = self.make()
        service.send("/review how to schedule?", author="anna")
        self.assertTrue(self.asked(1))
        ack = service.send("hello from ben", author="ben")
        self.assertEqual((ack["ok"], ack["queued"]), (True, True))
        time.sleep(0.2)
        self.assertEqual(self.answers, [])
        service.send("yes", author="anna")
        self.assertTrue(self.asked(2))
        service.stop()
        self.release.set()

    def test_a_command_while_waiting_is_no_answer(self):
        service = self.make()
        service.send("/review how to schedule?", author="anna")
        self.assertTrue(self.asked(1))
        ack = service.send("/lookup something", author="anna")
        self.assertTrue(ack["queued"])
        time.sleep(0.2)
        self.assertEqual(self.answers, [])
        service.stop()
        self.release.set()

    def test_stop_ends_the_wait_with_no_answer(self):
        service = self.make()
        service.send("/review how to schedule?", author="anna")
        self.assertTrue(self.asked(1))
        self.assertTrue(service.stop())
        self.assertTrue(wait_for(lambda: len(self.answers) >= 1))
        self.assertIsNone(self.answers[0])
        self.release.set()

    def test_no_reply_in_time_is_no_answer(self):
        service = self.make(ask_timeout=0.3)
        service.send("/review how to schedule?", author="anna")
        self.assertTrue(wait_for(lambda: len(self.answers) >= 1))
        self.assertIsNone(self.answers[0])
        self.release.set()

    def test_the_status_says_waiting_while_a_question_is_open(self):
        service = self.make()
        service.send("/review how to schedule?", author="anna")
        self.assertTrue(self.asked(1))
        self.assertTrue(wait_for(lambda: "waiting" in str(service.status())))
        service.send("yes", author="anna")
        self.release.set()

    def test_bare_and_unavailable_review_are_explained(self):
        service = self.make()
        ack = service.send("/review")
        self.assertFalse(ack["ok"])
        self.assertIn("/review", ack["error"])
        self.assertIn("question", ack["error"])
        self.assertFalse(self.make(review=False).send("/review a question")["ok"])
        self.assertTrue(any(c["command"].startswith("/review") for c in self.service_module.COMMANDS))


if __name__ == "__main__":
    unittest.main()
