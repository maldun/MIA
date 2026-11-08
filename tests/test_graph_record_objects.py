"""Unit tests of the data classes of the Graph tables (N-3.2, G-V2.STORE T-02) beyond the acceptance tests: edge cases of to_object and to_record.
Run with: python tests/test_graph_record_objects.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import graph_tables  # noqa: E402


def data_node(**fields):
    return {"id": "d1", "data": dict({"type": "data"}, **fields)}


class ClassesFromTypeIds(unittest.TestCase):
    def test_a_falsy_value_is_kept(self):
        """A data node whose value is 0, an empty text, False or an empty list keeps it through object and record (only None means absent).

        Example: value 0 -> the object has value 0 and to_record gives value 0 back.
        """
        for value in (0, "", False, []):
            with self.subTest(value=value):
                # Given: a record with a falsy value
                record = data_node(value=value, parameters={})
                # When: it is rebuilt and written back
                obj = graph_tables.to_object(record)["object"]
                # Then: the value is the same and the record equals the first one
                self.assertEqual(obj.value, value)
                self.assertEqual(graph_tables.to_record(obj), record)

    def test_an_object_shares_nothing_with_its_record(self):
        """Changing the object does not change the record it was built from, and the other way round.

        Example: obj.parameters["k"] = 2 leaves record["data"]["parameters"] == {"k": 1}.
        """
        # Given: a record and the object built from it
        record = data_node(parameters={"k": 1})
        obj = graph_tables.to_object(record)["object"]
        # When: the object is changed
        obj.parameters["k"] = 2
        # Then: the record is as it was, and the record written from the object is a copy too
        self.assertEqual(record["data"]["parameters"], {"k": 1})
        written = graph_tables.to_record(obj)
        written["data"]["parameters"]["k"] = 3
        self.assertEqual(obj.parameters, {"k": 2})

    def test_an_absent_value_and_a_null_value_are_the_same_node(self):
        """JSON null and an absent optional field are not told apart: both give None, and to_record leaves the field out.

        Example: {"type": "data", "value": null} -> value None -> record without `value` (parameters {} is added).
        """
        # Given/When: a record with an explicit null and one without the field
        with_null = graph_tables.to_object(data_node(value=None))["object"]
        without = graph_tables.to_object(data_node())["object"]
        # Then: equal objects, and the written record has no `value`
        self.assertEqual(with_null, without)
        self.assertEqual(graph_tables.to_record(without), {"id": "d1", "data": {"type": "data", "parameters": {}}})

    def test_an_object_of_another_class_is_not_a_node(self):
        """to_record of something that is not one of the listed classes raises TypeError (a programming error, not a record to refuse).

        Example: to_record({"id": "d1"}) -> TypeError.
        """
        # Given/When/Then
        with self.assertRaises(TypeError):
            graph_tables.to_record({"id": "d1"})

    def test_a_context_node_round_trips_with_its_category(self):
        """A context-graph node keeps its category and its other fields through object and record.

        Example: {"id": "c1", "data": {"type": "entity", "name": "Ada", "born": 1815}} -> ContextNode("c1", "entity", {...}) -> the same record.
        """
        # Given: a category that lists entity, and a node of it with two fields
        categories = {"entity": {"type": "object"}}
        record = {"id": "c1", "data": {"type": "entity", "name": "Ada", "born": 1815}}
        # When: it is rebuilt and written back
        obj = graph_tables.to_object(record, categories=categories)["object"]
        # Then: the category and fields are on the object and the record is the same
        self.assertEqual((obj.id, obj.type, obj.fields), ("c1", "entity", {"name": "Ada", "born": 1815}))
        self.assertEqual(graph_tables.to_record(obj), record)


if __name__ == "__main__":
    unittest.main()
