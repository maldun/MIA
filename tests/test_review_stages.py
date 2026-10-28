"""TC-WFM-019, -020, -021, -027, -028 (REQ-WFM-019..021, -027, -028): the review workflow as a literature review, model-free parts: query strings, collection with
cut-off and retraction drop list, two independent judgements per work with checked quotes, the keyword extension after approval, the checkpoint before the full text and
the stop by code. The model steps are scripted functions. Run with: python tests/test_review_stages.py"""
import datetime
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import review_stages as rs
import scholar
from review_request import ReviewRequest

TODAY = datetime.date(2026, 10, 28)
CRITERIA = {"outdated", "off_topic", "wrong_type"}


def work(doi, title, date="2020-05-01", abstract="Graph methods for scheduling in practice.", retracted=False):
    w = scholar.new_work("test", doi=doi, title=title, date=date, year=int(date[:4]), abstract=abstract)
    if retracted:
        w["retraction"] = {"status": "retracted", "notices": [{"type": "retracted", "date": "2021"}], "hints": []}
    return w


def judge(work_, grade=2, decision="include", reason="", quote=None):
    quote = quote or work_["abstract"][:20]
    return {"grade": grade, "decision": decision, "reason": reason, "quote": quote, "statement": "x"}


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class TestQueries(unittest.TestCase):
    def test_one_query_per_keyword_and_a_combined_string(self):
        q = rs.build_queries({"method": ["graph colouring", "scheduling"], "domain": ["timetable"]})
        self.assertEqual(q["per_keyword"], {"graph colouring": '"graph colouring"', "scheduling": '"scheduling"', "timetable": '"timetable"'})
        self.assertEqual(q["combined"], '("graph colouring" OR "scheduling") AND ("timetable")')


class TestCollect(unittest.TestCase):          # TC-WFM-021
    def test_merges_duplicates_and_remembers_the_keywords(self):
        a = work("10.1/a", "A")
        found = {"graph": [a, work("10.1/b", "B")], "timetable": [dict(a)]}
        out = rs.collect(found, until=TODAY)
        self.assertEqual(len(out["kept"]), 2)
        self.assertEqual(out["duplicates"], 1)
        self.assertEqual(sorted(next(w for w in out["kept"] if w["doi"] == "10.1/a")["keywords"]), ["graph", "timetable"])
        self.assertEqual(out["by_keyword"]["timetable"], ["10.1/a"])

    def test_no_work_after_the_cutoff_and_retracted_works_are_listed(self):
        found = {"k": [work("10.1/ok", "ok", "2019-01-01"), work("10.1/late", "late", "2025-03-01"),
                       work("10.1/ret", "ret", "2018-01-01", retracted=True), work("10.1/nodate", "nd", date="2020")]}
        found["k"][3].pop("date")
        found["k"][3]["year"] = None
        out = rs.collect(found, until=datetime.date(2024, 12, 31))
        self.assertEqual([w["doi"] for w in out["kept"]], ["10.1/ok"])
        self.assertEqual({d["work"]["doi"]: d["code"] for d in out["dropped"]},
                         {"10.1/late": "after_cutoff", "10.1/ret": "retracted", "10.1/nodate": "no_date"})


class TestJudgement(unittest.TestCase):        # TC-WFM-028
    def test_a_quote_that_is_not_in_the_source_makes_the_judgement_unverified(self):
        w = work("10.1/a", "A")
        bad = judge(w, quote="a sentence the paper never contains")
        out = rs.check_judgement(bad, w["abstract"], CRITERIA)
        self.assertFalse(out["verified"])
        self.assertEqual(out["decision"], "maybe")           # include is not trusted without a quote
        self.assertEqual(rs.check_judgement(judge(w), w["abstract"], CRITERIA)["decision"], "include")

    def test_grade_and_reason_are_checked(self):
        w = work("10.1/a", "A")
        for bad in (judge(w, grade=4), judge(w, grade=-1), judge(w, decision="yes"), judge(w, decision="exclude", reason="boring")):
            with self.assertRaises(rs.StageError):
                rs.check_judgement(bad, w["abstract"], CRITERIA)

    def test_grade_and_decision_are_independent(self):
        w = work("10.1/a", "A", "1965-01-01")
        high_excluded = rs.check_judgement(judge(w, grade=3, decision="exclude", reason="outdated"), w["abstract"], CRITERIA)
        low_included = rs.check_judgement(judge(w, grade=0, decision="include"), w["abstract"], CRITERIA)
        self.assertEqual((high_excluded["grade"], high_excluded["decision"]), (3, "exclude"))
        self.assertEqual((low_included["grade"], low_included["decision"]), (0, "include"))

    def test_abstract_only_keeps_the_abstract_judgements_and_marks_it(self):
        w = work("10.1/a", "A")
        out = rs.combine(judge(w, 2, "maybe", "off_topic"), None)
        self.assertEqual((out["grade"], out["decision"], out["abstract_only"]), (2, "maybe", True))

    def test_the_full_text_decision_replaces_the_abstract_decision(self):
        w = work("10.1/a", "A")
        full = {"sections": [{"grade": 3}, {"grade": 2}], "fits": True, "decision": "exclude", "reason": "outdated"}
        out = rs.combine(judge(w, 1, "include"), full)
        self.assertEqual((out["decision"], out["reason"], out["abstract_only"]), ("exclude", "outdated", False))

    def test_grade_rule_highest_when_the_sections_fit_the_conclusion_else_lowest(self):
        w = work("10.1/a", "A")
        sections = [{"grade": 3}, {"grade": 2}]                # mean 2.5 rounded down: 2
        base = {"decision": "include", "reason": ""}
        self.assertEqual(rs.combine(judge(w, 1), {**base, "sections": sections, "fits": True})["grade"], 2)
        self.assertEqual(rs.combine(judge(w, 3), {**base, "sections": sections, "fits": True})["grade"], 3)
        self.assertEqual(rs.combine(judge(w, 3), {**base, "sections": sections, "fits": False})["grade"], 2)
        self.assertEqual(rs.combine(judge(w, 1), {**base, "sections": sections, "fits": False})["grade"], 1)


