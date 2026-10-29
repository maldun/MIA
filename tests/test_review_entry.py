"""TC-WFM-018 (REQ-WFM-018): the review is an entry of the workflow library: saved once as a draft, a valid graph (data and process alternate), every stage names what runs it, and
it cannot be promoted without its specification and benchmark. Run with: python tests/test_review_entry.py"""
import os
import sys
import tempfile
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extensions.review import review_entry as re_
from storage import Storage
from storage_files import FileBackend
from workflow_library import WorkflowLibrary, WorkflowLibraryError


class ReviewEntry(unittest.TestCase):
    def setUp(self):
        self.lib = WorkflowLibrary(Storage(FileBackend(tempfile.mkdtemp())))

    def test_it_is_saved_once_as_a_draft(self):
        self.assertTrue(re_.ensure_review_workflow(self.lib))
        self.assertFalse(re_.ensure_review_workflow(self.lib))
        self.assertEqual(len(self.lib.history("workflows", "review")), 1)
        self.assertEqual(self.lib.read("workflows", "review")["status"], "draft")

    def test_data_and_process_nodes_alternate_and_the_chain_has_no_cycle(self):
        doc = re_.review_workflow()
        kinds = [n["kind"] for n in doc["nodes"]]
        self.assertTrue(all(a != b for a, b in zip(kinds, kinds[1:])))
        self.assertEqual(kinds[0], "data")
        self.assertEqual(kinds[-1], "data")
        self.assertEqual(len(doc["edges"]), len(doc["nodes"]) - 1)

    def test_every_process_names_what_runs_it(self):
        for node in re_.review_workflow()["nodes"]:
            if node["kind"] == "process":
                self.assertTrue(any(w in node["note"] for w in ("skill ", "review_stages.", "scholar.", "fulltext.", "review_chat.")), node["id"])

    def test_it_cannot_be_promoted_without_specification_and_benchmark(self):
        re_.ensure_review_workflow(self.lib)
        with self.assertRaises(WorkflowLibraryError) as raised:
            self.lib.set_status("review", "tested", "anna")
        self.assertEqual(raised.exception.code, "not_promotable")


if __name__ == "__main__":
    unittest.main()
