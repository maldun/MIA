"""
Toolbox import checks beyond the acceptance tests (REQ-WFM-052, 053, 055): every malformed exchange file is refused as invalid_file and stores nothing.
Run: python tests/test_toolbox.py
"""
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers"), os.path.join(REPO, "tests", "helpers", "mocks")):
    sys.path.insert(0, path)

from if_203_transforms import TransformLibraryMock     # noqa: E402
from toolbox_fakes import EventRecord, exchange_file    # noqa: E402
from toolbox import Toolbox, ToolboxError               # noqa: E402
from storage import Storage                             # noqa: E402
from storage_files import FileBackend                   # noqa: E402
from workflow_library import WorkflowLibrary            # noqa: E402

# The acceptance tests of the toolbox run once more on the real library (T-06, TR-TOOLBOX-001): the same file under another module name, since this module is called test_toolbox too.
_spec = importlib.util.spec_from_file_location("acceptance_toolbox", os.path.join(REPO, "tests", "acceptance", "test_toolbox.py"))
acceptance = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(acceptance)


class ToolboxOnTheRealLibrary(acceptance.ToolboxAcceptance):
    """Every acceptance test of the toolbox on the real WorkflowLibrary over the real Storage (file backend) instead of the mock; the stand-ins for accounts and events stay."""
    def setUp(self):
        super().setUp()
        folder = tempfile.mkdtemp(prefix="toolbox-store-")
        self.addCleanup(shutil.rmtree, folder, True)
        self.library = WorkflowLibrary(Storage(FileBackend(folder)))
        self.box = Toolbox(self.library, self.accounts.is_owner, self.events)


class ImportChecks(unittest.TestCase):
    def setUp(self):
        self.library = TransformLibraryMock()
        self.box = Toolbox(self.library, lambda account: True, EventRecord())

    def test_malformed_files_are_refused_and_store_nothing(self):
        """Example: text that is not JSON, a JSON list, version 0, version true and an `inputs` that is a text."""
        good = json.loads(exchange_file("t.one"))
        bad = ["not json", "[]", json.dumps(dict(good, version=0)), json.dumps(dict(good, version=True)), json.dumps(dict(good, inputs="x")), json.dumps(dict(good, id=""))]
        for text in bad:
            with self.subTest(text=text[:30]):
                with self.assertRaises(ToolboxError) as caught:
                    self.box.import_transform(text, "anna")
                self.assertEqual(caught.exception.code, "invalid_file")
        self.assertEqual(self.library.list_ids("transforms"), [])
        self.assertEqual(self.box.import_transform(json.dumps(good), "anna"), "t.one")      # the twin is accepted


class BaselineChecks(unittest.TestCase):
    def test_the_allowance_counts_only_for_a_retired_transform_and_a_failed_set_changes_nothing(self):
        """Example: an allowance given while the transform is live does not let it run as baseline; a refused allowance leaves the lifecycle as it was."""
        library = TransformLibraryMock()
        box = Toolbox(library, lambda account: account == "anna", EventRecord())
        box.import_transform(exchange_file("t.one", code="def run(args):\n    return 1\n"), "anna")
        box.set_lifecycle("t.one", "draft", "anna", allow_baseline=True)
        with self.assertRaises(ToolboxError) as caught:
            box.run("t.one", {}, as_baseline=True)
        self.assertEqual(caught.exception.code, "untrusted")
        with self.assertRaises(ToolboxError):
            box.set_lifecycle("t.one", "retired", "guest", allow_baseline=True)
        self.assertEqual(box.look_up("t.one")["lifecycle"], "draft")
        box.set_lifecycle("t.one", "retired", "anna")      # the twin: retired and allowed runs as baseline
        self.assertEqual(box.run("t.one", {}, as_baseline=True), 1)


class SeedChecks(unittest.TestCase):
    def test_seeding_twice_adds_nothing_and_keeps_a_changed_trust(self):
        """Example: after the second start a shipped node untrusted by hand is still untrusted and the toolbox holds the same entries."""
        import shutil
        import tempfile
        from toolbox_fakes import shipped_copy
        folder = tempfile.mkdtemp(prefix="toolbox-nodes-")
        self.addCleanup(shutil.rmtree, folder, True)
        shipped_copy(folder)
        library = TransformLibraryMock()
        box = Toolbox(library, lambda account: True, EventRecord())
        box.seed_shipped(folder)
        box.set_trust("check.plain", "untrusted", "anna")
        box.seed_shipped(folder)
        self.assertEqual(library.list_ids("transforms"), ["check.double", "check.gone", "check.plain"])
        self.assertEqual(library.history("transforms", "check.plain")[-1]["version"], 1)
        self.assertEqual(box.look_up("check.plain")["trust"], "untrusted")


if __name__ == "__main__":
    unittest.main()
