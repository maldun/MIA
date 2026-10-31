"""
Tests of the harness against the mock of IF-105 (N-4.1 T-01): TC-EVL-001 repeats, intervals and cost, TC-EVL-004 versions in every header,
TC-EVL-008 equal cases, TC-EVL-011 the platform only through IF-105.
Protected since A-63 (D-164). Run: python tests/acceptance/test_eval_platform.py
"""
import ast
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers", "mocks"))

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
    """the mock of IF-105 whose outcome per case is scripted: the input names the verdict; `started` counts the runs it was asked for"""

    started = 0

    def run_case(self, workflow, version, inputs, options):
        self.started += 1
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
        """TC-EVL-001: the report lists every case with its repeats and passes, the 95 % Wilson interval and the summed cost of the runs.

        Example: 5 cases (4 pass, 1 fails) x 3 repeats on the mock of IF-105 -> 12 of 15, interval 0.55 to 0.93, 45 calls, 27000 tokens, 135 s.
        """
        # Given: a suite of 5 scripted cases
        suite = make_suite(self.tmp.name, ["pass", "pass", "pass", "pass", "fail"])
        # When: it runs 3 times through the mock
        run = self.harness.run(suite, repeats=3, pin=PIN)
        # Then: 15 records, the passes per case, the interval (Wilson, checked by hand: 0.548 to 0.930) and the cost
        self.assertEqual(len(run.records), 15)
        table = {row["case"]: row for row in M.case_table(run.records)}
        self.assertEqual([table["c%d" % i]["passes"] for i in range(5)], [3, 3, 3, 3, 0])
        self.assertTrue(all(row["repeats"] == 3 for row in table.values()))
        overall = M.rate(sum(r["passes"] for r in table.values()), 15)
        self.assertEqual((overall["k"], overall["n"], round(overall["low"], 2), round(overall["high"], 2)), (12, 15, 0.55, 0.93))
        cost = M.cost(run.records)                                 # the mock's cost per run: 3 calls, 1800 tokens, 9.0 s
        self.assertEqual((cost["calls"], cost["tokens"], cost["seconds"]), (45, 27000, 135.0))
        # And: the report prints the table per case
        report = H.format_report(run)
        self.assertIn("27000", report)
        self.assertIn("per case (passes / repeats):", report)
        self.assertRegex(report, r"c0 +3 of 3")
        self.assertRegex(report, r"c4 +0 of 3")

    @mark.req("REQ-EVL-001")
    def test_report_without_repeats_has_no_case_table(self):
        """TC-EVL-001: a run without repeats has no table per case (one run per case says nothing about stability).

        Example: 2 cases x 1 run -> no "per case" in the report.
        """
        suite = make_suite(self.tmp.name, ["pass", "fail"])
        self.assertNotIn("per case", H.format_report(self.harness.run(suite, repeats=1, pin=PIN)))

    @mark.req("REQ-EVL-004")
    def test_every_header_carries_the_versions(self):
        """TC-EVL-004: every run header carries workflow, workflow version, model pin, seed, temperature and benchmark version.

        Example: 10 runs of lookup v1 with seeds 0..9 -> each header: lookup, 1, MP-light, its seed, 0, benchmark_version = suite_sha1.
        """
        # Given: a workflow suite of one case
        suite = make_suite(self.tmp.name, ["pass"])
        for i in range(10):
            # When: run i with seed i
            header = self.harness.run(suite, repeats=1, pin=dict(PIN, seed=i)).header
            # Then: the header names all of it
            self.assertEqual((header["workflow"], header["workflow_version"]), ("lookup", 1))
            self.assertEqual((header["pin"]["id"], header["pin"]["seed"], header["pin"]["temperature"]), ("MP-light", i, 0))
            self.assertEqual(header["benchmark_version"], header["suite_sha1"])

    @mark.req("REQ-EVL-004")
    def test_the_options_reach_the_platform_and_a_run_without_a_pin_is_refused(self):
        """TC-EVL-004: a workflow suite runs with a pin, and without one it is refused before any case runs.

        Example: one case with the pin MP-light -> status pass; the same without a pin -> SuiteError.
        """
        # Given / When: a run with the pin
        suite = make_suite(self.tmp.name, ["pass"])
        run = self.harness.run(suite, pin=PIN)
        self.assertEqual(run.records[0]["status"], "pass")
        # Then: without it the harness refuses
        with self.assertRaises(H.SuiteError):
            self.harness.run(suite)

    @mark.req("REQ-EVL-004")
    def test_a_pin_the_platform_does_not_know_is_an_error_record_not_a_fallback(self):
        """TC-EVL-004: a pin the platform does not hold makes every case an error record, never a run on another model.

        Example: the pin id MP-huge -> status error..., error names pin_unavailable.
        """
        # Given / When: a run with a pin the mock does not know
        suite = make_suite(self.tmp.name, ["pass"])
        run = self.harness.run(suite, pin=dict(PIN, id="MP-huge"))
        # Then: an error record
        self.assertTrue(run.records[0]["status"].startswith("error"))
        self.assertIn("pin_unavailable", run.records[0]["error"])

    @mark.req("REQ-EVL-008")
    def test_runs_with_different_case_lists_are_not_compared(self):
        """TC-EVL-008: runs on the same cases with the same repeats are compared; a different case list or other repeats are refused.

        Example: one suite under two variants -> compared; a suite without c2 -> refused naming c2; 1 repeat against 2 -> refused.
        """
        # Given: the same suite under two variants
        suite = make_suite(self.tmp.name, ["pass", "pass", "pass"], "s_a")
        a = self.harness.run(suite, {"name": "one"}, repeats=2, pin=PIN)
        same = self.harness.run(suite, {"name": "two"}, repeats=2, pin=PIN)
        H.require_same_cases(a, same)                              # no error: the same suite, two variants
        # When / Then: a run without c2 is refused with c2 named, a run with other repeats too
        other = self.harness.run(make_suite(self.tmp.name, ["pass", "pass"], "s_c"), repeats=2, pin=PIN)
        with self.assertRaises(H.SuiteError) as caught:
            H.require_same_cases(a, other)
        self.assertIn("c2", str(caught.exception))
        fewer = self.harness.run(make_suite(self.tmp.name, ["pass", "pass", "pass"], "s_d"), repeats=1, pin=PIN)
        with self.assertRaises(H.SuiteError):
            H.require_same_cases(a, fewer)                         # the same repeats, too

    @mark.req("REQ-EVL-008")
    def test_runs_of_different_suite_versions_are_not_compared(self):
        """TC-EVL-008 (regression, Verify F8, D-164): two runs with the same case ids but different suite contents (benchmark version) are not compared.

        Example: s_a with c0..c2 all pass, s_b with c0..c2 where c1 is scripted to fail -> "not the same suite version".
        """
        # Given: two suites with the same case ids and repeats but different contents
        a = self.harness.run(make_suite(self.tmp.name, ["pass", "pass", "pass"], "s_a"), repeats=2, pin=PIN)
        b = self.harness.run(make_suite(self.tmp.name, ["pass", "fail", "pass"], "s_b"), repeats=2, pin=PIN)
        # When: they are compared, Then: refused, the version named
        with self.assertRaises(H.SuiteError) as caught:
            H.require_same_cases(a, b)
        self.assertIn("suite version", str(caught.exception))

    @mark.req("REQ-EVL-004")
    def test_a_pin_without_id_seed_or_temperature_is_refused_per_case(self):
        """TC-EVL-004 (regression, Verify F7): a pin that lacks id, seed or temperature does not reach IF-105; every case is an error that names the missing pin parts.

        Example: the pin MP-light without seed -> the record "error:ValueError", "needs a pin with id, seed and temperature"; the mock ran nothing.
        """
        suite = make_suite(self.tmp.name, ["pass"])
        for key in ("id", "seed", "temperature"):
            # Given: a pin without one key, When: a case runs
            platform = ScriptedPlatform()
            run = H.Harness(platform=platform).run(suite, pin={k: v for k, v in PIN.items() if k != key})
            # Then: an error record, no run on the platform
            self.assertEqual(run.records[0]["status"], "error:ValueError", key)
            self.assertIn("id, seed and temperature", run.records[0]["error"])
            self.assertEqual(platform.started, 0, key)

    @mark.req("REQ-EVL-008", "REQ-EVL-002")
    def test_a_comparison_says_it_is_feedback_not_a_verdict(self):
        """TC-EVL-008 (regression, Verify F12): the compare report does not call a dev difference believable; REQ-EVL-002 decides only on held-out cases.

        Example: A right on 30 cases, B on none (sign test p < 0.001) -> "dev feedback, not a verdict"; no "a difference you can believe".
        """
        # Given: two runs of the same suite where only A is right
        suite = make_suite(self.tmp.name, ["pass"] * 30, "s_w")
        a = self.harness.run(suite, {"name": "a"}, pin=PIN)
        b = self.harness.run(suite, {"name": "b"}, pin=PIN)
        for record in b.records:
            record["status"] = "fail"
        # When: the report is formatted
        text = H.format_compare(a, b)
        # Then: the wording is feedback
        self.assertNotIn("a difference you can believe", text)
        self.assertIn("dev feedback, not a verdict", text)


