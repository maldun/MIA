"""Chat agent N-2.2 T-06: a minus on a fact opens a case (TC-CHA-016), adaptation to negative feedback (TC-CHA-017), counters visible and resettable (TC-CHA-018).
A fact is an answer with at least one reputable source (owner 2026-10-27); a behaviour is a named item of `character_behaviour` (the list is data and may change).
Run with: python tests/test_chat_behaviour.py"""
import os
import random
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                  # noqa: E402
from chat_log import ChatLog                              # noqa: E402
from chat_service import ChatService, ChatError, behaviours_from_file, show_chance   # noqa: E402
from moods import MoodTracker                             # noqa: E402
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402

START = 1767571200          # 2026-01-05 00:00 UTC
BEHAVIOURS = ["wave", "calm"]
GOOD, WEAK = {"url": "https://www.who.int/x", "trust": 0.85}, {"url": "https://someblog.example/p", "trust": 0.3}


def code_of(call):
    try:
        call()
    except ChatError as err:
        return err.code, err.rule
    raise AssertionError("no ChatError raised")


class BehaviourTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.now, self.events, self.sources = START, [], []
        self.storage = Storage(FileBackend(os.path.join(self.dir, "db")))
        self.log = ChatLog(os.path.join(self.dir, "log.jsonl"))

        def exchange(text, on_delta, on_emotion, should_stop):
            self.chat.note_sources(self.sources)                        # what the lookup skill reports: the sources behind the answer
            return "Paris is the capital of France."

        self.chat = ChatService(lambda e, p: self.events.append((e, p)), self.log, MoodTracker(os.path.join(ROOT, "moods.json")), exchange, queue_size=5, user_limit=2,
                                spawn=lambda target: target(), votes=self.storage, wall_clock=lambda: self.now, behaviours=lambda: BEHAVIOURS, reputable=0.6)

    def answer(self, sources, text="capital of France?"):
        self.sources = sources
        self.chat.send(text, author="anna")
        return self.log.last("assistant")["id"]

    # --- TC-CHA-016 ---------------------------------------------------------------------------------------
    @mark.req("REQ-CHA-016")
    def test_a_minus_on_a_fact_opens_one_case_and_leaves_the_answer_alone(self):
        """TC-CHA-016: the answer has a reputable source, so it counts as a fact: the minus proposes one case and the stored text is unchanged (exact)."""
        answer = self.answer([WEAK, GOOD])
        before = self.log.last("assistant")
        self.chat.vote("anna", answer, "answer_quality", -1)
        self.chat.vote("ben", answer, "answer_quality", -1)                  # another user, the same answer: still one case
        self.chat.vote("anna", answer, "answer_quality", -1)                 # a repeat changes nothing
        self.assertEqual(self.log.last("assistant"), before)
        self.assertEqual(self.storage.ids("cases"), [answer])
        case = self.storage.get("cases", answer)["doc"]
        self.assertEqual((case["question"], case["answer"], case["status"]), ("capital of France?", "Paris is the capital of France.", "proposed"))
        self.assertEqual(case["voters"], ["anna", "ben"])
        self.assertEqual([s["url"] for s in case["sources"]], [WEAK["url"], GOOD["url"]])

    @mark.req("REQ-CHA-016")
    def test_no_case_without_a_fact_or_without_a_minus(self):
        """An answer whose sources are all weak, an answer without sources, a plus, and a minus in another category open no case."""
        weak, none, fact = self.answer([WEAK]), self.answer([]), self.answer([GOOD])
        self.chat.vote("anna", weak, "answer_quality", -1)
        self.chat.vote("anna", none, "answer_quality", -1)
        self.chat.vote("anna", fact, "answer_quality", 1)
        self.chat.vote("anna", "voice", "service", -1)
        self.assertEqual(self.storage.ids("cases"), [])

    @mark.req("REQ-CHA-016")
    def test_the_threshold_is_the_trust_of_the_best_source(self):
        """Reputable means a trust of at least the configured value: exactly at the bound counts."""
        self.assertEqual(self.chat.is_fact({"sources": [{"url": "u", "trust": 0.6}]}), True)
        self.assertEqual(self.chat.is_fact({"sources": [{"url": "u", "trust": 0.59}]}), False)
        self.assertEqual(self.chat.is_fact({}), False)

    # --- TC-CHA-017 ---------------------------------------------------------------------------------------
    @mark.req("REQ-CHA-017")
    def test_five_net_negative_votes_make_the_behaviour_rare_and_positive_votes_bring_it_back(self):
        """TC-CHA-017: after 5 net negative votes the chance is at most 1 %, in 1000 opportunities it appears at most 10 times (20 fresh seeds); a plus raises it again."""
        for user in ("u1", "u2", "u3", "u4"):
            self.chat.vote(user, "wave", "character_behaviour", -1)
        self.assertEqual(self.chat.counters()["wave"]["chance"], 1.0)         # 4 net negative votes: not yet
        self.chat.vote("u5", "wave", "character_behaviour", -1)
        chance = self.chat.counters()["wave"]["chance"]
        self.assertLessEqual(chance, 0.01)
        for seed in range(20):
            rng = random.Random(seed)
            shown = sum(1 for _ in range(1000) if self.chat.show_behaviour("wave", rng=rng.random))
            self.assertLessEqual(shown, 10, "seed %d" % seed)
        self.assertTrue(all(self.chat.show_behaviour("calm", rng=lambda: 0.999) for _ in range(5)))     # another behaviour is untouched
        self.chat.vote("u6", "wave", "character_behaviour", 1)
        self.assertEqual(self.chat.counters()["wave"]["chance"], 1.0)

    @mark.req("REQ-CHA-017")
    def test_the_chance_is_a_function_of_the_net_votes(self):
        self.assertEqual([show_chance(n) for n in (3, 0, -4)], [1.0, 1.0, 1.0])
        self.assertTrue(all(0 < show_chance(n) <= 0.01 for n in (-5, -6, -50)))

    @mark.req("REQ-CHA-017")
    def test_a_behaviour_is_a_named_item_of_the_list(self):
        """Only the names of the list can be voted on in `character_behaviour`; the list is read every time, so a new name works at once; nothing is stored for a refused vote."""
        self.assertEqual(code_of(lambda: self.chat.vote("anna", "dance", "character_behaviour", -1)), ("invalid_vote", "subject"))
        self.assertEqual(self.storage.ids("votes"), [])
        BEHAVIOURS.append("dance")
        self.addCleanup(BEHAVIOURS.remove, "dance")
        self.assertTrue(self.chat.vote("anna", "dance", "character_behaviour", -1)["stored"])
        self.assertEqual(self.chat.counters()["dance"]["net"], -1)

    # --- TC-CHA-018 ---------------------------------------------------------------------------------------
    @mark.req("REQ-CHA-018")
    def test_counters_are_visible_and_a_reset_restores_the_default_rate(self):
        """TC-CHA-018: every behaviour has a counter (net, votes, chance); a reset by any user restores the default rate and announces it; the votes stay in the table."""
        counters = self.chat.counters()
        self.assertEqual(sorted(counters), sorted(BEHAVIOURS))
        self.assertEqual(counters["wave"], {"net": 0, "votes": 0, "chance": 1.0, "reset_at": None})
        for user in ("u1", "u2", "u3", "u4", "u5"):
            self.chat.vote(user, "wave", "character_behaviour", -1)
        self.assertEqual(self.chat.counters()["wave"]["net"], -5)
        self.now += 60
        self.events.clear()
        result = self.chat.reset_counter("ben", "wave")
        self.assertEqual((result["net"], result["chance"], result["votes"]), (0, 1.0, 0))
        self.assertEqual(self.events, [("counters_changed", {"name": "wave", "author": "ben"})])
        self.assertEqual(len(self.storage.ids("votes")), 5)                    # the history of the votes is kept
        self.assertEqual(self.chat.counters()["wave"]["chance"], 1.0)
        self.now += 60
        self.chat.vote("u1", "wave", "character_behaviour", -1)                # counts again from the reset on (u1 changed their earlier minus: a new version)
        self.assertEqual(self.chat.counters()["wave"]["net"], -1)
        self.assertEqual(code_of(lambda: self.chat.reset_counter("ben", "nope")), ("not_found", None))

    @mark.req("REQ-CHA-018")
    def test_a_vote_on_a_fact_leaves_the_counters_unchanged(self):
        """TC-CHA-018: only `character_behaviour` votes move counters; the answer (a fact) and the other categories do not, and a fact is no behaviour that can be reset or adapted."""
        answer = self.answer([GOOD])
        before = self.chat.counters()
        self.chat.vote("anna", answer, "answer_quality", -1)
        self.chat.vote("anna", "voice", "service", -1)
        self.chat.vote("anna", "wave", "reactions", -1)
        self.assertEqual(self.chat.counters(), before)
        self.assertEqual(code_of(lambda: self.chat.reset_counter("anna", answer)), ("not_found", None))
        self.assertTrue(self.chat.show_behaviour(answer, rng=lambda: 0.999))   # what is not a behaviour is always shown

    @mark.req("REQ-CHA-018")
    def test_the_counters_survive_a_restart(self):
        """The counters are a table of the database: a new service on the same store sees them."""
        for user in ("u1", "u2", "u3", "u4", "u5"):
            self.chat.vote(user, "calm", "character_behaviour", -1)
        again = ChatService(lambda e, p: None, self.log, MoodTracker(os.path.join(ROOT, "moods.json")), lambda *a: "", votes=self.storage, behaviours=lambda: BEHAVIOURS)
        self.assertEqual(again.counters()["calm"]["net"], -5)

    @mark.req("REQ-CHA-017")
    def test_the_list_comes_from_a_file_that_may_change(self):
        """the file is read at every call; a missing or broken file is an empty list, not a crash"""
        path = os.path.join(self.dir, "behaviours.json")
        read = behaviours_from_file(path)
        self.assertEqual(read(), [])
        for text, expected in (('{"behaviours": ["wave", "calm"]}', ["wave", "calm"]), ('{"behaviours": ["wave", "calm", "dance", 5]}', ["wave", "calm", "dance"]),
                               ("{broken", []), ('{"behaviours": "wave"}', [])):
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(text)
            self.assertEqual(read(), expected)


if __name__ == "__main__":
    unittest.main()
