"""
Acceptance tests of the graph records (N-3.2 Graph tables, G-V2.STORE): TC-GTB-006 to TC-GTB-021 (REQ-GTB-005 to REQ-GTB-020), written through the
storage stand-in of tests/helpers/graph_store_standin.py, which passes the IF-102 suite first (TR-GTB-002, checked in setUpModule).
Expected values are written by hand (TR-GTB-001). Run with: python tests/acceptance/test_graph_records.py
TC-GTB-014 runs the seeds 1 to N, N from the environment variable TC_GTB_014_N (default 1000, TR-GTB-004).
"""

import ast
import hashlib
import importlib.metadata
import json
import os
import random
import subprocess
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
sys.path.append(os.path.join(REPO, "tests", "helpers", "mocks"))   # appended: the mocks have their own graph_rules

import jsonschema                                                        # noqa: E402
from markers import mark                                                 # noqa: E402
from errors import StorageError                                          # noqa: E402
from graph_store_standin import GraphStoreStandIn, if_102_suite_problems  # noqa: E402
from if_102_storage import StorageMock                                   # noqa: E402
import graph_tables                                                      # noqa: E402

WHO = "anna"
RECORD_TABLES = {t: {"versioned": True, "deletable": False} for t in ("graph_nodes", "graph_edges", "graphs", "skills")}
NODE_TYPES = ["data", "master", "transform"]


def setUpModule():
    """TR-GTB-002: the storage under the checks passes the IF-102 contract suite before any check runs."""
    problems = if_102_suite_problems(GraphStoreStandIn)
    if problems:
        raise AssertionError("the storage stand-in does not pass IF-102: %s" % problems[:3])


def node(node_id, type_id, **fields):
    return {"id": node_id, "data": dict({"type": type_id}, **fields)}


def edge(edge_id, start, end, **data):
    return {"id": edge_id, "from": start, "to": end, "data": data}


def header(graph_id, nodes, edges, description="a test graph"):
    """A graph header whose members are given as (id, version) pairs."""
    return {"id": graph_id, "data": {"kind": "workflow", "context_graph_id": "ctx-" + graph_id, "testbench_id": "", "description": description,
                                     "nodes": [{"id": i, "version": v} for i, v in nodes], "edges": [{"id": i, "version": v} for i, v in edges]}}


def new_store(test):
    """A fresh storage stand-in; the Given of every check is that the Graph tables define the four record tables."""
    test.assertEqual(graph_tables.record_definitions(), RECORD_TABLES)
    return GraphStoreStandIn()


def snapshot(store):
    """Everything in the stand-in: table -> id -> number of versions (a refused write must not change it)."""
    return {t: {i: len(vs) for i, vs in rows.items()} for t, rows in store._rows.items()}


def refusal(test, store, table, record_id, record):
    """Writes a record that must be refused; returns (rule, detail) of the refusal and checks that nothing in the store changed."""
    before = snapshot(store)
    with test.assertRaises(StorageError) as caught:
        store.put(table, record_id, record, WHO)
    test.assertEqual(caught.exception.code, "invalid")
    test.assertEqual(snapshot(store), before)
    return caught.exception.rule, caught.exception.detail


class GraphRecordAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-005", "FR-40")
    def test_a_node_of_each_type_is_stored_as_a_record(self):
        """TC-GTB-016: one node of each registered type is written and read back with the same ID and the same JSON field, which holds its type.

        Example: {"id": "t1", "data": {"type": "transform", "toolbox_id": "t-demo"}} -> read back equal, data["type"] == "transform".
        """
        # Given: the registered types are data, master and transform; one node of each, with an ID and a JSON field that holds its type
        store = new_store(self)
        self.assertEqual(list(graph_tables.types()), NODE_TYPES)
        records = [node("d1", "data", value=7, parameters={"k": 1}), node("t1", "transform", toolbox_id="t-demo"),
                   node("m1", "master", toolbox_id="t-lead", stop={"max_repetitions": 3})]
        for record in records:
            # When: each is written and read back
            self.assertEqual(store.put("graph_nodes", record["id"], record, WHO), {"version": 1})
            read = store.get("graph_nodes", record["id"])
            # Then: the ID and the JSON field are the same as written
            self.assertEqual((read["doc"]["id"], read["doc"]["data"]), (record["id"], record["data"]))
            # And: the type is present in the JSON field
            self.assertEqual(read["doc"]["data"]["type"], record["data"]["type"])

    @mark.req("REQ-GTB-006")
    def test_an_edge_is_stored_as_a_record(self):
        """TC-GTB-006: an edge with an ID, a start node, an end node and a JSON field is read back with the same four fields.

        Example: e1 from n1 to n2 with {"label": "x"} -> {"id": "e1", "from": "n1", "to": "n2", "data": {"label": "x"}}.
        """
        # Given: the nodes n1 and n2 are stored, and the edge e1 with its JSON field
        store = new_store(self)
        store.put("graph_nodes", "n1", node("n1", "data"), WHO)
        store.put("graph_nodes", "n2", node("n2", "data"), WHO)
        # When: the edge is written and read back
        self.assertEqual(store.put("graph_edges", "e1", edge("e1", "n1", "n2", label="x"), WHO), {"version": 1})
        read = store.get("graph_edges", "e1")["doc"]
        # Then: it has the same ID, start node, end node and JSON field
        self.assertEqual(read, {"id": "e1", "from": "n1", "to": "n2", "data": {"label": "x"}})

    @mark.req("REQ-GTB-007")
    def test_a_transform_node_keeps_its_toolbox_id(self):
        """TC-GTB-007: a transform node whose JSON field names the toolbox ID t-demo is read back naming t-demo.

        Example: {"type": "transform", "toolbox_id": "t-demo"} -> the stored record and the rebuilt object both name t-demo.
        """
        # Given: a transform node that names the toolbox ID t-demo
        store = new_store(self)
        store.put("graph_nodes", "t1", node("t1", "transform", toolbox_id="t-demo"), WHO)
        # When: it is read back and rebuilt
        read = store.get("graph_nodes", "t1")["doc"]
        built = graph_tables.to_object(read)
        # Then: the node names t-demo
        self.assertEqual(read["data"]["toolbox_id"], "t-demo")
        self.assertEqual(set(built), {"object"})
        self.assertEqual(built["object"].toolbox_id, "t-demo")

    @mark.req("REQ-GTB-008")
    def test_a_master_node_keeps_its_definition_and_runs_nothing(self):
        """TC-GTB-008: a master node with a task definition and a stopping criterion is read back with both equal, and nothing is run.

        Example: task {"command": "touch <folder>/ran"} and stop {"max_repetitions": 3, "max_seconds": 2.5} -> equal on read, the file `ran` does not exist.
        """
        # Given: a master node whose task would leave a marker file if it were run (a fresh folder, so no earlier run can fake the result)
        folder = tempfile.mkdtemp(prefix="gtb-master-")
        marker = os.path.join(folder, "ran")
        task, stop = {"command": "touch %s" % marker}, {"max_repetitions": 3, "max_seconds": 2.5}
        store = new_store(self)
        store.put("graph_nodes", "m1", node("m1", "master", toolbox_id="t-lead", stop=stop, task=task), WHO)
        # When: it is read back and rebuilt
        read = store.get("graph_nodes", "m1")["doc"]
        built = graph_tables.to_object(read)
        # Then: the definition and the stopping criterion are equal to what was written
        self.assertEqual((read["data"]["task"], read["data"]["stop"]), (task, stop))
        self.assertEqual(set(built), {"object"})
        self.assertEqual((built["object"].task, built["object"].stop), (task, stop))
        # And: nothing was run (the definition is a record only until goal D)
        self.assertFalse(os.path.exists(marker))

    @mark.req("REQ-GTB-009")
    def test_the_class_is_rebuilt_from_the_type_id(self):
        """TC-GTB-009: each stored node is rebuilt as the class registered for its type ID, with equal values.

        Example: stored d1 (data, value 7) and d2 (data) -> two objects of one class; t1 (transform) and m1 (master) -> two other classes.
        """
        # Given: stored nodes of each registered type, two of type data (they must share their class)
        store = new_store(self)
        records = [node("d1", "data", value=7, parameters={"k": 1}), node("d2", "data"), node("t1", "transform", toolbox_id="t-demo"),
                   node("m1", "master", toolbox_id="t-lead", stop={"max_repetitions": 2}, task={"goal": "x"})]
        expected = {"d1": {"value": 7, "parameters": {"k": 1}}, "d2": {"value": None, "parameters": {}},   # an absent parameters is the empty object (contract)
                    "t1": {"toolbox_id": "t-demo"}, "m1": {"toolbox_id": "t-lead", "stop": {"max_repetitions": 2}, "task": {"goal": "x"}}}
        for record in records:
            store.put("graph_nodes", record["id"], record, WHO)
        # When: each is read and rebuilt
        objects = {}
        for record in records:
            built = graph_tables.to_object(store.get("graph_nodes", record["id"])["doc"])
            self.assertEqual(set(built), {"object"})
            objects[record["id"]] = built["object"]
        # Then: the class depends on the type ID alone
        self.assertIs(type(objects["d1"]), type(objects["d2"]))
        self.assertEqual(len({type(objects[i]) for i in ("d1", "t1", "m1")}), 3)
        # And: the values equal the stored ones
        for node_id, values in expected.items():
            self.assertEqual(objects[node_id].id, node_id)
            for name, value in values.items():
                self.assertEqual(getattr(objects[node_id], name), value)

    @mark.req("REQ-GTB-010")
    def test_an_unknown_type_is_refused_when_written_and_when_read(self):
        """TC-GTB-010: a node with the type ID x.unknown is refused as a write and as a record already in storage, both naming x.unknown.

        Example: {"id": "u1", "data": {"type": "x.unknown"}} -> write refused (unknown_type, x.unknown); read gives {"refused": unknown_type, x.unknown}.
        """
        # Given: a good node already stored, and a node of the type x.unknown
        store = new_store(self)
        store.put("graph_nodes", "ok", node("ok", "transform", toolbox_id="t"), WHO)
        record = node("u1", "x.unknown")
        # When: it is written
        rule = refusal(self, store, "graph_nodes", "u1", record)
        # Then: the write is refused and the message names x.unknown (no other record changed: refusal() compares the whole store)
        self.assertEqual(rule, ("unknown_type", "x.unknown"))
        # When: the same record is present in storage (put past the check, as a record written by an older or damaged writer) and is read
        StorageMock.put(store, "graph_nodes", "u1", record, WHO)
        built = graph_tables.to_object(store.get("graph_nodes", "u1")["doc"])
        # Then: the read is refused and the message names x.unknown
        self.assertEqual(built, {"refused": {"rule": "unknown_type", "detail": "x.unknown"}})
        # And: the other record is as before
        self.assertEqual(store.get("graph_nodes", "ok")["version"], 1)

    @mark.req("REQ-GTB-011")
    def test_a_field_that_breaks_its_schema_is_refused_naming_its_path(self):
        """TC-GTB-011: a node and an edge, each with one field that breaks its schema, are refused on write and the message names the path of the field.

        Example: transform without toolbox_id -> schema_break "toolbox_id"; transform with toolbox_id 5 -> "toolbox_id"; edge with data "x" -> "data".
        """
        # Given: two stored nodes for the edge to join, and one broken record each (top-level fields: the path is the key as the validator names it)
        store = new_store(self)
        store.put("graph_nodes", "n1", node("n1", "data"), WHO)
        store.put("graph_nodes", "n2", node("n2", "data"), WHO)
        cases = [("graph_nodes", node("t1", "transform"), "toolbox_id"),                # a required key is missing
                 ("graph_nodes", node("t1", "transform", toolbox_id=5), "toolbox_id"),  # a value of the wrong kind
                 ("graph_edges", {"id": "e1", "from": "n1", "to": "n2", "data": "x"}, "data")]   # the JSON field of an edge must be an object
        for table, record, path in cases:
            with self.subTest(record=record):
                # When/Then: each write is refused as schema_break and names the path of the broken field
                self.assertEqual(refusal(self, store, table, record["id"], record), ("schema_break", path))

    @mark.req("REQ-GTB-011")
    def test_the_paths_are_those_of_the_pinned_validator(self):
        """TC-GTB-011 setup (TR-GTB-003): jsonschema is 4.23.0 as on the host, and it names a wrong value by its key and a missing key as required.

        Example: schema with required text toolbox_id: {"toolbox_id": 5} -> path ["toolbox_id"]; {} -> "'toolbox_id' is a required property".
        """
        # Given: the validator the Graph tables must use, and a minimal schema of the shape of a transform node
        self.assertEqual(importlib.metadata.version("jsonschema"), "4.23.0")
        schema = {"type": "object", "properties": {"toolbox_id": {"type": "string"}}, "required": ["toolbox_id"]}
        validator = jsonschema.Draft202012Validator(schema)
        # When: a wrong value and a missing key are validated
        wrong, = list(validator.iter_errors({"toolbox_id": 5}))
        missing, = list(validator.iter_errors({}))
        # Then: the wrong value is named by its key; the missing key is named by the message of the validator, which the detail of schema_break repeats
        self.assertEqual(list(wrong.absolute_path), ["toolbox_id"])
        self.assertEqual((list(missing.absolute_path), missing.message), ([], "'toolbox_id' is a required property"))

    @mark.req("REQ-GTB-013", "FR-40")
    def test_an_edit_is_a_new_version(self):
        """TC-GTB-013: after an edit of a node, an edge and the whole graph, the new version exists and the one before is unchanged; all earlier versions can still be read.

        Example: node n1 toolbox "t-old" -> "t-new": versions [1, 2], version 1 still names "t-old".
        """
        # Given: a stored graph at version 1 (two nodes, an edge, the header)
        store = new_store(self)
        n1, n2, e1 = node("n1", "transform", toolbox_id="t-old"), node("n2", "data"), edge("e1", "n1", "n2", label="a")
        wf1 = header("wf1", [("n1", 1), ("n2", 1)], [("e1", 1)])
        for table, record in (("graph_nodes", n1), ("graph_nodes", n2), ("graph_edges", e1), ("graphs", wf1)):
            self.assertEqual(store.put(table, record["id"], record, WHO), {"version": 1})
        # When: one node is edited, then one edge, then the whole graph
        n1b, e1b = node("n1", "transform", toolbox_id="t-new"), edge("e1", "n1", "n2", label="b")
        wf1b = header("wf1", [("n1", 2), ("n2", 1)], [("e1", 2)], description="edited")
        edits = [("graph_nodes", n1, n1b), ("graph_edges", e1, e1b), ("graphs", wf1, wf1b)]
        for table, before, after in edits:
            self.assertEqual(store.put(table, after["id"], after, WHO), {"version": 2})
            # Then: versions 1 and 2 both exist and version 1 is unchanged
            self.assertEqual([h["version"] for h in store.history(table, after["id"])], [1, 2])
            self.assertEqual(store.get(table, after["id"], version=1)["doc"], before)
            self.assertEqual(store.get(table, after["id"])["doc"], after)
        # And: all earlier versions can still be read after the last edit
        for table, before, _ in edits:
            self.assertEqual(store.get(table, before["id"], version=1)["doc"], before)
        # And: no record of these tables can be deleted
        for table, before, _ in edits:
            with self.assertRaises(StorageError) as caught:
                store.delete(table, before["id"], WHO)
            self.assertEqual(caught.exception.code, "immutable")

    @mark.req("REQ-GTB-016")
    def test_a_refused_edit_changes_nothing(self):
        """TC-GTB-017: an edit that breaks a check (unknown type, schema break, an ID that already exists) is refused; the latest version stays 1 with its content.

        Example: node n1 edited to type x.unknown -> refused; version 1 of n1 is still the latest and no version 2 exists.
        """
        # Given: a stored graph at version 1, and one breaking edit each of a node, an edge and the whole graph
        store = new_store(self)
        n1, n2, e1 = node("n1", "transform", toolbox_id="t"), node("n2", "data"), edge("e1", "n1", "n2", label="a")
        wf1 = header("wf1", [("n1", 1), ("n2", 1)], [("e1", 1)])
        stored = [("graph_nodes", n1), ("graph_nodes", n2), ("graph_edges", e1), ("graphs", wf1)]
        for table, record in stored:
            store.put(table, record["id"], record, WHO)
        edits = [("graph_nodes", "n1", node("n1", "x.unknown")),                                     # an unknown type
                 ("graph_edges", "e1", {"id": "e1", "from": "n1", "to": "n2", "data": "x"}),         # a field that breaks its schema
                 ("graphs", "wf1", header("wf1", [("n1", 1), ("n1", 1)], [("e1", 1)]))]              # an ID that is already a member of the graph
        for table, record_id, record in edits:
            with self.subTest(table=table):
                # When: the edit is made; Then: it is refused (refusal() also checks that no table changed)
                before = snapshot(store)
                refusal(self, store, table, record_id, record)
                # And: the latest version is still 1, its content is unchanged and no version 2 exists
                self.assertEqual([h["version"] for h in store.history(table, record_id)], [1])
                original = [r for t, r in stored if t == table and r["id"] == record_id][0]
                self.assertEqual(store.get(table, record_id)["doc"], original)
                with self.assertRaises(StorageError) as caught:
                    store.get(table, record_id, version=2)
                self.assertEqual(caught.exception.code, "not_found")
                self.assertEqual(snapshot(store), before)

    @mark.req("REQ-GTB-017")
    def test_a_graph_version_pins_its_members(self):
        """TC-GTB-018: header version 1 still reads node n1 at version 1 with its old content after n1 was edited; header version 2 reads n1 at version 2.

        Example: n1 toolbox "t-old" (version 1) -> "t-new" (version 2); header version 1 -> n1 at version 1 names "t-old".
        """
        # Given: a header wf1 (kind workflow, context graph, empty testbench ID, description) naming n1, n2 and e1, each at version 1
        store = new_store(self)
        n1, n2, e1 = node("n1", "transform", toolbox_id="t-old"), node("n2", "data"), edge("e1", "n1", "n2")
        wf_v1 = header("wf1", [("n1", 1), ("n2", 1)], [("e1", 1)])
        for table, record in (("graph_nodes", n1), ("graph_nodes", n2), ("graph_edges", e1)):
            store.put(table, record["id"], record, WHO)
        # When: the header is stored and read back
        store.put("graphs", "wf1", wf_v1, WHO)
        # Then: the first read equals what was stored
        self.assertEqual(store.get("graphs", "wf1")["doc"], wf_v1)
        # When: n1 is edited (version 2) and a second header version naming n1 at version 2 is stored
        n1_v2 = node("n1", "transform", toolbox_id="t-new")
        self.assertEqual(store.put("graph_nodes", "n1", n1_v2, WHO), {"version": 2})
        wf_v2 = header("wf1", [("n1", 2), ("n2", 1)], [("e1", 1)])
        self.assertEqual(store.put("graphs", "wf1", wf_v2, WHO), {"version": 2})

        def members(version):
            """The nodes of a header version as the header pins them."""
            pinned = store.get("graphs", "wf1", version=version)["doc"]["data"]["nodes"]
            return {m["id"]: (m["version"], store.get("graph_nodes", m["id"], version=m["version"])["doc"]) for m in pinned}
        # And: header version 1 still reads n1 at version 1 with its old content
        self.assertEqual(members(1), {"n1": (1, n1), "n2": (1, n2)})
        # And: header version 2 reads n1 at version 2; the other members are the same as in version 1
        self.assertEqual(members(2), {"n1": (2, n1_v2), "n2": (1, n2)})
        self.assertEqual(store.get("graphs", "wf1", version=2)["doc"]["data"]["edges"], [{"id": "e1", "version": 1}])

    @mark.req("REQ-GTB-018")
    def test_a_skill_is_stored_as_a_versioned_record(self):
        """TC-GTB-019: a skill is read back with its four fields; editing its context graph ID is version 2 with version 1 unchanged; a record without a command is refused naming command.

        Example: lookup, /lookup, wf-lookup, ctx-a -> edited to ctx-b gives version 2; a skill without command -> schema_break "command".
        """
        # Given: a skill with ID lookup, command /lookup, a workflow graph ID and a context graph ID
        store = new_store(self)
        v1 = {"id": "lookup", "data": {"command": "/lookup", "workflow_graph_id": "wf-lookup", "context_graph_id": "ctx-a"}}
        # When: it is stored and read back
        self.assertEqual(store.put("skills", "lookup", v1, WHO), {"version": 1})
        # Then: the first read has the same four fields
        self.assertEqual(store.get("skills", "lookup")["doc"], v1)
        # When: its context graph ID is edited and stored
        v2 = {"id": "lookup", "data": {"command": "/lookup", "workflow_graph_id": "wf-lookup", "context_graph_id": "ctx-b"}}
        self.assertEqual(store.put("skills", "lookup", v2, WHO), {"version": 2})
        # Then: the edit is version 2 and version 1 is unchanged
        self.assertEqual(store.get("skills", "lookup", version=2)["doc"], v2)
        self.assertEqual(store.get("skills", "lookup", version=1)["doc"], v1)
        # When: a record without a command is stored; Then: it is refused and names command
        no_command = {"id": "review", "data": {"workflow_graph_id": "wf-review", "context_graph_id": "ctx-r"}}
        self.assertEqual(refusal(self, store, "skills", "review", no_command), ("schema_break", "command"))

    @mark.req("REQ-GTB-019")
    def test_a_header_with_a_missing_member_is_refused(self):
        """TC-GTB-020: a header naming n1 at version 5 when n1 has versions 1 and 2 is refused naming n1; the same header naming version 2 is accepted.

        Example: n1 versions [1, 2]; member {"id": "n1", "version": 5} -> unknown_member "n1"; version 2 -> stored as header version 1.
        """
        # Given: node n1 stored with versions 1 and 2
        store = new_store(self)
        store.put("graph_nodes", "n1", node("n1", "transform", toolbox_id="a"), WHO)
        store.put("graph_nodes", "n1", node("n1", "transform", toolbox_id="b"), WHO)
        # When: a header naming n1 at version 5 is stored; Then: it is refused and names n1
        self.assertEqual(refusal(self, store, "graphs", "wf1", header("wf1", [("n1", 5)], [])), ("unknown_member", "n1"))
        # When: the same header naming version 2 is stored; Then: it is accepted (the twin differs only in the broken rule)
        self.assertEqual(store.put("graphs", "wf1", header("wf1", [("n1", 2)], []), WHO), {"version": 1})

    @mark.req("REQ-GTB-020")
    def test_an_edge_to_a_missing_node_is_refused(self):
        """TC-GTB-021: an edge e1 from n1 to n9 with only n1 stored is refused naming n9; the same edge after n9 is stored is accepted.

        Example: stored n1 -> e1 (n1 to n9) refused with unknown_endpoint "n9"; after n9 is stored e1 is stored as version 1.
        """
        # Given: node n1 stored and the edge e1 from n1 to n9
        store = new_store(self)
        store.put("graph_nodes", "n1", node("n1", "data"), WHO)
        record = edge("e1", "n1", "n9", label="x")
        # When: the edge is stored; Then: it is refused and names n9
        self.assertEqual(refusal(self, store, "graph_edges", "e1", record), ("unknown_endpoint", "n9"))
        # When: n9 is stored and the same edge again; Then: it is accepted (the twin differs only in the broken rule)
        store.put("graph_nodes", "n9", node("n9", "data"), WHO)
        self.assertEqual(store.put("graph_edges", "e1", record, WHO), {"version": 1})


class StorageStandInAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-005")
    def test_the_storage_standin_passes_the_if_102_suite(self):
        """TC-GTB-016 setup (TR-GTB-002): the stand-in that stores the records passes the stage 1 cases of the IF-102 contract suite.

        Example: the 11 `_mock` cases of test_if_102_storage.py run with GraphStoreStandIn as the provider -> no failure, error or skip.
        """
        # Given: the stand-in; When: the IF-102 cases run with it as the provider
        problems = if_102_suite_problems(GraphStoreStandIn)
        # Then: nothing failed, nothing was skipped, and the suite did run
        self.assertEqual(problems, [])


MODULES_OF_THE_GRAPH_TABLES = ("graph_tables.py",)
BANNED = ("pickle", "marshal", "shelve")


def banned_imports(path):
    """The imports of pickle, marshal or shelve in the syntax tree of a module, also inside a function: a list of (line, name)."""
    found = []
    with open(path) as handle:
        tree = ast.parse(handle.read(), path)
    for item in ast.walk(tree):
        names = [a.name for a in item.names] if isinstance(item, ast.Import) else [item.module or ""] if isinstance(item, ast.ImportFrom) and not item.level else []
        found += [(item.lineno, name) for name in names if name.split(".")[0] in BANNED]
    return found


def local_imports(path):
    """The repository modules a module imports (plain or relative), so every module that the Graph tables use is inspected."""
    with open(path) as handle:
        tree = ast.parse(handle.read(), path)
    names = set()
    for item in ast.walk(tree):
        if isinstance(item, ast.Import):
            names |= {a.name.split(".")[0] for a in item.names}
        elif isinstance(item, ast.ImportFrom):
            names |= {item.module.split(".")[0]} if item.module else {a.name for a in item.names}
    return {n for n in names if os.path.exists(os.path.join(REPO, n + ".py"))}


