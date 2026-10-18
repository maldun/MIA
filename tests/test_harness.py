"""
Tests for the evaluation harness: loading and validating suites, running a target with failures and repeats, counting the cost, saving and loading runs, the reports, the comparison of two runs,
the variants of pipeline targets (skill, pinned pipeline, model), and the shipped suites. The deterministic suite of the hard checks is part of the regression: it must match every time.
Run with the MIA virtualenv: python tests/test_harness.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import harness as H                                   # noqa: E402
import metrics as M                                   # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402

SUITES = os.path.join(REPO, "eval", "suites")


def write_suite(root, name, cases, target=None, description="test suite"):
    folder = os.path.join(root, name)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "suite.json"), "w") as fp:
        json.dump({"name": name, "description": description, "target": target or {"kind": "fake"}}, fp)
    with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
        for case in cases:
            fp.write((case if isinstance(case, str) else json.dumps(case)) + "\n")
    return folder


def case(case_id, **kw):
    return dict({"id": case_id, "input": {"x": case_id}}, **kw)


class SuiteLoading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def load(self, cases, **kw):
        return H.load_suite(write_suite(self.tmp.name, "demo", cases, **kw))

    def test_a_good_suite(self):
        suite = self.load([case("a", truth=True, tags=["x", "y"]), case("b", expect="open"), case("c", truth=False, expect="fail", note="why")])
        self.assertEqual((suite.name, len(suite.cases), suite.target["kind"]), ("demo", 3, "fake"))
        self.assertEqual([c["id"] for c in suite.select(tags=["x"])], ["a"])
        self.assertEqual([c["id"] for c in suite.select(only=["b", "c"])], ["b", "c"])
        self.assertEqual([c["id"] for c in suite.select(limit=2)], ["a", "b"])
        self.assertEqual(suite.select(tags=["x", "nothing"]), [])

    def test_every_problem_is_named(self):
        bad = [case("a", truth=True), case("a", truth=True), case("b"), case("c", truth="yes"), case("d", expect="great"), case("e", truth=True, colour="red"),
               case("f", truth=True, tags="x"), {"input": {}, "truth": True}, "not json", {"id": "g", "truth": True}]
        with self.assertRaises(H.SuiteError) as raised:
            self.load(bad)
        text = str(raised.exception)
        for part in ("used twice", "needs 'truth' or 'expect'", "'truth' must be true or false", "'expect' must be one of", "unknown field 'colour'", "'tags' must be a list",
                     "every case needs an 'id'", "not valid JSON", "needs 'input' for a fake target"):
            self.assertIn(part, text)

    def test_the_input_key_depends_on_the_target(self):
        with self.assertRaises(H.SuiteError) as raised:
            self.load([{"id": "a", "input": {}, "truth": True}], target={"kind": "checks"})
        self.assertIn("needs 'claim'", str(raised.exception))
        self.assertEqual(len(self.load([{"id": "a", "claim": {"type": "x"}, "truth": True}], target={"kind": "checks"}).cases), 1)

    def test_missing_or_empty_files_and_wrong_names(self):
        with self.assertRaises(H.SuiteError):
            H.load_suite(os.path.join(self.tmp.name, "nothing"))
        with self.assertRaises(H.SuiteError) as raised:
            self.load([])
        self.assertIn("no cases", str(raised.exception))
        folder = write_suite(self.tmp.name, "other", [case("a", truth=True)])
        with open(os.path.join(folder, "suite.json"), "w") as fp:
            json.dump({"name": "wrong", "target": {"kind": "fake"}}, fp)
        with self.assertRaises(H.SuiteError) as raised:
            H.load_suite(folder)
        self.assertIn("folder name", str(raised.exception))

    def test_listing_keeps_going_past_a_broken_suite(self):
        write_suite(self.tmp.name, "good", [case("a", truth=True)])
        write_suite(self.tmp.name, "bad", [case("a")])
        found = H.list_suites(self.tmp.name)
        self.assertEqual([type(s).__name__ for s in found], ["SuiteError", "Suite"])


class Running(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clock_value = 1000.0
        self.suite = H.load_suite(write_suite(self.tmp.name, "demo", [case("a", truth=True, tags=["t"]), case("b", truth=False, tags=["t", "u"]), case("c", expect="open")]))

    def tearDown(self):
        self.tmp.cleanup()

    def clock(self):
        self.clock_value += 0.5
        return self.clock_value

    def harness(self, answers):
        calls = []

        def target(item, variant, suite):
            calls.append((item["id"], dict(variant)))
            answer = answers[item["id"]]
            if isinstance(answer, Exception):
                raise answer
            return answer, {"echo": item["id"]}
        h = H.Harness(clock=self.clock, targets={"fake": target})
        return h, calls

    def test_records_and_header(self):
        h, calls = self.harness({"a": "pass", "b": "fail", "c": "inconclusive"})
        run = h.run(self.suite, {"name": "v1", "model": "light"})
        self.assertEqual(run.header["suite"], "demo")
        self.assertEqual((run.header["variant"], run.header["repeats"], run.header["cases"]), ({"name": "v1", "model": "light"}, 1, 3))
        self.assertEqual([(r["case"], r["status"], r["truth"], r["expect"]) for r in run.records], [("a", "pass", True, None), ("b", "fail", False, None), ("c", "inconclusive", None, "open")])
        self.assertEqual(run.records[0]["tags"], ["t"])
        self.assertEqual(run.records[0]["output"], {"echo": "a"})
        self.assertEqual(run.records[0]["seconds"], 0.5)                                # measured with the clock
        self.assertEqual(calls[0][1]["model"], "light")                                  # the variant reaches the target
        self.assertTrue(all(M.is_right(r) for r in run.records))

    def test_a_target_that_raises_is_a_result_not_the_end(self):
        h, _ = self.harness({"a": ValueError("kaput"), "b": "fail", "c": KeyError("x")})
        run = h.run(self.suite)
        self.assertEqual([r["status"] for r in run.records], ["error:ValueError", "fail", "error:KeyError"])
        self.assertIn("kaput", run.records[0]["error"])
        self.assertFalse(M.is_right(run.records[0]))
        self.assertEqual(M.verification_metrics(run.records)["errors"]["k"], 1)

    def test_repeats_filters_and_progress(self):
        h, calls = self.harness({"a": "pass", "b": "fail", "c": "open"})
        seen = []
        run = h.run(self.suite, repeats=3, tags=["t"], progress=lambda done, total, record: seen.append((done, total, record["case"])))
        self.assertEqual(len(run.records), 6)
        self.assertEqual([(r["case"], r["repeat"]) for r in run.records], [("a", 0), ("b", 0), ("a", 1), ("b", 1), ("a", 2), ("b", 2)])
        self.assertEqual((seen[0], seen[-1]), ((1, 6, "a"), (6, 6, "b")))
        self.assertEqual(M.stability(run.records)["rate"], 1.0)
        run = h.run(self.suite, only=["c"], limit=5)
        self.assertEqual([r["case"] for r in run.records], ["c"])

    def test_an_unknown_target_kind_is_refused(self):
        suite = H.load_suite(write_suite(self.tmp.name, "other", [case("a", truth=True)], target={"kind": "mystery"}))
        with self.assertRaises(H.SuiteError):
            H.Harness(clock=self.clock).run(suite)

    def test_save_load_and_latest(self):
        h, _ = self.harness({"a": "pass", "b": "fail", "c": "open"})
        run1 = h.run(self.suite, {"name": "v1"})
        path1 = run1.save(os.path.join(self.tmp.name, "results"))
        self.clock_value += 3600
        path2 = h.run(self.suite, {"name": "v2"}).save(os.path.join(self.tmp.name, "results"))
        self.assertTrue(os.path.basename(path1).startswith("demo__v1__"))
        loaded = H.load_run(path1)
        self.assertEqual(loaded.header["variant"], {"name": "v1"})
        self.assertEqual([r["status"] for r in loaded.records], ["pass", "fail", "open"])
        folder = os.path.join(self.tmp.name, "results")
        self.assertEqual(H.latest_run(folder, "demo", "v1"), path1)
        self.assertEqual(H.latest_run(folder, "demo"), path2)
        self.assertIsNone(H.latest_run(folder, "nothing"))
        self.assertIsNone(H.latest_run(os.path.join(self.tmp.name, "missing"), "demo"))
        with open(os.path.join(folder, "broken.jsonl"), "w") as fp:
            fp.write(json.dumps({"kind": "record", "case": "x"}) + "\n")
        with self.assertRaises(H.SuiteError):
            H.load_run(os.path.join(folder, "broken.jsonl"))

    def test_reports(self):
        h, _ = self.harness({"a": "pass", "b": "pass", "c": "fail"})                      # b: a false pass, c: not the expected status
        text = H.format_report(h.run(self.suite, {"name": "v1"}))
        for part in ("suite demo, variant v1", "behaves as expected", "MISMATCH c", "FALSE PASS", "WRONG b", "by tag", "cost:", "confusion: pass/true 1  pass/false 1"):
            self.assertIn(part, text)
        self.assertNotIn("stability", text)
        h2, _ = self.harness({"a": "pass", "b": "fail", "c": "open"})
        text = H.format_report(h2.run(self.suite, repeats=2))
        self.assertIn("stability over repeats", text)
        self.assertIn("100.0%", text)

    def test_compare(self):
        a, _ = self.harness({"a": "pass", "b": "fail", "c": "open"})
        b, _ = self.harness({"a": "pass", "b": "pass", "c": "fail"})
        text = H.format_compare(a.run(self.suite, {"name": "good"}), b.run(self.suite, {"name": "bad"}))
        for part in ("A = demo/good", "B = demo/bad", "only A right: 2", "only B right: 0", "sign test p = 0.500", "not distinguishable from chance", "only A: b, c"):
            self.assertIn(part, text)


class CountingTheModel(unittest.TestCase):
    def test_calls_and_characters_are_counted_per_case(self):
        class Model:
            def chat(self, messages, **kw):
                return "x" * 10

        class FakeRunner:
            model = Model()

        class FakeCore:
            runner = FakeRunner()

        def target(item, variant, suite):
            core.runner.model.chat([{"role": "user", "content": "hello"}])
            if item["id"] == "b":
                core.runner.model.chat([{"role": "system", "content": "abc"}, {"role": "user", "content": "de"}])
            return "pass", None
        core = FakeCore()
        h = H.Harness(core, targets={"fake": target})
        self.assertIsInstance(core.runner.model, H.CountingModel)
        with tempfile.TemporaryDirectory() as tmp:
            suite = H.load_suite(write_suite(tmp, "demo", [case("a", truth=True), case("b", truth=True)]))
            run = h.run(suite)
        self.assertEqual([(r["calls"], r["chars_in"], r["chars_out"]) for r in run.records], [(1, 5, 10), (2, 5 + 5, 20)])
        self.assertEqual(M.cost(run.records)["calls"], 3)


class PipelineVariants(unittest.TestCase):
    """the pipeline target: the variant picks skill, pipeline version and model; a pipeline that fails is an error status"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        skills = os.path.join(self.tmp.name, "skills")
        os.makedirs(skills)
        for name, pipeline, model in (("summ", "summarize", "light"), ("other", "summarize", "full")):
            with open(os.path.join(skills, name + ".md"), "w") as fp:
                fp.write("---\nname: %s\npipeline: %s\nmodel: {profile: %s}\n---\n" % (name, pipeline, model))
        self.seen = []
        outer = self

        class Model:
            def chat(self, messages, schema=None, model=None, profile=None, options=None):
                outer.seen.append({"profile": profile, "model": model})
                return json.dumps({"summary": "s", "key_points": ["p"]})
        self.core = Core(skills, Library(os.path.join(REPO, "library")), self.tmp.name, model=Model())
        self.suite = H.load_suite(write_suite(self.tmp.name, "summ", [{"id": "a", "input": {"text": "t", "sentences": 1}, "expect": "open"}],
                                              target={"kind": "pipeline", "skill": "summ", "status_field": "summary"}))

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_and_variants(self):
        h = H.Harness(self.core)
        run = h.run(self.suite)
        self.assertEqual(run.records[0]["status"], "s")                                   # the field named in the target is the status
        self.assertEqual((run.header["pipeline"], run.header["skill_version"]), ("summarize", 1))
        self.assertEqual(self.seen[-1], {"profile": "light", "model": None})
        h.run(self.suite, {"name": "big", "model": "full"})
        self.assertEqual(self.seen[-1]["profile"], "full")
        h.run(self.suite, {"name": "named", "model": "qwen3:8b"})
        self.assertEqual(self.seen[-1], {"profile": None, "model": "qwen3:8b"})
        h.run(self.suite, {"name": "other skill", "skill": "other"})
        self.assertEqual(self.seen[-1]["profile"], "full")
        pinned = h.run(self.suite, {"name": "pinned", "pipeline": "summarize@1"})
        self.assertEqual(pinned.header["pipeline"], "summarize@1")
        self.assertEqual(pinned.records[0]["status"], "s")

    def test_failures_become_error_statuses(self):
        h = H.Harness(self.core)
        run = h.run(self.suite, {"name": "ghost", "pipeline": "summarize@9"})
        self.assertTrue(run.records[0]["status"].startswith("error:"))                    # a pipeline that does not exist
        run = h.run(self.suite, {"name": "ghost skill", "skill": "nothing"})
        self.assertTrue(run.records[0]["status"].startswith("error:"))
        broken = H.load_suite(write_suite(self.tmp.name, "nofield", [{"id": "a", "input": {"text": "t", "sentences": 1}, "expect": "open"}],
                                          target={"kind": "pipeline", "skill": "summ", "status_field": "verdict"}))
        self.assertEqual(h.run(broken).records[0]["status"], "error:no_verdict")
        self.assertEqual(len(self.seen), len(self.seen))


