"""
Unit tests of ChatService.skill_turn beyond its acceptance checks (G-V3.CHAT T-02; REQ-CHA-040 to 045, 056, 057): a refused kind adds nothing, the plain sentences when the digest
step is missing or fails, the phases of a service without declared phases, the record fields. Run with: python tests/test_skill_turn.py
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from chat_log import ChatLog              # noqa: E402
from chat_service import ChatError, ChatService  # noqa: E402
from markers import mark                  # noqa: E402
from moods import MoodTracker             # noqa: E402

LINK = " [Open in the Skill run view](#run=%s)"


class Broken:
    def status(self, phase):
        raise RuntimeError("model down")

    summary = failure = stopped = status


def service(test, digest=None, phases=None):
    folder = tempfile.mkdtemp()
    test.addCleanup(shutil.rmtree, folder, True)
    events = []
    chat = ChatService(lambda event, payload: events.append((event, payload)), ChatLog(os.path.join(folder, "log.jsonl")), MoodTracker(os.path.join(REPO, "moods.json")),
                       lambda *args: "", spawn=lambda target: target(), clock=lambda: 100.0, digest=digest, declared_phases=phases)
    return chat, events


class SkillTurn(unittest.TestCase):
    @mark.req("REQ-CHA-040")
    def test_an_unknown_kind_is_refused_and_adds_nothing(self):
        """kind chat is invalid_kind and the log stays as it was.
        Example: skill_turn("anna", "r1", "chat", "x") -> ChatError invalid_kind."""
        # Given: a service
        chat, events = service(self)
        # When / Then: the unknown kind is refused, nothing is added
        with self.assertRaises(ChatError) as caught:
            chat.skill_turn("anna", "r1", "chat", "x")
        self.assertEqual(caught.exception.code, "invalid_kind")
        self.assertEqual((chat.log.history(limit=10)[0], events), ([], []))

    @mark.req("REQ-CHA-043", "REQ-CHA-044", "REQ-CHA-056", "REQ-CHA-057")
    def test_without_a_digest_step_or_when_it_fails_the_run_still_ends_in_plain_words(self):
        """the end messages are plain sentences that invent nothing and still end with the link.
        Example: failed with "no network" -> "The run failed: no network" and the link."""
        for digest in (None, Broken()):
            with self.subTest(digest=digest):
                # Given: a service without a digest step, or with one that raises
                chat, _ = service(self, digest=digest)
                # When: the run ends done, failed and stopped
                for kind, payload in (("done", "a long result"), ("failed", "no network"), ("stopped", "stopped by the user")):
                    chat.skill_turn("anna", "r1", kind, payload)
                # Then: each message is a plain sentence with the link, the result text is not in the chat
                texts = [r["text"] for r in chat.log.history(limit=10)[0]]
                self.assertEqual(texts, ["The run is done." + LINK % "r1", "The run failed: no network" + LINK % "r1", "The run was stopped (stopped by the user)." + LINK % "r1"])

    @mark.req("REQ-CHA-042", "REQ-CHA-055")
    def test_a_service_without_declared_phases_gives_no_status(self):
        """no declared_phases means no phase has a message.
        Example: skill_turn(..., "phase", "collect") -> {"id": None}."""
        # Given: a service without declared phases
        chat, events = service(self)
        # When / Then: a phase gives no message and no event
        self.assertEqual(chat.skill_turn("anna", "r1", "phase", "collect"), {"id": None})
        self.assertEqual((chat.log.history(limit=10)[0], events), ([], []))

    @mark.req("REQ-CHA-040")
    def test_the_record_carries_the_run_and_the_kind(self):
        """the stored record and the event chat_message carry skill_run and kind.
        Example: a question of run r1 has skill_run r1 and kind question."""
        # Given: a service
        chat, events = service(self)
        # When: a question is added
        ack = chat.skill_turn("anna", "r1", "question", "Which period?")
        # Then: the record and the event carry the run and the kind
        record = chat.log.history(limit=10)[0][0]
        self.assertEqual((record["id"], record["skill_run"], record["kind"], record["role"], record["text"]), (ack["id"], "r1", "question", "assistant", "Which period?"))
        sent = [p for e, p in events if e == "chat_message"]
        self.assertEqual([(p["skill_run"], p["kind"]) for p in sent], [("r1", "question")])


if __name__ == "__main__":
    unittest.main()
