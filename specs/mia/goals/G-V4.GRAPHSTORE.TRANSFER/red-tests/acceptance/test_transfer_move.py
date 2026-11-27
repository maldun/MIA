"""
Acceptance tests of moving the whole store (groups MV of G-V4.GRAPHSTORE.TRANSFER): TC-SLY-016 to TC-SLY-021 and TC-SLY-009
(REQ-SLY-016 to REQ-SLY-021, the changes of REQ-SLY-009 and REQ-GA-008; HR-001, HR-004).

The source is the sample store (helper transfer_stores, TR-TRANSFER-003) on a fresh files folder; the database side is a fresh database in a
throw-away postgres:16 container (core_stores, TR-TRANSFER-002, -007), skipped visibly where it cannot run. Expected values are exact: histories
entry by entry, author and time included, since a move copies them (TR-TRANSFER-001, -005). TC-SLY-017, 018 and 019 are red on today's code for
the two defects they exist for (survey: each record checked alone, headers written before context steps; TR-TRANSFER-008).

Run with: python tests/acceptance/test_transfer_move.py
"""

import os
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
from storage import Storage, StorageError                                                      # noqa: E402
from storage_copy import seed_library, export_library                                          # noqa: E402
import graph_store_transfer as transfer                                                        # noqa: E402
from core_stores import FailingBackend, fresh_backend, stop_database                           # noqa: E402
import transfer_stores as ts                                                                   # noqa: E402


def tearDownModule():
    stop_database()


def total(entries):
    return sum(len(versions) for table in entries.values() for versions in table.values())


