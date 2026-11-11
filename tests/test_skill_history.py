"""
Unit tests of the history for the chat model (G-V3.CHAT T-03; REQ-CHA-046, 059): ChatService.model_history() holds, per skill run, its questions, the answers that follow them, the
last status message and the end message, and nothing else of the chat; Communicator.chat() puts these messages before the new user message and does not keep them in its own memory.
Run with: python tests/test_skill_history.py
"""
import importlib
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import checkout_copy  # noqa: E402  (MIA from a temporary copy: nothing is written into the checkout, D-169)
_LINK_DIR = checkout_copy.use()
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark  # noqa: E402


def service(test):
    chat_log = importlib.import_module("MIA.chat_log")
    chat_service = importlib.import_module("MIA.chat_service")
    moods = importlib.import_module("MIA.moods")
    folder = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, folder, True)
    return chat_service.ChatService(lambda event, payload: None, chat_log.ChatLog(os.path.join(folder, "log.jsonl")), moods.MoodTracker(os.path.join(ROOT, "moods.json")),
                                    lambda *args: "", spawn=lambda target: target(), clock=lambda: 100.0, declared_phases=lambda run: ("a", "b"))


class ModelHistory(unittest.TestCase):
    @mark.req("REQ-CHA-046", "REQ-CHA-059")
    def test_only_the_messages_of_skill_runs_that_the_model_needs(self):
        """an ordinary chat, a user message that is no answer, system notes and the status messages but the last are not in it.
        Example: Q1, answer, status a, status b, done -> Q1, answer, status b, done."""
        # Given: an ordinary exchange, then a run with a question, its answer, two status messages and a summary, then a user message that is no answer
        chat = service(self)
        chat.log.append("user", "hello", sender="anna")
        chat.log.append("assistant", "Hi.")
        chat.note("a system note")
        chat.skill_turn("anna", "r1", "question", "Which topic?")
        chat.log.append("user", "canary", sender="anna")
        chat.skill_turn("anna", "r1", "phase", "a")
        chat.skill_turn("anna", "r1", "phase", "b")
        chat.skill_turn("anna", "r1", "failed", "no network")
        chat.log.append("user", "thanks", sender="anna")
        # When / Then: the model history holds the question, the answer, the last status and the end message, in order
        texts = [m["text"] for m in chat.model_history()]
        self.assertEqual(texts[:2], ["Which topic?", "canary"])
        self.assertEqual(len(texts), 4)
        self.assertIn("no network", texts[3])
        self.assertEqual([m["role"] for m in chat.model_history()], ["assistant", "user", "assistant", "assistant"])

    @mark.req("REQ-CHA-046")
    def test_only_the_last_three_runs_are_in_it(self):
        """older runs are left out so that the history stays small.
        Example: five runs of one summary each -> the last three."""
        # Given: five finished runs
        chat = service(self)
        for n in range(1, 6):
            chat.skill_turn("anna", "r%d" % n, "done", "x")
        # When / Then: the history holds the end messages of runs 3 to 5
        runs = [t.split("#run=")[1].rstrip(")") for t in (m["text"] for m in chat.model_history())]
        self.assertEqual(runs, ["r3", "r4", "r5"])

    @mark.req("REQ-CHA-046")
    def test_without_a_skill_run_the_history_is_empty(self):
        """an ordinary chat gives no skill message.
        Example: [] ."""
        chat = service(self)
        chat.log.append("user", "hello", sender="anna")
        self.assertEqual(chat.model_history(), [])


class CommunicatorCall(unittest.TestCase):
    def setUp(self):
        communicator = importlib.import_module("MIA.communicator")
        self.sent = []
        outer = self

        class Client:
            def chat(self, model, messages, **kwargs):
                outer.sent.append([dict(m) for m in messages])
                return iter(())

        comm = communicator.Communicator.__new__(communicator.Communicator)
        comm._history, comm.version, comm.llm_options, comm.think, comm.keep_alive = [], "m", None, None, None
        comm.client, comm._addtional_calibration = Client(), ""
        self.comm = comm

    @mark.req("REQ-CHA-046")
    def test_the_skill_messages_come_before_the_new_user_message_and_are_not_kept(self):
        """the messages of the provider are in the call, in the roles and texts they have, between the system message and the user message; the memory of the Communicator does not keep them.
        Example: provider [assistant "Which topic?", user "canary"], chat("hi")."""
        # Given: a provider of skill messages
        self.comm.skill_history = lambda: [{"role": "assistant", "text": "Which topic?"}, {"role": "user", "text": "canary"}]
        # When: the next turn is asked twice
        self.comm.chat("hi")
        self.comm.chat("again")
        # Then: the call holds the system message, the skill messages and the new user message; the memory holds the two user messages only
        self.assertEqual([(m["role"], m["content"]) for m in self.sent[0][1:]], [("assistant", "Which topic?"), ("user", "canary"), ("user", "hi")])
        self.assertEqual([(m["role"], m["content"]) for m in self.sent[1][1:]], [("user", "hi"), ("assistant", "Which topic?"), ("user", "canary"), ("user", "again")])
        self.assertEqual([m["content"] for m in self.comm._history], ["hi", "again"])

    @mark.req("REQ-CHA-046")
    def test_a_provider_that_fails_or_is_missing_changes_nothing(self):
        """no provider and a provider that raises give the call of today.
        Example: skill_history = a function that raises."""
        # Given: no provider, then one that raises
        self.comm.chat("one")
        def broken():
            raise RuntimeError("log unreadable")
        self.comm.skill_history = broken
        self.comm.chat("two")
        # Then: both calls hold the system message and the history only
        self.assertEqual([m["content"] for m in self.sent[0][1:]], ["one"])
        self.assertEqual([m["content"] for m in self.sent[1][1:]], ["one", "two"])


if __name__ == "__main__":
    unittest.main()
