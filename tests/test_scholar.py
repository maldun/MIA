"""
Tests for the scholarly sources (scholar.py): spellings and dates, the parsers on recorded answers of the real APIs (tests/fixtures/scholar, recorded 2026-10-21;
the Semantic Scholar body is written by hand because its unauthenticated pool answered 429, which is recorded too), politeness, retry and cache, the clients'
requests, de-duplication, the strict date cut-off and the retraction status. No network. Run with the MIA virtualenv: python tests/test_scholar.py
"""
import datetime
import json
import os
import sys
import tempfile
import unittest

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import scholar as S                                     # noqa: E402
from web_tools import WebLog                            # noqa: E402

FIXTURES = os.path.join(HERE, "fixtures", "scholar")


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as fp:
        return fp.read()


class FakeResponse:
    def __init__(self, status=200, text="", headers=None):
        self.status_code, self.text, self.headers = status, text, headers or {}


class FakeSession:
    """answers by URL prefix; a list of responses is used one after the other; records every call"""

    def __init__(self, routes=None, error=None):
        self.routes, self.error, self.calls = routes or {}, error, []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append({"url": url, "params": dict(params or {}), "headers": dict(headers or {})})
        if self.error:
            raise self.error
        answer = self.routes.get(url)
        if isinstance(answer, list):
            answer = answer.pop(0) if len(answer) > 1 else answer[0]
        return answer if answer is not None else FakeResponse(404, "{}")


def http_for(session, **kwargs):
    kwargs.setdefault("sleep", lambda s: None)
    return S.ApiHttp(session=session, **kwargs)


class Spelling(unittest.TestCase):
    def test_umlaut_and_transliteration_match_each_other(self):
        text = "We make here use of the theory of Gröbner bases for solving algebraic equations."
        for term in ("Groebner basis", "Gröbner bases", "Grobner basis", "gröbner basis"):
            self.assertTrue(S.contains_term(text, term), term)
        self.assertTrue(S.contains_term("the Grobner basis", "Gröbner bases"))

    def test_hyphen_plural_and_case(self):
        self.assertTrue(S.contains_term("a nonsmooth functional", "non-smooth"))
        self.assertTrue(S.contains_term("a non smooth functional", "nonsmooth"))
        self.assertTrue(S.contains_term("squared SQUARES", "square"))
        self.assertTrue(S.contains_term("Electrical Networks", "electrical network"))

    def test_no_false_matches(self):
        self.assertFalse(S.contains_term("smooth functions", "non-smooth"))
        self.assertFalse(S.contains_term("a database of cases", "basis"))
        self.assertFalse(S.contains_term("", "basis"))
        self.assertFalse(S.contains_term("anything", ""))


class Dates(unittest.TestCase):
    def test_parse_forms(self):
        self.assertEqual(S.parse_date("2001-11-22"), (2001, 11, 22))
        self.assertEqual(S.parse_date("2001-11"), (2001, 11, None))
        self.assertEqual(S.parse_date("2001"), (2001, None, None))
        self.assertEqual(S.parse_date("1989 Feb"), (1989, 2, None))
        self.assertEqual(S.parse_date("2001/11/22"), (2001, 11, 22))
        self.assertIsNone(S.parse_date("not a date"))
        self.assertIsNone(S.parse_date(None))

    def test_latest_day_of_a_partial_date(self):
        self.assertEqual(S.latest_day("2001"), datetime.date(2001, 12, 31))
        self.assertEqual(S.latest_day("2000-02"), datetime.date(2000, 2, 29))
        self.assertEqual(S.latest_day("2001-11-22"), datetime.date(2001, 11, 22))

    def test_cutoff_is_strict(self):
        until = "2010-06-30"
        self.assertFalse(S.within({"date": "2010"}, until)[0])               # the year could mean December
        self.assertTrue(S.within({"date": "2010-05"}, until)[0])
        self.assertTrue(S.within({"date": "2010-06-30"}, until)[0])
        self.assertFalse(S.within({"date": "2010-07-01"}, until)[0])
        ok, reason = S.within({"date": None}, until)
        self.assertFalse(ok)
        self.assertIn("no publication date", reason)
        self.assertTrue(S.within({"date": None}, None)[0])                  # no cut-off: everything passes

    def test_since_does_not_drop_what_could_still_be_inside(self):
        self.assertTrue(S.within({"date": "2010"}, None, "2010-06-01")[0])
        self.assertFalse(S.within({"date": "2009-12"}, None, "2010-06-01")[0])

    def test_what_may_be_used_for_a_cutoff_in_the_past(self):
        today = datetime.date(2026, 10, 21)
        self.assertTrue(S.use_as_of("2026-10-21", today)["citations"])
        past = S.use_as_of("2010-01-01", today)
        self.assertFalse(past["citations"])
        self.assertFalse(past["retraction_notices"])
        self.assertIn("as of today", past["note"])


