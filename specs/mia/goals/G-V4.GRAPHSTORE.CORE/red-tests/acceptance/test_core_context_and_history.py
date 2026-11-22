"""
Acceptance tests of G-V4.GRAPHSTORE.CORE, groups CG (context graphs) and RD (reading and history): TC-WFM-170 to TC-WFM-177
(REQ-WFM-152 to REQ-WFM-159, REQ-WFM-161). Expected values are exact (TR-CORE-005); every check uses its own graph IDs and a fresh store
(TR-CORE-007); times are only checked for being present and not decreasing (TR-CORE-008). TC-WFM-176 and TC-WFM-177 use the graphs of
tests/fixtures/graphs/ (TR-CORE-004); TC-WFM-177 runs on the files backend and on PostgreSQL 16, whose half is skipped, never passed, where
podman, the image or psycopg 3 is missing (TR-CORE-003).
Run with: python tests/acceptance/test_core_context_and_history.py
"""

import copy
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

from markers import mark                                        # noqa: E402
import core_stores                                              # noqa: E402
from core_stores import KINDS, fixture_graph, fresh_backend, version_counts   # noqa: E402
import graph_model                                              # noqa: E402
import storage                                                  # noqa: E402

MEMBER_TABLES = ("graph_nodes", "graph_edges", "context_nodes", "context_edges")
# The fields of a workflow graph as the caller saw it before the kind existed (REQ-WFM-157, TC-WFM-175).
WORKFLOW_FIELDS = {"id", "context_graph_id", "testbench_id", "description", "nodes", "edges"}


def tearDownModule():
    core_stores.stop_database()


def new_store(test, kind="files"):
    return storage.Storage(fresh_backend(kind, test))


def model(store, author="ann"):
    return graph_model.GraphModel(store, author=author)


def step(local_id, category, **fields):
    return {"id": local_id, "data": dict({"type": category}, **fields)}


def connection(local_id, start, end, **data):
    return {"id": local_id, "from": start, "to": end, "data": data}


def context_graph(graph_id, nodes, edges, description="a context graph"):
    return {"id": graph_id, "kind": "context", "context_graph_id": "", "testbench_id": "", "description": description,
            "nodes": nodes, "edges": edges}


def workflow_graph(graph_id, description="a workflow graph"):
    """data `in` -> transform `t` -> data `out`: keeps every workflow rule."""
    return {"id": graph_id, "context_graph_id": "ctx", "testbench_id": "tb", "description": description,
            "nodes": [{"id": "in", "data": {"type": "data", "value": "x"}}, {"id": "t", "data": {"type": "transform", "toolbox_id": "copy"}},
                      {"id": "out", "data": {"type": "data"}}],
            "edges": [connection("e1", "in", "t"), connection("e2", "t", "out")]}


def ids(store, table):
    return store.ids(table)


