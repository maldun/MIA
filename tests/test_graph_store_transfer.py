"""Moving the whole store (G-V4.GRAPHSTORE.TRANSFER T-01, REQ-SLY-016 to 021, REQ-SLY-009): unit checks on files only.
Run with: python tests/test_graph_store_transfer.py"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

import graph_store_transfer as transfer          # noqa: E402
import migrate                                    # noqa: E402
import transfer_stores as ts                      # noqa: E402
from markers import mark                          # noqa: E402
from storage import Storage, StorageError         # noqa: E402
from storage_copy import export_library           # noqa: E402
from storage_files import FileBackend             # noqa: E402


class Move(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="transfer-unit-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.folder = lambda name: FileBackend(os.path.join(self.base, name))
        self.source = ts.small_store(self.folder("source"))

    def refusal(self, target):
        with self.assertRaises(StorageError) as refused:
            transfer.move_store(self.source, target)
        self.assertEqual((refused.exception.code, refused.exception.rule), ("invalid", "move_refused"))
        return refused.exception.detail["graphs"]

    @mark.req("REQ-SLY-016", "REQ-SLY-019")
    def test_every_table_is_moved_with_members_before_headers(self):
        """A memory record goes along, and no header is written before a member it names.
        Example: the small store plus memory `m` arrives entry by entry; the write log has no late member."""
        # Given: the small store plus a record outside the graph group
        Storage(self.source).put("memory", "m", {"text": "t", "source": "chat"}, "anna")
        target = ts.RecordingBackend(self.folder("target"))
        # When: the store is moved
        counts = transfer.move_store(self.source, target)
        # Then: every record arrived, in a good order
        self.assertEqual(ts.entries(target), ts.entries(self.source))
        self.assertEqual(ts.members_before_headers(target.log, target), [])
        self.assertEqual(counts["copied"], sum(len(t) for t in ts.entries(self.source).values()))

    @mark.req("REQ-SLY-018")
    def test_a_missing_member_version_is_named_and_nothing_is_written(self):
        """Example: cp2.multi's newest header names step.write version 5 of 4: {cp2.multi: [unknown_member cp2.multi/step.write]}."""
        # Given: a damaged header
        member, _version = ts.damage_header(self.source)
        target = self.folder("target")
        # When / Then: refused naming the member, and the target stays empty
        self.assertEqual(self.refusal(target), {ts.MULTI: [{"rule": "unknown_member", "detail": member}]})
        self.assertEqual(ts.entries(target), {})

    @mark.req("REQ-SLY-018")
    def test_a_connection_to_a_missing_step_is_named(self):
        """Example: sample.broken's e2 leads to var.gone: {sample.broken: [unknown_endpoint sample.broken/var.gone]}."""
        # Given: a graph with a connection to a step that is not stored
        broken, _edge = ts.add_broken(self.source)
        # When / Then: refused naming the missing end
        self.assertEqual(self.refusal(self.folder("target")), {broken: [{"rule": "unknown_endpoint", "detail": broken + "/var.gone"}]})

    @mark.req("REQ-SLY-021")
    def test_a_graph_of_an_unknown_kind_is_named_with_its_kind(self):
        """Example: alien of kind swarm: {alien: [unknown_kind swarm]}."""
        # Given: a graph of a kind the registry does not list
        alien = ts.add_alien(self.source)
        # When / Then: refused naming the kind
        self.assertEqual(self.refusal(self.folder("target")), {alien: [{"rule": "unknown_kind", "detail": "swarm"}]})

    @mark.req("REQ-SLY-017")
    def test_a_graph_that_only_breaks_a_rule_is_moved(self):
        """Example: `cyc` (d1 -> t1 -> d1) moves: the move checks records, not the eight rules."""
        # Given: a store with a cycle
        cyclic = self.folder("cyclic")
        ts.add_cycle(cyclic)
        target = self.folder("target")
        # When: it is moved
        transfer.move_store(cyclic, target)
        # Then: it arrived
        self.assertEqual(ts.entries(target), ts.entries(cyclic))

    @mark.req("REQ-SLY-020")
    def test_a_second_move_skips_everything(self):
        """Example: {"copied": 0, "skipped": N, "added_versions": 0} after a first move that copied N."""
        # Given: a target after one move
        target = self.folder("target")
        first = transfer.move_store(self.source, target)
        # When: the move runs again
        second = transfer.move_store(self.source, target)
        # Then: everything is skipped
        self.assertEqual(second, {"copied": 0, "skipped": first["copied"], "added_versions": 0})


class Commands(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="transfer-unit-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.data, self.db = os.path.join(self.base, "data"), os.path.join(self.base, "db")
        ts.small_store(FileBackend(self.data))

    def run_command(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(list(argv), open_db=lambda url: FileBackend(self.db))
        return code, out.getvalue()

    @mark.req("REQ-SLY-018")
    def test_files_to_db_with_a_damaged_header_names_the_graph_and_writes_nothing(self):
        """Example: "refused: cp2.multi: unknown_member cp2.multi/step.write (nothing was written)", exit 1, no database folder."""
        # Given: a damaged header in the data folder
        member, _version = ts.damage_header(FileBackend(self.data))
        # When: the folder is moved to the database
        code, text = self.run_command("files-to-db", "--data", self.data, "--database-url", "x")
        # Then: one line naming the graph and its missing member, exit 1, nothing written
        self.assertEqual(code, 1)
        self.assertEqual(text, "refused: %s: unknown_member %s (nothing was written)\n" % (ts.MULTI, member))
        self.assertEqual(ts.entries(FileBackend(self.db)), {})

    @mark.req("REQ-SLY-016")
    def test_files_to_db_moves_the_graph_group(self):
        """Example: files-to-db then db-to-files gives the small store back entry by entry."""
        # Given / When: the data folder moved to the database and back into an empty folder
        self.assertEqual(self.run_command("files-to-db", "--data", self.data, "--database-url", "x")[0], 0)
        back = os.path.join(self.base, "back")
        self.assertEqual(self.run_command("db-to-files", "--data", back, "--database-url", "x")[0], 0)
        # Then: the same entries
        self.assertEqual(ts.entries(FileBackend(back)), ts.entries(FileBackend(self.data)))


class Export(unittest.TestCase):
    @mark.req("REQ-SLY-009")
    def test_the_export_holds_the_graph_group(self):
        """Example: the export folder of the small store holds cp2.multi with its four versions and its steps."""
        # Given: the small store
        base = tempfile.mkdtemp(prefix="transfer-unit-")
        self.addCleanup(shutil.rmtree, base, True)
        source = ts.small_store(FileBackend(os.path.join(base, "source")))
        # When: the library is exported
        export_library(Storage(source), os.path.join(base, "export"))
        # Then: the graph group is in the folder
        self.assertEqual(ts.graph_group(FileBackend(os.path.join(base, "export"))), ts.graph_group(source))


if __name__ == "__main__":
    unittest.main()
