"""
Acceptance tests of the rule set of G-V4.GRAPHAPI.RULES (groups RS, RD, RF, DF): TC-GTB-037 to TC-GTB-045 (REQ-GTB-033 to REQ-GTB-052).

The rule set is pure (IF-301 v4: `kinds()`, `rule_report(graph)`, `run_check(graph, given)`, module `graph_rule_set`), so these checks need no store.
Every graph is written out here with at most eight steps, and each broken graph has a sound twin that differs in one place (TR-RULES-002).
Expected values are exact: rule names, parts in their order, sentences (TR-RULES-001). The converted skills are built at test time (TR-RULES-004).

Run with: python tests/acceptance/test_rules_rule_set.py
"""

import os
import subprocess
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
from graph_rule_set import kinds, rule_report, run_check                                       # noqa: E402
from rules_graphs import (CONTEXT_RULES, WORKFLOW_RULES, connection, converted_skill, data, graph, item, master, step,  # noqa: E402
                          transform)


def rules_of(report):
    return [(i["rule"], i["parts"]) for i in report]


class RuleSetAcceptance(unittest.TestCase):

    @mark.req("REQ-GTB-033", "REQ-GTB-034", "REQ-GTB-035", "REQ-GTB-036")
    def test_the_registry_names_two_kinds_with_their_rules_in_order(self):
        """TC-GTB-037: the registry names exactly `workflow` (eight rules in order, can run) and `context` (three rules, cannot run); a caller's change does not reach it.

        Example: kinds()["workflow"] == {"rules": [step_identity, ..., cycle], "runs": True}; kinds()["context"]["runs"] is False.
        """
        # Given: the rule set of IF-301 v4, nothing else
        # When: the registry is read, the first answer changed, and the registry read again
        first = kinds()
        expected = {"workflow": {"rules": WORKFLOW_RULES, "runs": True}, "context": {"rules": CONTEXT_RULES, "runs": False}}
        self.assertEqual({k: {"rules": list(v["rules"]), "runs": v["runs"]} for k, v in first.items()}, expected)
        first["workflow"]["rules"] = list(first["workflow"]["rules"])[:1]
        first["swarm"] = {"rules": [], "runs": True}
        second = kinds()
        # Then: exactly the two kinds, the eight workflow rules in the order of D-375, the three context rules; workflow runs, context does not
        # And: the change of the first answer did not reach the second
        self.assertEqual({k: {"rules": list(v["rules"]), "runs": v["runs"]} for k, v in second.items()}, expected)

    @mark.req("REQ-GTB-035")
    def test_a_context_graph_keeps_rule_four_and_has_no_order_rules(self):
        """TC-GTB-038: two identical context connections give `duplicate_connection` naming the second; a context cycle breaks no rule.

        Example: c1 -e1-> c2, c1 -e2-> c2 gives [duplicate_connection ["e2"]]; c1 -> c2 -> c1 gives [].
        """
        # Given: a context graph with two connections e1, e2 from c1 to c2 without role or name, and a second one with a cycle c1 -> c2 -> c1
        doubled = graph([step("c1", "entity"), step("c2", "entity")], [connection("e1", "c1", "c2"), connection("e2", "c1", "c2")], kind="context")
        cycle = graph([step("c1", "entity"), step("c2", "entity")], [connection("e1", "c1", "c2"), connection("e2", "c2", "c1")], kind="context")
        # When: each is checked
        # Then: the first gives exactly duplicate_connection naming e2 (Q-3: rule 4 in full)
        self.assertEqual(rule_report(doubled), [item("duplicate_connection", ["e2"])])
        # And: the cycle and two connected steps of one category break no rule of the context kind
        self.assertEqual(rule_report(cycle), [])

    @mark.req("REQ-GTB-037", "REQ-GTB-038")
    def test_the_rule_report_lists_every_broken_rule_in_the_registry_order(self):
        """TC-GTB-039: a missing end and two writers give two items in registry order, each with its sentence; a sound graph gives []; no kind means workflow.

        Example: [connection_endpoints ["e9"], single_writer ["d"]]; rule 3 comes before rule 6 in the registry.
        """
        # Given: a workflow graph with a connection e9 to the missing step z and two transforms writing d, its sound twin, and both without `kind`
        nodes = [data("a"), transform("t1"), transform("t2"), data("d")]
        broken = graph(nodes, [connection("e1", "a", "t1"), connection("e2", "t1", "d"), connection("e3", "t2", "d"), connection("e9", "t1", "z")],
                       kind="workflow")
        sound = graph(nodes, [connection("e1", "a", "t1"), connection("e2", "t1", "d"), connection("e3", "a", "t2")], kind="workflow")
        # When: each is checked
        # Then: exactly connection_endpoints (e9) and then single_writer (d), each with its fixed sentence
        self.assertEqual(rule_report(broken), [item("connection_endpoints", ["e9"]), item("single_writer", ["d"])])
        # And: the sound graph gives an empty list
        self.assertEqual(rule_report(sound), [])
        # And: without the field `kind` the reports are the same (REQ-WFM-153)
        self.assertEqual(rule_report({k: v for k, v in broken.items() if k != "kind"}), rule_report(broken))
        self.assertEqual(rule_report({k: v for k, v in sound.items() if k != "kind"}), [])

    @mark.req("REQ-GTB-039")
    def test_an_unknown_kind_is_the_only_item(self):
        """TC-GTB-040: under the kinds `swarm`, "" and 5 a broken graph gives only `unknown_kind`, naming the kind as text.

        Example: kind "swarm" with a cycle and a missing end -> [unknown_kind ["swarm"]]; kind 5 -> [unknown_kind ["5"]].
        """
        # Given: a graph with a missing end, two writers and a cycle
        edges = [connection("e1", "d", "t1"), connection("e2", "t1", "d"), connection("e3", "t2", "d"), connection("e9", "t1", "z")]
        for kind, named in (("swarm", "swarm"), ("", ""), (5, "5")):
            with self.subTest(kind=kind):
                # When: it is checked under the kind
                report = rule_report(graph([data("d"), transform("t1"), transform("t2")], edges, kind=kind))
                # Then: exactly one item unknown_kind naming the kind; none of the broken rules is listed
                self.assertEqual(report, [item("unknown_kind", [named])])

    @mark.req("REQ-GTB-040")
    def test_a_malformed_graph_never_makes_the_check_fail(self):
        """TC-GTB-041: six malformed inputs each give a list with the items of IF-301 v4 "Malformed input" (D-418 (2)), and nothing raises.

        Example: a step that is the number 5 -> [step_identity ["5"]]; a graph that is a list -> [step_identity ["graph"]].
        """
        cases = [  # label, the input, the expected report
            ("a step that is a number", graph([5], []), [item("step_identity", ["5"])]),
            ("connection data that is a list", graph([data("a"), transform("t")], [{"id": "e1", "from": "a", "to": "t", "data": []}]), []),
            ("a step without id", graph([{"data": {"type": "data"}}], []), [item("step_identity", ["None"])]),
            ("a connection without from", graph([data("a"), transform("t")], [{"id": "e1", "to": "t", "data": {}}]),
             [item("connection_endpoints", ["e1"])]),
            ("nodes that is a text", {"id": "g", "nodes": "x", "edges": []}, [item("step_identity", ["nodes"])]),
            ("a graph that is a list", [], [item("step_identity", ["graph"])]),
        ]
        for label, given, expected in cases:
            with self.subTest(case=label):
                # Given: one malformed input
                # When: it is checked
                report = rule_report(given)
                # Then: a list with the items the contract names, and no exception escaped
                self.assertEqual(report, expected)

    @mark.req("REQ-GTB-041", "REQ-GTB-042", "REQ-GTB-043", "REQ-GTB-044", "REQ-GTB-045", "REQ-GTB-046", "REQ-GTB-047", "REQ-GTB-048")
    def test_each_rule_finds_what_it_is_for_and_nothing_else(self):
        """TC-GTB-042: per rule a graph that breaks only it gives exactly that item; its twin, different in one place, gives [].

        Example: rule 7 names the masters m1 (no stop), m2 (max_repetitions 0), m3 (max_repetitions true), then the data step d (session),
        then the transform t (two settings connections): ["m1", "m2", "m3", "d", "t"], in the order of IF-301 v4.
        """
        cases = [  # rule, broken graph, its parts, sound twin
            ("step_identity", graph([data("a"), data("a"), data("")], []), ["a", ""], graph([data("a"), data("b"), data("x/y")], [])),
            ("step_kind", graph([step("x", "loop")], []), ["x"], graph([transform("x")], [])),
            ("connection_endpoints", graph([data("a"), transform("b")], [connection("e2", "a", "z")]), ["e2"],
             graph([data("a"), transform("b")], [connection("e2", "a", "b")])),
            ("duplicate_connection", graph([data("d"), transform("t")], [connection("e1", "d", "t"), connection("e2", "d", "t")]), ["e2"],
             graph([data("d"), transform("t")], [connection("e1", "d", "t", **{"as": "x"}), connection("e2", "d", "t", **{"as": "y"})])),
            ("adjacency", graph([data("d1"), data("d2"), transform("t1"), master("m1", {"max_repetitions": 1})],
                                [connection("e1", "d1", "d2"), connection("e2", "t1", "m1")]), ["e1", "e2"],
             graph([data("d1"), data("d2"), transform("t1")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d2")])),
            ("single_writer", graph([transform("t1"), transform("t2"), data("d")], [connection("e1", "t1", "d"), connection("e2", "t2", "d")]), ["d"],
             graph([transform("t1"), transform("t2"), data("d"), data("d2")], [connection("e1", "t1", "d"), connection("e2", "t2", "d2")])),
            ("stop_limit", graph([master("m1"), master("m2", {"max_repetitions": 0}), master("m3", {"max_repetitions": True}), data("d", session=True),
                                  data("s1"), data("s2"), transform("t")],
                                 [connection("e1", "s1", "t", role="settings"), connection("e2", "s2", "t", role="settings")]), ["m1", "m2", "m3", "d", "t"],
             graph([master("m1", {"max_seconds": 1.0}), data("d"), data("s1"), transform("t")], [connection("e1", "s1", "t", role="settings")])),
            ("cycle", graph([data("d1"), transform("t1")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1")]), ["d1", "t1", "d1"],
             graph([data("d1"), transform("t1"), data("d2")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d2")])),
        ]
        for rule, broken, parts, twin in cases:
            with self.subTest(rule=rule):
                # Given: a graph that breaks only this rule, and its sound twin
                # When: both are checked
                # Then: exactly one item with this rule and its parts; the twin gives an empty list
                self.assertEqual(rule_report(broken), [item(rule, parts)])
                self.assertEqual(rule_report(twin), [])
        # And: the pairs of rules acting on the same data (test spec, edge inputs)
        two_into_d = graph([transform("t1"), data("d")], [connection("e1", "t1", "d"), connection("e2", "t1", "d")])
        self.assertEqual(rules_of(rule_report(two_into_d)), [("duplicate_connection", ["e2"])])
        self_loop = graph([transform("T1")], [connection("T1>T1", "T1", "T1")])
        self.assertEqual(rules_of(rule_report(self_loop)), [("adjacency", ["T1>T1"]), ("cycle", ["T1", "T1"])])
        cycle_with_missing_end = graph([data("d1"), transform("t1")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1"),
                                                                      connection("e9", "t1", "z")])
        self.assertEqual(rules_of(rule_report(cycle_with_missing_end)), [("connection_endpoints", ["e9"])])
        data_to_missing = graph([data("d1")], [connection("e1", "d1", "z")])
        self.assertEqual(rules_of(rule_report(data_to_missing)), [("connection_endpoints", ["e1"])])

    @mark.req("REQ-GTB-049", "REQ-GTB-050")
    def test_the_run_check_names_the_kind_alone_then_rules_then_inputs(self):
        """TC-GTB-043: a context graph and an unknown kind are refused with only their kind; a workflow graph with rules and inputs lists the rule first.

        Example: context -> refused [kind_cannot_run ["context"]]; two writers of d and an unsupplied q -> [single_writer ["d"], unsupplied_input ["q"]].
        """
        # Given: a context graph that also has two identical connections
        context = graph([step("c1", "entity"), step("c2", "entity")], [connection("e1", "c1", "c2"), connection("e2", "c1", "c2")], kind="context")
        # And: a graph of kind swarm with a cycle
        swarm = graph([data("d1"), transform("t1")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1")], kind="swarm")
        # And: a workflow graph with two writers of d and a step t3 reading q, which nothing supplies
        rules_and_input = graph([transform("t1"), transform("t2"), data("d"), data("q"), transform("t3"), data("out")],
                                [connection("e1", "t1", "d"), connection("e2", "t2", "d"), connection("e3", "q", "t3"), connection("e4", "t3", "out")])
        # When: each is checked for a run, the converted chat skill with a value for input.text
        # Then: the kind is the only item for the context graph and for swarm
        self.assertEqual(run_check(context), {"status": "refused", "broken": [
            {"kind": "kind", "rule": "kind_cannot_run", "parts": ["context"], "text": item("kind_cannot_run", [])["text"]}]})
        self.assertEqual(run_check(swarm), {"status": "refused", "broken": [
            {"kind": "kind", "rule": "unknown_kind", "parts": ["swarm"], "text": item("unknown_kind", [])["text"]}]})
        # And: the workflow graph names single_writer first and the unsupplied input second
        said = run_check(rules_and_input)
        self.assertEqual(said["status"], "refused")
        self.assertEqual([(b["kind"], b["rule"], b["parts"]) for b in said["broken"]],
                         [("rule", "single_writer", ["d"]), ("input", "unsupplied_input", ["q"])])
        # And: chat with its value is ready with an empty list (AC-018)
        self.assertEqual(run_check(converted_skill("chat.md"), {"input.text": "hello"}), {"status": "ready", "broken": []})

    @mark.req("REQ-GTB-051")
    def test_an_input_nobody_supplies_is_named_with_its_step(self):
        """TC-GTB-044: chat without values names step.converse and input.text; a graph value, a writer, settings and order connections are not named.

        Example: run_check(chat)["broken"] == [{"kind": "input", "rule": "unsupplied_input", "step": "step.converse", "input": "input.text", ...}].
        """
        # Given: the converted chat skill without values
        chat = converted_skill("chat.md")
        # When: it is checked for a run with no values given
        said = run_check(chat)
        # Then: one item unsupplied_input with the step step.converse and the input input.text (AC-018)
        self.assertEqual(said, {"status": "refused", "broken": [{"kind": "input", "rule": "unsupplied_input", "step": "step.converse",
                                                                  "input": "input.text", "parts": ["input.text"], "text": item("unsupplied_input", [])["text"]}]})
        # And: a graph value, a data step another step writes, a settings and an order connection give no item
        supplied = graph(
            [data("v", value="x"), transform("t1"), data("w"), transform("t2"), data("out"), data("s"), data("o"), transform("t3"), data("out3")],
            [connection("e1", "v", "t1"), connection("e2", "t1", "w"), connection("e3", "w", "t2"), connection("e4", "t2", "out"),
             connection("e5", "s", "t3", role="settings"), connection("e6", "o", "t3", role="order"), connection("e7", "t3", "out3")])
        self.assertEqual(run_check(supplied), {"status": "ready", "broken": []})
        # And: a graph value of null counts as no start value, so its reader is named
        null_value = graph([data("n", value=None), transform("t"), data("out")], [connection("e1", "n", "t"), connection("e2", "t", "out")])
        self.assertEqual([(b["step"], b["input"]) for b in run_check(null_value)["broken"]], [("t", "n")])

    @mark.req("REQ-GTB-052")
    def test_the_document_form_and_its_suites_are_unchanged(self):
        """TC-GTB-045: the contract suites of the document form pass against the v4 code, and their files are byte-identical to goal/v4 (TR-RULES-009).

        Example: `git diff --quiet goal/v4 -- tests/acceptance/contract/test_if_301_graph_tables.py` exits 0 and the suite exits 0.
        """
        # Given: the contract suites of IF-301 v1, v2/v3, IF-102, IF-104 v1 (Python and JS) and IF-203 as they are on goal/v4
        suites = ["tests/acceptance/contract/test_if_301_graph_tables.py", "tests/acceptance/contract/test_if_301_v2_graph_tables.py",
                  "tests/acceptance/contract/test_if_102_storage.py", "tests/acceptance/contract/test_if_104_graph_api.py",
                  "tests/acceptance/contract/test_if_203_workflow_library.py", "tests/acceptance/contract/test_if_203_v1_transforms.py",
                  "tests/acceptance/contract/test_if_203_v2_snapshots.py", "tests/acceptance/contract/test_if_104_graph_api.test.mjs"]
        missing = [s for s in suites if not os.path.exists(os.path.join(REPO, s))]
        self.assertEqual(missing, [], "the document-form suites were not found")
        for suite in suites:
            with self.subTest(suite=suite):
                # When: the suite file is compared with goal/v4 and run
                same = subprocess.run(["git", "diff", "--quiet", "goal/v4", "--", suite], cwd=REPO).returncode
                command = ["node", "--test", suite] if suite.endswith(".mjs") else [sys.executable, suite]
                ran = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=600)
                # Then: the file is unchanged and the suite passes
                self.assertEqual(same, 0, "%s differs from goal/v4" % suite)
                self.assertEqual(ran.returncode, 0, ran.stdout[-2000:] + ran.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
