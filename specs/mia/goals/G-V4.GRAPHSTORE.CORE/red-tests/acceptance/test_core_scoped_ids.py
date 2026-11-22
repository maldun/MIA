"""
Acceptance tests of G-V4.GRAPHSTORE.CORE, group SC (steps belong to one graph): TC-GTB-033, TC-GTB-034, TC-GTB-035 (REQ-GTB-029 to REQ-GTB-031,
the Graph tables through the Storage layer), TC-WFM-178, TC-WFM-162, TC-WFM-163 (REQ-WFM-160, REQ-WFM-144, REQ-WFM-145, the Workflow management).
Expected values are exact (TR-CORE-005); every check has its own graph IDs and a fresh files store (TR-CORE-007); times are only checked for being
present and not decreasing (TR-CORE-008). Run with: python tests/acceptance/test_core_scoped_ids.py
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

from markers import mark                    # noqa: E402
import core_stores                          # noqa: E402
import graph_model                          # noqa: E402
import graph_tables                         # noqa: E402
import storage                              # noqa: E402
from storage import StorageError            # noqa: E402

WHO = "ann"


def tearDownModule():
    core_stores.stop_database()


def new_storage(test):
    """A Storage layer on a files store no other check has written to (TR-CORE-007)."""
    return storage.Storage(core_stores.fresh_backend("files", test))


def step_record(record_id):
    return {"id": record_id, "data": {"type": "data"}}


def connection_record(record_id, end):
    return {"id": record_id, "from": end, "to": end, "data": {}}


def header(graph_id, nodes=(), edges=()):
    """A header of a workflow graph that pins the given members, each in version 1."""
    return {"id": graph_id, "data": {"kind": "workflow", "context_graph_id": "", "testbench_id": "", "description": "a test graph",
                                     "nodes": [{"id": i, "version": 1} for i in nodes], "edges": [{"id": i, "version": 1} for i in edges]}}


def refused(test, store, table, record_id, doc):
    """Writes a record that must be refused; returns (rule, detail) and checks that nothing was stored under its ID."""
    with test.assertRaises(StorageError) as caught:
        store.put(table, record_id, doc, WHO)
    test.assertEqual(caught.exception.code, "invalid")
    test.assertNotIn(record_id, store.ids(table))
    return caught.exception.rule, caught.exception.detail


def workflow(graph_id, toolbox_id="write.a", **extra):
    """A small workflow graph with local IDs: the data step `query` feeds the transform step `step.write` (connection e1)."""
    graph = {"id": graph_id, "context_graph_id": "", "testbench_id": "", "description": "a test graph",
             "nodes": [{"id": "query", "data": {"type": "data"}}, {"id": "step.write", "data": {"type": "transform", "toolbox_id": toolbox_id}}],
             "edges": [{"id": "e1", "from": "query", "to": "step.write", "data": {}}]}
    graph.update(extra)
    return graph


class ScopedIdAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-029")
    def test_a_step_or_connection_without_a_graph_in_its_id_is_refused(self):
        """TC-GTB-033: a step and a connection record under chat, /chat, lookup/ and the empty ID are refused; under lookup/chat they are stored.

        Example: graph_nodes "chat" -> unscoped_id; graph_edges "" -> record_identity naming id; graph_nodes "lookup/chat" -> version 1.
        """
        # Given: a fresh store; a step record and a connection record, each offered under four IDs and once under lookup/chat.
        # The connection's ends are the step lookup/end, stored beforehand, so a connection is refused for its ID and not for a missing end.
        store = new_storage(self)
        store.put("graph_nodes", "lookup/end", step_record("lookup/end"), WHO)
        for table, make in (("graph_nodes", step_record), ("graph_edges", lambda i: connection_record(i, "lookup/end"))):
            with self.subTest(table):
                # When: the record is written under each of the three unscoped IDs
                for record_id in ("chat", "/chat", "lookup/"):
                    # Then: each is refused naming unscoped_id: chat has no slash, /chat has no graph part, lookup/ has no local part
                    rule, _ = refused(self, store, table, record_id, make(record_id))
                    self.assertEqual(rule, "unscoped_id", record_id)
                # And: the empty ID is refused naming record_identity with the field id, as before (D-409)
                self.assertEqual(refused(self, store, table, "", make("")), ("record_identity", "id"))
                # And: the record under lookup/chat is accepted (the first version) and stored as written
                self.assertEqual(store.put(table, "lookup/chat", make("lookup/chat"), WHO), {"version": 1})
                self.assertEqual(store.get(table, "lookup/chat")["doc"], make("lookup/chat"))

    @mark.req("REQ-GTB-030")
    def test_a_header_names_only_its_own_members(self):
        """TC-GTB-034: headers of the graph g that pin h/step or h/conn are refused naming unscoped_id; those with g/step or g/conn are accepted.

        Example: header g pinning h/step@1 -> unscoped_id; pinning g/step@1 -> version 1; pinning g/conn@1 -> version 2.
        """
        # Given: the members g/step, h/step, g/conn (g/step to g/step) and h/conn (h/step to h/step) exist, each in version 1
        store = new_storage(self)
        for record_id in ("g/step", "h/step"):
            store.put("graph_nodes", record_id, step_record(record_id), WHO)
        for record_id, end in (("g/conn", "g/step"), ("h/conn", "h/step")):
            store.put("graph_edges", record_id, connection_record(record_id, end), WHO)
        # When: the header of g that pins the step h/step is written
        # Then: it is refused naming unscoped_id (h/step begins with the ID of another graph) and no header of g is stored
        rule, _ = refused(self, store, "graphs", "g", header("g", nodes=["h/step"]))
        self.assertEqual(rule, "unscoped_id")
        # When: the header that pins its own step g/step is written; Then: it is accepted as the first version of g
        self.assertEqual(store.put("graphs", "g", header("g", nodes=["g/step"]), WHO), {"version": 1})
        # When: the header that pins the connection h/conn is written; Then: refused naming unscoped_id, g keeps one version
        with self.assertRaises(StorageError) as caught:
            store.put("graphs", "g", header("g", edges=["h/conn"]), WHO)
        self.assertEqual((caught.exception.code, caught.exception.rule), ("invalid", "unscoped_id"))
        self.assertEqual(len(store.history("graphs", "g")), 1)
        # And: the header that pins its own connection g/conn is accepted as the second version of g
        self.assertEqual(store.put("graphs", "g", header("g", edges=["g/conn"]), WHO), {"version": 2})

    @mark.req("REQ-GTB-031")
    def test_the_first_slash_separates_graph_and_local_id(self):
        """TC-GTB-035: the text before the first slash is the graph ID, the rest the local ID.

        Example: lookup/a/b -> (lookup, a/b); lookup/a -> (lookup, a); g// -> (g, /); lookup/ -> no local ID, not scoped (None).
        """
        # Given: the record IDs lookup/a/b, lookup/a, g// and lookup/, and the split of the Graph tables
        split = getattr(graph_tables, "split_scoped", None)
        self.assertIsNotNone(split, "the Graph tables have no split of a record ID into graph ID and local ID")
        # When: each is split
        # Then: the first slash separates; a local ID may hold slashes, an empty local ID is not scoped
        self.assertEqual(split("lookup/a/b"), ("lookup", "a/b"))
        self.assertEqual(split("lookup/a"), ("lookup", "a"))
        self.assertEqual(split("g//"), ("g", "/"))
        self.assertIsNone(split("lookup/"))

    @mark.req("REQ-WFM-160")
    def test_a_graph_id_with_a_slash_is_refused(self):
        """TC-WFM-178: a graph with steps saved under look/up, /lookup or the empty ID is refused naming unscoped_id and the record ID of the
        step or member that breaks the rule; nothing is stored for them; under lookup it is accepted. The slash is caught through the steps (D-410).

        Example: save_graph(graph with id "look/up") -> SaveResult(saved=False, rule="unscoped_id", detail="look/up/query"); id "lookup" -> saved, version 1.
        """
        # Given: a fresh store and the same small graph offered under the IDs look/up, /lookup, the empty ID and lookup
        store = new_storage(self)
        model = graph_model.GraphModel(store, author=WHO)
        # look/up/query splits at the first slash into the graph look, so the header of look/up names a member of another graph;
        # /lookup/query and /query have an empty graph part (REQ-GTB-029, REQ-GTB-031)
        expected = {"look/up": "look/up/query", "/lookup": "/lookup/query", "": "/query"}
        for graph_id, detail in expected.items():
            with self.subTest(graph_id=graph_id):
                before = core_stores.version_counts(store)
                # When: the graph is saved under the ID
                result = model.save_graph(workflow(graph_id))
                # Then: it is refused naming unscoped_id and the record ID that breaks it
                self.assertFalse(result.saved)
                self.assertEqual((result.rule, result.detail), ("unscoped_id", detail))
                # And: nothing is stored: no table has a new record or version
                self.assertEqual(core_stores.version_counts(store), before)
        # And: under lookup the graph is accepted as the first version of lookup
        result = model.save_graph(workflow("lookup"))
        self.assertEqual((result.saved, result.version), (True, 1))

    @mark.req("REQ-WFM-144")
    def test_a_graph_is_read_with_local_ids(self):
        """TC-WFM-162: a graph g with steps a and a/b and the connection e1 from a to a/b is read back with the same local IDs.

        Example: read_graph("g") -> nodes a, a/b; edge e1 from a to a/b; the store holds them as g/a, g/a/b and g/e1.
        """
        # Given: a fresh store and the workflow graph g: data step a, transform step a/b, connection e1 from a to a/b
        store = new_storage(self)
        model = graph_model.GraphModel(store, author=WHO)
        graph = {"id": "g", "context_graph_id": "", "testbench_id": "", "description": "a test graph",
                 "nodes": [{"id": "a", "data": {"type": "data"}}, {"id": "a/b", "data": {"type": "transform", "toolbox_id": "t"}}],
                 "edges": [{"id": "e1", "from": "a", "to": "a/b", "data": {}}]}
        # When: it is saved and read back
        self.assertTrue(model.save_graph(graph).saved)
        read = model.read_graph("g")
        # Then: the step IDs are a and a/b, the connection ID is e1 and its ends are a and a/b; no ID carries the graph ID
        self.assertEqual([n["id"] for n in read["nodes"]], ["a", "a/b"])
        self.assertEqual([(e["id"], e["from"], e["to"]) for e in read["edges"]], [("e1", "a", "a/b")])
        # And: the IDs are local only because the store holds the graph's records under <graph id>/<local id> (REQ-WFM-144 rationale, REQ-GTB-029)
        self.assertEqual(sorted(store.ids("graph_nodes")), ["g/a", "g/a/b"])
        self.assertEqual(sorted(store.ids("graph_edges")), ["g/e1"])

    @mark.req("REQ-WFM-145")
    def test_a_steps_history_lists_its_own_graphs_changes(self):
        """TC-WFM-163: the history of step.write of lookup lists its two versions, that of search one; the step x of look is never a member of lookup.

        Example: step_history("lookup", "step.write") -> versions [1, 2] by ann; step_history("search", "step.write") -> [1].
        """
        # Given: a fresh store; the graphs lookup and search, each with a step step.write of different content (toolbox write.a and write.b),
        # and the graph look with a step x (look is the prefix of lookup)
        store = new_storage(self)
        model = graph_model.GraphModel(store, author=WHO)
        look = {"id": "look", "context_graph_id": "", "testbench_id": "", "description": "a test graph",
                "nodes": [{"id": "x", "data": {"type": "data"}}], "edges": []}
        for graph in (workflow("lookup", "write.a"), workflow("search", "write.b"), look):
            self.assertTrue(model.save_graph(graph).saved, graph["id"])
        search_before = model.step_history("search", "step.write")
        # When: step.write of lookup is changed (toolbox write.c) and saved
        self.assertEqual(model.save_graph(workflow("lookup", "write.c")).version, 2)
        # Then: its history lists two versions, oldest first, each with account and time (times present and not decreasing, TR-CORE-008)
        history = model.step_history("lookup", "step.write")
        self.assertEqual([(h["version"], h["author"]) for h in history], [(1, WHO), (2, WHO)])
        self.assertTrue(all(h["time"] for h in history))
        self.assertLessEqual(history[0]["time"], history[1]["time"])
        # And: the history of step.write in search lists one version and is unchanged by the save of lookup
        after = model.step_history("search", "step.write")
        self.assertEqual([(h["version"], h["author"]) for h in after], [(1, WHO)])
        self.assertEqual(after, search_before)
        # And: the step x of look is never a member of lookup: not in any version of lookup, and lookup has no history of x
        for version in (1, 2):
            self.assertEqual([n["id"] for n in model.read_graph("lookup", version)["nodes"]], ["query", "step.write"])
        self.assertEqual(model.step_history("lookup", "x"), [])


if __name__ == "__main__":
    unittest.main()
