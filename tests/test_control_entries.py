"""
The controllers inside the converted path (T-CV-06/07 part, G-V2.CONVERT, D-258): the toolbox entries control.branch, control.map and control.loop, and a converted
verify_computable that runs its repair loop through them on scripted replies and a bound fake script_check. No model, no sandbox.
Run: python tests/test_control_entries.py
"""
import json
import os
import shutil
import sys
import tempfile
import types
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers"), os.path.join(REPO, "tests", "helpers", "mocks")):
    sys.path.insert(0, path)

from call_recording import ScriptedModel                 # noqa: E402
from toolbox_fakes import EventRecord                    # noqa: E402
from toolbox import Toolbox, ToolboxError                # noqa: E402
from storage import Storage                              # noqa: E402
from storage_files import FileBackend                    # noqa: E402
from workflow_library import WorkflowLibrary             # noqa: E402
import common_operations as ops                          # noqa: E402
import skill_converter                                   # noqa: E402
import plain_modules                                       # noqa: E402

setUpModule, tearDownModule = plain_modules.hooks()      # the package MIA is not importable while this module runs: F-3, tests/plain_modules.py

SKILLS, LIBRARY = os.path.join(REPO, "skills"), os.path.join(REPO, "library")
INPUT = {"claim": "1628.89 euros is what 1000 euros grow to", "data_description": "principal, rate, years, claimed", "data": {"principal": 1000, "rate": 5, "years": 10, "claimed": 1628.89}}


class Entries(unittest.TestCase):
    def setUp(self):
        folder = tempfile.mkdtemp(prefix="control-entries-")
        self.addCleanup(shutil.rmtree, folder, True)
        ops.reset()
        self.addCleanup(ops.reset)
        self.box = Toolbox(WorkflowLibrary(Storage(FileBackend(folder))), lambda account: True, EventRecord())

    def test_the_three_controllers_are_trusted_entries_and_seeding_twice_adds_nothing(self):
        """Example: after seed_controls the entries control.branch, control.loop and control.map are trusted; a second call changes nothing."""
        # Given a toolbox seeded twice
        self.box.seed_controls()
        self.box.seed_controls()
        # Then the three entries are there, trusted, once
        self.assertEqual([i for i in self.box.offer() if i.startswith("control.")], ["control.branch", "control.loop", "control.map"])
        self.assertEqual({self.box.look_up(i)["trust"] for i in self.box.offer()}, {"trusted"})

    def test_a_controller_without_a_registered_run_refuses_clearly(self):
        """Example: calling control.branch outside run_converted raises RuntimeError that says no node call is registered."""
        self.box.seed_controls()
        node = {"construct": "branch", "node": {"id": "b", "kind": "branch", "if": {"ref": "x", "op": "true"}, "then": []}}
        with self.assertRaisesRegex(RuntimeError, "no node call"):
            self.box.run_stage("control.branch", {"x": True}, {}, node)

    def test_a_controller_runs_its_nodes_through_the_registered_call(self):
        """Example: with a registered call, control.branch runs the node of its then part and returns the written variable."""
        self.box.seed_controls()
        seen = []
        ops.register_control(lambda use, args: seen.append((use, args)) or "done")
        node = {"construct": "branch", "node": {"id": "b", "kind": "branch", "if": {"ref": "x", "op": "true"}, "then": [{"id": "s", "use": "s@1", "wire": {"a": "$x"}, "output": "y"}]}}
        out = self.box.run_stage("control.branch", {"x": True}, {"y": None}, node)
        self.assertEqual((seen, out), ([("s@1", {"a": True})], {"outputs": {"y": "done"}}))

    def test_a_retired_controller_does_not_run(self):
        """Example: retiring control.loop makes it a step that does not run, like any entry (REQ-WFM-068)."""
        self.box.seed_controls()
        self.box.set_lifecycle("control.loop", "retired", "owner")
        with self.assertRaises(ToolboxError):
            self.box.run_stage("control.loop", {}, {}, {})


class ConvertedRepair(unittest.TestCase):
    def test_verify_computable_repairs_through_the_branch_and_the_loop(self):
        """Example: the first script check is inconclusive, the repaired one holds: the loop body runs once, the converted run is done and the verdict is the second one."""
        # Given a script check that is inconclusive once and then gives a verdict
        verdicts = iter([{"status": "inconclusive", "detail": "no values"}, {"status": "true", "detail": "ok"}])
        asked = []

        def script_check(**args):
            asked.append(args["script"])
            return next(verdicts)
        model = ScriptedModel([json.dumps({"script": "result = 1  # first draft", "approach": "a"}), json.dumps({"script": "result = 2  # repaired one", "approach": "b"})])
        # When verify_computable runs converted
        run = skill_converter.run_converted("verify_computable", INPUT, model=model, skills_dir=SKILLS, library_dir=LIBRARY, functions={"script_check": script_check})
        # Then the repair happened: two script checks on two different scripts, and the status of the last one is the answer
        self.assertEqual(run.status, "done", run.error)
        self.assertEqual(len(asked), 2)
        self.assertNotEqual(asked[0], asked[1])
        self.assertEqual(run.answer["status"], "true")


class FakeRouter:
    """a sandbox router that records what it is asked to run and answers like a finished run (the contract of sandbox.SandboxRouter.run)"""
    def __init__(self, result):
        self.result, self.asked = result, []

    def run(self, script, data, operation=None, **more):
        self.asked.append({"script": script, "data": data, "operation": operation, "more": more})
        return types.SimpleNamespace(status="ok", result=self.result, script_hash="h", backend="fake", tier="weak", degraded=False, seconds=0.0, stdout="", error=None, problems=[])


class ScriptsOnTheSandbox(unittest.TestCase):
    """T-CV-07a (D-259): script_check of the converted path is the function of the old runner (checks.make_script_check) on the router the caller hands over"""
    def run_skill(self, **more):
        model = ScriptedModel([json.dumps({"script": "result = 1  # the written script", "approach": "a"})] * 3)
        return skill_converter.run_converted("verify_computable", INPUT, model=model, skills_dir=SKILLS, library_dir=LIBRARY, **more)

    def test_the_script_runs_on_the_given_router_as_a_compute_operation_of_the_model(self):
        """Example: the written script and the data reach router.run once, as Operation compute from origin model, and a holds result with values gives status true."""
        # Given a router whose script run holds with values
        router = FakeRouter({"holds": True, "values": {"p": 1000}, "explanation": "recomputed"})
        # When verify_computable runs converted with that sandbox
        run = self.run_skill(sandbox=router)
        # Then the router ran the model's script on the data as the old runner would
        self.assertEqual(run.status, "done", run.error)
        self.assertEqual(len(router.asked), 1)
        asked = router.asked[0]
        self.assertIn("the written script", asked["script"])
        self.assertEqual(asked["data"], INPUT["data"])
        self.assertEqual((asked["operation"].kind, asked["operation"].origin), ("compute", "model"))
        self.assertEqual(run.answer["status"], "pass")

    def test_without_a_sandbox_the_verdict_is_inconclusive_and_nothing_runs(self):
        """Example: no sandbox: the check says so (inconclusive, no sandbox is configured) and the run is done; no script is executed anywhere."""
        run = self.run_skill()
        self.assertEqual(run.status, "done", run.error)
        self.assertIn("no sandbox is configured", json.dumps(run.values, default=str))


if __name__ == "__main__":
    unittest.main()
