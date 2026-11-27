"""
Acceptance tests of portable sets of files and of the lag and sync commands (groups PT and AS of G-V4.GRAPHSTORE.TRANSFER): TC-SLY-032 to
TC-SLY-035, TC-SLY-037, TC-SLY-039 (REQ-SLY-032 to 035, 037, 039; HR-006, HR-008).

Every set is a fresh folder (TR-TRANSFER-007). A set "without a marker" is made as a set from before this version: by today's save path with its
marker deleted afterwards (TC-SLY-033), or with an old-style record file written straight into the folder (TC-SLY-034), since every write now adds
the marker (owner's delegation, D-468). The path search looks for a random 16-character token in the source folder's name and for the home folder,
as bytes, in every file (TR-TRANSFER-011). The lock is held by a separate process (TR-TRANSFER-006).

Run with: python tests/acceptance/test_transfer_sets.py
"""

import contextlib
import io
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                                                       # noqa: E402
from storage import StorageError                                                               # noqa: E402
from storage_files import FileBackend                                                          # noqa: E402
import graph_store_transfer as transfer                                                        # noqa: E402
import migrate                                                                                 # noqa: E402
from core_stores import fresh_backend, fixture_graph                                           # noqa: E402
import transfer_stores as ts                                                                   # noqa: E402


def folder_bytes(root):
    """{relative path: bytes} of every file under root"""
    out = {}
    for base, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(base, name)
            with open(path, "rb") as f:
                out[os.path.relpath(path, root)] = f.read()
    return out


def marker(root):
    path = os.path.join(root, transfer.MARKER)
    return ts.read_json(path) if os.path.exists(path) else None


class Sets(unittest.TestCase):
    def folder(self, prefix="transfer-set-"):
        root = tempfile.mkdtemp(prefix=prefix)
        self.addCleanup(shutil.rmtree, root, True)
        return root

    @mark.req("REQ-SLY-032")
    def test_a_set_of_files_gets_its_format_marker(self):
        """TC-SLY-032: a move into an empty folder and a plain save into an empty folder each leave mia-store.json = {"format": 1}.

        Example: marker(moved) == {"format": 1}; marker(saved) == {"format": 1}.
        """
        # Given: two empty folders
        moved, saved = FileBackend(self.folder()), FileBackend(self.folder())
        # When: the small store is moved into the first, and one graph is saved into the second
        transfer.move_store(ts.small_store(fresh_backend("files", self)), moved)
        ts.save(saved, fixture_graph(ts.CODE), "owner")
        # Then: each folder holds the marker with format 1
        self.assertEqual(marker(moved.root), {"format": 1})
        self.assertEqual(marker(saved.root), {"format": 1})

    @mark.req("REQ-SLY-033")
    def test_todays_sets_without_a_marker_still_work(self):
        """TC-SLY-033: a set made by today's save path, its marker deleted, moves and syncs like a format-1 set.

        Example: entries(moved) == entries(old set); after a sync with the old set as the live store, graph_group(copy) == graph_group(old set).
        """
        # Given: a set written by today's save path (scoped graphs, and `workflows` documents), without a marker
        old = ts.small_store(FileBackend(self.folder()))
        old.append("workflows", "lookup", {"id": "lookup", "version": 1, "author": "owner", "time": ts.STAMP,
                                           "doc": {"nodes": [], "edges": []}})
        with contextlib.suppress(FileNotFoundError):
            os.remove(os.path.join(old.root, transfer.MARKER))
        # When: it is moved, and synced as the live store
        moved, copy = FileBackend(self.folder()), FileBackend(self.folder())
        transfer.move_store(old, moved)
        transfer.sync_store(old, copy)
        # Then: it behaves as a set with format 1
        self.assertEqual(ts.entries(moved), ts.entries(old))
        self.assertEqual(ts.graph_group(copy), ts.graph_group(old))

    @mark.req("REQ-SLY-034")
    def test_an_older_set_with_plain_step_ids_is_refused_by_name(self):
        """TC-SLY-034: a set without a marker holding graph_nodes/n1 (no graph ID in front) is refused for a move and a sync, naming the table, the
        record and MIGRATION's conversion step; nothing is written.

        Example: StorageError("invalid", rule="older_format", detail={"table": "graph_nodes", "id": "n1", "conversion": CONVERSION_STEP}).
        """
        # Given: a set without a marker, whose step record n1 is written straight into the folder as a set before A-167 held it
        root = self.folder()
        os.makedirs(os.path.join(root, "graph_nodes"))
        with open(os.path.join(root, "graph_nodes", "n1.json"), "w", encoding="utf-8") as f:
            json.dump([{"id": "n1", "version": 1, "author": "owner", "time": ts.STAMP, "doc": {"id": "n1", "data": {"type": "data"}}}], f)
        old = FileBackend(root)
        target, copy = FileBackend(self.folder()), FileBackend(self.folder())
        expected = {"table": "graph_nodes", "id": "n1", "conversion": transfer.CONVERSION_STEP}
        # When: it is moved, and synced
        with self.assertRaises(StorageError) as moved:
            transfer.move_store(old, target)
        with self.assertRaises(StorageError) as synced:
            transfer.sync_store(old, copy)
        # Then: both are refused naming graph_nodes, n1 and the conversion step of MIGRATION
        for refused in (moved, synced):
            self.assertEqual((refused.exception.code, refused.exception.rule, refused.exception.detail), ("invalid", "older_format", expected))
        self.assertIn("MIGRATION", transfer.CONVERSION_STEP)
        # And: nothing is written
        self.assertEqual((ts.entries(target), ts.entries(copy)), ({}, {}))

    @mark.req("REQ-SLY-035")
    def test_a_set_from_a_newer_mia_is_not_opened(self):
        """TC-SLY-035: a set whose marker says format 2 is refused naming 2 and 1, and no file of it changes.

        Example: FileBackend(root) raises StorageError("format", detail={"found": 2, "known": 1}).
        """
        # Given: a set whose marker says {"format": 2}, with one record
        root = self.folder()
        ts.small_store(FileBackend(root))
        with open(os.path.join(root, transfer.MARKER), "w", encoding="utf-8") as f:
            json.dump({"format": 2}, f)
        before = folder_bytes(root)
        # When: the Storage layer opens it
        with self.assertRaises(StorageError) as refused:
            FileBackend(root)
        # Then: refused naming format 2 and format 1
        self.assertEqual((refused.exception.code, refused.exception.detail), ("format", {"found": 2, "known": transfer.FORMAT}))
        # And: every file is byte for byte as before
        self.assertEqual(folder_bytes(root), before)

    @mark.req("REQ-SLY-037")
    def test_a_set_holds_no_path_of_the_machine(self):
        """TC-SLY-037: after a move, a sync with an aside file and a copy of the folder elsewhere, no file holds the source folder's path
        (a random token in its name) or the home folder, and the copied folder lists the same graphs and versions as the folder it was copied from.

        Example: token "3f9c0b5e7a1d2c4b" appears in no file of the three folders; graph_group(third) == graph_group(copy).
        """
        # Given: the sample store under a folder with a random token in its name
        token = secrets.token_hex(8)
        source = FileBackend(os.path.join(self.folder(), token, "store"))
        ts.sample_store(source)
        # When: it is moved to a second folder, which is synced as a copy with one aside file, and copied to a third place
        copy = FileBackend(self.folder())
        transfer.move_store(source, copy)
        self.assertEqual(ts.entries(copy), ts.entries(source))
        live = FileBackend(self.folder())
        ts.equalize(copy, live)
        ts.ac007(live, copy, with_store=False)
        answer = transfer.sync_store(live, copy)
        self.assertEqual(sorted(answer["set_aside"]), [ts.CODE])
        third = os.path.join(self.folder(), "third")
        shutil.copytree(copy.root, third)
        # Then: no file of the three folders holds the token or the home folder
        needles = (token.encode(), os.path.expanduser("~").encode())
        for root in (source.root, copy.root, third):
            for path, data in folder_bytes(root).items():
                for needle in needles:
                    self.assertNotIn(needle, data, "%s in %s" % (needle, path))
        # And: the copied folder lists the same graphs and versions as the folder it was copied from
        self.assertEqual(ts.graph_group(FileBackend(third)), ts.graph_group(copy))


