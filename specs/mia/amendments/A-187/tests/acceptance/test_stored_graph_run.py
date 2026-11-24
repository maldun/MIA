"""Acceptance tests of the stored-graph path of the run (G-V4.GRAPHAPI.RUN, protected after the Plan gate): TC-RUN-044 to TC-RUN-047, TC-WFM-187 and
TC-WFM-115 (REQ-RUN-042 to 045, REQ-WFM-168, REQ-WFM-115) against Core with `graph_store=` (D-480), on the scripted replies of REQ-WFM-058 and a throw-away
files store (TR-RUN-005, -006, -009). The model here is the scripted fake: it shows the code path, never decides an eval criterion. TC-RUN-045 is green from the
start (it guards a run without a stored graph); the others are red until the runner task. "No step ran" is shown by the model and the tools as markers: every
step of verify_claim with an effect goes through one of them, and the sound twin of each check shows they fire (TR-RUN-006).
Run with: python tests/acceptance/test_stored_graph_run.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(REPO, "tests", "helpers", "mocks"))

from markers import mark                                                      # noqa: E402
from call_recording import RecordingModel, Recording, ScriptedModel, first_difference   # noqa: E402
from rules_graphs import converted_skills                                     # noqa: E402
from run_store import INPUTS, LIBRARY, SIX, SKILLS, ThrowAwayStore, old_run, oracle, run_record, scripted_tools, stored_run   # noqa: E402
import skill_converter                                                        # noqa: E402

GRAPHS = dict(converted_skills())     # built at test time (TR-RUN-004)
VERIFY = GRAPHS["verify_claim.md"]


def cycle_in(stored):
    """the graph with one connection added that makes the writer of an input step read its own result: a cycle the save path would refuse (the rules)"""
    out = json.loads(json.dumps(stored))
    first = next(e for e in out["edges"] if e["from"].startswith("input."))
    out["edges"].append({"id": "cycle", "from": first["to"], "to": first["from"], "data": {}})
    return out


class StoreCase(unittest.TestCase):
    def setUp(self):
        self.store = ThrowAwayStore()
        self.addCleanup(self.store.close)
        self.runs = tempfile.mkdtemp(prefix="run-log-")
        self.addCleanup(__import__("shutil").rmtree, self.runs, True)


class RunFromTheStore(StoreCase):
    @mark.req("REQ-RUN-042")
    def test_a_skill_with_a_stored_graph_runs_from_it(self):
        """TC-RUN-044: verify_claim reads its stored graph once, by its ID, newest version, and gives the answer of the in-memory converted run.

        Example: the read is [("verify.single@1", None)]; the answer equals run_converted's.
        """
        # Given: the converted graph of verify_claim saved through CORE's save path; scripted replies; the answer of the in-memory converted run
        self.store.save(VERIFY)
        rec = Recording()
        in_memory = skill_converter.run_converted("verify_claim", INPUTS["verify_claim"], model=RecordingModel(ScriptedModel(), rec), tools=scripted_tools(rec),
                                                  skills_dir=SKILLS, library_dir=LIBRARY).answer
        # When: verify_claim runs one claim
        result, _, _ = stored_run("verify_claim", self.store, self.runs)
        # Then: the graph was read once, by its ID, at its newest version
        self.assertEqual(self.store.reads, [("verify.single@1", None)])
        # And: the answer equals the answer of the in-memory converted run
        self.assertEqual((result.status, result.answer), ("done", in_memory))

    @mark.req("REQ-RUN-043")
    def test_without_a_stored_graph_the_six_skills_run_as_before(self):
        """TC-RUN-045: with an empty store each of the six skills makes the model calls and gives the answer recorded at goal/v4.

        Example: research makes the 5 recorded model calls and the recorded answer; extract_claims_rules makes none.
        """
        # Given: an empty throw-away store; the scripted replies; the oracle recorded at goal/v4
        recorded = oracle()["old_runner"]
        for skill in SIX:
            with self.subTest(skill=skill):
                # When: the skill runs its scripted input
                result, rec, _ = stored_run(skill, self.store, self.runs)
                # Then: the recorded model calls (order, prompt, options) and the recorded answer, 0 differences
                self.assertEqual(json.loads(json.dumps(rec.model_calls())), recorded[skill]["model_calls"])
                self.assertEqual(json.loads(json.dumps(result.answer)), recorded[skill]["answer"])
        self.assertEqual(self.store.reads, [])      # an empty store: nothing was found, and the run did not need a stored graph

    @mark.req("REQ-RUN-044")
    def test_the_run_record_names_graph_and_version(self):
        """TC-RUN-046: the run record of a run from the store has graph and graph_version (the newest); a run without a stored graph has neither field.

        Example: graph "verify.single@1", graph_version 2 after two saves; with an empty store neither key is in the record.
        """
        # Given: verify.single@1 saved twice (the second with a changed description), and an empty store
        self.store.save(VERIFY)
        self.assertEqual(self.store.save(dict(VERIFY, description="changed")), 2)
        # When: verify_claim runs once against each store
        result, _, core = stored_run("verify_claim", self.store, self.runs)
        empty = ThrowAwayStore()
        self.addCleanup(empty.close)
        other_runs = tempfile.mkdtemp(prefix="run-log-")
        self.addCleanup(__import__("shutil").rmtree, other_runs, True)
        without, _, other = stored_run("verify_claim", empty, other_runs)
        # Then: the first record names the graph and version 2, the second neither
        record = run_record(core, result)
        self.assertEqual((record.get("graph"), record.get("graph_version")), ("verify.single@1", 2))
        bare = run_record(other, without)
        self.assertEqual(("graph" in bare, "graph_version" in bare), (False, False))

    @mark.req("REQ-RUN-045")
    def test_a_stored_graph_that_cannot_run_is_refused_and_named(self):
        """TC-RUN-047: a version 2 with a cycle ends the run refused, naming cycle, the graph ID and version 2, and no step runs; version 1 alone runs.

        Example: error mentions "cycle", "verify.single@1" and "version 2"; the model and the tools were called 0 times; with version 1 only: done, model called.
        """
        # Given: version 1 sound and a version 2 that has a cycle (planted: the save path refuses cycles); the model and the tools as markers
        self.store.save(VERIFY)
        self.store.save(dict(VERIFY, description="version 2"))
        self.store.plant("verify.single@1", cycle_in)
        # When: verify_claim runs
        result, rec, core = stored_run("verify_claim", self.store, self.runs)
        # Then: refused, naming the rule, the graph and the version; no marker fired; the runner did not fall back to version 1
        self.assertEqual(result.status, "refused")
        for part in ("cycle", "verify.single@1", "version 2"):
            self.assertIn(part, result.error)
        self.assertEqual((rec.model_calls(), rec.tool_calls()), ([], []))
        # And: the sound twin (version 1 alone) runs to the end and fires its markers
        twin = ThrowAwayStore()
        self.addCleanup(twin.close)
        twin.save(VERIFY)
        sound, sound_rec, _ = stored_run("verify_claim", twin, tempfile.mkdtemp(prefix="run-log-"))
        self.assertEqual(sound.status, "done")
        self.assertGreaterEqual(len(sound_rec.model_calls()), 1)


class SameCallsAndOutputs(StoreCase):
    @mark.req("REQ-WFM-168")
    def test_the_stored_graph_makes_the_model_calls_of_the_old_runner(self):
        """TC-WFM-187: for each of the six skills the model calls from the stored graph equal those of the old runner; a planted option is reported.

        Example: research from its stored graph: the same 5 calls; with temperature 0.2 in descriptor.model the diff names call 1, field options.
        """
        for skill in SIX:
            with self.subTest(skill=skill):
                # Given: the skill saved into the store; When: it runs from there and on the old runner, on the same scripted replies
                store = ThrowAwayStore()
                self.addCleanup(store.close)
                store.save(GRAPHS[skill + ".md"])
                _, old = old_run(skill, tempfile.mkdtemp(prefix="run-log-"))
                result, new, _ = stored_run(skill, store, tempfile.mkdtemp(prefix="run-log-"))
                # Then: the lists of model calls (order, prompt text, options) are equal, and the run was from the stored graph
                self.assertEqual(len(store.reads), 1)
                self.assertIsNone(first_difference(old.model_calls(), new.model_calls()), "%s: the calls differ" % skill)
        # And: with one option changed in the stored graph the check fails and names the first differing call
        for skill in [s for s in SIX if s != "extract_claims_rules"]:
            with self.subTest(planted=skill):
                changed = json.loads(json.dumps(GRAPHS[skill + ".md"]))
                node = next(n for n in changed["nodes"] if n["id"] == "descriptor.model")
                node["data"]["value"]["options"] = {"temperature": 0.2}
                store = ThrowAwayStore()
                self.addCleanup(store.close)
                store.save(changed)
                _, old = old_run(skill, tempfile.mkdtemp(prefix="run-log-"))
                _, new, _ = stored_run(skill, store, tempfile.mkdtemp(prefix="run-log-"))
                diff = first_difference(old.model_calls(), new.model_calls())
                self.assertIsNotNone(diff)
                self.assertEqual((diff["call"], diff["field"]), (1, "options"))

    @mark.req("REQ-WFM-115")
    def test_the_rule_based_skill_gives_the_same_outputs_from_the_stored_graph(self):
        """TC-WFM-115: the 51 dev cases of EV-extraction give equal outputs from the stored graph and on the old runner; a planted difference names the case.

        Example: 51 equal outputs; with the output of one case changed the report is {"case": "num-budget", ...}.
        """
        # Given: extract_claims_rules saved; the 51 dev cases of EV-extraction (no model)
        with open(os.path.join(REPO, "eval", "suites", "extraction", "cases.jsonl"), encoding="utf-8") as fp:
            cases = [c for c in map(json.loads, fp) if "split:dev" in c["tags"]]
        self.assertEqual(len(cases), 51)
        self.store.save(GRAPHS["extract_claims_rules.md"])
        # When: every case runs from the stored graph and on the old runner in the same check
        old, new = {}, {}
        for case in cases:
            old[case["id"]] = old_run_case(case, self.runs)
            result, _, _ = stored_run("extract_claims_rules", self.store, self.runs, inputs=case["input"])
            new[case["id"]] = result.answer
        # Then: the 51 outputs are equal
        self.assertEqual(differing(old, new), [])
        self.assertEqual(len(self.store.reads), 51)
        # And: a planted difference in one output is reported with the case
        planted = dict(new, **{cases[0]["id"]: {"claims": [], "dropped": [], "snapped": 99}})
        self.assertEqual([d["case"] for d in differing(old, planted)], [cases[0]["id"]])


def old_run_case(case, folder):
    from core import Core
    from library import Library
    rec = Recording()
    core = Core(SKILLS, Library(LIBRARY), folder, model=RecordingModel(ScriptedModel(), rec), tools=scripted_tools(rec))
    return core.run("extract_claims_rules", case["input"], started_by="command").answer


def differing(old, new):
    """[{"case", "old", "new"}] for every case whose outputs differ"""
    return [{"case": case, "old": old[case], "new": new.get(case)} for case in old if old[case] != new.get(case)]


if __name__ == "__main__":
    unittest.main()
