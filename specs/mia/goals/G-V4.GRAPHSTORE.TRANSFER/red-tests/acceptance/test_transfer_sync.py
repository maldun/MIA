"""
Acceptance tests of the same behaviour, the lag, the sync and the side records (groups SB, SY, SR of G-V4.GRAPHSTORE.TRANSFER): TC-SLY-022 to
TC-SLY-028, TC-SLY-030, TC-SLY-031 (REQ-SLY-022 to 028, 030, 031; HR-003, HR-005, HR-006).

Live and copy are fresh stores (core_stores, TR-TRANSFER-002, -007); the copy is always a files folder, the live store is files and, where the
scenario says so, a throw-away PostgreSQL database (skipped visibly where it cannot run). The cases AC-006 and AC-007 come from the helper
transfer_stores. The lock is held by a separate process (TR-TRANSFER-006). TC-SLY-030 is skipped while VIEW's side tables are not defined
(TR-TRANSFER-010). TC-SLY-022 is green on today's code (CORE already behaves alike on both backends): it guards that TRANSFER keeps it so.

Run with: python tests/acceptance/test_transfer_sync.py
"""

import itertools
import os
import stat
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                                                       # noqa: E402
import storage                                                                                 # noqa: E402
from storage import Storage, StorageError, table_definitions                                   # noqa: E402
from graph_model import GraphModel                                                             # noqa: E402
import graph_store_transfer as transfer                                                        # noqa: E402
from core_stores import FailingBackend, Interrupted, fresh_backend, stop_database              # noqa: E402
import transfer_stores as ts                                                                   # noqa: E402

LIVE_KINDS = ("files", "postgres")


def tearDownModule():
    stop_database()


def live_and_copy(test, kind):
    return fresh_backend(kind, test), fresh_backend("files", test)


