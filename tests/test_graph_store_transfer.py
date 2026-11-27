"""Moving the whole store, the lag and sync, the one-graph move (G-V4.GRAPHSTORE.TRANSFER T-01, T-03, T-04; REQ-SLY-009, 016 to 031, 038, 039):
unit checks on files only.
Run with: python tests/test_graph_store_transfer.py"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

import graph_store_transfer as transfer          # noqa: E402
import migrate                                    # noqa: E402
import transfer_stores as ts                      # noqa: E402
from markers import mark                          # noqa: E402
from storage import Storage, StorageError         # noqa: E402
from storage_copy import export_library           # noqa: E402
from storage_files import FileBackend             # noqa: E402

# the storage module the helpers write through: plain `storage` alone, or MIA.storage when the suite put the checkout copy first
STORAGE = sys.modules[Storage.__module__]


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


class Sync(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="transfer-unit-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.live = ts.small_store(FileBackend(os.path.join(self.base, "live")))
        self.copy = FileBackend(os.path.join(self.base, "copy"))
        ts.equalize(self.live, self.copy)

    def run_command(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(list(argv))
        return code, out.getvalue().splitlines()

    @mark.req("REQ-SLY-026", "REQ-SLY-038")
    def test_a_graph_only_on_the_copy_is_set_aside_and_leaves_header_first(self):
        """Example: `own` (only on the copy) is in the aside file with its header and step; the copy's first removal is its header."""
        # Given: a graph saved on the copy only
        graph = ts.multi_graph()
        graph["id"] = "own"
        ts.save(self.copy, graph, "copy-writer")
        header, step = self.copy.versions("graphs", "own"), self.copy.versions("graph_nodes", "own/var.in")
        logged = ts.WriteLog(self.copy)
        # When: the copy is synced
        answer = transfer.sync_store(self.live, logged)
        # Then: it is named, its aside file holds all its versions, and it is gone from the copy, header first
        named = answer["set_aside"]["own"]
        self.assertEqual((named["versions"], named["reason"]), ([1], "the graph exists only on the copy"))
        aside = ts.read_json(os.path.join(self.copy.root, named["file"]))
        self.assertEqual((aside["header"], aside["members"]["graph_nodes|own/var.in"]), (header, step))
        self.assertEqual(logged.log[:2], [("file", named["file"]), ("cut", "graphs|own")])
        self.assertNotIn("own", self.copy.ids("graphs"))
        self.assertEqual(ts.graph_group(self.copy), ts.graph_group(self.live))

    @mark.req("REQ-SLY-025")
    def test_a_differing_record_outside_every_graph_is_a_conflict_before_any_write(self):
        """Example: graph_nodes `loose/x` differs and no header names it: StorageError conflict naming it; the copy is unchanged."""
        # Given: a step no graph names, with another history on each side, and a live graph the copy lacks
        for store, author in ((self.live, "ann"), (self.copy, "bob")):
            store.append("graph_nodes", "loose/x", {"id": "loose/x", "version": 1, "author": author, "time": ts.STAMP,
                                                    "doc": {"id": "loose/x", "data": {"type": "data"}}})
        ts.new_multi_version(self.live, "new")
        before = ts.entries(self.copy)
        # When / Then: the sync is refused naming the record, and nothing is written
        with self.assertRaises(StorageError) as refused:
            transfer.sync_store(self.live, self.copy)
        self.assertEqual((refused.exception.code, refused.exception.detail), ("conflict", {"table": "graph_nodes", "id": "loose/x"}))
        self.assertEqual(ts.entries(self.copy), before)

    @mark.req("REQ-SLY-028")
    def test_the_lock_is_refused_while_held_and_free_after(self):
        """Example: a sync inside `with copy_lock(copy)` is refused `locked`; after the block the sync runs."""
        # Given: this process holds the copy's lock
        with transfer.copy_lock(self.copy.root):
            # When / Then: a sync is refused naming the lock
            with self.assertRaises(StorageError) as refused:
                transfer.sync_store(self.live, self.copy)
            self.assertEqual(refused.exception.detail, {"lock": transfer.LOCK})
        # And: once released, a sync runs
        self.assertEqual(transfer.sync_store(self.live, self.copy)["records"], 0)

    @mark.req("REQ-SLY-027", "REQ-SLY-039")
    def test_the_sync_command_names_the_aside_file(self):
        """Example: "synced 2 records, set aside 1 graphs", then "  sample.code: versions [2] set aside in <copy>/aside/... (the live store won)"."""
        # Given: AC-007 on the small store
        ts.ac007(self.live, self.copy, with_store=False)
        # When: the owner runs the sync
        code, lines = self.run_command("sync", "--data", self.live.root, "--copy", self.copy.root)
        # Then: the summary line and one line naming the graph, its version and the aside file in the copy folder
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], "synced 2 records, set aside 1 graphs")
        self.assertRegex(lines[1], r"^  sample\.code: versions \[2\] set aside in %s/aside/sample\.code__\d{8}T\d{6}Z\.json \(the live store won\)$"
                         % self.copy.root)
        self.assertEqual(len(lines), 2)

    @mark.req("REQ-SLY-039")
    def test_lag_and_sync_need_the_copy(self):
        """Example: `sync --data DIR` without --copy is a usage error (exit 2)."""
        # When / Then: argparse stops the command
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as stopped:
            migrate.main(["sync", "--data", self.live.root])
        self.assertEqual(stopped.exception.code, 2)


