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

    @mark.req("REQ-CHA-070")
    def test_a_question_that_times_out_gives_the_phase_line_back(self):
        """F-03 of the A-158 verification: when nobody answers, the line `waiting for your answer` does not stay while the skill goes on.
        Example: collect, waiting for your answer, collect (the timeout), None."""
        # Given: a skill that asks one question after its first phase, on a service whose question times out at once
        def asks(argument, on_delta, on_emotion, should_stop, ask, monitor):
            monitor.update(phase="collect")
            chat._review_timeout = 0
            ask("Which topic?")
            return "result"
        chat, _, _ = chat_with(self, asks, needs=("ask", "monitor"))
        seen = recording(chat)
        # When: the user starts it and nobody answers
        chat.send("/go x", sender="anna", author="anna")
        # Then: the phase line comes back after the waiting line
        self.assertEqual([x[1] for x in seen if x[0] == "line"], ["collect", "waiting for your answer", "collect", None])

    @mark.req("REQ-CHA-069", "REQ-CHA-070")
    def test_a_stop_while_a_question_waits_clears_the_line_before_the_end_message(self):
        """F-05 (d): the user stops a run that waits for an answer; the line is cleared before the end message.
        Example: collect, waiting for your answer, ..., None, then the stopped message."""
        # Given: a skill that waits for an answer
        def asks(argument, on_delta, on_emotion, should_stop, ask, monitor):
            monitor.update(phase="collect")
            ask("Which topic?")
            return "result"
        chat, _, _ = chat_with(self, asks, needs=("ask", "monitor"), spawn=lambda target: threading.Thread(target=target, daemon=True).start())
        seen = recording(chat)
        chat.send("/go x", sender="anna", author="anna")
        for _ in range(200):
            if ("line", "waiting for your answer") in seen:
                break
            time.sleep(0.05)
        # When: the user stops the run
        chat.stop()
        for _ in range(200):
            if ("done", "stopped") in seen:
                break
            time.sleep(0.05)
        # Then: the clearing comes before the end message and no line follows it
        cleared = seen.index(("line", None))
        self.assertLess(cleared, seen.index(("message", "chat_start")))
        self.assertEqual([x for x in seen[cleared + 1:] if x[0] == "line"], [])

    @mark.req("REQ-CHA-068", "REQ-CHA-070")
    def test_a_failing_emit_of_the_line_does_not_lose_the_answer_or_the_end(self):
        """F-05 (a): when the event of the line cannot be sent, the question is still answered and the run still ends with its summary.
        Example: chat_run_status raises; the answer `quantum` reaches the skill and the done message is in the chat."""
        # Given: a service whose event for the line raises
        def asks(argument, on_delta, on_emotion, should_stop, ask, monitor):
            monitor.update(phase="collect")
            return "Done " + str(ask("Which topic?"))
        chat, _, _ = chat_with(self, asks, needs=("ask", "monitor"), spawn=lambda target: threading.Thread(target=target, daemon=True).start())
        original = chat._emit

        def emit(event, payload):
            if event == "chat_run_status":
                raise RuntimeError("socket gone")
            original(event, payload)
        chat._emit = emit
        # When: the user starts it and answers the question
        chat.send("/go x", sender="anna", author="anna")
        for _ in range(200):
            if any(r["text"] == "Which topic?" for r in mia(chat)):
                break
            time.sleep(0.05)
        chat.send("quantum", sender="anna", author="anna")
        for _ in range(200):
            if any(r.get("kind") == "done" for r in mia(chat)):
                break
            time.sleep(0.05)
        # Then: the run ended with its summary and the history holds the question and the answer
        self.assertTrue(any(r.get("kind") == "done" for r in mia(chat)))
        self.assertEqual([m["text"] for m in chat.model_history()][:2], ["Which topic?", "quantum"])

    @mark.req("REQ-CHA-069", "REQ-CHA-070")
    def test_a_question_after_the_end_of_the_run_gives_no_line(self):
        """F-05 (c): a question that arrives after the run ended leaves no stale `waiting for your answer`.
        Example: collect, done, then a question of the same run: no line after the clearing."""
        # Given: a run that has ended
        chat, _, _ = chat_with(self, lambda *a, **k: "result")
        seen = recording(chat)
        chat.skill_turn("anna", "r1", "phase", "collect")
        chat.skill_turn("anna", "r1", "done", "a result")
        # When: a late question of the same run comes in
        chat.skill_turn("anna", "r1", "question", "Still there?")
        # Then: the last line event is the clearing
        self.assertEqual([x[1] for x in seen if x[0] == "line"][-1], None)


if __name__ == "__main__":
    unittest.main()
