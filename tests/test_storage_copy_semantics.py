"""The copy the Storage layer keeps and hands out (N-3.1, F-25, F-28) and a legal record at a deep call stack (N-3.2, F-26). Run with: python tests/test_storage_copy_semantics.py

Both shipped backends serialise to JSON, so aliasing between a caller's document and the stored one cannot be seen through them: these tests call the copy
directly and use a backend that keeps the Python objects, as a test double.
"""
import collections
import os
import shutil
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

import graph_tables                              # noqa: E402
from markers import mark                         # noqa: E402
from storage import Storage, StorageError, _copy  # noqa: E402
from storage_files import FileBackend            # noqa: E402


class ObjectBackend:
    """A test double: keeps the entries as Python objects, so what the Storage layer shares or copies stays visible."""

    def __init__(self):
        self.data = {}

    def versions(self, table, record_id):
        return self.data.get((table, record_id), [])

    def append(self, table, record_id, entry):
        self.data[(table, record_id)] = self.versions(table, record_id) + [entry]

    def ids(self, table):
        return [record_id for (name, record_id) in self.data if name == table]

    def remove(self, table, record_id):
        self.data.pop((table, record_id), None)


def nested(levels, wrap):
    leaf = 7
    for _ in range(levels):
        leaf = wrap(leaf)
    return leaf


def from_depth(frames, call, timeout=20):
    """call() run `frames` frames deep in a thread with a time limit: [result], or [("raised", type name)]."""
    outcome = []

    def run(left):
        if left:
            return run(left - 1)
        try:
            outcome.append(call())
        except StorageError as err:
            outcome.append(("StorageError", err.rule, err.detail))
        except BaseException as err:
            outcome.append(("raised", type(err).__name__))
    thread = threading.Thread(target=run, args=(frames,), daemon=True)
    thread.start()
    thread.join(timeout)
    assert not thread.is_alive(), "no answer within %s seconds" % timeout
    return outcome


class CopyOfADocument(unittest.TestCase):
    @mark.req("REQ-SLY-013")
    def test_the_copy_shares_what_the_document_shares_and_nothing_else(self):
        """F-28 (mutants C1 to C8): the docstring of _copy promises that a container named twice is copied once and that nothing is shared with the input.
        Example: doc = {"a": p, "b": [p], "c": (p,)} with the list p -> the copy has c["a"] is c["b"][0] is c["c"][0], and none of them is p.
        """
        # Given: one list named in a dict, a list and a tuple
        shared = [1, 2]
        document = {"a": shared, "b": [shared], "c": (shared,)}
        # When
        copied = _copy(document)
        # Then: equal, shared once, and no container is the caller's
        self.assertEqual(copied, document)
        self.assertIs(copied["a"], copied["b"][0])
        self.assertIs(copied["a"], copied["c"][0])
        for name, part in (("document", (document, copied)), ("a", (shared, copied["a"])), ("b", (document["b"], copied["b"])), ("c", (document["c"], copied["c"]))):
            self.assertIsNot(part[0], part[1], name)

    @mark.req("REQ-SLY-013")
    def test_a_tuple_stays_a_tuple_and_is_walked(self):
        """F-28 (mutants C5, C8): a tuple comes back as a tuple, and the containers inside it are copied (and shared with the rest of the document).
        Example: _copy((1, [2], (3,))) -> (1, [2], (3,)) with a new list inside.
        """
        inner = [2]
        copied = _copy({"t": (1, inner, (3,)), "l": inner})
        self.assertIs(type(copied["t"]), tuple)
        self.assertIs(type(copied["t"][2]), tuple)
        self.assertIsNot(copied["t"][1], inner)
        self.assertIs(copied["t"][1], copied["l"])

    @mark.req("REQ-SLY-013")
    def test_dict_subclasses_and_leaves_are_copied_as_before(self):
        """F-28: what is no plain dict, list or tuple (a subclass, a text, a number, None, another object) is left to copy.deepcopy: equal, same type, not the same container.
        Example: OrderedDict(a=[1]) comes back as an OrderedDict with a new list; "t", 1, 2.5, None come back equal.
        """
        ordered = collections.OrderedDict(a=[1])
        counter = collections.Counter("aab")
        unique = {1, 2}
        copied = _copy({"o": ordered, "n": counter, "s": unique, "t": "text", "i": 1, "f": 2.5, "z": None, "b": True})
        self.assertIs(type(copied["o"]), collections.OrderedDict)
        self.assertEqual(copied["o"], ordered)
        self.assertIsNot(copied["o"], ordered)
        self.assertIsNot(copied["o"]["a"], ordered["a"])
        self.assertIs(type(copied["n"]), collections.Counter)
        self.assertEqual((copied["s"], copied["t"], copied["i"], copied["f"], copied["z"], copied["b"]), (unique, "text", 1, 2.5, None, True))
        self.assertIsNot(copied["s"], unique)

    @mark.req("REQ-SLY-013")
    def test_a_tuple_as_a_dict_key_does_not_raise_key_error(self):
        """F-28 (latent defect): _copy({"a": 1, (1, 2): 2}) raised KeyError (the key was looked up in the memo although only values are walked); deepcopy copied it.
        Example: the copy equals the input; through Storage on the file backend the outcome is the one of before T-13 (the backend's TypeError: non-string keys are F-18), never a KeyError.
        """
        document = {"a": 1, (1, 2): 2, ("x", ("y",)): [3]}
        self.assertEqual(_copy(document), document)
        base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, base, True)
        store = Storage(FileBackend(base))
        outcome = from_depth(0, lambda: store.put("workflows", "w", {"nodes": [], "edges": [], "note": {(1, 2): 2}}, "anna"))
        self.assertNotEqual(outcome, [("raised", "KeyError")])
        self.assertIn(outcome, ([{"version": 1}], [("raised", "TypeError")]))


