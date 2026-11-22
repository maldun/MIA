"""The save path of the Workflow management on the rule set (G-V4.GRAPHAPI.RULES T-02, REQ-WFM-162 to 164, REQ-WFM-150, 154, 155 changed):
order of the checks (kind, rules, records), the field `rules` of a refusal, `named` as the parts of every item, check_graph as the flat view.
Files backend in a fresh folder per test. Run with: python tests/test_graph_model_rule_set.py"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                                                        # noqa: E402
from graph_model_fakes import FakeGraphTables, data_node, make_edge, make_graph, transform_node     # noqa: E402
from graph_model import GraphModel, check_graph                                                 # noqa: E402
from graph_rule_set import rule_report                                                          # noqa: E402
from storage import Storage                                                                     # noqa: E402
from storage_files import FileBackend                                                           # noqa: E402

TABLES = ("graph_nodes", "graph_edges", "graphs")


def doubled_writer(graph_id="g"):
    """T1 and T2 both write D2, and the connection D1>T1 is there twice: two broken rules, duplicate_connection before single_writer."""
    nodes = [data_node("D1", value="x"), transform_node("T1"), transform_node("T2"), data_node("D2")]
    edges = [make_edge("D1", "T1"), make_edge("D1", "T1"), make_edge("D1", "T2"), make_edge("T1", "D2"), make_edge("T2", "D2")]
    return make_graph(graph_id, nodes, edges)


class SaveOnTheRuleSet(unittest.TestCase):
    def setUp(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        self.storage = Storage(FileBackend(folder))
        self.model = GraphModel(self.storage, "anna")

    def counts(self):
        return {t: sum(len(self.storage.history(t, i)) for i in self.storage.ids(t)) for t in TABLES}

    @mark.req("REQ-WFM-162", "REQ-GTB-040")
    def test_connection_fields_that_are_lists_or_objects_are_refused_not_raised(self):
        """Verify V-1: a connection whose from is a list is refused with the rule report; one whose role is a list breaks no rule and no record check
        (a connection's data is free in IF-301) and is saved. Neither raises.

        Example: from ["D1"] -> refused, rules [connection_endpoints ["D1>T1"]], nothing stored; role ["x"] -> saved.
        """
        def odd(change, graph_id):
            graph = make_graph(graph_id, [data_node("D1", value="x"), transform_node("T1"), data_node("D2")], [make_edge("D1", "T1"), make_edge("T1", "D2")])
            change(graph["edges"][0])
            return graph
        # Given: a sound graph D1 -> T1 -> D2 whose first connection has a list as its start
        # When: it is saved
        result = self.model.save_graph(odd(lambda e: e.update({"from": ["D1"]}), "odd-from"))
        # Then: refused naming the connection, nothing stored
        self.assertEqual((result.saved, [(i["rule"], i["parts"]) for i in result.rules]), (False, [("connection_endpoints", ["D1>T1"])]))
        self.assertEqual(self.counts(), {t: 0 for t in TABLES})
        # And: the same graph with a list as the role of that connection is saved, without an exception
        self.assertTrue(self.model.save_graph(odd(lambda e: e["data"].update({"role": ["x"]}), "odd-role")).saved)

    @mark.req("REQ-WFM-163", "REQ-WFM-150")
    def test_a_refusal_carries_the_rule_report_and_names_every_part(self):
        """A graph with two broken rules is refused with the rule report in `rules`; `named` is the parts of both items in order; nothing stored.

        Example: rules == [duplicate_connection ["D1>T1"], single_writer ["D2"]]; named == ["D1>T1", "D2"]; rule and detail None.
        """
        # Given
        graph = doubled_writer()
        # When
        result = self.model.save_graph(graph)
        # Then
        self.assertEqual([i["rule"] for i in result.rules], ["duplicate_connection", "single_writer"])
        self.assertEqual(result.rules, rule_report(graph))
        self.assertEqual((result.saved, result.version, result.named, result.rule, result.detail), (False, None, ["D1>T1", "D2"], None, None))
        self.assertEqual(self.counts(), {t: 0 for t in TABLES})

    @mark.req("REQ-WFM-154")
    def test_the_kind_is_checked_before_the_rules(self):
        """An unknown kind on a graph that also breaks rules is refused naming the field `kind` only, with no rule report.

        Example: kind "swarm" plus two broken rules -> (False, schema_break, kind), rules None.
        """
        for kind in ("swarm", None):
            with self.subTest(kind=kind):
                # Given
                graph = {**doubled_writer(), "kind": kind}
                # When
                result = self.model.save_graph(graph)
                # Then
                self.assertEqual((result.saved, result.named, result.rule, result.detail, result.rules), (False, [], "schema_break", "kind", None))

    @mark.req("REQ-WFM-162")
    def test_the_rules_come_before_the_record_checks(self):
        """A graph that breaks a rule and a record check is refused for the rule; a graph that breaks only a record check names the record rule.

        Example: a second writer plus a connection whose data is "x" -> rules [single_writer]; the data "x" alone -> (schema_break, data), rules None.
        """
        # Given: the second writer and a connection with data that is not an object
        graph = doubled_writer()
        del graph["edges"][1]
        graph["edges"][-1]["data"] = "x"
        # When
        both = self.model.save_graph(graph)
        # Then
        self.assertEqual([i["rule"] for i in both.rules], ["single_writer"])
        # Given: only the record fault
        sound = make_graph("g", [data_node("D1", value="x"), transform_node("T1"), data_node("D2")], [make_edge("D1", "T1"), make_edge("T1", "D2")])
        sound["edges"][-1]["data"] = "x"
        # When
        record = self.model.save_graph(sound)
        # Then
        self.assertEqual((record.saved, record.rule, record.detail, record.rules), (False, "schema_break", "data", None))

    @mark.req("REQ-WFM-162")
    def test_a_saved_graph_has_no_rule_report(self):
        """A sound graph is saved; its result carries no rule report, on the Storage layer and on the fake.

        Example: SaveResult(True, 1, [], None, None, None).
        """
        sound = make_graph("g", [data_node("D1", value="x"), transform_node("T1"), data_node("D2")], [make_edge("D1", "T1"), make_edge("T1", "D2")])
        for label, model in (("storage", self.model), ("fake", GraphModel(FakeGraphTables()))):
            with self.subTest(tables=label):
                # When
                result = model.save_graph(sound)
                # Then
                self.assertEqual((result.saved, result.version, result.named, result.rules), (True, 1, [], None))

    @mark.req("REQ-WFM-162")
    def test_the_fake_tables_are_refused_by_the_same_rules(self):
        """The fake of the red tests of G-V2.MODEL goes through the same rule report.

        Example: doubled_writer on FakeGraphTables -> named ["D1>T1", "D2"], rules == rule_report.
        """
        # Given
        graph = doubled_writer()
        # When
        result = GraphModel(FakeGraphTables()).save_graph(graph)
        # Then
        self.assertEqual((result.saved, result.named, result.rules), (False, ["D1>T1", "D2"], rule_report(graph)))

    @mark.req("REQ-WFM-155")
    def test_a_context_graph_is_refused_by_the_context_rules_only(self):
        """A context graph with a cycle and a repeated step ID names only step_identity (the cycle is no context rule).

        Example: c1 -> c2 -> c1 and c1 twice -> rules [step_identity ["c1"]].
        """
        # Given
        nodes = [{"id": "c1", "data": {"type": "entity"}}, {"id": "c2", "data": {"type": "entity"}}, {"id": "c1", "data": {"type": "entity"}}]
        edges = [{"id": "a", "from": "c1", "to": "c2", "data": {}}, {"id": "b", "from": "c2", "to": "c1", "data": {}}]
        graph = {**make_graph("cx", nodes, edges), "kind": "context"}
        # When
        result = self.model.save_graph(graph)
        # Then
        self.assertEqual((result.saved, result.named, [i["rule"] for i in result.rules]), (False, ["c1"], ["step_identity"]))


class FlatView(unittest.TestCase):
    @mark.req("REQ-WFM-164")
    def test_check_graph_is_the_parts_of_every_item_in_order(self):
        """check_graph lists the parts of every item of the rule report, in order, repeats across items kept.

        Example: doubled_writer -> ["D1>T1", "D2"]; a step without data and a duplicate -> step_kind parts before duplicate_connection parts.
        """
        # Given
        graph = doubled_writer()
        # When / Then
        self.assertEqual(check_graph(graph), [p for i in rule_report(graph) for p in i["parts"]])
        self.assertEqual(check_graph(graph), ["D1>T1", "D2"])

    @mark.req("REQ-WFM-164")
    def test_check_graph_never_raises_on_a_malformed_graph(self):
        """A step without data or a connection to a missing step is named, not raised (the older check raised KeyError).

        Example: a connection D1>X9 to a missing step -> ["D1>X9"].
        """
        # Given
        graph = make_graph("g", [data_node("D1"), transform_node("T1")], [make_edge("D1", "T1"), make_edge("D1", "X9")])
        # When / Then
        self.assertEqual(check_graph(graph), ["D1>X9"])


if __name__ == "__main__":
    unittest.main()
