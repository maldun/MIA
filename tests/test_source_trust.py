"""
Tests for the source trust table (source_trust.py) and the review request with its budget (review_request.py). No network, no model.
Run with the MIA virtualenv: python tests/test_source_trust.py
"""
import datetime
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from extensions.review import review_request as RR                              # noqa: E402
import scholar as S                                      # noqa: E402
import source_trust as T                                 # noqa: E402


def fixture(name):
    with open(os.path.join(HERE, "fixtures", "scholar", name), encoding="utf-8") as fp:
        return fp.read()


class TrustTests(unittest.TestCase):
    def setUp(self):
        self.table = T.TrustTable.load()

    def test_default_table_is_complete(self):
        for kind in ("journal", "conference", "preprint", "book", "thesis", "report", "official_statistics", "standards_body", "university_page", "quality_press",
                     "trade_press", "company_blog", "blog", "forum", "wiki", "unknown"):
            prior, reason = self.table.prior(kind)
            self.assertTrue(0.0 <= prior <= 1.0, kind)
            self.assertTrue(reason, kind)
        self.assertGreater(self.table.prior("journal")[0], self.table.prior("preprint")[0])
        self.assertGreater(self.table.prior("preprint")[0], self.table.prior("forum")[0])
        for entry in list(self.table.classes.values()) + list(self.table.domains.values()) + list(self.table.suffixes.values()):
            self.assertTrue(entry.get("reason") and entry.get("set"))              # T1: every number has a reason and a date
        for entry in list(self.table.domains.values()) + list(self.table.suffixes.values()):
            self.assertIn(entry["class"], self.table.classes)

    def test_classes_of_recorded_records(self):
        openalex = S.parse_openalex(json.loads(fixture("openalex_search.json")))
        self.assertEqual(self.table.classify(openalex[0]), "book")                    # a book chapter
        pubmed = S.parse_pubmed(S._xml(fixture("pubmed_efetch.xml"), "t"))
        self.assertEqual(self.table.classify(pubmed[0]), "journal")
        arxiv = S.parse_arxiv(S._xml(fixture("arxiv_search.xml"), "t"))
        self.assertEqual(self.table.classify(arxiv[0]), "preprint")
        crossref = S.parse_crossref(json.loads(fixture("crossref_search.json")))
        self.assertEqual(self.table.classify(crossref[0]), "journal")
        self.assertEqual(self.table.classify(S.new_work("crossref", work_type="posted-content")), "preprint")
        self.assertEqual(self.table.classify(S.new_work("crossref", work_type="proceedings-article")), "conference")
        self.assertEqual(self.table.classify(S.new_work("crossref", work_type="dissertation")), "thesis")
        self.assertEqual(self.table.classify(S.new_work("crossref", work_type="something new")), "unknown")

    def test_retracted_work_is_not_usable(self):
        work = S.parse_crossref(json.loads(fixture("crossref_retracted.json")))[0]
        trust = self.table.for_work(work)
        self.assertFalse(trust["usable"])
        self.assertEqual(trust["score"], 0.0)
        self.assertIn("retracted", trust["flags"])

    def test_retraction_notice_after_the_cutoff_does_not_count(self):
        work = S.parse_crossref(json.loads(fixture("crossref_retracted.json")))[0]
        trust = self.table.for_work(work, as_of="2005-01-01")
        self.assertTrue(trust["usable"])
        self.assertGreater(trust["score"], 0.5)
        self.assertIn("has a correction", trust["flags"])

    def test_unconfirmed_hint_is_a_flag_not_a_verdict(self):
        work = S.parse_openalex({"results": [{"id": "https://openalex.org/W1", "title": "x", "type": "article", "is_retracted": True, "publication_date": "2000-01-01"}]})[0]
        trust = self.table.for_work(work)
        self.assertTrue(trust["usable"])
        self.assertTrue(any("unconfirmed" in f for f in trust["flags"]))

    def test_concern_lowers_and_correction_does_not(self):
        base = S.new_work("crossref", work_type="journal-article", title="x")
        plain = self.table.for_work(base)["score"]
        concern = S.new_work("crossref", work_type="journal-article", title="x")
        concern["retraction"] = {"status": S.CONCERN, "notices": [{"type": S.CONCERN, "date": "2020-01-01"}], "hints": []}
        correction = S.new_work("crossref", work_type="journal-article", title="x")
        correction["retraction"] = {"status": S.CORRECTION, "notices": [{"type": S.CORRECTION, "date": "2020-01-01"}], "hints": []}
        self.assertAlmostEqual(self.table.for_work(concern)["score"], plain - 0.2, places=3)
        self.assertEqual(self.table.for_work(correction)["score"], plain)

    def test_a_notice_is_not_evidence(self):
        pubmed = S.new_work("pubmed", title="Retraction--Ileal-lymphoid-nodular hyperplasia in children", work_type="journal-article", pub_types=["Retraction of Publication"])
        crossref = S.new_work("crossref", title="Retraction: Some paper", work_type="journal-article")
        plain = S.new_work("crossref", title="Retraction of memory in old age: a trial", work_type="journal-article")
        self.assertFalse(self.table.for_work(pubmed)["usable"])
        self.assertFalse(self.table.for_work(crossref)["usable"])
        self.assertTrue(self.table.for_work(plain)["usable"])                  # a title that only starts with the word is a normal paper

    def test_urls(self):
        self.assertEqual(self.table.for_url("https://arxiv.org/abs/1310.3954")["class"], "preprint")
        self.assertEqual(self.table.for_url("https://en.wikipedia.org/wiki/Squaring_the_square")["class"], "wiki")
        self.assertEqual(self.table.for_url("https://www.nih.gov/x")["class"], "official_statistics")
        self.assertEqual(self.table.for_url("https://imsc.uni-graz.at/x")["class"], "unknown")
        self.assertEqual(self.table.for_url("https://math.uni-graz.ac.at/x")["class"], "university_page")
        self.assertEqual(self.table.for_url("https://www.cs.ox.ac.uk/x")["class"], "university_page")
        self.assertEqual(self.table.for_url("https://example.org/page")["class"], "unknown")
        self.assertEqual(self.table.for_url("https://notnih.gov.example.org/")["class"], "unknown")        # a suffix must be the end of the host
        self.assertEqual(self.table.for_url("not a url")["class"], "unknown")

    def test_user_file_overrides_entry_by_entry(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "trust.json")
            with open(path, "w", encoding="utf-8") as fp:
                json.dump({"classes": {"preprint": {"prior": 0.65, "reason": "in my field preprints are the norm", "set": "2026-10-22"}},
                           "domains": {"imsc.uni-graz.at": {"class": "university_page", "reason": "my institute", "set": "2026-10-22"}},
                           "venues": {"Duke Mathematical Journal": {"adjust": 0.1, "reason": "top journal in my field", "set": "2026-10-22"}}}, fp)
            table = T.TrustTable.load(T.DEFAULT_FILE, path)
            self.assertEqual(table.prior("preprint")[0], 0.65)
            self.assertEqual(table.prior("journal")[0], self.table.prior("journal")[0])               # the rest stays
            self.assertEqual(table.for_url("https://imsc.uni-graz.at/x")["class"], "university_page")
            work = S.parse_crossref(json.loads(fixture("crossref_search.json")))[0]
            self.assertAlmostEqual(table.for_work(work)["score"], self.table.for_work(work)["score"] + 0.1, places=3)
            self.assertIn("top journal", table.for_work(work)["reason"])

    def test_broken_user_file_is_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "trust.json")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write("{ not json")
            self.assertEqual(T.TrustTable.load(T.DEFAULT_FILE, path).prior("journal"), self.table.prior("journal"))

    def test_scores_stay_between_zero_and_one(self):
        work = S.new_work("crossref", work_type="journal-article", venue="Venue X")
        table = T.TrustTable({"classes": {"journal": {"prior": 0.95, "reason": "r"}}, "venues": {"Venue X": {"adjust": 0.5, "reason": "r"}}})
        self.assertEqual(table.for_work(work)["score"], 1.0)