class TestKeywordExtension(unittest.TestCase):  # TC-WFM-027
    TEXTS = ["bipartite matching helps", "bipartite matching and flows", "a bipartite approach", "matching only here"]

    def test_only_terms_in_at_least_n_works_are_proposed(self):
        terms = {p["term"]: p["works"] for p in rs.propose_terms(self.TEXTS, ["scheduling"], n=3)}
        self.assertEqual(terms.get("bipartite"), 3)
        self.assertEqual(terms.get("matching"), 3)
        self.assertNotIn("flows", terms)
        self.assertNotIn("bipartite matching", terms)          # only 2 works

    def test_words_of_a_keyword_and_stop_words_are_not_proposed(self):
        texts = ["the graph scheduling method", "the graph scheduling method", "the graph scheduling method"]
        self.assertEqual([p["term"] for p in rs.propose_terms(texts, ["graph scheduling"], n=3)], ["method"])

    def test_a_proposed_term_is_not_searched_before_approval(self):
        pool = rs.KeywordPool(["graph"])
        pool.mark_searched("graph")
        pool.propose([{"term": "bipartite", "works": 3}])
        self.assertEqual(pool.to_search(), [])
        self.assertEqual(pool.keywords(), ["graph"])
        pool.approve("bipartite")
        self.assertEqual(pool.to_search(), ["bipartite"])
        self.assertEqual(pool.origin["bipartite"], "extension")
        with self.assertRaises(rs.StageError):
            pool.approve("never proposed")


def scripted_run(works_by_keyword, agree=lambda report: True, approve=lambda proposals: [], abstract=None, full=None, full_text=None, limits=None, clock=None, n=3, summarize=None):
    request = ReviewRequest("how to schedule with graphs", until=TODAY, today=TODAY, budget=limits, clock=clock or Clock())
    calls = {"search": [], "agree": 0, "screen_full": []}

    def search(keyword, query):
        calls["search"].append(keyword)
        return [dict(w) for w in works_by_keyword.get(keyword, [])]

    def counting_agree(report):
        calls["agree"] += 1
        return agree(report)

    def screen_full(w, text):
        calls["screen_full"].append(w["doi"])
        return full(w, text)

    run = rs.ReviewRun(request, ["graph"], CRITERIA, search=search, screen_abstract=abstract or (lambda w: judge(w)), screen_full=screen_full,
                       full_text=full_text or (lambda w: None), agree=counting_agree, approve_terms=approve, min_works=n, summarize=summarize)
    return run.run(), calls


