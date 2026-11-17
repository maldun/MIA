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
        """TC-IF-201-01 golden 1: message with sender, start, growing deltas, one audio chunk per sentence, done.
        Example: answers "Hello Anna." and "How are you?" give the events chat_message, chat_start, 2 chat_delta, 2 audio_chunk (index 0 and 1), chat_done."""
        # Given: a chat that answers with two sentences and a subscriber
        seen = []
        chat.subscribe(seen.append)
        # When: the user sends a message and the answer is settled
        self.assertEqual(chat.send("anna", "hi"), {"id": chat.history()[0]["id"], "position": 1})
        chat.settle()
        # Then: the events are in order, with one audio chunk per sentence
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
        """TC-IF-201-02 golden 2: blank text is empty_text and nothing is queued.
        Example: send("anna", "") and send("anna", "  \n") -> ServiceError empty_text, queue 0."""
        for text in ("", "  \n"):
            self.assertEqual(code_of(lambda: chat.send("anna", text)), "empty_text")
        self.assertEqual(chat.status()["queue"], 0)

    @mark.req("IF-201", "REQ-BE-003")
    @each_provider(IF, make(queue_limit=2))
    def test_a_full_queue_refuses_without_harm(self, chat):
        """TC-IF-201-03 golden 2: positions 1, 2; the third message is queue_full; the queued ones are still answered.
        Example: queue limit 2: positions 1 and 2, the third send -> queue_full, both queued messages are answered."""
        # Given: a chat with a queue limit of 2 that takes two messages
        self.assertEqual([chat.send("anna", "a")["position"], chat.send("ben", "b")["position"]], [1, 2])
        # When: a third message is sent
        self.assertEqual(code_of(lambda: chat.send("anna", "c")), "queue_full")
        # Then: it is refused and the queued ones are still answered
        self.assertEqual(chat.status()["queue"], 2)
        chat.settle()
        self.assertEqual(sum(1 for m in chat.history() if m["role"] == "assistant"), 2)

    @mark.req("IF-201", "REQ-BE-004")
    @each_provider(IF, make(answers=[["One.", "Two."]]))
    def test_stop(self, chat):
        """TC-IF-201-04 golden 3: stop right after send ends the answer without a delta; with nothing running it is stopped false.
        Example: send "story", stop() -> {"stopped": True}, no chat_delta, chat_done with status stopped; a second stop() -> {"stopped": False}."""
        # Given: a chat with a two-sentence answer and a subscriber
        seen = []
        chat.subscribe(seen.append)
        chat.send("anna", "story")
        # When: the user stops right after sending
        self.assertEqual(chat.stop(), {"stopped": True})
        chat.settle()
        # Then: the answer ends stopped without a delta, and a second stop finds nothing running
        self.assertNotIn("chat_delta", [e["event"] for e in seen])
        self.assertEqual([e["payload"]["status"] for e in seen if e["event"] == "chat_done"], ["stopped"])
        self.assertEqual(chat.stop(), {"stopped": False})

    @mark.req("IF-201", "REQ-BE-005")
    @each_provider(IF, make(answers=[["First answer."], ["Second answer."]]))
    def test_regenerate_asks_again_for_the_last_answer_only(self, chat):
        """TC-IF-201-05 (v1): regenerate of the last answer queues a new try and keeps the old answer; an older answer is not_the_last_answer; an unknown id is not_found.
        Example: two answers: regenerate of the first -> not_the_last_answer, of "nope" -> not_found, of the second -> position 1 and a third answer."""
        # Given: two answered messages
        chat.send("anna", "q1")
        chat.settle()
        chat.send("anna", "q2")
        chat.settle()
        answers = [m["id"] for m in chat.history() if m["role"] == "assistant"]
        # When: regenerate is asked for the older answer, an unknown id and the last answer
        self.assertEqual(code_of(lambda: chat.regenerate("anna", answers[0])), "not_the_last_answer")
        self.assertEqual(code_of(lambda: chat.regenerate("anna", "nope")), "not_found")
        result = chat.regenerate("anna", answers[1])
        # Then: the first two are refused, the last queues a new try and the old answer stays
        self.assertEqual(result["position"], 1)
        chat.settle()
        self.assertEqual(len([m for m in chat.history() if m["role"] == "assistant"]), 3)

    @mark.req("IF-201", "REQ-BE-006")
    @each_provider(IF, make(answers=[["One.", "Two."]]))
    def test_speak_again_and_the_account_of_an_answer(self, chat):
        """TC-IF-201-06 (v1): speak_again gives one audio_chunk per sentence; account lists plain steps in order; both are not_found for an id that is no answer.
        Example: an answer of two sentences, "One." and "Two.": speak_again -> {"sentences": 2} and audio_chunk index 0 and 1."""
        # Given: an answer of two sentences and a subscriber
        chat.send("anna", "hi")
        chat.settle()
        user, answer = chat.history()[0]["id"], chat.history()[-1]["id"]
        seen = []
        chat.subscribe(seen.append)
        # When: speak_again is asked for the answer
        self.assertEqual(chat.speak_again(answer), {"sentences": 2})
        # Then: one audio chunk per sentence follows, the account lists plain steps in order, and an id that is no answer is not_found
        self.assertEqual([e["payload"]["index"] for e in seen if e["event"] == "audio_chunk"], [0, 1])
        steps = chat.account(answer)
        self.assertEqual([s["seq"] for s in steps], sorted(s["seq"] for s in steps))
        self.assertTrue(all(isinstance(s["plain"], str) and s["plain"] for s in steps))
        for call in (lambda: chat.speak_again(user), lambda: chat.account(user), lambda: chat.account("nope")):
            self.assertEqual(code_of(call), "not_found")

    @mark.req("IF-201", "REQ-BE-028")
    @each_provider(IF, make(answers=[["Fine."]]))
    def test_votes_are_stored_and_the_score_is_given_per_week(self, chat):
        """TC-IF-201-07 (v1): a vote is stored and returns the score with its weeks (`series`, ISO weeks, oldest first); a bad category or value is invalid_vote with the rule; an unknown answer is not_found; a score event is pushed.
        Example: a vote +1 in week 2026-W02 and a vote -1 eight days later give overall 0, votes 2 and the series (W02, 1), (W03, -1)."""
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
        """TC-IF-201-08 (v2): 5 net negative votes on a behaviour give a chance of at most 0.01; a reset restores 1.0 and announces counters_changed; a name that is not on the list is invalid_vote (subject) or not_found.
        Example: five accounts vote -1 on talk: net -5, chance at most 0.01; reset_counter("ben", "talk") -> chance 1.0 and counters_changed."""
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
    """IF-201 v3 (A-142) and v4 (A-158): the turns of a skill run in the chat and its status line (G-V3.CHAT)."""

    @mark.req("IF-201", "REQ-CHA-040", "REQ-CHA-041", "REQ-CHA-043", "REQ-CHA-044", "REQ-CHA-056", "REQ-CHA-057")
    @each_provider(IF, make(phases=("screening", "reading")))
    def test_a_turn_of_a_skill_is_a_message_with_its_marker(self, chat):
        """TC-IF-201-09 (v3): `skill_turn(account, run, kind, payload)` with kind question, done, failed or stopped adds one message of MIA that carries `skill_run: <run>` and `kind` in the event chat_message and in the history and returns its `{id}`; the texts of done, failed and stopped end with ` [Open in the Skill run view](#run=<run>)`; a question is its text; the text of failed contains the reason; the summary of a long full result is shorter than the result.
        Example: skill_turn("anna", "r1", "failed", "the scholarly service is down") -> a message ending with the link, containing the reason."""
        # Given: a chat with a skill that declares screening and reading, and a subscriber
        seen = []
        chat.subscribe(seen.append)
        full = "The works agree on lower costs. " * 200
        turns = [("question", "Which period?"), ("done", full), ("failed", "the scholarly service is down"), ("stopped", "stopped by the user")]
        # When: one turn of each kind is added
        ids = []
        for kind, payload in turns:
            ack = chat.skill_turn("anna", "r1", kind, payload)
            self.assertEqual(set(ack), {"id"})
            ids.append(ack["id"])
        # Then: each is a message of MIA with its marker and kind; the end messages end with the link, the others hold none
        chat.settle()
        by_id = {m["id"]: m for m in chat.history()}
        self.assertEqual([by_id[i]["kind"] for i in ids], [k for k, _ in turns])
        for i in ids:
            self.assertEqual((by_id[i]["skill_run"], by_id[i]["role"], by_id[i]["sender"]), ("r1", "assistant", "MIA"))
        messages = [e["payload"] for e in seen if e["event"] == "chat_message" and e["payload"].get("skill_run")]
        self.assertEqual([(m["id"], m["kind"], m["skill_run"]) for m in messages], [(i, k, "r1") for i, (k, _) in zip(ids, turns)])
        self.assertIn("Which period?", by_id[ids[0]]["text"])
        for i in ids[1:]:
            self.assertTrue(by_id[i]["text"].endswith(LINK % "r1"), by_id[i]["text"])
        self.assertIn("the scholarly service is down", by_id[ids[2]]["text"])
        self.assertLess(len(by_id[ids[1]]["text"]), len(full))
        for i in ids[:1]:
            self.assertNotIn("#run=", by_id[i]["text"])

    @mark.req("IF-201", "REQ-CHA-041", "REQ-CHA-042", "REQ-CHA-055")
    @each_provider(IF, make(phases=("screening",)))
    def test_a_phase_that_the_skill_does_not_declare_adds_no_message(self, chat):
        """TC-IF-201-10 (v3, v4): a phase that the manifest of the skill does not declare gives `{"id": None}` and adds no message and no event; a declared phase gives `{"id": None}` too and adds no message, only the status line (TC-IF-201-13).
        Example: with declared phase screening, skill_turn("anna", "r1", "phase", "indexing") -> {"id": None}."""
        # Given: a skill that declares only screening
        seen = []
        chat.subscribe(seen.append)
        before = len(chat.history())
        # When: an undeclared phase and then the declared one are added
        self.assertEqual(chat.skill_turn("anna", "r1", "phase", "indexing"), {"id": None})
        # Then: the first adds no message and no event, the second adds no message either (A-156) but the event of the status line
        chat.settle()
        self.assertEqual((len(chat.history()), seen), (before, []))
        self.assertEqual(chat.skill_turn("anna", "r1", "phase", "screening"), {"id": None})
        chat.settle()
        self.assertEqual(len(chat.history()), before)
        self.assertEqual([e["event"] for e in seen if e["event"] in ("chat_message", "chat_run_status")], ["chat_run_status"])

    @mark.req("IF-201", "REQ-CHA-040")
    @each_provider(IF)
    def test_an_unknown_kind_is_refused_and_adds_nothing(self, chat):
        """TC-IF-201-11 (v3): an unknown kind is ServiceError invalid_kind and nothing is added.
        Example: skill_turn("anna", "r1", "chat", "x") -> ServiceError("invalid_kind")."""
        # Given: a chat with its history as it is
        before = chat.history()
        # When: a turn of the unknown kind chat is added
        self.assertEqual(code_of(lambda: chat.skill_turn("anna", "r1", "chat", "x")), "invalid_kind")
        # Then: it is invalid_kind and the history is unchanged
        chat.settle()
        self.assertEqual(chat.history(), before)

    @mark.req("IF-201", "REQ-CHA-045", "REQ-CHA-047")
    @each_provider(IF, make(phases=("screening",)))
    def test_every_message_of_a_skill_turn_is_sent_to_speech(self, chat):
        """TC-IF-201-12 (v3): each message that skill_turn adds is followed by at least one audio_chunk with its id, like an answer; a phase without a message gives none.
        Example: skill_turn("anna", "r1", "question", "Which period?") -> an audio_chunk {id, index 0, sentence}."""
        # Given: a skill that declares screening and a subscriber
        seen = []
        chat.subscribe(seen.append)
        # When: a question and a summary are added, and a declared and an undeclared phase
        ids = [chat.skill_turn("anna", "r1", kind, payload)["id"] for kind, payload in (("question", "Which period?"), ("done", "All done."))]
        self.assertIsNone(chat.skill_turn("anna", "r1", "phase", "screening")["id"])
        self.assertIsNone(chat.skill_turn("anna", "r1", "phase", "indexing")["id"])
        # Then: every added message has an audio chunk and the undeclared phase none
        chat.settle()
        spoken = {e["payload"]["id"] for e in seen if e["event"] == "audio_chunk"}
        self.assertEqual(spoken, set(ids))


    @mark.req("IF-201", "REQ-CHA-068", "REQ-CHA-071")
    @each_provider(IF, make(phases=("screening", "reading")))
    def test_the_status_line_follows_the_declared_phases_and_is_no_message(self, chat):
        """TC-IF-201-13 (v4): the events chat_run_status `{run, text}` carry the declared phases in order; a repeated phase and an undeclared one give none; `start` of a run with phases gives none; no turn adds a message, a history record or speech.
        Example: start, screening, screening, indexing, reading -> the lines screening, reading."""
        # Given: a skill that declares screening and reading, and a subscriber
        seen = []
        chat.subscribe(seen.append)
        before = len(chat.history())
        # When: the run starts and enters its phases, one of them twice, and an undeclared one
        for kind, payload in (("start", ""), ("phase", "screening"), ("phase", "screening"), ("phase", "indexing"), ("phase", "reading")):
            self.assertEqual(chat.skill_turn("anna", "r1", kind, payload), {"id": None})
        # Then: the lines are the two declared phases in order, and nothing else was added
        chat.settle()
        self.assertEqual([e["payload"] for e in seen if e["event"] == "chat_run_status"], [{"run": "r1", "text": "screening"}, {"run": "r1", "text": "reading"}])
        self.assertEqual(len(chat.history()), before)
        self.assertEqual([e for e in seen if e["event"] in ("chat_message", "audio_chunk")], [])

    @mark.req("IF-201", "REQ-CHA-068", "REQ-CHA-070")
    @each_provider(IF, make(phases=()))
    def test_a_run_without_phases_shows_working_and_a_question_shows_that_it_waits(self, chat):
        """TC-IF-201-14 (v4): `start` of a run without declared phases gives the line `working`; a question is followed by the line `waiting for your answer`; `answered` gives the line `working` again; the line never comes before its question.
        Example: start, question "Which period?", answered "2020" -> working, message, waiting for your answer, working."""
        # Given: a skill without declared phases and a subscriber
        seen = []
        chat.subscribe(seen.append)
        # When: the run starts, asks a question and gets the answer
        chat.skill_turn("anna", "r1", "start", "")
        chat.skill_turn("anna", "r1", "question", "Which period?")
        chat.skill_turn("anna", "r1", "answered", "2020")
        # Then: the lines and the question message come in this order (other events, such as the voice, do not count)
        chat.settle()
        order = [(e["event"], e["payload"]["text"] if e["event"] == "chat_run_status" else e["payload"]["kind"]) for e in seen if e["event"] in ("chat_run_status", "chat_message")]
        self.assertEqual(order, [("chat_run_status", "working"), ("chat_message", "question"), ("chat_run_status", "waiting for your answer"), ("chat_run_status", "working")])

    @mark.req("IF-201", "REQ-CHA-069")
    @each_provider(IF, make(phases=("screening",)))
    def test_the_line_is_cleared_before_the_end_message(self, chat):
        """TC-IF-201-15 (v4): for done, failed and stopped the clearing line `{run, text: null}` comes before the end message, and no line of that run follows it.
        Example: screening, then done -> the lines screening, null, then the message of kind done, nothing after."""
        # Given: a skill that declares screening and a subscriber
        seen = []
        chat.subscribe(seen.append)
        for kind, payload in (("done", "All done."), ("failed", "the service is down"), ("stopped", "stopped by the user")):
            with self.subTest(kind=kind):
                # When: a run is in its phase and then ends
                first = len(seen)
                chat.skill_turn("anna", "r-" + kind, "phase", "screening")
                chat.skill_turn("anna", "r-" + kind, kind, payload)
                chat.settle()
                # Then: the clearing line comes before the end message and nothing of the run's line follows
                order = [(e["event"], e["payload"]["text"] if e["event"] == "chat_run_status" else e["payload"]["kind"]) for e in seen[first:] if e["event"] in ("chat_run_status", "chat_message")]
                self.assertEqual(order, [("chat_run_status", "screening"), ("chat_run_status", None), ("chat_message", kind)])


if __name__ == "__main__":
    unittest.main()
