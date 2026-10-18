"""
Tests for the hard checks: quote in source, arithmetic (two evaluators, no eval), units, calendar facts, schema, schedule overlap, citation and web confirmation (with fake search
and fetch), the combination rule, and the dispatcher on top of the library. Run with the MIA virtualenv: python tests/test_checks.py
"""
import json
import os
import random
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import checks as C                                    # noqa: E402
import web_tools as W                                 # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402
from pipeline import Tool                             # noqa: E402

PASS, FAIL, INC, NA = C.PASS, C.FAIL, C.INCONCLUSIVE, C.NOT_APPLICABLE
SOURCE = ("The Eiffel Tower is 330 metres tall, including its antennas. It was completed in 1889 for the World's Fair in Paris.\n\n"
          "“We shall build a tower”, said Eiffel, – and so it was.")


class QuoteTests(unittest.TestCase):
    def status(self, quote, source=SOURCE, **kw):
        return C.quote_in_source(quote, source, **kw)["status"]

    def test_exact_and_normalised(self):
        self.assertEqual(self.status("330 metres tall"), PASS)
        self.assertEqual(self.status("THE EIFFEL   TOWER\nIS 330 METRES TALL"), PASS)                       # case and spaces
        self.assertEqual(self.status("We shall build a tower, said Eiffel, - and so it was"), PASS)           # curly quotes, en dash
        self.assertEqual(self.status("World’s Fair"), PASS)                                              # typographic apostrophe
        self.assertEqual(self.status("“we shall build a tower”"), PASS)                             # quotes around the quote
        self.assertEqual(self.status("ﬁnished", "it was finished"), PASS)                                     # ligature
        self.assertEqual(self.status("Straße", "Die Straße ist lang"), PASS)
        self.assertEqual(self.status("Case Matters", "case matters", ignore_case=False), FAIL)

    def test_ellipsis_skips_text_in_order(self):
        self.assertEqual(self.status("Eiffel Tower is 330 metres ... completed in 1889"), PASS)
        self.assertEqual(self.status("Eiffel Tower [...] World's Fair"), PASS)
        self.assertEqual(self.status("completed in 1889 … Eiffel Tower"), FAIL)                          # wrong order
        self.assertEqual(self.status("Eiffel Tower is ... nowhere to be found here"), FAIL)

    def test_absent_near_and_unusable(self):
        self.assertEqual(self.status("The Eiffel Tower is 300 metres tall, including its antennas."), INC)    # one word differs: not exact
        near = C.quote_in_source("The Eiffel Tower is 300 metres tall, including its antennas.", SOURCE)
        self.assertIn("330 metres", near["evidence"][0]["closest"])
        self.assertIn("not exact", near["detail"])
        self.assertEqual(self.status("The Colosseum is in Rome"), FAIL)
        self.assertEqual(self.status("Paris is the capital of Germany and was built in 1889 by Eiffel"), FAIL)
        for bad in ("", "ab", None, 5):
            self.assertEqual(self.status(bad), NA)
        self.assertEqual(C.quote_in_source("a long quote here", None)["status"], NA)

    def test_long_sources_are_fast(self):
        rng = random.Random(1)
        words = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", "iota", "kappa"]
        big = " ".join(rng.choice(words) for _ in range(20000))
        started = time.time()
        self.assertEqual(C.quote_in_source("alpha beta zzz gamma delta epsilon zeta eta theta iota kappa alpha", big)["status"], FAIL)
        self.assertLess(time.time() - started, 15)


