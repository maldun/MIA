"""The rule set of graphs (G-V4.GRAPHAPI.RULES T-01, IF-301 v4): edge cases the acceptance checks do not spell out. Run with: python tests/test_graph_rule_set.py"""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from graph_rule_set import kinds, rule_report, run_check                     # noqa: E402
from markers import mark                                                     # noqa: E402
from rules_graphs import TEXT, connection, data, graph, master, transform    # noqa: E402


def rules_of(report):
    return [(i["rule"], i["parts"]) for i in report]


class RuleSetUnit(unittest.TestCase):

    @mark.req("REQ-GTB-033")
    def test_the_module_does_not_import_the_workflow_management(self):
        """The rule set stands alone in N-3.2: it imports neither graph_model nor graph_run (plan T-01 notes).

        Example: the import names of graph_rule_set.py contain no graph_model.
        """
        # Given: the source of the module
        with open(os.path.join(ROOT, "graph_rule_set.py"), encoding="utf-8") as f:
            tree = ast.parse(f.read())
        # When: its imports are collected
        names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        names |= {n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        # Then: no module of N-2.3 or N-2.4.1 is among them
        self.assertFalse({"graph_model", "graph_run"} & names)

    @mark.req("REQ-GTB-033")
    def test_a_nested_change_of_the_registry_copy_does_not_reach_it(self):
        """kinds() is a deep copy: appending to a rule list of one answer leaves the next answer as it was.

        Example: kinds()["context"]["rules"].append("x") does not add "x" to the next kinds().
        """
        # Given: one answer of the registry
        first = kinds()
        # When: a rule list inside it is changed in place
        first["context"]["rules"].append("x")
        first["workflow"]["runs"] = False
        # Then: the next answer is unchanged
        self.assertEqual(kinds()["context"]["rules"], ["step_identity", "connection_endpoints", "duplicate_connection"])
        self.assertTrue(kinds()["workflow"]["runs"])

    @mark.req("REQ-GTB-037")
    def test_the_report_does_not_change_the_graph(self):
        """rule_report is pure: the graph it reads is equal before and after.

        Example: a graph with two writers is the same dict after rule_report.
        """
        # Given: a broken graph and a copy of it
        g = graph([transform("t1"), transform("t2"), data("d")], [connection("e1", "t1", "d"), connection("e2", "t2", "d")])
        before = repr(g)
        # When: it is checked
        rule_report(g)
        # Then: it is unchanged
        self.assertEqual(repr(g), before)

    @mark.req("REQ-GTB-040")
    def test_more_malformed_inputs_give_their_items(self):
        """Edges that are not a list, a connection that is not an object, data that is not an object, a non-text connection ID.

        Example: edges "x" -> [connection_endpoints ["edges"]]; a connection 7 -> [connection_endpoints ["7"]].
        """
        cases = [  # label, the input, the expected rules and parts
            ("edges that is a text", {"nodes": [], "edges": "x"}, [("connection_endpoints", ["edges"])]),
            ("a connection that is a number", graph([data("a")], [7]), [("connection_endpoints", ["7"])]),
            ("step data that is a list", graph([{"id": "a", "data": []}], []), [("step_kind", ["a"])]),
            ("a connection whose ID is a number", graph([data("a")], [{"id": 3, "from": "a", "to": "z", "data": {}}]), [("connection_endpoints", ["3"])]),
            ("a step whose ID is a list", graph([{"id": ["a"], "data": {"type": "data"}}], []), [("step_identity", ["['a']"])]),
            ("no nodes and no edges", {}, []),
        ]
        for label, given, expected in cases:
            with self.subTest(case=label):
                # Given: one malformed input; When: it is checked; Then: its items, no exception
                self.assertEqual(rules_of(rule_report(given)), expected)

    @mark.req("REQ-GTB-040", "REQ-GTB-049")
    def test_the_run_check_never_raises_on_malformed_input(self):
        """run_check gives refused with the rule items for malformed graphs, also for a graph that is not an object.

        Example: run_check([]) == {"status": "refused", "broken": [{"kind": "rule", "rule": "step_identity", "parts": ["graph"], ...}]}.
        """
        # Given: a graph that is a list, and a graph whose nodes are a text
        # When: each is checked for a run
        # Then: refused, with the rule items of the report, each marked as a rule
        self.assertEqual(run_check([]), {"status": "refused", "broken": [
            {"kind": "rule", "rule": "step_identity", "parts": ["graph"], "text": TEXT["step_identity"]}]})
        self.assertEqual([(b["kind"], b["rule"], b["parts"]) for b in run_check({"nodes": "x", "edges": [5]})["broken"]],
                         [("rule", "step_identity", ["nodes"]), ("rule", "connection_endpoints", ["5"])])

    @mark.req("REQ-GTB-048")
    def test_the_cycle_is_not_asked_while_a_step_id_repeats(self):
        """With rule 1 broken the cycle is not asked (IF-301 v4, rule 8: only while rules 1 and 3 are kept).

        Example: d1 -> t1 -> d1 plus a second step d1 gives step_identity ["d1"] and no cycle.
        """
        # Given: a cycle d1 -> t1 -> d1 and a repeated step d1
        g = graph([data("d1"), transform("t1"), data("d1")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1")])
        # When: it is checked; Then: step_identity, no cycle
        self.assertEqual(rules_of(rule_report(g)), [("step_identity", ["d1"])])

    @mark.req("REQ-GTB-047")
    def test_a_valid_stop_limit_in_seconds_or_repetitions(self):
        """A master with max_repetitions 2.0 or max_seconds 0.5 keeps rule 7; max_seconds 0, a text or null breaks it.

        Example: master m with {"max_seconds": 0} -> [stop_limit ["m"]].
        """
        for stop, broken in (({"max_repetitions": 2.0}, False), ({"max_seconds": 0.5}, False), ({"max_seconds": 0}, True),
                             ({"max_repetitions": "3"}, True), ({"max_repetitions": None}, True), ({"other": 1}, True)):
            with self.subTest(stop=stop):
                # Given: one master with this stop; When: it is checked
                report = rules_of(rule_report(graph([master("m", stop)], [])))
                # Then: stop_limit names m exactly when the stop is not valid
                self.assertEqual(report, [("stop_limit", ["m"])] if broken else [])

    @mark.req("REQ-GTB-051")
    def test_given_counts_by_its_keys(self):
        """A mapping counts by its keys (a value of None counts as given); a list or set of IDs works the same.

        Example: run_check(g, {"q": None}) and run_check(g, ["q"]) are both ready.
        """
        # Given: a step t reading q, which nothing supplies
        g = graph([data("q"), transform("t"), data("out")], [connection("e1", "q", "t"), connection("e2", "t", "out")])
        ready = {"status": "ready", "broken": []}
        # When: q is given as a key with None, as a list, as a set; Then: ready each time
        self.assertEqual(run_check(g, {"q": None}), ready)
        self.assertEqual(run_check(g, ["q"]), ready)
        self.assertEqual(run_check(g, {"q"}), ready)
        # And: a value for another step does not supply q
        self.assertEqual([b["input"] for b in run_check(g, {"other": "x"})["broken"]], ["q"])

    @mark.req("REQ-GTB-040")
    def test_connection_fields_that_are_lists_or_objects_never_raise(self):
        """REQ-GTB-040 (Verify V-1): a connection whose from, to, id, role or as is a list or an object gives a report, never an exception.

        Example: a connection {"id": "e1", "from": ["a"], "to": "t"} gives [connection_endpoints ["e1"]]; with "role": ["x"] the graph stays sound.
        """
        from graph_model import check_graph
        nodes = [data("a"), transform("t"), data("out")]
        cases = [  # label, the odd connection, the rule report expected
            ("from is a list", {"id": "e1", "from": ["a"], "to": "t", "data": {}}, [("connection_endpoints", ["e1"])]),
            ("to is an object", {"id": "e1", "from": "a", "to": {"x": 1}, "data": {}}, [("connection_endpoints", ["e1"])]),
            ("id is a list", {"id": ["e1"], "from": "a", "to": "t", "data": {}}, []),
            ("role is a list", {"id": "e1", "from": "a", "to": "t", "data": {"role": ["x"]}}, []),
            ("as is an object", {"id": "e1", "from": "a", "to": "t", "data": {"as": {"x": 1}}}, []),
        ]
        for label, odd, expected in cases:
            with self.subTest(case=label):
                # Given: a sound graph a -> t -> out whose first connection is replaced by the odd one
                g = graph(nodes, [odd, connection("e2", "t", "out")])
                # When: the rule report, the run check and check_graph are asked
                # Then: no exception; the report names only what the contract says
                self.assertEqual(rules_of(rule_report(g)), expected)
                self.assertIsInstance(run_check(g)["broken"], list)
                self.assertIsInstance(check_graph(g), list)
        # And: two identical odd connections are still found as duplicates
        twice = graph(nodes, [{"id": "e1", "from": "a", "to": "t", "data": {"role": ["x"]}},
                              {"id": "e3", "from": "a", "to": "t", "data": {"role": ["x"]}}, connection("e2", "t", "out")])
        self.assertEqual(rules_of(rule_report(twice)), [("duplicate_connection", ["e3"])])

    @mark.req("REQ-GTB-040", "REQ-GTB-051")
    def test_a_malformed_given_counts_as_no_values_and_never_raises(self):
        """IF-301 v4: run_check never raises; a `given` that is not a list of IDs counts as no values given (T-01 finding, settled by delegation D-423).

        Example: run_check(g, 5) == run_check(g) == refused, naming q as an unsupplied input.
        """
        # Given: a step t reading q, which nothing supplies
        g = graph([data("q"), transform("t"), data("out")], [connection("e1", "q", "t"), connection("e2", "t", "out")])
        for given in (5, object(), [["q"]], 2.5):
            with self.subTest(given=given):
                # When: the run is checked with a malformed `given`
                said = run_check(g, given)
                # Then: no exception, and q is named as if nothing were given
                self.assertEqual([b["input"] for b in said["broken"]], ["q"])

    @mark.req("REQ-GTB-051")
    def test_a_master_input_is_named_and_repeats_are_kept(self):
        """An input of a master counts too, and a data step read by two steps is named once per connection, in connection order.

        Example: q read by t and by m -> two items (t, q) and (m, q).
        """
        # Given: q read by a transform t and by a master m
        g = graph([data("q"), transform("t"), master("m", {"max_repetitions": 1}), data("o1"), data("o2")],
                  [connection("e1", "q", "t"), connection("e2", "q", "m"), connection("e3", "t", "o1"), connection("e4", "m", "o2")])
        # When: it is checked for a run
        said = run_check(g)
        # Then: both readers are named, each with q
        self.assertEqual([(b["step"], b["input"], b["parts"]) for b in said["broken"]], [("t", "q", ["q"]), ("m", "q", ["q"])])


if __name__ == "__main__":
    unittest.main()
