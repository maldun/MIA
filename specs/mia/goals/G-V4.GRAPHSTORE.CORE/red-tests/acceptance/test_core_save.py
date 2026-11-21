"""
Acceptance tests of saving a graph (group SV of G-V4.GRAPHSTORE.CORE): TC-WFM-164 to TC-WFM-169 (REQ-WFM-146 to REQ-WFM-151).

The graphs are the fixtures of tests/fixtures/graphs/ (TR-CORE-004): `memory.write@5` (five steps, four connections: ten writes for a first save) and
`context.cp13` (three steps, two connections: six writes). Every check gets a fresh store (TR-CORE-007, helper core_stores). TC-WFM-165 and TC-WFM-169
interrupt each save at every write position k (TR-CORE-001), show by the counted writes that the injector fired (TR-CORE-002) and run on the files
store and on PostgreSQL 16 (TR-CORE-003; a missing podman, image or psycopg 3 shows as a skip). The other checks run on the files store.
Expected values are written by hand (TR-CORE-005).

Run with: python tests/acceptance/test_core_save.py
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
from storage import Storage                                                                     # noqa: E402
from graph_model import GraphModel                                                              # noqa: E402
import core_stores                                                                              # noqa: E402
from core_stores import KINDS, FailingBackend, Interrupted, fixture_graph, fresh_backend, version_counts  # noqa: E402

WHO = "ann"
WORKFLOW = "memory.write@5"      # 5 steps, 4 connections
CONTEXT = "context.cp13"         # 3 steps, 2 connections


def tearDownModule():
    core_stores.stop_database()


def model(backend):
    return GraphModel(Storage(backend), author=WHO)


def node_of(graph, local_id):
    return next(n for n in graph["nodes"] if n["id"] == local_id)


def edge_of(graph, local_id):
    return next(e for e in graph["edges"] if e["id"] == local_id)


def workflow_changed():
    """memory.write@5 with one step and one connection changed: a changed save of three writes (the step, the connection, the header)."""
    g = fixture_graph(WORKFLOW)
    node_of(g, "step.write")["data"]["toolbox_id"] = "view.memory_write_v2"
    edge_of(g, "step.write>var.answer")["data"]["as"] = "result"
    return g


def context_changed():
    """context.cp13 with one step changed: a changed save of two writes (the step, the header)."""
    g = fixture_graph(CONTEXT)
    node_of(g, "note")["data"]["text"] = "ctx, second wording"
    return g


def expected_counts(graph, header_versions, changed=()):
    """The hand-worked version counts of the stores after the saves of one graph: every member 1 version, the changed ones 2, the header as given."""
    gid = graph["id"]
    node_table, edge_table = ("context_nodes", "context_edges") if graph.get("kind") == "context" else ("graph_nodes", "graph_edges")
    counts = {t: {} for t in ("graph_nodes", "graph_edges", "context_nodes", "context_edges", "graphs")}
    counts[node_table] = {"%s/%s" % (gid, n["id"]): 2 if n["id"] in changed else 1 for n in graph["nodes"]}
    counts[edge_table] = {"%s/%s" % (gid, e["id"]): 2 if e["id"] in changed else 1 for e in graph["edges"]}
    counts["graphs"] = {gid: header_versions}
    return counts


# The four saves of TC-WFM-165 and TC-WFM-169: (name, graph stored before or None, graph saved, writes of that save, local IDs it changes).
# The writes are the known answer of TR-CORE-002: a first save writes every member and the header (5 + 4 + 1 = 10, 3 + 2 + 1 = 6), a changed save
# only the changed members and the header (2 + 1 = 3, 1 + 1 = 2).
def interrupted_saves():
    return [("workflow first save", None, fixture_graph(WORKFLOW), 10, ()),
            ("workflow changed save", fixture_graph(WORKFLOW), workflow_changed(), 3, ("step.write", "step.write>var.answer")),
            ("context first save", None, fixture_graph(CONTEXT), 6, ()),
            ("context changed save", fixture_graph(CONTEXT), context_changed(), 2, ("note",))]


class SaveTestCase(unittest.TestCase):
    maxDiff = None

    def store_with(self, kind, before):
        """A fresh backend that holds `before` as version 1 (or nothing)."""
        backend = fresh_backend(kind, self)
        if before is not None:
            self.assertEqual(model(backend).save_graph(before).version, 1)
        return backend

    def run_interrupted(self, backend, graph, k, writes):
        """The save of `graph` interrupted at write k; k = writes + 1 is the interruption after the last write (the header), where the save is complete."""
        failing = FailingBackend(backend, fail_at=k)
        if k <= writes:
            with self.assertRaises(Interrupted):
                model(failing).save_graph(graph)
            # TR-CORE-002: the injector fired at k, after exactly k - 1 writes
            self.assertEqual((failing.fired, failing.writes), (True, k - 1))
        else:
            self.assertTrue(model(failing).save_graph(graph).saved)
            self.assertEqual((failing.fired, failing.writes), (False, writes))

    def counted_save(self, backend, graph):
        """(result, number of writes) of one save."""
        counter = FailingBackend(backend)
        result = model(counter).save_graph(graph)
        return result, counter.writes

    def probe(self, kind):
        """Makes the PostgreSQL half skip once, before its many write positions (TR-CORE-003)."""
        fresh_backend(kind, self)


class SaveGraph(SaveTestCase):

    @mark.req("REQ-WFM-146")
    def test_the_whole_graph_is_checked_before_the_first_write(self):
        """TC-WFM-164 The whole graph is checked before the first write.
        Example: memory.write@5 stored; a copy whose last connection leads to `step.missing` is refused naming that connection, and no table changed.
        The broken parts sit at the end of each graph, so a check made while writing would have written the steps before it."""
        # Given: a stored graph, and three new graphs
        backend = self.store_with("files", fixture_graph(WORKFLOW))
        storage = Storage(backend)
        missing = fixture_graph(WORKFLOW)
        missing["id"] = "tc164.missing"
        missing["edges"][-1]["to"] = "step.missing"                # the last connection: descriptor.model>step.write
        cycle = fixture_graph(WORKFLOW)
        cycle["id"] = "tc164.cycle"
        cycle["edges"].append({"id": "var.answer>step.write", "from": "var.answer", "to": "step.write", "data": {"as": "again"}})
        broken = fixture_graph(WORKFLOW)
        broken["id"] = "tc164.broken"
        broken["nodes"][-1]["data"]["colour"] = "red"              # the last step, descriptor.model: a data step has no field `colour`
        before = version_counts(storage)
        # Hand-worked: the missing end breaks the alternation check and names the connection; the cycle is step.write -> var.answer -> step.write
        # (first ID repeated); the broken step is refused by the record check of graph_nodes, schema_break naming the extra field.
        cases = [(missing, ["descriptor.model>step.write"], None, None),
                 (cycle, ["step.write", "var.answer", "step.write"], None, None),
                 (broken, [], "schema_break", "colour")]
        for graph, named, rule, detail in cases:
            with self.subTest(graph["id"]):
                # When: it is saved
                result = model(backend).save_graph(graph)
                # Then: it is refused naming the IDs or the rule
                self.assertEqual((result.saved, result.version, result.named, result.rule, result.detail), (False, None, named, rule, detail))
                # And: the number of versions of every record of every graph table is as before
                self.assertEqual(version_counts(storage), before)

    @mark.req("REQ-WFM-147")
    def test_the_header_is_written_last(self):
        """TC-WFM-165 The header is written last: no half-stored graph at any write.
        Example: the first save of memory.write@5 interrupted at write 10 (the header) leaves the graph unlisted; the changed save interrupted at
        write 2 leaves version 1 listed and read exactly as before. Every k from 1 to the writes of the save, one run per k, files and PostgreSQL."""
        for kind in KINDS:
            with self.subTest(kind):
                self.probe(kind)
                for name, before, graph, writes, _changed in interrupted_saves():
                    gid = graph["id"]
                    # Given: the store holds the graph before the save (or nothing); TR-CORE-002: an uninterrupted save counts the known writes
                    _result, counted = self.counted_save(self.store_with(kind, before), graph)
                    self.assertEqual(counted, writes, name)
                    for k in range(1, writes + 1):
                        with self.subTest(save=name, k=k):
                            backend = self.store_with(kind, before)
                            # When: the save fails at write k
                            self.run_interrupted(backend, graph, k, writes)
                            # Then: the graph is not listed, or is entirely as before; never listed with a missing member
                            storage = Storage(backend)
                            if before is None:
                                self.assertNotIn(gid, storage.ids("graphs"))
                            else:
                                self.assertIn(gid, storage.ids("graphs"))
                                self.assertEqual(len(model(backend).graph_versions(gid)), 1)
                                self.assertEqual(model(backend).read_graph(gid), before)
                    # And (edge input): an interruption after the last write (the header) leaves the graph entirely new
                    with self.subTest(save=name, k="after the last write"):
                        backend = self.store_with(kind, before)
                        self.run_interrupted(backend, graph, writes + 1, writes)
                        self.assertEqual(model(backend).read_graph(gid), graph)
                        self.assertEqual(len(model(backend).graph_versions(gid)), 1 if before is None else 2)

    @mark.req("REQ-WFM-148")
    def test_only_changed_members_get_a_new_version(self):
        """TC-WFM-166 Only changed members get a new version.
        Example: memory.write@5 saved (every member 1 version, header 1); step.write changed and saved: step.write 2 versions, header 2, the other
        four steps and four connections still 1. Then the connection step.write>var.answer changed: it has 2, header 3, step.write still 2.
        Then input.text changed and changed back: input.text 3 versions (two new: the content is compared with the newest version only), header 5."""
        # Given: a workflow graph of five steps saved as version 1
        backend = self.store_with("files", fixture_graph(WORKFLOW))
        storage = Storage(backend)
        graph = fixture_graph(WORKFLOW)
        self.assertEqual(version_counts(storage), expected_counts(graph, 1))
        # When: one step is changed and the graph is saved again
        node_of(graph, "step.write")["data"]["toolbox_id"] = "view.memory_write_v2"
        self.assertEqual(model(backend).save_graph(graph).version, 2)
        # Then: one new version of that step and one new header version; the other four steps and all connections have none
        self.assertEqual(version_counts(storage), expected_counts(graph, 2, changed=("step.write",)))
        # And: one connection changed and saved: one new version of it and one new header version; no step has a new version
        edge_of(graph, "step.write>var.answer")["data"]["as"] = "result"
        self.assertEqual(model(backend).save_graph(graph).version, 3)
        self.assertEqual(version_counts(storage), expected_counts(graph, 3, changed=("step.write", "step.write>var.answer")))
        # And: a step changed and changed back gives two new step versions
        node_of(graph, "input.text")["data"]["value"] = "x"
        self.assertEqual(model(backend).save_graph(graph).version, 4)
        node_of(graph, "input.text")["data"].pop("value")
        self.assertEqual(model(backend).save_graph(graph).version, 5)
        counts = expected_counts(graph, 5, changed=("step.write", "step.write>var.answer"))
        counts["graph_nodes"]["memory.write@5/input.text"] = 3
        self.assertEqual(version_counts(storage), counts)
        self.assertEqual(model(backend).read_graph("memory.write@5"), graph)

    @mark.req("REQ-WFM-149")
    def test_an_unchanged_graph_gets_no_new_version(self):
        """TC-WFM-167 An unchanged graph gets no new version.
        Example: sample.code (7 steps, 6 connections) saved as version 1 (14 writes); saved again unchanged: 0 writes, answer version 1; saved with
        only a new description: 1 write (the header), version 2, every step and connection still 1 version."""
        # Given: a graph saved as version 1
        backend = fresh_backend("files", self)
        storage = Storage(backend)
        graph = fixture_graph("sample.code")
        result, writes = self.counted_save(backend, graph)
        self.assertEqual((result.saved, result.version, writes), (True, 1, 14))
        # When: the same graph is saved again
        result, writes = self.counted_save(backend, fixture_graph("sample.code"))
        # Then: the second save writes no record and answers with version 1
        self.assertEqual((result.saved, result.version, writes), (True, 1, 0))
        self.assertEqual(version_counts(storage), expected_counts(graph, 1))
        # When: only its description is changed and it is saved
        graph["description"] = "a code step, a loop and hostile names (second wording)"
        result, writes = self.counted_save(backend, graph)
        # Then: one header version and no step version are written
        self.assertEqual((result.saved, result.version, writes), (True, 2, 1))
        self.assertEqual(version_counts(storage), expected_counts(graph, 2))
        self.assertEqual(model(backend).read_graph("sample.code")["description"], "a code step, a loop and hostile names (second wording)")

    @mark.req("REQ-WFM-150")
    def test_a_refused_save_writes_nothing(self):
        """TC-WFM-168 A refused save writes nothing.
        Example: memory.write@5 stored at version 2; a copy with a second writer `step.other` of var.answer is refused naming var.answer; no table
        grew; memory.write@5 still at version 2 and read as saved."""
        # Given: a stored graph at version 2 and four new graphs
        backend = self.store_with("files", fixture_graph(WORKFLOW))
        storage = Storage(backend)
        stored = workflow_changed()
        self.assertEqual(model(backend).save_graph(stored).version, 2)
        cycle = fixture_graph(WORKFLOW)
        cycle["id"] = "tc168.cycle"
        cycle["edges"].append({"id": "var.answer>step.write", "from": "var.answer", "to": "step.write", "data": {"as": "again"}})
        writers = fixture_graph(WORKFLOW)
        writers["id"] = "tc168.writers"
        writers["nodes"].append({"id": "step.other", "data": {"type": "transform", "toolbox_id": "view.other"}})
        writers["edges"].append({"id": "step.other>var.answer", "from": "step.other", "to": "var.answer", "data": {"as": "output"}})
        unknown = fixture_graph(WORKFLOW)
        unknown["id"] = "tc168.unknown"
        unknown["nodes"].append({"id": "step.loop", "data": {"type": "loop", "toolbox_id": "view.loop"}})
        context = fixture_graph(CONTEXT)
        context["id"] = "tc168.context"
        context["edges"][-1]["to"] = "gone"                          # e2: claim -> gone, a step that is not there
        before = version_counts(storage)
        # Hand-worked: the cycle step.write -> var.answer -> step.write; var.answer has the writers step.write and step.other; step.loop has a kind
        # that is not data, transform or master; the context connection e2 leads to a missing step.
        cases = [(cycle, ["step.write", "var.answer", "step.write"]), (writers, ["var.answer"]), (unknown, ["step.loop"]), (context, ["e2"])]
        for graph, named in cases:
            with self.subTest(graph["id"]):
                # When: it is saved
                result = model(backend).save_graph(graph)
                # Then: it is refused naming the IDs
                self.assertEqual((result.saved, result.version, result.named, result.rule, result.detail), (False, None, named, None, None))
                # And: no table grew
                self.assertEqual(version_counts(storage), before)
                self.assertNotIn(graph["id"], storage.ids("graphs"))
        # And: the stored graph is still at version 2
        self.assertEqual([v["version"] for v in model(backend).graph_versions(WORKFLOW)], [1, 2])
        self.assertEqual(model(backend).read_graph(WORKFLOW), stored)

    @mark.req("REQ-WFM-151")
    def test_an_interrupted_save_is_finished_by_repeating_it(self):
        """TC-WFM-169 An interrupted save is finished by repeating it.
        Example: the first save of memory.write@5 interrupted at write 4 (three steps written); the repeated save writes the remaining 7 records
        (10 - 3), the graph reads back equal to the saved one, the header has 1 version and every member 1 (no step stored twice).
        Every k from 1 to the writes of the save, and after the last write (the repeated save then writes nothing); files and PostgreSQL."""
        for kind in KINDS:
            with self.subTest(kind):
                self.probe(kind)
                for name, before, graph, writes, changed in interrupted_saves():
                    gid = graph["id"]
                    headers = 1 if before is None else 2
                    for k in range(1, writes + 2):
                        with self.subTest(save=name, k=k):
                            # Given: the save interrupted at write k (k = writes + 1: after the last write); TR-CORE-002 is shown in run_interrupted
                            backend = self.store_with(kind, before)
                            self.run_interrupted(backend, graph, k, writes)
                            # When: the same save is repeated
                            result, repeated = self.counted_save(backend, graph)
                            # Then: the graph is complete and equals the saved one, with exactly one new header version
                            self.assertEqual((result.saved, result.version), (True, headers))
                            self.assertEqual(model(backend).read_graph(gid), graph)
                            self.assertEqual(len(model(backend).graph_versions(gid)), headers)
                            # And: no member is stored twice for equal content: the repeat writes only what the interrupted save did not
                            self.assertEqual(repeated, writes - (k - 1))
                            self.assertEqual(version_counts(Storage(backend)), expected_counts(graph, headers, changed))


if __name__ == "__main__":
    unittest.main()
