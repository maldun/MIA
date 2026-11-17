"""
Tools on the converted path (T-CV-06a, G-V2.CONVERT; owner decisions 2026-11-16): tool_step counts the calls of a run against the skill's budget keys, goes through the IF-402 door
when the app gives one, records tool_call and budget_spent events, and a budget end gives the status budget with its reason. No model, no network.
Run: python tests/test_converted_tools.py
"""
import contextvars
import os
import sys
import threading
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers")):
    sys.path.insert(0, path)

import common_operations as ops                          # noqa: E402
import control_flow as CF                                # noqa: E402
import skill_converter                                   # noqa: E402
from call_recording import ScriptedModel                 # noqa: E402
from pipeline import BudgetExceeded, Tool                # noqa: E402
import plain_modules                                       # noqa: E402

setUpModule, tearDownModule = plain_modules.hooks()      # the package MIA is not importable while this module runs: F-3, tests/plain_modules.py

SKILLS, LIBRARY = os.path.join(REPO, "skills"), os.path.join(REPO, "library")
SEARCH = {"tool": "web_search", "settings": {}}


class Refusal(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class Door:
    """a stand-in for ToolCalls.call(run, tool, args) of IF-402"""
    def __init__(self, answer=None, refuse=None):
        self.answer, self.refuse, self.seen = answer or {"output": "found", "trust": "untrusted"}, refuse, []

    def call(self, run, name, args):
        self.seen.append((run, name, args))
        if self.refuse:
            raise Refusal(self.refuse)
        return self.answer


class Counting(unittest.TestCase):
    def setUp(self):
        ops.reset()
        self.addCleanup(ops.reset)
        self.asked = []
        ops.register_tool("web_search", lambda query: self.asked.append(query) or ["hit"])

    def start(self, **more):
        ops.register_run(budget={"search_calls": 2}, tool_keys={"web_search": "search_calls"}, **more)

    def test_a_call_over_the_limit_raises_and_is_not_made(self):
        """Example: search_calls 2: the third call raises BudgetExceeded("search_calls") before the tool runs; the budget end is remembered."""
        # Given a run with two search calls allowed
        self.start()
        # When three calls are made
        ops.tool_step({"tool": SEARCH, "query": "a"})
        ops.tool_step({"tool": SEARCH, "query": "b"})
        with self.assertRaises(BudgetExceeded) as caught:
            ops.tool_step({"tool": SEARCH, "query": "c"})
        # Then the third was not made and the reason is the key
        self.assertEqual((self.asked, caught.exception.args[0], ops.budget_end()), (["a", "b"], "search_calls", "search_calls"))

    def test_budget_spent_events_say_used_and_limit(self):
        """Example: the first call records budget_spent with name search_calls, used 1, limit 2, and a tool_call event without a trust label (plain function)."""
        self.start()
        ops.tool_step({"tool": SEARCH, "query": "a"})
        events = ops.run_events()
        self.assertIn({"kind": "budget_spent", "name": "search_calls", "amount": 1, "used": 1, "limit": 2}, events)
        self.assertIn({"kind": "tool_call", "tool": "web_search", "trust": None}, events)

    def test_a_tool_without_a_budget_key_is_not_counted(self):
        """Example: a tool the run gave no key is called any number of times."""
        ops.register_run(budget={"search_calls": 1}, tool_keys={})
        for _ in range(5):
            ops.tool_step({"tool": SEARCH, "query": "a"})
        self.assertEqual(len(self.asked), 5)

    def test_parallel_calls_are_counted_exactly(self):
        """Example: 8 threads call a tool with limit 5: exactly 5 calls are made, 3 raise."""
        ops.register_run(budget={"search_calls": 5}, tool_keys={"web_search": "search_calls"})
        failures = []

        def one():
            try:
                ops.tool_step({"tool": SEARCH, "query": "x"})
            except BudgetExceeded:
                failures.append(1)
        # the threads of a parallel map are started with a copy of the run's context (control_flow._map); the state of a run is per run since F-01
        threads = [threading.Thread(target=contextvars.copy_context().run, args=(one,)) for _ in range(8)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual((len(self.asked), len(failures)), (5, 3))

    def test_a_tool_inside_a_map_is_counted_too(self):
        """Example: a map over 4 queries with limit 2 stops with BudgetExceeded inside the controller, and the end is remembered."""
        self.start()
        node = {"id": "m", "kind": "map", "over": "$qs", "as": "q", "collect": "r", "output": "rs", "body": [{"id": "s", "use": "tool.web_search@1", "wire": {"query": "$q"}, "output": "r"}]}
        with self.assertRaises(BudgetExceeded):
            CF.run_construct(node, {"qs": list("abcd")}, {"rs": None}, lambda use, args: ops.tool_step({"tool": SEARCH, **args}))
        self.assertEqual(self.asked, ["a", "b"])


class Door_(unittest.TestCase):
    def setUp(self):
        ops.reset()
        self.addCleanup(ops.reset)

    def start(self, door, budget=None):
        ops.register_run(budget=budget or {"search_calls": 12}, tool_keys={"web_search": "search_calls"}, door=door, door_tools={"web_search": "search_calls"}, run_id="r1")

    def test_a_door_tool_goes_through_the_door_with_the_limits_and_keeps_the_trust_label(self):
        """Example: the door gets run id r1, the limit 12 for web_search and the arguments; the output is returned and tool_call records trust untrusted."""
        door = Door()
        self.start(door)
        out = ops.tool_step({"tool": SEARCH, "query": "a"})
        self.assertEqual(out, "found")
        self.assertEqual(door.seen, [({"id": "r1", "limits": {"web_search": 12}}, "web_search", {"query": "a"})])
        self.assertIn({"kind": "tool_call", "tool": "web_search", "trust": "untrusted"}, ops.run_events())

    def test_a_refusal_the_door_does_not_count_gives_the_call_back(self):
        """Example: with a limit of 1 the door refuses three calls with bad_arguments: all three raise the refusal and none a BudgetExceeded, because each reserved call was given back."""
        self.start(Door(refuse="bad_arguments"), budget={"search_calls": 1})
        for _ in range(3):
            with self.assertRaises(Refusal):
                ops.tool_step({"tool": SEARCH, "query": "a"})

    def test_the_budget_code_of_the_door_is_a_budget_end(self):
        """Example: the door says budget: BudgetExceeded with the key, remembered as the end of the run."""
        self.start(Door(refuse="budget"))
        with self.assertRaises(BudgetExceeded):
            ops.tool_step({"tool": SEARCH, "query": "a"})
        self.assertEqual(ops.budget_end(), "search_calls")

    def test_an_unregistered_tool_is_refused_even_with_a_door(self):
        """Example: a descriptor that names a tool neither registered nor a door tool raises ToolMissing."""
        self.start(Door())
        with self.assertRaises(ops.ToolMissing):
            ops.tool_step({"tool": {"tool": "delete_everything", "settings": {}}})


class RunLevel(unittest.TestCase):
    def test_a_research_run_over_its_search_budget_ends_with_status_budget(self):
        """Example: research with search_calls 0 ends with status budget, the error names search_calls, the events hold the budget_spent and the tool was never called."""
        asked = []
        tools = {"web_search": Tool(lambda **kw: asked.append(kw) or [], "search_calls"), "fetch_page": Tool(lambda **kw: {"text": ""}, "fetch_calls")}
        run = skill_converter.run_converted("research", {"question": "When did the Rivertown Bridge open to traffic?"}, model=ScriptedModel(), tools=tools,
                                            skills_dir=SKILLS, library_dir=LIBRARY, skill_changes={"budget": {"search_calls": 0}})
        self.assertEqual(run.status, "budget", run.error)
        self.assertIn("search_calls", run.error)
        self.assertEqual(asked, [])
        self.assertTrue(any(e["kind"] == "budget_spent" and e["name"] == "search_calls" for e in run.events))

    def test_a_run_inside_its_budgets_is_done_and_has_tool_events(self):
        """Example: research with the skill's own budget on scripted replies is done; the events include a tool_call of web_search."""
        tools = {"web_search": Tool(lambda **kw: [], "search_calls"), "fetch_page": Tool(lambda **kw: {"text": ""}, "fetch_calls")}
        run = skill_converter.run_converted("research", {"question": "When did the Rivertown Bridge open to traffic?"}, model=ScriptedModel(), tools=tools,
                                            skills_dir=SKILLS, library_dir=LIBRARY)
        self.assertEqual(run.status, "done", run.error)
        self.assertTrue(any(e["kind"] == "tool_call" and e["tool"] == "web_search" for e in run.events))


if __name__ == "__main__":
    unittest.main()