class Parsers(unittest.TestCase):
    def test_openalex(self):
        works = S.parse_openalex(json.loads(fixture("openalex_search.json")))
        self.assertEqual(len(works), 3)
        first = works[0]
        self.assertEqual(first["title"], "Electrical networks and squared squares")
        self.assertEqual(first["doi"], "10.1017/cbo9780511987045.038")
        self.assertEqual(first["date"], "2001-11-22")
        self.assertEqual(first["year"], 2001)
        self.assertEqual(first["work_type"], "book-chapter")
        self.assertEqual(first["authors"][0], "Jacobus H. Lint")
        self.assertEqual(first["ids"]["openalex"], "W2482094588")
        self.assertEqual(first["sources"], ["openalex"])
        self.assertEqual(first["retraction"]["status"], S.UNKNOWN)

    def test_openalex_abstract_from_inverted_index(self):
        self.assertEqual(S.reconstruct_abstract({"Squares": [0], "can": [1], "be": [2], "wires": [3, 5], "and": [4], "nodes": [6]}), "Squares can be wires and wires nodes")
        self.assertEqual(S.reconstruct_abstract(None), "")

    def test_openalex_retracted_flag_is_only_a_hint(self):
        work = S.parse_openalex({"results": [{"id": "https://openalex.org/W1", "title": "x", "is_retracted": True, "publication_date": "2000-01-01"}]})[0]
        state = S.retraction_state(work)
        self.assertEqual(state["status"], S.UNKNOWN)
        self.assertTrue(state["unconfirmed"])

    def test_crossref_search(self):
        works = S.parse_crossref(json.loads(fixture("crossref_search.json")))
        self.assertEqual(len(works), 3)
        self.assertEqual(works[0]["doi"], "10.1215/s0012-7094-93-07217-1")
        self.assertEqual(works[0]["date"], "1993-11-01")
        self.assertEqual(works[0]["venue"], "Duke Mathematical Journal")
        self.assertEqual(works[0]["authors"], ["S. J. Chapman"])

    def test_crossref_notices_of_a_retracted_paper(self):
        work = S.parse_crossref(json.loads(fixture("crossref_retracted.json")))[0]
        self.assertTrue(work["title"].startswith("RETRACTED:"))
        kinds = [n["type"] for n in work["retraction"]["notices"]]
        self.assertEqual(kinds, [S.CORRECTION, S.RETRACTED])
        self.assertEqual(work["retraction"]["status"], S.RETRACTED)
        self.assertEqual(S.retraction_state(work)["status"], S.RETRACTED)
        self.assertEqual(work["retraction"]["notices"][1]["date"], "2010-02-06")

    def test_retraction_as_of_a_date_before_the_notice(self):
        work = S.parse_crossref(json.loads(fixture("crossref_retracted.json")))[0]
        before = S.retraction_state(work, "2005-01-01")
        self.assertEqual(before["status"], S.CORRECTION)                     # the correction of 2004 existed, the retraction of 2010 not yet
        long_before = S.retraction_state(work, "2000-01-01")
        self.assertEqual(long_before["status"], S.NONE)
        self.assertEqual(S.retraction_state(work)["status"], S.RETRACTED)

    def test_pubmed(self):
        works = S.parse_pubmed(S._xml(fixture("pubmed_efetch.xml"), "test"))
        self.assertEqual(len(works), 3)
        first = works[0]
        self.assertEqual(first["ids"]["pmid"], "2536517")
        self.assertEqual(first["doi"], "10.1016/0002-9343(89)90261-1")
        self.assertIn("Fish-oil dietary supplementation", first["title"])
        self.assertEqual(first["venue"], "The American journal of medicine")
        self.assertEqual(first["date"], "1989-Feb")
        self.assertEqual(S.latest_day(first["date"]), datetime.date(1989, 2, 28))
        self.assertTrue(first["abstract"])
        self.assertTrue(first["authors"])
        self.assertEqual(first["retraction"]["status"], S.NONE)              # PubMed gives the status itself
        self.assertEqual(works[1]["date"], "1986")                           # a season is not a month

    def test_arxiv(self):
        works = S.parse_arxiv(S._xml(fixture("arxiv_search.xml"), "test"))
        self.assertEqual(len(works), 3)
        first = works[0]
        self.assertEqual(first["ids"]["arxiv"], "1310.3954")
        self.assertEqual(first["date"], "2013-10-15")
        self.assertEqual(first["work_type"], "preprint")
        self.assertTrue(first["oa_url"].startswith("https://arxiv.org/pdf/"))
        self.assertIn("thresholding", first["title"].lower())
        self.assertEqual(first["sources"], ["arxiv"])

    def test_semantic_scholar_body_written_by_hand(self):
        body = {"data": [{"paperId": "abc123", "title": "Fish oil in Raynaud", "abstract": "A trial.", "year": 1989, "venue": "Am J Med", "citationCount": 120,
                          "externalIds": {"DOI": "10.1016/0002-9343(89)90261-1", "PubMed": "2536517"}, "openAccessPdf": {"url": "https://example.org/a.pdf"},
                          "publicationDate": "1989-02-01", "publicationTypes": ["JournalArticle"], "authors": [{"name": "R. DiGiacomo"}]}]}
        work = S.parse_semantic_scholar(body)[0]
        self.assertEqual(work["doi"], "10.1016/0002-9343(89)90261-1")
        self.assertEqual(work["ids"]["pmid"], "2536517")
        self.assertEqual(work["cited_by"], 120)

    def test_xml_without_entities_dtd_or_network(self):
        evil = '<?xml version="1.0"?><!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>'
        root = S._xml(evil, "test")
        self.assertNotIn("root:", S._text(root))
        with self.assertRaises(S.ScholarError):
            S._xml("<a><b></a>", "test")


