"""Unit tests of the record checks of the Graph tables (N-3.2, G-V2.STORE T-01) beyond the acceptance tests: edge cases found while writing check_record.
Run with: python tests/test_graph_record_checks.py"""
import os
import shutil
import sys
import http.server
import tempfile
import threading
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


def nested_record(levels):
    """A data node record with exactly `levels` levels of objects: the record is level 1, its data level 2."""
    value = {}
    for _ in range(levels - 3):
        value = {"k": value}
    return {"id": "n", "data": {"type": "data", "value": value}}


class RecordCheckBounds(unittest.TestCase):
    def test_exactly_200_levels_are_accepted_and_201_refused(self):
        """F-16: the boundary of REQ-GTB-027, the record is level 1.

        Example: nested_record(200) -> None; nested_record(201) -> schema_break "data"; 1000 levels -> schema_break "data".
        """
        # When/Then
        self.assertIsNone(graph_tables.check_record("graph_nodes", nested_record(200)))
        for levels in (201, 1000):
            self.assertEqual(graph_tables.check_record("graph_nodes", nested_record(levels)), {"rule": "schema_break", "detail": "data"}, levels)

    def test_the_validator_cache_is_bounded_and_shares_equal_schemas(self):
        """F-16: 20 000 distinct categories keep the cache at its bound, 1000 equal ones (fresh dicts) keep one entry.

        Example: 20 000 categories {"t": {"type": "object", "title": str(i)}} -> len(_validators) <= _MAX_VALIDATORS; 1000 equal -> 1.
        """
        record = {"id": "n", "data": {"type": "t"}}
        # Given/When: distinct schemas
        graph_tables._validators.clear()
        for i in range(20000):
            graph_tables.check_record("graph_nodes", record, categories={"t": {"type": "object", "title": str(i)}})
        # Then: bounded
        self.assertLessEqual(len(graph_tables._validators), graph_tables._MAX_VALIDATORS)
        # Given/When: equal schemas in fresh dicts
        graph_tables._validators.clear()
        for _ in range(1000):
            graph_tables.check_record("graph_nodes", record, categories={"t": {"type": "object", "title": "same"}})
        # Then: one entry
        self.assertEqual(len(graph_tables._validators), 1)


class ScalarsAndTuplesAreLevels(unittest.TestCase):
    def test_a_scalar_is_a_level_of_a_record(self):
        """F-23 (sixth Verify run, mutant G6): a deepest value of any kind counts as a level.
        Example: a node whose deepest value (an empty object, an empty list or the number 7) is at level 200 -> None; at level 201 -> schema_break "data"; a tuple counts like a list.
        """
        # Given: the record is level 1, its data level 2, the value inside data is level 3
        def record(leaf, levels, container):
            value = leaf
            for _ in range(levels - 3):
                value = container(value)
            return {"id": "n", "data": {"type": "data", "value": value}}
        for name, leaf in (("empty object", {}), ("empty list", []), ("scalar", 7), ("empty tuple", ())):
            for container in (lambda v: {"k": v}, lambda v: [v], lambda v: (v,)):
                # When / Then
                with self.subTest(leaf=name):
                    self.assertIsNone(graph_tables.check_record("graph_nodes", record(leaf, 200, container)))
                    self.assertEqual(graph_tables.check_record("graph_nodes", record(leaf, 201, container)), {"rule": "schema_break", "detail": "data"})

    def test_tuples_that_are_cyclic_shared_or_deep_are_refused_within_a_second(self):
        """F-24 (sixth Verify run): a tuple was no container to the checks, so such records were walked without end or raised a RecursionError.
        Example: a record that contains itself through a tuple, a DAG of tuples 60 levels deep and a tuple nested 5000 deep -> schema_break "data" from check_record and to_object, each within one second.
        """
        # Given: the three records
        loop = []
        loop.append((loop,))
        shared = ()
        for _ in range(60):
            shared = (shared, shared)
        deep = ()
        for _ in range(5000):
            deep = (deep,)
        refusal = {"rule": "schema_break", "detail": "data"}
        for name, value in (("cyclic", loop), ("shared", shared), ("deep", deep)):
            record = {"id": "n", "data": {"type": "data", "value": value}}
            for label, call, expected in (("check_record", lambda r=record: graph_tables.check_record("graph_nodes", r), refusal),
                                          ("to_object", lambda r=record: graph_tables.to_object(r), {"refused": refusal})):
                outcome = []

                def run(call=call):
                    try:
                        outcome.append(call())
                    except BaseException as err:    # the finding is the exception itself: record it for the assertion
                        outcome.append(type(err).__name__)
                # When: the call runs in a thread with a time limit, so a hang fails the test
                thread = threading.Thread(target=run, daemon=True)
                thread.start()
                thread.join(1)
                # Then
                with self.subTest(record=name, call=label):
                    self.assertFalse(thread.is_alive(), "no answer within one second")
                    self.assertEqual(outcome, [expected])

    def test_a_tuple_holding_a_nan_is_named_like_a_list_holding_one(self):
        """F-24: the path of a number that is not finite goes through a tuple as it goes through a list.
        Example: data {"type": "data", "value": (1, float("nan"))} is refused with the same detail as the value [1, nan].
        """
        # Given / When
        as_list = graph_tables.check_record("graph_nodes", {"id": "n", "data": {"type": "data", "value": [1, float("nan")]}})
        as_tuple = graph_tables.check_record("graph_nodes", {"id": "n", "data": {"type": "data", "value": (1, float("nan"))}})
        # Then
        self.assertIsNotNone(as_list)
        self.assertEqual(as_tuple, as_list)


