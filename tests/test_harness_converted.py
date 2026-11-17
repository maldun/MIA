"""
The variant `converted` of the extraction target (T-CV-09 part, G-V2.CONVERT, D-255): a case goes through run_converted instead of the old runner, on the model of the pin.
Run: python tests/test_harness_converted.py
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers")):
    sys.path.insert(0, path)

import harness as H                                       # noqa: E402
from call_recording import ScriptedModel                  # noqa: E402
from core import Core                                     # noqa: E402
from library import Library                              # noqa: E402
import skill_converter                                    # noqa: E402
from unittest import mock                                 # noqa: E402
import plain_modules                                       # noqa: E402

setUpModule, tearDownModule = plain_modules.hooks()      # the package MIA is not importable while this module runs: F-3, tests/plain_modules.py

PIN = {"id": "MP-light", "name": "gemma4:12b-it-qat", "digest": "sha256:x", "seed": 7, "temperature": 0}


class Seen(ScriptedModel):
    def __init__(self):
        super().__init__()
        self.calls = []

    def chat(self, messages, schema=None, model=None, profile=None, options=None, **more):
        self.calls.append({"model": model, "profile": profile, "options": options})
        return super().chat(messages, schema=schema, model=model, profile=profile, options=options)


class ConvertedVariant(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.model = Seen()
        self.core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), self.tmp.name, model=self.model)
        with open(os.path.join(REPO, "eval", "suites", "extraction", "cases.jsonl"), encoding="utf-8") as fp:
            case = json.loads(fp.readline())
        folder = os.path.join(self.tmp.name, "ext")
        os.makedirs(folder)
        with open(os.path.join(folder, "suite.json"), "w") as fp:
            json.dump({"name": "ext", "description": "d", "target": {"kind": "extraction", "skill": "extract_claims"}}, fp)
        with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
            fp.write(json.dumps(case) + "\n")
        self.suite = H.load_suite(folder)

    def records(self, variant):
        run = H.Harness(self.core).run(self.suite, variant=variant, pin=PIN)
        return [r for r in run["records"]] if isinstance(run, dict) else [r for r in run.records]

    def test_the_converted_variant_calls_the_model_of_the_pin_with_its_seed(self):
        """Example: variant {"converted": true} asks the model once per call with model=gemma4:12b-it-qat, seed 7, temperature 0 and gives a status that is no error."""
        # Given the extraction suite of one case and the pin
        # When the converted variant runs
        with mock.patch.object(skill_converter, "run_converted", wraps=skill_converter.run_converted) as spy:
            records = self.records({"name": "conv", "converted": True})
        # Then run_converted ran the skill, the model was asked with the pin's name and options and the case has a score
        self.assertEqual([c.args[0] for c in spy.call_args_list], ["extract_claims"])
        self.assertTrue(self.model.calls)
        for call in self.model.calls:
            self.assertEqual(call["model"], PIN["name"])
            self.assertEqual((call["options"] or {}).get("seed"), 7)
            self.assertEqual((call["options"] or {}).get("temperature"), 0)
        self.assertFalse(str(records[0]["status"]).startswith("error"), records[0])

    def test_without_the_variant_the_old_runner_is_used(self):
        """Example: the default variant makes the same calls as before (model name from the pin, no profile)."""
        # Given the same suite
        # When the default variant runs
        with mock.patch.object(skill_converter, "run_converted") as spy:
            self.records({"name": "default"})
        # Then run_converted was not used and every call carries the pin's name and no profile (the old path)
        spy.assert_not_called()
        self.assertTrue(self.model.calls)
        self.assertTrue(all(c["profile"] is None for c in self.model.calls))


class ConvertedPipelineTarget(unittest.TestCase):
    def test_the_pipeline_target_runs_verify_claim_through_run_converted(self):
        """Example: variant {"converted": true} on a verdicts case calls run_converted("verify_claim", the case input) with the pin's model and gives a status of the tally."""
        # Given a verdicts suite of one case, a scripted model and the pin
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        model = Seen()
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tmp.name, model=model)
        with open(os.path.join(REPO, "eval", "suites", "verdicts", "cases.jsonl"), encoding="utf-8") as fp:
            case = json.loads(fp.readline())
        folder = os.path.join(tmp.name, "verd")
        os.makedirs(folder)
        with open(os.path.join(folder, "suite.json"), "w") as fp:
            json.dump({"name": "verd", "description": "d", "target": {"kind": "pipeline", "skill": "verify_claim"}}, fp)
        with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
            fp.write(json.dumps(case) + "\n")
        # When the converted variant runs
        with mock.patch.object(skill_converter, "run_converted", wraps=skill_converter.run_converted) as spy:
            run = H.Harness(core).run(H.load_suite(folder), variant={"name": "conv", "converted": True}, pin=PIN)
        records = run["records"] if isinstance(run, dict) else run.records
        # Then run_converted ran the skill with the case input, the pin's model was used and the status is no error
        self.assertEqual([(c.args[0], c.args[1]) for c in spy.call_args_list], [("verify_claim", case["input"])])
        self.assertTrue(model.calls and all(c["model"] == PIN["name"] for c in model.calls))
        self.assertFalse(str(records[0]["status"]).startswith("error"), records[0])