class Http(unittest.TestCase):
    URL = "https://api.openalex.org/works"

    def test_retry_once_after_429_then_success(self):
        session = FakeSession({self.URL: [FakeResponse(429, "", {"Retry-After": "3"}), FakeResponse(200, "{\"results\": []}")]})
        slept = []
        http = http_for(session, sleep=slept.append)
        self.assertEqual(http.get(self.URL, {"search": "x"}), "{\"results\": []}")
        self.assertEqual(len(session.calls), 2)
        self.assertIn(3.0, slept)

    def test_retry_wait_is_capped(self):
        session = FakeSession({self.URL: [FakeResponse(429, "", {"Retry-After": "9999"}), FakeResponse(200, "ok")]})
        slept = []
        http_for(session, sleep=slept.append, max_wait=30).get(self.URL)
        self.assertEqual(max(slept), 30)

    def test_two_429_raise_and_say_so(self):
        session = FakeSession({self.URL: FakeResponse(429, fixture("semanticscholar_429.json"))})
        with self.assertRaises(S.ScholarError) as caught:
            http_for(session).get(self.URL)
        self.assertIn("limiting requests", str(caught.exception))
        self.assertEqual(len(session.calls), 2)

    def test_other_status_and_network_error(self):
        with self.assertRaises(S.ScholarError) as caught:
            http_for(FakeSession({self.URL: FakeResponse(500)})).get(self.URL)
        self.assertIn("500", str(caught.exception))
        with self.assertRaises(S.ScholarError):
            http_for(FakeSession(error=requests.ConnectionError("down"))).get(self.URL)

    def test_politeness_interval_per_host(self):
        now = [100.0]
        slept = []
        http = S.ApiHttp(session=FakeSession({self.URL: FakeResponse(200, "ok")}), min_intervals={"api.openalex.org": 2.0}, clock=lambda: now[0], sleep=slept.append)
        http.get(self.URL)
        now[0] += 0.5
        http.get(self.URL)
        self.assertEqual(slept, [1.5])
        now[0] += 10
        http.get(self.URL)
        self.assertEqual(slept, [1.5])

    def test_cache_answers_without_a_request_and_expires(self):
        with tempfile.TemporaryDirectory() as folder:
            clock = [1000.0]
            cache = S.ResponseCache(folder, days=1, clock=lambda: clock[0])
            session = FakeSession({self.URL: FakeResponse(200, "first")})
            http = http_for(session, cache=cache)
            self.assertEqual(http.get(self.URL, {"search": "a"}), "first")
            self.assertEqual(http.get(self.URL, {"search": "a"}), "first")
            self.assertEqual(len(session.calls), 1)
            self.assertEqual(http.get(self.URL, {"search": "b"}), "first")
            self.assertEqual(len(session.calls), 2)
            clock[0] += 2 * 86400
            http.get(self.URL, {"search": "a"})
            self.assertEqual(len(session.calls), 3)

    def test_errors_are_not_cached(self):
        with tempfile.TemporaryDirectory() as folder:
            session = FakeSession({self.URL: [FakeResponse(500), FakeResponse(200, "fine")]})
            http = http_for(session, cache=S.ResponseCache(folder))
            with self.assertRaises(S.ScholarError):
                http.get(self.URL)
            self.assertEqual(http.get(self.URL), "fine")

    def test_every_request_is_in_the_web_log(self):
        with tempfile.TemporaryDirectory() as folder:
            http = http_for(FakeSession({self.URL: FakeResponse(200, "ok")}), log=WebLog(folder))
            http.get(self.URL, {"search": "squared squares"})
            files = os.listdir(folder)
            self.assertEqual(len(files), 1)
            with open(os.path.join(folder, files[0]), encoding="utf-8") as fp:
                line = json.loads(fp.readline())
            self.assertEqual(line["kind"], "scholar")
            self.assertIn("squared%20squares", line["url"])

    def test_no_address_is_sent_unless_configured(self):
        session = FakeSession({self.URL: FakeResponse(200, "{\"results\": []}")})
        S.OpenAlexClient(http_for(session)).search("x")
        self.assertNotIn("mailto", session.calls[0]["params"])
        self.assertNotIn("mailto", session.calls[0]["headers"]["User-Agent"])
        session2 = FakeSession({self.URL: FakeResponse(200, "{\"results\": []}")})
        S.OpenAlexClient(http_for(session2, email="me@example.org"), "me@example.org").search("x")
        self.assertEqual(session2.calls[0]["params"]["mailto"], "me@example.org")