def graph_table_modules():
    """graph_tables.py and, transitively, every repository module it imports."""
    todo, seen = ["graph_tables"], set()
    while todo:
        name = todo.pop()
        if name not in seen:
            seen.add(name)
            todo += sorted(local_imports(os.path.join(REPO, name + ".py")))
    return [os.path.join(REPO, n + ".py") for n in sorted(seen)]


class InspectionAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-012")
    def test_no_module_of_the_graph_tables_imports_a_language_specific_serialiser(self):
        """TC-GTB-012: no module of the Graph tables imports pickle, marshal or shelve, and the inspection does report a module that does.

        Example: graph_tables.py and the modules it imports -> no import found; a temporary module with `import pickle` -> reported.
        """
        # Given: the source of every module of the Graph tables, and a test module that imports pickle
        modules = graph_table_modules()
        self.assertIn(os.path.join(REPO, "graph_tables.py"), modules)
        folder = tempfile.mkdtemp(prefix="gtb-inspect-")
        bad = os.path.join(folder, "bad_module.py")
        with open(bad, "w") as handle:
            handle.write("import pickle\n")
        # When: the inspection reads the syntax trees
        found = {path: banned_imports(path) for path in modules}
        # Then: it finds no import of pickle, marshal or shelve in the Graph tables
        self.assertEqual({p: f for p, f in found.items() if f}, {})
        # And: it does report the test module (the inspection can fail)
        self.assertEqual(banned_imports(bad), [(1, "pickle")])

    @mark.req("REQ-GTB-012")
    def test_the_inspection_sees_each_banned_import_also_inside_a_function(self):
        """TC-GTB-012 setup (TR-GTB-005): the inspection reports pickle, marshal and shelve in every import form, also inside a function, and nothing in a clean module.

        Example: `def f(): import shelve` -> [(2, "shelve")]; `import json` -> [].
        """
        # Given: modules that import each banned name in a different way, and a clean one
        sources = {"top.py": ("import pickle\n", [(1, "pickle")]),
                   "marshal_from.py": ("from marshal import dumps\n", [(1, "marshal")]),
                   "alias.py": ("import shelve as s\n", [(1, "shelve")]),
                   "inside.py": ("def f():\n    import shelve\n", [(2, "shelve")]),
                   "nested.py": ("def f():\n    def g():\n        from pickle import loads\n", [(3, "pickle")]),
                   "dotted.py": ("import pickle.x\n", [(1, "pickle.x")]),
                   "clean.py": ("import json\nfrom os import path\n", [])}
        folder = tempfile.mkdtemp(prefix="gtb-inspect-")
        for name, (source, expected) in sources.items():
            path = os.path.join(folder, name)
            with open(path, "w") as handle:
                handle.write(source)
            with self.subTest(module=name):
                # When/Then: the inspection reports exactly the banned imports, with their line
                self.assertEqual(banned_imports(path), expected)