class RequestTests(unittest.TestCase):
    TODAY = datetime.date(2026, 10, 22)

    def make(self, **kw):
        kw.setdefault("today", self.TODAY)
        return RR.ReviewRequest("Do transformations of signal theory help in the numerical analysis of wave equations?", **kw)

    def test_defaults(self):
        request = self.make()
        self.assertEqual(request.until, self.TODAY)
        self.assertTrue(request.as_of_today())
        self.assertEqual(request.languages, ["en"])
        self.assertFalse(request.include_transfer)
        self.assertEqual(request.budget.limits["checkpoint_every"], 10)

    def test_cutoff_in_the_past_is_not_as_of_today(self):
        request = self.make(until="2010-06-30", since="2000-01-01")
        self.assertFalse(request.as_of_today())
        self.assertEqual(request.to_dict()["until"], "2010-06-30")

    def test_bad_requests(self):
        for kwargs, text in (({"until": "2030-01-01"}, "future"), ({"until": "yesterday"}, "date"), ({"since": "2011-01-01", "until": "2010-01-01"}, "after the cut-off")):
            with self.assertRaises(RR.RequestError) as caught:
                self.make(**kwargs)
            self.assertIn(text, str(caught.exception))
        with self.assertRaises(RR.RequestError):
            RR.ReviewRequest("short", today=self.TODAY)
        with self.assertRaises(RR.RequestError):
            RR.ReviewRequest("x" * 1001, today=self.TODAY)

    def test_budget_refuses_what_crosses_a_limit(self):
        budget = RR.Budget({"calls": 3})
        self.assertTrue(budget.spend("calls", 2))
        self.assertFalse(budget.spend("calls", 2))                  # would make 4
        self.assertEqual(budget.used["calls"], 2)                   # nothing was counted
        self.assertEqual(budget.hit, "calls")
        self.assertTrue(budget.spend("calls", 1))
        self.assertEqual(budget.exhausted(), "calls")

    def test_budget_rejects_nonsense(self):
        for limits in ({"colour": 3}, {"calls": 0}, {"calls": "many"}, {"calls": True}):
            with self.assertRaises(RR.RequestError):
                RR.Budget(limits)
        with self.assertRaises(RR.RequestError):
            RR.Budget().spend("seconds")

    def test_seconds_come_from_the_clock(self):
        now = [100.0]
        budget = RR.Budget({"seconds": 60}, clock=lambda: now[0])
        budget.start()
        now[0] += 59
        self.assertIsNone(budget.exhausted())
        now[0] += 2
        self.assertEqual(budget.exhausted(), "seconds")
        self.assertEqual(budget.remaining("seconds"), 0)

    def test_checkpoint_every_k_sources(self):
        budget = RR.Budget({"checkpoint_every": 3})
        due = [budget.note_source_checked() for _ in range(7)]
        self.assertEqual(due, [False, False, True, False, False, True, False])

    def test_limits_from_the_configuration(self):
        request = RR.ReviewRequest.from_config("A research question that is long enough?", {"review_budget": {"screen": 12, "checkpoint_every": 5}}, today=self.TODAY)
        self.assertEqual(request.budget.limits["screen"], 12)
        self.assertEqual(request.budget.limits["read"], RR.DEFAULT_BUDGET["read"])

    def test_the_number_of_domain_experts_is_adjustable_and_the_fixed_roles_stay(self):
        for n in (0, 1, 2, 3, 5):
            roles = self.make(domain_experts=n).roles()
            self.assertEqual(roles["fixed"], ["planner", "collector", "source_expert"])
            self.assertEqual((roles["domain_experts"], roles["generalist"]), (n, n == 0))
        self.assertEqual(self.make().roles()["domain_experts"], RR.DEFAULT_DOMAIN_EXPERTS)
        for bad in (-1, 11, 2.5, "3", True, None):
            with self.assertRaises(RR.RequestError):
                self.make(domain_experts=bad)

    def test_fields_for_the_experts_and_models_for_the_roles(self):
        request = self.make(domain_experts=2, expert_fields=["electrical engineering", "physics"], role_models={"source_expert": "gemma4:26b", "domain": None})
        roles = request.roles()
        self.assertEqual(roles["expert_fields"], ["electrical engineering", "physics"])
        self.assertEqual(roles["models"], {"planner": None, "collector": None, "source_expert": "gemma4:26b", "domain": None})
        with self.assertRaises(RR.RequestError):
            self.make(domain_experts=1, expert_fields=["a", "b"])                       # more fields than experts
        with self.assertRaises(RR.RequestError):
            self.make(role_models={"jury": "x"})                                        # no such role
        self.assertEqual(request.to_dict()["roles"]["domain_experts"], 2)

    def test_the_default_comes_from_the_configuration(self):
        request = RR.ReviewRequest.from_config("A research question that is long enough?", {"review_domain_experts": 1, "review_role_models": {"collector": "tiny"}}, today=self.TODAY)
        self.assertEqual(request.domain_experts, 1)
        self.assertEqual(request.roles()["models"]["collector"], "tiny")
        explicit = RR.ReviewRequest.from_config("A research question that is long enough?", {"review_domain_experts": 1}, today=self.TODAY, domain_experts=4)
        self.assertEqual(explicit.domain_experts, 4)                                    # a request overrides the default

    def test_the_first_slice_is_one_minute_and_continue_adds_another(self):
        now = [0.0]
        request = RR.ReviewRequest("A research question that is long enough?", today=self.TODAY, clock=lambda: now[0])
        budget = request.budget
        budget.start()
        self.assertEqual(budget.limits["seconds"], 60)
        now[0] = 61
        self.assertEqual(budget.exhausted(), "seconds")
        self.assertEqual(budget.slices(), 1)
        grown = budget.continue_run()
        self.assertEqual(grown, {"seconds": 120})                                          # nothing else was used up
        self.assertIsNone(budget.hit)
        self.assertIsNone(budget.exhausted())
        self.assertEqual(budget.slices(), 2)
        now[0] = 125
        self.assertEqual(budget.exhausted(), "seconds")
        self.assertEqual(budget.continue_run(seconds=300), {"seconds": 420})               # the user names a longer slice
        self.assertEqual([e["amount"] for e in budget.extensions], [60, 300])
        self.assertEqual(budget.state()["slices"], 3)

    def test_continue_renews_the_other_limits_that_were_used_up(self):
        budget = RR.Budget({"calls": 3, "seconds": 60})
        self.assertTrue(budget.spend("calls", 3))
        self.assertFalse(budget.spend("calls", 1))
        self.assertEqual(budget.hit, "calls")
        grown = budget.continue_run()
        self.assertEqual(grown["calls"], 6)
        self.assertEqual(grown["seconds"], 120)
        self.assertNotIn("tokens", grown)                                                  # a limit that was not used up does not grow
        self.assertTrue(budget.spend("calls", 1))
        for bad in (0, -5, "x", True):
            with self.assertRaises(RR.RequestError):
                budget.extend("calls", bad)
        with self.assertRaises(RR.RequestError):
            budget.extend("colour")

    def test_the_advice_at_the_end_of_a_slice(self):
        stop = RR.recommend({"new_sources": 2, "new_findings": 1}, sufficient=True, open_items=3)
        self.assertEqual(stop["action"], "stop")
        self.assertIn("direction is clear", stop["why"])
        go = RR.recommend({"new_sources": 3, "new_findings": 0, "closed_slots": 0}, open_items=2)
        self.assertEqual(go["action"], "continue")
        stuck = RR.recommend({"new_sources": 0, "new_findings": 0, "closed_slots": 0}, open_items=2)
        self.assertEqual(stuck["action"], "stop")
        self.assertIn("other keywords", stuck["why"])
        done = RR.recommend({"new_findings": 2}, open_items=0)
        self.assertEqual(done["action"], "stop")
        self.assertIn("nothing is open", done["why"])
        self.assertEqual(RR.recommend({}, open_items=0)["action"], "stop")                 # an empty slice never invites to run on

    def test_state_for_the_intermediate_report(self):
        budget = RR.Budget({"api_requests": 5})
        budget.spend("api_requests", 5)
        budget.spend("api_requests", 1)
        state = budget.state()
        self.assertEqual(state["hit"], "api_requests")
        self.assertEqual(state["used"]["api_requests"], 5)


if __name__ == "__main__":
    unittest.main()
