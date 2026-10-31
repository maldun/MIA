"""
TC-RUN-012, TC-RUN-013 (REQ-RUN-012, REQ-RUN-013): the Pipeline runner reaches its neighbours only through their interfaces: the workflow through IF-203, the
tools through IF-402 (`ToolCalls.call`), the events through IF-401 (`RunEvents.emit`, beside the run log, D-120); and it names no workflow. With the mocks of the
three interfaces a scripted workflow the repository has never seen runs end to end. Run with: python tests/test_runner_interfaces.py
"""
import ast
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.join(HERE, "helpers", "mocks"))

from markers import mark                                       # noqa: E402
from core import Core                                          # noqa: E402
from library import Library                                    # noqa: E402
from pipeline import Runner                                    # noqa: E402
from run_workflow import WorkflowRuns                          # noqa: E402
from skill_store import parse_skill                            # noqa: E402
from if_203_workflow_library import WorkflowLibraryMock        # noqa: E402
from if_401_run_events import RunEventsMock                    # noqa: E402
from if_402_tool_calls import ToolCallsMock                    # noqa: E402

SKILL = """---
name: towers
version: 1
description: search, read, check a number
budget: {steps: 20, seconds: 60, search_calls: 2, fetch_calls: 2}
model: {profile: light}
tools: [web_search, fetch_passages, number_check]
pipeline: towers
---
"""
GRAPH = {"name": "towers", "version": 1, "result": "check",
         "nodes": [{"id": "search", "kind": "tool", "tool": "web_search", "args": {"query": "$input.question"}, "output": "hits"},
                   {"id": "pick", "kind": "code", "function": "first_url", "args": {"hits": "$hits"}, "output": "url"},
                   {"id": "read", "kind": "tool", "tool": "fetch_passages", "args": {"url": "$url", "question": "$input.question"}, "output": "page"},
                   {"id": "quotes", "kind": "code", "function": "quotes", "args": {"page": "$page"}, "output": "evidence"},
                   {"id": "check", "kind": "tool", "tool": "number_check", "args": {"claim": "$input.claim", "evidence": "$evidence"}, "output": "check"}]}
FUNCTIONS = {"first_url": lambda hits: hits[0]["url"], "quotes": lambda page: [p["quote"] for p in page["passages"]]}
DOOR = {"web_search": "search_calls", "fetch_passages": "fetch_calls", "number_check": None}
INPUT = {"question": "How high is the tower?", "claim": "The tower is 330 m high."}
SUMMARY = {"skill": "summarize", "nodes": [{"id": "text", "kind": "data"}, {"id": "summarize", "kind": "process"}, {"id": "answer", "kind": "data"}],
           "edges": [{"from": "text", "to": "summarize"}, {"from": "summarize", "to": "answer"}]}
PINS = {"MP-light": {"name": "gemma4:12b-it-qat", "digest": "38044be4f923"}}
RUNNER_MODULES = ("pipeline.py", "run_workflow.py")
ALLOWED = {"collections", "concurrent", "contextvars", "json", "math", "random", "re", "secrets", "statistics", "threading", "time",
           "events", "schema_check", "sandbox", "pipeline_model", "pipeline"}


class FakeModel:
    """a valid summary, 50 tokens in and 10 out a call"""
    def chat_with_usage(self, messages, schema=None, model=None, profile=None, options=None):
        return '{"summary": "A tall tower.", "key_points": ["330 m"]}', {"tokens_in": 50, "tokens_out": 10}

    def chat(self, messages, **kwargs):
        return self.chat_with_usage(messages, **kwargs)[0]


def imported_modules(path):
    """the top-level names a module imports; `from . import events` gives `events`, `from .schema_check import check` gives `schema_check`"""
    found = set()
    for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
            else:
                found.update(alias.name for alias in node.names)
    return found


def text_constants(path):
    return {node.value for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())) if isinstance(node, ast.Constant) and isinstance(node.value, str)}


