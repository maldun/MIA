"""
TC-N24-003 (REQ-WFX-019, REQ-RUN-012), N-2.4 integration step: the three parts of the Workflow execution wired as the app wires them (web_app.py): the real
Pipeline runner (`pipeline.Runner`) calls the real door (`tool_calls.ToolCalls`, scripted web functions, no network) and writes the real run events
(`run_events.RunEvents`, a fresh folder). The protected step test (tests/integration/N-2.4/step_03) runs each part behind its own interface; this test runs
them together. Run with: python tests/test_workflow_execution_wired.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                       # noqa: E402
from pipeline import Runner                                    # noqa: E402
from run_events import RunEvents                               # noqa: E402
from skill_store import parse_skill                            # noqa: E402
from tool_calls import ToolCalls                               # noqa: E402
from test_runner_interfaces import DOOR, FUNCTIONS, GRAPH, INPUT, SKILL     # noqa: E402

PAGE = "The tower is 330 m high. It was finished in 1889."


def search(query):
    return {"query": query, "results": [{"url": "https://example.org/a", "title": "A", "snippet": "The tower is 330 m high."}]}


def fetch(url):
    if url != "https://example.org/a":
        raise OSError("not found")
    return {"ref": url, "url": url, "title": "A", "text": PAGE}


class WiredWorkflowExecution(unittest.TestCase):

    def setUp(self):
        self.door = ToolCalls(web_search=search, fetch_page=fetch, trust=lambda url: {"class": "web", "score": 0.5})
        self.events = RunEvents(os.path.join(tempfile.mkdtemp(), "runs"))

    def run_towers(self, graph=GRAPH, **budget):
        skill = parse_skill(SKILL, "towers.md")
        skill["budget"].update(budget)
        runner = Runner(functions=FUNCTIONS, tool_calls=self.door, door_tools=DOOR, run_events=self.events)
        return runner.run(skill, graph, INPUT, user="u1", started_by="command")

    # REQ-RUN-012
    @mark.req("REQ-RUN-012", "REQ-WFX-019")
    def test_a_workflow_runs_through_the_real_door_and_log(self):
        """TC-N24-003: the real runner, door and run events together: the run is done, every tool call is in the log with its trust, in order.

        Example: search, read, check of "330 m" -> done, pass; tool_call events web_search/web, fetch_passages/web, number_check/code; order intact.
        """
        # Given: the real door and the real run events
        # When: the scripted workflow runs
        result = self.run_towers()
        # Then: it is done and the log holds the three calls with their trust, framed by run_start and run_end
        self.assertEqual((result.status, result.answer["status"]), ("done", "pass"))
        events = self.events.events(result.run_id)
        self.assertEqual((events[0]["type"], events[-1]["type"]), ("run_start", "run_end"))
        calls = [(e["payload"]["tool"], e["payload"]["trust"]) for e in events if e["type"] == "tool_call"]
        self.assertEqual(calls, [("web_search", "web"), ("fetch_passages", "web"), ("number_check", "code")])
        self.assertEqual(self.events.check_order(result.run_id), [])

    # REQ-WFX-019
    @mark.req("REQ-WFX-019", "REQ-RUN-012")
    def test_a_call_the_real_door_refuses_uses_no_budget(self):
        """TC-N24-003 (N-6 of the N-2.4.2 re-verification): a call the real door refuses as bad_arguments counts nothing, in the runner either.

        Example: budget search_calls 1, a skipped search with an unknown argument, then the search of the workflow -> done, no budget missing.
        """
        # Given: a first search with an argument web_search does not take, allowed to fail (skip), and a budget of one search
        graph = json.loads(json.dumps(GRAPH))
        graph["nodes"].insert(0, {"id": "bad", "kind": "tool", "tool": "web_search", "args": {"query": "$input.question", "typo": 1}, "output": "ignored",
                                  "on_error": "skip"})
        # When: the workflow runs
        result = self.run_towers(graph, search_calls=1)
        # Then: the refused search used no budget; the real one ran and the run is done
        self.assertEqual((result.status, result.missing), ("done", []))
        spent = [e["payload"]["used"] for e in self.events.events(result.run_id) if e["type"] == "budget_spent" and e["payload"]["name"] == "search_calls"]
        self.assertEqual(spent, [1])

    # REQ-WFX-019
    @mark.req("REQ-WFX-019")
    def test_a_used_up_budget_ends_the_run_and_names_it(self):
        """TC-N24-003: the second search over a budget of one ends the run with what is missing; the door ran one search.

        Example: two searches, budget search_calls 1 -> status budget, missing ["search_calls"].
        """
        # Given: a workflow with two searches and a budget of one
        graph = json.loads(json.dumps(GRAPH))
        graph["nodes"].insert(1, dict(graph["nodes"][0], id="search2", output="hits2"))
        # When: the workflow runs
        result = self.run_towers(graph, search_calls=1)
        # Then: the run ends with the budget named
        self.assertEqual((result.status, result.missing), ("budget", ["search_calls"]))


if __name__ == "__main__":
    unittest.main()
