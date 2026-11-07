"""IF-301 v2 graph tables (record tables, types, record checks, conversion; A-90): the contract suite runs against the mock (stage 1, green) and the
real Graph tables (stage 2; no skip since A-91, N-3.2 integrated). The v1 cases stay in test_if_301_graph_tables.py (unchanged).
Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_301_v2_graph_tables.py
"""
import copy
import os
import sys
import time
import unittest

import jsonschema

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider  # noqa: E402
import contract as contract_module            # noqa: E402  (for the real provider, loaded with the real graph rules)
from markers import mark                      # noqa: E402

IF = "IF-301"
NODE_RECORD_TABLES = {t: {"versioned": True, "deletable": False} for t in ("graph_nodes", "graph_edges", "graphs", "skills")}


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
        """TC-IF-301-05: definitions() stays the two tables of v1; record_definitions() lists the four record tables, versioned, not deletable.

        Example: record_definitions() -> graph_nodes, graph_edges, graphs, skills, each {"versioned": True, "deletable": False}.
        """
        # Given: the provider; When: both definitions are read; Then: v1 is unchanged and the four tables are added in their own operation
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

        Example: {"id": "t1", "data": {"type": "transform", "toolbox_id": "t-demo"}} -> None; the object has id t1 and toolbox_id t-demo.
        """
        # Given: one record of each type, written by hand (the master one with a task and a stopping criterion)
        records = {"data": node("d1", "data", value=7, parameters={"k": 1}),
                   "transform": node("t1", "transform", toolbox_id="t-demo"),
                   "master": node("m1", "master", toolbox_id="t-lead", stop={"max_repetitions": 3, "max_seconds": 2.5}, task={"goal": "x"})}
        expected = {"data": {"id": "d1", "value": 7, "parameters": {"k": 1}},
                    "transform": {"id": "t1", "toolbox_id": "t-demo"},
                    "master": {"id": "m1", "toolbox_id": "t-lead", "stop": {"max_repetitions": 3, "max_seconds": 2.5}, "task": {"goal": "x"}}}
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

    @mark.req("IF-301", "REQ-GTB-022")
    @each_provider(IF, make=subject)
    def test_a_node_with_an_extra_field_is_refused_naming_it(self, tables):
        """TC-IF-301-21 golden 16: a node with a field its type does not list gives schema_break naming that field, in check_record and in to_object.

        Example: {"id": "d1", "data": {"type": "data", "foo": 1}} -> {"rule": "schema_break", "detail": "foo"}; a key id inside data -> detail "id".
        """
        # Given: one node per type with an extra field foo, and a data node with a key id inside its JSON field
        stop = {"max_repetitions": 1}
        cases = [(node("d1", "data", foo=1), "foo"),
                 (node("t1", "transform", toolbox_id="t", foo=1), "foo"),
                 (node("m1", "master", toolbox_id="t", stop=stop, foo=1), "foo"),
                 (node("d2", "data", id="x"), "id")]
        for record, field in cases:
            with self.subTest(record=record):
                # When/Then: the check and the rebuild both refuse it as schema_break naming the field, and the rebuild does not raise
                refusal = {"rule": "schema_break", "detail": field}
                self.assertEqual(tables.check_record("graph_nodes", record), refusal)
                self.assertEqual(tables.to_object(record), {"refused": refusal})
        # And: the twins without the extra field are accepted
        for record in (node("d1", "data"), node("t1", "transform", toolbox_id="t"), node("m1", "master", toolbox_id="t", stop=stop)):
            self.assertIsNone(tables.check_record("graph_nodes", record))
        # And: a missing required key is named before an extra field (decision 13)
        self.assertEqual(tables.check_record("graph_nodes", node("t1", "transform", foo=1)), {"rule": "schema_break", "detail": "toolbox_id"})
        # And: the schemas of the fixed list say so, and the node of a context graph keeps the fields of its own category
        for type_id, schema in tables.types().items():
            self.assertIs(schema.get("additionalProperties"), False, type_id)
        self.assertIsNone(tables.check_record("graph_nodes", node("c1", "entity", foo=1), categories={"entity": {"type": "object"}}))

    @mark.req("IF-301", "REQ-GTB-010")
    @each_provider(IF, make=subject)
    def test_an_unknown_type_is_refused_naming_it(self, tables):
        """TC-IF-301-08 golden 2: a node whose type is x.unknown gives unknown_type naming it, in check_record and in to_object.

        Example: {"id": "u1", "data": {"type": "x.unknown"}} -> {"rule": "unknown_type", "detail": "x.unknown"}.
        """
        # Given: a record with a type that is not in the fixed list
        record = node("u1", "x.unknown")
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
        cases = [(node("t1", "transform"), "toolbox_id"),                                            # required key missing
                 (node("t1", "transform", toolbox_id=5), "toolbox_id"),                            # wrong kind
                 (node("m1", "master", toolbox_id="t"), "stop"),                                   # required key missing
                 (node("m1", "master", toolbox_id="t", stop="x"), "stop"),                         # wrong kind
                 (node("m1", "master", toolbox_id="t", stop={}), "stop"),                          # at least one limit is required
                 (node("d1", "data", parameters="x"), "parameters"),                               # wrong kind
                 ({"id": "n1", "data": "x"}, "data")]                                              # no JSON field
        for record, path in cases:
            with self.subTest(record=record):
                # When/Then: refused as schema_break with the path as detail
                self.assertEqual(tables.check_record("graph_nodes", record), {"rule": "schema_break", "detail": path})
        # And: a data node needs only its type; optional fields may be absent
        self.assertIsNone(tables.check_record("graph_nodes", node("d1", "data")))
        # And: a limit below its minimum is a schema_break inside `stop`
        broken = tables.check_record("graph_nodes", node("m1", "master", toolbox_id="t", stop={"max_repetitions": 0}))
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
        record, stored = edge("e1", "n1", "n9"), {"nodes": {"n1": [1]}, "edges": {}}
        before = copy.deepcopy((record, stored))
        # When: it is checked twice
        first, second = tables.check_record("graph_edges", record, stored=stored), tables.check_record("graph_edges", record, stored=stored)
        # Then: the same refusal both times
        self.assertEqual(first, {"rule": "unknown_endpoint", "detail": "n9"})
        self.assertEqual(second, first)
        # And: nothing was changed; the version of a refused edit stays with the Storage layer (TC-GTB-017)
        self.assertEqual((record, stored), before)

    @mark.req("IF-301", "REQ-GTB-015")
    @each_provider(IF, make=subject)
    def test_the_document_form_and_the_record_form_convert_both_ways(self, tables):
        """TC-IF-301-11 golden 5: from_document(to_document(g)) equals g for a graph without a master node, and the document passes the v1 validation.

        Example: records d1, t1 (transform), d2 with edges e1, e2 -> document kinds data, process, data -> the same records back.
        """
        # Given: a graph of records without a master node (data, transform, data)
        nodes = [node("d1", "data", value=7, parameters={"k": 1}), node("t1", "transform", toolbox_id="tb"), node("d2", "data", value="x", parameters={})]
        edges = [edge("e1", "d1", "t1", label="a"), edge("e2", "t1", "d2")]
        # When: it is written as a document
        converted = tables.to_document(nodes, edges)
        # Then: the kinds follow the types (transform is process) and the v1 rules accept the document
        self.assertEqual(set(converted), {"document"})
        doc = converted["document"]
        self.assertEqual([(n["id"], n["kind"]) for n in doc["nodes"]], [("d1", "data"), ("t1", "process"), ("d2", "data")])
        self.assertEqual([(e["from"], e["to"]) for e in doc["edges"]], [("d1", "t1"), ("t1", "d2")])
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
        """TC-IF-301-13 golden 6: a graph header naming n1 at version 5 when n1 has versions 1 and 2 gives unknown_member naming n1; version 2 gives None.

        Example: stored nodes {"n1": [1, 2]}; header names {"id": "n1", "version": 5} -> {"rule": "unknown_member", "detail": "n1"}.
        """
        # Given: what the caller has stored, and a header that names n1 at version 5 (the twin names version 2)
        stored = {"nodes": {"n1": [1, 2]}, "edges": {}}
        def header(version):
            return {"id": "wf1", "data": {"kind": "workflow", "context_graph_id": "ctx", "testbench_id": "", "description": "d",
                                          "nodes": [{"id": "n1", "version": version}], "edges": []}}
        # When/Then: version 5 is refused naming n1, version 2 is accepted
        self.assertEqual(tables.check_record("graphs", header(5), stored=stored), {"rule": "unknown_member", "detail": "n1"})
        self.assertIsNone(tables.check_record("graphs", header(2), stored=stored))
        # And: an edge member is checked against the stored edges the same way
        edge_header = header(2)
        edge_header["data"]["edges"] = [{"id": "e1", "version": 1}]
        self.assertEqual(tables.check_record("graphs", edge_header, stored=stored), {"rule": "unknown_member", "detail": "e1"})
        # And: without `stored` the rule is not checked (a pure function stores nothing)
        self.assertIsNone(tables.check_record("graphs", header(5)))

    @mark.req("IF-301", "REQ-GTB-006", "REQ-GTB-020")
    @each_provider(IF, make=subject)
    def test_an_edge_names_stored_nodes_only(self, tables):
        """TC-IF-301-14 golden 7: an edge e1 from n1 to n9 with only n1 stored gives unknown_endpoint naming n9; with n9 stored it gives None.

        Example: stored nodes {"n1": [1]} -> {"rule": "unknown_endpoint", "detail": "n9"}; stored nodes {"n1": [1], "n9": [1]} -> None.
        """
        # Given: the edge and the two states of the store
        record = edge("e1", "n1", "n9", label="x")
        # When/Then: refused naming the missing end; accepted when it is stored
        self.assertEqual(tables.check_record("graph_edges", record, stored={"nodes": {"n1": [1]}, "edges": {}}), {"rule": "unknown_endpoint", "detail": "n9"})
        self.assertIsNone(tables.check_record("graph_edges", record, stored={"nodes": {"n1": [1], "n9": [1]}, "edges": {}}))
        # And: a start node that is missing is named the same way
        self.assertEqual(tables.check_record("graph_edges", record, stored={"nodes": {"n9": [1]}, "edges": {}}), {"rule": "unknown_endpoint", "detail": "n1"})
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

        Example: {"id": "c1", "data": {"type": "entity", "name": "Ada"}} with the schema "name is text" -> None; without categories -> unknown_type entity.
        """
        # Given: a context graph's own category with its schema, and a node of that category
        categories = {"entity": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}
        record = node("c1", "entity", name="Ada")
        # When/Then: accepted with the categories, a plain ContextNode is built; refused without them
        self.assertIsNone(tables.check_record("graph_nodes", record, categories=categories))
        built = tables.to_object(record, categories=categories)
        self.assertEqual(set(built), {"object"})
        obj = built["object"]
        self.assertEqual((obj.id, obj.type), ("c1", "entity"))
        self.assertEqual(tables.to_record(obj), record)
        self.assertEqual(tables.check_record("graph_nodes", record), {"rule": "unknown_type", "detail": "entity"})
        # And: a field that breaks the category's schema is a schema_break naming it
        self.assertEqual(tables.check_record("graph_nodes", node("c2", "entity", name=5), categories=categories), {"rule": "schema_break", "detail": "name"})
        # And: a category the context graph does not list is unknown_type
        self.assertEqual(tables.check_record("graph_nodes", node("c3", "place"), categories=categories), {"rule": "unknown_type", "detail": "place"})

    @mark.req("IF-301", "REQ-GTB-015")
    @each_provider(IF, make=subject)
    def test_a_master_node_has_no_document_form(self, tables):
        """TC-IF-301-17 golden 10: to_document of a graph with a master node gives not_representable naming the master node.

        Example: nodes d1, m1 (master), d2 -> {"refused": {"rule": "not_representable", "detail": "m1"}}.
        """
        # Given: a graph with a master node
        nodes = [node("d1", "data"), node("m1", "master", toolbox_id="t", stop={"max_repetitions": 1}), node("d2", "data")]
        edges = [edge("e1", "d1", "m1"), edge("e2", "m1", "d2")]
        # When/Then: refused, naming the master node
        self.assertEqual(tables.to_document(nodes, edges), {"refused": {"rule": "not_representable", "detail": "m1"}})

    @mark.req("IF-301", "REQ-GTB-005", "REQ-GTB-006", "REQ-GTB-018")
    @each_provider(IF, make=subject)
    def test_a_record_without_its_identity_is_named_and_a_foreign_table_is_refused(self, tables):
        """TC-IF-301-18: a record without ID (or an edge without an end) is record_identity naming the field; a table that is not a record table is a ValueError; nothing raises.

        Example: {"data": {"type": "data"}} -> {"rule": "record_identity", "detail": "id"}; check_record("memory", {}) raises ValueError.
        """
        # Given/When/Then: the identity fields are named
        self.assertEqual(tables.check_record("graph_nodes", {"data": {"type": "data"}}), {"rule": "record_identity", "detail": "id"})
        self.assertEqual(tables.check_record("graph_nodes", {"id": 5, "data": {"type": "data"}}), {"rule": "record_identity", "detail": "id"})
        self.assertEqual(tables.check_record("graph_edges", {"id": "e1", "from": "n1", "data": {}}), {"rule": "record_identity", "detail": "to"})
        self.assertEqual(tables.check_record("skills", {"data": {}}), {"rule": "record_identity", "detail": "id"})
        # And: a table that is not defined here is a ValueError (the caller asks IF-302 instead)
        with self.assertRaises(ValueError):
            tables.check_record("memory", {})
        # And: any other input gives a rule, never an exception (as A-60)
        for table in ("graph_nodes", "graph_edges", "graphs", "skills"):
            for garbage in (None, [], "x", 5, {}, {"id": "a"}, {"id": "a", "data": None}, {"id": "a", "data": {"type": ["x"]}}):
                with self.subTest(table=table, record=garbage):
                    result = tables.check_record(table, garbage, categories={"entity": {}}, stored={"nodes": {}, "edges": {}})
                    self.assertEqual(set(result), {"rule", "detail"})
        for garbage in (None, [], "x", 5, {}, {"id": "a"}, {"id": "a", "data": {"type": ["x"]}}):
            with self.subTest(to_object=garbage):
                self.assertEqual(set(tables.to_object(garbage)), {"refused"})

    @mark.req("IF-301", "REQ-GTB-011")
    @each_provider(IF, make=subject)
    def test_500_node_records_and_500_edge_records_are_checked_in_half_a_second(self, tables):
        """TC-IF-301-19 bound: 500 node records and 500 edge records are checked in at most 500 ms (best of 3 runs, so a busy host does not decide).

        Example: 500 transform nodes n0..n499 and 500 edges e0..e499 between stored nodes -> all None in at most 0.5 s.
        """
        # Given: 500 valid node records, 500 valid edge records and the store state they need
        nodes = [node("n%d" % i, "transform", toolbox_id="tb") for i in range(500)]
        stored = {"nodes": {"n%d" % i: [1] for i in range(500)}, "edges": {}}
        edges = [edge("e%d" % i, "n%d" % i, "n%d" % ((i + 1) % 500)) for i in range(500)]
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
        """TC-IF-301-20 golden 15: a record whose id is n1, checked with record_id x, gives record_identity naming id; with record_id n1, or without, it gives None.

        Example: {"id": "n1", "data": {"type": "data"}} with record_id="x" -> {"rule": "record_identity", "detail": "id"}.
        """
        # Given: a node record with its own ID n1
        record = node("n1", "data")
        # When/Then: under another record ID it is refused naming the field id; the twin under its own ID and the call without record_id are accepted
        self.assertEqual(tables.check_record("graph_nodes", record, record_id="x"), {"rule": "record_identity", "detail": "id"})
        self.assertIsNone(tables.check_record("graph_nodes", record, record_id="n1"))
        self.assertIsNone(tables.check_record("graph_nodes", record))
        # And: the same holds for the other three tables
        for table, other in (("graph_edges", edge("e1", "n1", "n2")), ("skills", {"id": "s1", "data": {"command": "/s", "workflow_graph_id": "w", "context_graph_id": "c"}})):
            self.assertEqual(tables.check_record(table, other, record_id="x"), {"rule": "record_identity", "detail": "id"})
            self.assertIsNone(tables.check_record(table, other, record_id=other["id"]))


if __name__ == "__main__":
    unittest.main()
