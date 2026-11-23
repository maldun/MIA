"""The file backend's own operations for G-V4.GRAPHSTORE.TRANSFER T-02: durable replacement (REQ-SLY-023), cutting a record back to a version
(REQ-SLY-038's backend operation) and writing a plain file durably (put_file, used by the aside file of REQ-SLY-026).
Run with: python tests/test_storage_files.py"""
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from markers import mark                         # noqa: E402
from storage_files import FileBackend            # noqa: E402


def entry(record_id, version):
    return {"id": record_id, "version": version, "author": "ann", "time": "2026-11-23T10:00:0%dZ" % version, "doc": {"text": "v%d" % version}}


class Recorded:
    """Records the calls of os.fsync (file or folder) and os.replace while active."""

    def __init__(self):
        self.calls = []
        self._fsync, self._replace = os.fsync, os.replace

    def fsync(self, fd):
        self.calls.append(("fsync", "folder" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file"))
        return self._fsync(fd)

    def replace(self, a, b):
        self.calls.append(("replace",))
        return self._replace(a, b)

    def __enter__(self):
        self._patches = [mock.patch("os.fsync", self.fsync), mock.patch("os.replace", self.replace)]
        for patch in self._patches:
            patch.start()
        return self

    def __exit__(self, *exc):
        for patch in self._patches:
            patch.stop()


class FileBackendTransfer(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.backend = FileBackend(self.dir)

    def with_versions(self, record_id, n):
        for version in range(1, n + 1):
            self.backend.append("graphs", record_id, entry(record_id, version))

    @mark.req("REQ-SLY-023")
    def test_an_append_flushes_the_file_replaces_then_flushes_the_folder(self):
        """An append into a new table writes durably: fsync of the new file, replace, fsync of the folder, and nothing else.

        Example: append of memos/m version 1 -> calls == [fsync file, replace, fsync folder].
        """
        # Given: an empty files store with the calls recorded
        with Recorded() as recorded:
            # When: one version is appended
            self.backend.append("memos", "m", entry("m", 1))
        # Then: exactly the three calls, in this order, and the version is there
        self.assertEqual(recorded.calls, [("fsync", "file"), ("replace",), ("fsync", "folder")])
        self.assertEqual(self.backend.versions("memos", "m"), [entry("m", 1)])

    @mark.req("REQ-SLY-023")
    def test_a_failed_write_leaves_the_old_file_and_no_temporary_file(self):
        """A write that fails before the replacement keeps the record as it was and leaves no temporary file behind.

        Example: memos/m at version 1, fsync raises during the append of version 2 -> versions [1]; the folder holds only m.json.
        """
        # Given: a record at version 1 and a failing flush
        self.backend.append("memos", "m", entry("m", 1))
        # When: the append of version 2 fails at the flush
        with mock.patch("os.fsync", side_effect=OSError("disk gone")), self.assertRaises(OSError):
            self.backend.append("memos", "m", entry("m", 2))
        # Then: the old file is untouched and no temporary file is left
        self.assertEqual(self.backend.versions("memos", "m"), [entry("m", 1)])
        self.assertEqual(os.listdir(os.path.join(self.dir, "memos")), ["m.json"])

    @mark.req("REQ-SLY-038")
    def test_a_record_cut_back_to_version_2_lists_versions_1_and_2(self):
        """cut keeps the versions 1 to n, unchanged, and replaces the file durably.

        Example: sample.code at versions 1..4, cut to 2 -> versions [1, 2]; calls == [fsync file, replace, fsync folder].
        """
        # Given: a record with four versions
        self.with_versions("sample.code", 4)
        # When: it is cut back to version 2
        with Recorded() as recorded:
            self.backend.cut("graphs", "sample.code", 2)
        # Then: versions 1 and 2 remain unchanged, written durably
        self.assertEqual(self.backend.versions("graphs", "sample.code"), [entry("sample.code", 1), entry("sample.code", 2)])
        self.assertEqual(recorded.calls, [("fsync", "file"), ("replace",), ("fsync", "folder")])

    @mark.req("REQ-SLY-038")
    def test_a_cut_at_or_above_the_last_version_writes_nothing(self):
        """Cutting a record back to its last version, above it or a missing record changes nothing and writes nothing.

        Example: sample.code at versions 1..2, cut to 2 and to 5 -> versions [1, 2], no call; missing/x cut to 1 -> no file.
        """
        # Given: a record with two versions
        self.with_versions("sample.code", 2)
        # When: cut to its last version, above it, and a missing record cut
        with Recorded() as recorded:
            self.backend.cut("graphs", "sample.code", 2)
            self.backend.cut("graphs", "sample.code", 5)
            self.backend.cut("graphs", "missing/x", 1)
        # Then: nothing was written
        self.assertEqual(recorded.calls, [])
        self.assertEqual([e["version"] for e in self.backend.versions("graphs", "sample.code")], [1, 2])
        self.assertEqual(self.backend.ids("graphs"), ["sample.code"])

    @mark.req("REQ-SLY-038")
    def test_a_cut_to_version_0_leaves_no_record(self):
        """Cutting back to version 0 keeps no version: the record is gone, as on the database.

        Example: sample.code at versions 1..2, cut to 0 -> versions [], ids [].
        """
        # Given: a record with two versions
        self.with_versions("sample.code", 2)
        # When: it is cut back to version 0
        self.backend.cut("graphs", "sample.code", 0)
        # Then: it is gone
        self.assertEqual(self.backend.versions("graphs", "sample.code"), [])
        self.assertEqual(self.backend.ids("graphs"), [])

    @mark.req("REQ-SLY-026")
    def test_put_file_writes_a_file_below_the_root_durably(self):
        """put_file writes text to a path relative to the store's root, making its folders, durably.

        Example: put_file("aside/sample.code.json", '{"a": 1}') -> the file holds it; calls == [fsync file, replace, fsync folder].
        """
        # Given: an empty files store with the calls recorded
        with Recorded() as recorded:
            # When: a file is put into a folder that does not exist yet
            self.backend.put_file(os.path.join("aside", "sample.code.json"), json.dumps({"a": 1}))
        # Then: the file holds the text, written durably, and the store's tables see no record
        with open(os.path.join(self.dir, "aside", "sample.code.json"), encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), {"a": 1})
        self.assertEqual(recorded.calls, [("fsync", "file"), ("replace",), ("fsync", "folder")])
        self.assertEqual(sorted(os.listdir(os.path.join(self.dir, "aside"))), ["sample.code.json"])


if __name__ == "__main__":
    unittest.main()
