"""The runner asks the run check of IF-301 v4 first (G-V4.GRAPHAPI.RULES T-03, REQ-RUN-036 to 039): what counts as given, the values of a refused
run, malformed graphs, and the trust callback left unasked. Run with: python tests/test_graph_run_rule_set.py"""
import os
import shutil
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                                         # noqa: E402
from graph_model_fakes import Script, data_node, make_edge, make_graph, transform_node   # noqa: E402
from graph_run import GraphRunner, Stage                                         # noqa: E402


def reader(graph_id="g"):
    """DB (no value) -> T -> DO: the input DB is unsupplied unless the run gives it."""
    return make_graph(graph_id, [data_node("DB"), transform_node("T"), data_node("DO")], [make_edge("DB", "T"), make_edge("T", "DO")])


class RunCheckFirst(unittest.TestCase):
    def setUp(self):
        self.script = Script()
        self.addCleanup(shutil.rmtree, self.script.folder, True)
        self.asked = []
        self.runner = GraphRunner(lambda node_id: self.asked.append(node_id) or "trusted")

    @mark.req("REQ-RUN-036", "REQ-GTB-040")
    def test_connection_fields_that_are_lists_or_objects_refuse_instead_of_raising(self):
        """Verify V-1: a connection whose to or from is a list or an object makes the run refused before any step, never an exception.

        Example: DB -> T with "to": ["T"] -> ("refused", ["DB>T"]), T not called.
        """
        for label, field, value in (("to is a list", "to", ["T"]), ("from is an object", "from", {"x": 1})):
            with self.subTest(case=label):
                # Given: the reader graph with one connection end replaced by a list or object, and a Stage with prepare on T
                g = reader()
                g["edges"][0][field] = value
                calls = []
                stage = Stage(lambda inputs, outputs, node: calls.append("T"), prepare=lambda inputs, outputs, node: None)
                # When: it is run
                result = self.runner.run(g, {"T": stage}, {})
                # Then: refused naming the connection, nothing ran
                self.assertEqual((result.status, result.named), ("refused", ["DB>T"]))
                self.assertEqual(calls, [])

    @mark.req("REQ-RUN-039")
    def test_a_stage_without_prepare_does_not_make_its_inputs_given(self):
        """Only a Stage with a prepare function counts its inputs as given; a Stage without one is refused like a plain function.

        Example: Stage(f) for T, no value for DB -> ("refused", ["DB"]), f not called.
        """
        # Given
        calls = []
        stage = Stage(lambda inputs, outputs, node: calls.append("T"))
        # When
        result = self.runner.run(reader(), {"T": stage}, {})
        # Then
        self.assertEqual((result.status, result.named, result.named_status, calls), ("refused", ["DB"], None, []))

    @mark.req("REQ-RUN-036")
    def test_a_value_given_as_none_counts_as_given(self):
        """A run input given as None is given (the key counts), so the run is not refused; the step reads None.

        Example: inputs {"DB": None} -> "done", DO == "T(None)".
        """
        # When
        result = self.runner.run(reader(), {"T": self.script.node("T")}, {"DB": None})
        # Then
        self.assertEqual((result.status, result.values["DO"]), ("done", "T(None)"))

    @mark.req("REQ-RUN-036", "REQ-RUN-038")
    def test_a_refused_run_asks_no_trust_and_keeps_the_given_data_values(self):
        """A refusal of the run check asks the trust callback for no step and answers the data values the run was given, as before.

        Example: a cycle D1 -> T1 -> D1 with inputs {"D1": "x", "zz": 1} -> values {"D1": "x"}, trust asked for nothing.
        """
        # Given
        loop = make_graph("g", [data_node("D1"), transform_node("T1")], [make_edge("D1", "T1"), make_edge("T1", "D1")])
        # When
        result = self.runner.run(loop, {"T1": self.script.node("T1")}, {"D1": "x", "zz": 1})
        # Then
        self.assertEqual((result.status, result.named, result.values), ("refused", ["D1", "T1", "D1"], {"D1": "x"}))
        self.assertEqual((self.asked, self.script.order), ([], []))

    @mark.req("REQ-RUN-036")
    def test_a_malformed_graph_is_refused_without_raising(self):
        """A step without data or nodes that are not a list is refused by the run check, not raised.

        Example: a step {"id": "T"} with no data -> refused naming "T"; nodes "x" -> refused naming "nodes".
        """
        cases = [  # label, graph, named
            ("a step without data", make_graph("g", [data_node("D1", value=1), {"id": "T"}], [make_edge("D1", "T")]), ["T"]),
            ("nodes not a list", {**make_graph("g", [], []), "nodes": "x"}, ["nodes"]),
        ]
        for label, graph, named in cases:
            with self.subTest(case=label):
                # When
                result = self.runner.run(graph, {"T": self.script.node("T")}, {})
                # Then
                self.assertEqual((result.status, result.named, result.values), ("refused", named, {}))



if __name__ == "__main__":
    unittest.main()