class ContextGraphs(unittest.TestCase):
    """Group CG: the same save path for the second kind of graph; the kind of a graph."""

    @mark.req("REQ-WFM-152")
    def test_context_graph_is_stored_in_the_context_tables(self):
        """TC-WFM-170 A context graph is stored in the context tables.
        Example: context graph `c` with steps claim, source, note and connections e1 (source -> claim), e2 (claim -> note) -> records c/claim,
        c/note, c/source in context_nodes, c/e1, c/e2 in context_edges, nothing in graph_nodes or graph_edges, header kind `context`."""
        # Given: a context graph `c` of three steps and two connections, a fresh store
        store = new_store(self)
        graph = context_graph("c", [step("claim", "claim", text="water boils at 100 C"), step("source", "source", url="local:book-1"),
                                    step("note", "note", text="ctx")],
                              [connection("e1", "source", "claim", relation="supports"), connection("e2", "claim", "note")])
        # When: it is saved
        result = model(store).save_graph(graph)
        # Then: it is saved as version 1 of the graph
        self.assertTrue(result.saved, result)
        self.assertEqual(result.version, 1)
        # And: the members are the records c/<local> in the context tables (store.ids is sorted), none in the workflow tables
        self.assertEqual(ids(store, "context_nodes"), ["c/claim", "c/note", "c/source"])
        self.assertEqual(ids(store, "context_edges"), ["c/e1", "c/e2"])
        self.assertEqual(ids(store, "graph_nodes"), [])
        self.assertEqual(ids(store, "graph_edges"), [])
        # And: the header has the kind `context` and pins the scoped members in the order of the graph
        data = store.get("graphs", "c")["doc"]["data"]
        self.assertEqual(data["kind"], "context")
        self.assertEqual([m["id"] for m in data["nodes"]], ["c/claim", "c/source", "c/note"])
        self.assertEqual([m["id"] for m in data["edges"]], ["c/e1", "c/e2"])

    @mark.req("REQ-WFM-153")
    def test_no_kind_means_workflow(self):
        """TC-WFM-171 No kind means workflow.
        Example: the graph in -> t -> out saved as `w1` without a kind and as `w2` with the kind `workflow` -> both headers kind `workflow`,
        members w1/in, w1/out, w1/t and w2/in, w2/out, w2/t in graph_nodes, the context tables empty, the same content read back."""
        # Given: a graph given without a kind, and the same graph with the kind `workflow` written out
        store = new_store(self)
        bare = workflow_graph("w1")
        self.assertNotIn("kind", bare)
        explicit = dict(workflow_graph("w2"), kind="workflow")
        # When: each is saved under its own ID
        first = model(store).save_graph(bare)
        second = model(store).save_graph(explicit)
        # Then: both are saved, each as its version 1
        self.assertEqual((first.saved, first.version), (True, 1), first)
        self.assertEqual((second.saved, second.version), (True, 1), second)
        # And: both headers have the kind `workflow`
        self.assertEqual(store.get("graphs", "w1")["doc"]["data"]["kind"], "workflow")
        self.assertEqual(store.get("graphs", "w2")["doc"]["data"]["kind"], "workflow")
        # And: the members are in the workflow tables, none in the context tables
        self.assertEqual(ids(store, "graph_nodes"), ["w1/in", "w1/out", "w1/t", "w2/in", "w2/out", "w2/t"])
        self.assertEqual(ids(store, "graph_edges"), ["w1/e1", "w1/e2", "w2/e1", "w2/e2"])
        self.assertEqual(ids(store, "context_nodes"), [])
        self.assertEqual(ids(store, "context_edges"), [])
        # And: the same content: read back, the two graphs differ only in their ID
        read1 = model(store).read_graph("w1")
        read2 = model(store).read_graph("w2")
        self.assertEqual({k: v for k, v in read1.items() if k != "id"}, {k: v for k, v in read2.items() if k != "id"})

    @mark.req("REQ-WFM-154")
    def test_unknown_kind_is_refused(self):
        """TC-WFM-172 An unknown kind is refused.
        Example: the graph in -> t -> out with the kind `swarm`, `` or 3 -> refused, rule `schema_break` naming the field `kind`; no record stored."""
        for number, kind in enumerate(("swarm", "", 3)):
            with self.subTest(kind=kind):
                # Given: a graph with the kind `swarm`, the empty text or the number 3, a fresh store
                store = new_store(self)
                graph = dict(workflow_graph("k%d" % number), kind=kind)
                before = version_counts(store)
                # When: it is saved
                result = model(store).save_graph(graph)
                # Then: it is refused naming the field `kind`
                self.assertFalse(result.saved, result)
                self.assertIsNone(result.version)
                self.assertEqual((result.rule, result.detail), ("schema_break", "kind"))
                # And: nothing is stored: every table is as empty as before
                self.assertEqual(version_counts(store), before)
                self.assertEqual(before, {t: {} for t in MEMBER_TABLES + ("graphs",)})

    @mark.req("REQ-WFM-155", "REQ-WFM-161")
    def test_context_graph_keeps_identity_and_ends(self):
        """TC-WFM-173 A context graph keeps identity and ends.
        Example: steps `claim` twice -> refused naming ["claim"]; connection `e1` twice -> ["e1"]; e1 from claim to the missing step `ghost`
        -> ["e1"] (the connection that has the missing end); nothing written. An empty context graph `empty` -> saved, one header version."""
        claim, source = step("claim", "claim", text="t"), step("source", "source")
        cases = (("repeated step", [claim, step("claim", "note")], [], ["claim"]),
                 ("repeated connection", [claim, source], [connection("e1", "source", "claim"), connection("e1", "claim", "source")], ["e1"]),
                 ("missing step", [claim], [connection("e1", "claim", "ghost")], ["e1"]))
        for name, nodes, edges, named in cases:
            with self.subTest(name):
                # Given: a context graph with a repeated step ID, a repeated connection ID or a connection to a missing step
                store = new_store(self)
                before = version_counts(store)
                # When: it is saved
                result = model(store).save_graph(context_graph("bad", nodes, edges))
                # Then: it is refused naming the repeated or missing ID
                self.assertFalse(result.saved, result)
                self.assertIsNone(result.version)
                self.assertEqual(result.named, named)
                # And: nothing is written
                self.assertEqual(version_counts(store), before)
                self.assertEqual(before, {t: {} for t in MEMBER_TABLES + ("graphs",)})
        # And: an empty context graph is accepted as one header version, with no member record
        store = new_store(self)
        result = model(store).save_graph(context_graph("empty", [], []))
        self.assertEqual((result.saved, result.version), (True, 1), result)
        self.assertEqual(version_counts(store), {"graph_nodes": {}, "graph_edges": {}, "context_nodes": {}, "context_edges": {}, "graphs": {"empty": 1}})
        self.assertEqual(store.get("graphs", "empty")["doc"]["data"]["kind"], "context")

    @mark.req("REQ-WFM-156")
    def test_workflow_rules_do_not_apply_to_a_context_graph(self):
        """TC-WFM-174 Workflow rules do not apply to a context graph.
        Example: steps a and b, both of the category `claim`, connections e1 (a -> b) and e2 (b -> a): a cycle, no alternation of data and
        processing steps, b and a each with a writer of the same category, no stop limit -> saved as version 1 and read back as given."""
        # Given: a context graph of two connected steps of the same category and a connection back, so that it has a cycle
        store = new_store(self)
        graph = context_graph("loop", [step("a", "claim", text="A"), step("b", "claim", text="B")],
                              [connection("e1", "a", "b"), connection("e2", "b", "a")])
        # When: it is saved
        result = model(store).save_graph(graph)
        # Then: it is accepted: no order, alternation, writer or stop-limit rule of workflow graphs is applied
        self.assertEqual((result.saved, result.version, result.named), (True, 1, []), result)
        # And: it is stored as given
        self.assertEqual(model(store).read_graph("loop"), graph)

    @mark.req("REQ-WFM-157")
    def test_context_graph_is_read_with_its_kind(self):
        """TC-WFM-175 A context graph is read with its kind.
        Example: context graph `cx` and workflow graph `wf`, each saved twice (description `first`, then `second`) -> `cx` read at versions 1
        and 2 has the kind `context`; `wf` read at versions 1 and 2 has exactly the keys id, context_graph_id, testbench_id, description, nodes,
        edges (no `kind`)."""
        # Given: a context graph and a workflow graph, each saved twice
        store = new_store(self)
        ctx = context_graph("cx", [step("claim", "claim", text="t")], [])
        for description in ("first", "second"):
            self.assertTrue(model(store).save_graph(dict(ctx, description=description)).saved)
            self.assertTrue(model(store).save_graph(workflow_graph("wf", description)).saved)
        for version, description in ((1, "first"), (2, "second")):
            with self.subTest(version=version):
                # When: each is read at every version
                read_ctx = model(store).read_graph("cx", version)
                read_wf = model(store).read_graph("wf", version)
                # Then: the context graph is returned with the kind `context` at every version
                self.assertEqual(read_ctx["kind"], "context")
                self.assertEqual(read_ctx["description"], description)
                # And: the workflow graph has exactly the fields it had before the kind existed
                self.assertEqual(set(read_wf), WORKFLOW_FIELDS)
                self.assertEqual(read_wf, workflow_graph("wf", description))