class Clients(unittest.TestCase):
    def test_openalex_filter_for_the_cutoff(self):
        session = FakeSession({S.OPENALEX: FakeResponse(200, fixture("openalex_search.json"))})
        works = S.OpenAlexClient(http_for(session)).search("squared squares", limit=2, until="2010-06-30", since="2000-01-01")
        self.assertEqual(len(works), 2)
        params = session.calls[0]["params"]
        self.assertEqual(params["search"], "squared squares")
        self.assertEqual(params["filter"], "to_publication_date:2010-06-30,from_publication_date:2000-01-01")
        self.assertEqual(params["per-page"], 2)

    def test_crossref_filter_and_lookup(self):
        session = FakeSession({S.CROSSREF: FakeResponse(200, fixture("crossref_search.json")),
                               S.CROSSREF + "/10.1016/s0140-6736(97)11096-0": FakeResponse(200, fixture("crossref_retracted.json"))})
        client = S.CrossrefClient(http_for(session))
        client.search("rectangles squares", until="1999-12-31")
        self.assertEqual(session.calls[0]["params"]["filter"], "until-pub-date:1999-12-31")
        record = client.lookup("https://doi.org/10.1016/S0140-6736(97)11096-0")
        self.assertEqual(record["retraction"]["status"], S.RETRACTED)

    def test_crossref_lookup_of_an_unknown_doi_and_of_a_clean_record(self):
        client = S.CrossrefClient(http_for(FakeSession({})))
        self.assertIsNone(client.lookup("10.1/none"))
        clean = json.loads(fixture("crossref_retracted.json"))
        del clean["message"]["updated-by"]
        clean["message"]["title"] = ["A fine paper"]
        record = S.CrossrefClient(http_for(FakeSession({S.CROSSREF + "/10.1/fine": FakeResponse(200, json.dumps(clean))}))).lookup("10.1/fine")
        self.assertEqual(record["retraction"]["status"], S.NONE)

    def test_pubmed_is_two_steps_with_dates(self):
        session = FakeSession({S.PUBMED_SEARCH: FakeResponse(200, fixture("pubmed_esearch.json")), S.PUBMED_FETCH: FakeResponse(200, fixture("pubmed_efetch.xml"))})
        works = S.PubMedClient(http_for(session)).search("fish oil raynaud", limit=3, until="1990-12-31")
        self.assertEqual(len(works), 3)
        self.assertEqual(session.calls[0]["params"]["maxdate"], "1990/12/31")
        self.assertEqual(session.calls[0]["params"]["datetype"], "pdat")
        self.assertEqual(session.calls[1]["params"]["id"], "2536517,3797213,1626282")
        self.assertNotIn("email", session.calls[0]["params"])

    def test_pubmed_without_hits_makes_one_request(self):
        session = FakeSession({S.PUBMED_SEARCH: FakeResponse(200, json.dumps({"esearchresult": {"idlist": []}}))})
        self.assertEqual(S.PubMedClient(http_for(session)).search("zzz"), [])
        self.assertEqual(len(session.calls), 1)

    def test_arxiv_query_and_dates(self):
        session = FakeSession({S.ARXIV: FakeResponse(200, fixture("arxiv_search.xml"))})
        S.ArxivClient(http_for(session)).search("iterative thresholding of sparse signals", until="2014-12-31")
        query = session.calls[0]["params"]["search_query"]
        self.assertIn("all:iterative AND all:thresholding", query)
        self.assertIn("submittedDate:[19910101", query)
        self.assertIn("201412312359]", query)

    def test_semantic_scholar_needs_a_key_to_be_reliable(self):
        session = FakeSession({S.SEMANTIC_SCHOLAR: FakeResponse(429, fixture("semanticscholar_429.json"))})
        with self.assertRaises(S.ScholarError):
            S.SemanticScholarClient(http_for(session)).search("fish oil")
        keyed = FakeSession({S.SEMANTIC_SCHOLAR: FakeResponse(200, "{\"data\": []}")})
        S.SemanticScholarClient(http_for(keyed), api_key="k").search("x", until="2010-01-01")
        self.assertEqual(keyed.calls[0]["headers"]["x-api-key"], "k")
        self.assertEqual(keyed.calls[0]["params"]["publicationDateOrYear"], ":2010-01-01")


