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
    return lambda kind: ChatApiMock(**options) if kind == "mock" else subject_for(IF, kind, **options)


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
        """TC-IF-101-05 golden 3: positions 1, 2, 3 (two users); a fourth message is 503 queue_full and queues nothing; after settle the queue is empty."""
        s, b = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        self.assertEqual([api.send(s, "m1")["position"], api.send(b, "m2")["position"], api.send(s, "m3")["position"]], [1, 2, 3])
        err = error_of(lambda: api.send(b, "m4"))
        self.assertEqual((err.status, err.code), (503, "queue_full"))
        api.settle()
        self.assertEqual(api.send(s, "m5")["position"], 1)
        self.assertEqual([m["text"] for m in api.history(s, 50) if m["role"] == "user"], ["m1", "m2", "m3", "m5"])

    @mark.req("IF-101", "REQ-BE-003")
    @each_provider(IF)
    def test_one_user_cannot_fill_the_queue(self, api):
        """TC-IF-101-09: with the defaults (5 in all, 2 per user) a third waiting message of one user is 503 queue_full while another user can still send."""
        s, b = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.send(s, "a1")
        api.send(s, "a2")
        err = error_of(lambda: api.send(s, "a3"))
        self.assertEqual((err.status, err.code), (503, "queue_full"))
        self.assertEqual(api.send(b, "b1")["position"], 3)
        api.settle()
        self.assertEqual(api.send(s, "a4")["position"], 1)

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

    # ------------------------------------------------------------ v1 (amendment A-03)
    @mark.req("IF-101", "REQ-FE-001", "REQ-CLV-001")
    @each_provider(IF)
    def test_the_acknowledgement_carries_the_stored_message_and_the_client_id_comes_back(self, api):
        """TC-IF-101-09 (v1): send answers with id, position and the stored message; the message and its chat_message event carry the client id, so the page finds its own copy."""
        anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.connect(ben)
        api.events(ben)
        ack = api.send(anna, "hi", client_id="c-1")
        self.assertEqual((ack["position"], ack["message"]["id"], ack["message"]["sender"], ack["message"]["client_id"]), (1, ack["id"], "anna", "c-1"))
        event = [e["payload"] for e in api.events(ben) if e["event"] == "chat_message"][0]
        self.assertEqual((event["id"], event["client_id"]), (ack["id"], "c-1"))
        self.assertEqual(api.history(anna, 5)[-1]["client_id"], "c-1")

    @mark.req("IF-101", "REQ-CLV-014", "REQ-BE-011")
    @each_provider(IF)
    def test_whoami_and_the_own_password(self, api):
        """TC-IF-101-10 (v1): a kept session knows its account; the own password changes with the old one; a weak or wrong one is refused; the old password stops working."""
        s = api.login("anna", "pw-anna")
        self.assertEqual(api.whoami(s), {"user": "anna"})
        self.assertEqual(error_of(lambda: api.change_password(s, "wrong", "long-enough-1")).status, 401)
        err = error_of(lambda: api.change_password(s, "pw-anna", "short"))
        self.assertEqual((err.status, err.code), (422, "weak_password"))
        self.assertEqual(api.change_password(s, "pw-anna", "long-enough-1"), {"changed": True})
        self.assertEqual(error_of(lambda: api.login("anna", "pw-anna")).status, 401)
        self.assertTrue(api.login("anna", "long-enough-1"))
        self.assertEqual(error_of(lambda: api.whoami("no-session")).status, 401)

    @mark.req("IF-101", "REQ-CLV-022", "REQ-BE-077")
    @each_provider(IF)
    def test_logout_ends_only_that_session(self, api):
        """TC-IF-101-18 (v2): after a logout the session is refused with 401 on every operation; a second session of the same account and the password stay valid."""
        s1 = api.login("anna", "pw-anna")
        s2 = api.login("anna", "pw-anna")
        api.connect(s1)
        self.assertEqual(api.logout(s1), {"loggedOut": True})
        self.assertEqual(error_of(lambda: api.whoami(s1)).status, 401)
        self.assertEqual(error_of(lambda: api.history(s1, 5)).status, 401)
        self.assertEqual(error_of(lambda: api.logout(s1)).status, 401)
        self.assertEqual(api.whoami(s2), {"user": "anna"})
        self.assertTrue(api.login("anna", "pw-anna"))

    @mark.req("IF-101", "REQ-CLV-005", "REQ-BE-006")
    @each_provider(IF, make(answers=[["First try."], ["Second try. Better."]]))
    def test_regenerate_the_last_answer_and_speak_any_answer_again(self, api):
        """TC-IF-101-11 (v1): regenerate queues a new try of the LAST answer (the old one stays); speak_again sends one audio_chunk per sentence of any answer."""
        s = api.login("anna", "pw-anna")
        api.connect(s)
        api.send(s, "hi")
        api.settle()
        first = api.history(s, 5)[-1]
        self.assertEqual(error_of(lambda: api.regenerate(s, "nope")).status, 404)
        self.assertEqual(error_of(lambda: api.regenerate(s, api.history(s, 5)[0]["id"])).status, 422)       # a user message is not an answer
        self.assertEqual(api.regenerate(s, first["id"])["position"], 1)
        api.settle()
        history = api.history(s, 10)
        self.assertEqual([m["text"] for m in history if m["role"] == "assistant"], ["First try.", "Second try. Better."])
        self.assertEqual(error_of(lambda: api.regenerate(s, first["id"])).status, 422)                       # no longer the last answer
        api.events(s)
        self.assertEqual(api.speak_again(s, first["id"]), {"sentences": 1})
        chunks = [e["payload"] for e in api.events(s) if e["event"] == "audio_chunk"]
        self.assertEqual([(c["id"], c["index"], c["sentence"]) for c in chunks], [(first["id"], 0, "First try.")])
        self.assertEqual(error_of(lambda: api.speak_again(s, "nope")).status, 404)

    @mark.req("IF-101", "REQ-BE-028", "REQ-CLV-010")
    @each_provider(IF, make(answers=[["Fine."]]))
    def test_the_score_is_also_given_per_week(self, api):
        """TC-IF-101-21 (v4): `series` has the sums of each ISO week with a vote, oldest first; the sums of the weeks add up to the totals; a refused vote is in no week."""
        anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.connect(ben)
        api.send(anna, "hi")
        api.settle()
        answer = api.history(anna, 5)[-1]["id"]
        api.events(ben)
        api.vote(anna, answer, "answer_quality", 1)
        api.vote(ben, "service", "service", -1)
        api.advance_time(8 * 24 * 3600)                                             # the next week and a bit
        api.vote(ben, answer, "answer_quality", 1)
        self.assertEqual(error_of(lambda: api.vote(ben, answer, "answer_quality", 5)).code, "invalid_vote")          # refused
        score = api.score(anna)
        self.assertEqual([w["week"] for w in score["series"]], ["2026-W02", "2026-W03"])
        self.assertEqual((score["series"][0]["overall"], score["series"][1]["overall"]), (0, 1))
        self.assertEqual(score["series"][0]["categories"], {"answer_quality": 1, "reactions": 0, "character_behaviour": 0, "service": -1})
        self.assertEqual(sum(w["overall"] for w in score["series"]), score["overall"])
        pushed = [e["payload"] for e in api.events(ben) if e["event"] == "score"]
        self.assertEqual(pushed[-1]["series"], score["series"])

    @mark.req("IF-101", "REQ-CLV-010", "REQ-BE-028")
    @each_provider(IF)
    def test_votes_have_a_category_and_the_scores_follow(self, api):
        """TC-IF-101-12 (v1): a vote is kept with user, subject, category and value; the score per category and overall is returned and pushed to everybody."""
        anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.connect(ben)
        api.send(anna, "hi")
        api.settle()
        answer = api.history(anna, 5)[-1]["id"]
        api.events(ben)
        result = api.vote(anna, answer, "answer_quality", 1)
        self.assertEqual(result["score"]["categories"]["answer_quality"], 1)
        api.vote(ben, answer, "answer_quality", -1)
        api.vote(ben, "service", "service", -1)
        score = api.score(anna)
        self.assertEqual((score["overall"], score["votes"], score["categories"]["service"]), (-1, 3, -1))
        pushed = [e["payload"] for e in api.events(ben) if e["event"] == "score"]
        self.assertEqual(pushed[-1]["overall"], -1)
        for category, value in (("mood", 1), ("service", 5), ("service", True)):
            err = error_of(lambda: api.vote(anna, answer, category, value))
            self.assertEqual((err.status, err.code), (422, "invalid_vote"))
        self.assertEqual(api.score(anna)["votes"], 3)                                  # a refused vote is not stored

    @mark.req("IF-101", "REQ-CLV-011", "REQ-BE-026", "REQ-BE-032")
    @each_provider(IF)
    def test_tasks_memos_and_memory_are_listed_changed_and_deleted_by_every_user(self, api):
        """TC-IF-101-13 (v1): all records are listed; a user changes or deletes the record of another; the others get item_changed; memory needs a source; text comes back byte for byte."""
        anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.connect(ben)
        text = "Call Zoë at 9:00 – bring \"the\" notes\n\tdone ✓"
        task = api.save_item(anna, "tasks", None, text)
        self.assertEqual((task["text"], task["author"]), (text, "anna"))
        api.events(ben)
        changed = api.save_item(ben, "tasks", task["id"], "Water the plants")
        self.assertEqual((changed["id"], changed["author"]), (task["id"], "ben"))
        self.assertEqual([e["payload"] for e in api.events(ben) if e["event"] == "item_changed"], [{"kind": "tasks", "id": task["id"], "author": "ben", "deleted": False}])
        for n in range(50):
            api.save_item(anna, "memos", None, "memo %d" % n)
        self.assertEqual(len(api.items(ben, "memos")), 50)
        err = error_of(lambda: api.save_item(anna, "memory", None, "likes tea"))
        self.assertEqual((err.status, err.rule), (422, "source"))
        self.assertEqual(api.save_item(anna, "memory", None, "likes tea", source="chat")["source"], "chat")
        self.assertEqual(api.delete_item(ben, "tasks", task["id"]), {"deleted": True})
        self.assertEqual(api.items(anna, "tasks"), [])
        self.assertEqual(error_of(lambda: api.delete_item(ben, "tasks", task["id"])).status, 404)
        self.assertEqual(error_of(lambda: api.items(anna, "dreams")).status, 404)
        self.assertEqual(error_of(lambda: api.save_item(anna, "memos", None, "  ")).status, 422)

    @mark.req("IF-101", "REQ-CLV-012", "REQ-BE-025")
    @each_provider(IF)
    def test_the_trust_value_of_a_source_is_edited_with_old_and_new_value(self, api):
        """TC-IF-101-14 (v1): the edit carries source id, old and new value and the author; a value outside 0..1 and an unknown source are refused."""
        s = api.login("anna", "pw-anna")
        api.connect(s)
        old = api.trust(s)["example.org"]
        api.events(s)
        self.assertEqual(api.set_trust(s, "example.org", 0.2), {"source": "example.org", "old": old, "new": 0.2})
        self.assertEqual([e["payload"] for e in api.events(s) if e["event"] == "trust_changed"], [{"source": "example.org", "old": old, "new": 0.2, "author": "anna"}])
        self.assertEqual(api.trust(s)["example.org"], 0.2)
        self.assertEqual(error_of(lambda: api.set_trust(s, "example.org", 1.5)).code, "invalid_trust")
        self.assertEqual(error_of(lambda: api.set_trust(s, "unknown.example", 0.5)).status, 404)

    @mark.req("IF-101", "REQ-CLV-009", "REQ-BE-021")
    @each_provider(IF)
    def test_the_persona_is_saved_as_data_and_others_hear_of_it(self, api):
        """TC-IF-101-15 (v1): the shared persona is read and saved as data; the other pages get persona_changed with the author; an empty one is refused."""
        anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.connect(ben)
        api.events(ben)
        self.assertEqual(api.save_persona(anna, {"text": "MIA is calm and dry."})["text"], "MIA is calm and dry.")
        self.assertEqual(api.persona(ben)["text"], "MIA is calm and dry.")
        self.assertEqual([e["payload"] for e in api.events(ben) if e["event"] == "persona_changed"], [{"author": "anna"}])
        self.assertEqual(error_of(lambda: api.save_persona(anna, {"text": " "})).code, "invalid_persona")
        self.assertEqual(api.persona(anna)["text"], "MIA is calm and dry.")

    @mark.req("IF-101", "REQ-CLV-008", "REQ-WFX-001")
    @each_provider(IF)
    def test_the_account_of_an_answer_is_a_list_of_plain_sentences(self, api):
        """TC-IF-101-16 (v1): opening an answer gives its step-by-step account in order; a message that is not an answer has none."""
        s = api.login("anna", "pw-anna")
        api.send(s, "hi")
        api.settle()
        history = api.history(s, 5)
        lines = api.account(s, history[-1]["id"])
        self.assertEqual([l["seq"] for l in lines], list(range(1, len(lines) + 1)))
        self.assertTrue(all(isinstance(l["plain"], str) and l["plain"] for l in lines))
        self.assertEqual(error_of(lambda: api.account(s, history[0]["id"])).status, 404)

    @mark.req("IF-101", "REQ-CLV-013", "REQ-BE-043")
    @each_provider(IF)
    def test_an_answer_announces_the_character_variant_of_its_workflow(self, api):
        """TC-IF-101-17 (v1): the event variant {name} comes with every answer: the name of the variant, or null when the workflow has none (the chat's variant stays)."""
        s = api.login("anna", "pw-anna")
        api.connect(s)
        api.send(s, "one")
        api.settle()
        self.assertEqual([e["payload"] for e in api.events(s) if e["event"] == "variant"], [{"name": None}])
        api.run_with_variant("summer")
        api.send(s, "two")
        api.settle()
        self.assertEqual([e["payload"] for e in api.events(s) if e["event"] == "variant"], [{"name": "summer"}])


if __name__ == "__main__":
    unittest.main()