class RecordCheckRemoteReference(unittest.TestCase):
    def test_a_remote_reference_of_a_category_schema_is_never_fetched(self):
        """F-17: untrusted text gets no network access; a $ref to a URL must not make the checker send a request.

        Example: schema {"properties": {"x": {"$ref": "http://127.0.0.1:<port>/s.json"}}} -> schema_break "type", the server saw 0 requests.
        """
        # Given: a local server that counts its requests, and a category schema that points to it
        requests = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                body = b'{"type": "string"}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass
        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = "http://127.0.0.1:%d/s.json" % server.server_port
        categories = {"entity": {"type": "object", "properties": {"x": {"$ref": url}}}}
        graph_tables._validators.clear()
        # When/Then: both tables refuse and no request arrives
        results = [graph_tables.check_record(table, {"id": "n", "data": {"type": "entity", "x": 1}}, categories=categories)
                   for table in ("graph_nodes", "context_nodes")]
        self.assertEqual(requests, [])
        self.assertEqual(results, [{"rule": "schema_break", "detail": "type"}] * 2)

    def test_a_recursion_error_is_a_schema_break_naming_data_never_a_record_identity(self):
        """F-30 (eighth Verify run): the JSON-schema validator recursed on a legal 190-level node against a recursive category schema; from a deep caller stack
        the RecursionError was caught by the catch-all and reported as record_identity "record", as if the record were malformed.

        Example: x nested 190 levels against {"$ref": "#/$defs/v"} with v = an integer or a list of v -> None at 0 frames and, at 600 frames, None or
        schema_break "data" ("cannot be checked", as for a record nested too deep), never record_identity; a RecursionError raised inside the checks gives schema_break "data".
        """
        # Given: a legal context node and a category whose schema refers to itself
        nested = 7
        for _ in range(190):
            nested = [nested]
        record = {"id": "n", "data": {"type": "entity", "x": nested}}
        value = {"type": ["integer", "array"], "items": {"$ref": "#/$defs/v"}}
        categories = {"entity": {"type": "object", "$defs": {"v": value}, "properties": {"x": {"$ref": "#/$defs/v"}}}}
        cannot_check = {"rule": "schema_break", "detail": "data"}
        outcome = []

        def run(left):
            if left:
                return run(left - 1)
            try:
                outcome.append(graph_tables.check_record("context_nodes", record, categories=categories))
            except BaseException as err:
                outcome.append(("raised", type(err).__name__))

        # When: checked from 0 and from 600 frames, each in a thread with a time limit
        answers = []
        for frames in (0, 600):
            del outcome[:]
            thread = threading.Thread(target=run, args=(frames,), daemon=True)
            thread.start()
            thread.join(10)
            self.assertFalse(thread.is_alive(), "no answer within 10 seconds at %d frames" % frames)
            answers.append(list(outcome))
        # Then: the legal record is accepted at 0 frames, and deep down it is accepted or cannot be checked, never a violation of the record
        self.assertEqual(answers[0], [None])
        self.assertIn(answers[1], ([None], [cannot_check]))
        # And: a RecursionError from inside the checks is the same answer
        original = graph_tables._check

        def exhausted(*args):
            raise RecursionError("maximum recursion depth exceeded")
        graph_tables._check = exhausted
        try:
            self.assertEqual(graph_tables.check_record("context_nodes", record, categories=categories), cannot_check)
        finally:
            graph_tables._check = original

    def test_a_local_reference_still_works(self):
        """The registry that refuses remote references keeps `#/$defs/...` working.

        Example: {"$defs": {"s": {"type": "string"}}, "properties": {"x": {"$ref": "#/$defs/s"}}}: x 1 -> schema_break "x", x "a" -> None.
        """
        # Given: a category whose schema refers to its own `$defs`
        categories = {"entity": {"type": "object", "$defs": {"s": {"type": "string"}}, "properties": {"x": {"$ref": "#/$defs/s"}}}}
        # When / Then: the reference is followed, so a wrong x is named and a right x passes
        self.assertEqual(graph_tables.check_record("context_nodes", {"id": "n", "data": {"type": "entity", "x": 1}}, categories=categories),
                         {"rule": "schema_break", "detail": "x"})
        self.assertIsNone(graph_tables.check_record("context_nodes", {"id": "n", "data": {"type": "entity", "x": "a"}}, categories=categories))


if __name__ == "__main__":
    unittest.main()
