"""Chat agent N-2.2: votes and the operations on answers (IF-201 v1): TC-CHA-015 (votes stored complete, scores equal their sums), the weekly series
of TC-IF-201-07, regenerate (TC-IF-201-05), speak_again and account (TC-IF-201-06). Run with: python tests/test_chat_answers.py"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
from chat_log import ChatLog                              # noqa: E402
from chat_service import ChatService, ChatError           # noqa: E402
from moods import MoodTracker                             # noqa: E402
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402

A59_INSTALLED = "`categories()`" in open(os.path.join(ROOT, "contracts", "IF-102-storage-interface.md"), encoding="utf-8").read()   # IF-102 v2 (A-59)
DAY = 24 * 3600
START = 1767225600          # 2026-01-01 00:00 UTC, a Thursday of ISO week 2026-W01


def code_of(call):
    try:
        call()
    except ChatError as err:
        return err.code, err.rule
    raise AssertionError("no ChatError raised")


class AnswersTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.now = START
        self.events = []
        self.asked = []
        self.storage = Storage(FileBackend(os.path.join(self.dir, "db")))
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))

        def exchange(text, on_delta, on_emotion, should_stop):
            self.asked.append(text)
            return "One. Two."

        self.chat = ChatService(lambda event, payload: self.events.append((event, payload)), self.log, MoodTracker(os.path.join(ROOT, "moods.json")), exchange,
                                queue_size=5, user_limit=2, spawn=lambda target: target(), votes=self.storage, wall_clock=lambda: self.now)

    def answer(self, text="hi"):
        self.chat.send(text, author="anna")
        return self.log.last("assistant")["id"]

    @mark.req("REQ-CHA-015")
    def test_votes_are_stored_complete_and_the_scores_equal_their_sums(self):
        """TC-CHA-015: every vote keeps user, time, subject and category in the votes table; the scores are the sums."""
        answer = self.answer()
        scripted = [("anna", answer, "answer_quality", 1), ("ben", answer, "answer_quality", 1), ("anna", "voice", "service", -1),
                    ("ben", "wave", "reactions", 1), ("anna", "calm", "character_behaviour", -1)]
        for vote in scripted:
            self.assertTrue(self.chat.vote(*vote)["stored"])
        self.assertEqual(len(self.storage.ids("votes")), len(scripted))
        stored = [self.storage.get("votes", i) for i in self.storage.ids("votes")]
        for entry in stored:
            self.assertEqual(sorted(entry["doc"]), ["category", "created", "subject", "user", "value"])
            self.assertEqual(entry["author"], entry["doc"]["user"])
        score = self.chat.score()
        self.assertEqual(score["categories"], {"answer_quality": 2, "reactions": 1, "character_behaviour": -1, "service": -1})
        self.assertEqual((score["overall"], score["votes"]), (1, 5))

    @mark.req("REQ-CHA-015")
    def test_a_user_counts_once_per_subject_and_category(self):
        """Clicking plus again does not raise the score; a changed mind replaces the vote (the table keeps the earlier version); other users count on."""
        answer = self.answer()
        for _ in range(3):
            self.chat.vote("anna", answer, "answer_quality", 1)
        self.assertEqual((self.chat.score()["overall"], self.chat.score()["votes"]), (1, 1))
        self.assertEqual(self.chat.vote("anna", answer, "answer_quality", -1)["score"]["overall"], -1)
        self.assertEqual(self.chat.vote("ben", answer, "answer_quality", 1)["score"]["overall"], 0)
        self.assertEqual(self.chat.vote("anna", answer, "reactions", 1)["score"]["votes"], 3)             # another category is another vote
        entry = self.storage.ids("votes")
        self.assertEqual(len(entry), 3)
        self.assertEqual(max(len(self.storage.history("votes", i)) for i in entry), 4)

    @mark.req("REQ-CHA-015")
    def test_the_score_is_given_per_iso_week_and_pushed(self):
        """TC-IF-201-07: sums per ISO week, oldest first, only weeks with a vote; the sums of the weeks equal the totals; a score event follows."""
        self.chat.vote("anna", "service", "service", 1)
        self.now += 8 * DAY
        self.chat.vote("ben", "service", "service", -1)
        self.chat.vote("anna", "voice", "reactions", 1)
        score = self.chat.score()
        self.assertEqual([(w["week"], w["overall"]) for w in score["series"]], [("2026-W01", 1), ("2026-W02", 0)])
        self.assertEqual(sum(w["overall"] for w in score["series"]), score["overall"])
        self.assertEqual([p for e, p in self.events if e == "score"][-1], score)

    @mark.req("REQ-CHA-015")
    def test_refused_votes_store_nothing(self):
        """TC-IF-201-07: a wrong category or value is invalid_vote with the rule, an unknown answer is not_found."""
        self.answer()
        self.assertEqual(code_of(lambda: self.chat.vote("anna", "service", "mood", 1)), ("invalid_vote", "category"))
        self.assertEqual(code_of(lambda: self.chat.vote("anna", "service", "service", 5)), ("invalid_vote", "value"))
        self.assertEqual(code_of(lambda: self.chat.vote("anna", "nope", "answer_quality", 1)), ("not_found", None))
        self.assertEqual(self.chat.score()["votes"], 0)
        self.assertEqual(self.storage.ids("votes"), [])

    @mark.req("REQ-CHA-015", "REQ-RTB-003")
    def test_a_float_or_boolean_vote_value_is_refused(self):
        """F3 (N-3.3 Verify, D-161): 1.0, -1.0 and True equal 1 or -1 in Python but are no vote values; nothing is stored.

        Example: vote("anna", "service", "service", 1.0) is invalid_vote, rule value.
        """
        # Given an answer
        self.answer()
        for value in (1.0, -1.0, True, False):
            with self.subTest(value=value):
                # When a vote has a float or boolean value, Then it is refused
                self.assertEqual(code_of(lambda: self.chat.vote("anna", "service", "service", value)), ("invalid_vote", "value"))
        # And nothing is stored
        self.assertEqual(self.storage.ids("votes"), [])

    @mark.req("REQ-CHA-015", "IF-102")
    def test_the_chat_service_takes_the_vote_categories_from_the_storage(self):
        """D-162: the chat service asks the storage (IF-102 categories()) and keeps no list of its own.
        Example: a storage that lists only "service": a vote "reactions" is invalid_vote/category and the score has only "service"."""
        import chat_service

        class OnlyService:
            def __init__(self, store):
                self._store = store

            def categories(self):
                return ["service"]

            def __getattr__(self, name):
                return getattr(self._store, name)
        # Given: a chat service on a storage that lists one category
        chat = ChatService(lambda event, payload: None, self.log, MoodTracker(os.path.join(ROOT, "moods.json")), lambda *a: "",
                           spawn=lambda target: target(), votes=OnlyService(self.storage), wall_clock=lambda: self.now)
        # When: a vote of another category and one of the listed one
        with self.assertRaises(ChatError) as caught:
            chat.vote("anna", "wave", "reactions", 1)
        chat.vote("anna", "voice", "service", 1)
        # Then: the storage's list decides, and the module has no copy
        self.assertEqual((caught.exception.code, caught.exception.rule), ("invalid_vote", "category"))
        self.assertEqual(chat.score()["categories"], {"service": 1})
        self.assertFalse(hasattr(chat_service, "CATEGORIES"))

    @unittest.skipUnless(A59_INSTALLED, "waits for amendment A-59 (IF-102 v2, categories())")
    @mark.req("REQ-CHA-015", "IF-102")
    def test_the_chat_service_votes_on_the_if_102_mock(self):
        """D-162: the IF-102 mock offers categories() too, so the chat service runs on it.
        Example: a vote "service" +1 on the mock gives the score {"answer_quality": 0, "reactions": 0, "character_behaviour": 0, "service": 1}."""
        mocks = os.path.join(ROOT, "tests", "helpers", "mocks")
        sys.path.insert(0, mocks)          # only for this import: the mocks have a graph_rules of their own, which must not shadow the real one
        try:
            from if_102_storage import StorageMock
        finally:
            sys.path.remove(mocks)
        # Given: a chat service on the mock of IF-102
        chat = ChatService(lambda event, payload: None, self.log, MoodTracker(os.path.join(ROOT, "moods.json")), lambda *a: "",
                           spawn=lambda target: target(), votes=StorageMock(), wall_clock=lambda: self.now)
        # When: one vote
        chat.vote("anna", "voice", "service", 1)
        # Then: the four categories are scored
        self.assertEqual(chat.score()["categories"], {"answer_quality": 0, "reactions": 0, "character_behaviour": 0, "service": 1})

    @mark.req("REQ-CHV-006")
    @mark.req("REQ-CHA-015")
    def test_a_minus_makes_the_character_shocked(self):
        """REQ-CHV-006 (D-137, D-143): every stored minus, in any category, lets the character react `shocked`; a plus or a refused vote does not.

        Example: plus on the answer -> no reaction; minus on the service -> react("shocked"); minus with value 5 -> refused, no reaction
        """
        # Given a service whose character reactions are recorded
        reactions = []
        self.chat._react = reactions.append
        answer = self.answer()
        # When a plus, a minus and a refused minus arrive
        self.chat.vote("anna", answer, "answer_quality", 1)
        self.chat.vote("ben", "voice", "service", -1)
        code_of(lambda: self.chat.vote("ben", "voice", "service", 5))
        # Then only the stored minus gives the shocked reaction
        self.assertEqual(reactions, ["shocked"])

    def test_regenerate_asks_again_for_the_last_answer_only(self):
        """TC-IF-201-05: a new try of the last answer, the old answer stays; an older answer or an unknown id is refused."""
        first = self.answer("q1")
        last = self.answer("q2")
        self.assertEqual(code_of(lambda: self.chat.regenerate("anna", first)), ("not_the_last_answer", None))
        self.assertEqual(code_of(lambda: self.chat.regenerate("anna", "nope")), ("not_found", None))
        user = [m for m in self.log.history()[0] if m["role"] == "user"][0]["id"]
        self.assertEqual(code_of(lambda: self.chat.regenerate("anna", user)), ("not_the_last_answer", None))      # a known message that is no answer: 422 like the mock, not 404
        result = self.chat.regenerate("anna", last)
        self.assertEqual(result["position"], 1)
        self.assertEqual(self.asked, ["[anna] q1", "[anna] q2", "[anna] q2"])
        self.assertEqual(len([m for m in self.log.history()[0] if m["role"] == "assistant"]), 3)
        self.assertEqual(len([m for m in self.log.history()[0] if m["role"] == "user"]), 2)        # the question is not stored twice

    def test_speak_again_gives_one_audio_chunk_per_sentence(self):
        """TC-IF-201-06: speak_again of any answer; a message that is no answer is not_found."""
        answer = self.answer()
        user = [m for m in self.log.history()[0] if m["role"] == "user"][0]["id"]
        self.events.clear()
        self.assertEqual(self.chat.speak_again(answer), {"sentences": 2})
        self.assertEqual([p["index"] for e, p in self.events if e == "audio_chunk"], [0, 1])
        self.assertEqual(code_of(lambda: self.chat.speak_again(user)), ("not_found", None))

    def test_the_account_lists_plain_steps_in_order(self):
        """TC-IF-201-06: the plain steps of the pipeline events kept with the answer; an answer without steps still gives one."""
        answer = self.answer()
        record = self.log.last("assistant")
        steps = self.chat.account(answer)
        self.assertEqual([s["seq"] for s in steps], list(range(1, len(steps) + 1)))
        self.assertTrue(all(isinstance(s["plain"], str) and s["plain"] for s in steps))
        self.assertEqual(code_of(lambda: self.chat.account("nope")), ("not_found", None))
        self.assertEqual(record["id"], answer)

    def test_the_account_uses_the_pipeline_events_of_the_answer(self):
        self.log.append("assistant", "Hello.", id="a1", pipeline=[{"kind": "start", "plain": "Read the question."}, {"kind": "event", "plain": ""},
                                                                  {"kind": "end", "plain": "Answered."}])
        self.assertEqual(self.chat.account("a1"), [{"seq": 1, "plain": "Read the question."}, {"seq": 2, "plain": "Answered."}])


if __name__ == "__main__":
    unittest.main()