def generated_graph(seed):
    """A graph of 1 to 20 nodes of the three types and up to 40 edges between them, made from the seed alone (TR-GTB-004)."""
    rnd = random.Random(seed)
    nodes = []
    for i in range(rnd.randint(1, 20)):
        kind = rnd.choice(NODE_TYPES)
        if kind == "data":
            fields = {"value": rnd.choice([rnd.randint(-5, 5), "v%d" % i, [1, "a"], {"k": i}, 1.5, True]), "parameters": {"p": rnd.randint(0, 3)}}
        elif kind == "transform":
            fields = {"toolbox_id": "t%d" % rnd.randint(0, 5)}
        else:
            stop = {}
            if rnd.random() < 0.7:
                stop["max_repetitions"] = rnd.randint(1, 9)
            if not stop or rnd.random() < 0.5:
                stop["max_seconds"] = rnd.randint(1, 9) / 2
            fields = {"toolbox_id": "t%d" % rnd.randint(0, 5), "stop": stop}
            if rnd.random() < 0.5:
                fields["task"] = {"goal": "g%d" % i}
        nodes.append(node("n%d" % i, kind, **fields))
    edges = [edge("e%d" % i, rnd.choice(nodes)["id"], rnd.choice(nodes)["id"], **({"label": "l%d" % i} if rnd.random() < 0.5 else {}))
             for i in range(rnd.randint(0, 40))]
    members = header("g%d" % seed, [(n["id"], 1) for n in nodes], [(e["id"], 1) for e in edges])
    return nodes, edges, members


