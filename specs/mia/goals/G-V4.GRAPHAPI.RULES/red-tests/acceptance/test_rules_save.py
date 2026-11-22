"""
Acceptance tests of saving with the rule set (group SV of G-V4.GRAPHAPI.RULES): TC-WFM-179 to TC-WFM-184
(REQ-WFM-162 to REQ-WFM-165, and the changes of REQ-WFM-150, REQ-WFM-154, REQ-WFM-155).

Every check saves on a fresh files store (helper core_stores, TR-CORE-007): a refusal happens before the first write (REQ-WFM-146), so the backend
does not change the verdict (HR-004 reference). The graphs are written out here with a sound twin where a refusal is expected (TR-RULES-002);
expected values are exact (TR-RULES-001). A refused save carries the rule report in the field `rules` of its result (ASM-8, REQ-WFM-163).

Run with: python tests/acceptance/test_rules_save.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                                                       # noqa: E402
from storage import Storage, StorageError                                                      # noqa: E402
from graph_model import GraphModel, check_graph                                                # noqa: E402
from graph_rule_set import rule_report                                                         # noqa: E402
from core_stores import fresh_backend, version_counts                                          # noqa: E402
from rules_graphs import ac017, connection, data, graph, item, step, transform                 # noqa: E402

WHO = "ann"


class RulesSaveAcceptance(unittest.TestCase):
    def setUp(self):
        self.storage = Storage(fresh_backend("files", self))
        self.model = GraphModel(self.storage, author=WHO)

    def assert_nothing_stored(self, before):
        self.assertEqual(version_counts(self.storage), before)

    @mark.req("REQ-WFM-162")
    def test_a_save_uses_the_rule_set_of_the_kind(self):
        """TC-WFM-179: two identical connections, a rule the five older rules lack, refuse the save naming `duplicate_connection` and `e2`.

        Example: in -e1-> t, in -e2-> t, t -e3-> out: refused, rules == [duplicate_connection ["e2"]] == rule_report(graph); nothing stored.
        """
        # Given: a fresh files store and a workflow graph with two identical connections e1, e2 from `in` to `t`
        doubled = graph([data("in", value="x"), transform("t"), data("out")],
                        [connection("e1", "in", "t"), connection("e2", "in", "t"), connection("e3", "t", "out")], graph_id="dup")
        before = version_counts(self.storage)
        # When: it is saved
        result = self.model.save_graph(doubled)
        # Then: the save is refused naming duplicate_connection with e2
        self.assertFalse(result.saved)
        self.assertEqual(getattr(result, "rules", None), [item("duplicate_connection", ["e2"])])
        # And: the items equal the rule report of the same graph; nothing is stored
        self.assertEqual(getattr(result, "rules", None), rule_report(doubled))
        self.assert_nothing_stored(before)
        # And: the sound twin (one connection) is saved
        self.assertTrue(self.model.save_graph(graph(doubled["nodes"], [doubled["edges"][0], doubled["edges"][2]], graph_id="dup")).saved)

    @mark.req("REQ-WFM-163", "REQ-WFM-150")
    def test_a_refused_save_carries_every_broken_rule(self):
        """TC-WFM-180: the AC-017 graph is refused carrying single_writer and then cycle; the named IDs are the parts of both, repeats kept; no table grew.

        Example: rules == [single_writer ["d1"], cycle ["d1", "t1", "d1"]]; named == ["d1", "d1", "t1", "d1"].
        """
        # Given: a fresh files store and the AC-017 graph (a cycle d1 -> t1 -> d1 and a second writer t2 -> d1)
        g = ac017()
        before = version_counts(self.storage)
        # When: it is saved
        result = self.model.save_graph(g)
        # Then: the save is refused and carries the rule report: single_writer naming d1, then cycle naming d1, t1, d1
        self.assertFalse(result.saved)
        self.assertEqual(getattr(result, "rules", None), [item("single_writer", ["d1"]), item("cycle", ["d1", "t1", "d1"])])
        self.assertEqual(getattr(result, "rules", None), rule_report(g))
        # And: the named IDs are the parts of both rules in that order, repeats kept; no table grew
        self.assertEqual(result.named, ["d1", "d1", "t1", "d1"])
        self.assert_nothing_stored(before)

    @mark.req("REQ-WFM-164")
    def test_check_graph_stays_the_flat_list_of_parts(self):
        """TC-WFM-181: check_graph gives [] for a sound graph, the cycle with its first step repeated, and for AC-017 the parts of both rules in order.

        Example: AC-017 -> ["d1"] (single_writer) + ["d1", "t1", "d1"] (cycle) == ["d1", "d1", "t1", "d1"].
        """
        # Given: a sound workflow graph, a cycle d1 -> t1 -> d1 and the AC-017 graph
        sound = graph([data("d1"), transform("t1"), data("d2")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d2")])
        cycle = graph([data("d1"), transform("t1")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1")])
        # When: each is checked with check_graph
        # Then: [], the cycle with d1 at both ends, and the parts of single_writer before those of cycle
        self.assertEqual(check_graph(sound), [])
        self.assertEqual(check_graph(cycle), ["d1", "t1", "d1"])
        self.assertEqual(check_graph(ac017()), ["d1", "d1", "t1", "d1"])

    @mark.req("REQ-WFM-165")
    def test_a_graph_that_was_never_stored_has_no_history(self):
        """TC-WFM-182: the versions of `never` and the history of its step `a` each fail with not_found, and the store stays empty (CORE V-3).

        Example: graph_versions("never") raises StorageError with code "not_found".
        """
        # Given: an empty files store
        before = version_counts(self.storage)
        # When: the versions of the graph `never` and the history of its step `a` are asked
        # Then: each fails with the reason not_found
        for ask in (lambda: self.model.graph_versions("never"), lambda: self.model.step_history("never", "a")):
            with self.assertRaises(StorageError) as caught:
                ask()
            self.assertEqual(caught.exception.code, "not_found")
        # And: the store is still empty
        self.assert_nothing_stored(before)

    @mark.req("REQ-WFM-154")
    def test_an_empty_kind_is_refused(self):
        """TC-WFM-183: a graph with "kind": None is refused naming the field `kind`, and nothing is stored (CORE V-2).

        Example: SaveResult(saved=False, ..., rule="schema_break", detail="kind").
        """
        # Given: a fresh files store and a sound graph with "kind": None
        g = graph([data("d1", value="x"), transform("t1"), data("d2")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d2")], kind=None)
        g["kind"] = None
        before = version_counts(self.storage)
        # When: it is saved
        result = self.model.save_graph(g)
        # Then: the save is refused naming the field kind, and nothing is stored
        self.assertFalse(result.saved)
        self.assertEqual(result.detail, "kind")
        self.assert_nothing_stored(before)

    @mark.req("REQ-WFM-155")
    def test_a_context_graph_is_saved_with_the_rules_of_its_kind(self):
        """TC-WFM-184: two identical context connections and an empty step ID are each refused naming the rule and its parts; nothing written.

        Example: c1 -e1-> c2, c1 -e2-> c2 -> rules [duplicate_connection ["e2"]]; a step "" -> rules [step_identity [""]].
        """
        cases = [  # label, the context graph, the expected rule report
            ("two identical connections", graph([step("c1", "entity"), step("c2", "entity")],
                                                [connection("e1", "c1", "c2"), connection("e2", "c1", "c2")], kind="context", graph_id="cx1"),
             [item("duplicate_connection", ["e2"])]),
            ("an empty step ID", graph([step("c1", "entity"), step("", "entity")], [], kind="context", graph_id="cx2"),
             [item("step_identity", [""])]),
        ]
        for label, g, expected in cases:
            with self.subTest(case=label):
                # Given: a fresh files store and the context graph
                before = version_counts(self.storage)
                # When: it is saved
                result = self.model.save_graph(g)
                # Then: it is refused naming the rule and its parts; nothing is written (Q-3, finding 7)
                self.assertFalse(result.saved)
                self.assertEqual(getattr(result, "rules", None), expected)
                self.assert_nothing_stored(before)


if __name__ == "__main__":
    unittest.main()
