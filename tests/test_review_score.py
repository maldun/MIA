"""
Tests for the scoring of literature reviews (review_score.py) and for the consistency of the toy world (eval/suites/review_toy): the gold of every case must agree with the corpus
(every quote occurs in the paper it cites, the cut-offs and the retractions are what the gold says). Run with the MIA virtualenv: python tests/test_review_score.py
"""
import copy
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import harness as H                                      # noqa: E402
from extensions.review import review_score as RS                                # noqa: E402
import scholar                                           # noqa: E402

SUITE = os.path.join(REPO, "eval", "suites", "review_toy")
WORLD = json.load(open(os.path.join(SUITE, "world.json"), encoding="utf-8"))
BY_DOI = {w["doi"]: w for w in WORLD["works"]}
CASES = {c["id"]: c for c in (json.loads(l) for l in open(os.path.join(SUITE, "cases.jsonl"), encoding="utf-8") if l.strip())}


def perfect(case):
    """the best possible review of a case: the included works, every question answered as the gold says with the gold quotes"""
    gold = case["gold"]
    return {"sources": [{"doi": d, "date": BY_DOI[d]["date"]} for d in gold["included"]], "retrieved": list(gold["included"]) + [e["doi"] for e in gold["excluded"]],
            "answers": [{"id": q["id"], "answer": q["answer"], "quotes": q["evidence"]} for q in gold["questions"]], "report": "..."}


class ToyWorld(unittest.TestCase):
    def test_the_suite_is_valid_for_the_harness(self):
        suite = H.load_suite(SUITE)
        self.assertEqual((suite.name, suite.target["kind"]), ("review_toy", "review"))
        self.assertEqual(len(suite.cases), 7)

    def test_the_corpus_is_well_formed(self):
        self.assertEqual(len(BY_DOI), len(WORLD["works"]))                                  # unique DOIs
        for w in WORLD["works"]:
            self.assertTrue(w["abstract"] and w["sections"]["conclusion"], w["doi"])
            self.assertTrue(scholar.parse_date(w["date"]), w["doi"])
            for ref in w["references"]:
                self.assertIn(ref, BY_DOI, w["doi"])
                self.assertLess(BY_DOI[ref]["date"], w["date"], "%s cites a work from its future" % w["doi"])

    def test_the_gold_agrees_with_the_corpus(self):
        for case in CASES.values():
            gold, until = case["gold"], case["input"]["until"]
            for doi in gold["included"]:
                self.assertIn(doi, BY_DOI)
                self.assertTrue(scholar.within(BY_DOI[doi], until)[0], "%s: %s is after the cut-off" % (case["id"], doi))
                self.assertIsNone(BY_DOI[doi]["retraction"], "%s: %s is retracted" % (case["id"], doi))
            for e in gold["excluded"]:
                work = BY_DOI[e["doi"]]
                if e["reason"] == "retracted":
                    self.assertIsNotNone(work["retraction"], e["doi"])
                if e["reason"] == "after_cutoff":
                    self.assertFalse(scholar.within(work, until)[0], e["doi"])
            for q in gold["questions"]:
                self.assertIn(q["answer"], RS.ANSWERS)
                for item in q["evidence"]:
                    text = RS.work_text(BY_DOI[item["source"]])
                    self.assertIn(item["source"], gold["included"] + [x["doi"] for x in gold["excluded"]])
                    self.assertIn(item["quote"], text, "%s: the quote is not in the paper" % q["id"])
                if q["answer"] == "unknown":
                    self.assertEqual(q["evidence"], [])

    def test_the_traps_are_there(self):
        reasons = {e["reason"] for c in CASES.values() for e in c["gold"]["excluded"]}
        self.assertEqual(reasons, {"retracted", "off_topic", "after_cutoff"})
        answers = {q["answer"] for c in CASES.values() for q in c["gold"]["questions"]}
        self.assertEqual(answers, set(RS.ANSWERS))                                          # every kind of answer, the unanswerable one included


