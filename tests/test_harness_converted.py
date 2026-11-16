"""
The variant `converted` of the extraction target (T-CV-09 part, G-V2.CONVERT, D-255): a case goes through run_converted instead of the old runner, on the model of the pin.
Run: python tests/test_harness_converted.py
"""
import json
import os
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


if __name__ == "__main__":
    unittest.main()