class RealProvider(unittest.TestCase):
    @mark.req("REQ-EVL-004", "REQ-EVL-011")
    def test_the_pin_of_the_command_line_runs_on_the_real_provider(self):
        """TC-EVL-004 (regression, Verify F2): the harness sends the pin id to IF-105, so the real provider (run_workflow.WorkflowRuns) runs the case.

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


def git_head():
    """the commit of the checkout, or None without git (a copy, a container without the repository's .git)"""
    try:
        done = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def write_suite(root, name, target, cases):
    folder = os.path.join(root, name)
    os.makedirs(folder)
    with open(os.path.join(folder, "suite.json"), "w") as fp:
        json.dump({"name": name, "description": "t", "target": target}, fp)
    with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
        for case in cases:
            fp.write(json.dumps(case) + "\n")
    return folder


class CommandLine(unittest.TestCase):
    """tools/eval.py run (D-164 F3): the IF-105 platform, a required pin and the versions of what ran, for every suite kind"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = os.path.join(self.tmp.name, "cfg.json")
        with open(self.cfg, "w") as fp:
            json.dump({"accounts_dir": os.path.join(self.tmp.name, "db"), "eval_dir": os.path.join(self.tmp.name, "runs")}, fp)
        self.suites = os.path.join(self.tmp.name, "suites")
        os.makedirs(self.suites)
        self.addCleanup(setattr, EVAL_CLI, "SUITES", EVAL_CLI.SUITES)
        EVAL_CLI.SUITES = self.suites
        write_suite(self.suites, "rules_mini", {"kind": "text_rules"}, [{"id": "c0", "input": {"text": "Hello."}, "gold": {"rules": []}, "expect": "pass"}])

    def main(self, *argv):
        out = io.StringIO()
        with unittest.mock.patch.object(sys, "argv", ["eval.py", *argv, "--cfg", self.cfg]), contextlib.redirect_stdout(out):
            EVAL_CLI.main()
        return out.getvalue()

    @mark.req("REQ-EVL-004")
    def test_a_run_without_a_pin_is_refused_with_the_pins_named(self):
        """TC-EVL-004 (regression, Verify F3): every run of tools/eval.py needs --pin; without it the run stops before anything runs.

        Example: `eval.py run rules_mini` -> exit "a run needs --pin (MP-light)", no run saved.
        """
        # Given: a suite that needs no model
        # When: it is run without --pin
        with self.assertRaises(SystemExit) as stopped:
            self.main("run", "rules_mini")
        # Then: the message names the option and the pins, and nothing was saved
        self.assertIn("--pin", str(stopped.exception.code))
        self.assertIn("MP-light", str(stopped.exception.code))
        self.assertFalse(os.path.isdir(os.path.join(self.tmp.name, "runs")))

    @mark.req("REQ-EVL-004")
    def test_a_saved_run_names_the_pin_id_and_the_code_version(self):
        """TC-EVL-004 (regression, Verify F3): a run of a code target (no skill, no pipeline) records the pin with its id and the commit of the code that ran.

        Example: `eval.py run rules_mini --pin MP-light` -> header pin id MP-light, pipeline None, commit = git HEAD of the repository
        (None where there is no git, e.g. a copy without .git: the header does not guess).
        """
        # Given: the text-rules suite and the pin MP-light
        # When: it is run and saved
        self.main("run", "rules_mini", "--pin", "MP-light", "--quiet")
        # Then: the saved header says which pin and which code
        folder = os.path.join(self.tmp.name, "runs")
        header = H.load_run(os.path.join(folder, os.listdir(folder)[0])).header
        self.assertEqual((header["pin"]["id"], header["pin"]["name"]), ("MP-light", "gemma4:12b-it-qat"))
        self.assertIn("pipeline", header)
        self.assertIsNone(header["pipeline"])
        self.assertIn("commit", header)
        self.assertEqual(header["commit"], git_head())

    @mark.req("REQ-EVL-001", "REQ-EVL-011")
    def test_the_harness_of_the_command_line_reaches_workflows_through_if_105(self):
        """TC-EVL-001 (regression, Verify F3): the harness of tools/eval.py has the target `workflow` on the real IF-105 provider with the pins of eval-spec.md.

        Example: make_harness(cfg, core) -> targets["workflow"] runs on run_workflow.WorkflowRuns whose pins are {"MP-light": name, digest}.
        """
        # Given: a core without a model (the provider is built, not run)
        core = EVAL_CLI.Core(os.path.join(REPO, "skills"), EVAL_CLI.Library(os.path.join(REPO, "library")), self.tmp.name)
        # When: the command line builds its harness
        harness = EVAL_CLI.make_harness(json.load(open(self.cfg)), core)
        # Then: the workflow target talks to the real provider, which knows the pin by its id
        platform = harness.targets["workflow"].platform
        self.assertEqual(type(platform).__name__, "WorkflowRuns")
        self.assertEqual(platform.pins, {"MP-light": {"name": "gemma4:12b-it-qat", "digest": EVAL_CLI.PINS["MP-light"]["digest"]}})


class PinDecidesTheModel(unittest.TestCase):
    """D-166: the pin decides the model of a run, and a model of the variant next to a pin is refused, so the header always names what ran"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    @mark.req("REQ-EVL-004")
    def test_every_model_call_of_a_pinned_run_uses_the_model_of_the_pin(self):
        """TC-EVL-004 (D-166): a pinned run of a skill suite calls the model named by the pin, whatever the skill file names.

        Example: verify_claim (light profile in its skill file) with the pin MP-light -> every call has model gemma4:12b-it-qat.
        """
        # Given: the shipped skill verify_claim on a scripted model that remembers the model it was asked for
        from core import Core
        from gate_lab import Scripted, vote
        from library import Library

        class Remembering(Scripted):
            def chat(self, messages, schema=None, model=None, profile=None, options=None):
                self.models = getattr(self, "models", []) + [model]
                return super().chat(messages, schema, model, profile, options)
        model = Remembering(lambda p, n: vote("supported"))
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), os.path.join(self.tmp.name, "runs"), model=model)
        claim = {"claim": "The tower is 100 m tall.", "evidence": "", "rounds": 3, "experts": []}
        suite = H.load_suite(write_suite(self.tmp.name, "claims", {"kind": "pipeline", "skill": "verify_claim"}, [{"id": "c0", "input": claim, "truth": True}]))
        # When: it runs with the pin of the command line
        H.Harness(core).run(suite, pin=PIN)
        # Then: every call names the pin's model
        self.assertTrue(model.models)
        self.assertEqual(set(model.models), {"gemma4:12b-it-qat"})

    @mark.req("REQ-EVL-004")
    def test_a_variant_model_next_to_a_pin_is_refused(self):
        """TC-EVL-004 (D-166): the harness and the command line refuse --model together with --pin before anything runs.

        Example: variant model full with the pin MP-light -> SuiteError naming --model and --pin; `eval.py run ... --pin MP-light --model full` -> exit with the same.
        """
        # Given: a suite and a variant that names a model
        suite = H.load_suite(write_suite(self.tmp.name, "rules_m", {"kind": "text_rules"}, [{"id": "c0", "input": {"text": "Hello."}, "gold": {"rules": []}, "expect": "pass"}]))
        # When / Then: the harness refuses
        with self.assertRaises(H.SuiteError) as caught:
            H.Harness().run(suite, {"model": "full"}, pin=PIN)
        self.assertIn("--model", str(caught.exception))
        self.assertIn("--pin", str(caught.exception))
        # And: the command line refuses too, before a core is built
        cfg = os.path.join(self.tmp.name, "cfg.json")
        with open(cfg, "w") as fp:
            json.dump({"accounts_dir": os.path.join(self.tmp.name, "db"), "eval_dir": os.path.join(self.tmp.name, "runs")}, fp)
        self.addCleanup(setattr, EVAL_CLI, "SUITES", EVAL_CLI.SUITES)
        EVAL_CLI.SUITES = self.tmp.name
        argv = ["eval.py", "run", "rules_m", "--pin", "MP-light", "--model", "full", "--cfg", cfg]
        with unittest.mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as stopped:
            EVAL_CLI.main()
        self.assertIn("--model", str(stopped.exception.code))
        self.assertFalse(os.path.isdir(os.path.join(self.tmp.name, "runs")))


