"""
TC-WFM-037 (REQ-WFM-037): the file store of the files volume: names and types are checked, the limits are kept, nothing is deleted by the store, the list is read from the folder.
Run: python tests/test_file_store.py
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from file_store import FileStore, FileStoreError  # noqa: E402


def code_of(call):
    try:
        call()
    except FileStoreError as err:
        return err.code
    raise AssertionError("no FileStoreError raised")


class FileStoreTest(unittest.TestCase):
    def setUp(self):
        self.folder = os.path.join(tempfile.mkdtemp(), "files")
        self.store = FileStore(self.folder, max_file_bytes=100, max_total_bytes=250)

    def test_a_stored_file_is_listed_and_read_back_byte_for_byte(self):
        info = self.store.put("review-2026.md", "# Report\n", task="review", message_id="m7", account="anna")
        self.assertEqual((info["name"], info["size"], info["task"], info["message_id"]), ("review-2026.md", 9, "review", "m7"))
        listed = self.store.list()
        self.assertEqual([f["name"] for f in listed], ["review-2026.md"])
        with open(self.store.path("review-2026.md"), "rb") as handle:
            self.assertEqual(handle.read(), b"# Report\n")

    def test_a_name_with_a_path_or_odd_characters_is_refused(self):
        for bad in ("../x.md", "a/b.md", "a\\b.md", "", ".hidden.md", "x y.md"):
            self.assertEqual(code_of(lambda: self.store.put(bad, "x")), "invalid_file_name")
        self.assertEqual(self.store.list(), [])

    def test_only_the_allowed_types_are_stored(self):
        self.assertEqual(code_of(lambda: self.store.put("run.sh", "x")), "type_not_allowed")
        for ok in ("a.md", "a.tex", "a.txt", "a.json", "a.csv"):
            self.store.put(ok, "x")
        self.assertEqual(len(self.store.list()), 5)

    def test_a_file_over_the_limit_or_a_full_volume_is_refused_and_nothing_is_written(self):
        self.assertEqual(code_of(lambda: self.store.put("big.md", "x" * 101)), "too_large")
        self.store.put("a.md", "x" * 100)
        self.store.put("b.md", "x" * 100)
        self.assertEqual(code_of(lambda: self.store.put("c.md", "x" * 100)), "volume_full")
        self.assertEqual(sorted(f["name"] for f in self.store.list()), ["a.md", "b.md"])

    def test_the_same_name_gets_a_number_and_nothing_is_overwritten(self):
        first = self.store.put("r.md", "one")
        second = self.store.put("r.md", "two")
        self.assertEqual((first["name"], second["name"]), ("r.md", "r-2.md"))
        with open(self.store.path("r.md"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "one")

    def test_a_file_deleted_in_the_volume_leaves_the_list(self):
        self.store.put("a.md", "x")
        os.remove(os.path.join(self.folder, "a.md"))
        self.assertEqual(self.store.list(), [])
        self.assertEqual(code_of(lambda: self.store.path("a.md")), "not_found")

    def test_the_list_is_newest_first(self):
        self.store.put("a.md", "x")
        os.utime(os.path.join(self.folder, "a.md"), (1000, 1000))
        self.store.put("b.md", "x")
        self.assertEqual([f["name"] for f in self.store.list()], ["b.md", "a.md"])


if __name__ == '__main__':
    unittest.main()
