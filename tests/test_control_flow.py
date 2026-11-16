"""
The controllers control.branch, control.map and control.loop (T-CV-06/07 part, G-V2.CONVERT, D-258; REQ-WFM-058): the construct JSON of a pipeline is run by control_flow.run_construct,
the calls of library nodes are injected, so no model and no toolbox are needed. The semantics are those of the old runner (pipeline.py _do_branch, _do_loop, _do_map).
Run: python tests/test_control_flow.py
"""
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import control_flow as CF                                    # noqa: E402
from pipeline import BudgetExceeded, NodeError               # noqa: E402


class Calls:
    """a fake `call(use, args)`: records every call, answers by node id from `answers` (a value or a function of the args)"""
    def __init__(self, **answers):
        self.answers, self.seen = answers, []

    def __call__(self, use, args):
        self.seen.append((use, args))
        answer = self.answers[use]
        if isinstance(answer, Exception):
            raise answer
        return answer(args) if callable(answer) else answer


def step(id, use, output=None, **wire):
    return {"id": id, "use": use, "wire": wire, **({"output": output} if output else {})}


class Branch(unittest.TestCase):
    NODE = {"id": "b", "kind": "branch", "if": {"ref": "verdict.status", "op": "==", "value": "inconclusive"},
            "then": [step("fix", "fix@1", "verdict", claim="$input.claim")], "else": [step("keep", "keep@1", "note")]}

    def test_the_then_part_runs_when_the_condition_holds(self):
        """Example: verdict.status is inconclusive, so fix runs with the claim of the input and writes verdict."""
        # Given a branch and a variable that makes the condition true
        calls = Calls(**{"fix@1": {"status": "ok"}})
        # When it runs
        out = CF.run_construct(self.NODE, {"verdict": {"status": "inconclusive"}, "input.claim": "c"}, {"verdict": None, "note": None}, calls)
        # Then fix ran with the resolved claim and the new verdict is written, note stays empty
        self.assertEqual(calls.seen, [("fix@1", {"claim": "c"})])
        self.assertEqual(out, {"outputs": {"verdict": {"status": "ok"}, "note": None}})

    def test_the_else_part_runs_otherwise(self):
        """Example: verdict.status is true, so keep runs and verdict passes through unchanged."""
        calls = Calls(**{"keep@1": "kept"})
        out = CF.run_construct(self.NODE, {"verdict": {"status": "true"}, "input.claim": "c"}, {"verdict": None, "note": None}, calls)
        self.assertEqual(calls.seen, [("keep@1", {})])
        self.assertEqual(out["outputs"], {"verdict": {"status": "true"}, "note": "kept"})

    def test_a_missing_else_is_an_empty_part(self):
        """Example: a branch without else and a false condition runs nothing and returns what it was given."""
        node = {"id": "b", "kind": "branch", "if": {"ref": "x", "op": "true"}, "then": [step("s", "s@1", "y")]}
        calls = Calls(**{"s@1": 1})
        out = CF.run_construct(node, {"x": False, "y": "old"}, {"y": None}, calls)
        self.assertEqual((calls.seen, out["outputs"]), ([], {"y": "old"}))


