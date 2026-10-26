"""IF-201 chat turn service (API and accounts to Chat agent): the contract suite runs against the mock (stage 1) and the real Chat agent
(stage 2, skipped until N-2.2 is integrated). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_201_chat_turn.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ServiceError                             # noqa: E402
from if_201_chat_turn import ChatTurnMock                   # noqa: E402

IF = "IF-201"


def make(**options):
    return lambda kind: ChatTurnMock(**options) if kind == "mock" else subject_for(IF, kind)


def code_of(call):
    try:
        call()
    except ServiceError as err:
        return err.code
    raise AssertionError("no ServiceError raised")


@contract
class ChatTurnContract(unittest.TestCase):
    @mark.req("IF-201", "REQ-BE-001")
    @each_provider(IF, make(answers=[{"sentences": ["Hello Anna.", "How are you?"], "emotion": "happy"}]))
    def test_an_answer_is_delivered_as_events(self, chat):
        """TC-IF-201-01 golden 1: message with sender, start, growing deltas, one audio chunk per sentence, done."""
        seen = []
        chat.subscribe(seen.append)
        self.assertEqual(chat.send("anna", "hi"), {"id": chat.history()[0]["id"], "position": 1})
        chat.settle()
        events = [e["event"] for e in seen]
        self.assertEqual(events[0], "chat_message")
        self.assertEqual(seen[0]["payload"]["sender"], "anna")
        self.assertEqual([e for e in events if e in ("chat_start", "chat_done")], ["chat_start", "chat_done"])
        self.assertEqual(events.count("chat_delta"), 2)
        self.assertEqual([e["payload"]["index"] for e in seen if e["event"] == "audio_chunk"], [0, 1])
        self.assertEqual(chat.history()[-1]["sender"], "MIA")

    @mark.req("IF-201", "REQ-BE-001")
    @each_provider(IF)
    def test_blank_text_is_refused(self, chat):
        """TC-IF-201-02 golden 2: blank text is empty_text and nothing is queued."""
        for text in ("", "  \n"):
            self.assertEqual(code_of(lambda: chat.send("anna", text)), "empty_text")
        self.assertEqual(chat.status()["queue"], 0)

    @mark.req("IF-201", "REQ-BE-003")
    @each_provider(IF, make(queue_limit=2))
    def test_a_full_queue_refuses_without_harm(self, chat):
        """TC-IF-201-03 golden 2: positions 1, 2; the third message is queue_full; the queued ones are still answered."""
        self.assertEqual([chat.send("anna", "a")["position"], chat.send("ben", "b")["position"]], [1, 2])
        self.assertEqual(code_of(lambda: chat.send("anna", "c")), "queue_full")
        self.assertEqual(chat.status()["queue"], 2)
        chat.settle()
        self.assertEqual(sum(1 for m in chat.history() if m["role"] == "assistant"), 2)

    @mark.req("IF-201", "REQ-BE-004")
    @each_provider(IF, make(answers=[["One.", "Two."]]))
    def test_stop(self, chat):
        """TC-IF-201-04 golden 3: stop right after send ends the answer without a delta; with nothing running it is stopped false."""
        seen = []
        chat.subscribe(seen.append)
        chat.send("anna", "story")
        self.assertEqual(chat.stop(), {"stopped": True})
        chat.settle()
        self.assertNotIn("chat_delta", [e["event"] for e in seen])
        self.assertEqual([e["payload"]["status"] for e in seen if e["event"] == "chat_done"], ["stopped"])
        self.assertEqual(chat.stop(), {"stopped": False})


if __name__ == "__main__":
    unittest.main()