class ConvertedPlanTarget(unittest.TestCase):
    def test_the_plan_target_runs_plan_question_through_run_converted(self):
        """Example: variant {"converted": true} on a plans case calls run_converted("plan_question", the case input) with the pin's model and the case gets a plan score or a plain error status."""
        # Given a plans suite of one case, a scripted model and the pin
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        model = Seen()
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tmp.name, model=model)
        with open(os.path.join(REPO, "eval", "suites", "plans", "cases.jsonl"), encoding="utf-8") as fp:
            case = json.loads(fp.readline())
        folder = os.path.join(tmp.name, "pl")
        os.makedirs(folder)
        with open(os.path.join(folder, "suite.json"), "w") as fp:
            json.dump({"name": "pl", "description": "d", "target": {"kind": "plan", "skill": "plan_question"}}, fp)
        with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
            fp.write(json.dumps(case) + "\n")
        # When the converted variant runs
        with mock.patch.object(skill_converter, "run_converted", wraps=skill_converter.run_converted) as spy:
            H.Harness(core).run(H.load_suite(folder), variant={"name": "conv", "converted": True}, pin=PIN)
        # Then run_converted ran the skill with the case input on the pin's model
        self.assertEqual([(c.args[0], c.args[1]) for c in spy.call_args_list], [("plan_question", case["input"])])
        self.assertTrue(model.calls and all(c["model"] == PIN["name"] for c in model.calls))


class ConvertedResearchTarget(unittest.TestCase):
    def test_the_research_target_runs_through_run_converted_with_the_recorded_web(self):
        """Example: variant {"converted": true} on a research case calls run_converted("research", the case input) with the tools web_search and fetch_page (the recorded web, with their budget keys)."""
        # Given a research suite of one case over the recorded web, a scripted model and the pin
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        model = Seen()
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tmp.name, model=model)
        source = os.path.join(REPO, "eval", "suites", "research")
        with open(os.path.join(source, "cases.jsonl"), encoding="utf-8") as fp:
            case = json.loads(fp.readline())
        with open(os.path.join(source, "suite.json"), encoding="utf-8") as fp:
            target = json.load(fp)["target"]
        folder = os.path.join(tmp.name, "res")
        os.makedirs(folder)
        shutil.copy(os.path.join(source, target["fixtures"]), os.path.join(folder, target["fixtures"]))
        with open(os.path.join(folder, "suite.json"), "w") as fp:
            json.dump({"name": "res", "description": "d", "target": target}, fp)
        with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
            fp.write(json.dumps(case) + "\n")
        # When the converted variant runs
        with mock.patch.object(skill_converter, "run_converted", wraps=skill_converter.run_converted) as spy:
            H.Harness(core).run(H.load_suite(folder), variant={"name": "conv", "converted": True}, pin=PIN)
        # Then run_converted ran the skill with the case input and the two tools, each with a budget key, and the pin's model
        call = spy.call_args_list[0]
        self.assertEqual((call.args[0], call.args[1]), (target["skill"], case["input"]))
        self.assertEqual({n: t.budget_key for n, t in call.kwargs["tools"].items()}, {"web_search": "search_calls", "fetch_page": "fetch_calls"})
        self.assertTrue(model.calls and all(c["model"] == PIN["name"] for c in model.calls))


if __name__ == "__main__":
    unittest.main()
