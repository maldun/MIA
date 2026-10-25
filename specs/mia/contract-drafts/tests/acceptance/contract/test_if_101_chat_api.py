"""IF-101 chat, expression, audio and REST API: the contract suite runs against the mock (stage 1) and the real provider
(stage 2, skipped until N-2 is integrated). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_101_chat_api.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ApiError                                 # noqa: E402
from if_101_chat_api import ChatApiMock                     # noqa: E402

IF = "IF-101"


def make(**options):
    return lambda kind: ChatApiMock(**options) if kind == "mock" else subject_for(IF, kind)


def error_of(call):
    try:
        call()
    except ApiError as err:
        return err
    raise AssertionError("no ApiError raised")


def names(events):
    return [e["event"] for e in events]


@contract
class ChatApiContract(unittest.TestCase):
    @mark.req("IF-101", "REQ-BE-008")
    @each_provider(IF)
    def test_login(self, api):
        """TC-IF-101-01: the right password opens a session, a wrong one is 401 bad_credentials."""
        self.assertTrue(api.login("anna", "pw-anna"))
        err = error_of(lambda: api.login("anna", "wrong"))
        self.assertEqual((err.status, err.code), (401, "bad_credentials"))

    @mark.req("IF-101", "REQ-BE-009")
    @each_provider(IF)
    def test_the_sixth_failed_login_in_a_minute_is_throttled(self, api):
        """TC-IF-101-02 golden 2: five failures, then 429 even with the right password; after 61 s the right password works."""
        for _ in range(5):
            self.assertEqual(error_of(lambda: api.login("anna", "wrong")).status, 401)
        err = error_of(lambda: api.login("anna", "pw-anna"))
        self.assertEqual((err.status, err.code), (429, "throttled"))
        self.assertTrue(api.login("ben", "pw-ben"))                  # another account is not affected
        api.advance_time(61)
        self.assertTrue(api.login("anna", "pw-anna"))

    @mark.req("IF-101", "REQ-BE-008", "NFR-6")
    @each_provider(IF)
    def test_no_session_no_access(self, api):
        """TC-IF-101-03: send, stop, history and connect without a session are 401 unauthenticated and queue nothing."""
        for call in (lambda: api.send("made-up", "hi"), lambda: api.stop("made-up"), lambda: api.history("made-up"), lambda: api.connect("made-up")):
            err = error_of(call)
            self.assertEqual((err.status, err.code), (401, "unauthenticated"))

    @mark.req("IF-101", "REQ-BE-001", "REQ-FE-001")
    @each_provider(IF, make(answers=[{"sentences": ["Hello Anna.", "How are you?"], "emotion": "happy"}]))
    def test_an_answer_streams_to_every_connected_user(self, api):
        """TC-IF-101-04 golden 1: ben's connection sees anna's message with its sender, then start, growing deltas, one audio chunk per sentence, done."""
        anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.connect(anna)
        api.connect(ben)
        self.assertEqual(api.events(ben)[0]["event"], "chat_status")
        ack = api.send(anna, "hi")
        api.settle()
        events = api.events(ben)
        self.assertEqual(names(events)[0], "chat_message")
        self.assertEqual((events[0]["payload"]["sender"], events[0]["payload"]["text"]), ("anna", "hi"))
        order = [n for n in names(events) if n in ("chat_start", "chat_delta", "chat_done")]
        self.assertEqual(order, ["chat_start", "chat_delta", "chat_delta", "chat_done"])
        deltas = [e["payload"]["text"] for e in events if e["event"] == "chat_delta"]
        self.assertTrue(deltas[1].startswith(deltas[0]) and len(deltas[1]) > len(deltas[0]))
        done = [e["payload"] for e in events if e["event"] == "chat_done"][0]
        self.assertEqual((done["text"], done["status"], done["emotion"]), (deltas[-1], "done", "happy"))
        chunks = [e["payload"] for e in events if e["event"] == "audio_chunk"]
        self.assertEqual([c["index"] for c in chunks], [0, 1])
        self.assertEqual([c["sentence"] for c in chunks], ["Hello Anna.", "How are you?"])
        self.assertIn({"name": "happy"}, [e["payload"] for e in events if e["event"] == "expression"])
        self.assertEqual(ack["position"], 1)

    @mark.req("IF-101", "REQ-BE-003", "REQ-FE-002")
    @each_provider(IF, make(queue_limit=3))
    def test_waiting_messages_have_positions_and_the_queue_has_a_limit(self, api):
        """TC-IF-101-05 golden 3: positions 1, 2, 3; a fourth message is 503 queue_full and queues nothing; after settle the queue is empty."""
        s = api.login("anna", "pw-anna")
        self.assertEqual([api.send(s, "m%d" % i)["position"] for i in (1, 2, 3)], [1, 2, 3])
        err = error_of(lambda: api.send(s, "m4"))
        self.assertEqual((err.status, err.code), (503, "queue_full"))
        api.settle()
        self.assertEqual(api.send(s, "m5")["position"], 1)
        self.assertEqual([m["text"] for m in api.history(s, 50) if m["role"] == "user"], ["m1", "m2", "m3", "m5"])

    @mark.req("IF-101", "REQ-BE-004")
    @each_provider(IF, make(answers=[["One.", "Two.", "Three."]]))
    def test_stop_ends_the_answer_without_a_delta(self, api):
        """TC-IF-101-06 golden 3: stop right after send gives chat_done with status stopped and no chat_delta."""
        s = api.login("anna", "pw-anna")
        api.connect(s)
        api.events(s)
        api.send(s, "tell me a story")
        self.assertEqual(api.stop(s), {"stopped": True})
        api.settle()
        events = api.events(s)
        self.assertNotIn("chat_delta", names(events))
        done = [e["payload"] for e in events if e["event"] == "chat_done"][0]
        self.assertEqual((done["status"], done["text"]), ("stopped", ""))
        self.assertEqual(api.stop(s), {"stopped": False})            # nothing left to stop

    @mark.req("IF-101", "REQ-BE-001")
    @each_provider(IF)
    def test_empty_text_is_refused(self, api):
        """TC-IF-101-07: empty or blank text is 422 empty_text and nothing is queued."""
        s = api.login("anna", "pw-anna")
        for text in ("", "   "):
            err = error_of(lambda: api.send(s, text))
            self.assertEqual((err.status, err.code), (422, "empty_text"))
        self.assertEqual(api.history(s, 50), [])

    @mark.req("IF-101", "REQ-FE-003", "REQ-BE-002")
    @each_provider(IF, make(answers=[["Hi there."]]))
    def test_history_after_reload_is_shared_and_attributed(self, api):
        """TC-IF-101-08: a user who connects later gets the same ordered history with senders, the assistant's messages from MIA."""
        anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.send(anna, "hi")
        api.settle()
        api.connect(ben)
        history = api.history(ben, 50)
        self.assertEqual([(m["role"], m["sender"], m["text"]) for m in history], [("user", "anna", "hi"), ("assistant", "MIA", "Hi there.")])
        self.assertEqual(len(api.history(ben, 1)), 1)


if __name__ == "__main__":
    unittest.main()