def round_trip_failures(seeds, store_class=GraphStoreStandIn):
    """Writes, reads and rebuilds the generated graph of each seed; returns [(seed, reason, graph)] for every seed whose graph came back different."""
    failures = []
    for seed in seeds:
        nodes, edges, members = generated_graph(seed)
        store, reason = store_class(), None
        for table, record in [("graph_nodes", n) for n in nodes] + [("graph_edges", e) for e in edges] + [("graphs", members)]:
            store.put(table, record["id"], record, WHO)
        for table, record in [("graph_nodes", n) for n in nodes] + [("graph_edges", e) for e in edges] + [("graphs", members)]:
            if store.get(table, record["id"])["doc"] != record:
                reason = "stored %s %s differs" % (table, record["id"])
                break
        if reason is None:
            for original in nodes:
                built = graph_tables.to_object(store.get("graph_nodes", original["id"])["doc"])
                if set(built) != {"object"} or graph_tables.to_record(built["object"]) != original:
                    reason = "rebuilt node %s differs" % original["id"]
                    break
        if reason:
            failures.append((seed, reason, {"nodes": nodes, "edges": edges, "header": members}))
    return failures


class DroppingTheTask(GraphStoreStandIn):
    """A deliberately broken writer (mutation): it loses the task of a master node when it stores it."""

    def put(self, table, record_id, doc, author, expected_version=None, categories=None):
        if table == "graph_nodes" and "task" in doc["data"]:
            doc = {"id": doc["id"], "data": {k: v for k, v in doc["data"].items() if k != "task"}}
        return super().put(table, record_id, doc, author, expected_version, categories)


class GeneratedGraphAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-014", "FR-40")
    def test_a_stored_graph_is_rebuilt_equal(self):
        """TC-GTB-014: N generated graphs (seeds 1 to N, default 1000) of the three node types are written, read and rebuilt equal to what was stored.

        Example: seed 1 -> its nodes, edges and header come back with the same IDs, types, fields and edge ends; a failing seed is reported with its graph.
        """
        # Given: the seeds 1 to N (N from TC_GTB_014_N, default 1000)
        n = int(os.environ.get("TC_GTB_014_N", "1000"))
        # When: each graph is written, read and rebuilt
        failures = round_trip_failures(range(1, n + 1))
        # Then: every rebuilt graph equals the stored one
        # And: a failing seed is reported with its graph, so it can be replayed (the first three are shown)
        report = "\n".join("seed %d: %s\n  %s" % (seed, reason, json.dumps(graph)) for seed, reason, graph in failures[:3])
        self.assertEqual(len(failures), 0, "%d of %d seeds failed; first:\n%s" % (len(failures), n, report))

    @mark.req("REQ-GTB-014")
    def test_the_round_trip_check_can_fail(self):
        """TC-GTB-014 setup (TR-GTB-004): a writer that loses the task of master nodes is caught by the check, with its seed and graph; the generator keeps its bounds.

        Example: seeds 1 to 50 with a writer that drops `task` -> at least one failing seed whose reason names the stored node.
        """
        # Given: a deliberately broken writer and the seeds 1 to 50 (enough master nodes with a task, see the bounds below)
        # When: the check runs with it
        failures = round_trip_failures(range(1, 51), store_class=DroppingTheTask)
        # Then: it reports a failing seed with its graph for every graph that has a master node with a task, found at the stored form
        # (independent of the code under test: whatever else fails in the rebuild comes on top of these)
        with_task = [(seed, reason, graph) for seed, reason, graph in failures if any("task" in n["data"] for n in graph["nodes"])]
        self.assertGreater(len(with_task), 0)
        self.assertTrue(all(reason.startswith("stored graph_nodes") for _, reason, _ in with_task))
        # And: the generator keeps the sizes of TR-GTB-004 and uses all three types over the seeds
        sizes = [generated_graph(seed) for seed in range(1, 201)]
        self.assertTrue(all(1 <= len(g[0]) <= 20 and len(g[1]) <= 40 for g in sizes))
        self.assertEqual({n["data"]["type"] for g in sizes for n in g[0]}, set(NODE_TYPES))


