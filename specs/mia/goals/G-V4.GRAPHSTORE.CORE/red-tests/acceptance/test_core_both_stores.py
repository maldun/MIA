"""
Acceptance check TC-GTB-036 of G-V4.GRAPHSTORE.CORE (REQ-GTB-032): both stores refuse the same way.

The refusal cases of TC-GTB-033, TC-GTB-034, TC-WFM-164, TC-WFM-172, TC-WFM-173 and TC-WFM-178 run on a fresh files backend and on a fresh
PostgreSQL 16 database (a throw-away container of tests/helpers/core_stores.py, TR-CORE-003). Each case must give the same refusal rule and the
same named detail on both stores, and the values the scenarios name (exact, TR-CORE-005). Where podman, the image or psycopg 3 is missing the
PostgreSQL half is reported as skipped, never as passed.
Run with: python tests/acceptance/test_core_both_stores.py
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

import core_stores                                  # noqa: E402
from core_stores import KINDS, fresh_backend, version_counts   # noqa: E402
from markers import mark                            # noqa: E402
import graph_model                                  # noqa: E402
import storage                                      # noqa: E402
from storage import StorageError                    # noqa: E402

WHO = "ann"


def tearDownModule():
    core_stores.stop_database()


def graph(graph_id, nodes, edges, **fields):
    return dict({"id": graph_id, "context_graph_id": "", "testbench_id": "", "description": "a test graph", "nodes": nodes, "edges": edges}, **fields)


def data(step_id):
    return {"id": step_id, "data": {"type": "data"}}


def transform(step_id):
    return {"id": step_id, "data": {"type": "transform", "toolbox_id": "tb"}}


def category(step_id, name="claim"):
    return {"id": step_id, "data": {"type": name}}


def edge(edge_id, start, end):
    return {"id": edge_id, "from": start, "to": end, "data": {}}


def header(graph_id, nodes=(), edges=()):
    """A workflow header whose members are (record ID, version) pairs."""
    return {"id": graph_id, "data": {"kind": "workflow", "context_graph_id": "", "testbench_id": "", "description": "a test graph",
                                     "nodes": [{"id": i, "version": v} for i, v in nodes], "edges": [{"id": i, "version": v} for i, v in edges]}}


def put_outcome(store, table, record_id, doc):
    """("stored", version) or (code, rule, detail) of the refusal."""
    try:
        return ("stored", store.put(table, record_id, doc, WHO)["version"])
    except StorageError as err:
        return (err.code, err.rule, err.detail)


def save_outcome(model, g):
    r = model.save_graph(g)
    return (r.saved, r.version, r.named, r.rule, r.detail)


class BothStoresRefuseAlike(unittest.TestCase):

    def on_both(self, run, expected):
        """Runs `run(store)` on a fresh store of each kind; each must give `expected`, and the two stores the same outcome."""
        outcomes = {}
        for kind in KINDS:
            with self.subTest(kind):
                store = storage.Storage(fresh_backend(kind, self))     # SkipTest of a missing PostgreSQL propagates: reported as skipped
                outcomes[kind] = run(store)
                self.assertEqual(outcomes[kind], expected)
        if len(outcomes) == len(KINDS):
            self.assertEqual(outcomes["files"], outcomes["postgres"])

    @mark.req("REQ-GTB-032", "REQ-GTB-029")
    def test_unscoped_member_ids_refused_alike(self):
        """TC-GTB-036 (cases of TC-GTB-033): a step or connection without a graph in its ID is refused the same way on both stores.
        Example: the step `chat` -> invalid, unscoped_id, `chat` on files and on PostgreSQL; the empty ID -> record_identity, `id`."""
        def run(store):
            out = []
            for table in ("graph_nodes", "graph_edges"):
                for rid in ("chat", "/chat", "lookup/", ""):
                    doc = data(rid) if table == "graph_nodes" else edge(rid, "lookup/a", "lookup/b")
                    out.append((table, rid) + put_outcome(store, table, rid, doc))
            # And: nothing is stored
            out.append(("stored ids", store.ids("graph_nodes"), store.ids("graph_edges")))
            return out
        # Given: an empty store of each kind
        # When: each unscoped record is written
        # Then: `chat`, `/chat` and `lookup/` name unscoped_id with the ID itself (no graph part, empty graph part, empty local part);
        #       the empty ID names record_identity with the field `id` (D-409)
        expected = []
        for table in ("graph_nodes", "graph_edges"):
            expected += [(table, rid, "invalid", "unscoped_id", rid) for rid in ("chat", "/chat", "lookup/")]
            expected.append((table, "", "invalid", "record_identity", "id"))
        expected.append(("stored ids", [], []))
        self.on_both(run, expected)

    @mark.req("REQ-GTB-032", "REQ-GTB-030")
    def test_header_with_foreign_member_refused_alike(self):
        """TC-GTB-036 (cases of TC-GTB-034): a header of `g` that pins a member of `h` is refused the same way on both stores.
        Example: the header `g` pinning `h/step` version 1 -> invalid, unscoped_id, `h/step`."""
        def run(store):
            # Given: the members g/step, h/step, g/conn, h/conn exist (each connection from its graph's step to itself)
            for rid in ("g/step", "h/step"):
                store.put("graph_nodes", rid, data(rid), WHO)
            store.put("graph_edges", "g/conn", edge("g/conn", "g/step", "g/step"), WHO)
            store.put("graph_edges", "h/conn", edge("h/conn", "h/step", "h/step"), WHO)
            # When: the headers with a member of h are written
            out = [put_outcome(store, "graphs", "g", header("g", nodes=[("h/step", 1)])),
                   put_outcome(store, "graphs", "g", header("g", edges=[("h/conn", 1)]))]
            out.append(("stored headers", store.ids("graphs")))
            return out
        # Then: each names unscoped_id with the foreign member's ID; And: no header is stored
        self.on_both(run, [("invalid", "unscoped_id", "h/step"), ("invalid", "unscoped_id", "h/conn"), ("stored headers", [])])

    @mark.req("REQ-GTB-032", "REQ-WFM-146")
    def test_whole_graph_check_refuses_alike(self):
        """TC-GTB-036 (cases of TC-WFM-164): a missing step, a cycle and a broken step content are refused alike, and nothing is written.
        Example: a graph whose last connection e3 leads to the missing step `ghost` -> refused naming [`e3`] on both stores."""
        def run(store):
            model = graph_model.GraphModel(store, author=WHO)
            # Given: a stored graph `kept` (a -> t -> b)
            model.save_graph(graph("kept", [data("a"), transform("t"), data("b")], [edge("e1", "a", "t"), edge("e2", "t", "b")]))
            before = version_counts(store)
            # When: three new graphs are saved
            out = [
                # the last connection e3 leads to `ghost`, which is not a step: the end check of the alternation rule names e3
                save_outcome(model, graph("ends", [data("a"), transform("t"), data("b")],
                                          [edge("e1", "a", "t"), edge("e2", "t", "b"), edge("e3", "b", "ghost")])),
                # a -> t -> a: the depth-first search from a finds the cycle a, t, a
                save_outcome(model, graph("loop", [data("a"), transform("t")], [edge("e1", "a", "t"), edge("e2", "t", "a")])),
                # a transform without its toolbox_id: the record check of the scoped step names the missing field
                save_outcome(model, graph("broken", [data("a"), {"id": "t", "data": {"type": "transform"}}], [edge("e1", "a", "t")])),
            ]
            # And: the number of versions of every record of every graph table is as before
            out.append(("versions unchanged", version_counts(store) == before))
            return out
        # Then: each is refused with the same names on both stores
        self.on_both(run, [(False, None, ["e3"], None, None),
                           (False, None, ["a", "t", "a"], None, None),
                           (False, None, [], "schema_break", "toolbox_id"),
                           ("versions unchanged", True)])

    @mark.req("REQ-GTB-032", "REQ-WFM-154")
    def test_unknown_kind_refused_alike(self):
        """TC-GTB-036 (cases of TC-WFM-172): the kinds `swarm`, the empty text and 3 are refused naming `kind` on both stores; nothing is stored.
        Example: kind `swarm` -> (False, schema_break, `kind`)."""
        def run(store):
            model = graph_model.GraphModel(store, author=WHO)
            # Given: an empty store; When: a one-step graph is saved with each unknown kind
            out = [save_outcome(model, graph("k%d" % n, [data("a")], [], kind=kind)) for n, kind in enumerate(("swarm", "", 3))]
            # And: no record in any graph table
            out.append(("stored", version_counts(store)))
            return out
        empty = {t: {} for t in ("graph_nodes", "graph_edges", "context_nodes", "context_edges", "graphs")}
        # Then: each refusal names the field kind
        self.on_both(run, [(False, None, [], "schema_break", "kind")] * 3 + [("stored", empty)])

    @mark.req("REQ-GTB-032", "REQ-WFM-155", "REQ-WFM-161")
    def test_context_identity_and_ends_refused_alike(self):
        """TC-GTB-036 (cases of TC-WFM-173): a context graph with a repeated step ID, a repeated connection ID or a connection to a missing step
        is refused naming that ID on both stores; nothing is written.
        Example: the steps s1, s1 -> refused naming [`s1`]."""
        def run(store):
            model = graph_model.GraphModel(store, author=WHO)
            # Given: an empty store; When: three broken context graphs are saved
            out = [
                save_outcome(model, graph("c1", [category("s1"), category("s1", "source")], [], kind="context")),
                save_outcome(model, graph("c2", [category("s1"), category("s2")], [edge("e1", "s1", "s2"), edge("e1", "s2", "s1")], kind="context")),
                save_outcome(model, graph("c3", [category("s1")], [edge("e1", "s1", "ghost")], kind="context")),
            ]
            # And: nothing is written
            out.append(("stored", version_counts(store)))
            return out
        empty = {t: {} for t in ("graph_nodes", "graph_edges", "context_nodes", "context_edges", "graphs")}
        # Then: the repeated step s1, the repeated connection e1 and the connection e1 to the missing step are named
        self.on_both(run, [(False, None, ["s1"], None, None), (False, None, ["e1"], None, None), (False, None, ["e1"], None, None),
                           ("stored", empty)])

    @mark.req("REQ-GTB-032", "REQ-WFM-160")
    def test_graph_id_with_slash_refused_alike(self):
        """TC-GTB-036 (cases of TC-WFM-178): the graph IDs `look/up`, `/lookup` and the empty ID are refused the same way on both stores.
        Example: `look/up` with the step `a` -> unscoped_id naming `look/up/a`; the empty ID with the step `a` -> unscoped_id naming `/a` (D-410)."""
        def run(store):
            model = graph_model.GraphModel(store, author=WHO)
            # Given: an empty store; When: a graph of one step is saved under `look/up`, `/lookup` and the empty ID
            out = [save_outcome(model, graph("look/up", [transform("a")], [])),
                   save_outcome(model, graph("/lookup", [transform("a")], [])),
                   save_outcome(model, graph("", [transform("a")], []))]
            # And: nothing is stored for them
            out.append(("stored", version_counts(store)))
            return out
        empty = {t: {} for t in ("graph_nodes", "graph_edges", "context_nodes", "context_edges", "graphs")}
        # Then: `look/up/a` splits at the first slash into graph `look`, not `look/up`; `/lookup/a` has an empty graph part: both unscoped_id;
        #       `/a` (the step of the graph with the empty ID) has an empty graph part as well (D-410: the graph ID is caught through its steps)
        self.on_both(run, [(False, None, [], "unscoped_id", "look/up/a"), (False, None, [], "unscoped_id", "/lookup/a"),
                           (False, None, [], "unscoped_id", "/a"), ("stored", empty)])


if __name__ == "__main__":
    unittest.main()