class FakeClient:
    def __init__(self, name, works=None, error=None):
        self.name, self.works, self.error = name, works or [], error

    def search(self, query, limit=10, until=None, since=None):
        if self.error:
            raise S.ScholarError(self.error)
        return list(self.works)


def work(title, doi=None, date="2000-01-01", source="openalex", **kw):
    return S.new_work(source, title=title, doi=doi, date=date, **kw)


class Together(unittest.TestCase):
    def test_a_failing_source_does_not_stop_the_others(self):
        scholar = S.Scholar([FakeClient("openalex", [work("A long enough title one", "10.1/a")]), FakeClient("pubmed", error="pubmed answered 500")])
        result = scholar.search("x")
        self.assertEqual(len(result["works"]), 1)
        self.assertIn("pubmed", result["errors"])
        self.assertEqual(result["counts"], {"openalex": 1})

    def test_dedupe_by_doi_and_by_title_and_year(self):
        a = work("Squaring the square by electrical networks", "10.1/x", cited_by=5, abstract="short", date="1940")
        b = work("Squaring the Square by Electrical Networks", None, source="arxiv", cited_by=9, abstract="a much longer abstract", date="1940-03-01")
        c = work("Something else entirely and different", "10.1/x2")
        d = work("Squaring the square by electrical networks", None, source="pubmed", date="1990")           # same title, 50 years later: another paper
        unique, merged = S.dedupe([a, b, c, d])
        self.assertEqual(len(unique), 3)
        self.assertEqual(merged, 1)
        first = unique[0]
        self.assertEqual(first["cited_by"], 9)
        self.assertEqual(first["abstract"], "a much longer abstract")
        self.assertEqual(first["sources"], ["openalex", "arxiv"])
        self.assertEqual(first["doi"], "10.1/x")
        self.assertEqual(first["date"], "1940-03-01")                         # the more exact date

    def test_dedupe_by_database_ids(self):
        a = work("One title here that is long", ids={"pmid": "55"})
        b = work("A completely different wording of it", ids={"pmid": "55"}, source="pubmed")
        self.assertEqual(len(S.dedupe([a, b])[0]), 1)

    def test_spelling_variants_of_a_title_are_the_same_work(self):
        a = work("Minimierung mit Gröbner-Basen", "10.1/g1", date="2015")
        b = work("Minimierung mit Groebner Basen", None, date="2015", source="arxiv")
        self.assertEqual(len(S.dedupe([a, b])[0]), 1)

    def test_cutoff_drops_with_reasons(self):
        scholar = S.Scholar([FakeClient("openalex", [work("A paper before the cut-off date", "10.1/a", date="2009-05-05"), work("A paper after the cut-off date", "10.1/b", date="2011-01-01"),
                                                     work("A paper without any date at all", "10.1/c", date=None), work("A paper from the cutoff year", "10.1/d", date="2010")])])
        result = scholar.search("x", until="2010-06-30")
        self.assertEqual([w["doi"] for w in result["works"]], ["10.1/a"])
        reasons = {d["ref"]: d["reason"] for d in result["dropped"]}
        self.assertEqual(len(reasons), 3)
        self.assertIn("after the cut-off", reasons["doi:10.1/b"])
        self.assertIn("no publication date", reasons["doi:10.1/c"])
        self.assertIn("2010", reasons["doi:10.1/d"])

    def test_retraction_is_looked_up_and_merged(self):
        crossref = S.CrossrefClient(http_for(FakeSession({S.CROSSREF + "/10.1016/s0140-6736(97)11096-0": FakeResponse(200, fixture("crossref_retracted.json"))})))
        scholar = S.Scholar([FakeClient("openalex", [work("Ileal-lymphoid-nodular hyperplasia in children", "10.1016/S0140-6736(97)11096-0", date="1998-02"),
                                                     work("A fine paper that nobody retracted ever", "10.1/fine")])], crossref=crossref)
        result = scholar.search("x", check_retraction=True)
        by_doi = {w["doi"]: w for w in result["works"]}
        self.assertEqual(S.retraction_state(by_doi["10.1016/s0140-6736(97)11096-0"])["status"], S.RETRACTED)
        self.assertIn("crossref", by_doi["10.1016/s0140-6736(97)11096-0"]["sources"])
        self.assertEqual(result["errors"], {})                                # a DOI that Crossref does not know (404) is no error ...
        self.assertEqual(S.retraction_state(by_doi["10.1/fine"])["status"], S.UNKNOWN)   # ... and the status stays unknown, not "none"

    def test_merge_keeps_the_strongest_status(self):
        retracted = {"status": S.RETRACTED, "notices": [{"type": S.RETRACTED, "date": "2010-02-06", "doi": None, "source": "x", "label": None}], "hints": []}
        nothing = {"status": S.NONE, "notices": [], "hints": []}
        unknown = {"status": S.UNKNOWN, "notices": [], "hints": ["OpenAlex flag"]}
        self.assertEqual(S.merge_retraction(nothing, retracted)["status"], S.RETRACTED)
        self.assertEqual(S.merge_retraction(unknown, nothing)["status"], S.NONE)
        self.assertEqual(S.merge_retraction(None, None)["status"], S.UNKNOWN)

    def test_reference_names(self):
        self.assertEqual(S.reference_of(work("x" * 20, "10.1/A")), "doi:10.1/a")
        self.assertEqual(S.reference_of(work("x" * 20, ids={"pmid": "7"})), "pmid:7")
        self.assertTrue(S.reference_of(work("A title only here")).startswith("title:"))

    def test_build_from_the_configuration(self):
        scholar, http = S.build_scholar({"scholar_backends": ["crossref", "arxiv", "nonsense", "semanticscholar"], "scholar_email": "", "scholar_cache_dir": None}, session=FakeSession())
        self.assertEqual([c.name for c in scholar.clients], ["crossref", "arxiv", "semanticscholar"])
        self.assertIsNone(http.email)
        default, _ = S.build_scholar({}, session=FakeSession())
        self.assertEqual([c.name for c in default.clients], ["openalex", "crossref", "pubmed", "arxiv"])       # Semantic Scholar only on request


if __name__ == "__main__":
    unittest.main()