class Loop(unittest.TestCase):
    NODE = {"id": "again", "kind": "loop", "max": 3, "until": {"ref": "verdict.status", "op": "!=", "value": "inconclusive"},
            "body": [step("rerun", "rerun@1", "verdict", script="$written")]}

    def test_it_stops_when_until_holds(self):
        """Example: the second run gives a verdict, so the body runs twice and not three times."""
        answers = iter([{"status": "inconclusive"}, {"status": "true"}, {"status": "never"}])
        calls = Calls(**{"rerun@1": lambda args: next(answers)})
        out = CF.run_construct(self.NODE, {"verdict": {"status": "inconclusive"}, "written": "s"}, {"verdict": None}, calls)
        self.assertEqual(len(calls.seen), 2)
        self.assertEqual(out["outputs"]["verdict"], {"status": "true"})

    def test_it_stops_at_max(self):
        """Example: the verdict never changes, so the body runs max = 3 times and the loop ends without an error."""
        calls = Calls(**{"rerun@1": {"status": "inconclusive"}})
        CF.run_construct(self.NODE, {"verdict": {"status": "inconclusive"}, "written": "s"}, {"verdict": None}, calls)
        self.assertEqual(len(calls.seen), 3)

    def test_the_body_runs_once_before_until_is_tested(self):
        """Example: until is true from the start, the body still runs once (the old runner tests after the body)."""
        calls = Calls(**{"rerun@1": {"status": "true"}})
        CF.run_construct(self.NODE, {"verdict": {"status": "true"}, "written": "s"}, {"verdict": None}, calls)
        self.assertEqual(len(calls.seen), 1)


class Map(unittest.TestCase):
    NODE = {"id": "read", "kind": "map", "over": "$urls", "as": "address", "collect": "page", "output": "pages",
            "body": [step("fetch", "fetch@1", "page", url="$address")]}

    def test_the_results_are_collected_in_order(self):
        """Example: three addresses give three pages in the order of the addresses; `as` is a name inside the body only."""
        calls = Calls(**{"fetch@1": lambda args: "page of " + args["url"]})
        out = CF.run_construct(self.NODE, {"urls": ["a", "b", "c"]}, {"pages": None}, calls)
        self.assertEqual(out["outputs"]["pages"], ["page of a", "page of b", "page of c"])

    def test_an_error_with_skip_leaves_none_at_that_place(self):
        """Example: the second fetch fails and has on_error skip: the list is [page a, None, page c] and the run goes on."""
        node = {**self.NODE, "body": [{**self.NODE["body"][0], "on_error": "skip"}]}
        calls = Calls(**{"fetch@1": lambda args: (_ for _ in ()).throw(RuntimeError("down")) if args["url"] == "b" else "page " + args["url"]})
        out = CF.run_construct(node, {"urls": ["a", "b", "c"]}, {"pages": None}, calls)
        self.assertEqual(out["outputs"]["pages"], ["page a", None, "page c"])

    def test_an_error_without_a_policy_fails_the_node(self):
        """Example: no on_error means fail: NodeError names the node."""
        calls = Calls(**{"fetch@1": RuntimeError("down")})
        with self.assertRaises(NodeError) as caught:
            CF.run_construct(self.NODE, {"urls": ["a"]}, {"pages": None}, calls)
        self.assertIn("fetch", str(caught.exception))

    def test_a_default_policy_gives_the_default(self):
        """Example: on_error default with default "none" puts "none" in the list."""
        node = {**self.NODE, "body": [{**self.NODE["body"][0], "on_error": "default", "default": "none"}]}
        out = CF.run_construct(node, {"urls": ["a"]}, {"pages": None}, Calls(**{"fetch@1": RuntimeError("x")}))
        self.assertEqual(out["outputs"]["pages"], ["none"])

    def test_over_must_be_a_list(self):
        """Example: over a text is refused with NodeError, not iterated by letters."""
        with self.assertRaises(NodeError):
            CF.run_construct(self.NODE, {"urls": "abc"}, {"pages": None}, Calls())

    def test_several_workers_give_the_same_list(self):
        """Example: workers 3 over five addresses gives the same ordered list as one worker."""
        node = {**self.NODE, "workers": 3}
        calls = Calls(**{"fetch@1": lambda args: args["url"].upper()})
        out = CF.run_construct(node, {"urls": list("abcde")}, {"pages": None}, calls)
        self.assertEqual(out["outputs"]["pages"], list("ABCDE"))