class TestRun(unittest.TestCase):
    WORKS = {"graph": [work("10.1/%d" % i, "T%d" % i) for i in range(4)]}

    def test_the_run_waits_after_the_abstract_screening_and_reads_no_full_text_without_agreement(self):   # TC-WFM-019
        report, calls = scripted_run(self.WORKS, agree=lambda r: False, full_text=lambda w: {"sections": [], "conclusion": ""})
        self.assertEqual(calls["agree"], 1)
        self.assertEqual(calls["screen_full"], [])
        self.assertEqual(report["ended_by"], "user")
        self.assertEqual(report["recommendation"]["action"] in ("stop", "continue"), True)
        self.assertEqual(report["flow"]["screened"], 4)

    def test_with_agreement_the_full_text_is_read_where_it_is_open(self):
        text = {"sections": [{"name": "Intro", "text": "Graph methods for scheduling in practice."}], "conclusion": "Graph methods for scheduling in practice."}
        has_text = {"10.1/0", "10.1/1"}

        def full(w, t):
            return {"sections": [{"grade": 3}], "fits": True, "decision": "include", "reason": "", "quote": "Graph methods for scheduling", "statement": "ok"}
        report, calls = scripted_run(self.WORKS, full=full, full_text=lambda w: text if w["doi"] in has_text else None)
        self.assertEqual(sorted(calls["screen_full"]), ["10.1/0", "10.1/1"])
        by_doi = {w["doi"]: w for w in report["works"]}
        self.assertEqual((by_doi["10.1/0"]["grade"], by_doi["10.1/0"]["abstract_only"]), (3, False))
        self.assertTrue(by_doi["10.1/3"]["abstract_only"])

    def test_the_slice_ends_at_a_budget_and_the_run_continues_only_on_agreement(self):    # TC-WFM-019
        def timed():
            clock = Clock()

            def slow(w):
                clock.now += 40
                return judge(w)
            return clock, slow
        clock, slow = timed()
        report, calls = scripted_run(self.WORKS, abstract=slow, clock=clock, agree=lambda r: True)
        self.assertGreater(calls["agree"], 1)                  # asked at the end of the first 60 s slice and at the checkpoint
        self.assertEqual(report["flow"]["screened"], 4)
        clock, slow = timed()
        stopped, _ = scripted_run(self.WORKS, abstract=slow, clock=clock, agree=lambda r: False)
        self.assertEqual(stopped["flow"]["screened"], 2)       # 80 s are used after the second work: the slice is over
        self.assertEqual(stopped["ended_by"], "budget:seconds")

    def test_a_model_that_says_done_does_not_end_the_run(self):              # TC-WFM-020
        def eager(w):
            return {**judge(w), "done": True}
        report, _ = scripted_run(self.WORKS, abstract=eager)
        self.assertEqual(report["flow"]["screened"], 4)
        self.assertEqual(report["flow"]["undecided"], 0)

    def test_a_used_up_budget_ends_the_run_and_lists_the_undecided_works(self):      # TC-WFM-020
        report, _ = scripted_run(self.WORKS, limits={"screen": 2}, agree=lambda r: False)
        self.assertEqual(report["flow"]["screened"], 2)
        self.assertEqual(report["flow"]["undecided"], 2)
        self.assertEqual(report["ended_by"], "budget:screen")

    def test_approved_keywords_extend_the_search_and_the_run_ends_when_none_is_left(self):    # TC-WFM-027, -020
        works = {"graph": [work("10.1/%d" % i, "T%d" % i, abstract="Bipartite methods for scheduling.") for i in range(3)],
                 "bipartite": [work("10.1/x", "X", abstract="A bipartite note.")]}
        asked = []

        def approve(proposals):
            asked.append([p["term"] for p in proposals])
            return [p["term"] for p in proposals if p["term"] == "bipartite"]
        report, calls = scripted_run(works, approve=approve)
        self.assertEqual(calls["search"], ["graph", "bipartite"])
        self.assertEqual(len(report["works"]), 4)
        self.assertIn("bipartite", asked[0])
        self.assertEqual(len(asked), 1)                         # the second round proposes nothing new and ends the loop

    def test_without_approval_the_keyword_set_is_unchanged(self):            # TC-WFM-027
        works = {"graph": [work("10.1/%d" % i, "T%d" % i, abstract="Bipartite methods for scheduling.") for i in range(3)]}
        report, calls = scripted_run(works, approve=lambda proposals: [])
        self.assertEqual(calls["search"], ["graph"])
        self.assertEqual([k["keyword"] for k in report["keywords"]], ["graph"])

    def test_the_report_has_flow_counts_keywords_gaps_and_dropped_works(self):       # TC-WFM-018, -021
        works = {"graph": [work("10.1/a", "A"), work("10.1/late", "L", "2027-01-01")], "empty": []}
        request = ReviewRequest("how to schedule with graphs", until=TODAY, today=TODAY, clock=Clock())
        run = rs.ReviewRun(request, ["graph", "empty"], CRITERIA, search=lambda k, q: [dict(w) for w in works[k]], screen_abstract=lambda w: judge(w),
                           screen_full=None, full_text=lambda w: None, agree=lambda r: True, approve_terms=lambda p: [])
        report = run.run()
        self.assertEqual(report["flow"]["found"], 2)
        self.assertEqual(report["flow"]["dropped"], 1)
        self.assertEqual(report["flow"]["included"], 1)
        self.assertEqual(report["dropped"][0]["code"], "after_cutoff")
        self.assertEqual(report["gaps"], ["empty"])
        self.assertEqual({k["keyword"]: k["hits"] for k in report["keywords"]}, {"graph": 2, "empty": 0})


