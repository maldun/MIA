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


if __name__ == "__main__":
    unittest.main()
