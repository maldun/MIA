"""Unit tests of the record checks of the Graph tables (N-3.2, G-V2.STORE T-01) beyond the acceptance tests: edge cases found while writing check_record.
Run with: python tests/test_graph_record_checks.py"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import graph_tables  # noqa: E402
from storage import Storage, StorageError  # noqa: E402
from storage_files import FileBackend  # noqa: E402


def master(**fields):
    return {"id": "m1", "data": dict({"type": "master", "toolbox_id": "t"}, **fields)}


class RecordCheckEdges(unittest.TestCase):
    def test_a_number_that_is_not_finite_breaks_the_schema(self):
        """A stopping limit of NaN or infinity is refused like in v1 (A-60) and names its path: JSON has no such number.

        Example: stop {"max_seconds": NaN} -> schema_break "stop.max_seconds"; {"max_seconds": inf} -> the same.
        """
        # Given: master nodes whose limit is NaN or infinity
        for number in (float("nan"), float("inf")):
            with self.subTest(number=number):
                # When: each is checked; Then: refused as schema_break with the path of the limit
                self.assertEqual(graph_tables.check_record("graph_nodes", master(stop={"max_seconds": number})),
                                 {"rule": "schema_break", "detail": "stop.max_seconds"})
        # And: a finite limit is accepted
        self.assertIsNone(graph_tables.check_record("graph_nodes", master(stop={"max_seconds": 0.5})))

    def test_a_boolean_is_not_a_repetition_count(self):
        """True is not an integer limit (as in v1, D-160).

        Example: stop {"max_repetitions": True} -> schema_break "stop.max_repetitions"; 1 is valid.
        """
        # Given/When/Then
        self.assertEqual(graph_tables.check_record("graph_nodes", master(stop={"max_repetitions": True})),
                         {"rule": "schema_break", "detail": "stop.max_repetitions"})
        self.assertIsNone(graph_tables.check_record("graph_nodes", master(stop={"max_repetitions": 1})))

    def test_a_malformed_header_is_named_and_never_raises(self):
        """A header whose members are not objects, or whose kind is unknown, is a schema_break naming the field, not an exception.

        Example: nodes ["n1"] -> schema_break "nodes.0"; kind "x" -> schema_break "kind".
        """
        # Given: two broken headers and the empty store state
        base = {"kind": "workflow", "context_graph_id": "c", "testbench_id": "", "description": "d", "nodes": [], "edges": []}
        stored = {"nodes": {}, "edges": {}}
        # When/Then
        self.assertEqual(graph_tables.check_record("graphs", {"id": "g", "data": dict(base, nodes=["n1"])}, stored=stored),
                         {"rule": "schema_break", "detail": "nodes.0"})
        self.assertEqual(graph_tables.check_record("graphs", {"id": "g", "data": dict(base, kind="x")}, stored=stored),
                         {"rule": "schema_break", "detail": "kind"})

    def test_a_type_that_is_not_text_is_an_unknown_type(self):
        """A type ID that is a list cannot be in the fixed list: unknown_type naming it.

        Example: {"type": ["x"]} -> unknown_type; an empty `categories` makes even "data" unknown (a context graph without that category).
        """
        # Given/When/Then
        self.assertEqual(graph_tables.check_record("graph_nodes", {"id": "a", "data": {"type": ["x"]}})["rule"], "unknown_type")
        self.assertEqual(graph_tables.check_record("graph_nodes", {"id": "a", "data": {"type": "data"}}, categories={}),
                         {"rule": "unknown_type", "detail": "data"})


class FixedFieldsOfANode(unittest.TestCase):
    """REQ-GTB-022 (A-93, T-07): a node has only the fields its type lists, on write and on read."""

    def test_an_extra_field_or_an_id_inside_data_is_refused_naming_it(self):
        """check_record and to_object refuse a node with a field its type does not list, and never raise.

        Example: {"type": "data", "foo": 1} -> schema_break foo; {"type": "data", "id": "x"} -> schema_break id.
        """
        # Given
        cases = {"foo": {"type": "data", "foo": 1}, "id": {"type": "data", "id": "x"}}
        for field, data in cases.items():
            record = {"id": "n1", "data": data}
            # When/Then
            self.assertEqual(graph_tables.check_record("graph_nodes", record), {"rule": "schema_break", "detail": field})
            self.assertEqual(graph_tables.to_object(record), {"refused": {"rule": "schema_break", "detail": field}})

    def test_several_extra_fields_name_the_first_in_sorted_order(self):
        """Example: {"type": "data", "zed": 1, "bar": 2} -> detail bar; a missing key is named before an extra field."""
        # Given/When/Then
        self.assertEqual(graph_tables.check_record("graph_nodes", {"id": "n", "data": {"type": "data", "zed": 1, "bar": 2}})["detail"], "bar")
        self.assertEqual(graph_tables.check_record("graph_nodes", {"id": "n", "data": {"type": "transform", "foo": 1}})["detail"], "toolbox_id")

    def test_storage_put_refuses_an_extra_field_and_stores_nothing(self):
        """Example: put("graph_nodes", "n1", {"id": "n1", "data": {"type": "data", "foo": 1}}) -> invalid, schema_break, foo; ids() is empty."""
        # Given
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        store = Storage(FileBackend(os.path.join(directory, "main")))
        # When
        with self.assertRaises(StorageError) as caught:
            store.put("graph_nodes", "n1", {"id": "n1", "data": {"type": "data", "foo": 1}}, "anna")
        # Then
        self.assertEqual((caught.exception.code, caught.exception.rule, caught.exception.detail), ("invalid", "schema_break", "foo"))
        self.assertEqual(list(store.ids("graph_nodes")), [])


class RobustnessOfTheChecks(unittest.TestCase):
    """T-09 (A-98): fixes of F-03, F-09 and F-11 found in Verify."""

    def test_fresh_categories_do_not_grow_the_validator_cache_without_bound(self):
        """F-03: a caller that builds its categories anew for each call must not leak one validator per call.

        Example: 10 000 calls with equal, freshly built categories -> fewer than 256 cached validators.
        """
        # Given/When
        for _ in range(10000):
            categories = {"entity": {"type": "object", "properties": {"type": {}}}}
            graph_tables.check_record("context_nodes", {"id": "c", "data": {"type": "entity"}}, categories=categories)
        # Then
        self.assertLess(len(graph_tables._validators), 256)

    def test_an_additional_field_is_not_one_a_pattern_property_matches(self):
        """F-11: with patternProperties the refusal names the field no pattern matches.

        Example: {"type": "entity", "xa": 1, "zz": 2} with "^x" allowed -> detail zz.
        """
        # Given
        schema = {"type": "object", "properties": {"type": {}}, "patternProperties": {"^x": {}}, "additionalProperties": False}
        # When/Then
        self.assertEqual(graph_tables.check_record("graph_nodes", {"id": "n", "data": {"type": "entity", "xa": 1, "zz": 2}}, categories={"entity": schema}),
                         {"rule": "schema_break", "detail": "zz"})

    def test_a_record_nested_too_deep_is_a_schema_break_naming_data(self):
        """REQ-GTB-027: 200 levels count the record itself as level 1; deeper is refused, never raised.

        Example: a node whose value is nested 250 levels deep -> schema_break "data" in check_record and to_object; 100 levels is accepted.
        """
        # Given: the record is level 1, its data level 2, the value starts at level 3
        def nested(levels):
            value = {}
            for _ in range(levels - 3):
                value = {"k": value}
            return {"id": "n", "data": {"type": "data", "value": value}}
        deep = nested(250)
        refusal = {"rule": "schema_break", "detail": "data"}
        # When/Then
        self.assertEqual(graph_tables.check_record("graph_nodes", deep), refusal)
        self.assertEqual(graph_tables.to_object(deep), {"refused": refusal})
        self.assertIsNone(graph_tables.check_record("graph_nodes", nested(100)))

    def test_a_category_schema_that_is_not_a_schema_is_a_schema_break_naming_type(self):
        """REQ-GTB-027: a category whose schema fails check_schema cannot check a node.

        Example: schema {"type": "nope"} -> schema_break "type" for graph_nodes and context_nodes.
        """
        # Given
        categories = {"entity": {"type": "nope"}}
        # When/Then
        for table in ("graph_nodes", "context_nodes"):
            self.assertEqual(graph_tables.check_record(table, {"id": "n", "data": {"type": "entity"}}, categories=categories),
                             {"rule": "schema_break", "detail": "type"}, table)


if __name__ == "__main__":
    unittest.main()
