"""
Tests for plans.py: the two forms of a plan, the structural checks of a typed plan (every way it can be broken) and the scoring against the gold of a case (a lost word, a redundant lookup, a drift, a rewritten
single question, a missing dependency or operation). Run with the MIA virtualenv: python tests/test_plans.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import plans as P                                     # noqa: E402

TYPED = {"steps": [{"id": 1, "op": "lookup", "attribute": "founding year", "entity": "Tarn Museum"},
                   {"id": 2, "op": "lookup", "attribute": "company that built", "entity": "Rivertown Bridge"},
                   {"id": 3, "op": "lookup", "attribute": "founding year", "entity": "#2"},
                   {"id": 4, "op": "difference", "args": ["#1", "#3"], "unit": "years"}], "answer": "#4"}
QUESTION = "Which is older, the Tarn Museum or the company that built the Rivertown Bridge, and by how many years?"
GOLD = {"lookups": [3, 3], "cover": [["tarn museum"], ["rivertown bridge"], ["found", "founded", "founding"]], "dependent": True, "ops": ["difference"]}


def free(*questions, calc=False):
    return {"subquestions": [{"id": i + 1, "question": q, "query": q} for i, q in enumerate(questions)], "needs_calculation": calc, "single": len(questions) == 1}


def broken(**changes):
    plan = {"steps": [dict(s) for s in TYPED["steps"]], "answer": "#4"}
    for key, value in changes.items():
        if key == "answer":
            plan["answer"] = value
        else:
            index, field = key.split("_")
            plan["steps"][int(index) - 1][field] = value
    return plan


class Structure(unittest.TestCase):
    def test_a_sound_plan(self):
        self.assertEqual(P.typed_problems(TYPED), [])

    def test_every_way_to_break_it(self):
        cases = {
            "ids": (broken(**{"2_id": 5}), "ids must run"),
            "operation": (broken(**{"4_op": "teleport"}), "unknown operation"),
            "arguments": (broken(**{"4_args": ["#1"]}), "needs 2 arguments"),
            "forward reference": (broken(**{"1_entity": "#3"}), "does not come before"),
            "reference to nothing": (broken(**{"3_entity": "#9"}), "does not come before"),
            "no attribute": (broken(**{"1_attribute": " "}), "needs an attribute"),
            "no entity": (broken(**{"1_entity": ""}), "needs an entity"),
            "answer": (broken(answer="#9"), "answer must be"),
            "unused step": (broken(**{"4_args": ["#1", "#2"]}), "step 3 is not used"),
        }
        for name, (plan, expected) in cases.items():
            self.assertTrue(any(expected in p for p in P.typed_problems(plan)), (name, P.typed_problems(plan)))

    def test_not_a_plan(self):
        for bad in (None, "x", {}, {"steps": []}, {"steps": ["junk"], "answer": "#1"}):
            self.assertTrue(P.typed_problems(bad))


class Items(unittest.TestCase):
    def test_both_forms_give_items(self):
        typed = P.plan_items(TYPED)
        self.assertEqual([i["kind"] for i in typed], ["lookup", "lookup", "lookup", "op"])
        self.assertEqual(typed[2]["refs"], ["#2"])
        self.assertEqual(typed[3]["refs"], ["#1", "#3"])
        self.assertEqual(len(P.plan_items(free("a b", "c d"))), 2)
        for odd in (None, {}, "x", {"subquestions": "x"}, {"steps": ["x"]}):
            self.assertEqual(P.plan_items(odd), [])


class Scoring(unittest.TestCase):
    Q = "How many works does the Tarn Museum hold?"
    G = {"lookups": [1, 1], "cover": [["tarn"], ["museum"], ["works", "collection", "hold"]], "verbatim": True, "must_not": ["name of the tarn museum"]}

    def test_a_good_typed_plan(self):
        s = P.score_plan(TYPED, GOLD, QUESTION)
        self.assertTrue(s["ok"], s)
        self.assertEqual((s["structure_ok"], s["dependent_ok"], s["ops_ok"]), (True, True, True))

    def test_the_drift_of_the_first_measurement(self):
        s = P.score_plan(free("What is the name of the Tarn Museum?"), self.G, self.Q)
        self.assertFalse(s["ok"])
        self.assertFalse(s["coverage_ok"])
        self.assertFalse(s["drift_ok"])
        self.assertFalse(s["verbatim_ok"])

    def test_the_question_kept_verbatim_is_a_good_single_plan(self):
        s = P.score_plan(free(self.Q), self.G, self.Q)
        self.assertTrue(s["ok"], s)
        self.assertTrue(s["verbatim_ok"])

    def test_a_reworded_single_lookup_is_not_verbatim_but_may_cover(self):
        s = P.score_plan(free("How many works are in the Tarn Museum collection?"), self.G, self.Q)
        self.assertTrue(s["coverage_ok"])
        self.assertFalse(s["verbatim_ok"])
        self.assertFalse(s["ok"])

    def test_too_many_and_redundant_lookups(self):
        s = P.score_plan(free(self.Q, "How many works does the Tarn Museum hold in total?"), self.G, self.Q)
        self.assertFalse(s["n_ok"])
        self.assertFalse(s["redundancy_ok"])
        self.assertEqual(len(s["duplicate"]), 2)

    def test_a_free_plan_cannot_state_a_dependency_but_must_flag_a_calculation(self):
        gold = dict(GOLD, lookups=[2, 4])
        s = P.score_plan(free("When was the Tarn Museum founded?", "When was the Rivertown Bridge built?", calc=False), gold, QUESTION)
        self.assertIsNone(s["dependent_ok"])
        self.assertFalse(s["calculation_ok"])
        self.assertTrue(P.score_plan(free("When was the Tarn Museum founded?", "When was the Rivertown Bridge built?", calc=True), gold, QUESTION)["calculation_ok"])

    def test_a_typed_plan_without_the_dependency_or_the_operation(self):
        flat = {"steps": [{"id": 1, "op": "lookup", "attribute": "founding year", "entity": "Tarn Museum"}, {"id": 2, "op": "lookup", "attribute": "founding year", "entity": "Rivertown Bridge builder"},
                          {"id": 3, "op": "lookup", "attribute": "built", "entity": "Rivertown Bridge"}], "answer": "#1"}
        s = P.score_plan(flat, GOLD, QUESTION)
        self.assertFalse(s["dependent_ok"])
        self.assertFalse(s["ops_ok"])
        self.assertFalse(s["structure_ok"])

    def test_not_a_plan(self):
        self.assertEqual(P.score_plan(None, GOLD, QUESTION), {"ok": False, "shape": False})
        self.assertEqual(P.score_plan({"subquestions": []}, GOLD, QUESTION), {"ok": False, "shape": False})


if __name__ == "__main__":
    unittest.main()