class NumberTests(unittest.TestCase):
    def test_arithmetic(self):
        for expression, value, expected in (("12*1.5+3", 21, PASS), ("2**10", "1,024", PASS), ("2+2", 5, FAIL), ("(1+2)*3", 9, PASS), ("10/4", 2.5, PASS),
                                            ("7//2", 3, PASS), ("7%4", 3, PASS), ("-3+5", 2, PASS), ("2^3", 8, PASS), ("6×7", 42, PASS), ("sqrt(16)+abs(-2)", 6, PASS),
                                            ("pi*2", 6.28, PASS), ("pi*2", 6.0, FAIL), ("0.1+0.2", 0.3, PASS), ("1000*1.07", "1,070", PASS), ("100/3", 33.3, PASS),
                                            ("100/3", 33, PASS), ("100/3", 34, FAIL), ("100/3", "33.33", PASS)):
            self.assertEqual(C.arithmetic_claim(expression, value)["status"], expected, "%s = %s" % (expression, value))

    def test_rounding_the_claim_shows_is_allowed_but_not_more(self):
        self.assertEqual(C.arithmetic_claim("22/7", "3.14")["status"], PASS)        # 3.142857 shown with two decimals
        self.assertEqual(C.arithmetic_claim("22/7", "3.1")["status"], PASS)         # half a unit of the first decimal is 0.05, 1.6 percent
        self.assertEqual(C.arithmetic_claim("22/7", "3")["status"], FAIL)           # rounding to a whole number would explain 0.5, but only 2 percent (0.06) may be explained by rounding
        self.assertEqual(C.arithmetic_claim("1000/3", "333")["status"], PASS)       # a large number rounded to a whole number is fine
        self.assertEqual(C.arithmetic_claim("1000/3", "330")["status"], FAIL)

    def test_nothing_is_evaluated_that_is_not_arithmetic(self):
        for bad in ("__import__('os').system('echo hi')", "open('/etc/passwd')", "[1,2,3]", "x+1", "2 ** 100000000", "9**9**9", "1/0", "(-1)**0.5", "sqrt(-4)",
                    "().__class__", "lambda: 1", "1; 2", "", "a" * 500, "2" + "*2" * 100, "(" * 300 + "1" + ")" * 300, "True+1"):
            outcome = C.arithmetic_claim(bad, 1)
            self.assertEqual(outcome["status"], NA, bad[:40])

    def test_claimed_value_must_be_a_number(self):
        self.assertEqual(C.arithmetic_claim("1+1", "two")["status"], NA)
        self.assertEqual(C.arithmetic_claim("1+1", None)["status"], NA)
        self.assertEqual(C.arithmetic_claim("1+1", True)["status"], NA)

    def test_number_formats(self):
        for text, expected in (("1,234.5", 1234.5), ("1.234,5", 1234.5), ("3,5", 3.5), ("1,234", 1234.0), ("1.234.567", 1234567.0), ("-2.5", -2.5), ("1 000", 1000.0), (7, 7.0)):
            self.assertEqual(C.parse_number(text), expected, text)
        with self.assertRaises(ValueError):
            C.parse_number("abc")

    def test_units(self):
        for args, expected in (((5, "km", "mi", 3.1), PASS), ((5, "km", "mi", 3), FAIL), ((100, "C", "F", 212), PASS), ((0, "celsius", "K", 273.15), PASS), ((32, "°F", "C", 0), PASS),
                               ((1, "kg", "lb", 2.2), PASS), ((1, "kg", "lb", 2.0), FAIL), ((330, "m", "ft", 1083), PASS), ((1, "mile", "km", 1.6), PASS), ((60, "mph", "km/h", 96.6), PASS),
                               ((1, "GiB", "MB", 1073.7), PASS), ((2, "hours", "min", 120), PASS), ((1, "gal", "l", 3.8), PASS), ((1, "atm", "kPa", 101.3), PASS),
                               ((1, "kWh", "kJ", 3600), PASS), ((5, "km", "kg", 3), NA), ((5, "parsec", "mi", 3), NA), (("x", "km", "mi", 3), NA)):
            self.assertEqual(C.unit_conversion(*args)["status"], expected, args)


