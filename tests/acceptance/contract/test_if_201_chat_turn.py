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
    return lambda kind: ChatTurnMock(**options) if kind == "mock" else subject_for(IF, kind, **options)


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

    @mark.req("IF-201", "REQ-BE-005")
    @each_provider(IF, make(answers=[["First answer."], ["Second answer."]]))
    def test_regenerate_asks_again_for_the_last_answer_only(self, chat):
        """TC-IF-201-05 (v1): regenerate of the last answer queues a new try and keeps the old answer; an older answer is not_the_last_answer; an unknown id is not_found."""
        chat.send("anna", "q1")
        chat.settle()
        chat.send("anna", "q2")
        chat.settle()
        answers = [m["id"] for m in chat.history() if m["role"] == "assistant"]
        self.assertEqual(code_of(lambda: chat.regenerate("anna", answers[0])), "not_the_last_answer")
        self.assertEqual(code_of(lambda: chat.regenerate("anna", "nope")), "not_found")
        result = chat.regenerate("anna", answers[1])
        self.assertEqual(result["position"], 1)
        chat.settle()
        self.assertEqual(len([m for m in chat.history() if m["role"] == "assistant"]), 3)

    @mark.req("IF-201", "REQ-BE-006")
    @each_provider(IF, make(answers=[["One.", "Two."]]))
    def test_speak_again_and_the_account_of_an_answer(self, chat):
        """TC-IF-201-06 (v1): speak_again gives one audio_chunk per sentence; account lists plain steps in order; both are not_found for an id that is no answer."""
        chat.send("anna", "hi")
        chat.settle()
        user, answer = chat.history()[0]["id"], chat.history()[-1]["id"]
        seen = []
        chat.subscribe(seen.append)
        self.assertEqual(chat.speak_again(answer), {"sentences": 2})
        self.assertEqual([e["payload"]["index"] for e in seen if e["event"] == "audio_chunk"], [0, 1])
        steps = chat.account(answer)
        self.assertEqual([s["seq"] for s in steps], sorted(s["seq"] for s in steps))
        self.assertTrue(all(isinstance(s["plain"], str) and s["plain"] for s in steps))
        for call in (lambda: chat.speak_again(user), lambda: chat.account(user), lambda: chat.account("nope")):
            self.assertEqual(code_of(call), "not_found")

    @mark.req("IF-201", "REQ-BE-028")
    @each_provider(IF, make(answers=[["Fine."]]))
    def test_votes_are_stored_and_the_score_is_given_per_week(self, chat):
        """TC-IF-201-07 (v1): a vote is stored and returns the score with its weeks (`series`, ISO weeks, oldest first); a bad category or value is invalid_vote with the rule; an unknown answer is not_found; a score event is pushed."""
        chat.send("anna", "hi")
        chat.settle()
        answer = chat.history()[-1]["id"]
        seen = []
        chat.subscribe(seen.append)
        self.assertTrue(chat.vote("anna", answer, "answer_quality", 1)["stored"])
        chat.advance_time(8 * 24 * 3600)
        chat.vote("ben", "service", "service", -1)
        score = chat.score()
        self.assertEqual((score["overall"], score["votes"]), (0, 2))
        self.assertEqual([(w["week"], w["overall"]) for w in score["series"]], [("2026-W02", 1), ("2026-W03", -1)])
        self.assertEqual([e["payload"] for e in seen if e["event"] == "score"][-1], score)
        for category, value, rule in (("nonsense", 1, "category"), ("service", 5, "value")):
            try:
                chat.vote("anna", "service", category, value)
            except ServiceError as err:
                self.assertEqual((err.code, err.rule), ("invalid_vote", rule))
            else:
                self.fail("no ServiceError raised")
        self.assertEqual(code_of(lambda: chat.vote("anna", "nope", "answer_quality", 1)), "not_found")
        self.assertEqual(chat.score()["votes"], 2)                                  # refused votes are not stored

    @mark.req("IF-201", "REQ-CHA-017", "REQ-CHA-018")
    @each_provider(IF)
    def test_the_counters_follow_the_votes_and_a_reset_restores_the_default_rate(self, chat):
        """TC-IF-201-08 (v2): 5 net negative votes on a behaviour give a chance of at most 0.01; a reset restores 1.0 and announces counters_changed; a name that is not on the list is invalid_vote (subject) or not_found."""
        seen = []
        chat.subscribe(seen.append)
        self.assertEqual(sorted(chat.counters()), ["greet", "idle", "no", "talk", "yes"])
        for account in ("anna", "ben", "carl", "dora", "emil"):
            chat.vote(account, "talk", "character_behaviour", -1)
        self.assertEqual((chat.counters()["talk"]["net"], chat.counters()["talk"]["votes"]), (-5, 5))
        self.assertLessEqual(chat.counters()["talk"]["chance"], 0.01)
        chat.advance_time(60)
        self.assertEqual(chat.reset_counter("ben", "talk")["chance"], 1.0)
        self.assertEqual([e["payload"] for e in seen if e["event"] == "counters_changed"], [{"name": "talk", "author": "ben"}])
        self.assertEqual(chat.score()["votes"], 5)                                  # the votes stay
        self.assertEqual(code_of(lambda: chat.reset_counter("ben", "dance")), "not_found")
        try:
            chat.vote("anna", "dance", "character_behaviour", -1)
        except ServiceError as err:
            self.assertEqual((err.code, err.rule), ("invalid_vote", "subject"))
        else:
            self.fail("no ServiceError raised")