class Nested(unittest.TestCase):
    def test_a_loop_inside_a_branch_sees_and_changes_the_outer_variables(self):
        """Example: the shape of verify.computable: a branch whose then part is a loop that rewrites `written` and `verdict`."""
        # Given a branch (verdict inconclusive) with a loop of fix and rerun
        loop = {"id": "again", "kind": "loop", "max": 2, "until": {"ref": "verdict.status", "op": "!=", "value": "inconclusive"},
                "body": [step("fix", "fix@1", "written", problem="$verdict.detail"), step("rerun", "rerun@1", "verdict", script="$written.script")]}
        node = {"id": "repair", "kind": "branch", "if": {"ref": "verdict.status", "op": "==", "value": "inconclusive"}, "then": [loop]}
        calls = Calls(**{"fix@1": {"script": "new"}, "rerun@1": {"status": "true"}})
        # When it runs
        out = CF.run_construct(node, {"verdict": {"status": "inconclusive", "detail": "d"}, "written": {"script": "old"}}, {"verdict": None, "written": None}, calls)
        # Then fix got the detail, rerun the new script, and both variables leave the node changed
        self.assertEqual(calls.seen, [("fix@1", {"problem": "d"}), ("rerun@1", {"script": "new"})])
        self.assertEqual(out["outputs"], {"verdict": {"status": "true"}, "written": {"script": "new"}})


class Limits(unittest.TestCase):
    def test_the_seconds_budget_ends_the_run(self):
        """Example: with 5 seconds allowed and a clock that jumps 10 s, the next node raises BudgetExceeded and no more node runs."""
        clock = iter([0, 0, 10, 10, 10])
        limits = CF.Limits(seconds=5, clock=lambda: next(clock))
        node = {"id": "l", "kind": "loop", "max": 5, "body": [step("s", "s@1", "y")]}
        calls = Calls(**{"s@1": 1})
        with self.assertRaises(BudgetExceeded):
            CF.run_construct(node, {}, {"y": None}, calls, limits)
        self.assertLessEqual(len(calls.seen), 1)

    def test_the_steps_budget_ends_the_run(self):
        """Example: 2 steps allowed, a loop of max 5 runs two node runs and then raises BudgetExceeded."""
        limits = CF.Limits(steps=2)
        node = {"id": "l", "kind": "loop", "max": 5, "body": [step("s", "s@1", "y")]}
        calls = Calls(**{"s@1": 1})
        with self.assertRaises(BudgetExceeded):
            CF.run_construct(node, {}, {"y": None}, calls, limits)
        self.assertEqual(len(calls.seen), 2 - 1)        # the loop node itself counts as a step, like in the old runner

    def test_a_stop_request_ends_the_run(self):
        """Example: should_stop is true from the start: the run raises Stopped before the first call."""
        from pipeline import Stopped
        limits = CF.Limits(should_stop=lambda: True)
        with self.assertRaises(Stopped):
            CF.run_construct({"id": "l", "kind": "loop", "max": 1, "body": [step("s", "s@1", "y")]}, {}, {"y": None}, Calls(**{"s@1": 1}), limits)


class Inputs(unittest.TestCase):
    def test_the_fields_of_the_input_are_nested_for_references(self):
        """Example: the edge name input.claim is read by the reference $input.claim."""
        node = {"id": "b", "kind": "branch", "if": {"ref": "input.claim", "op": "not_empty"}, "then": [step("s", "s@1", "y", claim="$input.claim")]}
        calls = Calls(**{"s@1": 1})
        CF.run_construct(node, {"input.claim": "c"}, {"y": None}, calls)
        self.assertEqual(calls.seen, [("s@1", {"claim": "c"})])

    def test_an_unknown_reference_is_a_node_error(self):
        """Example: $nothing is not a variable: NodeError, like the old runner."""
        node = {"id": "b", "kind": "branch", "if": {"ref": "x", "op": "true"}, "then": [step("s", "s@1", "y", a="$nothing")]}
        with self.assertRaises(NodeError):
            CF.run_construct(node, {"x": True}, {"y": None}, Calls(**{"s@1": 1}))


if __name__ == "__main__":
    unittest.main()
