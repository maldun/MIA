"""
Tests of the harness against the mock of IF-105 (N-4.1 T-01): TC-EVL-001 repeats, intervals and cost, TC-EVL-004 versions in every header,
TC-EVL-008 equal cases, TC-EVL-011 the platform only through IF-105.
Run: python tests/test_eval_platform.py
"""
import ast
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

PIN = {"name": "MP-light", "digest": "sha256:test", "seed": 7, "temperature": 0}


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
            self.assertEqual((header["pin"]["name"], header["pin"]["seed"], header["pin"]["temperature"]), ("MP-light", i, 0))
            self.assertEqual(header["benchmark_version"], header["suite_sha1"])

    def test_the_options_reach_the_platform_and_a_run_without_a_pin_is_refused(self):
        suite = make_suite(self.tmp.name, ["pass"])
        run = self.harness.run(suite, pin=PIN)
        self.assertEqual(run.records[0]["status"], "pass")
        with self.assertRaises(H.SuiteError):
            self.harness.run(suite)

    def test_a_pin_the_platform_does_not_know_is_an_error_record_not_a_fallback(self):
        suite = make_suite(self.tmp.name, ["pass"])
        run = self.harness.run(suite, pin=dict(PIN, name="MP-huge"))
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
