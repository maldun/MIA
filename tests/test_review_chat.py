"""TC-WFM-019, -028 (REQ-WFM-019, -028): the review as a chat task, with scripted skills, a fake scholar and a scripted user: the keywords are shown and may be replaced, the full text is
read only after a yes, a no ends the run with the report as it stands, the report names the person who has to check the summary. Run: python tests/test_review_chat.py"""
import datetime
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import review_chat as rc
import scholar

TODAY = datetime.date(2026, 10, 28)
TEXT = "Graph methods for scheduling in practice."


def work(doi, title, date="2020-05-01"):
    return scholar.new_work("test", doi=doi, title=title, date=date, year=int(date[:4]), abstract=TEXT, oa_url="https://oa.example/" + doi)


class FakeScholar:
    def __init__(self, works):
        self.works, self.queries = works, []

    def search(self, query, limit=None, until=None, since=None, check_retraction=False):
        self.queries.append((query, until, check_retraction))
        return {"works": [dict(w) for w in self.works], "errors": {}, "counts": {}, "dropped": [], "merged": 0}


def skills(calls):
    def run_skill(name, inputs):
        calls.append(name)
        if name == "review_keywords":
            return {"concepts": [{"name": "m", "keywords": ["graph colouring", "timetabling"]}], "criteria": [{"code": "outdated", "text": "too old"}]}
        if name == "review_abstract":
            return {"grade": 3, "decision": "include", "reason": "", "quote": "Graph methods for scheduling", "statement": "on topic"}
        if name == "review_summary":
            return {"found": [{"point": "colouring works", "works": ["10.1/a"]}], "coverage": "thin", "gaps": []}
        raise AssertionError("unexpected skill " + name)
    return run_skill


class Conversation:
    """the scripted user: replies in order; the questions are kept"""

    def __init__(self, *replies):
        self.replies, self.questions = list(replies), []

    def __call__(self, text):
        self.questions.append(text)
        return self.replies.pop(0) if self.replies else None


def review(user, works=None, text="How to schedule? until 2026-01-01", **kwargs):
    calls, events, searcher = [], [], FakeScholar(works if works is not None else [work("10.1/a", "Colouring")])
    out = rc.run_review(text, skills(calls), searcher, kwargs.pop("full_text", lambda w: None), user, on_event=events.append, today=TODAY, **kwargs)
    return out, calls, events, searcher


class TestReviewChat(unittest.TestCase):
    def test_the_keywords_are_shown_first_and_a_yes_starts_the_search(self):
        user = Conversation("yes", "no")
        out, calls, events, searcher = review(user)
        self.assertIn("- graph colouring", user.questions[0])
        self.assertIn("- timetabling", user.questions[0])
        self.assertEqual([q for q, _u, _c in searcher.queries], ['"graph colouring"', '"timetabling"'])
        self.assertEqual({u for _q, u, _c in searcher.queries}, {datetime.date(2026, 1, 1)})     # the cut-off of the request goes to the search
        self.assertTrue(all(c for _q, _u, c in searcher.queries))                                 # retraction is checked
        self.assertTrue(out.startswith("## Literature review"))

    def test_the_user_can_replace_the_keywords(self):
        _out, _calls, _events, searcher = review(Conversation("alpha, beta", "no"))
        self.assertEqual([q for q, _u, _c in searcher.queries], ['"alpha"', '"beta"'])

    def test_a_no_before_the_search_searches_nothing(self):
        out, calls, _events, searcher = review(Conversation("no"))
        self.assertEqual(searcher.queries, [])
        self.assertEqual(calls, ["review_keywords"])
        self.assertIn("cancelled", out)

    def test_the_full_text_is_read_only_after_a_yes_at_the_checkpoint(self):
        opened = []
        user = Conversation("yes", "no")
        review(user, full_text=lambda w: opened.append(w["doi"]))
        self.assertEqual(opened, [])
        self.assertIn("Recommendation", user.questions[1])
        self.assertIn("Read the full texts", user.questions[1])
        user = Conversation("yes", "yes")
        review(user, full_text=lambda w: opened.append(w["doi"]))
        self.assertEqual(opened, ["10.1/a"])

    def test_a_no_at_the_checkpoint_gives_the_report_as_it_stands_without_a_summary(self):
        out, calls, _events, _s = review(Conversation("yes", "no"))
        self.assertIn("Ended by:** user", out)
        self.assertIn("**Colouring**", out)
        self.assertNotIn("review_summary", calls)
        self.assertNotIn("Summary", out)

    def test_nobody_answering_is_a_no(self):
        out, _calls, _events, _s = review(Conversation("yes"))                  # ask gives None after the first reply
        self.assertIn("Ended by:** user", out)

    def test_the_summary_says_a_person_has_to_check_it(self):
        out, _calls, _events, _s = review(Conversation("yes", "yes"))
        self.assertIn("a person has to check it against the sources", out)
        self.assertIn("colouring works (10.1/a)", out)
        self.assertIn("**Coverage of the question: thin.**", out)

    def test_a_date_in_the_future_is_refused_in_plain_words(self):
        out, calls, _events, _s = review(Conversation("yes"), text="How to schedule? until 2030-01-01")
        self.assertIn("cannot start the review", out)
        self.assertEqual(calls, [])

    def test_the_stages_are_reported_as_steps(self):
        _out, _calls, events, _s = review(Conversation("yes", "no"))
        self.assertEqual(events[0], {"kind": "run_start", "payload": {"show": True}})
        plain = [e["plain"] for e in events if e["kind"] == "step"]
        self.assertEqual(plain[0], "choosing keywords")
        self.assertIn("searching for graph colouring", plain)
        self.assertIn("reading the abstract: Colouring", plain)
        self.assertEqual(plain[-1], "writing the report")