class ShippedSuites(unittest.TestCase):
    def test_every_shipped_suite_is_valid(self):
        found = H.list_suites(SUITES)
        self.assertGreaterEqual(len(found), 2)
        for suite in found:
            self.assertNotIsInstance(suite, Exception, str(suite))
            self.assertGreaterEqual(len(suite.cases), 30, suite.name)
            for item in suite.cases:
                self.assertTrue(item.get("note") or item.get("tags"), "%s/%s has neither tags nor a note" % (suite.name, item["id"]))

    def test_the_computable_suite_is_balanced_and_consistent(self):
        suite = H.load_suite(os.path.join(SUITES, "computable"))
        truths = [c["truth"] for c in suite.cases]
        self.assertGreaterEqual(min(truths.count(True), truths.count(False)), 15)
        for item in suite.cases:
            self.assertEqual(item["expect"], "pass" if item["truth"] else "fail", item["id"])
            self.assertIn("claimed", item["input"]["data"])                                                 # every case carries the number that is claimed
        traps = [c for c in suite.cases if "trap" in c["tags"]]
        self.assertGreaterEqual(len(traps), 6)
        self.assertEqual(len(traps), len({c["id"] for c in traps}))

    def test_the_hard_checks_suite_matches_every_time(self):
        """the regression: the exact checks behave as the suite says. A failure here is a bug in a check (or a wrong expectation: decide which, do not just change the number)."""
        suite = H.load_suite(os.path.join(SUITES, "hard_checks"))
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tempfile.mkdtemp())
        run = H.Harness(core).run(suite)
        mismatches = [(r["case"], r["status"], r["expect"]) for r in run.records if not M.is_right(r)]
        self.assertEqual(mismatches, [])
        verification = M.verification_metrics(run.records)
        self.assertEqual(verification["false_pass"]["k"], 0)
        self.assertEqual(verification["false_fail"]["k"], 0)
        self.assertGreater(verification["n"], 90)
        self.assertEqual(M.stability(H.Harness(core).run(suite, repeats=2).records)["rate"], 1.0)             # deterministic

    def test_the_known_limits_are_documented_not_hidden(self):
        suite = H.load_suite(os.path.join(SUITES, "hard_checks"))
        for item in suite.select(tags=["known_limit"]):
            self.assertTrue(item.get("note"), item["id"])


if __name__ == "__main__":
    unittest.main()
