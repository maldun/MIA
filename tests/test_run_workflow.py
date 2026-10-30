"""
TC-RUN-014, TC-RUN-015 (REQ-RUN-014, REQ-RUN-015, REQ-RUN-008): the provider of IF-202 and IF-105, `run_workflow.WorkflowRuns`. A workflow of the library (IF-203)
names its skill (D-112); the provider reads it, refuses a run whose estimate exceeds the budget, runs the skill's pipeline under the budget, names what ended it,
returns the cost and events with run id and user, and gives the measured costs of a node. The real WorkflowLibrary on a fresh folder, the shipped skill
`summarize` and a fake model. Run with: python tests/test_run_workflow.py
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

from core import Core                                         # noqa: E402
from library import Library                                   # noqa: E402
from run_workflow import RunWorkflowError, WorkflowRuns, sync_skills   # noqa: E402
from storage import Storage                                   # noqa: E402
from storage_files import FileBackend                         # noqa: E402
from workflow_library import WorkflowLibrary                  # noqa: E402

SUMMARY = {"skill": "summarize", "nodes": [{"id": "text", "kind": "data"}, {"id": "summarize", "kind": "process"}, {"id": "answer", "kind": "data"}],
           "edges": [{"from": "text", "to": "summarize"}, {"from": "summarize", "to": "answer"}]}
PINS = {"MP-light": {"name": "gemma4:12b-it-qat", "digest": "38044be4f923"}}
INPUT = {"text": "The tower is 330 m high.", "sentences": 1}


class FakeModel:
    """a valid summary, 50 tokens in and 10 out a call"""
    def __init__(self):
        self.calls = []

    def chat_with_usage(self, messages, schema=None, model=None, profile=None, options=None):
        self.calls.append({"model": model, "profile": profile, "options": options})
        return '{"summary": "A tall tower.", "key_points": ["330 m"]}', {"tokens_in": 50, "tokens_out": 10}

    def chat(self, messages, **kwargs):
        return self.chat_with_usage(messages, **kwargs)[0]


def make(held=None):
    """(provider, model): the library holds `summary` v1 (skill summarize) and `graph_only` v1 (no skill)"""
    folder = tempfile.mkdtemp()
    model = FakeModel()
    core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), os.path.join(folder, "runs"), model=model)
    runs = WorkflowRuns(None, core, pins=PINS, held=held or (lambda: {"gemma4:12b-it-qat": "38044be4f923e5a5"}))
    library = WorkflowLibrary(Storage(FileBackend(os.path.join(folder, "db"))), costs=runs.node_costs)
    runs.library = library
    library.save("workflows", "summary", SUMMARY, "test")
    library.save("workflows", "graph_only", {k: v for k, v in SUMMARY.items() if k != "skill"}, "test")
    return runs, model


def code_of(call):
    try:
        call()
    except RunWorkflowError as err:
        return err.code
    raise AssertionError("no RunWorkflowError raised")


class RunTests(unittest.TestCase):
    def test_a_run_is_done_with_outputs_events_and_cost(self):
        """TC-RUN-014 golden 1: a run under budget is done; run_start first, run_end last, every event has the run id and the user; the cost is what was spent.
        Example: summary v1, budget {calls: 15} -> done, outputs.summary 'A tall tower.', cost calls 1, tokens 60."""
        # Given the workflow summary and a fake model
        runs, model = make()
        # When anna runs it under a budget of 15 calls
        result = runs.run("summary", 1, INPUT, {"calls": 15}, "anna")
        # Then it is done and framed by run_start and run_end
        self.assertEqual(result["status"], "done")
        self.assertEqual(result["outputs"]["summary"], "A tall tower.")
        events = result["events"]
        self.assertEqual((events[0]["type"], events[-1]["type"], events[-1]["status"]), ("run_start", "run_end", "done"))
        self.assertTrue(all(e["run_id"] == result["run_id"] and e["user"] == "anna" for e in events))
        self.assertEqual((result["cost"]["calls"], result["cost"]["tokens"], result["missing"]), (1, 60, []))

    def test_a_run_over_its_token_budget_ends_with_what_it_has(self):
        """TC-RUN-008, TC-RUN-014 golden 2: the last step passes the token budget: budget_exhausted, missing names tokens, the outputs so far are kept.
        Example: 60 tokens spent, budget {tokens: 50}, no measured cost yet (estimate 0) -> budget_exhausted, ["tokens"], summary kept."""
        runs, _ = make()
        result = runs.run("summary", 1, INPUT, {"tokens": 50}, "anna")
        self.assertEqual((result["status"], result["missing"]), ("budget_exhausted", ["tokens"]))
        self.assertEqual(result["outputs"]["summary"], "A tall tower.")
        self.assertEqual((result["events"][-1]["type"], result["events"][-1]["status"]), ("run_end", "budget_exhausted"))

    def test_an_estimate_over_the_budget_is_refused_before_any_call(self):
        """TC-RUN-014 golden 3: once a run is recorded, the estimate of summary is 1 call and 60 tokens; a budget of 30 tokens is refused, nothing is asked.
        Example: estimate tokens 60 > budget 30 -> refused, missing ["tokens"], events run_start and run_end, cost all 0."""
        # Given one recorded run, so that the estimate knows the cost of the node summarize
        runs, model = make()
        runs.run("summary", 1, INPUT, {}, "anna")
        # When a run has a budget below the estimate
        result = runs.run("summary", 1, INPUT, {"tokens": 30}, "anna")
        # Then it is refused before any model call
        self.assertEqual((result["status"], result["missing"], result["outputs"]), ("refused", ["tokens"], {}))
        self.assertEqual([e["type"] for e in result["events"]], ["run_start", "run_end"])
        self.assertEqual(result["cost"], {"steps": 0, "seconds": 0, "calls": 0, "tokens": 0})
        self.assertEqual(len(model.calls), 1)

    def test_unknown_or_unrunnable_workflows_are_unknown_workflow(self):
        """TC-RUN-014 (errors): an unknown id, an unknown version and a workflow that names no skill are unknown_workflow; nothing is run.
        Example: run("nothing", 1, ...) -> unknown_workflow; run("graph_only", 1, ...) -> unknown_workflow."""
        runs, model = make()
        for workflow, version in (("nothing", 1), ("summary", 9), ("graph_only", 1)):
            self.assertEqual(code_of(lambda: runs.run(workflow, version, INPUT, {}, "anna")), "unknown_workflow", workflow)
        self.assertEqual(model.calls, [])

    def test_measured_costs_of_a_node(self):
        """TC-RUN-014 (costs): the costs of a node are the median of the recorded runs; a node that never ran is None.
        Example: two runs of summary -> costs("summary", "summarize") calls 1, tokens 60; costs("summary", "nope") None."""
        runs, _ = make()
        runs.run("summary", 1, INPUT, {}, "anna")
        runs.run("summary", 1, INPUT, {}, "ben")
        costs = runs.costs("summary", "summarize")
        self.assertEqual((set(costs), costs["calls"], costs["tokens"]), ({"seconds", "calls", "tokens"}, 1, 60))
        self.assertIsNone(runs.costs("summary", "nope"))

    def test_options_are_recorded_and_reach_the_model(self):
        """TC-RUN-014 (options): the pin, seed and temperature are in run_start; the model is asked with the pinned name, the seed and the temperature.
        Example: MP-light, seed 7, temperature 0 -> model 'gemma4:12b-it-qat', options {seed: 7, temperature: 0}."""
        runs, model = make()
        options = {"model_pin": "MP-light", "seed": 7, "temperature": 0}
        result = runs.run("summary", 1, INPUT, {}, "anna", options=options)
        self.assertEqual(result["events"][0]["options"], options)
        self.assertEqual(model.calls[0]["model"], "gemma4:12b-it-qat")
        self.assertEqual((model.calls[0]["options"]["seed"], model.calls[0]["options"]["temperature"]), (7, 0))


class EvaluationAccessTests(unittest.TestCase):
    def test_run_case_needs_the_options_and_a_held_pin(self):
        """TC-RUN-015 golden 2: options without seed are bad_options; an unknown pin and a pin whose digest the server does not hold are pin_unavailable.
        Example: {model_pin, temperature} -> bad_options ["seed"]; MP-huge -> pin_unavailable; held digest 'other' -> pin_unavailable."""
        runs, model = make()
        self.assertEqual(code_of(lambda: runs.run_case("summary", 1, INPUT, {"model_pin": "MP-light", "temperature": 0})), "bad_options")
        self.assertEqual(code_of(lambda: runs.run_case("summary", 1, INPUT, {"model_pin": "MP-huge", "seed": 1, "temperature": 0})), "pin_unavailable")
        other, _ = make(held=lambda: {"gemma4:12b-it-qat": "other"})
        self.assertEqual(code_of(lambda: other.run_case("summary", 1, INPUT, {"model_pin": "MP-light", "seed": 1, "temperature": 0})), "pin_unavailable")
        self.assertEqual(model.calls, [])

    def test_run_case_runs_as_harness_and_is_reproducible(self):
        """TC-RUN-015 golden 1 and 3: the run is the harness's, returns its options, its events can be read again, and two equal runs give equal outputs and
        event types. Example: run_case twice with seed 7 -> same outputs, same sequence of event types; events(run_id) == the events of the result."""
        # Given the evaluation access
        runs, _ = make()
        options = {"model_pin": "MP-light", "seed": 7, "temperature": 0, "budget": {"calls": 15}}
        # When the same case runs twice
        first = runs.run_case("summary", 1, INPUT, options)
        second = runs.run_case("summary", 1, INPUT, options)
        # Then both are the harness's and equal apart from run id and time
        self.assertEqual((first["status"], first["options"], first["events"][0]["user"]), ("done", options, "harness"))
        self.assertEqual(first["outputs"], second["outputs"])
        self.assertEqual([e["type"] for e in first["events"]], [e["type"] for e in second["events"]])
        self.assertEqual(runs.events(first["run_id"]), first["events"])
        self.assertEqual(code_of(lambda: runs.events("r-none")), "unknown_run")

    def test_workflows_lists_the_library(self):
        """TC-RUN-015 (workflows): the ids, versions and status of the library. Example: [graph_only [1] draft, summary [1] draft]."""
        runs, _ = make()
        self.assertEqual(runs.workflows(), [{"id": "graph_only", "versions": [1], "status": "draft"}, {"id": "summary", "versions": [1], "status": "draft"}])


class CostTests(unittest.TestCase):
    def test_calls_of_nested_steps_count_for_their_top_node(self):
        """TC-RUN-014 (costs of a composite node): the model calls between the start and the end of a top node count for it, also those of the steps inside a
        map. Example: node screen (a map) with two model calls of its inner step rate, at 1.0 s and 4.0 s -> screen: calls 2, tokens 30, seconds 3.0."""
        call = lambda seq, at: {"kind": "event", "type": "model_call", "seq": seq, "at": at, "node": "rate", "actor": "rate",
                                "payload": {"tokens_in": 10, "tokens_out": 5}}
        run = {"task": "w", "events": [{"kind": "start", "node": "screen", "seq": 1, "at": 1.0}, {"kind": "start", "node": "rate", "seq": 2, "at": 1.0},
                                       call(3, 2.0), call(4, 3.0), {"kind": "done", "node": "screen", "seq": 5, "at": 4.0},
                                       {"kind": "event", "type": "model_call", "seq": 6, "at": 5.0, "node": None, "actor": "other", "payload": {"tokens_in": 99, "tokens_out": 1}}]}
        self.assertEqual(WorkflowRuns._median([run], "screen"), {"seconds": 3.0, "calls": 2, "tokens": 30})


class SyncTests(unittest.TestCase):
    def test_every_skill_gets_a_workflow_once(self):
        """TC-RUN-014 (sync, D-112): each skill of the shipped folder gets a workflow that names it and its pipeline, with the top steps of the pipeline as
        process nodes; a second sync saves nothing; a workflow that is not made from a skill (the review draft) is left alone.
        Example: summarize -> {"skill": "summarize", "pipeline": "summarize@1"}, process nodes ["summarize"]; second sync -> saved []."""
        # Given an empty library with the review draft in it
        runs, _ = make()
        runs.library.save("workflows", "review", {"nodes": [{"id": "q", "kind": "data"}], "edges": [], "implemented_by": "review_chat.run_review"}, "test")
        # When the skills are synced twice
        first = sync_skills(runs.library, runs.core)
        second = sync_skills(runs.library, runs.core)
        # Then the first sync saved summarize, the second nothing, and review is untouched
        self.assertIn("summarize", first["saved"])
        self.assertEqual(second["saved"], [])
        doc = runs.library.read("workflows", "summarize")["doc"]
        self.assertEqual((doc["skill"], doc["pipeline"]), ("summarize", "summarize@1"))
        self.assertEqual([n["id"] for n in doc["nodes"] if n["kind"] == "process"], ["summarize"])
        self.assertNotIn("skill", runs.library.read("workflows", "review")["doc"])
        self.assertIn("review", first["kept"])
        # And the synced workflow runs
        self.assertEqual(runs.run("summarize", None, INPUT, {}, "anna")["status"], "done")


if __name__ == "__main__":
    unittest.main()
