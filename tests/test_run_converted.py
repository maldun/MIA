"""
Unit tests of the settings argument of thin toolbox entries (T-CV-04, D-254): the settings object of a transform reaches its `run` entry, so code.pick_field gets its path.
Run: python tests/test_run_converted.py
"""
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers"), os.path.join(REPO, "tests", "helpers", "mocks")):
    sys.path.insert(0, path)

from toolbox_fakes import EventRecord, exchange_file    # noqa: E402
from toolbox import Toolbox                              # noqa: E402
from storage import Storage                              # noqa: E402
from storage_files import FileBackend                    # noqa: E402
from workflow_library import WorkflowLibrary             # noqa: E402
import common_operations as ops                          # noqa: E402
import skill_converter                                   # noqa: E402


class SettingsReachTheEntry(unittest.TestCase):
    def setUp(self):
        folder = tempfile.mkdtemp(prefix="run-converted-")
        self.addCleanup(shutil.rmtree, folder, True)
        ops.reset()
        self.addCleanup(ops.reset)
        self.box = Toolbox(WorkflowLibrary(Storage(FileBackend(folder))), lambda account: True, EventRecord())
        self.box.seed_shipped(os.path.join(REPO, "library", "nodes"))

    def test_pick_field_reads_its_path_from_the_settings(self):
        """Example: run("code.pick_field", {"value": {"claims": [1, 2]}}, settings={"path": "claims.1"}) gives 2."""
        # Given the shipped pick entry and a settings object with the path
        # When it runs with the settings
        got = self.box.run("code.pick_field", {"value": {"claims": [1, 2]}}, settings={"path": "claims.1"})
        # Then the path of the settings is used
        self.assertEqual(got, 2)

    def test_an_entry_that_takes_only_args_still_runs_when_settings_are_given(self):
        """Example: an imported entry `def run(args)` is called with the args alone when settings are handed over."""
        # Given an entry in the old form run(args)
        self.box.import_transform(exchange_file("t.one", code="def run(args):\n    return args['x']\n"), "anna")
        self.box.library.set_meta("t.one", "anna", trust="trusted")
        # When it runs with settings
        # Then it still works
        self.assertEqual(self.box.run("t.one", {"x": 5}, settings={"path": "a"}), 5)

    def test_the_adapter_hands_the_settings_node_to_a_run_entry(self):
        """Example: a graph with one pick node and a settings node gives the adapter's stage the settings {"path": "claims"}."""
        # Given a one-node graph and the toolbox
        graph = {"nodes": [{"id": "pick", "data": {"type": "transform", "toolbox_id": "code.pick_field"}}], "edges": []}
        nodes, _trust = skill_converter.stages_from_toolbox(graph, self.box)
        # When the stage runs with settings in the node argument
        got = nodes["pick"].function({"value": {"claims": ["a"]}}, {}, {"path": "claims.0"})
        # Then the entry received the path
        self.assertEqual(got, "a")


if __name__ == "__main__":
    unittest.main()
