"""
Tests of the harness against the mock of IF-105 (N-4.1 T-01): TC-EVL-001 repeats, intervals and cost, TC-EVL-004 versions in every header,
TC-EVL-008 equal cases, TC-EVL-011 the platform only through IF-105.
Run: python tests/test_eval_platform.py
"""
import ast
import importlib.util
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.join(HERE, "helpers", "mocks"))

import eval_platform as EP                            # noqa: E402
import harness as H                                   # noqa: E402
import metrics as M                                   # noqa: E402
from if_105_evaluation_access import EvaluationAccessMock  # noqa: E402
from markers import mark                              # noqa: E402
import contract                                       # noqa: E402  (the real IF-105 provider of the contract suite, read-only)


def load_eval_cli():
    """tools/eval.py as a module (its file name would shadow the builtin `eval`)"""
    spec = importlib.util.spec_from_file_location("eval_cli", os.path.join(REPO, "tools", "eval.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVAL_CLI = load_eval_cli()
PIN = EVAL_CLI.pin_record("MP-light")                 # the shape tools/eval.py hands to the harness: id MP-light, name = the model tag


class ScriptedPlatform(EvaluationAccessMock):
    """the mock of IF-105 whose outcome per case is scripted: the input names the verdict"""

    def run_case(self, workflow, version, inputs, options):
        result = super().run_case(workflow, version, inputs, options)
        result["outputs"] = dict(result["outputs"], status=inputs["verdict"])
        return result


def make_suite(root, verdicts, name="lookup_mock"):
    folder = os.path.join(root, name)
    os.makedirs(folder)
    with open(os.path.join(folder, "suite.json"), "w") as fp:
        json.dump({"name": name, "description": "t", "target": {"kind": "workflow", "workflow": "lookup", "version": 1}}, fp)
    with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
        for i, verdict in enumerate(verdicts):
            fp.write(json.dumps({"id": "c%d" % i, "input": {"question": "q%d" % i, "verdict": verdict}, "expect": "pass"}) + "\n")
    return H.load_suite(folder)


class PlatformHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.harness = H.Harness(platform=ScriptedPlatform())

    @mark.req("REQ-EVL-001", "REQ-EVL-011")
    def test_five_cases_three_repeats_counts_intervals_and_the_cost_of_the_runs(self):
        """TC-EVL-001"""
        suite = make_suite(self.tmp.name, ["pass", "pass", "pass", "pass", "fail"])
        run = self.harness.run(suite, repeats=3, pin=PIN)
        self.assertEqual(len(run.records), 15)
        table = {row["case"]: row for row in M.case_table(run.records)}
        self.assertEqual([table["c%d" % i]["passes"] for i in range(5)], [3, 3, 3, 3, 0])
        self.assertTrue(all(row["repeats"] == 3 for row in table.values()))
        overall = M.rate(sum(r["passes"] for r in table.values()), 15)
        self.assertEqual((overall["k"], overall["n"], round(overall["low"], 2), round(overall["high"], 2)), (12, 15, 0.55, 0.93))
        cost = M.cost(run.records)                                 # the mock's cost per run: 3 calls, 1800 tokens, 9.0 s
        self.assertEqual((cost["calls"], cost["tokens"], cost["seconds"]), (45, 27000, 135.0))
        report = H.format_report(run)
        self.assertIn("27000", report)
        self.assertIn("per case (passes / repeats):", report)
        self.assertRegex(report, r"c0 +3 of 3")
        self.assertRegex(report, r"c4 +0 of 3")

    def test_report_without_repeats_has_no_case_table(self):
        suite = make_suite(self.tmp.name, ["pass", "fail"])
        self.assertNotIn("per case", H.format_report(self.harness.run(suite, repeats=1, pin=PIN)))

    @mark.req("REQ-EVL-004")
    def test_every_header_carries_the_versions(self):
        """TC-EVL-004: 10 runs"""
        suite = make_suite(self.tmp.name, ["pass"])
        for i in range(10):
            header = self.harness.run(suite, repeats=1, pin=dict(PIN, seed=i)).header
            self.assertEqual((header["workflow"], header["workflow_version"]), ("lookup", 1))
            self.assertEqual((header["pin"]["id"], header["pin"]["seed"], header["pin"]["temperature"]), ("MP-light", i, 0))
            self.assertEqual(header["benchmark_version"], header["suite_sha1"])

    def test_the_options_reach_the_platform_and_a_run_without_a_pin_is_refused(self):
        suite = make_suite(self.tmp.name, ["pass"])
        run = self.harness.run(suite, pin=PIN)
        self.assertEqual(run.records[0]["status"], "pass")
        with self.assertRaises(H.SuiteError):
            self.harness.run(suite)

    def test_a_pin_the_platform_does_not_know_is_an_error_record_not_a_fallback(self):
        suite = make_suite(self.tmp.name, ["pass"])
        run = self.harness.run(suite, pin=dict(PIN, id="MP-huge"))
        self.assertTrue(run.records[0]["status"].startswith("error"))
        self.assertIn("pin_unavailable", run.records[0]["error"])

    @mark.req("REQ-EVL-008")
    def test_runs_with_different_case_lists_are_not_compared(self):
        """TC-EVL-008"""
        a = self.harness.run(make_suite(self.tmp.name, ["pass", "pass", "pass"], "s_a"), repeats=2, pin=PIN)
        same = self.harness.run(make_suite(self.tmp.name, ["pass", "fail", "pass"], "s_b"), repeats=2, pin=PIN)
        H.require_same_cases(a, same)                              # no error
        other = self.harness.run(make_suite(self.tmp.name, ["pass", "pass"], "s_c"), repeats=2, pin=PIN)
        with self.assertRaises(H.SuiteError) as caught:
            H.require_same_cases(a, other)
        self.assertIn("c2", str(caught.exception))
        fewer = self.harness.run(make_suite(self.tmp.name, ["pass", "pass", "pass"], "s_d"), repeats=1, pin=PIN)
        with self.assertRaises(H.SuiteError):
            H.require_same_cases(a, fewer)                         # the same repeats, too


class RealProvider(unittest.TestCase):
    @mark.req("REQ-EVL-004", "REQ-EVL-011")
    def test_the_pin_of_the_command_line_runs_on_the_real_provider(self):
        """REG (Verify F2): the harness sends the pin id to IF-105, so the real provider (run_workflow.WorkflowRuns) runs the case.

        Example: pin MP-light (model tag gemma4:12b-it-qat) on the workflow lookup -> status "42" (the answer); it was pin_unavailable.
        """
        # Given: the real IF-105 provider of the contract suite (fake model, the project's pins) and a workflow suite of one case
        with tempfile.TemporaryDirectory() as root:
            folder = os.path.join(root, "lookup_real")
            os.makedirs(folder)
            with open(os.path.join(folder, "suite.json"), "w") as fp:
                json.dump({"name": "lookup_real", "description": "t", "target": {"kind": "workflow", "workflow": "lookup", "version": 1, "status_field": "answer"}}, fp)
            with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
                fp.write(json.dumps({"id": "c0", "input": {"question": "q"}, "truth": True}) + "\n")
            suite = H.load_suite(folder)
            # When: the harness runs it with the pin as tools/eval.py builds it
            run = H.Harness(platform=contract.real_subject("IF-105")).run(suite, pin=PIN)
        # Then: the provider accepted the pin and ran the workflow (the fixture's judge step answers "42")
        self.assertEqual((run.records[0]["status"], run.records[0].get("error")), ("42", None))


class OnlyThroughIF105(unittest.TestCase):
    @mark.req("REQ-EVL-011")
    def test_the_adapter_imports_no_runner_library_or_store(self):
        """TC-EVL-011 (inspection) for the module that talks to the platform; the older targets of harness.py still use the in-process Core (see implementation-log)"""
        with open(os.path.join(REPO, "eval_platform.py"), encoding="utf-8") as fp:
            tree = ast.parse(fp.read())
        imported = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)}
        imported |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imported.discard("")
        self.assertEqual(imported - set(sys.stdlib_module_names), set())


if __name__ == "__main__":
    unittest.main()