V1_SUITES = {"tests/acceptance/contract/test_if_301_graph_tables.py": "1d9022ca5df24312b4209d3d7bdf1d74fe89cec898c0602461487a1621e5606b",
             "tests/acceptance/contract/test_if_203_workflow_library.py": "0eb58da6f0a808c589e6c25c6f40b56472f7d0ba28fd807f0493811b8a9214c3"}


class DocumentFormAcceptance(unittest.TestCase):
    @mark.req("REQ-GTB-015")
    def test_the_document_form_still_works(self):
        """TC-GTB-015: with graphs held as records, the IF-301 v1 and IF-203 v0 suites pass, and their files are those from before A-90.

        Example: the v1 lookup-style document -> records -> document gives back the same document; both suite files match their recorded sha256.
        """
        # Given: the contract suites of IF-301 v1 and IF-203 v0 (sha256 recorded 2026-11-07 before A-90), and a v1 graph held as records
        doc = {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process"}, {"id": "a", "kind": "data"}],
               "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "a"}]}
        records = graph_tables.from_document(doc)
        self.assertEqual([n["data"]["type"] for n in records.get("nodes", [])], ["data", "transform", "data"])
        # When: the records are written back as a document, and both suites run (each in its own process, from the files as they are)
        back = graph_tables.to_document(records.get("nodes", []), records.get("edges", []))
        results = {}
        for path in V1_SUITES:
            run = subprocess.run([sys.executable, os.path.join(REPO, path)], cwd=REPO, capture_output=True, text=True, timeout=600)
            results[path] = (run.returncode, run.stderr.strip().splitlines()[-1] if run.stderr.strip() else "")
        # Then: both pass, and the document is the one that went in
        self.assertEqual(set(back), {"document"})
        self.assertEqual([(n["id"], n["kind"]) for n in back["document"]["nodes"]], [(n["id"], n["kind"]) for n in doc["nodes"]])
        self.assertEqual([(e["from"], e["to"]) for e in back["document"]["edges"]], [(e["from"], e["to"]) for e in doc["edges"]])
        self.assertEqual({p: r[0] for p, r in results.items()}, {p: 0 for p in V1_SUITES}, results)
        # And: the suite files are the ones from before A-90 (no edit): a changed file fails here whatever its suite says
        for path, recorded in V1_SUITES.items():
            with open(os.path.join(REPO, path), "rb") as handle:
                self.assertEqual(hashlib.sha256(handle.read()).hexdigest(), recorded, path)


if __name__ == "__main__":
    unittest.main()