class VersionsOfEveryKind(unittest.TestCase):
    @mark.req("REQ-EVL-004")
    def test_every_skill_kind_records_its_skill_and_pipeline_versions(self):
        """TC-EVL-004 (regression, Verify F3): the header of a run of every suite kind that runs a skill names the skill, its version and the pipeline.

        Example: a research suite on the skill research -> header skill research, skill_version 3, pipeline research.escalate@1 (the skill file's);
        with the variant pipeline research.baseline@1 that one.
        """
        # Given: the shipped skills and fake targets (the header is written before any case runs, so no model is needed)
        from core import Core
        from library import Library
        with tempfile.TemporaryDirectory() as root:
            core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), root)
            fake = {kind: (lambda case, variant, suite: ("pass", {})) for kind in ("pipeline", "research", "plan", "extraction")}
            harness = H.Harness(core, targets=fake)
            skill = core.skills.get("research")
            for kind in ("pipeline", "research", "plan", "extraction"):
                suite = H.load_suite(write_suite(root, "s_" + kind, {"kind": kind, "skill": "research", "fixtures": "web.json"}, [{"id": "c0", "input": {"text": "x"}, "gold": [], "expect": "pass"}]))
                # When: a run with and without a pipeline in the variant
                plain = harness.run(suite, pin=PIN).header
                pinned = harness.run(suite, {"pipeline": "research.baseline@1"}, pin=PIN).header
                # Then: both headers name what ran
                self.assertEqual((plain["skill"], plain["skill_version"], plain["pipeline"]), ("research", skill["version"], skill["pipeline"]), kind)
                self.assertEqual(pinned["pipeline"], "research.baseline@1", kind)


class OnlyThroughIF105(unittest.TestCase):
    @mark.req("REQ-EVL-011")
    def test_the_adapter_imports_no_runner_library_or_store(self):
        """TC-EVL-011 (inspection): the module that talks to the platform imports only the standard library, no runner, library or store.

        Example: the imports of eval_platform.py minus the standard library -> the empty set. The older targets of harness.py still use the
        in-process Core (implementation log, F-1).
        """
        # Given: the syntax tree of the adapter
        with open(os.path.join(REPO, "eval_platform.py"), encoding="utf-8") as fp:
            tree = ast.parse(fp.read())
        # When: its imported top-level modules are collected
        imported = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)}
        imported |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imported.discard("")
        # Then: all of them are in the standard library
        self.assertEqual(imported - set(sys.stdlib_module_names), set())


if __name__ == "__main__":
    unittest.main()