class TestVoice(unittest.TestCase):
    """the voice (owner 2026-10-28): the questions are spoken before the review waits, and a short result at the end; never the whole markdown report"""

    def test_the_keywords_question_is_spoken_plainly(self):
        said = rc.spoken_keywords(["graph colouring", "timetabling"])
        self.assertEqual(said, "I will search for these keywords: graph colouring, timetabling. Shall I start? Say yes, or send your own list.")
        many = rc.spoken_keywords(["keyword %d" % i for i in range(30)])
        self.assertIn("keyword 7", many)                                   # at most 8 are read
        self.assertNotIn("keyword 8", many)

    def test_the_checkpoint_and_limit_questions(self):
        report = {"flow": {"found": 9, "duplicates": 2, "dropped": 1, "screened": 6, "included": 4, "maybe": 1, "excluded_abstract": 1, "excluded_full": 0, "undecided": 0},
                  "recommendation": {"action": "continue", "why": "two items are open"}, "asking": "checkpoint"}
        said = rc.spoken_checkpoint(report)
        self.assertIn("6 works", said)
        self.assertIn("4 included", said)
        self.assertIn("I recommend to continue", said)
        self.assertTrue(said.endswith("Shall I read the full texts?"))
        self.assertEqual(rc.spoken_checkpoint({**report, "asking": "limit:seconds"}), "The limit seconds is used up. Shall I continue?")

    def test_the_terms_question(self):
        self.assertEqual(rc.spoken_terms([{"term": "bipartite", "works": 4}, {"term": "matching", "works": 3}]),
                         "These terms occur in several works: bipartite, matching. Shall I search for them too?")

    def test_the_result_is_short_and_says_where_the_report_is(self):
        report = {"ended_by": "complete", "flow": {"found": 9, "included": 4},
                  "summary": {"coverage": "The literature covers the question in part. A second sentence.", "figures": {"level": "moderate", "included": 4}}}
        said = rc.spoken_result(report)
        self.assertEqual(said, "The review is done. I found 9 works and included 4. Coverage of your question is moderate. The report is in the chat, please check the summary against the sources.")
        stopped = rc.spoken_result({"ended_by": "user", "flow": {"found": 9, "included": 1}})
        self.assertEqual(stopped, "I stopped the review. I found 9 works and included 1. The report is in the chat as it stands.")

    def test_the_questions_and_the_result_are_spoken_in_order_and_only_when_a_voice_is_given(self):
        said = []
        review(Conversation("yes", "yes"), speak=said.append)
        self.assertTrue(said[0].startswith("I will search for these keywords: graph colouring, timetabling."))
        self.assertIn("Shall I read the full texts?", said[1])
        self.assertTrue(said[-1].startswith("The review is done."))
        self.assertEqual(len(said), 3)
        review(Conversation("yes", "no"))                                  # no voice: nothing happens, nothing fails

    def test_a_voice_that_fails_does_not_take_the_report_away(self):
        def broken(text):
            raise RuntimeError("no speaker")
        out, _calls, _events, _s = review(Conversation("yes", "yes"), speak=broken)
        self.assertTrue(out.startswith("## Literature review"))


class CardMonitor:
    def __init__(self):
        self.phases, self.budget, self.counts = [], {}, {}

    def update(self, phase=None, budget=None, counts=None):
        if phase:
            self.phases.append(phase)
        for name, figures in (budget or {}).items():
            self.budget.setdefault(name, {}).update(figures)
        self.counts.update(counts or {})


class TestReviewCard(unittest.TestCase):                                         # TC-WFM-031, -032, -034
    def test_the_card_gets_phases_counts_and_the_used_calls_and_tokens(self):
        card = CardMonitor()
        review(Conversation("yes", "no"), monitor=card)
        self.assertEqual(card.phases[0], "choosing keywords")
        self.assertIn("searching for graph colouring", card.phases)
        self.assertEqual((card.counts["on_list"], card.counts["processed"], card.counts["to_process"], card.counts["included"]), (1, 1, 0, 1))
        self.assertEqual(card.budget["calls"]["used"], 2)                        # the keywords and one abstract
        self.assertGreater(card.budget["tokens"]["used"], 0)
        self.assertEqual(card.budget["api_requests"]["used"], 2)

    def test_the_mode_run_has_caps_of_ten_times_the_limits_and_the_option_slice_brings_the_limits_back(self):
        card = CardMonitor()
        review(Conversation("yes", "no"), monitor=card)
        self.assertEqual((card.budget["screen"]["limit"], card.budget["seconds"]["limit"]), (400, 600))
        card = CardMonitor()
        review(Conversation("yes", "no"), monitor=card, options={"slice": True})
        self.assertEqual((card.budget["screen"]["limit"], card.budget["seconds"]["limit"]), (40, 60))
        card = CardMonitor()
        review(Conversation("yes", "no"), monitor=card, options={"cap_factor": 2})
        self.assertEqual(card.budget["screen"]["limit"], 80)

    def test_a_cap_factor_below_one_is_refused_and_nothing_is_asked(self):
        user = Conversation("yes")
        out, _calls, _events, _s = review(user, options={"cap_factor": 0})
        self.assertIn("cannot start", out)
        self.assertEqual(user.questions, [])


if __name__ == "__main__":
    unittest.main()