class Commands(unittest.TestCase):
    def run_command(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(list(argv))
        return code, out.getvalue().strip().splitlines()

    @mark.req("REQ-SLY-039")
    def test_lag_and_sync_are_commands(self):
        """TC-SLY-039: `lag --copy` prints the line of cp2.multi and exits 0; `sync --copy` reports the records added and exits 0; a sync while
        another process holds the lock is one line naming sync.lock and exits 1.

        Example: lag line split == ["cp2.multi", "live", "6", "copy", "4", "behind"]; sync line "synced 12 records, set aside 0 graphs".
        """
        # Given: AC-006 on files
        live, copy = fresh_backend("files", self), fresh_backend("files", self)
        ts.ac006(live, copy)
        # When: the owner runs lag, then sync
        lag_code, lag_lines = self.run_command("lag", "--data", live.root, "--copy", copy.root)
        sync_code, sync_lines = self.run_command("sync", "--data", live.root, "--copy", copy.root)
        # Then: lag prints the line of cp2.multi and exits 0
        self.assertEqual(lag_code, 0)
        self.assertEqual([line.split() for line in lag_lines], [[ts.MULTI, "live", "6", "copy", "4", "behind"]])
        # And: sync reports the records added and exits 0, and the copy equals the live store
        self.assertEqual(sync_code, 0)
        self.assertEqual(len(sync_lines), 1)
        found = re.fullmatch(r"synced (\d+) records, set aside 0 graphs", sync_lines[0])
        self.assertIsNotNone(found, sync_lines)
        self.assertGreater(int(found.group(1)), 0)
        self.assertEqual(ts.graph_group(copy), ts.graph_group(live))
        # And: a sync while another process holds the lock is one line naming sync.lock, exit code 1
        holder = ts.hold_lock(copy.root)
        self.addCleanup(holder.kill)
        locked_code, locked_lines = self.run_command("sync", "--data", live.root, "--copy", copy.root)
        self.assertEqual(locked_code, 1)
        self.assertEqual(len(locked_lines), 1)
        self.assertIn(transfer.LOCK, locked_lines[0])


if __name__ == "__main__":
    unittest.main()