LINK = " [Open in the Skill run view](#run=%s)"


@contract
class SkillTurnContract(unittest.TestCase):
    """IF-201 v3 (A-142): the turns of a skill run in the chat (G-V3.CHAT)."""

    @mark.req("IF-201", "REQ-CHA-040", "REQ-CHA-041", "REQ-CHA-043", "REQ-CHA-044", "REQ-CHA-056", "REQ-CHA-057")
    @each_provider(IF, make(phases=("screening", "reading")))
    def test_a_turn_of_a_skill_is_a_message_with_its_marker(self, chat):
        """TC-IF-201-09 (v3): `skill_turn(account, run, kind, payload)` with kind question, phase, done, failed or stopped adds one message of MIA that carries `skill_run: <run>` and `kind` in the event chat_message and in the history and returns its `{id}`; the texts of done, failed and stopped end with ` [Open in the Skill run view](#run=<run>)`; a question is its text; the text of failed contains the reason; the summary of a long full result is shorter than the result.
        Example: skill_turn("anna", "r1", "failed", "the scholarly service is down") -> a message ending with the link, containing the reason."""
        seen = []
        chat.subscribe(seen.append)
        full = "The works agree on lower costs. " * 200
        turns = [("question", "Which period?"), ("phase", "screening"), ("done", full), ("failed", "the scholarly service is down"), ("stopped", "stopped by the user")]
        ids = []
        for kind, payload in turns:
            ack = chat.skill_turn("anna", "r1", kind, payload)
            self.assertEqual(set(ack), {"id"})
            ids.append(ack["id"])
        chat.settle()
        by_id = {m["id"]: m for m in chat.history()}
        self.assertEqual([by_id[i]["kind"] for i in ids], [k for k, _ in turns])
        for i in ids:
            self.assertEqual((by_id[i]["skill_run"], by_id[i]["role"], by_id[i]["sender"]), ("r1", "assistant", "MIA"))
        messages = [e["payload"] for e in seen if e["event"] == "chat_message" and e["payload"].get("skill_run")]
        self.assertEqual([(m["id"], m["kind"], m["skill_run"]) for m in messages], [(i, k, "r1") for i, (k, _) in zip(ids, turns)])
        self.assertIn("Which period?", by_id[ids[0]]["text"])
        for i in ids[2:]:
            self.assertTrue(by_id[i]["text"].endswith(LINK % "r1"), by_id[i]["text"])
        self.assertIn("the scholarly service is down", by_id[ids[3]]["text"])
        self.assertLess(len(by_id[ids[2]]["text"]), len(full))
        for i in ids[:2]:
            self.assertNotIn("#run=", by_id[i]["text"])

    @mark.req("IF-201", "REQ-CHA-041", "REQ-CHA-042", "REQ-CHA-055")
    @each_provider(IF, make(phases=("screening",)))
    def test_a_phase_that_the_skill_does_not_declare_adds_no_message(self, chat):
        """TC-IF-201-10 (v3): a phase that the manifest of the skill does not declare gives `{"id": None}` and adds no message and no event; a declared phase gives a message.
        Example: with declared phase screening, skill_turn("anna", "r1", "phase", "indexing") -> {"id": None}."""
        seen = []
        chat.subscribe(seen.append)
        before = len(chat.history())
        self.assertEqual(chat.skill_turn("anna", "r1", "phase", "indexing"), {"id": None})
        chat.settle()
        self.assertEqual((len(chat.history()), seen), (before, []))
        ack = chat.skill_turn("anna", "r1", "phase", "screening")
        self.assertTrue(ack["id"])
        self.assertEqual(len(chat.history()), before + 1)

    @mark.req("IF-201", "REQ-CHA-040")
    @each_provider(IF)
    def test_an_unknown_kind_is_refused_and_adds_nothing(self, chat):
        """TC-IF-201-11 (v3): an unknown kind is ServiceError invalid_kind and nothing is added.
        Example: skill_turn("anna", "r1", "chat", "x") -> ServiceError("invalid_kind")."""
        before = chat.history()
        self.assertEqual(code_of(lambda: chat.skill_turn("anna", "r1", "chat", "x")), "invalid_kind")
        chat.settle()
        self.assertEqual(chat.history(), before)

    @mark.req("IF-201", "REQ-CHA-045", "REQ-CHA-047")
    @each_provider(IF, make(phases=("screening",)))
    def test_every_message_of_a_skill_turn_is_sent_to_speech(self, chat):
        """TC-IF-201-12 (v3): each message that skill_turn adds is followed by at least one audio_chunk with its id, like an answer; a phase without a message gives none.
        Example: skill_turn("anna", "r1", "question", "Which period?") -> an audio_chunk {id, index 0, sentence}."""
        seen = []
        chat.subscribe(seen.append)
        ids = [chat.skill_turn("anna", "r1", kind, payload)["id"] for kind, payload in (("question", "Which period?"), ("phase", "screening"), ("done", "All done."))]
        self.assertIsNone(chat.skill_turn("anna", "r1", "phase", "indexing")["id"])
        chat.settle()
        spoken = {e["payload"]["id"] for e in seen if e["event"] == "audio_chunk"}
        self.assertEqual(spoken, set(ids))


if __name__ == "__main__":
    unittest.main()
