"""
TC-EVL-002 (N-4.1 T-02): a verdict is decided only on held-out cases. The guard refuses a dev-split run, decides a holdout run with eval_decide.py of the agent-app skill,
and the harness leaves cases tagged split:holdout out of a dev run.
Protected since A-63 (D-164). Run: python tests/acceptance/test_decide_guard.py
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
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

import decide_guard as G                              # noqa: E402
import harness as H                                   # noqa: E402
from markers import mark                              # noqa: E402

DECIDE = os.path.expanduser("~/.claude/skills/agent-app/scripts/eval_decide.py")


def write_run(folder, name, suite, rights, tag=None):
    """a run file: a header and one record per case; rights = list of True (status pass, truth true) or False (status fail, truth true)"""
    path = os.path.join(folder, name)
    with open(path, "w") as fp:
        fp.write(json.dumps({"kind": "header", "suite": suite, "variant": {"name": "v"}, "repeats": 1}) + "\n")
        for i, right in enumerate(rights):
            record = {"kind": "record", "case": "c%d" % i, "repeat": 0, "status": "pass" if right else "fail", "truth": True, "tags": [tag] if tag else []}
            fp.write(json.dumps(record) + "\n")
    return path


class Guard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    @mark.req("REQ-EVL-002")
    def test_a_dev_split_run_is_refused(self):
        """TC-EVL-002: a run of the dev split is not decided; the reason says dev split.

        Example: a run of the suite verdicts (no holdout name, no tags), 20 right -> ok False, "dev split".
        """
        # Given: a dev run
        run = write_run(self.tmp.name, "dev.jsonl", "verdicts", [True] * 20)
        # When: the guard checks it
        verdict = G.check_runs([run])
        # Then: refused
        self.assertFalse(verdict["ok"])
        self.assertIn("dev split", verdict["reason"])

    @mark.req("REQ-EVL-002")
    def test_a_mixed_or_unlabelled_run_is_refused_too(self):
        """TC-EVL-002: one dev run among holdout runs spoils the decision, and no run at all is no decision.

        Example: [verdicts.holdout, verdicts] -> ok False; [] -> ok False.
        """
        dev = write_run(self.tmp.name, "dev.jsonl", "verdicts", [True] * 5)
        hold = write_run(self.tmp.name, "hold.jsonl", "verdicts.holdout", [True] * 5)
        self.assertFalse(G.check_runs([hold, dev])["ok"])           # one dev run among the holdout runs spoils the decision
        self.assertFalse(G.check_runs([])["ok"])

    @mark.req("REQ-EVL-002")
    def test_holdout_runs_are_accepted_by_the_suite_name_or_the_tag(self):
        """TC-EVL-002: a holdout run is known by its suite name (*.holdout) or by every record tagged split:holdout.

        Example: verdicts.holdout, and verdicts with every record tagged split:holdout -> ok True.
        """
        by_name = write_run(self.tmp.name, "a.jsonl", "verdicts.holdout", [True] * 5)
        by_tag = write_run(self.tmp.name, "b.jsonl", "verdicts", [True] * 5, tag="split:holdout")
        self.assertTrue(G.check_runs([by_name, by_tag])["ok"])

    @unittest.skipUnless(os.path.exists(DECIDE), "eval_decide.py of the agent-app skill is not installed")
    @mark.req("REQ-EVL-002")
    def test_a_holdout_run_is_decided_by_the_rule_and_a_dev_run_is_not_decided(self):
        """TC-EVL-002: the holdout run is decided by eval_decide.py of the agent-app skill; the dev run is not decided.

        Example: 40 of 40 right -> PASS (min 0.9, low 0.8); 0 of 40 -> FAIL; a dev run of 40 right -> NOT DECIDED "dev split".
        """
        # Given: a good and a bad holdout run and a good dev run
        good = write_run(self.tmp.name, "good.jsonl", "verdicts.holdout", [True] * 40)
        bad = write_run(self.tmp.name, "bad.jsonl", "verdicts.holdout", [False] * 40)
        dev = write_run(self.tmp.name, "dev.jsonl", "verdicts", [True] * 40)
        # When / Then: the rule decides the holdout runs, the guard refuses the dev run
        self.assertEqual(G.decide([good], ["--metric", "right", "--min", "0.9", "--low", "0.8", "--fold", "majority"])["decision"], "PASS")
        self.assertEqual(G.decide([bad], ["--metric", "right", "--min", "0.9", "--low", "0.8"])["decision"], "FAIL")
        refused = G.decide([dev], ["--metric", "right", "--min", "0.9"])
        self.assertEqual(refused["decision"], "NOT DECIDED")
        self.assertIn("dev split", refused["reason"])


class NoOptionOverridesTheHoldout(unittest.TestCase):
    """Verify F5a: the options passed on to eval_decide.py cannot switch the split, and a re-run is checked like the run"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.hold = write_run(self.tmp.name, "hold.jsonl", "verdicts.holdout", [True] * 5)
        self.dev = write_run(self.tmp.name, "dev.jsonl", "verdicts", [True] * 5)

    def guard(self, *argv):
        """main() of the guard with eval_decide.py replaced: a refusal must come before it is called"""
        out = io.StringIO()
        with unittest.mock.patch.object(G.subprocess, "run", side_effect=AssertionError("eval_decide.py was called")), contextlib.redirect_stdout(out):
            code = G.main(list(argv))
        return code, out.getvalue()

    @mark.req("REQ-EVL-002")
    def test_a_split_option_is_refused_in_every_spelling(self):
        """TC-EVL-002 (regression, Verify F5a): `--split dev` after a holdout run decided on dev records; now any option that argparse reads as --split is refused.

        Example: --run hold.jsonl --split dev -> NOT DECIDED "--split", exit 2; the same for --split=dev and the abbreviation --spl dev.
        """
        for options in (["--split", "dev"], ["--split=dev"], ["--spl", "dev"], ["--split", "holdout"]):
            # Given: a holdout run, When: an option names the split
            code, out = self.guard("--run", self.hold, *options, "--metric", "right", "--min", "0.9")
            # Then: nothing is decided and the message names the option
            self.assertEqual(code, 2, options)
            self.assertIn("NOT DECIDED", out)
            self.assertIn("--split", out)

    @mark.req("REQ-EVL-002")
    def test_a_rerun_of_the_dev_split_is_refused_like_a_run(self):
        """TC-EVL-002 (regression, Verify F5a): the files of --rerun (fresh seeds after a FAIL) were passed on unchecked; now they must be holdout runs too.

        Example: --run hold.jsonl --rerun dev.jsonl -> NOT DECIDED "dev split: dev.jsonl"; also as --rerun=dev.jsonl and --rer dev.jsonl.
        """
        for options in (["--rerun", self.dev], ["--rerun=" + self.dev], ["--rer", self.dev], ["--run=" + self.dev]):
            # Given: a holdout run, When: a dev run comes in as a re-run (or as --run=)
            code, out = self.guard("--run", self.hold, *options, "--metric", "right")
            # Then: refused before eval_decide.py runs, with the file named
            self.assertEqual(code, 2, options)
            self.assertIn("dev split", out)
            self.assertIn("dev.jsonl", out)

    @mark.req("REQ-EVL-002")
    def test_a_holdout_rerun_is_passed_on_as_a_rerun(self):
        """TC-EVL-002: the files of --rerun reach eval_decide.py as --rerun after the check, with --split holdout fixed.

        Example: --run hold.jsonl --rerun hold2.jsonl -> eval_decide.py gets --split holdout --run hold.jsonl --rerun hold2.jsonl.
        """
        # Given: two holdout runs and a stand-in for eval_decide.py that records its command
        again = write_run(self.tmp.name, "hold2.jsonl", "verdicts.holdout", [True] * 5)
        seen = {}

        def fake_run(command, **_):
            seen["command"] = command
            return unittest.mock.Mock(stdout=json.dumps({"verdict": "PASS"}), stderr="")
        # When: the guard decides
        with unittest.mock.patch.object(G.subprocess, "run", side_effect=fake_run), contextlib.redirect_stdout(io.StringIO()):
            code = G.main(["--run", self.hold, "--rerun", again, "--metric", "right"])
        # Then: the split is fixed and the re-run is passed on
        self.assertEqual(code, 0)
        command = seen["command"]
        self.assertEqual(command[command.index("--split") + 1], "holdout")
        self.assertEqual(command[command.index("--rerun") + 1], again)
        self.assertEqual(command.count("--split"), 1)


