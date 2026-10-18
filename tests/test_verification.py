"""
Tests for the verification styles: the counting (tally), and the pipelines single, consistency, jury, cops and trial run with scripted replies instead of a model: how many calls, who sees what,
how the votes become a verdict. Nothing here says how good a style is with a real model; that is for the harness. Run with the MIA virtualenv: python tests/test_verification.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import verification as V                              # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402

CLAIM = "The Great Wall of China is visible from space with the naked eye."
EVIDENCE = "Astronaut Yang Liwei said he could not see it."


def vote(word, reason="because"):
    return {"verdict": word, "reason": reason, "confidence": 0.8}


class Tally(unittest.TestCase):
    def test_majority_wins(self):
        out = V.tally([vote("refuted"), vote("refuted"), vote("supported")])
        self.assertEqual((out["status"], out["verdict"], out["agreement"]), ("fail", "refuted", 0.667))
        self.assertEqual(out["counts"], {"supported": 1, "refuted": 2, "unclear": 0})

    def test_a_tie_is_not_a_verdict(self):
        out = V.tally([vote("supported"), vote("refuted")])
        self.assertEqual((out["status"], out["verdict"]), ("inconclusive", "unclear"))
        self.assertIn("split", out["detail"])

    def test_unclear_votes_dilute(self):
        self.assertEqual(V.tally([vote("supported"), vote("unclear"), vote("unclear")])["status"], "inconclusive")
        self.assertEqual(V.tally([vote("supported"), vote("supported"), vote("unclear")])["status"], "pass")
        self.assertEqual(V.tally([vote("supported"), vote("unclear")])["status"], "pass")          # exactly half is enough when nobody disagrees

    def test_one_object_and_odd_input(self):
        self.assertEqual(V.tally(vote("supported"))["status"], "pass")
        self.assertEqual(V.tally([])["status"], "inconclusive")
        self.assertEqual(V.tally(None)["detail"], "no votes")
        out = V.tally(["junk", {"verdict": "MAYBE"}, {"verdict": " Supported "}])
        self.assertEqual(out["counts"], {"supported": 1, "refuted": 0, "unclear": 2})

    def test_helpers(self):
        self.assertEqual(V.sequence(3), [0, 1, 2])
        self.assertEqual((V.sequence("x"), V.sequence(-2), len(V.sequence(99))), ([], [], 20))
        self.assertEqual(len(V.experts(None)), 3)
        mine = [{"name": "a", "context": "c"}, {"name": "no context"}]
        self.assertEqual(V.experts(mine), [{"name": "a", "context": "c"}])


class Scripted:
    """a model that answers from a function of the prompt; keeps the prompts"""
    def __init__(self, answer):
        self.answer, self.prompts = answer, []

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        prompt = messages[-1]["content"]
        self.prompts.append(prompt)
        reply = self.answer(prompt, len(self.prompts))
        return reply if isinstance(reply, str) else json.dumps(reply)


class Styles(unittest.TestCase):
    TEMPLATE = open(os.path.join(REPO, "skills", "verify_claim.md"), encoding="utf-8").read()

    def run_style(self, pipeline, answer, **inputs):
        folder = tempfile.mkdtemp()
        os.makedirs(os.path.join(folder, "skills"))
        with open(os.path.join(folder, "skills", "verify_claim.md"), "w", encoding="utf-8") as fp:
            fp.write(self.TEMPLATE.replace("pipeline: verify.single@1", "pipeline: %s@1" % pipeline))
        model = Scripted(answer)
        core = Core(os.path.join(folder, "skills"), Library(os.path.join(REPO, "library")), folder, model=model)
        result = core.run("verify_claim", {"claim": CLAIM, "evidence": EVIDENCE, **inputs})
        self.assertEqual(result.status, "done", result.error)
        return result.answer, model

    def test_single(self):
        out, model = self.run_style("verify.single", lambda p, n: vote("refuted"))
        self.assertEqual((out["status"], len(model.prompts)), ("fail", 1))
        self.assertIn(CLAIM, model.prompts[0])
        self.assertIn(EVIDENCE, model.prompts[0])

    def test_consistency_asks_again_and_takes_the_majority(self):
        answers = ["supported", "refuted", "refuted", "refuted", "supported"]
        out, model = self.run_style("verify.consistency", lambda p, n: vote(answers[n - 1]), rounds=5)
        self.assertEqual((len(model.prompts), out["verdict"], out["agreement"]), (5, "refuted", 0.6))

    def test_consistency_split_is_inconclusive(self):
        out, model = self.run_style("verify.consistency", lambda p, n: vote("supported" if n % 2 else "refuted"), rounds=4)
        self.assertEqual((len(model.prompts), out["status"]), (4, "inconclusive"))

    def test_jury_gives_every_expert_their_own_context(self):
        experts = [{"name": "historian", "context": "You are a historian of China."}, {"name": "astronaut", "context": "You are an astronaut."}, {"name": "optician", "context": "You study eyesight."}]
        out, model = self.run_style("verify.jury", lambda p, n: vote("refuted" if "an astronaut" in p or "eyesight" in p else "supported"), experts=experts)
        self.assertEqual((len(model.prompts), out["status"]), (3, "fail"))
        for prompt, expert in zip(model.prompts, experts):
            self.assertIn(expert["context"], prompt)
            self.assertNotIn(experts[(experts.index(expert) + 1) % 3]["context"], prompt)

    def test_jury_default_panel(self):
        out, model = self.run_style("verify.jury", lambda p, n: vote("unclear"), experts=[])
        self.assertEqual((len(model.prompts), out["status"]), (3, "inconclusive"))
        self.assertEqual(len({p for p in model.prompts}), 3)

    def test_cops_the_judge_sees_both_cases_the_advocates_see_neither(self):
        def answer(prompt, n):
            if "Your side: for" in prompt:
                return {"points": ["PRO-POINT"]}
            if "Your side: against" in prompt:
                return {"points": ["CON-POINT"]}
            return vote("refuted", "the con case is stronger")
        out, model = self.run_style("verify.cops", answer)
        self.assertEqual((out["status"], len(model.prompts)), ("fail", 3))
        self.assertNotIn("CON-POINT", model.prompts[0])
        self.assertNotIn("PRO-POINT", model.prompts[1])
        self.assertIn("PRO-POINT", model.prompts[2])
        self.assertIn("CON-POINT", model.prompts[2])
        self.assertEqual(out["reasons"], ["the con case is stronger"])

    def test_trial_has_a_second_round(self):
        def answer(prompt, n):
            if "The case of the other side" in prompt:
                return {"points": ["REBUTTAL-OF-" + ("CON" if "Your side: for" in prompt else "PRO")]}
            if "Your side: for" in prompt:
                return {"points": ["PRO-POINT"]}
            if "Your side: against" in prompt:
                return {"points": ["CON-POINT"]}
            return vote("supported")
        out, model = self.run_style("verify.trial", answer)
        self.assertEqual((out["status"], len(model.prompts)), ("pass", 5))
        rebuttal_for = [p for p in model.prompts if "The case of the other side" in p and "Your side: for" in p][0]
        self.assertIn("CON-POINT", rebuttal_for)
        self.assertNotIn("PRO-POINT", rebuttal_for)
        judge = model.prompts[-1]
        for part in ("PRO-POINT", "CON-POINT", "REBUTTAL-OF-CON", "REBUTTAL-OF-PRO"):
            self.assertIn(part, judge)

    def test_an_answer_outside_the_schema_is_retried_once_then_fails(self):
        out, model = self.run_style("verify.single", lambda p, n: "not json" if n == 1 else vote("supported"))
        self.assertEqual((out["status"], len(model.prompts)), ("pass", 2))

    def test_the_library_entries_are_sound(self):
        library = Library(os.path.join(REPO, "library"))
        for ref in ("verify.single", "verify.consistency", "verify.jury", "verify.cops", "verify.trial"):
            pipeline = library.resolve(ref + "@1")
            self.assertEqual(pipeline["status"], "draft")
            self.assertIn("verify", pipeline["tags"])
        self.assertEqual(library.resolve("code.tally@1", "node")["status"], "trusted")


class VerdictsSuite(unittest.TestCase):
    def test_the_suite_loads_and_is_balanced(self):
        import harness as H
        suite = H.load_suite(os.path.join(REPO, "eval", "suites", "verdicts"))
        cases = suite.cases
        self.assertGreaterEqual(len(cases), 50)
        truths = [c.get("truth") for c in cases]
        self.assertGreaterEqual(truths.count(True), 15)
        self.assertGreaterEqual(truths.count(False), 15)
        for case in cases:
            self.assertEqual(sorted(case["input"]), ["claim", "evidence", "experts", "rounds"], case["id"])
            if case.get("truth") is None:
                self.assertEqual(case.get("expect"), "inconclusive", case["id"])

    def test_every_case_runs_through_a_style_with_a_scripted_model(self):
        import harness as H
        cases = H.load_suite(os.path.join(REPO, "eval", "suites", "verdicts")).cases
        folder = tempfile.mkdtemp()
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), folder, model=Scripted(lambda p, n: vote("unclear")))
        for case in cases[:6]:
            result = core.run("verify_claim", case["input"])
            self.assertEqual((result.status, result.answer["status"]), ("done", "inconclusive"), case["id"])


if __name__ == "__main__":
    unittest.main()