class OneGraph(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="transfer-unit-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.live = ts.small_store(FileBackend(os.path.join(self.base, "live")))
        self.copy = FileBackend(os.path.join(self.base, "copy"))
        ts.equalize(self.live, self.copy)

    @mark.req("REQ-SLY-031", "REQ-SLY-019")
    def test_the_lacking_versions_arrive_with_the_header_last(self):
        """Example: two new live versions of cp2.multi: the copy gets var.in 2, 3 and headers 5, 6, the headers written last; sample.code untouched."""
        # Given: two new live versions of cp2.multi and a version of sample.code the copy lacks too
        ts.new_multi_version(self.live, "a")
        ts.new_multi_version(self.live, "b")
        ts.new_code_version(self.live, "not moved", "elsewhere")
        target = ts.RecordingBackend(self.copy)
        # When: cp2.multi is moved alone
        answer = transfer.move_graph(self.live, target, ts.MULTI)
        # Then: exactly its lacking versions, headers last, and nothing of sample.code
        self.assertEqual(answer, {"graphs": 1, "records": 4})
        self.assertEqual(target.log, [("graph_nodes", ts.MULTI + "/var.in", 2), ("graph_nodes", ts.MULTI + "/var.in", 3),
                                      ("graphs", ts.MULTI, 5), ("graphs", ts.MULTI, 6)])
        self.assertEqual(len(self.copy.versions("graphs", ts.CODE)), 1)

    @mark.req("REQ-SLY-031")
    def test_a_member_of_the_copys_own_is_a_conflict_too(self):
        """Example: the copy holds its own version 2 of cp2.multi/var.in (header unchanged): conflict naming cp2.multi, nothing written."""
        # Given: a step version only the copy has, and a new live version
        own = dict(self.copy.versions("graph_nodes", ts.MULTI + "/var.in")[0], version=2, author="copy-writer")
        self.copy.append("graph_nodes", ts.MULTI + "/var.in", own)
        ts.new_multi_version(self.live, "a")
        before = ts.entries(self.copy)
        # When / Then: refused, the copy unchanged
        with self.assertRaises(StorageError) as refused:
            transfer.move_graph(self.live, self.copy, ts.MULTI)
        self.assertEqual((refused.exception.code, refused.exception.detail), ("conflict", {"graph": ts.MULTI}))
        self.assertEqual(ts.entries(self.copy), before)

    @mark.req("REQ-SLY-021")
    def test_a_graph_of_an_unknown_kind_is_not_moved_alone_either(self):
        """Example: move_graph of `alien` (kind swarm): move_refused {alien: [unknown_kind swarm]}, the copy unchanged."""
        # Given: alien on the live store
        alien = ts.add_alien(self.live)
        before = ts.entries(self.copy)
        # When / Then: refused by the graph check, nothing written
        with self.assertRaises(StorageError) as refused:
            transfer.move_graph(self.live, self.copy, alien)
        self.assertEqual(refused.exception.detail, {"graphs": {alien: [{"rule": "unknown_kind", "detail": "swarm"}]}})
        self.assertEqual(ts.entries(self.copy), before)

    @mark.req("REQ-SLY-028")
    def test_a_move_into_a_locked_copy_is_refused(self):
        """Example: move_graph while this process holds the copy's lock: StorageError locked."""
        # Given: a new live version and the copy's lock held
        ts.new_multi_version(self.live, "a")
        with transfer.copy_lock(self.copy.root):
            # When / Then: the move is refused naming the lock
            with self.assertRaises(StorageError) as refused:
                transfer.move_graph(self.live, self.copy, ts.MULTI)
        self.assertEqual(refused.exception.detail, {"lock": transfer.LOCK})

    @mark.req("REQ-SLY-030")
    def test_the_side_records_belong_to_the_graph_where_their_tables_exist(self):
        """Example: with graph_changes and arrangements defined: cp2.multi/1 to /4 and arrangements cp2.multi come before the header;
        without them, members and the header only."""
        # Given: the records of cp2.multi as the module lists them, without and with VIEW's side tables
        # both states are patched: since VIEW's merge the tables are defined in the real registry
        undefined = {t: d for t, d in transfer.table_definitions().items() if t not in ("graph_changes", "arrangements")}
        with mock.patch.object(transfer, "table_definitions", lambda: undefined):
            without = transfer._graph_records(self.live, self.copy, ts.MULTI)
        defined = dict(undefined, graph_changes={}, arrangements={})
        with mock.patch.object(transfer, "table_definitions", lambda: defined):
            records = transfer._graph_records(self.live, self.copy, ts.MULTI)
        # Then: no side record without the tables; with them, one change record per version and the arrangement, the header still last
        self.assertFalse([key for key in without if key[0] in ("graph_changes", "arrangements")])
        side = [("graph_changes", "%s/%d" % (ts.MULTI, v)) for v in range(1, 5)] + [("arrangements", ts.MULTI)]
        self.assertEqual(records, without[:-1] + side + [("graphs", ts.MULTI)])


class OlderSets(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="transfer-unit-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.old = FileBackend(os.path.join(self.base, "old"))
        ts.small_store(self.old)
        self.old.append("graph_edges", "e9", {"id": "e9", "version": 1, "author": "owner", "time": ts.STAMP,
                                              "doc": {"id": "e9", "from": "a", "to": "b", "data": {}}})

    @mark.req("REQ-SLY-034")
    def test_an_unscoped_connection_in_a_set_without_a_marker_stops_the_one_graph_move(self):
        """Example: graph_edges/e9 (no graph ID in front), no marker: move_graph of cp2.multi refused older_format naming e9; nothing written."""
        # Given: the set without its marker
        os.remove(os.path.join(self.old.root, transfer.MARKER))
        target = FileBackend(os.path.join(self.base, "target"))
        # When / Then: refused naming the record and the conversion step
        with self.assertRaises(StorageError) as refused:
            transfer.move_graph(self.old, target, ts.MULTI)
        self.assertEqual((refused.exception.rule, refused.exception.detail),
                         ("older_format", {"table": "graph_edges", "id": "e9", "conversion": transfer.CONVERSION_STEP}))
        self.assertEqual(ts.entries(target), {})

    @mark.req("REQ-SLY-034")
    def test_a_set_with_its_marker_and_an_unscoped_record_is_invalid_not_older(self):
        """Example: the same set with its marker: the move is refused by the record check (invalid, unscoped_id), not as older_format."""
        # Given: the set keeps its marker
        target = FileBackend(os.path.join(self.base, "target"))
        # When / Then: refused as a damaged record of today's format, nothing written
        with self.assertRaises(StorageError) as refused:
            transfer.move_store(self.old, target)
        self.assertEqual((refused.exception.rule, refused.exception.detail["id"]), ("unscoped_id", "e9"))
        self.assertEqual(ts.entries(target), {})

    @mark.req("REQ-SLY-035")
    def test_the_commands_name_a_newer_set_in_one_line(self):
        """Example: `lag --data <set of format 2> --copy DIR`: "refused: ... format 2 ... knows format 1 ...", exit 1."""
        # Given: a live set of format 2
        with open(os.path.join(self.old.root, transfer.MARKER), "w", encoding="utf-8") as handle:
            handle.write('{"format": 2}')
        out = io.StringIO()
        # When: the owner asks for the lag
        with contextlib.redirect_stdout(out):
            code = migrate.main(["lag", "--data", self.old.root, "--copy", os.path.join(self.base, "copy")])
        # Then: one line naming both formats, exit 1
        self.assertEqual(code, 1)
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^refused: .*format 2.*format 1")


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


class CopyInUse(unittest.TestCase):
    """the lag in IF-104 v2 terms and AutoSync (T-06)"""

    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="transfer-unit-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.live = ts.small_store(FileBackend(os.path.join(self.base, "live")))
        self.copy = FileBackend(os.path.join(self.base, "copy"))
        ts.equalize(self.live, self.copy)
        self.lines = []

    def auto(self, open_live):
        return transfer.AutoSync(open_live, self.copy, "the folder live", self.lines.append)

    @mark.req("REQ-API-064")
    def test_the_lag_summary_of_a_current_copy_is_empty(self):
        """Example: live and copy equal -> {"graphs": 0, "since": None}."""
        self.assertEqual(transfer.lag_summary(self.live, self.copy), {"graphs": 0, "since": None})

    @mark.req("REQ-API-064")
    def test_since_is_the_oldest_header_version_the_copy_lacks(self):
        """D-540. Example: two new live versions of cp2.multi -> 1 graph, since the time of live version 5."""
        # Given: two newer live versions of cp2.multi, the older one stamped earlier
        with mock.patch.object(STORAGE, "utc_now", side_effect=["2026-11-27T10:00:0%dZ" % n for n in range(9)]):
            ts.new_multi_version(self.live, "a")
        ts.new_multi_version(self.live, "b")
        # When / Then: one graph lags, since the header version 5
        self.assertEqual(transfer.lag_summary(self.live, self.copy),
                         {"graphs": 1, "since": self.live.versions("graphs", ts.MULTI)[4]["time"]})

    @mark.req("REQ-API-064")
    def test_since_is_the_oldest_over_all_lagging_graphs(self):
        """Example: cp2.multi new at 10:00, sample.code new at 11:00 -> 2 graphs since 10:00 (whichever graph is read first)."""
        with mock.patch.object(STORAGE, "utc_now", return_value="2026-11-27T11:00:00Z"):
            ts.new_code_version(self.live, "later", "anna")
        with mock.patch.object(STORAGE, "utc_now", return_value="2026-11-27T10:00:00Z"):
            ts.new_multi_version(self.live, "earlier")
        self.assertEqual(transfer.lag_summary(self.live, self.copy), {"graphs": 2, "since": "2026-11-27T10:00:00Z"})

    @mark.req("REQ-API-064")
    def test_a_differing_copy_lags_since_the_first_live_version_it_does_not_share(self):
        """Example: sample.code version 2 differs on live and copy -> 1 graph, since live's version 2."""
        ts.ac007(self.live, self.copy, with_store=False)
        self.assertEqual(transfer.lag_summary(self.live, self.copy),
                         {"graphs": 1, "since": self.live.versions("graphs", ts.CODE)[1]["time"]})

    @mark.req("REQ-API-062")
    def test_autosync_brings_the_copy_to_the_live_store_and_logs_one_line(self):
        """Example: a new live version -> after run("start") the copy equals live; one line names start and the counts."""
        ts.new_multi_version(self.live, "a")
        report = self.auto(lambda: self.live).run("start")
        self.assertEqual(ts.graph_group(self.copy), ts.graph_group(self.live))
        self.assertEqual(report["graphs"], 1)
        self.assertEqual(len(self.lines), 1)
        self.assertIn("AutoSync at start", self.lines[0])

    @mark.req("REQ-API-063")
    def test_an_unreachable_live_store_is_one_line_and_the_copy_stays(self):
        """Example: opening the live store raises OSError -> no exception, the copy unchanged, one line naming the store and "sync not run"."""
        before = ts.graph_group(self.copy)

        def down():
            raise ConnectionRefusedError("refused")
        report = self.auto(down).run("stop")
        self.assertEqual(ts.graph_group(self.copy), before)
        self.assertEqual(report["unreachable"], "the folder live")
        self.assertEqual(len(self.lines), 1)
        self.assertIn("the folder live", self.lines[0])
        self.assertIn("sync not run", self.lines[0])

    @mark.req("REQ-API-063")
    def test_a_database_driver_error_counts_as_unreachable(self):
        """Example: an error class named OperationalError (psycopg's) -> reported, not raised."""
        OperationalError = type("OperationalError", (Exception,), {})

        def down():
            raise OperationalError("connection failed")
        self.assertIn("unreachable", self.auto(down).run("start"))

    @mark.req("REQ-API-062")
    def test_a_refused_sync_is_a_log_line_not_a_crash(self):
        """Example: the copy's lock is held -> the report names `locked`, one line, nothing raised."""
        ts.new_multi_version(self.live, "a")
        with transfer.copy_lock(self.copy.root):
            report = self.auto(lambda: self.live).run("start")
        self.assertEqual(report["refused"], "locked")
        self.assertEqual(len(self.lines), 1)

    def test_a_bug_is_not_hidden(self):
        """Example: a KeyError while syncing is raised, not logged as unreachable."""
        with mock.patch.object(transfer, "sync_store", side_effect=KeyError("x")):
            with self.assertRaises(KeyError):
                self.auto(lambda: self.live).run("start")


if __name__ == "__main__":
    unittest.main()
