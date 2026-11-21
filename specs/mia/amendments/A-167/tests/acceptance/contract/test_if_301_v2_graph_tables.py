"""IF-301 v2 graph tables (record tables, types, record checks, conversion; A-90): the contract suite runs against the mock (stage 1, green) and the
real Graph tables (stage 2; no skip since A-91, N-3.2 integrated). The v1 cases stay in test_if_301_graph_tables.py (unchanged).
Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_301_v2_graph_tables.py
"""
import copy
import os
import sys
import threading
import time
import unittest

import jsonschema

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider  # noqa: E402
import contract as contract_module            # noqa: E402  (for the real provider, loaded with the real graph rules)
from markers import mark                      # noqa: E402

IF = "IF-301"
NODE_RECORD_TABLES = {t: {"versioned": True, "deletable": False}
                      for t in ("graph_nodes", "graph_edges", "graphs", "skills", "context_nodes", "context_edges")}


def subject(kind):
    """The provider of this suite: the v2 mock, or the real Graph tables (A-91: no skip, N-3.2 is integrated)."""
    if kind == "mock":
        from if_301_graph_tables_v2 import GraphTablesV2Mock
        return GraphTablesV2Mock()
    return contract_module._real_graph_tables()


def node(node_id, type_id, **fields):
    return {"id": node_id, "data": dict({"type": type_id}, **fields)}


def edge(edge_id, start, end, **data):
    return {"id": edge_id, "from": start, "to": end, "data": data}