class RunnerInterfaceTests(unittest.TestCase):

    def run_towers(self, tools, events, **budget):
        skill = parse_skill(SKILL, "towers.md")
        skill["budget"].update(budget)
        runner = Runner(functions=FUNCTIONS, tool_calls=tools, door_tools=DOOR, run_events=events)
        return runner.run(skill, GRAPH, INPUT, user="u1")

    def types(self, events, run_id):
        return [e["type"] for e in events.events(run_id)]

    # REQ-RUN-012
    @mark.req("REQ-RUN-012")
    def test_a_scripted_workflow_runs_through_the_three_mocks(self):
        """TC-RUN-012: a scripted workflow runs end to end with the mocks of IF-402 and IF-401.

        Example: search, read, check of "330 m" -> done, number_check pass, 3 tool calls through the door, events run_start ... run_end of user u1.
        """
        # Given: the mocks of the tool calls and the run events
        tools, events = ToolCallsMock(), RunEventsMock()
        # When: the scripted workflow runs
        result = self.run_towers(tools, events)
        # Then: it is done, every tool was called once through the door and the events are in order
        self.assertEqual(result.status, "done")
        self.assertEqual(result.answer["status"], "pass")
        self.assertEqual(tools._used[result.run_id], {"web_search": 1, "fetch_passages": 1, "number_check": 1})
        types = self.types(events, result.run_id)
        self.assertEqual(types[0], "run_start")
        self.assertEqual(types[-1], "run_end")
        self.assertEqual(types.count("tool_call"), 3)
        self.assertEqual(events.check_order(result.run_id), [])
        self.assertEqual({e["user"] for e in events.events(result.run_id)}, {"u1"})

    # REQ-RUN-012
    @mark.req("REQ-RUN-012")
    def test_a_used_up_budget_stops_before_the_door(self):
        """TC-RUN-012: a tool whose budget is used up is not called through the door.

        Example: budget search_calls 0 -> status budget, missing ["search_calls"], no call counted by IF-402.
        """
        # Given: a budget of no searches
        tools, events = ToolCallsMock(), RunEventsMock()
        # When: the scripted workflow runs
        result = self.run_towers(tools, events, search_calls=0)
        # Then: the run ends with the budget and the door counted nothing
        self.assertEqual(result.status, "budget")
        self.assertEqual(result.missing, ["search_calls"])
        self.assertEqual(tools._used.get(result.run_id, {}), {})

    # REQ-RUN-012
    @mark.req("REQ-RUN-012")
    def test_a_failing_source_is_a_visible_error(self):
        """TC-RUN-012: an error of IF-402 ends the step as an error that names it.

        Example: fetch_passages of an unknown page -> status error, "source_error" in the error, an error event in IF-401.
        """
        # Given: a door that knows no page
        tools, events = ToolCallsMock(pages={}), RunEventsMock()
        # When: the scripted workflow runs
        result = self.run_towers(tools, events)
        # Then: the run is an error that names the source error, and IF-401 has it
        self.assertEqual(result.status, "error")
        self.assertIn("source_error", result.error)
        self.assertIn("error", self.types(events, result.run_id))

    # REQ-RUN-012
    @mark.req("REQ-RUN-012")
    def test_the_workflow_is_read_through_the_library_mock(self):
        """TC-RUN-012: a workflow fetched through the mock of IF-203 runs and writes its events through IF-401.

        Example: workflow summary (skill summarize) in WorkflowLibraryMock -> status done, events run_start ... run_end of user u1.
        """
        # Given: the mock library holds the workflow and the core writes events through the IF-401 mock
        events = RunEventsMock()
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), os.path.join(tempfile.mkdtemp(), "runs"), model=FakeModel(), run_events=events)
        library = WorkflowLibraryMock()
        library.save("workflows", "summary", SUMMARY, "test")
        runs = WorkflowRuns(library, core, pins=PINS, held=lambda: {"gemma4:12b-it-qat": "38044be4f923e5a5"})
        # When: the workflow runs for user u1
        found = runs.run("summary", None, {"text": "The tower is 330 m high.", "sentences": 1}, {}, "u1")
        # Then: it is done and IF-401 holds its events
        self.assertEqual(found["status"], "done")
        types = self.types(events, found["run_id"])
        self.assertEqual((types[0], types[-1]), ("run_start", "run_end"))
        self.assertEqual({e["user"] for e in events.events(found["run_id"])}, {"u1"})

    # REQ-RUN-012
    @mark.req("REQ-RUN-012")
    def test_the_runner_imports_no_neighbour(self):
        """TC-RUN-012: the runner modules import no tool, library or log module of a neighbour.

        Example: imports of pipeline.py and run_workflow.py -> only the standard library and events, schema_check, sandbox, pipeline_model, pipeline.
        """
        # Given: the modules of the runner
        # When: their imports are read
        for name in RUNNER_MODULES:
            found = imported_modules(os.path.join(REPO, name))
            # Then: each import is an allowed one
            self.assertEqual(found - ALLOWED, set(), name)

    # REQ-RUN-013
    @mark.req("REQ-RUN-013")
    def test_no_workflow_is_named_in_the_runner(self):
        """TC-RUN-013: the runner modules name no shipped skill.

        Example: the text constants of pipeline.py and run_workflow.py -> none is the name of a file in skills/.
        """
        # Given: the names of the shipped skills
        names = {f[:-3] for f in os.listdir(os.path.join(REPO, "skills")) if f.endswith(".md")}
        # When: the text constants of the runner modules are read
        for name in RUNNER_MODULES:
            # Then: no constant is the name of a skill
            self.assertEqual(text_constants(os.path.join(REPO, name)) & names, set(), name)

    # REQ-RUN-013
    @mark.req("REQ-RUN-013")
    def test_one_runner_runs_two_new_entries(self):
        """TC-RUN-013: the same runner runs two entries it has never seen, without a change of code.

        Example: the towers graph and a one-step check graph on one Runner -> both done.
        """
        # Given: one runner and two graphs the repository does not ship
        runner = Runner(functions=FUNCTIONS, tool_calls=ToolCallsMock(), door_tools=DOOR, run_events=RunEventsMock())
        check_only = {"name": "check", "version": 1, "result": "check",
                       "nodes": [{"id": "check", "kind": "tool", "tool": "number_check", "args": {"claim": "$input.claim", "evidence": ["It is 330 m."]}, "output": "check"}]}
        # When: both run
        first = runner.run(parse_skill(SKILL, "towers.md"), GRAPH, INPUT, user="u1")
        second = runner.run(parse_skill(SKILL, "towers.md"), check_only, INPUT, user="u1")
        # Then: both are done
        self.assertEqual((first.status, second.status), ("done", "done"))

if __name__ == "__main__":
    unittest.main()
