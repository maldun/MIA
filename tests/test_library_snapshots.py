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


if __name__ == "__main__":
    unittest.main()