@contract
class GraphTablesV2Contract(unittest.TestCase):
    @mark.req("IF-301", "REQ-GTB-001", "REQ-GTB-013")
    @each_provider(IF, make=subject)
    def test_the_record_tables_are_versioned_and_not_deletable(self, tables):
        """TC-IF-301-05: definitions() stays the two tables of v1; record_definitions() lists the six record tables, versioned, not deletable.

        Example: record_definitions() -> graph_nodes, graph_edges, graphs, skills, context_nodes, context_edges, each {"versioned": True, "deletable": False}.
        """
        # Given: the provider; When: both definitions are read; Then: v1 is unchanged and the six tables are added in their own operation
        self.assertEqual(tables.definitions(), {"workflows": {"versioned": True, "deletable": False}, "context_graphs": {"versioned": True, "deletable": False}})
        self.assertEqual(tables.record_definitions(), NODE_RECORD_TABLES)

    @mark.req("IF-301", "REQ-GTB-009", "REQ-GTB-011")
    @each_provider(IF, make=subject)
    def test_the_fixed_list_of_types(self, tables):
        """TC-IF-301-06: types() lists data, master and transform, sorted, each with a JSON schema that is itself valid.

        Example: list(types()) -> ["data", "master", "transform"].
        """
        # When: the list is read
        listed = tables.types()
        # Then: exactly these three type IDs in sorted order
        self.assertEqual(list(listed), ["data", "master", "transform"])
        # And: each schema is a valid JSON schema (the validator decides, TR-GTB-003)
        for type_id, schema in listed.items():
            with self.subTest(type=type_id):
                jsonschema.Draft202012Validator.check_schema(schema)

    @mark.req("IF-301", "REQ-GTB-007", "REQ-GTB-008", "REQ-GTB-009", "REQ-GTB-014")
    @each_provider(IF, make=subject)
    def test_a_known_type_with_a_fitting_field_is_accepted_and_rebuilt(self, tables):
        """TC-IF-301-07 golden 1: a record of each type with a fitting field gives None; to_object returns an object with equal values; to_record returns the record.

        Example: {"id": "g/t1", "data": {"type": "transform", "toolbox_id": "t-demo"}} -> None; the object has id g/t1 and toolbox_id t-demo.
        """
        # Given: one record of each type, written by hand (the master one with a task and a stopping criterion)
        records = {"data": node("g/d1", "data", value=7, parameters={"k": 1}),
                   "transform": node("g/t1", "transform", toolbox_id="t-demo"),
                   "master": node("g/m1", "master", toolbox_id="t-lead", stop={"max_repetitions": 3, "max_seconds": 2.5}, task={"goal": "x"})}
        expected = {"data": {"id": "g/d1", "value": 7, "parameters": {"k": 1}},
                    "transform": {"id": "g/t1", "toolbox_id": "t-demo"},
                    "master": {"id": "g/m1", "toolbox_id": "t-lead", "stop": {"max_repetitions": 3, "max_seconds": 2.5}, "task": {"goal": "x"}}}
        classes = set()
        for type_id, record in records.items():
            with self.subTest(type=type_id):
                # When: the record is checked and rebuilt
                self.assertIsNone(tables.check_record("graph_nodes", record))
                built = tables.to_object(record)
                # Then: an object whose attributes equal the stored values
                self.assertEqual(set(built), {"object"})
                obj = built["object"]
                for name, value in expected[type_id].items():
                    self.assertEqual(getattr(obj, name), value)
                classes.add(type(obj))
                # And: the object gives the record back, and the record gives an equal object
                self.assertEqual(tables.to_record(obj), record)
                self.assertEqual(tables.to_object(tables.to_record(obj)), built)
        # And: one class per type ID
        self.assertEqual(len(classes), 3)

    @mark.req("IF-301", "REQ-GTB-023", "REQ-GTB-024", "REQ-GTB-025", "REQ-GTB-026")
    @each_provider(IF, make=subject)
    def test_the_context_tables_are_checked(self, tables):
        """TC-IF-301-22 golden 17 to 19: context_nodes and context_edges check the shape, the ends of an edge and the members of a context header in the context tables.

        Example: {"id": "h1/c1", "data": {}} as context_nodes -> schema_break "type"; an edge to h1/c9 with only h1/c1 stored -> unknown_endpoint "h1/c9".
        """
        # Given: a stored context node h1/c1, and the shapes of the context records
        stored = {"context_nodes": {"h1/c1": [1]}}
        entity = {"entity": {"type": "object", "properties": {"type": {}, "name": {"type": "string"}}}}

        def header(kind, member):
            return {"id": "h1", "data": {"kind": kind, "context_graph_id": "ctx", "testbench_id": "", "description": "d",
                                         "nodes": [{"id": member, "version": 1}], "edges": []}}
        # When/Then: the six tables are listed, versioned and not deletable
        for table in ("context_nodes", "context_edges"):
            self.assertEqual(tables.record_definitions()[table], {"versioned": True, "deletable": False})
        # And: the shape of a node is checked without categories, the type and schema with them
        self.assertIsNone(tables.check_record("context_nodes", node("h1/c1", "entity")))
        self.assertEqual(tables.check_record("context_nodes", {"id": "h1/c1", "data": {}}), {"rule": "schema_break", "detail": "type"})
        self.assertEqual(tables.check_record("context_nodes", {"id": "h1/c1"}), {"rule": "schema_break", "detail": "data"})
        self.assertEqual(tables.check_record("context_nodes", node("h1/c1", "entity", name=5), categories=entity), {"rule": "schema_break", "detail": "name"})
        self.assertEqual(tables.check_record("context_nodes", node("h1/c1", "other"), categories=entity), {"rule": "unknown_type", "detail": "other"})
        self.assertIsNone(tables.check_record("context_nodes", node("h1/c1", "entity", name="x"), categories=entity))
        # And: an edge needs a text end and stored context nodes as ends; a workflow node does not count
        self.assertEqual(tables.check_record("context_edges", {"id": "h1/e1", "from": "h1/c1", "data": {}}), {"rule": "record_identity", "detail": "to"})
        self.assertEqual(tables.check_record("context_edges", edge("h1/e1", "h1/c1", "h1/c9"), stored=stored), {"rule": "unknown_endpoint", "detail": "h1/c9"})
        self.assertEqual(tables.check_record("context_edges", edge("h1/e1", "h1/c1", "h1/c9"), stored={"nodes": {"h1/c9": [1]}, "context_nodes": {"h1/c1": [1]}}),
                         {"rule": "unknown_endpoint", "detail": "h1/c9"})
        self.assertIsNone(tables.check_record("context_edges", edge("h1/e1", "h1/c1", "h1/c1"), stored=stored))
        # And: a header of kind context looks in the context tables, a header of kind workflow does not
        self.assertEqual(tables.check_record("graphs", header("context", "h1/c9"), stored=stored), {"rule": "unknown_member", "detail": "h1/c9"})
        self.assertEqual(tables.check_record("graphs", header("workflow", "h1/c1"), stored=stored), {"rule": "unknown_member", "detail": "h1/c1"})
        self.assertIsNone(tables.check_record("graphs", header("context", "h1/c1"), stored=stored))

    @mark.req("IF-301", "REQ-GTB-028")
    @each_provider(IF, make=subject)
    def test_a_record_with_too_many_values_is_a_schema_break(self, tables):
        """TC-IF-301-24 golden 21: a record with more than 100 000 values (every path counted) is schema_break naming data, also a record that shares sub-objects (2**30 paths), at once.

        Example: a data node whose value is a list of 99 996 numbers -> {"rule": "schema_break", "detail": "data"}; 99 995 numbers -> None.
        """
        # Given: data nodes whose value is a list of 99 995 and of 99 996 numbers (the record, its id, its data object, its type and the list add 5 values: 100 000 and 100 001),
        # and a record that names the same child twice on 30 levels (31 levels deep, 2**30 paths)
        shared = 1
        for _ in range(30):
            shared = [shared, shared]
        answers = {}

        def check(name, record):
            """The answer of check_record, or a text when it did not finish in 5 s (a daemon thread, so a hang fails this test and does not stall the suite)."""
            thread = threading.Thread(target=lambda: answers.__setitem__(name, tables.check_record("graph_nodes", record)), daemon=True)
            thread.start()
            thread.join(5)
            return answers.get(name, "no answer within 5 s")
        # When/Then: the record at the limit is accepted, the one over it is refused naming data
        self.assertIsNone(check("at", node("g/d1", "data", value=[1] * 99995)))
        self.assertEqual(check("over", node("g/d1", "data", value=[1] * 99996)), {"rule": "schema_break", "detail": "data"})
        # And: the record with 2**30 paths is refused the same way within the time limit
        self.assertEqual(check("shared", node("g/d1", "data", value=shared)), {"rule": "schema_break", "detail": "data"})

    @mark.req("IF-301", "REQ-GTB-027")
    @each_provider(IF, make=subject)
    def test_input_that_cannot_be_checked_is_a_schema_break(self, tables):
        """TC-IF-301-23 golden 20: a record nested deeper than 200 levels is schema_break naming data, a category with an invalid schema is schema_break naming type.

        Example: a data node whose value is a list nested 300 times -> {"rule": "schema_break", "detail": "data"}; categories {"entity": {"type": 5}} -> detail "type".
        """
        # Given: a data node whose value is nested 300 levels, one nested 150 levels, and a category with an invalid schema
        deep, shallow = 1, 1
        for _ in range(300):
            deep = [deep]
        for _ in range(150):
            shallow = [shallow]
        # When/Then: the deep record is refused as schema_break naming data, in the check and in the rebuild, and nothing raises
        refused = {"rule": "schema_break", "detail": "data"}
        self.assertEqual(tables.check_record("graph_nodes", node("g/d1", "data", value=deep)), refused)
        self.assertEqual(tables.to_object(node("g/d1", "data", value=deep)), {"refused": refused})
        # And: the twin nested 150 levels is accepted
        self.assertIsNone(tables.check_record("graph_nodes", node("g/d1", "data", value=shallow)))
        # And: a category whose schema is not valid is refused naming type, for both node tables
        broken = {"rule": "schema_break", "detail": "type"}
        self.assertEqual(tables.check_record("graph_nodes", node("g/c1", "entity"), categories={"entity": {"type": 5}}), broken)
        self.assertEqual(tables.check_record("context_nodes", node("g/c1", "entity"), categories={"entity": {"type": 5}}), broken)

    @mark.req("IF-301", "REQ-GTB-022")
    @each_provider(IF, make=subject)
    def test_a_node_with_an_extra_field_is_refused_naming_it(self, tables):
        """TC-IF-301-21 golden 16: a node with a field its type does not list gives schema_break naming that field, in check_record and in to_object.

        Example: {"id": "g/d1", "data": {"type": "data", "foo": 1}} -> {"rule": "schema_break", "detail": "foo"}; a key id inside data -> detail "id".
        """
        # Given: one node per type with an extra field foo, and a data node with a key id inside its JSON field
        stop = {"max_repetitions": 1}
        cases = [(node("g/d1", "data", foo=1), "foo"),
                 (node("g/t1", "transform", toolbox_id="t", foo=1), "foo"),
                 (node("g/m1", "master", toolbox_id="t", stop=stop, foo=1), "foo"),
                 (node("g/d2", "data", id="x"), "id")]
        for record, field in cases:
            with self.subTest(record=record):
                # When/Then: the check and the rebuild both refuse it as schema_break naming the field, and the rebuild does not raise
                refusal = {"rule": "schema_break", "detail": field}
                self.assertEqual(tables.check_record("graph_nodes", record), refusal)
                self.assertEqual(tables.to_object(record), {"refused": refusal})
        # And: the twins without the extra field are accepted
        for record in (node("g/d1", "data"), node("g/t1", "transform", toolbox_id="t"), node("g/m1", "master", toolbox_id="t", stop=stop)):
            self.assertIsNone(tables.check_record("graph_nodes", record))
        # And: a missing required key is named before an extra field (decision 13)
        self.assertEqual(tables.check_record("graph_nodes", node("g/t1", "transform", foo=1)), {"rule": "schema_break", "detail": "toolbox_id"})
        # And: the schemas of the fixed list say so, and the node of a context graph keeps the fields of its own category
        for type_id, schema in tables.types().items():
            self.assertIs(schema.get("additionalProperties"), False, type_id)
        self.assertIsNone(tables.check_record("graph_nodes", node("g/c1", "entity", foo=1), categories={"entity": {"type": "object"}}))

    @mark.req("IF-301", "REQ-GTB-010")
    @each_provider(IF, make=subject)
    def test_an_unknown_type_is_refused_naming_it(self, tables):
        """TC-IF-301-08 golden 2: a node whose type is x.unknown gives unknown_type naming it, in check_record and in to_object.

        Example: {"id": "g/u1", "data": {"type": "x.unknown"}} -> {"rule": "unknown_type", "detail": "x.unknown"}.
        """
        # Given: a record with a type that is not in the fixed list
        record = node("g/u1", "x.unknown")
        # When/Then: the check and the rebuild both refuse it and name the type
        self.assertEqual(tables.check_record("graph_nodes", record), {"rule": "unknown_type", "detail": "x.unknown"})
        self.assertEqual(tables.to_object(record), {"refused": {"rule": "unknown_type", "detail": "x.unknown"}})

    @mark.req("IF-301", "REQ-GTB-011")
    @each_provider(IF, make=subject)
    def test_a_field_that_breaks_the_schema_names_its_path(self, tables):
        """TC-IF-301-09 golden 3: a missing required key and a value of the wrong kind give schema_break naming the field.

        Example: {"type": "transform"} without toolbox_id -> {"rule": "schema_break", "detail": "toolbox_id"}.
        """
        # Given: records that break one field each (paths of the pinned validator, top-level fields only: nested paths are not fixed by the contract)
        cases = [(node("g/t1", "transform"), "toolbox_id"),                                            # required key missing
                 (node("g/t1", "transform", toolbox_id=5), "toolbox_id"),                            # wrong kind
                 (node("g/m1", "master", toolbox_id="t"), "stop"),                                   # required key missing
                 (node("g/m1", "master", toolbox_id="t", stop="x"), "stop"),                         # wrong kind
                 (node("g/m1", "master", toolbox_id="t", stop={}), "stop"),                          # at least one limit is required
                 (node("g/d1", "data", parameters="x"), "parameters"),                               # wrong kind
                 ({"id": "g/n1", "data": "x"}, "data")]                                              # no JSON field
        for record, path in cases:
            with self.subTest(record=record):
                # When/Then: refused as schema_break with the path as detail
                self.assertEqual(tables.check_record("graph_nodes", record), {"rule": "schema_break", "detail": path})
        # And: a data node needs only its type; optional fields may be absent
        self.assertIsNone(tables.check_record("graph_nodes", node("g/d1", "data")))
        # And: a limit below its minimum is a schema_break inside `stop`
        broken = tables.check_record("graph_nodes", node("g/m1", "master", toolbox_id="t", stop={"max_repetitions": 0}))
        self.assertIsNotNone(broken)
        self.assertEqual(broken["rule"], "schema_break")
        self.assertTrue(broken["detail"].startswith("stop"))

    @mark.req("IF-301", "REQ-GTB-016")
    @each_provider(IF, make=subject)
    def test_a_check_changes_nothing(self, tables):
        """TC-IF-301-10 golden 4: check_record stores nothing and changes neither the record nor `stored`; the same input gives the same answer.

        Example: a refused record checked twice -> the same refusal; `stored` equal to its copy afterwards.
        """
        # Given: a refused record (unknown endpoint) and the state the caller holds
        record, stored = edge("g/e1", "g/n1", "g/n9"), {"nodes": {"g/n1": [1]}, "edges": {}}
        before = copy.deepcopy((record, stored))
        # When: it is checked twice
        first, second = tables.check_record("graph_edges", record, stored=stored), tables.check_record("graph_edges", record, stored=stored)
        # Then: the same refusal both times
        self.assertEqual(first, {"rule": "unknown_endpoint", "detail": "g/n9"})
        self.assertEqual(second, first)
        # And: nothing was changed; the version of a refused edit stays with the Storage layer (TC-GTB-017)
        self.assertEqual((record, stored), before)

    @mark.req("IF-301", "REQ-GTB-015")
    @each_provider(IF, make=subject)
    def test_the_document_form_and_the_record_form_convert_both_ways(self, tables):
        """TC-IF-301-11 golden 5: from_document(to_document(g)) equals g for a graph without a master node, and the document passes the v1 validation.

        Example: records g/d1, g/t1 (transform), g/d2 with edges g/e1, g/e2 -> document kinds data, process, data -> the same records back.
        """
        # Given: a graph of records without a master node (data, transform, data)
        nodes = [node("g/d1", "data", value=7, parameters={"k": 1}), node("g/t1", "transform", toolbox_id="tb"), node("g/d2", "data", value="x", parameters={})]
        edges = [edge("g/e1", "g/d1", "g/t1", label="a"), edge("g/e2", "g/t1", "g/d2")]
        # When: it is written as a document
        converted = tables.to_document(nodes, edges)
        # Then: the kinds follow the types (transform is process) and the v1 rules accept the document
        self.assertEqual(set(converted), {"document"})
        doc = converted["document"]
        self.assertEqual([(n["id"], n["kind"]) for n in doc["nodes"]], [("g/d1", "data"), ("g/t1", "process"), ("g/d2", "data")])
        self.assertEqual([(e["from"], e["to"]) for e in doc["edges"]], [("g/d1", "g/t1"), ("g/t1", "g/d2")])
        self.assertIsNone(tables.validate("workflows", doc))
        # And: reading the document back gives the graph that was written
        self.assertEqual(tables.from_document(doc), {"nodes": nodes, "edges": edges})

    @mark.req("IF-301", "REQ-GTB-015")
    @each_provider(IF, make=subject)
    def test_a_v1_document_becomes_records(self, tables):
        """TC-IF-301-12 compatibility: from_document turns the kinds of a v1 document into types (process to transform, data stays data) and keeps the edge ends.

        Example: nodes q (data), p (process), a (data), edges q->p, p->a -> types data, transform, data.
        """
        # Given: the v1 document of the golden examples of v1
        doc = {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process"}, {"id": "a", "kind": "data"}],
               "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "a"}]}
        # When: it is read
        records = tables.from_document(doc)
        # Then: the types follow the kinds and the edge ends are kept
        self.assertEqual([(n["id"], n["data"]["type"]) for n in records["nodes"]], [("q", "data"), ("p", "transform"), ("a", "data")])
        self.assertEqual([(e["from"], e["to"]) for e in records["edges"]], [("q", "p"), ("p", "a")])
        # And: every edge got its own non-empty ID (a v1 edge has none)
        ids = [e["id"] for e in records["edges"]]
        self.assertTrue(all(isinstance(i, str) and i for i in ids))
        self.assertEqual(len(set(ids)), 2)

    @mark.req("IF-301", "REQ-GTB-017", "REQ-GTB-019")
    @each_provider(IF, make=subject)
    def test_a_header_names_stored_versions_only(self, tables):
        """TC-IF-301-13 golden 6: a graph header naming wf1/n1 at version 5 when wf1/n1 has versions 1 and 2 gives unknown_member naming wf1/n1; version 2 gives None.

        Example: stored nodes {"wf1/n1": [1, 2]}; header names {"id": "wf1/n1", "version": 5} -> {"rule": "unknown_member", "detail": "wf1/n1"}.
        """
        # Given: what the caller has stored, and a header that names wf1/n1 at version 5 (the twin names version 2)
        stored = {"nodes": {"wf1/n1": [1, 2]}, "edges": {}}
        def header(version):
            return {"id": "wf1", "data": {"kind": "workflow", "context_graph_id": "ctx", "testbench_id": "", "description": "d",
                                          "nodes": [{"id": "wf1/n1", "version": version}], "edges": []}}
        # When/Then: version 5 is refused naming wf1/n1, version 2 is accepted
        self.assertEqual(tables.check_record("graphs", header(5), stored=stored), {"rule": "unknown_member", "detail": "wf1/n1"})
        self.assertIsNone(tables.check_record("graphs", header(2), stored=stored))
        # And: an edge member is checked against the stored edges the same way
        edge_header = header(2)
        edge_header["data"]["edges"] = [{"id": "wf1/e1", "version": 1}]
        self.assertEqual(tables.check_record("graphs", edge_header, stored=stored), {"rule": "unknown_member", "detail": "wf1/e1"})
        # And: without `stored` the rule is not checked (a pure function stores nothing)
        self.assertIsNone(tables.check_record("graphs", header(5)))

    @mark.req("IF-301", "REQ-GTB-006", "REQ-GTB-020")
    @each_provider(IF, make=subject)
    def test_an_edge_names_stored_nodes_only(self, tables):
        """TC-IF-301-14 golden 7: an edge g/e1 from g/n1 to g/n9 with only g/n1 stored gives unknown_endpoint naming g/n9; with g/n9 stored it gives None.

        Example: stored nodes {"g/n1": [1]} -> {"rule": "unknown_endpoint", "detail": "g/n9"}; stored nodes {"g/n1": [1], "g/n9": [1]} -> None.
        """
        # Given: the edge and the two states of the store
        record = edge("g/e1", "g/n1", "g/n9", label="x")
        # When/Then: refused naming the missing end; accepted when it is stored
        self.assertEqual(tables.check_record("graph_edges", record, stored={"nodes": {"g/n1": [1]}, "edges": {}}), {"rule": "unknown_endpoint", "detail": "g/n9"})
        self.assertIsNone(tables.check_record("graph_edges", record, stored={"nodes": {"g/n1": [1], "g/n9": [1]}, "edges": {}}))
        # And: a start node that is missing is named the same way
        self.assertEqual(tables.check_record("graph_edges", record, stored={"nodes": {"g/n9": [1]}, "edges": {}}), {"rule": "unknown_endpoint", "detail": "g/n1"})
        # And: without `stored` the rule is not checked
        self.assertIsNone(tables.check_record("graph_edges", record))

    @mark.req("IF-301", "REQ-GTB-018")
    @each_provider(IF, make=subject)
    def test_a_skill_needs_its_two_graph_ids(self, tables):
        """TC-IF-301-15 golden 8: a skill without a context graph ID gives schema_break naming context_graph_id; a complete skill gives None.

        Example: {"id": "lookup", "data": {"command": "/lookup", "workflow_graph_id": "wf-lookup"}} -> {"rule": "schema_break", "detail": "context_graph_id"}.
        """
        # Given: the skill of the golden example without the context graph ID, and the complete one
        broken = {"id": "lookup", "data": {"command": "/lookup", "workflow_graph_id": "wf-lookup"}}
        complete = {"id": "lookup", "data": {"command": "/lookup", "workflow_graph_id": "wf-lookup", "context_graph_id": "ctx-lookup"}}
        # When/Then
        self.assertEqual(tables.check_record("skills", broken), {"rule": "schema_break", "detail": "context_graph_id"})
        self.assertIsNone(tables.check_record("skills", complete))
        # And: a record without a command names the command
        self.assertEqual(tables.check_record("skills", {"id": "lookup", "data": {"workflow_graph_id": "w", "context_graph_id": "c"}}),
                         {"rule": "schema_break", "detail": "command"})

    @mark.req("IF-301", "REQ-GTB-010", "REQ-GTB-011")
    @each_provider(IF, make=subject)
    def test_a_context_graph_node_takes_its_schema_from_the_caller(self, tables):
        """TC-IF-301-16 golden 9: a node of category entity with categories {"entity": schema} and a fitting field gives None; without categories it is unknown_type naming entity.

        Example: {"id": "g/c1", "data": {"type": "entity", "name": "Ada"}} with the schema "name is text" -> None; without categories -> unknown_type entity.
        """
        # Given: a context graph's own category with its schema, and a node of that category
        categories = {"entity": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}
        record = node("g/c1", "entity", name="Ada")
        # When/Then: accepted with the categories, a plain ContextNode is built; refused without them
        self.assertIsNone(tables.check_record("graph_nodes", record, categories=categories))
        built = tables.to_object(record, categories=categories)
        self.assertEqual(set(built), {"object"})
        obj = built["object"]
        self.assertEqual((obj.id, obj.type), ("g/c1", "entity"))
        self.assertEqual(tables.to_record(obj), record)
        self.assertEqual(tables.check_record("graph_nodes", record), {"rule": "unknown_type", "detail": "entity"})
        # And: a field that breaks the category's schema is a schema_break naming it
        self.assertEqual(tables.check_record("graph_nodes", node("g/c2", "entity", name=5), categories=categories), {"rule": "schema_break", "detail": "name"})
        # And: a category the context graph does not list is unknown_type
        self.assertEqual(tables.check_record("graph_nodes", node("g/c3", "place"), categories=categories), {"rule": "unknown_type", "detail": "place"})

    @mark.req("IF-301", "REQ-GTB-015")
    @each_provider(IF, make=subject)
    def test_a_master_node_has_no_document_form(self, tables):
        """TC-IF-301-17 golden 10: to_document of a graph with a master node gives not_representable naming the master node.

        Example: nodes g/d1, g/m1 (master), g/d2 -> {"refused": {"rule": "not_representable", "detail": "g/m1"}}.
        """
        # Given: a graph with a master node
        nodes = [node("g/d1", "data"), node("g/m1", "master", toolbox_id="t", stop={"max_repetitions": 1}), node("g/d2", "data")]
        edges = [edge("g/e1", "g/d1", "g/m1"), edge("g/e2", "g/m1", "g/d2")]
        # When/Then: refused, naming the master node
        self.assertEqual(tables.to_document(nodes, edges), {"refused": {"rule": "not_representable", "detail": "g/m1"}})

    @mark.req("IF-301", "REQ-GTB-005", "REQ-GTB-006", "REQ-GTB-018")
    @each_provider(IF, make=subject)
    def test_a_record_without_its_identity_is_named_and_a_foreign_table_is_refused(self, tables):
        """TC-IF-301-18: a record without ID (or an edge without an end) is record_identity naming the field; a table that is not a record table is a ValueError; nothing raises.

        Example: {"data": {"type": "data"}} -> {"rule": "record_identity", "detail": "id"}; check_record("memory", {}) raises ValueError.
        """
        # Given/When/Then: the identity fields are named
        self.assertEqual(tables.check_record("graph_nodes", {"data": {"type": "data"}}), {"rule": "record_identity", "detail": "id"})
        self.assertEqual(tables.check_record("graph_nodes", {"id": 5, "data": {"type": "data"}}), {"rule": "record_identity", "detail": "id"})
        self.assertEqual(tables.check_record("graph_edges", {"id": "g/e1", "from": "g/n1", "data": {}}), {"rule": "record_identity", "detail": "to"})
        self.assertEqual(tables.check_record("skills", {"data": {}}), {"rule": "record_identity", "detail": "id"})
        # And: a table that is not defined here is a ValueError (the caller asks IF-302 instead)
        with self.assertRaises(ValueError):
            tables.check_record("memory", {})
        # And: any other input gives a rule, never an exception (as A-60)
        for table in ("graph_nodes", "graph_edges", "graphs", "skills"):
            for garbage in (None, [], "x", 5, {}, {"id": "g/a"}, {"id": "g/a", "data": None}, {"id": "g/a", "data": {"type": ["x"]}}):
                with self.subTest(table=table, record=garbage):
                    result = tables.check_record(table, garbage, categories={"entity": {}}, stored={"nodes": {}, "edges": {}})
                    self.assertEqual(set(result), {"rule", "detail"})
        for garbage in (None, [], "x", 5, {}, {"id": "g/a"}, {"id": "g/a", "data": {"type": ["x"]}}):
            with self.subTest(to_object=garbage):
                self.assertEqual(set(tables.to_object(garbage)), {"refused"})

    @mark.req("IF-301", "REQ-GTB-011")
    @each_provider(IF, make=subject)
    def test_500_node_records_and_500_edge_records_are_checked_in_half_a_second(self, tables):
        """TC-IF-301-19 bound: 500 node records and 500 edge records are checked in at most 500 ms (best of 3 runs, so a busy host does not decide).

        Example: 500 transform nodes g/n0..g/n499 and 500 edges g/e0..g/e499 between stored nodes -> all None in at most 0.5 s.
        """
        # Given: 500 valid node records, 500 valid edge records and the store state they need
        nodes = [node("g/n%d" % i, "transform", toolbox_id="tb") for i in range(500)]
        stored = {"nodes": {"g/n%d" % i: [1] for i in range(500)}, "edges": {}}
        edges = [edge("g/e%d" % i, "g/n%d" % i, "g/n%d" % ((i + 1) % 500)) for i in range(500)]
        timings = []
        for _ in range(3):
            # When: all 1000 are checked
            start = time.perf_counter()
            results = [tables.check_record("graph_nodes", n, stored=stored) for n in nodes] + [tables.check_record("graph_edges", e, stored=stored) for e in edges]
            timings.append(time.perf_counter() - start)
            # Then: every one is accepted
            self.assertEqual(results, [None] * 1000)
        # And: the fastest run is within the bound of the contract (0.5 s)
        self.assertLessEqual(min(timings), 0.5)

    @mark.req("IF-301", "REQ-GTB-021")
    @each_provider(IF, make=subject)
    def test_a_record_under_another_id_is_refused(self, tables):
        """TC-IF-301-20 golden 15: a record whose id is g/n1, checked with record_id x, gives record_identity naming id; with record_id g/n1, or without, it gives None.

        Example: {"id": "g/n1", "data": {"type": "data"}} with record_id="x" -> {"rule": "record_identity", "detail": "id"}.
        """
        # Given: a node record with its own ID g/n1
        record = node("g/n1", "data")
        # When/Then: under another record ID it is refused naming the field id; the twin under its own ID and the call without record_id are accepted
        self.assertEqual(tables.check_record("graph_nodes", record, record_id="x"), {"rule": "record_identity", "detail": "id"})
        self.assertIsNone(tables.check_record("graph_nodes", record, record_id="g/n1"))
        self.assertIsNone(tables.check_record("graph_nodes", record))
        # And: the same holds for the other three tables
        for table, other in (("graph_edges", edge("g/e1", "g/n1", "g/n2")), ("skills", {"id": "s1", "data": {"command": "/s", "workflow_graph_id": "w", "context_graph_id": "c"}})):
            self.assertEqual(tables.check_record(table, other, record_id="x"), {"rule": "record_identity", "detail": "id"})
            self.assertIsNone(tables.check_record(table, other, record_id=other["id"]))


    @mark.req("IF-301", "REQ-GTB-029", "REQ-GTB-031")
    @each_provider(IF, make=subject)
    def test_a_step_or_connection_without_its_graph_in_the_id_is_refused(self, tables):
        """TC-IF-301-25 golden 22 (v3, A-167): a record of a step or connection table under n1, /n1 or g/ is unscoped_id naming that ID; the empty ID stays record_identity; g/n1 and lookup/a/b are accepted.

        Example: {"id": "n1", "data": {"type": "data"}} as graph_nodes -> {"rule": "unscoped_id", "detail": "n1"}; {"id": "lookup/a/b", ...} -> None.
        """
        # Given: one record of each of the four tables, made under a given ID (an edge with the ends g/a and g/b)
        make = {"graph_nodes": lambda i: node(i, "data"), "graph_edges": lambda i: edge(i, "g/a", "g/b"),
                "context_nodes": lambda i: node(i, "entity"), "context_edges": lambda i: edge(i, "g/a", "g/b")}
        for table, build in make.items():
            # When/Then: a plain ID, an empty graph part and an empty local part are refused naming the ID
            for bad in ("n1", "/n1", "g/"):
                self.assertEqual(tables.check_record(table, build(bad)), {"rule": "unscoped_id", "detail": bad}, (table, bad))
            # And: the empty ID is still record_identity naming id (checked first, as in v2; D-409)
            self.assertEqual(tables.check_record(table, build("")), {"rule": "record_identity", "detail": "id"}, table)
            # And: a scoped ID is accepted, also one whose local ID holds a slash (the first slash separates, REQ-GTB-031)
            for good in ("g/n1", "lookup/a/b"):
                self.assertIsNone(tables.check_record(table, build(good)), (table, good))

    @mark.req("IF-301", "REQ-GTB-030")
    @each_provider(IF, make=subject)
    def test_a_header_names_only_members_of_its_own_graph(self, tables):
        """TC-IF-301-26 golden 23 (v3, A-167): a header g naming the node h/n1 or the edge h/e1 is unscoped_id naming that member, with and without stored; g/n1 and g/e1 are accepted.

        Example: header g with nodes [{"id": "h/n1", "version": 1}] -> {"rule": "unscoped_id", "detail": "h/n1"}.
        """
        # Given: a header of the workflow graph g and what is stored of g
        def header(nodes, edges):
            return {"id": "g", "data": {"kind": "workflow", "context_graph_id": "", "testbench_id": "", "description": "d",
                                        "nodes": [{"id": i, "version": 1} for i in nodes], "edges": [{"id": i, "version": 1} for i in edges]}}
        stored = {"nodes": {"g/n1": [1], "h/n1": [1]}, "edges": {"g/e1": [1], "h/e1": [1]}}
        # When/Then: a node or an edge of the graph h is refused naming it, even when it is stored and when nothing is passed as stored
        for nodes, edges, member in ((["h/n1"], [], "h/n1"), (["g/n1"], ["h/e1"], "h/e1")):
            for given in (stored, None):
                self.assertEqual(tables.check_record("graphs", header(nodes, edges), stored=given), {"rule": "unscoped_id", "detail": member})
        # And: the members of g itself are accepted
        self.assertIsNone(tables.check_record("graphs", header(["g/n1"], ["g/e1"]), stored=stored))

if __name__ == "__main__":
    unittest.main()
