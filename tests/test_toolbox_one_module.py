"""
F-7 of G-V4.GRAPHAPI.RUN (T-05, D-486): the thin code of a toolbox entry reaches the `common_operations` module of the toolbox that runs it, the one
run_converted registers model and tools in, whichever of `MIA.common_operations` and `common_operations` is importable. Each case runs in a fresh
process, so the import state of this test run does not matter. Run with the MIA virtualenv: python tests/test_toolbox_one_module.py
"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL_STEP = """
import os, sys, tempfile
link = tempfile.mkdtemp()
os.symlink(%(repo)r, os.path.join(link, "MIA"))
sys.path[:0] = [link, %(repo)r]
%(imports)s
box = toolbox.Toolbox(WorkflowLibrary(Storage(FileBackend(tempfile.mkdtemp()))), lambda account: True, skill_converter._NoEvents())
box.seed_shipped(os.path.join(%(repo)r, "library", "nodes"))
common_operations.reset()
common_operations.register_tool("web_search", lambda **kw: ["hit"])
print(box.run_stage("tool.web_search", {"tool": {"tool": "web_search"}, "query": "x"}, {}, {}))
"""
PLAIN = """import MIA.common_operations
import common_operations, toolbox, skill_converter
from workflow_library import WorkflowLibrary
from storage import Storage
from storage_files import FileBackend"""
PACKAGE = """from MIA import common_operations, toolbox, skill_converter
from MIA.workflow_library import WorkflowLibrary
from MIA.storage import Storage
from MIA.storage_files import FileBackend"""


def tool_step_in_fresh_process(imports):
    """(exit code, last lines of the output) of a fresh Python that registers web_search on the toolbox's module and runs the shipped tool step"""
    done = subprocess.run([sys.executable, "-c", TOOL_STEP % {"repo": REPO, "imports": imports}], cwd=HERE, capture_output=True, text=True, timeout=120)
    return done.returncode, (done.stdout + done.stderr)[-500:]


class ThinCodeReachesTheToolboxModule(unittest.TestCase):
    def test_plain_modules_with_the_package_importable(self):
        """F-7: plain `toolbox` and `common_operations` while the package MIA is importable and imported: the tool step finds the registered tool.
        Example: register_tool("web_search") on the plain module, run_stage("tool.web_search") -> ["hit"] (before the fix: ToolMissing)."""
        # Given: a fresh process in which MIA.common_operations was imported next to the plain modules
        # When: a tool registered on the plain module runs as the shipped tool step
        status, output = tool_step_in_fresh_process(PLAIN)
        # Then: the step reaches it
        self.assertEqual(status, 0, output)
        self.assertIn("hit", output)

    def test_the_package_as_the_app_runs_it(self):
        """The app (`python -m MIA`) imports everything from the package: the tool step finds the tool there as before.
        Example: register_tool on MIA.common_operations, run_stage("tool.web_search") -> ["hit"]."""
        # Given: a fresh process that imports the package only
        # When: a tool registered on the package's module runs as the shipped tool step
        status, output = tool_step_in_fresh_process(PACKAGE)
        # Then: the step reaches it
        self.assertEqual(status, 0, output)
        self.assertIn("hit", output)


if __name__ == "__main__":
    unittest.main()
