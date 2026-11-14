"""Unit tests of the conversion between the record form and the v1 document form (N-3.2, G-V2.STORE T-03) beyond the acceptance tests.
Run with: python tests/test_graph_document_form.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import graph_tables  # noqa: E402

SESSION_DOC = {"nodes": [{"id": "q", "kind": "data"},
                         {"id": "debate", "kind": "process", "session": True, "stop": {"max_cycles": 3, "max_seconds": None}},
                         {"id": "a", "kind": "data"}],
               "edges": [{"from": "q", "to": "debate"}, {"from": "debate", "to": "a"}]}


class DocumentForm(unittest.TestCase):
    def test_a_session_node_survives_the_trip_through_records(self):
        """The other fields of a v1 node (session, stop) are kept when a document becomes records and back, and the v1 rules still accept it.

        Example: process node `debate` with session true and stop {"max_cycles": 3} -> a transform record with the same fields -> the same node.
        """
        # Given: a v1 document with a session node
        # When: it becomes records and is written back as a document
        records = graph_tables.from_document(SESSION_DOC)
        back = graph_tables.to_document(records["nodes"], records["edges"])["document"]
        # Then: the node is the same, with the same session and stop
        self.assertEqual(back["nodes"], SESSION_DOC["nodes"])
        # And: the edges have the same ends in the same order, and the v1 rules accept the document
        self.assertEqual([(e["from"], e["to"]) for e in back["edges"]], [("q", "debate"), ("debate", "a")])
        self.assertIsNone(graph_tables.validate("workflows", back))
        # And: the generated edge IDs are e1 and e2
        self.assertEqual([e["id"] for e in records["edges"]], ["e1", "e2"])

    def test_an_edge_keeps_its_id_and_json_field_through_the_document(self):
        """An edge record with an ID and a JSON field comes back with both after to_document and from_document.

        Example: {"id": "x7", "from": "a", "to": "b", "data": {"label": "y"}} -> the same record.
        """
        # Given: two nodes and an edge with its own ID and field
        nodes = [{"id": "a", "data": {"type": "data", "parameters": {}}}, {"id": "b", "data": {"type": "transform", "toolbox_id": "t"}}]
        edges = [{"id": "x7", "from": "a", "to": "b", "data": {"label": "y"}}]
        # When: they are written as a document and read back
        document = graph_tables.to_document(nodes, edges)["document"]
        back = graph_tables.from_document(document)
        # Then: the edge is the same
        self.assertEqual(back["edges"], edges)

    def test_a_document_that_is_not_one_is_refused_not_raised(self):
        """from_document names a malformed document by the v1 rule node_identity: lists missing, a node of unknown kind, an edge without ends.

        Example: {"nodes": [{"id": "n", "kind": "x"}], "edges": []} -> {"refused": {"rule": "node_identity", "detail": "n"}}.
        """
        # Given: four malformed documents
        cases = [(None, "nodes and edges must be lists"), ({"nodes": []}, "nodes and edges must be lists"),
                 ({"nodes": [{"id": "n", "kind": "x"}], "edges": []}, "n"), ({"nodes": ["n"], "edges": []}, None),
                 ({"nodes": [], "edges": [{"from": "a"}]}, "an edge needs from and to"), ({"nodes": [], "edges": ["e"]}, "an edge needs from and to")]
        for doc, detail in cases:
            with self.subTest(doc=doc):
                # When/Then: refused with node_identity and the detail
                self.assertEqual(graph_tables.from_document(doc), {"refused": {"rule": "node_identity", "detail": detail}})

    def test_a_type_without_a_document_form_is_refused(self):
        """to_document refuses a node of a type that is neither data, transform nor master, naming it.

        Example: a node of type entity -> {"refused": {"rule": "unknown_type", "detail": "entity"}}.
        """
        # Given/When/Then
        nodes = [{"id": "c1", "data": {"type": "entity"}}]
        self.assertEqual(graph_tables.to_document(nodes, []), {"refused": {"rule": "unknown_type", "detail": "entity"}})


if __name__ == "__main__":
    unittest.main()