class ReadingAndHistory(unittest.TestCase):
    """Group RD: versions with who and when, a version as it was saved."""

    @mark.req("REQ-WFM-158")
    def test_versions_are_listed_with_who_and_when(self):
        """TC-WFM-176 Versions are listed with who and when.
        Example: the fixture graph chat@1 saved by ann, then by bob with the description `by bob`, then by cy with `by cy` -> versions
        [(1, ann), (2, bob), (3, cy)], oldest first, each with a time that is present and not before the one of the version before."""
        # Given: a graph saved by the accounts ann, bob and cy, one version each (a changed description makes each save a new version)
        store = new_store(self)
        graph = fixture_graph("chat@1")
        saved = [model(store, "ann").save_graph(graph),
                 model(store, "bob").save_graph(dict(graph, description="by bob")),
                 model(store, "cy").save_graph(dict(graph, description="by cy"))]
        self.assertEqual([(r.saved, r.version) for r in saved], [(True, 1), (True, 2), (True, 3)])
        # When: the versions are asked
        versions = model(store).graph_versions("chat@1")
        # Then: versions 1 to 3 are listed oldest first with ann, bob, cy
        self.assertEqual([(v["version"], v["author"]) for v in versions], [(1, "ann"), (2, "bob"), (3, "cy")])
        # And: each with a time: present, and not decreasing (TR-CORE-008: never compared exactly)
        times = [v["time"] for v in versions]
        for t in times:
            self.assertIsInstance(t, str)
            self.assertTrue(t)
        self.assertEqual(times, sorted(times))

    @mark.req("REQ-WFM-159")
    def test_every_version_reads_back_as_saved(self):
        """TC-WFM-177 Every version reads back as saved.
        Example: sample.code saved as given (v1), with the stop of the loop-controlling step `loop.review` raised from 3 to 5 repetitions (v2),
        then with connection e2 given the role `script` and a new description (v3); context.cp13 saved as given (v1), with the text of
        `claim` changed (v2), then with connection e1 given the relation `refutes` and a new description (v3) -> each read at 1, 2, 3 equals
        what was saved at that version, step by step and connection by connection; on files and on PostgreSQL."""
        for kind in KINDS:
            with self.subTest(kind):
                # Given: a workflow graph with a loop-controlling step and a context graph with category steps, each saved in three versions
                store = new_store(self, kind)
                for name, change_step, change_connection in (("sample.code", self._raise_loop_limit, self._retag_code_connection),
                                                             ("context.cp13", self._change_claim, self._retag_support_connection)):
                    v1 = fixture_graph(name)
                    v2 = change_step(copy.deepcopy(v1))
                    v3 = change_connection(copy.deepcopy(v2))
                    saved = {}
                    for number, graph in enumerate((v1, v2, v3), start=1):
                        result = model(store).save_graph(graph)
                        self.assertEqual((result.saved, result.version), (True, number), (name, result))
                        saved[number] = copy.deepcopy(graph)
                    for number in (1, 2, 3):
                        # When: each version is read at its number
                        read = model(store).read_graph(name, number)
                        # Then: it equals what was saved at that version, step by step and connection by connection
                        expected = saved[number]
                        self.assertEqual(len(read["nodes"]), len(expected["nodes"]), (name, number))
                        for got, want in zip(read["nodes"], expected["nodes"]):
                            self.assertEqual(got, want, (name, number))
                        self.assertEqual(len(read["edges"]), len(expected["edges"]), (name, number))
                        for got, want in zip(read["edges"], expected["edges"]):
                            self.assertEqual(got, want, (name, number))
                        # And: the header fields too, so the whole graph is equal
                        self.assertEqual(read, expected, (name, number))

    # The three versions differ in exactly one place each, so a read of the wrong version cannot pass.
    @staticmethod
    def _raise_loop_limit(graph):
        node = next(n for n in graph["nodes"] if n["id"] == "loop.review")
        assert node["data"]["type"] == "master" and node["data"]["stop"] == {"max_repetitions": 3}
        node["data"]["stop"] = {"max_repetitions": 5}
        return graph

    @staticmethod
    def _retag_code_connection(graph):
        edge = next(e for e in graph["edges"] if e["id"] == "e2")
        edge["data"] = {"role": "script"}
        graph["description"] = "sample.code, third version"
        return graph

    @staticmethod
    def _change_claim(graph):
        node = next(n for n in graph["nodes"] if n["id"] == "claim")
        node["data"]["text"] = "water boils at 100 C at sea level"
        return graph

    @staticmethod
    def _retag_support_connection(graph):
        edge = next(e for e in graph["edges"] if e["id"] == "e1")
        edge["data"] = {"relation": "refutes"}
        graph["description"] = "context.cp13, third version"
        return graph


if __name__ == "__main__":
    unittest.main(verbosity=1)
