"""
Acceptance tests of interrupted moves and syncs (group SY of G-V4.GRAPHSTORE.TRANSFER): TC-SLY-029, TC-SLY-036, TC-SLY-038
(REQ-SLY-029, REQ-SLY-036, REQ-SLY-038; HR-007, NFR-16).

Every write position is tried, one run per position, through FailingBackend on the target side, which counts appends, removals, cut backs and
file writes (TR-TRANSFER-004); the number of positions is the write count of the same run without a stop, and the check asserts that count first,
so a run that writes nothing cannot pass. Each run starts from the same state: the source and the target's start are built once on files and
cloned per run, so the entries (times included) of every run can be compared (TR-TRANSFER-005). The move uses the small store (cp2.multi,
sample.code, context.cp13; owner, D-468). The target is files and, where the scenario says both backends, a throw-away PostgreSQL database filled
from the clone (TR-TRANSFER-002, skipped visibly where it cannot run).

Run with: python tests/acceptance/test_transfer_interrupt.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                                                       # noqa: E402
import graph_store_transfer as transfer                                                        # noqa: E402
from core_stores import FailingBackend, Interrupted, fresh_backend, stop_database              # noqa: E402
import transfer_stores as ts                                                                   # noqa: E402

KINDS = ("files", "postgres")


def tearDownModule():
    stop_database()


def total(entries):
    return sum(len(versions) for table in entries.values() for versions in table.values())


class Runs:
    """The three runs of TC-SLY-029 and 036, each from a fixed start: (source, target start, the call)."""

    def __init__(self, test):
        self.test = test
        self.small = ts.small_store(fresh_backend("files", test))              # the move: the small store into an empty target
        self.empty = fresh_backend("files", test)
        self.live = ts.sample_store(fresh_backend("files", test))              # the one-graph move and the sync: AC-006 plus AC-007
        self.copy = fresh_backend("files", test)
        ts.equalize(self.live, self.copy)
        ts.new_multi_version(self.live, "a")
        ts.new_multi_version(self.live, "b")
        ts.ac007(self.live, self.copy, with_store=False)

    def cases(self, kind):
        """(name, source, target start, the call, the backend of the target): the move and the one-graph move write into a target on `kind`;
        the sync always writes into a files copy (it holds the aside folder and the lock), so for the sync `kind` is the live side"""
        live = self.live
        if kind == "postgres":
            live = fresh_backend("postgres", self.test)
            ts.equalize(self.live, live)
        return (("move", self.small, self.empty, transfer.move_store, kind),
                ("one-graph move", self.live, self.copy, lambda s, t: transfer.move_graph(s, t, ts.MULTI), kind),
                ("sync", live, self.copy, transfer.sync_store, "files"))

    def target(self, start, kind):
        """a target in the state `start` on the backend `kind`: a clone of the folder, or a fresh database filled entry by entry"""
        if kind == "files":
            return ts.clone_folder(start, self.test)
        database = fresh_backend("postgres", self.test)
        ts.equalize(start, database)
        return database


def uninterrupted(runs, source, start, call, kind):
    target = FailingBackend(runs.target(start, kind))
    call(source, target)
    return target.writes, ts.graph_group(target.backend)


class InterruptAcceptance(unittest.TestCase):
    @mark.req("REQ-SLY-029")
    @mark.req("REQ-SLY-036")
    def test_a_stop_at_any_write_leaves_complete_graphs_and_a_rerun_finishes(self):
        """TC-SLY-029 and TC-SLY-036: after a stop at write k no header names a missing member; the rerun equals the run without a stop.

        Example: the move of the small store writes 32 entries: 32 runs, each stopped at its k-th write, each complete, each finished by a rerun.
        """
        runs = Runs(self)
        for side in KINDS:
            for name, source, start, call, kind in runs.cases(side):
                with self.subTest(backend=side, run=name):
                    # Given: the run without a stop, for its number of writes and its result
                    writes, reference = uninterrupted(runs, source, start, call, kind)
                    if name == "move":
                        self.assertEqual(writes, total(ts.entries(source)))      # every entry of the small store is one write
                    else:
                        self.assertGreater(writes, 0)
                    for k in range(1, writes + 1):
                        # When: the run is stopped at write k
                        target = FailingBackend(runs.target(start, kind), fail_at=k)
                        with self.assertRaises(Interrupted):
                            call(source, target)
                        self.assertTrue(target.fired)
                        # Then (TC-SLY-029): no header in the target names a member that is not there
                        self.assertEqual(ts.headers_complete(target.backend), [], "stopped at write %d of %d" % (k, writes))
                        # And (TC-SLY-036): running it again gives the result of the run without a stop
                        call(source, target.backend)
                        self.assertEqual(ts.graph_group(target.backend), reference, "rerun after write %d of %d" % (k, writes))

    @mark.req("REQ-SLY-038")
    def test_a_differing_graph_never_disappears_from_the_copy(self):
        """TC-SLY-038: at every stop of the AC-007 sync, sample.code is on the copy at the shared version 1, the copy's version 2 or the live
        version 2, and every header names only members that are there.

        Example: stopped after the cut of the header: newest header == version 1 entry; stopped after the live version 2: == live's entry.
        """
        for kind in KINDS:
            with self.subTest(live=kind):
                # Given: AC-007, the live store on files or on the database
                live = fresh_backend("files", self)
                start = fresh_backend("files", self)
                ts.sample_store(live)
                ts.equalize(live, start)
                ts.ac007(live, start, with_store=False)
                if kind == "postgres":
                    database = fresh_backend("postgres", self)
                    ts.equalize(live, database)
                    live = database
                shared, own, won = start.versions("graphs", ts.CODE)[0], start.versions("graphs", ts.CODE)[1], live.versions("graphs", ts.CODE)[1]
                counted = FailingBackend(ts.clone_folder(start, self))
                transfer.sync_store(live, counted)
                self.assertGreater(counted.writes, 0)
                for k in range(1, counted.writes + 1):
                    # When: the sync is stopped at write k
                    copy = FailingBackend(ts.clone_folder(start, self), fail_at=k)
                    with self.assertRaises(Interrupted):
                        transfer.sync_store(live, copy)
                    # Then: sample.code is listed, at one of the three complete versions
                    self.assertIn(ts.CODE, copy.ids("graphs"), "stopped at write %d" % k)
                    self.assertIn(copy.versions("graphs", ts.CODE)[-1], (shared, own, won), "stopped at write %d" % k)
                    # And: every header names only members that are there
                    self.assertEqual(ts.headers_complete(copy.backend), [], "stopped at write %d" % k)


if __name__ == "__main__":
    unittest.main()