def load_eval_cli():
    """tools/eval.py as a module (its file name would shadow the builtin `eval`)"""
    spec = importlib.util.spec_from_file_location("eval_cli", os.path.join(REPO, "tools", "eval.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HoldoutSuitesOnTheCommandLine(unittest.TestCase):
    """Verify F5b, D-164: tools/eval.py hides holdout suites from list and refuses cases and run on them unless --holdout is given (synthetic suites)"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cli = load_eval_cli()
        self.cli.SUITES = os.path.join(self.tmp.name, "suites")
        for name in ("toy", "toy.holdout"):
            folder = os.path.join(self.cli.SUITES, name)
            os.makedirs(folder)
            with open(os.path.join(folder, "suite.json"), "w") as fp:
                json.dump({"name": name, "description": "synthetic " + name, "target": {"kind": "text_rules"}}, fp)
            with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
                fp.write(json.dumps({"id": "secret-case" if name.endswith("holdout") else "open-case", "input": {"text": "Hello."},
                                     "gold": {"rules": []}, "expect": "pass", "note": "synthetic"}) + "\n")
        self.cfg = os.path.join(self.tmp.name, "cfg.json")
        with open(self.cfg, "w") as fp:
            json.dump({"accounts_dir": os.path.join(self.tmp.name, "db"), "eval_dir": os.path.join(self.tmp.name, "runs")}, fp)

    def main(self, *argv):
        out = io.StringIO()
        with unittest.mock.patch.object(sys, "argv", ["eval.py", *argv, "--cfg", self.cfg]), contextlib.redirect_stdout(out):
            self.cli.main()
        return out.getvalue()

    def watch_reads(self):
        """the names of the suite folders that harness.load_suite is asked to read from now on: the fixtures are valid, so the only sign that a
        held-out suite was opened is the call itself (A-68, N-4.1 R4)"""
        reads = []
        real = self.cli.harness.load_suite

        def spy(folder):
            reads.append(os.path.basename(os.path.normpath(folder)))
            return real(folder)
        patcher = unittest.mock.patch.object(self.cli.harness, "load_suite", spy)
        patcher.start()
        self.addCleanup(patcher.stop)
        return reads

    @mark.req("REQ-EVL-002")
    def test_list_shows_no_holdout_suite(self):
        """TC-EVL-002 (regression, Verify F5b): `eval.py list` loaded and counted every holdout suite.

        Example: suites toy and toy.holdout -> list names toy only.
        """
        reads = self.watch_reads()
        # When: the suites are listed without --holdout
        out = self.main("list")
        # Then: only the dev suite is there, and the holdout suite was not even read
        self.assertIn("toy ", out)
        self.assertNotIn("toy.holdout", out)
        self.assertNotIn("toy.holdout", reads)

    @mark.req("REQ-EVL-002")
    def test_cases_and_run_refuse_a_holdout_suite_without_the_flag(self):
        """TC-EVL-002 (regression, Verify F5b): `cases toy.holdout` printed the held-out cases and `run toy.holdout` ran them.

        Example: cases toy.holdout -> exit "toy.holdout is a holdout suite: only with --holdout (Verify)"; no case id printed, no run saved.
        """
        reads = self.watch_reads()
        for argv in (("cases", "toy.holdout"), ("run", "toy.holdout", "--pin", "MP-light")):
            # When: a holdout suite is named without --holdout
            with self.assertRaises(SystemExit) as stopped:
                out = self.main(*argv)
            # Then: refused with the flag named, nothing of the suite shown or saved
            self.assertIn("--holdout", str(stopped.exception.code), argv)
            self.assertNotIn("secret-case", str(stopped.exception.code))
        self.assertFalse(os.path.isdir(os.path.join(self.tmp.name, "runs")))
        # And: refused before anything of it was read (A-68, N-4.1 R4)
        self.assertNotIn("toy.holdout", reads)

    @mark.req("REQ-EVL-002")
    def test_with_the_flag_the_holdout_suite_is_listed_and_shown(self):
        """TC-EVL-002: with --holdout (the Verify run) the holdout suite is listed and its cases are shown.

        Example: list --holdout -> toy and toy.holdout; cases toy.holdout --holdout -> the synthetic case secret-case.
        """
        self.assertIn("toy.holdout", self.main("list", "--holdout"))
        self.assertIn("secret-case", self.main("cases", "toy.holdout", "--holdout"))


class HarnessKeepsHoldoutOut(unittest.TestCase):
    @mark.req("REQ-EVL-002")
    def test_a_dev_run_never_selects_a_case_tagged_split_holdout(self):
        """TC-EVL-002: the harness never reads a case tagged split:holdout in a dev run, not even by name; a holdout suite has all.

        Example: cases a, b (split:holdout), c (split:dev) -> the suite verdicts selects a, c; only=["b"] selects nothing; verdicts.holdout selects a, b, c.
        """
        cases = [{"id": "a", "tags": []}, {"id": "b", "tags": ["split:holdout"]}, {"id": "c", "tags": ["split:dev"]}]
        dev = H.Suite("verdicts", "", {"kind": "fake"}, cases)
        self.assertEqual([c["id"] for c in dev.select()], ["a", "c"])
        self.assertEqual([c["id"] for c in dev.select(only=["b"])], [])        # not even by name
        holdout = H.Suite("verdicts.holdout", "", {"kind": "fake"}, cases)
        self.assertEqual([c["id"] for c in holdout.select()], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