def report_of(grades_and_decisions, keywords=("graph", "timetable"), abstract_only=0):
    works = [{"doi": "10.1/%d" % i, "title": "T%d" % i, "grade": g, "decision": d, "reason": "", "abstract_only": i < abstract_only, "keywords": [keywords[i % len(keywords)]],
              "notes": ["note %d [quote]" % i]} for i, (g, d) in enumerate(grades_and_decisions)]
    return {"works": works, "keywords": [{"keyword": k, "hits": 3} for k in keywords], "flow": {"found": len(works), "dropped": 0}, "gaps": [], "ended_by": "complete"}


class TestSummary(unittest.TestCase):          # the summary stage: figures and level by code, the prose checked against the works
    def test_the_coverage_level_is_made_by_code_from_the_included_works(self):
        level = lambda pairs: rs.coverage_figures(report_of(pairs))["level"]
        self.assertEqual(level([]), "none")
        self.assertEqual(level([(3, "exclude"), (1, "maybe")]), "none")
        self.assertEqual(level([(1, "include"), (1, "include"), (1, "include")]), "thin")
        self.assertEqual(level([(3, "include"), (2, "include")]), "thin")           # fewer than 3 included
        self.assertEqual(level([(2, "include")] * 3), "moderate")
        self.assertEqual(level([(3, "include")] * 4 + [(2, "include")] * 4), "good")

    def test_the_figures_count_grades_keywords_and_abstract_only(self):
        figures = rs.coverage_figures(report_of([(3, "include"), (2, "include"), (0, "include"), (3, "exclude"), (1, "maybe")], abstract_only=2))
        self.assertEqual((figures["included"], figures["maybe"], figures["grade3"], figures["grade2"], figures["abstract_only"]), (3, 1, 1, 1, 2))
        self.assertEqual((figures["keywords"], figures["keywords_with_includes"]), (2, 2))

    def test_points_citing_unknown_works_are_dropped_and_counted(self):
        report = report_of([(3, "include"), (2, "include")])
        summary = {"found": [{"point": "good", "works": ["10.1/0", "10.1/999"]}, {"point": "invented", "works": ["10.1/999"]}], "coverage": "thin", "gaps": [{"gap": "g", "works": []}]}
        out = rs.check_summary(summary, report)
        self.assertEqual(out["found"], [{"point": "good", "works": ["10.1/0"]}])
        self.assertEqual(out["dropped_points"], 1)
        self.assertEqual(out["gaps"], [{"gap": "g", "works": []}])
        self.assertTrue(out["needs_check"])
        self.assertEqual(out["figures"]["level"], "thin")

    def test_the_run_adds_the_summary_and_skips_it_when_the_user_stopped(self):
        seen = []

        def summarize(report):
            seen.append(report["flow"]["screened"])
            return {"found": [{"point": "p", "works": ["10.1/0"]}], "coverage": "c", "gaps": []}
        report, _ = scripted_run(TestRun.WORKS, summarize=summarize)
        self.assertEqual(seen, [4])
        self.assertTrue(report["summary"]["needs_check"])
        self.assertEqual(report["summary"]["found"][0]["works"], ["10.1/0"])
        stopped, _ = scripted_run(TestRun.WORKS, agree=lambda r: False, summarize=summarize)
        self.assertNotIn("summary", stopped)


class TestAskingAndStop(unittest.TestCase):
    def test_the_user_is_told_what_is_asked(self):
        asked = []
        clock = Clock()

        def slow(w):
            clock.now += 40
            return judge(w)
        scripted_run(TestRun.WORKS, abstract=slow, clock=clock, agree=lambda r: asked.append(r["asking"]) or True)
        self.assertEqual(asked[0], "limit:seconds")
        self.assertEqual(asked[-1], "checkpoint")

    def test_a_stop_ends_the_run_before_the_next_step_and_gives_no_summary(self):
        stop = {"now": False}

        def abstract(w):
            stop["now"] = True                                   # the user presses stop during the first work
            return judge(w)
        request = ReviewRequest("how to schedule with graphs", until=TODAY, today=TODAY, clock=Clock())
        run = rs.ReviewRun(request, ["graph"], CRITERIA, search=lambda k, q: [dict(w) for w in TestRun.WORKS[k]], screen_abstract=abstract, screen_full=None,
                           full_text=lambda w: None, agree=lambda r: True, approve_terms=lambda p: [], should_stop=lambda: stop["now"],
                           summarize=lambda r: {"found": [], "coverage": "", "gaps": []})
        report = run.run()
        self.assertEqual(report["flow"]["screened"], 1)
        self.assertEqual(report["ended_by"], "stopped")
        self.assertNotIn("summary", report)


if __name__ == "__main__":
    unittest.main()