class Scoring(unittest.TestCase):
    CASE = CASES["canary-failed-releases"]

    def score(self, result, case=None):
        case = case or self.CASE
        return RS.score_review(result, case["gold"], case["input"], world=BY_DOI)

    def test_the_perfect_review(self):
        s = self.score(perfect(self.CASE))
        self.assertTrue(s["ok"])
        self.assertEqual(s["status"], "pass")
        self.assertEqual((s["sources"]["recall"], s["sources"]["precision"]), (1.0, 1.0))
        self.assertEqual(s["conclusion"]["accuracy"], 1.0)
        self.assertEqual(s["anchored"]["share"], 1.0)
        self.assertEqual(s["hard_failures"], [])

    def test_every_case_has_a_perfect_review(self):
        for case in CASES.values():
            self.assertTrue(self.score(perfect(case), case)["ok"], case["id"])

    def test_a_retracted_source_is_a_hard_failure(self):
        r = perfect(self.CASE)
        r["sources"].append({"doi": "10.9999/rt.0004"})
        s = self.score(r)
        self.assertFalse(s["ok"])
        self.assertEqual(s["excluded_used"], [{"source": "10.9999/rt.0004", "reason": "retracted"}])
        self.assertLess(s["sources"]["precision"], 1.0)
        self.assertEqual(s["sources"]["recall"], 1.0)                                       # finding more does not repair relying on a retracted paper

    def test_a_source_after_the_cutoff_is_a_hard_failure_with_or_without_a_date(self):
        r = perfect(self.CASE)
        r["sources"].append({"doi": "10.9999/rt.0006"})                                    # no date given: looked up in the world
        s = self.score(r)
        self.assertEqual([u["reason"] for u in s["excluded_used"]], ["after_cutoff"])
        self.assertTrue(s["cutoff_violations"])
        r2 = perfect(self.CASE)
        r2["sources"].append({"doi": "10.9999/rt.0099", "title": "Some other paper"})        # unknown date anywhere
        r2["retrieved"].append("10.9999/rt.0099")
        s2 = self.score(r2)
        self.assertTrue(any("no publication date" in v["reason"] for v in s2["cutoff_violations"]))

    def test_an_invented_reference_is_a_hard_failure(self):
        r = perfect(self.CASE)
        r["sources"].append({"doi": "10.9999/rt.0001x", "title": "A paper the run never found", "date": "2020-01-01"})
        s = self.score(r)
        self.assertEqual(s["invented"], ["10.9999/rt.0001x"])
        self.assertFalse(s["ok"])
        r["retrieved"] = None
        self.assertIsNone(self.score(r)["invented"])                                        # not countable without the list of what was retrieved

    def test_an_invented_quote_is_a_hard_failure(self):
        r = perfect(self.CASE)
        r["answers"][0]["quotes"] = [{"source": "10.9999/rt.0001", "quote": "Canary releases halved the failures."}]
        s = self.score(r)
        self.assertLess(s["anchored"]["share"], 1.0)
        self.assertTrue(any(f.startswith("quote not in") for f in s["hard_failures"]))
        self.assertFalse(s["ok"])

    def test_wrong_and_abstained_answers(self):
        r = perfect(self.CASE)
        r["answers"][0]["answer"] = "does_not_support"                                       # what the retracted paper claimed
        r["answers"][1]["answer"] = "unknown"
        s = self.score(r)
        self.assertEqual([x["outcome"] for x in s["questions"]], ["wrong", "abstained", "correct"])
        self.assertEqual((s["conclusion"]["correct"], s["conclusion"]["wrong"], s["conclusion"]["abstained"]), (1, 1, 1))
        self.assertAlmostEqual(s["conclusion"]["precision_when_answered"], 0.5)
        self.assertFalse(s["ok"])
        self.assertEqual(s["hard_failures"], [])                                           # a wrong answer is bad but not a hard failure of the process

    def test_a_missing_answer_counts_as_abstained(self):
        r = perfect(self.CASE)
        r["answers"] = r["answers"][:1]
        s = self.score(r)
        self.assertEqual(s["conclusion"]["abstained"], 2)

    def test_the_question_without_an_answer(self):
        case = CASES["kv-nothing-to-find"]
        good = self.score(perfect(case), case)
        self.assertTrue(good["ok"])
        self.assertIsNone(good["sources"]["recall"])                                        # nothing to find: recall is not defined
        self.assertEqual(good["sources"]["precision"], None)
        bad = perfect(case)
        bad["answers"][0]["answer"] = "supports"
        s = self.score(bad, case)
        self.assertEqual(s["questions"][0]["outcome"], "wrong")                             # claiming an answer that no paper gives
        invented_source = perfect(case)
        invented_source["sources"].append({"doi": "10.9999/rt.0011"})
        self.assertEqual(self.score(invented_source, case)["sources"]["precision"], 0.0)    # listing sources for a question with no answer

    def test_answers_are_read_in_their_common_forms(self):
        for said, meant in (("Yes", "supports"), ("does not support", "does_not_support"), ("MIXED", "inconclusive"), (None, "unknown"), ("whatever", "unknown"), ("does-not-support", "does_not_support")):
            self.assertEqual(RS.normalize_answer(said), meant)

    def test_sources_are_matched_by_title_when_there_is_no_doi(self):
        gold = {"included": [{"title": "Squaring the Square", "doi": None}, {"doi": "10.1/x", "title": "Electrical networks and squared squares"}], "excluded": [], "questions": []}
        result = {"sources": [{"title": "Squaring the square"}, {"doi": "https://doi.org/10.1/X"}, {"title": "Something else entirely different"}]}
        s = RS.score_review(result, gold, {})
        self.assertEqual((s["sources"]["found"], s["sources"]["listed"]), (2, 3))
        self.assertAlmostEqual(s["sources"]["precision"], 2 / 3)

    def test_cross_field_recall_counts_only_the_works_with_other_terms(self):
        gold = {"included": [{"doi": "10.1/a"}, {"doi": "10.1/b", "terms_differ": True}, {"doi": "10.1/c", "terms_differ": True}], "excluded": [], "questions": []}
        s = RS.score_review({"sources": [{"doi": "10.1/a"}, {"doi": "10.1/b"}]}, gold, {})
        self.assertEqual(s["cross_field_recall"], 0.5)
        self.assertIsNone(RS.score_review({"sources": []}, {"included": [{"doi": "10.1/a"}], "questions": []}, {})["cross_field_recall"])

    def test_a_dead_result_scores_without_crashing(self):
        for result in (None, {}, "text", {"sources": None, "answers": None}):
            try:
                s = self.score(result)
            except TypeError:
                self.fail("score_review crashed on %r" % (result,))
            self.assertFalse(s["ok"])

    def test_summary_over_cases(self):
        scores = [self.score(perfect(c), c) for c in CASES.values()]
        bad = perfect(self.CASE)
        bad["answers"][0]["answer"] = "does_not_support"
        bad["sources"].append({"doi": "10.9999/rt.0004"})
        scores.append(self.score(bad))
        summary = RS.summarize(scores)
        self.assertEqual((summary["cases"], summary["passed"]), (len(CASES) + 1, len(CASES)))
        self.assertEqual(summary["questions"], sum(len(c["gold"]["questions"]) for c in CASES.values()) + 3)
        self.assertEqual(summary["wrong"], 1)
        self.assertEqual(summary["hard_failures"]["excluded"], 1)
        low, high = summary["interval"]
        self.assertTrue(low < summary["accuracy"] < high)


if __name__ == "__main__":
    unittest.main()