class MoveAcceptance(unittest.TestCase):
    def setUp(self):
        self.source = ts.sample_store(fresh_backend("files", self))

    @mark.req("REQ-SLY-016")
    def test_the_whole_store_goes_to_the_database_and_back_unchanged(self):
        """TC-SLY-016: files -> database -> files keeps every record of every table entry by entry, author and time included.

        Example: cp2.multi arrives with its four versions by owner, author2, author3, author4, each with the time it was saved.
        """
        # Given: the sample store on files, an empty database and an empty second folder
        database = fresh_backend("postgres", self)
        back = fresh_backend("files", self)
        # When: the whole store is moved to the database, and from there to the second folder
        transfer.move_store(self.source, database)
        transfer.move_store(database, back)
        # Then: every record of every table is the same, entry by entry, in the database and in the second folder
        self.assertEqual(ts.entries(database), ts.entries(self.source))
        self.assertEqual(ts.entries(back), ts.entries(self.source))
        # And: cp2.multi has its four versions by its four authors in order
        self.assertEqual([e["author"] for e in back.versions("graphs", ts.MULTI)], list(ts.AUTHORS))

    @mark.req("REQ-SLY-017")
    def test_a_damaged_graph_is_found_before_anything_is_written(self):
        """TC-SLY-017: a header naming a step version the source lacks is found before the first write; a graph that only breaks a rule moves.

        Example: cp2.multi's newest header names cp2.multi/step.write version 5 of 4: refused, 0 writes; `cyc` (d1 -> t1 -> d1) is moved.
        """
        # Given: the sample store with a damaged header of cp2.multi; a target that counts its writes
        ts.damage_header(self.source)
        target = FailingBackend(fresh_backend("files", self))
        # When: the store is moved
        with self.assertRaises(StorageError) as refused:
            transfer.move_store(self.source, target)
        # Then: it is refused with 0 writes counted
        self.assertEqual((refused.exception.code, refused.exception.rule), ("invalid", "move_refused"))
        self.assertEqual(target.writes, 0)
        # And: a store whose only graph has a cycle is moved: records are checked, not the eight rules
        cyclic = fresh_backend("files", self)
        ts.add_cycle(cyclic)
        cycle_target = fresh_backend("files", self)
        transfer.move_store(cyclic, cycle_target)
        self.assertEqual(ts.entries(cycle_target), ts.entries(cyclic))

    @mark.req("REQ-SLY-018")
    def test_one_damaged_graph_stops_the_whole_move_and_is_named(self):
        """TC-SLY-018: the refusal names every damaged graph with its missing part, and the target keeps exactly what it held.

        Example: detail graphs == {cp2.multi: [unknown_member cp2.multi/step.write], sample.broken: [unknown_endpoint sample.broken/var.gone]}.
        """
        # Given: the damaged store of TC-SLY-017 plus sample.broken; a target database holding one unrelated graph
        member, _missing = ts.damage_header(self.source)
        broken, _edge = ts.add_broken(self.source)
        target = fresh_backend("postgres", self)
        ts.add_cycle(target, graph_id="unrelated")
        before = ts.entries(target)
        # When: the store is moved
        with self.assertRaises(StorageError) as refused:
            transfer.move_store(self.source, target)
        # Then: refused with move_refused, naming both graphs with their missing parts
        err = refused.exception
        self.assertEqual((err.code, err.rule), ("invalid", "move_refused"))
        self.assertEqual(err.detail, {"graphs": {ts.MULTI: [{"rule": "unknown_member", "detail": member}],
                                                 broken: [{"rule": "unknown_endpoint", "detail": broken + "/var.gone"}]}})
        # And: the target holds exactly its one graph, as before
        self.assertEqual(ts.entries(target), before)

    @mark.req("REQ-SLY-019")
    def test_steps_and_connections_are_written_before_the_header_that_names_them(self):
        """TC-SLY-019: in the write log of a move every header version comes after each member version it names.

        Example: context.cp13's header version 1 is logged after context_nodes context.cp13/... version 1 (today it comes before: defect 1).
        """
        # Given: the sample store (workflow graphs and the context graph); a target that logs its writes
        target = ts.RecordingBackend(fresh_backend("files", self))
        # When: the store is moved
        transfer.move_store(self.source, target)
        # Then: the move wrote every entry, and no header version names a member version written later
        self.assertEqual(len(target.log), total(ts.entries(self.source)))
        self.assertEqual(ts.members_before_headers(target.log, target), [])

    @mark.req("REQ-SLY-020")
    def test_moving_again_changes_nothing(self):
        """TC-SLY-020: the second move reports 0 copied, 0 versions added and as many skipped as the first copied.

        Example: the first move copies N records (N > 0); the second answers {"copied": 0, "skipped": N, "added_versions": 0}.
        """
        # Given: the source and a target after one move
        target = fresh_backend("files", self)
        first = transfer.move_store(self.source, target)
        after_first = ts.entries(target)
        # When: the same move is run again
        second = transfer.move_store(self.source, target)
        # Then: nothing is copied or added, everything is skipped
        self.assertGreater(first["copied"], 0)
        self.assertEqual(second, {"copied": 0, "skipped": first["copied"], "added_versions": 0})
        # And: the target is unchanged
        self.assertEqual(ts.entries(target), after_first)

    @mark.req("REQ-SLY-021")
    def test_a_graph_of_an_unknown_kind_stops_a_move_and_a_sync(self):
        """TC-SLY-021: a graph of kind `swarm` refuses the whole move and the whole sync, named with unknown_kind.

        Example: detail graphs == {"alien": [{"rule": "unknown_kind", "detail": "swarm"}]}; target and copy unchanged.
        """
        # Given: the sample store plus `alien` of kind swarm, written straight through the backend
        alien = ts.add_alien(self.source)
        target = fresh_backend("files", self)
        copy = fresh_backend("files", self)
        before_target, before_copy = ts.entries(target), ts.entries(copy)
        expected = {"graphs": {alien: [{"rule": "unknown_kind", "detail": "swarm"}]}}
        # When: the store is moved, and synced as the live store to a copy
        with self.assertRaises(StorageError) as moved:
            transfer.move_store(self.source, target)
        with self.assertRaises(StorageError) as synced:
            transfer.sync_store(self.source, copy)
        # Then: both are refused naming alien and unknown_kind
        self.assertEqual((moved.exception.rule, moved.exception.detail), ("move_refused", expected))
        self.assertEqual((synced.exception.rule, synced.exception.detail), ("move_refused", expected))
        # And: the target and the copy are unchanged
        self.assertEqual((ts.entries(target), ts.entries(copy)), (before_target, before_copy))

    @mark.req("REQ-SLY-009")
    @mark.req("REQ-GA-008")
    def test_export_and_seed_carry_the_stored_graphs(self):
        """TC-SLY-009 (graph group): export then seed gives every library entry and every graph-group record, members before headers.

        Example: after seeding, graph_group(seeded) == graph_group(source) and the seed's write log has no header before its members.
        """
        # Given: the sample store
        folder = tempfile.mkdtemp(prefix="transfer-export-")
        self.addCleanup(__import__("shutil").rmtree, folder, True)
        seeded = ts.RecordingBackend(fresh_backend("files", self))
        # When: the library is exported to a new folder and seeded into an empty store that logs its writes
        export_library(Storage(self.source), folder)
        seed_library(Storage(seeded), folder)
        # Then: every library entry and every graph-group record arrives identical
        self.assertEqual(ts.graph_group(seeded), ts.graph_group(self.source))
        self.assertEqual(ts.entries(seeded, ["workflows", "context_graphs"]), ts.entries(self.source, ["workflows", "context_graphs"]))
        # And: members come before headers in the seed's write log
        self.assertEqual(ts.members_before_headers(seeded.log, seeded), [])


if __name__ == "__main__":
    unittest.main()
