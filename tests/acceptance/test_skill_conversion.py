"""
Acceptance tests of the conversion of the skills (G-V2.CONVERT): TC-WFM-057, 058, 059, 060, 069 and 115 (REQ-WFM-057, -058, -059, -060, -069, -115) against
skill_converter.py. RED until T-CV-02 to T-CV-08: the stubs return nothing. No model runs: the old runner is driven by scripted replies and recorded
(tests/helpers/call_recording.py, T-CV-01); TC-WFM-110 to 114 are stage 4 eval runs and are not written here.
Run with: python tests/acceptance/test_skill_conversion.py
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                                        # noqa: E402
from call_recording import Recording, RecordingModel, RecordingTool, Replay, ScriptedModel, first_difference   # noqa: E402
from core import Core                                                           # noqa: E402
from library import Library                                                     # noqa: E402
import skill_converter as C                                                     # noqa: E402

SKILLS, LIBRARY = os.path.join(REPO, "skills"), os.path.join(REPO, "library")

# the Eval criterion line of REQ-WFM-110 as written on 2026-11-07 (0.92 baseline minus the margin 0.10); REQ-WFM-110 is held until the baseline probe: if
# the margin changes, this copy and the numbers below are amended together
CRITERION = "suite=EV-research; select=; metric=right; min=0.82; n=20; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0050; split=dev"

INPUTS = {"research": {"question": "When did the Rivertown Bridge open to traffic?"},
          "plan_question": {"question": "Which is older, the Tarn Museum or the company that built the Rivertown Bridge?"},
          "verify_claim": {"claim": "The Pacific is the largest ocean on Earth.", "evidence": "", "rounds": 3, "experts": []},
          "verify_computable": {"claim": "1628.89 euros is what 1000 euros grow to at 5 percent interest per year in 10 years", "data_description": "principal, rate, years, claimed",
                                "data": {"principal": 1000, "rate": 5, "years": 10, "claimed": 1628.89}},
          "extract_claims": {"text": "Quick check of the budget: 12 * 1.5 + 3 = 21, so we stay within limits."}}
ALL_SKILLS = ["chat", "check_speech", "extract_claims", "extract_claims_rules", "memory_write", "plan_question", "research", "review_abstract", "review_full",
              "review_keywords", "review_section", "review_summary", "summarize", "verify_claim", "verify_computable"]
SIX = ["research", "plan_question", "verify_claim", "verify_computable", "extract_claims", "extract_claims_rules"]


def old_run(skill, folder):
    """the old runner on scripted replies and scripted tool results; returns the recording (model replies and tool results) of that run"""
    rec = Recording()
    tools = {"web_search": RecordingTool("web_search", lambda **kw: [], rec), "fetch_page": RecordingTool("fetch_page", lambda **kw: {"text": ""}, rec)}
    core = Core(SKILLS, Library(LIBRARY), folder, model=RecordingModel(ScriptedModel(), rec), tools=tools)
    result = core.run(skill, INPUTS[skill], started_by="command")
    assert result.status == "done", "the scripted old run of %s ended with %s: %s" % (skill, result.status, result.error)
    return rec


def converted_calls(skill, replay, **changes):
    C.run_converted(skill, INPUTS[skill], model=replay.model, tools=replay.tools, skills_dir=SKILLS, library_dir=LIBRARY, skill_changes=changes or None)
    return replay.model_calls()


class FakeRunner:
    def __init__(self):
        self.runs = []

    def run(self, skill, graph, inputs, **kwargs):
        self.runs.append((skill["name"], skill["form"]))
        return "ran"


class OldRunnerUntilProven(unittest.TestCase):
    def setUp(self):
        self.reads, self.runner = [], FakeRunner()

        def converted(name):
            self.reads.append(name)
            return {"name": name, "form": "converted"}, {"graph": "converted"}
        self.conv = C.SkillConverter(lambda name: ({"name": name, "form": "old"}, {"graph": "old"}), converted, self.runner)

    @mark.req("REQ-WFM-057")
    def test_an_unconverted_skill_runs_old_and_a_converted_one_runs_converted(self):
        """TC-WFM-057: A (unconverted) runs its old skill file and pipeline and its converted record is not read; B (converted after a passed check) runs the converted one."""
        self.conv.mark_converted("B", {"verdict": "PASS", "accepted": True})
        self.conv.run("A", {})
        self.conv.run("B", {})
        self.assertEqual(self.runner.runs, [("A", "old"), ("B", "converted")])
        self.assertEqual(self.reads, ["B"])

    @mark.req("REQ-WFM-057")
    def test_marking_a_skill_converted_without_a_passed_check_is_refused(self):
        """TC-WFM-057: marking A converted with a failed or undecided check is refused and A stays unconverted."""
        for check in ({"verdict": "FAIL", "accepted": False}, {"verdict": "NOT DECIDED", "accepted": False}):
            with self.assertRaises(C.ConversionError):
                self.conv.mark_converted("A", check)
        self.assertEqual(self.conv.state("A"), "unconverted")


class SameModelCalls(unittest.TestCase):
    @mark.req("REQ-WFM-058")
    def test_the_converted_skill_makes_the_same_model_calls_as_the_old_runner(self):
        """TC-WFM-058: for research, plan_question, verify_claim, verify_computable and extract_claims the lists of model calls (order, prompt, options) of the old run and of
        the converted run, both replayed from one recording, are equal; the diff names the first differing call."""
        for skill in INPUTS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as folder:
                rec = old_run(skill, folder)
                self.assertGreaterEqual(len(rec.model_calls()), 1)
                for _ in range(2):                                       # replayed twice: the same list of calls both times
                    self.assertIsNone(first_difference(rec.model_calls(), converted_calls(skill, Replay(rec))), "the converted %s calls differ" % skill)

    @mark.req("REQ-WFM-058")
    def test_one_changed_option_makes_the_check_fail_and_names_call_1(self):
        """TC-WFM-058: with temperature 0.2 added to the converted skill, the check fails and names call 1 and the field options."""
        for skill in INPUTS:
            with self.subTest(skill=skill), tempfile.TemporaryDirectory() as folder:
                rec = old_run(skill, folder)
                new = converted_calls(skill, Replay(rec), model={"profile": "light", "options": {"temperature": 0.2}})
                diff = first_difference(rec.model_calls(), new)
                self.assertIsNotNone(diff)
                self.assertEqual((diff["call"], diff["field"]), (1, "options"))
                self.assertEqual(diff["new"], {"temperature": 0.2})


def write_run(folder, name, suite, rights):
    """a scripted run file: a header and 3 repeats per case (right = status pass with truth true, so the majority of the repeats is the same), every case tagged split:dev"""
    path = os.path.join(folder, name)
    with open(path, "w") as fp:
        fp.write(json.dumps({"kind": "header", "suite": suite, "variant": {"name": "v"}, "repeats": 3}) + "\n")
        for i, right in enumerate(rights):
            for repeat in range(3):
                fp.write(json.dumps({"kind": "record", "case": "c%d" % i, "repeat": repeat, "status": "pass" if right else "fail", "truth": True, "tags": ["split:dev"]}) + "\n")
    return path


class AcceptOnTheCriterion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_file(self, name, suite, right):
        return write_run(self.tmp.name, name, suite, [True] * right + [False] * (20 - right))

    @mark.req("REQ-WFM-059")
    def test_17_of_20_is_pass_and_the_skill_is_accepted(self):
        """TC-WFM-059: 17 of 20 right = 0.85 against the limit 0.82 (0.92 - 0.10): PASS, accepted."""
        out = C.decide_acceptance(self.run_file("r1.jsonl", "EV-research", 17), CRITERION)
        self.assertEqual((out["verdict"], out["accepted"]), ("PASS", True))

    @mark.req("REQ-WFM-059")
    def test_15_of_20_twice_is_fail_after_the_rerun_and_the_skill_stays_unconverted(self):
        """TC-WFM-059: 15 of 20 = 0.75 in the first run and in the re-run: FAIL, not accepted."""
        out = C.decide_acceptance(self.run_file("r1.jsonl", "EV-research", 15), CRITERION, rerun_path=self.run_file("r2.jsonl", "EV-research", 15))
        self.assertEqual((out["verdict"], out["accepted"]), ("FAIL", False))

    @mark.req("REQ-WFM-059")
    def test_a_run_of_another_suite_is_not_decided_and_the_skill_stays_unconverted(self):
        """TC-WFM-059: a run whose header names the suite plans (17 of 20) is NOT DECIDED for the criterion of EV-research, not accepted."""
        out = C.decide_acceptance(self.run_file("r1.jsonl", "plans", 17), CRITERION)
        self.assertEqual((out["verdict"], out["accepted"]), ("NOT DECIDED", False))


class RecordOfTheCheck(unittest.TestCase):
    @mark.req("REQ-WFM-060")
    def test_every_skill_names_its_form_and_a_verdict_or_a_reason(self):
        """TC-WFM-060: the 15 skills of v0.1.0 each name the form; the six with an equivalence requirement carry suite, run, pins and verdict or a reason; the nine others the reason of the owner (part of the user interface, revisited in another goal)."""
        records = C.conversion_records(SKILLS)
        self.assertEqual(sorted(records), ALL_SKILLS)
        for name, rec in records.items():
            self.assertIn(rec.get("form"), ("old", "converted"), name)
            if name in SIX:
                self.assertTrue(all(rec.get(k) for k in ("suite", "run", "pins", "verdict")) or rec.get("reason"), name)
            else:
                self.assertEqual(rec["form"], "old", name)
                self.assertIn("user interface", rec.get("reason", ""), name)
                self.assertTrue("later goal" in rec["reason"] or "another goal" in rec["reason"], name)


class SettingsAreVersioned(unittest.TestCase):
    @mark.req("REQ-WFM-069")
    def test_a_changed_margin_is_version_2_and_the_earlier_result_keeps_version_1(self):
        """TC-WFM-069: version 1 = margin 0.10, repeats 3, rule threshold; after the margin 0.05: version 2; the new result names 2, the earlier one still 1 and is unchanged."""
        with tempfile.TemporaryDirectory() as folder:
            settings = C.EquivalenceSettings(folder)
            self.assertEqual(settings.current(), {"version": 1, "margin": 0.10, "repeats": 3, "rule": "threshold"})
            first = settings.record_result("research", "PASS")
            self.assertEqual(first["settings_version"], 1)
            settings.update(margin=0.05)
            second = settings.record_result("research", "PASS")
            self.assertEqual(settings.current(), {"version": 2, "margin": 0.05, "repeats": 3, "rule": "threshold"})
            self.assertEqual([v["version"] for v in settings.versions()], [1, 2])
            self.assertEqual(second["settings_version"], 2)
            self.assertEqual(settings.results()[0], first)
            self.assertEqual(settings.results()[0]["settings_version"], 1)


def extraction_cases():
    """the 51 cases of the suite extraction (EV-extraction); the tags split:dev are not set yet (amendment A-120, proposed), so all 51 stand for the dev cases"""
    with open(os.path.join(REPO, "eval", "suites", "extraction", "cases.jsonl"), encoding="utf-8") as fp:
        return [json.loads(line) for line in fp if line.strip()]


class SameOutputsOfTheRuleBasedSkill(unittest.TestCase):
    @mark.req("REQ-WFM-115")
    def test_the_51_outputs_of_the_converted_and_the_old_run_are_equal(self):
        """TC-WFM-115: extract_claims_rules on the 51 cases of EV-extraction, no model: old and converted outputs are equal."""
        cases = extraction_cases()
        self.assertEqual(len(cases), 51)
        with tempfile.TemporaryDirectory() as folder:
            core = Core(SKILLS, Library(LIBRARY), folder)
            old = {c["id"]: core.run("extract_claims_rules", c["input"], started_by="command").answer for c in cases}
            new = {}
            for c in cases:
                result = C.run_converted("extract_claims_rules", c["input"], skills_dir=SKILLS, library_dir=LIBRARY)
                new[c["id"]] = getattr(result, "answer", "no converted run")
        self.assertEqual(C.compare_outputs(old, new), [])

    @mark.req("REQ-WFM-115")
    def test_a_planted_difference_in_one_output_is_reported_with_its_case(self):
        """TC-WFM-115: one output changed in a copy of 51: exactly one diff, naming the case."""
        old = {"case%02d" % i: [{"claim": "c%d" % i}] for i in range(51)}
        new = {k: list(v) for k, v in old.items()}
        new["case17"] = [{"claim": "changed"}]
        self.assertEqual(C.compare_outputs(old, new), [{"case": "case17", "old": [{"claim": "c17"}], "new": [{"claim": "changed"}]}])
        self.assertEqual(C.compare_outputs(old, dict(old)), [])


if __name__ == "__main__":
    unittest.main()