class DateTests(unittest.TestCase):
    def test_calendar_facts(self):
        cases = [(dict(kind="weekday", date="2024-02-29", weekday="Thursday"), PASS), (dict(kind="weekday", date="2024-02-29", weekday="Friday"), FAIL),
                 (dict(kind="weekday", date="29.02.2024", weekday="donnerstag"), PASS), (dict(kind="weekday", date="February 29, 2024", weekday="Thu"), PASS),
                 (dict(kind="weekday", date="29 February 2024", weekday="Do"), PASS),
                 (dict(kind="days_between", start="2024-01-01", end="2024-12-31", days=365), PASS), (dict(kind="days_between", start="2024-01-01", end="2024-12-31", days=366), FAIL),
                 (dict(kind="add_days", start="2024-02-28", days=2, result_date="2024-03-01"), PASS), (dict(kind="add_days", start="2023-02-28", days=2, result_date="2023-03-01"), FAIL),
                 (dict(kind="age", birth="1990-05-17", on="2026-05-17", years=36), PASS), (dict(kind="age", birth="1990-05-17", on="2026-05-16", years=36), FAIL),
                 (dict(kind="leap_year", year=2000, leap=True), PASS), (dict(kind="leap_year", year=1900, leap=True), FAIL), (dict(kind="leap_year", year="2024", leap=True), PASS),
                 (dict(kind="order", a="2024-01-01", b="2024-01-02", relation="before"), PASS), (dict(kind="order", a="2024-01-01", b="2024-01-02", relation="after"), FAIL),
                 (dict(kind="order", a="2024-01-01", b="2024-01-01", relation="same"), PASS)]
        for kwargs, expected in cases:
            self.assertEqual(C.date_claim(**kwargs)["status"], expected, kwargs)

    def test_unreadable_data_is_not_applicable(self):
        for kwargs in (dict(kind="weekday", date="2023-02-30", weekday="Monday"), dict(kind="weekday", date="soon", weekday="Monday"), dict(kind="weekday", date="2024-01-01", weekday="Funday"),
                       dict(kind="days_between", start="2024-01-01", end="2024-01-05", days="many"), dict(kind="teleport"), dict(kind="age", birth="1990-05-17", on=None, years=1),
                       dict(kind="weekday")):
            self.assertEqual(C.date_claim(**kwargs)["status"], NA, kwargs)

    def test_detail_names_the_right_answer(self):
        self.assertIn("Thursday", C.date_claim("weekday", date="2024-02-29", weekday="Friday")["detail"])


class StructureTests(unittest.TestCase):
    def test_schema(self):
        schema = {"type": "object", "required": ["a"], "properties": {"a": {"type": "integer", "minimum": 1}}}
        self.assertEqual(C.schema_valid({"a": 2}, schema)["status"], PASS)
        failed = C.schema_valid({"a": 0}, schema)
        self.assertEqual((failed["status"], failed["evidence"][0]["problems"][0]), (FAIL, "$.a: below 1"))
        self.assertEqual(C.schema_valid({"a": 1}, "no schema")["status"], NA)

    def test_schedule(self):
        ok = [{"name": "A", "start": "09:00", "end": "10:00"}, {"name": "B", "start": "10:00", "end": "11:00"}, {"name": "C", "start": "2000-01-01T11:30", "end": "12:00"}]
        self.assertEqual(C.schedule_overlap(ok)["status"], PASS)
        self.assertEqual(C.schedule_overlap(ok, allow_touching=False)["status"], FAIL)
        clash = C.schedule_overlap([{"name": "A", "start": "09:00", "end": "10:30"}, {"name": "B", "start": "10:00", "end": "11:00"}])
        self.assertEqual((clash["status"], clash["evidence"]), (FAIL, [{"first": "A", "second": "B"}]))
        self.assertEqual(C.schedule_overlap([{"name": "A", "start": "11:00", "end": "10:00"}])["status"], FAIL)
        self.assertEqual(C.schedule_overlap([{"name": "A", "start": "later", "end": "10:00"}])["status"], NA)
        self.assertEqual(C.schedule_overlap("nothing")["status"], NA)
        unsorted = [{"name": "B", "start": "2026-05-01T10:00", "end": "2026-05-01T11:00"}, {"name": "A", "start": "2026-05-01T09:00", "end": "2026-05-01T09:30"}]
        self.assertEqual(C.schedule_overlap(unsorted)["status"], PASS)


class CombineTests(unittest.TestCase):
    def test_the_rule(self):
        r = lambda *s: [{"status": x} for x in s]            # noqa: E731
        self.assertEqual(C.combine(r(PASS, PASS)), {"status": "pass", "verdict": "supported"})
        self.assertEqual(C.combine(r(PASS, FAIL, INC)), {"status": "fail", "verdict": "contradicted"})     # a failed check decides
        self.assertEqual(C.combine(r(PASS, INC)), {"status": "open", "verdict": "open"})                      # a pass is evidence, not proof
        self.assertEqual(C.combine(r(INC)), {"status": "open", "verdict": "open"})
        self.assertEqual(C.combine(r(PASS, NA)), {"status": "pass", "verdict": "supported"})                  # not applicable does not count
        self.assertEqual(C.combine(r(NA, NA)), {"status": "not_applicable", "verdict": "none"})
        self.assertEqual(C.combine([]), {"status": "not_applicable", "verdict": "none"})


class FakeFetch:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        page = self.pages.get(url)
        if isinstance(page, Exception):
            raise page
        if page is None:
            raise W.HttpStatusError(404)
        return {"url": url, "title": page.get("title", ""), "text": page["text"], "clipped": page.get("clipped", False), "signals": page.get("signals", []),
                "content_type": "text/html"}