class SameBehaviour(unittest.TestCase):
    @mark.req("REQ-SLY-022")
    def test_files_and_database_give_the_same_answers(self):
        """TC-SLY-022: one sequence of saves, reads, lists and refusals answers alike on files and on PostgreSQL, under one fixed clock.

        Example: the third save of cp2.multi answers version 3 by author3 at 2026-11-22T10:00:03Z on both; a stale save is `conflict` on both.
        """
        def script(backend):
            # the fixed clock: the same sequence of times for both stores (TR-TRANSFER-005)
            times = ("2026-11-22T10:00:%02dZ" % n for n in itertools.count())
            with mock.patch.object(storage, "utc_now", lambda: next(times)):
                store = Storage(backend)
                out = []
                for k, author in enumerate(ts.AUTHORS, start=1):
                    out.append(tuple(GraphModel(store, author=author).save_graph(ts.multi_graph("tool.v%d" % k))))
                model = GraphModel(store, author="reader")
                out += [model.read_graph(ts.MULTI, 1), model.read_graph(ts.MULTI), model.graph_versions(ts.MULTI),
                        model.step_history(ts.MULTI, "step.write"), store.ids("graphs"), store.ids("graph_nodes")]
                for call in (lambda: store.put("graph_nodes", "cp2.multi/bad", {"id": "cp2.multi/bad", "data": {"type": "transform"}}, "ann"),
                             lambda: store.put("graphs", ts.MULTI, store.get("graphs", ts.MULTI)["doc"], "ann", expected_version=1)):
                    try:
                        call()
                        out.append("accepted")
                    except StorageError as err:
                        out.append((err.code, err.rule, err.detail))
                return out

        # Given: an empty files store and an empty database, both under the same fixed clock
        files, database = fresh_backend("files", self), fresh_backend("postgres", self)
        # When: the same sequence runs on each
        on_files, on_database = script(files), script(database)
        # Then: the two lists of answers are equal
        self.assertEqual(on_files, on_database)
        self.assertEqual(on_files[-2][:2], ("invalid", "schema_break"))
        self.assertEqual(on_files[-1][0], "conflict")

    @mark.req("REQ-SLY-023")
    def test_a_record_file_is_on_disk_before_it_replaces_the_old_one(self):
        """TC-SLY-023: one append flushes the new file, replaces, then flushes the table folder.

        Example: calls == [("fsync", "file"), ("replace",), ("fsync", "folder")].
        """
        # Given: a files store with the flush and replace calls recorded
        backend = fresh_backend("files", self)
        calls, real_fsync, real_replace = [], os.fsync, os.replace

        def fsync(fd):
            calls.append(("fsync", "folder" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file"))
            return real_fsync(fd)

        def replace(a, b):
            calls.append(("replace",))
            return real_replace(a, b)

        # When: one version is appended
        with mock.patch("os.fsync", fsync), mock.patch("os.replace", replace):
            backend.append("memos", "m", {"id": "m", "version": 1, "author": "ann", "time": ts.STAMP, "doc": {"text": "t"}})
        record_calls = [c for c in calls]
        # Then: flush of the new file, replacement, flush of the table folder, in this order (a marker written first adds its own three calls)
        self.assertEqual(record_calls[-3:], [("fsync", "file"), ("replace",), ("fsync", "folder")])


class LagAndSync(unittest.TestCase):
    @mark.req("REQ-SLY-024")
    def test_the_lag_names_what_is_behind_what_differs_and_what_is_refused(self):
        """TC-SLY-024: exactly three graphs are listed: cp2.multi behind, sample.code differs, alien refused.

        Example: {"cp2.multi": {"live": 6, "copy": 4, "state": "behind", "reason": None}, ..., "alien": {..., "state": "refused", "reason": "unknown_kind"}}.
        """
        for kind in LIVE_KINDS:
            with self.subTest(live=kind):
                # Given: AC-006, AC-007 and alien on the live store
                live, copy = live_and_copy(self, kind)
                ts.ac006(live, copy)
                ts.ac007(live, copy, with_store=False)
                ts.add_alien(live)
                # When: the owner asks for the lag
                answer = transfer.lag(live, copy)
                # Then: exactly the three graphs, with their versions, states and reasons
                self.assertEqual(answer, {ts.MULTI: {"live": 6, "copy": 4, "state": "behind", "reason": None},
                                          ts.CODE: {"live": 2, "copy": 2, "state": "differs", "reason": None},
                                          "alien": {"live": 1, "copy": 0, "state": "refused", "reason": "unknown_kind"}})

    @mark.req("REQ-SLY-025")
    def test_the_sync_makes_the_copy_equal_the_live_store(self):
        """TC-SLY-025: after the sync every graph-group record has the live history on the copy; a second sync adds nothing.

        Example: graph_group(copy) == graph_group(live); second answer records == 0; lag == {}.
        """
        for kind in LIVE_KINDS:
            with self.subTest(live=kind):
                # Given: AC-006 and AC-007
                live, copy = live_and_copy(self, kind)
                ts.ac006(live, copy)
                ts.ac007(live, copy, with_store=False)
                # When: the sync runs, and runs again
                first = transfer.sync_store(live, copy)
                second = transfer.sync_store(live, copy)
                # Then: the graph group is equal on both sides
                self.assertGreater(first["records"], 0)
                self.assertEqual(ts.graph_group(copy), ts.graph_group(live))
                # And: the second sync adds 0 records and the lag is empty
                self.assertEqual(second["records"], 0)
                self.assertEqual(transfer.lag(live, copy), {})

    @mark.req("REQ-SLY-026")
    def test_the_copys_own_version_is_set_aside_before_it_goes(self):
        """TC-SLY-026: the aside file holds the copy's version 2 of sample.code and its changed step with author and time; a fault after the
        aside file leaves the copy's version 2 in place and the file complete.

        Example: aside["header"] == [copy's version 2 entry]; aside["members"]["graph_nodes|sample.code/var.in"] == [copy's var.in version 2 entry].
        """
        # Given: AC-007, kept as a starting state to run twice
        live, start = live_and_copy(self, "files")
        ts.ac006(live, start)
        ts.ac007(live, start, with_store=False)
        own_header = start.versions("graphs", ts.CODE)[1]
        own_step = start.versions("graph_nodes", ts.CODE + "/var.in")[1]
        # When: the sync runs without a fault
        copy = ts.clone_folder(start, self)
        answer = transfer.sync_store(live, copy)
        # Then: the aside file holds the copy's version 2 and its changed step, each with author and time
        self.assertIn(ts.CODE, answer["set_aside"])
        aside = ts.read_json(os.path.join(copy.root, answer["set_aside"][ts.CODE]["file"]))
        self.assertEqual(aside["header"], [own_header])
        self.assertEqual(aside["members"]["graph_nodes|%s/var.in" % ts.CODE], [own_step])
        # And: with a fault at the first write after the aside file, the copy still holds version 2 and the aside file is complete
        logged = ts.WriteLog(ts.clone_folder(start, self))
        transfer.sync_store(live, logged)
        after_aside = next(n for n, (kind, name) in enumerate(logged.log, start=1) if kind == "file" and name.startswith(transfer.ASIDE + "/")) + 1
        faulty = FailingBackend(ts.clone_folder(start, self), fail_at=after_aside)
        with self.assertRaises(Interrupted):
            transfer.sync_store(live, faulty)
        self.assertTrue(faulty.fired)
        self.assertEqual(faulty.versions("graphs", ts.CODE)[1], own_header)
        files = os.listdir(os.path.join(faulty.root, transfer.ASIDE))
        self.assertEqual(len(files), 1)
        self.assertEqual(ts.read_json(os.path.join(faulty.root, transfer.ASIDE, files[0]))["header"], [own_header])

    @mark.req("REQ-SLY-027")
    def test_the_sync_says_what_it_set_aside_and_where(self):
        """TC-SLY-027: the answer names sample.code, versions [2] and a file under aside/ relative to the copy, which exists.

        Example: set_aside == {"sample.code": {"versions": [2], "file": "aside/sample.code__20261122T100000Z.json", "reason": "the live store won"}}.
        """
        # Given: AC-007
        live, copy = live_and_copy(self, "files")
        ts.ac006(live, copy)
        ts.ac007(live, copy, with_store=False)
        # When: the sync runs
        answer = transfer.sync_store(live, copy)
        # Then: it names sample.code with versions [2] and a relative aside file that exists
        self.assertEqual(sorted(answer["set_aside"]), [ts.CODE])
        named = answer["set_aside"][ts.CODE]
        self.assertEqual(named["versions"], [2])
        self.assertFalse(os.path.isabs(named["file"]))
        self.assertTrue(named["file"].startswith(transfer.ASIDE + "/" + ts.CODE + "__"))
        self.assertTrue(os.path.isfile(os.path.join(copy.root, named["file"])))

    @mark.req("REQ-SLY-028")
    def test_only_one_sync_at_a_time_and_a_crashed_one_does_not_block(self):
        """TC-SLY-028: while another process holds the lock the sync is refused naming sync.lock; after that process is killed the sync runs.

        Example: StorageError("locked", detail={"lock": "sync.lock"}); copy unchanged; after SIGKILL of the holder the sync answers.
        """
        # Given: AC-006; a helper process holding the copy's lock
        live, copy = live_and_copy(self, "files")
        ts.ac006(live, copy)
        before = ts.entries(copy)
        holder = ts.hold_lock(copy.root)
        self.addCleanup(holder.kill)
        # When: this process syncs
        with self.assertRaises(StorageError) as refused:
            transfer.sync_store(live, copy)
        # Then: refused naming sync.lock, the copy unchanged
        self.assertEqual((refused.exception.code, refused.exception.detail), ("locked", {"lock": transfer.LOCK}))
        self.assertEqual(ts.entries(copy), before)
        # And: after the holder is killed, the sync runs
        ts.kill(holder)
        transfer.sync_store(live, copy)
        self.assertEqual(ts.graph_group(copy), ts.graph_group(live))


class SideRecords(unittest.TestCase):
    @mark.req("REQ-SLY-030")
    def test_recorded_changes_and_the_arrangement_travel_with_their_graph(self):
        """TC-SLY-030: graph_changes and arrangements arrive unchanged with the move, the one-graph move and the sync; a version kept without a
        record of changes still has none.

        Example: graph_changes cp2.multi/2 and cp2.multi/3 and arrangements cp2.multi arrive; cp2.multi/4 does not exist at the destination either.
        """
        # Given: VIEW's side tables (skipped while they are not defined, TR-TRANSFER-010)
        missing = {"graph_changes", "arrangements"} - set(table_definitions())
        if missing:
            self.skipTest("VIEW's side tables are not defined yet: %s (IF-302 v15, A-172)" % ", ".join(sorted(missing)))
        source = ts.small_store(fresh_backend("files", self))
        store = Storage(source)
        for version in (2, 3):                      # version 4 is kept without a record of changes (VIEW REQ-API-040)
            record = "%s/%d" % (ts.MULTI, version)
            store.put("graph_changes", record, {"graph": ts.MULTI, "version": version, "from_version": version - 1, "kind": "editor",
                                                "entries": [{"op": "change", "step": "step.write"}]}, "owner")
        store.put("arrangements", ts.MULTI, {"graph": ts.MULTI, "positions": {"var.in": {"x": 0, "y": 0}}}, "owner")
        side = ts.entries(source, ["graph_changes", "arrangements"])
        # When: the store is moved, the graph is moved alone, and a copy is synced
        moved, alone, synced = fresh_backend("files", self), fresh_backend("files", self), fresh_backend("files", self)
        transfer.move_store(source, moved)
        transfer.move_graph(source, alone, ts.MULTI)
        transfer.sync_store(source, synced)
        # Then: each destination has the same side records, and none for version 4
        for destination in (moved, alone, synced):
            self.assertEqual(ts.entries(destination, ["graph_changes", "arrangements"]), side)
            self.assertEqual(destination.versions("graph_changes", ts.MULTI + "/4"), [])

    @mark.req("REQ-SLY-031")
    def test_one_graph_moves_alone_and_never_over_the_copys_own_version(self):
        """TC-SLY-031: the one-graph move adds exactly the new live version of cp2.multi and its new members; over a copy with its own version 5
        it ends with conflict and changes nothing.

        Example: added entries == the live entries the copy lacked; second move: StorageError("conflict", detail={"graph": "cp2.multi"}).
        """
        # Given: live and copy equal, then a new live version of cp2.multi
        live, copy = live_and_copy(self, "files")
        ts.sample_store(live)
        ts.equalize(live, copy)
        copy_with_own = ts.clone_folder(copy, self)                 # for the And: a copy that gets a version 5 of its own
        ts.new_multi_version(copy_with_own, "own on the copy", author="copy-writer")
        ts.new_multi_version(live, "new")
        before = ts.entries(copy)
        # When: cp2.multi is moved alone
        answer = transfer.move_graph(live, copy, ts.MULTI)
        # Then: exactly the new version and its new members are added; every other record is unchanged
        after = ts.entries(copy)
        added = {(t, i, e["version"]) for t, recs in after.items() for i, es in recs.items() for e in es} - \
                {(t, i, e["version"]) for t, recs in before.items() for i, es in recs.items() for e in es}
        self.assertEqual(added, {("graphs", ts.MULTI, 5), ("graph_nodes", ts.MULTI + "/var.in", 2)})
        self.assertEqual(answer, {"graphs": 1, "records": 2})
        self.assertEqual(ts.graph_group(copy)["graphs"][ts.MULTI], live.versions("graphs", ts.MULTI))
        # And: over a copy that holds a version 5 of its own, the move ends with conflict and the copy is unchanged
        before_own = ts.entries(copy_with_own)
        with self.assertRaises(StorageError) as refused:
            transfer.move_graph(live, copy_with_own, ts.MULTI)
        self.assertEqual((refused.exception.code, refused.exception.detail), ("conflict", {"graph": ts.MULTI}))
        self.assertEqual(ts.entries(copy_with_own), before_own)


if __name__ == "__main__":
    unittest.main()
