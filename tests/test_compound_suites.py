"""
Tests for the suites research_compound (compound questions over a recorded web) and plans (plans scored alone): the world agrees with the gold, the first hop of every chain can be searched, the plan gold
accepts a reference plan for a handful of questions and rejects the known drift, the harness target `plan` with a scripted planner, and the report. Run with the MIA virtualenv:
python tests/test_compound_suites.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import harness as H                                   # noqa: E402
import metrics as M                                   # noqa: E402
import plans as P                                     # noqa: E402
import research_score as S                            # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402

SUITES = os.path.join(REPO, "eval", "suites")
COMPOUND = H.load_suite(os.path.join(SUITES, "research_compound"))
PLANS = H.load_suite(os.path.join(SUITES, "plans"))
with open(os.path.join(SUITES, "research_compound", "web.json"), encoding="utf-8") as _fp:
    WORLD = json.load(_fp)
CASES = {c["id"]: c for c in COMPOUND.cases}
PLAN_CASES = {c["id"]: c for c in PLANS.cases}


def found(query):
    return [r["url"] for r in H.FixtureWebSession(WORLD)._keyword_results(query)]


class World(unittest.TestCase):
    def test_the_facts_of_the_uncomputed_answers_are_in_the_pages(self):
        for case in COMPOUND.cases:
            gold = case["gold"]
            if gold["kind"] != "answer" or "calculation" in case["tags"]:
                continue
            text = " ".join(S.page_text(WORLD, url) or "" for url in gold["sources_any"])
            score = S.score_research({"answer": text, "status": "answered", "sources": []}, dict(gold, must_not=[]), WORLD)
            self.assertTrue(score["facts_ok"], (case["id"], score.get("missing")))

    def test_the_computed_values_agree_with_the_pages(self):
        import datetime
        self.assertIn("5 June 1998", S.page_text(WORLD, "https://bridges.brookfield.example/oakline-viaduct"))
        self.assertEqual(datetime.date(1998, 6, 5).strftime("%A"), "Friday")
        self.assertEqual(CASES["viaduct-opening-weekday"]["gold"]["must_include"], [["Friday"]])
        self.assertEqual((datetime.date(2024, 9, 14) - datetime.date(1998, 6, 5)).days, 9598)
        self.assertIn(["9598", "9,598"], CASES["days-viaduct-to-fair"]["gold"]["must_include"])
        self.assertIn(["84"], CASES["older-company-by-years"]["gold"]["must_include"])

    def test_the_first_hop_of_every_chain_can_be_searched(self):
        first = {"mayor-of-builders-town": "https://bridges.brookfield.example/alder-bridge", "population-of-brandt-town": "https://brandt-engineering.example/about",
                 "author-town-mayor": "https://books.example/the-river-atlas", "length-of-bridge-of-1971-company": "https://brandt-engineering.example/about",
                 "director-of-museum-founded-1985": "https://glass-museum.example/about"}
        for case_id, url in first.items():
            self.assertIn(url, found(CASES[case_id]["input"]["question"]), case_id)

    def test_the_company_register_is_a_decoy_that_answers_nothing(self):
        text = S.page_text(WORLD, "https://brookfield.example/companies-register")
        for name in ("Weissbach", "Kellerau", "Hartmann", "1887"):
            self.assertNotIn(name, text)

    def test_the_near_miss_has_no_answer_in_the_pages(self):
        everything = " ".join(S.page_text(WORLD, url) or "" for url in WORLD["pages"]).casefold()
        self.assertNotIn("hartmann & sons was founded in", everything)
        self.assertIn("head office is in weissbach", everything)
        self.assertEqual(CASES["mayor-of-founding-town-unknown"]["gold"]["kind"], "unknown")


class PlanGold(unittest.TestCase):
    def test_the_two_suites_are_consistent(self):
        compound_ids = {"c-" + c for c in CASES}
        self.assertTrue(compound_ids <= set(PLAN_CASES))
        self.assertGreaterEqual(len(PLANS.cases), 30)
        for case in PLANS.cases:
            gold = case["gold"]
            self.assertIn("lookups", gold, case["id"])
            self.assertIn("cover", gold, case["id"])
            for group in gold["cover"]:
                self.assertTrue(group and all(isinstance(a, str) for a in group), case["id"])

    def test_a_reference_typed_plan_passes_the_gold(self):
        plan = {"steps": [{"id": 1, "op": "lookup", "attribute": "company that built", "entity": "Alder Bridge"}, {"id": 2, "op": "lookup", "attribute": "head office", "entity": "#1"},
                          {"id": 3, "op": "lookup", "attribute": "mayor", "entity": "#2"}], "answer": "#3"}
        score = P.score_plan(plan, PLAN_CASES["c-mayor-of-builders-town"]["gold"], CASES["mayor-of-builders-town"]["input"]["question"])
        self.assertTrue(score["ok"], score)
        self.assertTrue(score["dependent_ok"])

    def test_a_reference_free_plan_for_a_single_question_must_keep_the_words(self):
        question = PLAN_CASES["r-museum-works-conflict"]["input"]["question"]
        gold = PLAN_CASES["r-museum-works-conflict"]["gold"]
        self.assertTrue(P.score_plan({"subquestions": [{"id": 1, "question": question, "query": "Tarn Museum works"}], "needs_calculation": False, "single": True}, gold, question)["ok"])
        drifted = {"subquestions": [{"id": 1, "question": "What is the name of the Tarn Museum?", "query": "Tarn Museum name"}], "needs_calculation": False, "single": True}
        score = P.score_plan(drifted, gold, question)
        self.assertFalse(score["ok"])
        self.assertFalse(score["drift_ok"])

    def test_a_calculation_must_be_flagged(self):
        question = PLAN_CASES["r-weekday-of-opening"]["input"]["question"]
        gold = PLAN_CASES["r-weekday-of-opening"]["gold"]
        plan = {"subquestions": [{"id": 1, "question": question, "query": question}], "needs_calculation": False, "single": True}
        self.assertFalse(P.score_plan(plan, gold, question)["calculation_ok"])
        self.assertTrue(P.score_plan(dict(plan, needs_calculation=True), gold, question)["ok"])


class Target(unittest.TestCase):
    """the harness target `plan` and the report, with a planner that follows a script"""

    class Model:
        def __init__(self, plan_for):
            self.plan_for = plan_for
            self.questions = []

        def chat(self, messages, schema=None, model=None, profile=None, options=None):
            question = messages[-1]["content"].split("Question:\n", 1)[1].split("\n", 1)[0]
            self.questions.append(question)
            return json.dumps(self.plan_for(question))

    def run_with(self, plan_for, only):
        model = self.Model(plan_for)
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tempfile.mkdtemp(), model=model)
        return H.Harness(core).run(PLANS, {"name": "scripted"}, only=only), model

    def test_a_planner_that_copies_the_question_passes_the_single_cases_only(self):
        copy = lambda q: {"subquestions": [{"question": q, "query": q}], "needs_calculation": False}      # noqa: E731
        run, model = self.run_with(copy, ["r-bridge-date", "r-museum-works-conflict", "c-library-founded-single", "c-mayor-of-builders-town", "r-weekday-of-opening"])
        status = {r["case"]: r["status"] for r in run.records}
        self.assertEqual(status["r-bridge-date"], "pass")
        self.assertEqual(status["r-museum-works-conflict"], "pass")
        self.assertEqual(status["c-library-founded-single"], "pass")
        self.assertEqual(status["c-mayor-of-builders-town"], "fail")            # one lookup for a chain of three
        self.assertEqual(status["r-weekday-of-opening"], "fail")                # the calculation is not flagged
        self.assertEqual(len(model.questions), 5)

    def test_the_report_has_the_planner_section(self):
        copy = lambda q: {"subquestions": [{"question": q, "query": q}], "needs_calculation": False}      # noqa: E731
        run, _ = self.run_with(copy, ["r-bridge-date", "c-mayor-of-builders-town"])
        report = H.format_report(run)
        self.assertIn("as a planner, on 2 plans", report)
        self.assertIn("a single lookup keeps the question's own words", report)
        table = M.plan_metrics(run.records)
        self.assertEqual((table["plans"], table["ok"]["k"], table["ok"]["n"]), (2, 1, 2))
        self.assertEqual(table["structure_ok"]["n"], 0)                          # not applicable to free plans

    def test_a_garbage_plan_is_normalised_to_the_question(self):
        run, _ = self.run_with(lambda q: {"subquestions": [], "needs_calculation": False}, ["r-bridge-date"])
        self.assertEqual(run.records[0]["status"], "pass")                       # normalize_plan falls back to the question itself


if __name__ == "__main__":
    unittest.main()
