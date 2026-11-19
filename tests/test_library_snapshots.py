"""The snapshot operations of the real WorkflowLibrary (G-V2.SNAPSHOT, T-SN-01): what the contract suite does not pin. Run with: python tests/test_library_snapshots.py"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import Storage                              # noqa: E402
from storage_files import FileBackend                    # noqa: E402
from workflow_library import WorkflowLibrary, WorkflowLibraryError  # noqa: E402

SKILL = {"id": "s", "data": {"command": "s", "workflow_graph_id": "lookup", "context_graph_id": "places"}}


def library(**kw):
    return WorkflowLibrary(Storage(FileBackend(tempfile.mkdtemp())), **kw)


class LibrarySnapshots(unittest.TestCase):
    def test_without_is_owner_nobody_is_the_owner(self):
        lib = library()
        for call in (lambda: lib.snapshot("a", "anna"), lambda: lib.list_snapshots("anna"), lambda: lib.restore_snapshot("a", "anna")):
            with self.assertRaises(WorkflowLibraryError) as caught:
                call()
            self.assertEqual(caught.exception.code, "forbidden")

    def test_pins_is_a_mapping_or_a_function_and_defaults_to_empty(self):
        self.assertEqual(library().pins(), {})
        self.assertEqual(library(pins={"MP-light": "m"}).pins(), {"MP-light": "m"})
        self.assertEqual(library(pins=lambda: {"MP-full": "n"}).pins(), {"MP-full": "n"})

    def test_snapshots_are_not_a_kind_of_the_graph_api(self):
        import workflow_library
        self.assertNotIn("snapshots", workflow_library.KINDS)

    def test_the_seam_fires_once_and_a_later_restore_succeeds(self):
        lib = library(is_owner=lambda a: a == "anna")
        lib.save("skills", "s", SKILL, "anna")
        lib.snapshot("a", "anna")
        lib.save("skills", "s", dict(SKILL, data=dict(SKILL["data"], command="t")), "anna")
        lib.fail_set_current_version_at = 1
        with self.assertRaises(WorkflowLibraryError) as caught:
            lib.restore_snapshot("a", "anna")
        self.assertEqual(caught.exception.code, "unavailable")
        self.assertEqual(lib.read("skills", "s")["version"], 2)          # changed back
        lib.restore_snapshot("a", "anna")                               # the seam is spent
        self.assertEqual(lib.read("skills", "s")["version"], 1)

    def test_moves_outside_a_restore_are_not_counted(self):
        lib = library()
        lib.save("skills", "s", SKILL, "anna")
        lib.fail_set_current_version_at = 1
        self.assertEqual(lib.set_current_version("skills", "s", 1, "anna"), {"version": 1})

    def test_an_empty_name_is_invalid_schema(self):
        lib = library(is_owner=lambda a: True)
        with self.assertRaises(WorkflowLibraryError) as caught:
            lib.snapshot("", "anna")
        self.assertEqual((caught.exception.code, caught.exception.rule), ("invalid", "schema"))

    def test_f04_only_a_bad_name_is_mapped_to_invalid_name(self):
        import snapshot_store
        lib = library(is_owner=lambda a: True)
        original = snapshot_store.SnapshotStore.snapshot
        snapshot_store.SnapshotStore.snapshot = lambda self, name, account: (_ for _ in ()).throw(ValueError("other"))
        try:
            with self.assertRaises(ValueError):          # not turned into invalid/schema/name
                lib.snapshot("a", "anna")
        finally:
            snapshot_store.SnapshotStore.snapshot = original

    def test_f04_a_malformed_stored_snapshot_is_invalid_schema_snapshot(self):
        lib = library(is_owner=lambda a: True)
        lib.save("skills", "s", SKILL, "anna")
        lib.snapshot("a", "anna")
        doc = lib.read_snapshot("a")
        doc["items"] = [{"kind": "transforms", "id": "t", "version": 1}]          # a transform without trust and lifecycle
        lib.save("snapshots", "bad", dict(doc, name="bad"), "anna")
        before = lib.list_snapshots("anna")
        with self.assertRaises(WorkflowLibraryError) as caught:
            lib.restore_snapshot("bad", "anna")
        self.assertEqual((caught.exception.code, caught.exception.rule, caught.exception.detail), ("invalid", "schema", "snapshot"))
        self.assertEqual(lib.list_snapshots("anna"), before)

    def test_f01_a_snapshot_is_written_once_even_when_the_name_check_is_passed_by_a_second_writer(self):
        lib = library(is_owner=lambda a: True)
        lib.snapshot("a", "anna")
        first = lib.read_snapshot("a")
        real = lib.list_ids
        lib.list_ids = lambda kind: [] if kind == "snapshots" else real(kind)          # the other writer is not visible when the name is checked
        with self.assertRaises(WorkflowLibraryError) as caught:
            lib.snapshot("a", "anna")
        self.assertEqual(caught.exception.code, "conflict")
        del lib.list_ids
        self.assertEqual(len(lib.history("snapshots", "a")), 1)          # no version 2
        self.assertEqual(lib.read_snapshot("a"), first)

    def test_f01_a_new_version_of_an_ordinary_item_is_still_allowed(self):
        lib = library()
        lib.save("skills", "s", SKILL, "anna")
        self.assertEqual(lib.save("skills", "s", SKILL, "anna"), {"version": 2})


if __name__ == "__main__":
    unittest.main()
