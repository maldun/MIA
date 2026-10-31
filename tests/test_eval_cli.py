"""
tools/eval.py on the command line (N-4.1 re-verification R5, R8; D-172): saved holdout runs are shown only with --holdout, and a missing or unknown
suite is a one-line error. Synthetic suites and runs in a temporary folder; no real suite or holdout is read.
Run: python tests/test_eval_cli.py
"""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

import harness as H                                   # noqa: E402
from markers import mark                              # noqa: E402


def load_eval_cli():
    """tools/eval.py as a module (its file name would shadow the builtin `eval`)"""
    spec = importlib.util.spec_from_file_location("eval_cli", os.path.join(REPO, "tools", "eval.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVAL_CLI = load_eval_cli()


def saved_run(folder, suite_name, variant, clock):
    """a run of a synthetic suite (one passing case `secret-case`), saved like tools/eval.py saves it"""
    suite = H.Suite(suite_name, "synthetic", {"kind": "fake"}, [{"id": "secret-case", "expect": "pass", "tags": []}])
    suite.path = None
    harness = H.Harness(clock=lambda: clock, targets={"fake": lambda case, v, s: ("pass", {})})
    with unittest.mock.patch.object(H, "suite_sha1", lambda path: {"cases.jsonl": "synthetic"}):
        return harness.run(suite, {"name": variant}).save(folder)


class CommandLine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runs = os.path.join(self.tmp.name, "runs")
        self.cfg = os.path.join(self.tmp.name, "cfg.json")
        with open(self.cfg, "w") as fp:
            json.dump({"accounts_dir": os.path.join(self.tmp.name, "db"), "eval_dir": self.runs}, fp)
        self.addCleanup(setattr, EVAL_CLI, "SUITES", EVAL_CLI.SUITES)
        EVAL_CLI.SUITES = os.path.join(self.tmp.name, "suites")
        os.makedirs(EVAL_CLI.SUITES)

    def main(self, *argv):
        """(exit message or None, printed text) of `eval.py <argv>`"""
        out = io.StringIO()
        with unittest.mock.patch.object(sys, "argv", ["eval.py", *argv, "--cfg", self.cfg]), contextlib.redirect_stdout(out):
            try:
                EVAL_CLI.main()
            except SystemExit as stopped:
                return str(stopped.code), out.getvalue()
        return None, out.getvalue()


class SavedHoldoutRuns(CommandLine):
    @mark.req("REQ-EVL-002")
    def test_report_refuses_a_saved_holdout_run_without_the_flag(self):
        """TC-EVL-002 (R5, D-172): `report` shows a saved run of a holdout suite only with --holdout, by name and by file.

        Example: report toy.holdout -> exit "... holdout ... --holdout", no case id printed; with --holdout the report names secret-case's suite.
        """
        # Given: a saved run of the synthetic suite toy.holdout
        path = saved_run(self.runs, "toy.holdout", "v", 1000.0)
        for name in ("toy.holdout", path):
            # When: it is reported without --holdout
            message, printed = self.main("report", name)
            # Then: refused with the flag named, nothing of the run printed
            self.assertIn("--holdout", message or "", name)
            self.assertNotIn("secret-case", printed + (message or ""))
        # And: with the flag it is reported
        message, printed = self.main("report", "toy.holdout", "--holdout")
        self.assertIsNone(message)
        self.assertIn("toy.holdout", printed)

    @mark.req("REQ-EVL-002")
    def test_compare_refuses_saved_holdout_runs_without_the_flag(self):
        """TC-EVL-002 (R5, D-172): `compare` of saved holdout runs needs --holdout, by suite and variants and by files.

        Example: compare toy.holdout a b -> exit naming --holdout; with --holdout the two runs are compared.
        """
        # Given: two saved runs of toy.holdout under the variants a and b
        first = saved_run(self.runs, "toy.holdout", "a", 1000.0)
        second = saved_run(self.runs, "toy.holdout", "b", 2000.0)
        for argv in (("compare", "toy.holdout", "a", "b"), ("compare", first, second)):
            # When: compared without --holdout
            message, printed = self.main(*argv)
            # Then: refused, nothing printed
            self.assertIn("--holdout", message or "", argv)
            self.assertNotIn("secret-case", printed)
        # And: with the flag they are compared
        message, printed = self.main("compare", "toy.holdout", "a", "b", "--holdout")
        self.assertIsNone(message)
        self.assertIn("A = toy.holdout/a", printed)

    @mark.req("REQ-EVL-002")
    def test_dev_runs_are_reported_as_before(self):
        """TC-EVL-002 (R5): a saved run of a dev suite needs no flag.

        Example: report toy -> the report of the run, exit none.
        """
        # Given: a saved run of a dev suite
        saved_run(self.runs, "toy", "v", 1000.0)
        # When: it is reported without a flag
        message, printed = self.main("report", "toy")
        # Then: the report is printed
        self.assertIsNone(message)
        self.assertIn("suite toy, variant v", printed)


if __name__ == "__main__":
    unittest.main()