class CitationTests(unittest.TestCase):
    def check(self, pages, **kw):
        fetch = FakeFetch(pages)
        return C.make_citation_check(fetch)(**kw), fetch

    def test_statuses(self):
        page = {"https://a.example/x": {"title": "Eiffel Tower facts", "text": SOURCE}}
        self.assertEqual(self.check(page, url="https://a.example/x", quote="330 metres tall")[0]["status"], PASS)
        self.assertEqual(self.check(page, url="https://a.example/x", quote="the tower is 12 metres tall and green")[0]["status"], FAIL)
        self.assertEqual(self.check(page, url="https://a.example/x", quote="The Eiffel Tower is 300 metres tall, including its antennas.")[0]["status"], INC)
        self.assertEqual(self.check(page, url="https://a.example/x")[0]["status"], PASS)                         # no quote: the page exists
        self.assertEqual(self.check(page, url="https://a.example/x", title="Eiffel Tower facts")[0]["status"], PASS)
        outcome = self.check(page, url="https://a.example/x", title="Cooking pasta at home")[0]
        self.assertEqual(outcome["status"], INC)
        self.assertIn("title", outcome["detail"])

    def test_failures_and_doubts_when_the_page_cannot_be_read(self):
        kinds = [(W.HttpStatusError(404), FAIL), (W.HttpStatusError(410), FAIL), (W.HttpStatusError(503), INC), (W.HttpStatusError(429), INC), (W.WebError("timed out"), INC),
                 (W.UnsupportedContent("content type 'application/pdf' is not read"), INC), (W.UnsafeUrl("points to a private address"), FAIL)]
        for error, expected in kinds:
            self.assertEqual(self.check({"https://a.example/x": error}, url="https://a.example/x", quote="anything at all")[0]["status"], expected, repr(error))

    def test_search_pages_are_no_sources(self):
        for url in ("https://www.google.com/search?q=eiffel", "https://duckduckgo.com/?q=eiffel", "https://example.com/search?query=x", "https://www.bing.com/search?q=eiffel", "https://duckduckgo.com/"):
            outcome, fetch = self.check({}, url=url)
            self.assertEqual(outcome["status"], FAIL, url)
            self.assertEqual(fetch.calls, [])                                                                    # not even fetched
        self.assertEqual(self.check({}, url="")[0]["status"], NA)

    def test_a_clipped_page_cannot_prove_an_absence(self):
        pages = {"https://a.example/long": {"text": "Only the beginning of a very long article.", "clipped": True}}
        outcome = self.check(pages, url="https://a.example/long", quote="something that may be further down")[0]
        self.assertEqual(outcome["status"], INC)
        self.assertIn("clipped", outcome["detail"])

    def test_injection_signals_are_reported(self):
        pages = {"https://a.example/x": {"text": SOURCE, "signals": ["ignore all previous instructions"]}}
        outcome = self.check(pages, url="https://a.example/x", quote="330 metres")[0]
        self.assertEqual(outcome["evidence"][0]["signals"], ["ignore all previous instructions"])


class FakeSearch:
    def __init__(self, answers, fail=()):
        self.answers = answers          # query word (or "") -> list of results
        self.fail = fail
        self.queries = []

    def __call__(self, query, count=None, language=None, time_range=None):
        self.queries.append(query)
        if any(query.endswith(word) for word in self.fail):
            raise W.SearchError("no backend answered", ["x"])
        for suffix in sorted(self.answers, key=len, reverse=True):
            if suffix and query.endswith(" " + suffix):
                return {"results": self.answers[suffix]}
        return {"results": self.answers.get("", [])}


def hit(url, title="", snippet=""):
    return {"title": title, "url": url, "snippet": snippet}


