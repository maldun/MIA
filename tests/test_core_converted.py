"""
The converted path in the app's run entry (T-CV-09 rest, G-V2.CONVERT; D-256, D-257): Core.run runs a skill on the graph path only when its acceptance record exists in conversion_dir;
everything else (no record, a `pipeline=` variant, a pipeline that cannot be converted) stays on the old runner, and the guards of the old runner (a message may not start a skill that
reaches the internet) still hold. The result has the shape of the old result and the run is in the run log.
Run: python tests/test_core_converted.py
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers")):
    sys.path.insert(0, path)

from call_recording import ScriptedModel                 # noqa: E402
from core import Core                                    # noqa: E402
from library import Library                              # noqa: E402
from pipeline import PipelineError                       # noqa: E402
from skill_store import load_skill                       # noqa: E402
import skill_converter                                   # noqa: E402
import plain_modules                                       # noqa: E402

setUpModule, tearDownModule = plain_modules.hooks()      # the package MIA is not importable while this module runs: F-3, tests/plain_modules.py

SKILLS, LIBRARY = os.path.join(REPO, "skills"), os.path.join(REPO, "library")
PLAN = {"question": "Which is older, the Tarn Museum or the company that built the Rivertown Bridge?"}
CHECK = {"suite": "EV-plans", "run": "plans__x.jsonl", "pins": "MP-light", "verdict": "PASS"}


class Seen(ScriptedModel):
    def __init__(self):
        super().__init__()
        self.calls = []

    def chat(self, messages, schema=None, model=None, profile=None, options=None, **more):
        self.calls.append(profile)
        return super().chat(messages, schema=schema, model=model, profile=profile, options=options)


class CoreRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.records = os.path.join(self.tmp.name, "conversion")
        self.model = Seen()

    def core(self, **more):
        return Core(SKILLS, Library(LIBRARY), os.path.join(self.tmp.name, "runs"), model=self.model, conversion_dir=self.records, **more)

    def record(self, *skills):
        """a record bound to the skill file and the pipeline on disk, with a run file that exists (F-02: a record that does not fit them no longer routes to the graph path)"""
        run = os.path.join(self.tmp.name, "run.jsonl")
        open(run, "w").write("{}\n")
        for name in skills:
            skill = load_skill(os.path.join(SKILLS, name + ".md"))
            ref = skill_converter.pipeline_ref(Library(LIBRARY).resolve(skill["pipeline"], "pipeline"))
            skill_converter.save_check(self.records, name, dict(CHECK, run=run, skill_version=skill["version"], pipeline=skill["pipeline"], pipeline_resolved=ref))

    def test_without_a_record_the_old_runner_runs(self):
        """Example: no record for plan_question: run_converted is not called and the run is done on the old runner."""
        with mock.patch.object(skill_converter, "run_converted") as spy:
            result = self.core().run("plan_question", PLAN, started_by="command")
        spy.assert_not_called()
        self.assertEqual(result.status, "done")

    def test_with_a_record_the_graph_path_runs_and_the_result_has_the_old_shape(self):
        """Example: with a record for plan_question the run goes through run_converted once; the result has run_id, status done, an answer with subquestions, seconds, events, missing and cost."""
        self.record("plan_question")
        core = self.core()
        with mock.patch.object(skill_converter, "run_converted", wraps=skill_converter.run_converted) as spy:
            result = core.run("plan_question", PLAN, started_by="command")
        self.assertEqual([c.args[0] for c in spy.call_args_list], ["plan_question"])
        self.assertEqual((result.status, result.ok), ("done", True))
        self.assertIn("subquestions", result.answer)
        self.assertTrue(result.run_id)
        self.assertEqual((result.missing, isinstance(result.cost, dict), result.seconds >= 0), ([], True, True))
        self.assertTrue(self.model.calls)

    def test_the_run_is_in_the_run_log_with_its_status(self):
        """Example: after a converted run the run log holds one record for the task with status done and the answer."""
        self.record("plan_question")
        core = self.core()
        result = core.run("plan_question", PLAN, started_by="command")
        runs = core.run_log.read()
        self.assertEqual([(r["id"], r["task"], r["status"]) for r in runs], [(result.run_id, "plan_question", "done")])
        self.assertIn("subquestions", json.dumps(runs[0]["output"]))

    def test_a_pipeline_variant_stays_on_the_old_runner(self):
        """Example: core.run(..., pipeline="plan.free@1") with a record: the variant is not the converted skill, so run_converted is not called."""
        self.record("plan_question")
        with mock.patch.object(skill_converter, "run_converted") as spy:
            self.core().run("plan_question", PLAN, pipeline="plan.free@1", started_by="command")
        spy.assert_not_called()

    def test_a_message_may_not_start_a_skill_that_reaches_the_internet(self):
        """Example: research with a record, started by a message: PipelineError as on the old runner and nothing ran."""
        self.record("research")
        with mock.patch.object(skill_converter, "run_converted") as spy:
            with self.assertRaises(PipelineError):
                self.core().run("research", {"question": "q"}, started_by="message")
        spy.assert_not_called()

    def test_a_pipeline_that_cannot_be_converted_falls_back_to_the_old_runner(self):
        """Example: run_converted refuses (ConversionError): the old runner runs the skill, the run is done, and exactly one record is in the run log."""
        self.record("plan_question")
        core = self.core()
        with mock.patch.object(skill_converter, "run_converted", side_effect=skill_converter.ConversionError("nope")):
            result = core.run("plan_question", PLAN, started_by="command")
        self.assertEqual(result.status, "done")
        self.assertEqual(len(core.run_log.read()), 1)

    def test_a_budget_end_has_status_budget_and_names_the_key(self):
        """Example: the converted run ends with a budget end (search_calls): status budget, missing ["search_calls"], an error that says so."""
        self.record("plan_question")
        ended = mock.Mock(status="budget", answer=None, values={}, error="budget: search_calls", events=[{"kind": "budget_spent"}], named=None)
        with mock.patch.object(skill_converter, "run_converted", return_value=ended):
            result = self.core().run("plan_question", PLAN, started_by="command")
        self.assertEqual((result.status, result.missing), ("budget", ["search_calls"]))
        self.assertIn("budget", result.error)

    def test_a_failed_graph_is_an_error_with_a_reason(self):
        """Example: the graph run failed at a node: status error and the error names it."""
        self.record("plan_question")
        failed = mock.Mock(status="failed", answer=None, values={}, error="the graph run ended with failed ['step.draw']", events=[], named=["step.draw"])
        with mock.patch.object(skill_converter, "run_converted", return_value=failed):
            result = self.core().run("plan_question", PLAN, started_by="command")
        self.assertEqual(result.status, "error")
        self.assertIn("step.draw", result.error)

    def test_a_stop_request_before_the_run_gives_stopped_and_asks_no_model(self):
        """Example: should_stop is true at once: status stopped, the model was not asked."""
        self.record("plan_question")
        result = self.core().run("plan_question", PLAN, started_by="command", should_stop=lambda: True)
        self.assertEqual(result.status, "stopped")
        self.assertEqual(self.model.calls, [])

    def test_the_run_start_and_end_events_reach_the_listener(self):
        """Example: on_event gets a run_start and a run_end event for the converted run, so the status block opens and closes."""
        self.record("plan_question")
        seen = []
        self.core().run("plan_question", PLAN, started_by="command", on_event=seen.append)
        kinds = [e["kind"] for e in seen]
        self.assertEqual((kinds[0], kinds[-1]), ("run_start", "run_end"))

    def test_the_records_are_read_at_every_run(self):
        """Example: a record written after the core was made counts at the next run (accept_conversion.py needs no restart)."""
        core = self.core()
        with mock.patch.object(skill_converter, "run_converted", wraps=skill_converter.run_converted) as spy:
            core.run("plan_question", PLAN, started_by="command")
            self.record("plan_question")
            core.run("plan_question", PLAN, started_by="command")
        self.assertEqual(len(spy.call_args_list), 1)


if __name__ == "__main__":
    unittest.main()
