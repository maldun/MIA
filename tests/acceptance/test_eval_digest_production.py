"""
Acceptance tests of the digest target of the eval harness (N-4.1, A-162 of G-V3.CHAT): TC-EVL-012 to 015 (REQ-EVL-012, 013, 014, 015) with the scripted model of TR-CHAT-012.
The target must run the step as the app runs it: the options of the step, the context length of the pin, an input by reference with a checked SHA-256. No model server is
started; texts and hashes are written here. Note: specs/mia/amendments/A-162-draft-eval-digest-target-runs-the-step-as-production.md.
Run with: python tests/acceptance/test_eval_digest_production.py
"""

import hashlib
import importlib.util
import inspect
import os
import sys
import tempfile
import types
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                  # noqa: E402
import harness as H                       # noqa: E402
from fake_model import FakeModel          # noqa: E402

PIN = {"id": "MP-light", "name": "gemma4:12b-it-qat", "digest": "sha256:38044be4f923", "seed": 7, "temperature": 0, "num_ctx": 8192}
KINDS = ("summary", "failed", "stopped")


def real_chat_parameters():
    """the parameters of OllamaModel.chat; imported without the package so that the test runs as a script"""
    try:
        from MIA.pipeline_model import OllamaModel
    except ImportError:
        from pipeline_model import OllamaModel
    return [name for name in inspect.signature(OllamaModel.chat).parameters if name != "self"]


class ScriptedModel:
    """TR-CHAT-012: takes exactly the arguments of OllamaModel.chat (a change of that signature breaks the tests that use it), fails on an unknown one and keeps every call"""

    def __init__(self, replies):
        self.fake, self.kwargs = FakeModel(replies), []

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        self.kwargs.append({"schema": schema, "model": model, "profile": profile, "options": options})
        return self.fake(messages)


def case(kind, text=None, **extra):
    data = {"kind": kind, "skill": "research_question@1", "phases": []}
    if kind == "summary":
        if text is not None:
            data["result"] = text
    else:
        data["reason"] = "search service unreachable" if kind == "failed" else "stopped by the user"
    data.update(extra)
    return {"id": "c-" + kind, "tags": [kind], "input": data}


def run_target(model, cases, current_model="gemma4:26b"):
    """the harness on a core whose current model is another model than the pin"""
    core = types.SimpleNamespace(runner=types.SimpleNamespace(model=model, current=current_model), skills={})
    harness = H.Harness(core)
    harness.pin = PIN
    suite = types.SimpleNamespace(name="skill_turns", path="", target={"kind": "digest", "persona": "MIA is a friendly assistant."})
    return [harness.targets["digest"](c, {"name": "default"}, suite) for c in cases]


class Setup(unittest.TestCase):
    @mark.req("REQ-EVL-012")
    def test_the_scripted_model_takes_the_arguments_of_the_real_model(self):
        """TR-CHAT-012: the scripted model has the parameters of OllamaModel.chat, and an unknown argument fails."""
        # Given: the scripted model of this file
        parameters = [name for name in inspect.signature(ScriptedModel.chat).parameters if name != "self"]
        # Then: it takes the same parameters as the real model, in the same order
        self.assertEqual(parameters, real_chat_parameters())
        # And: an unknown argument fails
        with self.assertRaises(TypeError):
            ScriptedModel(["x"]).chat([{"role": "user", "content": "x"}], unknown=1)


