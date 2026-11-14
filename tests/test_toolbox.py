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
from toolbox import REASON_IMPORTED, Toolbox, ToolboxError               # noqa: E402
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
        """Example: an allowance given while the transform is live is refused (F2, D-229); a refused allowance leaves the lifecycle as it was."""
        library = TransformLibraryMock()
        box = Toolbox(library, lambda account: account == "anna", EventRecord())
        box.import_transform(exchange_file("t.one", code="def run(args):\n    return 1\n"), "anna")
        with self.assertRaises(ToolboxError) as caught:
            box.set_lifecycle("t.one", "draft", "anna", allow_baseline=True)
        self.assertEqual(caught.exception.code, "allowance_needs_retired")
        with self.assertRaises(ToolboxError):
            box.run("t.one", {}, as_baseline=True)
        with self.assertRaises(ToolboxError):
            box.set_lifecycle("t.one", "retired", "guest", allow_baseline=True)
        self.assertEqual(box.look_up("t.one")["lifecycle"], "draft")
        box.set_lifecycle("t.one", "retired", "anna", allow_baseline=True)      # the twin: retired and allowed runs as baseline
        self.assertEqual(box.run("t.one", {}, as_baseline=True), 1)


class VerifyFindings:
    """Findings F1 to F5 of the Verify run of 2026-11-12 (D-229), on the mock and on the real library. A failing test came first for each."""
    def make_library(self):
        raise NotImplementedError

    def setUp(self):
        self.library = self.make_library()
        self.events = EventRecord()
        self.box = Toolbox(self.library, lambda account: account == "anna", self.events)

    def untrusted_retired_allowed(self, tid="t.one"):
        self.box.import_transform(exchange_file(tid, 1), "guest")
        self.box.set_lifecycle(tid, "retired", "anna", allow_baseline=True)

    def test_f1_an_allowance_does_not_survive_a_newer_version(self):
        """Example: the owner allows version 1 as baseline; another account imports version 2; the check is refused as untrusted."""
        self.untrusted_retired_allowed()
        self.box.import_transform(exchange_file("t.one", 2), "mallory")
        self.assertFalse(self.box.look_up("t.one")["baseline_allowed"])
        with self.assertRaises(ToolboxError) as caught:
            self.box.run("t.one", {}, as_baseline=True)
        self.assertEqual(caught.exception.code, "untrusted")

    def test_f2_an_allowance_belongs_to_a_retirement(self):
        """Example: an allowance with another lifecycle is refused and stores nothing; un-retiring clears an allowance."""
        self.box.import_transform(exchange_file("t.one", 1), "guest")
        with self.assertRaises(ToolboxError) as caught:
            self.box.set_lifecycle("t.one", "draft", "anna", allow_baseline=True)
        self.assertEqual(caught.exception.code, "allowance_needs_retired")
        self.assertFalse(self.box.look_up("t.one")["baseline_allowed"])
        self.untrusted_retired_allowed("t.two")
        self.box.set_lifecycle("t.two", "draft", "guest")
        self.assertFalse(self.box.look_up("t.two")["baseline_allowed"])
        self.box.set_lifecycle("t.two", "retired", "guest")         # a later retire by any account must not bring it back
        with self.assertRaises(ToolboxError):
            self.box.run("t.two", {}, as_baseline=True)

    def test_f3_a_float_version_is_invalid_file(self):
        good = json.loads(exchange_file("t.one"))
        with self.assertRaises(ToolboxError) as caught:
            self.box.import_transform(json.dumps(dict(good, version=1.0)), "anna")
        self.assertEqual(caught.exception.code, "invalid_file")
        self.assertEqual(self.library.list_ids("transforms"), [])

    def test_f4_the_reason_after_an_untrust_is_not_the_import_text_and_not_empty(self):
        """Example: a trusted entry, untrusted by the owner, and a shipped one untrusted by an account."""
        self.box.import_transform(exchange_file("t.one", 1), "guest")
        self.box.set_trust("t.one", "trusted", "anna")
        self.box.set_trust("t.one", "untrusted", "anna")
        reason = self.box.look_up("t.one")["reason"]
        self.assertTrue(reason)
        self.assertNotEqual(reason, REASON_IMPORTED)

    def test_f5_a_failed_event_refuses_the_replace(self):
        """Example: the event stand-in raises; the call raises ToolboxError(store_failed) and the entry stays in version 1 (N2)."""
        self.box.import_transform(exchange_file("t.one", 1), "guest")
        self.box.set_trust("t.one", "trusted", "anna")

        def broken(event):
            raise RuntimeError("event store down")
        self.events.record = broken
        with self.assertRaises(ToolboxError) as caught:
            self.box.import_transform(exchange_file("t.one", 2), "guest")
        self.assertEqual(caught.exception.code, "store_failed")
        self.assertEqual(self.box.look_up("t.one")["version"], 1)

    def test_n2_a_failed_save_is_a_toolbox_error_and_the_old_version_stays(self):
        """Example: the save raises after the allowance was cleared; ToolboxError(store_failed), version 1, no allowance kept (N2, N3c)."""
        self.untrusted_retired_allowed()

        def broken(*args, **kwargs):
            raise RuntimeError("disk")
        self.library.save = broken
        with self.assertRaises(ToolboxError) as caught:
            self.box.import_transform(exchange_file("t.one", 2), "mallory")
        self.assertEqual(caught.exception.code, "store_failed")
        entry = self.box.look_up("t.one")
        self.assertEqual(entry["version"], 1)
        self.assertFalse(entry["baseline_allowed"])

    def test_n1_an_untrust_of_an_untrusted_entry_keeps_its_reason(self):
        """Example: a fresh import untrusted again by an account still says it came from outside."""
        self.box.import_transform(exchange_file("t.one", 1), "guest")
        self.box.set_trust("t.one", "untrusted", "guest")
        self.box.set_trust("t.one", "untrusted", "anna")
        self.assertEqual(self.box.look_up("t.one")["reason"], REASON_IMPORTED)

    def test_n3a_the_reason_texts_by_account_and_for_a_shipped_entry(self):
        """Example: an account's untrust, the owner's untrust and an untrusted shipped entry each have their own non-empty text."""
        self.box.import_transform(exchange_file("t.one", 1), "guest")
        self.box.set_trust("t.one", "trusted", "anna")
        self.box.set_trust("t.one", "untrusted", "guest")
        by_account = self.box.look_up("t.one")["reason"]
        self.box.set_trust("t.one", "trusted", "anna")
        self.box.set_trust("t.one", "untrusted", "anna")
        by_owner = self.box.look_up("t.one")["reason"]
        folder = tempfile.mkdtemp(prefix="toolbox-nodes-")
        self.addCleanup(shutil.rmtree, folder, True)
        os.makedirs(os.path.join(folder, "s.one"))
        with open(os.path.join(folder, "s.one", "1.json"), "w") as handle:
            json.dump({"id": "s.one", "version": 1, "inputs": {}, "outputs": {}}, handle)
        self.box.seed_shipped(folder)
        self.box.set_trust("s.one", "untrusted", "guest")
        shipped = self.box.look_up("s.one")["reason"]
        for reason in (by_account, by_owner, shipped):
            self.assertTrue(reason)
            self.assertNotEqual(reason, REASON_IMPORTED)
        self.assertNotEqual(by_account, by_owner)

    def test_n3b_other_whole_looking_numbers_are_invalid_file(self):
        good = json.loads(exchange_file("t.one"))
        text = json.dumps(dict(good, version=0))
        for number in ("1e0", "2.0", "1e400"):
            with self.subTest(number=number):
                with self.assertRaises(ToolboxError) as caught:
                    self.box.import_transform(text.replace('"version": 0', '"version": ' + number), "anna")
                self.assertEqual(caught.exception.code, "invalid_file")
        self.assertEqual(self.library.list_ids("transforms"), [])

    def test_f8_an_unknown_id_is_a_toolbox_error(self):
        """Example: every call that names an ID the toolbox does not hold raises ToolboxError("not_found") naming the ID."""
        calls = (lambda: self.box.look_up("t.none"), lambda: self.box.run("t.none", {}), lambda: self.box.set_trust("t.none", "untrusted", "anna"),
                 lambda: self.box.set_lifecycle("t.none", "draft", "anna"), lambda: self.box.export_transform("t.none"))
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises(ToolboxError) as caught:
                    call()
                self.assertEqual(caught.exception.code, "not_found")
                self.assertIn("t.none", caught.exception.why)


class VerifyFindingsMock(VerifyFindings, unittest.TestCase):
    def make_library(self):
        return TransformLibraryMock()


class VerifyFindingsReal(VerifyFindings, unittest.TestCase):
    def make_library(self):
        folder = tempfile.mkdtemp(prefix="toolbox-store-")
        self.addCleanup(shutil.rmtree, folder, True)
        return WorkflowLibrary(Storage(FileBackend(folder)))


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

    def test_a_seeded_entry_is_tested_with_the_evidence_shipped_with_mia(self):
        """Example: D-226 (owner 2026-11-11): a shipped entry shows lifecycle tested and the evidence, not draft."""
        import shutil
        import tempfile
        from toolbox_fakes import shipped_copy
        folder = tempfile.mkdtemp(prefix="toolbox-nodes-")
        self.addCleanup(shutil.rmtree, folder, True)
        shipped_copy(folder)
        box = Toolbox(TransformLibraryMock(), lambda account: True, EventRecord())
        box.seed_shipped(folder)
        entry = box.look_up("check.plain")
        self.assertEqual((entry["lifecycle"], entry["evidence"]), ("tested", "shipped with MIA"))


if __name__ == "__main__":
    unittest.main()
