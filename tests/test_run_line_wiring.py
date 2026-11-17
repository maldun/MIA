"""
Unit tests of the wiring of the live status line (G-V3.CHAT T-09, A-158; REQ-CHA-068 to 071): a task through ChatService.send gives the line `working` for a skill without phases,
the phases of a skill that declares them, `waiting for your answer` and the phase again around a question, and the clearing before the end message. Run with: python tests/test_run_line_wiring.py
"""
import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                       # noqa: E402
from test_chat_verify_fixes import chat_with, mia   # noqa: E402


def recording(chat):
    """what the page would see of the run: the status lines and the messages in order ('line' texts, 'message' kinds)"""
    seen = []
    original = chat._emit

    def emit(event, payload):
        if event == "chat_run_status":
            seen.append(("line", payload["text"]))
        elif event == "chat_message" or event == "chat_start":
            seen.append(("message", payload.get("kind") or event))
        elif event == "chat_done":
            seen.append(("done", payload.get("status")))
        original(event, payload)
    chat._emit = emit
    return seen


class RunLineWiring(unittest.TestCase):
    @mark.req("REQ-CHA-068", "REQ-CHA-069")
    def test_a_skill_without_phases_shows_working_and_the_line_is_cleared_before_the_end(self):
        """T-09: a lookup-like run gives `working` at its start and the clearing before its end message.
        Example: lines working, None; the clearing comes before chat_start of the summary."""
        # Given: a skill without declared phases
        def lookup(argument, on_delta, on_emotion, should_stop, monitor):
            return "result"
        chat, _, _ = chat_with(self, lookup, declared=())
        seen = recording(chat)
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: the line `working` comes first, the clearing before the end message
        self.assertEqual([x for x in seen if x[0] == "line"], [("line", "working"), ("line", None)])
        self.assertLess(seen.index(("line", None)), seen.index(("message", "chat_start")))

    @mark.req("REQ-CHA-068", "REQ-CHA-070")
    def test_the_phases_and_a_question_give_their_lines_in_order(self):
        """T-09: collect, a question (waiting line), the answer (the phase line again), rank, the clearing.
        Example: lines collect, waiting for your answer, collect, rank, None."""
        # Given: a skill with two declared phases that asks one question after the first
        def asks(argument, on_delta, on_emotion, should_stop, ask, monitor):
            monitor.update(phase="collect")
            answer = ask("Which topic?")
            monitor.update(phase="rank")
            return "Done " + answer
        chat, _, _ = chat_with(self, asks, needs=("ask", "monitor"), spawn=lambda target: threading.Thread(target=target, daemon=True).start())
        seen = recording(chat)
        # When: the user starts it and answers
        chat.send("/go x", sender="anna", author="anna")
        for _ in range(200):
            if ("line", "waiting for your answer") in seen:
                break
            time.sleep(0.05)
        chat.send("quantum", sender="anna", author="anna")
        for _ in range(200):
            if ("line", None) in seen:
                break
            time.sleep(0.05)
        # Then: the lines are in the order of the run
        self.assertEqual([x[1] for x in seen if x[0] == "line"], ["collect", "waiting for your answer", "collect", "rank", None])
        # And: the line is in no record of the chat
        self.assertTrue(all("collect" not in r["text"] for r in mia(chat)))

    @mark.req("REQ-CHA-069")
    def test_a_failing_run_clears_the_line_too(self):
        """T-09: a skill that raises after its first phase still ends with the clearing.
        Example: lines collect, None."""
        # Given: a skill that raises after its first phase
        def raises(argument, on_delta, on_emotion, should_stop, monitor):
            monitor.update(phase="collect")
            raise RuntimeError("boom")
        chat, _, _ = chat_with(self, raises)
        seen = recording(chat)
        # When: the user starts it
        chat.send("/go x", sender="anna", author="anna")
        # Then: the line is cleared at the end
        self.assertEqual([x[1] for x in seen if x[0] == "line"], ["collect", None])


if __name__ == "__main__":
    unittest.main()