class DigestTargetAsProduction(unittest.TestCase):
    @mark.req("REQ-EVL-012")
    def test_every_call_carries_the_options_of_the_step_and_the_seed_and_temperature_of_the_pin(self):
        """TC-EVL-012: three cases (a summary of 30 000 characters that needs pieces, a failed and a stopped case); every call carries num_predict 1024, seed 7 and temperature 0.
        Example: a summary of 30 000 characters is cut into pieces, so the first case needs more than one call."""
        # Given: a scripted model that answers every call with a short text, and the three cases
        long_text = "The Marrow Bridge is 12 metres long. " * 800        # about 29 600 characters, more than the 4096 tokens of one call
        # When: the harness runs the three cases
        model = ScriptedModel(lambda messages: "A short answer.")
        run_target(model, [case("summary", long_text)])
        calls_of_summary = len(model.kwargs)
        run_target(model, [case("failed"), case("stopped")])
        # Then: every call carries num_predict 1024, seed 7 and temperature 0
        for kwargs in model.kwargs:
            options = kwargs["options"] or {}
            self.assertEqual((options.get("num_predict"), options.get("seed"), options.get("temperature")), (1024, 7, 0))
        # And: the first case needed more than one call
        self.assertGreater(calls_of_summary, 1)

    @mark.req("REQ-EVL-013")
    def test_every_call_carries_the_context_length_of_the_pin_whichever_model_is_current(self):
        """TC-EVL-013: the app's current model is another model than the pin; every call carries num_ctx 8192, and the pin of the eval tool names it too.
        Example: num_ctx 8192 is the value of MP-light in eval-spec.md."""
        # Given: a scripted model and a core whose current model is gemma4:26b, not the pin
        model = ScriptedModel(lambda messages: "A short answer.")
        # When: the harness runs one digest case of each kind
        run_target(model, [case(kind, "Found 12 works." if kind == "summary" else None) for kind in KINDS], current_model="gemma4:26b")
        # Then: every call carries num_ctx 8192
        self.assertEqual(len(model.kwargs), 3)
        for kwargs in model.kwargs:
            self.assertEqual((kwargs["options"] or {}).get("num_ctx"), 8192)
            self.assertEqual(kwargs["model"], "gemma4:12b-it-qat")
        # And: the pin MP-light of tools/eval.py holds the same value
        spec = importlib.util.spec_from_file_location("eval_cli", os.path.join(REPO, "tools", "eval.py"))
        eval_cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(eval_cli)
        self.assertEqual(eval_cli.PINS["MP-light"].get("num_ctx"), 8192)


class InputByReference(unittest.TestCase):
    TEXT = ("Work %d found. " * 400)[:5000]

    def reference(self, directory, text=None, tamper=False, missing=False):
        text = self.TEXT if text is None else text
        path = os.path.join(directory, "result.txt")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if not missing:
            with open(path, "w", encoding="utf-8") as fp:
                fp.write(text[:-1] + "X" if tamper else text)
        return {"path": path, "sha256": digest, "chars": len(text)}

    @mark.req("REQ-EVL-014")
    def test_a_case_with_a_reference_is_run_with_exactly_the_text_of_the_file(self):
        """TC-EVL-014: a file of 5 000 characters and a case with its path and SHA-256 and no result; the step receives exactly the text of the file.
        Example: the text of the file is "Work %d found. " repeated and cut at 5 000 characters."""
        with tempfile.TemporaryDirectory() as directory:
            # Given: the file and a case that holds its path and SHA-256 and no result
            self.assertEqual(len(self.TEXT), 5000)
            ref = self.reference(directory)
            model = ScriptedModel(lambda messages: "A short answer.")
            # When: the harness runs the case
            run_target(model, [case("summary", result_ref=ref)])
            # Then: the step receives exactly the text of the file, compared character by character
            received = [m["content"] for m in model.fake.calls[0] if m["role"] == "user"]
            self.assertEqual(received, [self.TEXT])

    @mark.req("REQ-EVL-015")
    def test_a_missing_file_or_a_changed_character_stops_the_run_before_the_first_call(self):
        """TC-EVL-015: the case of TC-EVL-014 with the file removed and with one character changed; the run stops with an error that holds the case id and no model call is recorded."""
        for label, options in (("missing", {"missing": True}), ("one character changed", {"tamper": True})):
            with self.subTest(label), tempfile.TemporaryDirectory() as directory:
                # Given: the reference whose file is missing / differs in one character from the hash
                ref = self.reference(directory, **options)
                model = ScriptedModel(lambda messages: "A short answer.")
                # When: the harness runs the case
                # Then: the run stops with an error that holds the case id (not an error:no_output record of a case)
                with self.assertRaises(Exception) as caught:
                    run_target(model, [case("summary", result_ref=ref)])
                self.assertIn("c-summary", str(caught.exception))
                # And: no model call is recorded
                self.assertEqual(model.kwargs, [])


if __name__ == "__main__":
    unittest.main()