class StorageKeepsItsOwnCopy(unittest.TestCase):
    def setUp(self):
        self.backend = ObjectBackend()
        self.store = Storage(self.backend)

    @mark.req("REQ-SLY-013")
    def test_changing_the_callers_document_after_put_changes_nothing_stored(self):
        """F-28 (mutant C1): put keeps a copy. Example: put {"nodes": [], "edges": [], "note": [1]}, then append to the caller's lists -> get gives the document as put."""
        shared = [1]
        document = {"nodes": [], "edges": [], "note": shared, "again": shared}
        self.store.put("workflows", "w", document, "anna")
        shared.append(2)
        document["nodes"].append({"id": "x"})
        document["extra"] = 1
        self.assertEqual(self.store.get("workflows", "w")["doc"], {"nodes": [], "edges": [], "note": [1], "again": [1]})
        self.assertIsNot(self.backend.versions("workflows", "w")[0]["doc"], document)

    @mark.req("REQ-SLY-013")
    def test_changing_what_get_returns_changes_nothing_stored(self):
        """F-28 (mutant C2): get hands out a copy. Example: append to a list of the result of get -> the next get is as before; the result is not the stored object."""
        self.store.put("workflows", "w", {"nodes": [], "edges": [], "note": [1]}, "anna")
        first = self.store.get("workflows", "w")
        first["doc"]["note"].append(2)
        first["doc"]["nodes"].append(1)
        self.assertEqual(self.store.get("workflows", "w")["doc"], {"nodes": [], "edges": [], "note": [1]})
        self.assertIsNot(first, self.backend.versions("workflows", "w")[0])
        self.assertIsNot(self.store.get("workflows", "w")["doc"], self.backend.versions("workflows", "w")[0]["doc"])

    @mark.req("REQ-SLY-013")
    def test_what_the_document_shares_is_shared_in_the_stored_and_the_returned_version(self):
        """F-28 (mutants C6, C7): a sub-object named twice is kept and handed out once, so a document of 2**30 paths stays small.
        Example: {"note": p, "other": p} -> stored["doc"]["note"] is stored["doc"]["other"], and the same in the result of get.
        """
        shared = {"k": [1]}
        self.store.put("workflows", "w", {"nodes": [], "edges": [], "note": shared, "other": shared}, "anna")
        stored = self.backend.versions("workflows", "w")[0]["doc"]
        returned = self.store.get("workflows", "w")["doc"]
        for name, doc in (("stored", stored), ("returned", returned)):
            self.assertIs(doc["note"], doc["other"], name)
            self.assertIsNot(doc["note"], shared, name)


class ALegalRecordAtADeepCallStack(unittest.TestCase):
    """F-26 (seventh Verify run): a 200-level node of the graphs was refused as record_identity from a caller stack of about 400 frames, and to_object raised from 600."""
    FRAMES = (0, 500, 700)

    def setUp(self):
        self.record = {"id": "d1", "data": {"type": "data", "value": nested(197, lambda leaf: [leaf])}}   # record 1, data 2, 197 lists, a scalar at level 200
        base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, base, True)
        self.store = Storage(FileBackend(base))

    @mark.req("REQ-GTB-027")
    def test_check_record_gives_the_same_answer_at_every_stack_depth(self):
        """F-26. Example: check_record("graph_nodes", a node of 200 levels) is None called from 0, 500 and 700 frames."""
        for frames in self.FRAMES:
            with self.subTest(frames=frames):
                self.assertEqual(from_depth(frames, lambda: graph_tables.check_record("graph_nodes", self.record)), [None])

    @mark.req("REQ-GTB-027")
    def test_a_non_finite_number_is_named_at_every_stack_depth(self):
        """F-26. Example: the NaN at the end of a 190-level list in "value" is named by its path from 0 and from 700 frames, not turned into record_identity."""
        record = {"id": "d1", "data": {"type": "data", "value": [nested(190, lambda leaf: [leaf]), float("nan")]}}
        expected = "value.1"
        for frames in (0, 700):
            with self.subTest(frames=frames):
                self.assertEqual(from_depth(frames, lambda: graph_tables.check_record("graph_nodes", record)),
                                 [{"rule": "schema_break", "detail": expected}])

    @mark.req("REQ-GTB-009")
    def test_to_object_gives_an_object_at_every_stack_depth(self):
        """F-26. Example: to_object of a 200-level data node returns {"object": DataNode} from 0, 500 and 700 frames, and raises nothing."""
        for frames in self.FRAMES:
            with self.subTest(frames=frames):
                outcome = from_depth(frames, lambda: graph_tables.to_object(self.record))
                self.assertEqual([list(o) for o in outcome], [["object"]])
                self.assertEqual(outcome[0]["object"].value, self.record["data"]["value"])
                self.assertIsNot(outcome[0]["object"].value, self.record["data"]["value"])

    @mark.req("REQ-SLY-013")
    def test_put_of_a_graph_node_and_get_work_at_every_stack_depth(self):
        """F-26. Example: Storage.put("graph_nodes", "d1", a 200-level node) is stored from 0, 500 and 700 frames (never record_identity), and get returns it."""
        for frames in self.FRAMES:
            with self.subTest(frames=frames):
                record_id = "d%d" % frames
                record = dict(self.record, id=record_id)
                self.assertEqual(from_depth(frames, lambda: self.store.put("graph_nodes", record_id, record, "anna")), [{"version": 1}])
                self.assertEqual(from_depth(frames, lambda: self.store.get("graph_nodes", record_id)["doc"]), [record])


if __name__ == "__main__":
    unittest.main()
