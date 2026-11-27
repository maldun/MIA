"""
`tools/eval.py run ... --stored` (G-V4.GRAPHAPI.RUN T-04, REQ-WFM-110 to 114): the skill of the suite runs from its graph saved into a throw-away store,
through Core with `graph_store=` (the stored-graph path of REQ-RUN-042), on the model of the pin; the run header names the path, the graph and its version.
Scripted replies, no model; the store lives in a temporary folder.
Run: python tests/test_eval_cli_stored.py
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

import test_eval_cli as T                             # noqa: E402
from call_recording import ScriptedModel              # noqa: E402

E = T.EVAL_CLI
CLAIM = {"claim": "The Pacific is the largest ocean on Earth.", "evidence": "", "rounds": 3, "experts": []}
PIN = E.pin_record("MP-light")


class Stop(Exception):
    pass


class Listening(ScriptedModel):
    """scripted replies; keeps the model name and options of every call"""

    def __init__(self):
        super().__init__()
        self.calls = []

    def chat(self, messages, schema=None, model=None, profile=None, options=None, **more):
        self.calls.append((model, dict(options or {})))
        return super().chat(messages, schema, model, profile, options, **more)


def scripted_core(model):
    library = E.Library(os.path.join(E.REPO, "library"), None, os.path.join(tempfile.mkdtemp(prefix="eval-stored-"), "library.sqlite"))
    return E.Core(os.path.join(E.REPO, "skills"), library, tempfile.mkdtemp(prefix="eval-stored-"), model=model)


def one_case_suite():
    suite = E.harness.Suite("toy", "one claim", {"kind": "pipeline", "skill": "verify_claim"}, [{"id": "pacific", "input": CLAIM, "expect": "true", "tags": []}])
    suite.path = None
    return suite


class TheFlag(T.CommandLine):
    def run_variant(self, *extra):
        folder = os.path.join(E.SUITES, "toy")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "suite.json"), "w") as fp:
            json.dump({"name": "toy", "target": {"kind": "fake", "skill": "verify_claim"}}, fp)
        with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
            fp.write(json.dumps({"id": "a", "input": {}, "expect": "pass"}) + "\n")
        seen = []

        class Harness:
            def run(self, suite, variant, *args, **kwargs):
                seen.append(variant)
                raise Stop()
        with mock.patch.object(E, "build_core", lambda *a, **k: None), mock.patch.object(E, "store_skill_graph", lambda core, skill, folder: ("g@1", 1)), \
                mock.patch.object(E, "make_harness", lambda *a, **k: Harness()):
            try:
                message, _ = self.main("run", "toy", "--pin", "MP-light", *extra)
            except Stop:
                message = None
        return (seen[0] if seen else None), message

    def test_the_flag_sets_the_variant_key(self):
        """Example: run toy --pin MP-light --stored -> variant {"name": "default", "stored": True}."""
        # Given a suite and the flag
        # When the run starts
        variant, _ = self.run_variant("--stored")
        # Then the harness gets the key
        self.assertEqual(variant, {"name": "default", "stored": True})

    def test_a_variant_that_is_not_the_skills_own_graph_is_refused(self):
        """Example: --stored --pipeline verify.single@1 -> exit naming --stored; the run never starts."""
        for extra in (("--pipeline", "verify.single@1"), ("--converted",)):
            # Given the flag next to an option that changes what runs
            # When the run starts
            variant, message = self.run_variant("--stored", *extra)
            # Then it is refused before the harness
            self.assertIsNone(variant, extra)
            self.assertIn("--stored", message or "")


class TheStore(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="eval-store-")
        self.addCleanup(lambda: __import__("shutil").rmtree(self.folder, True))

    def test_the_skills_graph_is_saved_under_its_pipeline_and_read_by_the_core(self):
        """Example: verify_claim -> ("verify.single@1", 1); the core's store gives the same graph back."""
        # Given a core without a store
        core = scripted_core(Listening())
        # When the graph of verify_claim is stored
        graph_id, version = E.store_skill_graph(core, "verify_claim", self.folder)
        # Then it is version 1 of verify.single@1, and the core finds it as its stored graph
        self.assertEqual((graph_id, version), ("verify.single@1", 1))
        self.assertEqual(core._stored_graph(core.skills.get("verify_claim"))[:2], ("verify.single@1", 1))


class TheRun(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="eval-store-")
        self.addCleanup(lambda: __import__("shutil").rmtree(self.folder, True))

    def test_a_case_runs_from_the_stored_graph_on_the_pin(self):
        """Example: verify_claim stored, one case -> header and run record names verify.single@1 version 1, every call has the pin's name, seed and temperature."""
        # Given verify_claim stored and a harness on the stored path
        model = Listening()
        core = scripted_core(model)
        run_harness = E.StoredHarness(core, E.store_skill_graph(core, "verify_claim", self.folder))
        # When one case runs
        run = run_harness.run(one_case_suite(), {"name": "stored", "stored": True}, 1, pin=PIN)
        # Then it ran on the stored path, named in the run header and the run log, on the pin
        self.assertEqual(run.header["stored_graph"], {"path": "Core graph_store (REQ-RUN-042)", "graph": "verify.single@1", "version": 1})
        self.assertNotIn("error", run.records[0], run.records[0])
        record = core.run_log.read()[-1]
        self.assertEqual((record.get("graph"), record.get("graph_version")), ("verify.single@1", 1))
        self.assertTrue(model.calls)
        self.assertEqual({(name, o.get("seed"), o.get("temperature")) for name, o in model.calls}, {(PIN["name"], 7, 0)})

    def test_a_run_that_left_the_stored_path_is_an_error_of_the_case(self):
        """Example: nothing stored -> the case ends "error:..." naming the stored graph; the old runner's answer is not scored."""
        # Given a harness on the stored path and an empty store
        core = scripted_core(Listening())
        run_harness = E.StoredHarness(core, E.store_skill_graph(core, "verify_computable", self.folder))
        # When a case of verify_claim runs
        run = run_harness.run(one_case_suite(), {"name": "stored", "stored": True}, 1, pin=PIN)
        # Then the case is an error that says so
        self.assertTrue(run.records[0]["status"].startswith("error:"), run.records[0])
        self.assertIn("stored graph", run.records[0]["error"])


if __name__ == "__main__":
    unittest.main()