class WebConfirmTests(unittest.TestCase):
    FACT = "The Eiffel Tower is 330 metres tall."

    def pages(self, **extra):
        pages = {"https://a.example/eiffel": {"title": "A", "text": "Facts: the Eiffel Tower measures 330 metres in height. " + "More text about Paris. " * 30},
                 "https://www.b.example.org/tower": {"title": "B", "text": "A guide to Paris. The Eiffel Tower, 330 metres high, opened in 1889. " + "Visitor information. " * 40},
                 "https://c.example.co.uk/x": {"title": "C", "text": "Other trivia about bridges only. " * 20}}
        pages.update(extra)
        return pages

    def run_check(self, search, pages, **kw):
        fetch = FakeFetch(pages)
        outcome = C.make_web_confirm(search, fetch)(**kw)
        return outcome, fetch

    def test_two_independent_sources_and_a_quiet_disconfirming_search_pass(self):
        search = FakeSearch({"": [hit("https://a.example/eiffel"), hit("https://www.b.example.org/tower"), hit("https://c.example.co.uk/x")]})
        outcome, fetch = self.run_check(search, self.pages(), entities=["Eiffel Tower", "330"])
        self.assertEqual(outcome["status"], PASS)
        self.assertEqual([s["domain"] for s in outcome["evidence"][0]["sources"]], ["a.example", "example.org"])
        self.assertIn("330", outcome["evidence"][0]["sources"][0]["passage"])
        self.assertEqual(search.queries, ["Eiffel Tower 330", "Eiffel Tower 330 myth", "Eiffel Tower 330 false"])      # built from the entities; two disconfirming searches
        self.assertEqual(outcome["evidence"][0]["calls"], {"searches": 3, "fetches": 3})

    def test_not_enough_independent_sources(self):
        search = FakeSearch({"": [hit("https://a.example/eiffel"), hit("https://a.example/other"), hit("https://c.example.co.uk/x")]})
        pages = self.pages(**{"https://a.example/other": {"title": "A2", "text": "The Eiffel Tower is 330 m tall, said another page of the same site."}})
        outcome, fetch = self.run_check(search, pages, entities=["Eiffel Tower", "330"])
        self.assertEqual(outcome["status"], INC)
        self.assertIn("1 of 2 independent sources", outcome["detail"])
        self.assertEqual(sum(1 for u in fetch.calls if "a.example" in u), 1)                                           # one domain is read once

    def test_mirrors_count_once(self):
        copy = self.pages()["https://a.example/eiffel"]
        pages = self.pages(**{"https://mirror.example/copy": dict(copy, title="Copy")})
        search = FakeSearch({"": [hit("https://a.example/eiffel"), hit("https://mirror.example/copy")]})
        outcome, _ = self.run_check(search, pages, entities=["Eiffel Tower", "330"])
        self.assertEqual(outcome["status"], INC)
        self.assertEqual(outcome["evidence"][0]["mirrors_ignored"], 1)
        self.assertIn("1 mirror", outcome["detail"])

    def test_a_correction_in_the_results_stops_the_pass(self):
        search = FakeSearch({"": [hit("https://a.example/eiffel"), hit("https://www.b.example.org/tower")],
                             "myth": [hit("https://debunk.example/1", "The Eiffel Tower 330 metres myth", "Many believe the Eiffel Tower is 330 metres, but this is a common misconception.")]})
        outcome, _ = self.run_check(search, self.pages(), entities=["Eiffel Tower", "330"])
        self.assertEqual(outcome["status"], INC)
        self.assertEqual(outcome["evidence"][0]["disputes"][0]["url"], "https://debunk.example/1")
        self.assertIn("correction or a debunking", outcome["detail"])
        search = FakeSearch({"": [hit("https://a.example/eiffel"), hit("https://www.b.example.org/tower")], "myth": [hit("https://x.example/", "Myths about Paris", "nothing about the tower numbers")]})
        self.assertEqual(self.run_check(search, self.pages(), entities=["Eiffel Tower", "330"])[0]["status"], PASS)    # a "myth" page without the fact is no dispute
        # a page about myths in general that mentions the fact in passing is no dispute either (found with the real search: the query word "myth" attracts such pages)
        passing = "The tower was inaugurated for the 1889 World's Fair in Paris and has been visited by millions since then, which is a lot of people. Here is the number one Parisian myth that never goes away."
        search = FakeSearch({"": [hit("https://a.example/eiffel"), hit("https://www.b.example.org/tower")], "myth": [hit("https://x.example/", "Parisian myths", passing)]})
        self.assertEqual(self.run_check(search, self.pages(), entities=["Eiffel Tower", "330"], facts=["330"])[0]["status"], PASS)
        near = "Many people think the tower was built in 1889 by Eiffel himself, which is a myth."
        search = FakeSearch({"": [hit("https://a.example/eiffel"), hit("https://www.b.example.org/tower")], "myth": [hit("https://x.example/", "Parisian myths", near)]})
        pages = self.pages(**{"https://a.example/eiffel": {"text": "The tower was built in 1889. " * 20}, "https://www.b.example.org/tower": {"text": "In 1889 the tower opened. " + "Paris. " * 40}})
        self.assertEqual(self.run_check(search, pages, entities=["tower", "1889"], facts=["1889"])[0]["status"], INC)

    def test_nothing_found_is_inconclusive_not_a_failure(self):
        outcome, fetch = self.run_check(FakeSearch({"": []}), self.pages(), entities=["Nonexistent Thing", "42"])
        self.assertEqual(outcome["status"], INC)
        self.assertEqual(fetch.calls, [])
        outcome, _ = self.run_check(FakeSearch({}, fail=("Thing 42",)), self.pages(), entities=["Thing", "42"])
        self.assertEqual(outcome["status"], INC)
        self.assertIn("no search backend answered", outcome["detail"])

    def test_the_disconfirming_search_has_to_run(self):
        search = FakeSearch({"": [hit("https://a.example/eiffel"), hit("https://www.b.example.org/tower")]}, fail=("myth", "false"))
        outcome, _ = self.run_check(search, self.pages(), entities=["Eiffel Tower", "330"])
        self.assertEqual(outcome["status"], INC)
        self.assertIn("disconfirming search could not run", outcome["detail"])
        self.assertTrue(any("disconfirming search" in n for n in outcome["evidence"][0]["notes"]))

    def test_the_query_is_not_the_wording_of_the_claim(self):
        search = FakeSearch({"": []})
        outcome, _ = self.run_check(search, {}, entities=["The", "Eiffel", "Tower", "is", "330", "metres", "tall"], claim=self.FACT)
        self.assertEqual(outcome["status"], NA)
        self.assertEqual(search.queries, [])
        self.assertEqual(self.run_check(FakeSearch({"": []}), {}, entities=[])[0]["status"], NA)

    def test_pages_that_fail_and_budgets(self):
        search = FakeSearch({"": [hit("https://down.example/x"), hit("https://a.example/eiffel"), hit("https://www.b.example.org/tower"), hit("https://c.example.co.uk/x"),
                                  hit("https://d.example/1"), hit("https://e.example/1")]})
        pages = self.pages(**{"https://down.example/x": W.WebError("timed out")})
        outcome, fetch = self.run_check(search, pages, entities=["Eiffel Tower", "330"], max_fetches=2)
        self.assertEqual(len(fetch.calls), 2)                                                                           # the budget is kept
        self.assertEqual(outcome["status"], INC)                                                                        # one of the two reads was lost to the failed page
        outcome, fetch = self.run_check(search, pages, entities=["Eiffel Tower", "330"], max_fetches=3)
        self.assertEqual((len(fetch.calls), outcome["status"]), (3, PASS))                                              # a third read makes up for it
        self.assertTrue(any("down.example" in n for n in outcome["evidence"][0]["notes"]))

    def test_number_formats_and_injection_signals(self):
        pages = {"https://a.example/1": {"text": "The tower has 1,063 feet of height.", "signals": ["ignore previous instructions"]},
                 "https://b.example/2": {"text": "Height: 1063 feet in total."}}
        search = FakeSearch({"": [hit("https://a.example/1"), hit("https://b.example/2")]})
        outcome, _ = self.run_check(search, pages, entities=["tower"], facts=["1063"])
        self.assertEqual(outcome["status"], PASS)
        self.assertEqual(outcome["evidence"][0]["injection_signals"], [{"domain": "a.example", "signals": ["ignore previous instructions"]}])

    def test_domains_and_copies(self):
        for host, expected in (("www.news.example.co.uk", "example.co.uk"), ("a.b.example.com", "example.com"), ("example.com", "example.com"), ("localhost", "localhost"), ("EXAMPLE.org.", "example.org")):
            self.assertEqual(C.registered_domain(host), expected)
        text = "word " * 10 + " ".join("w%d" % i for i in range(100))
        self.assertTrue(C.same_content(text, text + " extra"))
        self.assertFalse(C.same_content(text, " ".join("x%d" % i for i in range(100))))


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.library = Library(os.path.join(REPO, "library"))
        self.fetch = FakeFetch({"https://a.example/x": {"title": "Eiffel", "text": SOURCE}})
        self.search = FakeSearch({"": []})
        functions = {**C.OFFLINE_FUNCTIONS, **C.build_web_checks(self.search, self.fetch)}
        tools = {"web_search": Tool(self.search, "search_calls"), "fetch_page": Tool(self.fetch, "fetch_calls")}
        self.core = Core(os.path.join(REPO, "skills"), self.library, self.tmp.name, tools=tools, functions=functions)
        self.runner = self.core.checks

    def tearDown(self):
        self.tmp.cleanup()

    def test_the_shipped_check_nodes_are_consistent_with_the_code(self):
        nodes = [e for e in self.library.entries("node") if "check" in e["tags"] and e.get("applies_to", {}).get("claim_types")]        # injection_signals is a helper, not a claim check
        self.assertEqual(len(nodes), 10)
        functions = {**C.OFFLINE_FUNCTIONS, **C.build_web_checks(self.search, self.fetch), **C.build_script_checks(None)}
        for entry in nodes:
            self.assertIn(entry["body"]["function"], functions, entry["id"])
            self.assertTrue(entry["applies_to"]["claim_types"], entry["id"])
            import inspect
            accepted = set(inspect.signature(functions[entry["body"]["function"]]).parameters)
            declared = set(entry["inputs"]["schema"]["properties"]) | set(entry.get("params", {}))
            self.assertLessEqual(declared, accepted, "%s declares inputs the function does not accept: %s" % (entry["id"], declared - accepted))
            for required in entry["inputs"]["schema"].get("required", []):
                self.assertIn(required, accepted, entry["id"])

    def test_checks_are_picked_by_claim_type(self):
        outcome = self.runner.run({"type": "numeric", "text": "twelve times one and a half plus three is 21", "data": {"expression": "12*1.5+3", "value": 21}})
        self.assertEqual((outcome["status"], outcome["verdict"]), ("pass", "supported"))
        self.assertEqual([t["ref"] for t in outcome["trace"]], ["check.arithmetic@1"])
        outcome = self.runner.run({"type": "unit", "data": {"value": 5, "from_unit": "km", "to_unit": "mi", "result_value": 2}})
        self.assertEqual((outcome["status"], outcome["verdict"]), ("fail", "contradicted"))
        outcome = self.runner.run({"type": "date", "data": {"kind": "weekday", "date": "2024-02-29", "weekday": "Thursday"}})
        self.assertEqual(outcome["verdict"], "supported")
        outcome = self.runner.run({"type": "quotation", "data": {"quote": "330 metres tall", "source": SOURCE}})
        self.assertEqual(outcome["verdict"], "supported")
        outcome = self.runner.run({"type": "schedule", "data": {"events": [{"name": "A", "start": "09:00", "end": "10:00"}, {"name": "B", "start": "09:30", "end": "10:30"}]}})
        self.assertEqual(outcome["verdict"], "contradicted")
        self.assertEqual(self.runner.run({"type": "structured", "data": {"value": {"a": 1}, "schema": {"type": "object", "required": ["a"]}}})["verdict"], "supported")

    def test_missing_data_unknown_types_and_bad_claims(self):
        outcome = self.runner.run({"type": "numeric", "data": {"expression": "1+1"}})                                  # value missing
        self.assertEqual((outcome["status"], outcome["verdict"]), ("not_applicable", "none"))
        self.assertIn("missing value", outcome["trace"][0]["skipped"])
        self.assertEqual(self.runner.run({"type": "gossip", "data": {}})["verdict"], "none")
        self.assertEqual(self.runner.run("nonsense")["verdict"], "none")
        self.assertEqual(self.runner.run({"type": "numeric", "data": "text"})["verdict"], "none")

    def test_web_checks_run_only_when_allowed(self):
        claim = {"type": "citation", "data": {"url": "https://a.example/x", "quote": "330 metres tall"}}
        offline = self.runner.run(claim, include_web=False)
        self.assertEqual(offline["verdict"], "none")
        self.assertEqual(self.fetch.calls, [])                                                                          # nothing was fetched
        online = self.runner.run(claim, include_web=True)
        self.assertEqual((online["verdict"], [t["ref"] for t in online["trace"]]), ("supported", ["check.citation@1"]))
        self.assertEqual(self.fetch.calls, ["https://a.example/x"])

    def test_a_fact_claim_gets_the_claim_text_for_the_query_guard(self):
        outcome = self.runner.run({"type": "fact", "text": "The Eiffel Tower is 330 metres tall",
                                   "data": {"entities": ["The", "Eiffel", "Tower", "is", "330", "metres", "tall"]}}, include_web=True)
        self.assertEqual(outcome["status"], "not_applicable")
        self.assertEqual(self.search.queries, [])

    def test_fail_fast_and_order_by_cost(self):
        claim = {"type": "quotation", "data": {"quote": "this is not in the source text at all", "source": SOURCE}}
        self.assertEqual(self.runner.run(claim)["verdict"], "contradicted")
        # a library with two checks for one type: the cheap one runs first and a fail stops the rest
        calls = []
        library = Library(os.path.join(REPO, "library"), os.path.join(self.tmp.name, "user"))
        for name, seconds in (("check.zz_slow", 5), ("check.aa_fast", 0.1)):
            entry = {"id": name, "version": 1, "kind": "code", "title": name, "tags": ["check"], "applies_to": {"claim_types": ["probe"]},
                     "inputs": {"schema": {"type": "object", "required": ["x"], "properties": {"x": {"type": "string"}}}}, "body": {"function": name.replace("check.", "")},
                     "cost": {"seconds": seconds}, "status": "trusted"}
            library.add_draft("node", entry)
            library.set_status(name + "@1", "trusted")
        functions = {"zz_slow": lambda x: calls.append("slow") or C.result(PASS, "slow"), "aa_fast": lambda x: calls.append("fast") or C.result(FAIL, "fast")}
        runner = C.CheckRunner(library, lambda: functions)
        outcome = runner.run({"type": "probe", "data": {"x": "1"}})
        self.assertEqual((calls, outcome["verdict"]), (["fast"], "contradicted"))
        calls.clear()
        outcome = runner.run({"type": "probe", "data": {"x": "1"}}, fail_fast=False)
        self.assertEqual((calls, len(outcome["results"])), (["fast", "slow"], 2))

    def test_a_check_that_crashes_is_inconclusive(self):
        library = Library(os.path.join(REPO, "library"))
        runner = C.CheckRunner(library, lambda: {**C.OFFLINE_FUNCTIONS, "arithmetic_claim": lambda **kw: 1 / 0})
        outcome = runner.run({"type": "numeric", "data": {"expression": "1+1", "value": 2}})
        self.assertEqual((outcome["status"], outcome["results"][0]["status"]), ("open", INC))
        self.assertIn("ZeroDivisionError", outcome["results"][0]["detail"])

    def test_the_dispatcher_nodes_run_in_a_pipeline_and_respect_safety(self):
        user = os.path.join(self.tmp.name, "user2")
        library = Library(os.path.join(REPO, "library"), user)
        pipeline = {"id": "verify.hard_test", "version": 1, "title": "Hard checks for claims", "tags": ["verify"], "result": "verdicts",
                    "nodes": [{"id": "each", "kind": "map", "over": "$input.claims", "as": "claim", "collect": "outcome", "output": "verdicts",
                               "body": [{"id": "hard", "use": "code.hard_checks_offline@2", "wire": {"claim": "$claim"}, "output": "outcome"}]}]}
        library.add_draft("pipeline", pipeline)
        library.set_status("verify.hard_test@1", "trusted")
        skills = os.path.join(self.tmp.name, "skills")
        os.makedirs(skills)
        with open(os.path.join(skills, "t.md"), "w") as fp:
            fp.write("---\nname: t\npipeline: verify.hard_test\nmax_safety: {runs_code: true}\n---\n")
        core = Core(skills, library, self.tmp.name, functions=C.OFFLINE_FUNCTIONS)
        result = core.run("t", {"claims": [{"type": "numeric", "data": {"expression": "2+2", "value": 4}}, {"type": "numeric", "data": {"expression": "2+2", "value": 5}}]})
        self.assertEqual([v["verdict"] for v in result.answer], ["supported", "contradicted"])
        self.assertEqual({e["library"] for e in result.events if e["kind"] == "start" and e["node"] == "hard"}, {"code.hard_checks_offline@2"})
        # the web dispatcher is a node that reads the web: a skill without that permission is refused
        library.add_draft("pipeline", dict(pipeline, id="verify.hard_web", nodes=[{"id": "hard", "use": "code.hard_checks_web@2", "wire": {"claim": "$input.claim"}, "output": "verdicts"}]))
        library.set_status("verify.hard_web@1", "trusted")
        with open(os.path.join(skills, "w.md"), "w") as fp:
            fp.write("---\nname: w\npipeline: verify.hard_web\ntools: [web_search, fetch_page]\nmax_safety: {runs_code: true}\n---\n")
        self.assertIn("reads_web", "; ".join(core.check().get("w", [])))


if __name__ == "__main__":
    unittest.main()
