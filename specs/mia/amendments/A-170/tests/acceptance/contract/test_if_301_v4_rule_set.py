"""IF-301 v4, the rule set of graphs (A-170, D-417, D-419): the contract suite runs every golden example 24 to 31 against the mock
(tests/helpers/mocks/if_301_graph_tables_v4.py, stage 1, green) and the real module graph_rule_set of N-3.2 (stage 2). The cases of v1 to v3 stay in
test_if_301_graph_tables.py and test_if_301_v2_graph_tables.py, unchanged (REQ-GTB-052). Expected values are exact (TR-RULES-001); the mock and the real
module must agree on every case (TR-RULES-007). Protected after the Plan gate.

Run with: python tests/acceptance/contract/test_if_301_v4_rule_set.py
"""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(REPO, "tests", "helpers", "mocks"))

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402
from rules_graphs import TEXT, connection, converted_skill, data, graph, step, transform   # noqa: E402

IF = "IF-301"
WORKFLOW = ["step_identity", "step_kind", "connection_endpoints", "duplicate_connection", "adjacency", "single_writer", "stop_limit", "cycle"]
CONTEXT = ["step_identity", "connection_endpoints", "duplicate_connection"]


def subject(kind):
    """The provider: the v4 mock, or the real module graph_rule_set loaded from the repository (never a cached module of the same name)."""
    if kind == "mock":
        from if_301_graph_tables_v4 import RuleSetV4Mock
        return RuleSetV4Mock()
    spec = importlib.util.spec_from_file_location("graph_rule_set_real", os.path.join(REPO, "graph_rule_set.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def item(rule, parts):
    return {"rule": rule, "parts": list(parts), "text": TEXT[rule]}


def golden26():
    return graph([data("d1"), transform("t1"), transform("t2")], [connection("e1", "d1", "t1"), connection("e2", "t1", "d1"), connection("e3", "t2", "d1")])


@contract
class RuleSetV4Contract(unittest.TestCase):

    @mark.req("IF-301", "REQ-GTB-033", "REQ-GTB-034", "REQ-GTB-035", "REQ-GTB-036")
    @each_provider(IF, make=subject)
    def test_golden_24_the_registry(self, rules):
        """TC-IF-301-27: kinds() equals the registry of the contract; a changed answer does not change the next one.

        Example: kinds() == {"workflow": {"rules": [eight names], "runs": True}, "context": {"rules": [three names], "runs": False}}.
        """
        # Given: the provider; When: kinds() is read, changed and read again
        expected = {"workflow": {"rules": WORKFLOW, "runs": True}, "context": {"rules": CONTEXT, "runs": False}}
        first = rules.kinds()
        self.assertEqual(first, expected)
        first["workflow"]["rules"].append("ninth")
        first["swarm"] = {"rules": [], "runs": True}
        # Then: the second answer is the registry as before
        self.assertEqual(rules.kinds(), expected)

    @mark.req("IF-301", "REQ-GTB-037", "REQ-GTB-038")
    @each_provider(IF, make=subject)
    def test_golden_25_a_sound_skill(self, rules):
        """TC-IF-301-28: the converted chat skill breaks no rule, with and without its kind.

        Example: rule_report(chat) == [] and rule_report(chat without "kind") == [].
        """
        # Given: the stored form of the converted chat skill, once with "kind": "workflow", once without the field
        chat = converted_skill("chat.md")
        with_kind = dict(chat, kind="workflow")
        without = {k: v for k, v in chat.items() if k != "kind"}
        # When: each is checked; Then: both reports are empty
        self.assertEqual((rules.rule_report(with_kind), rules.rule_report(without)), ([], []))

    @mark.req("IF-301", "REQ-GTB-037", "REQ-GTB-046", "REQ-GTB-048")
    @each_provider(IF, make=subject)
    def test_golden_26_several_rules_in_order(self, rules):
        """TC-IF-301-29: d1 -> t1 -> d1 with a second writer t2 -> d1 gives single_writer, then cycle.

        Example: [single_writer ["d1"], cycle ["d1", "t1", "d1"]].
        """
        # Given: the graph of golden 26; When: it is checked; Then: exactly the two items, in registry order
        self.assertEqual(rules.rule_report(golden26()), [item("single_writer", ["d1"]), item("cycle", ["d1", "t1", "d1"])])

    @mark.req("IF-301", "REQ-GTB-043", "REQ-GTB-048")
    @each_provider(IF, make=subject)
    def test_golden_27_the_cycle_waits_for_known_steps(self, rules):
        """TC-IF-301-30: golden 26 plus a connection e9 to the missing z gives connection_endpoints and single_writer, and no cycle.

        Example: [connection_endpoints ["e9"], single_writer ["d1"]].
        """
        # Given: the graph of golden 26 plus e9 from t1 to the missing z
        g = golden26()
        g["edges"].append(connection("e9", "t1", "z"))
        # When: it is checked; Then: rule 3 and rule 6, and rule 8 is not asked (Q-5)
        self.assertEqual(rules.rule_report(g), [item("connection_endpoints", ["e9"]), item("single_writer", ["d1"])])

    @mark.req("IF-301", "REQ-GTB-035")
    @each_provider(IF, make=subject)
    def test_golden_28_context_graphs_keep_rule_four(self, rules):
        """TC-IF-301-31: two context connections c1 -> c2 give duplicate_connection naming e2; a context cycle breaks no rule.

        Example: [duplicate_connection ["e2"]] and [].
        """
        # Given: a context graph with e1, e2 both from c1 to c2, and one with c1 -> c2 -> c1 between steps of one category
        doubled = graph([step("c1", "entity"), step("c2", "entity")], [connection("e1", "c1", "c2"), connection("e2", "c1", "c2")], kind="context")
        cycle = graph([step("c1", "entity"), step("c2", "entity")], [connection("e1", "c1", "c2"), connection("e2", "c2", "c1")], kind="context")
        # When: each is checked; Then: the first names e2, the second nothing
        self.assertEqual(rules.rule_report(doubled), [item("duplicate_connection", ["e2"])])
        self.assertEqual(rules.rule_report(cycle), [])

    @mark.req("IF-301", "REQ-GTB-039", "REQ-GTB-049")
    @each_provider(IF, make=subject)
    def test_golden_29_an_unknown_kind_and_a_kind_that_cannot_run(self, rules):
        """TC-IF-301-32: kind swarm with a cycle gives only unknown_kind in both operations; a context graph's run check gives only kind_cannot_run.

        Example: run_check(context) == {"status": "refused", "broken": [{"kind": "kind", "rule": "kind_cannot_run", "parts": ["context"], ...}]}.
        """
        # Given: the graph of golden 26 under the kind swarm, and an empty context graph
        swarm = dict(golden26(), kind="swarm")
        context = graph([step("c1", "entity")], [], kind="context")
        # When: they are checked and run checked
        # Then: unknown_kind alone, in the rule report and in the run check
        self.assertEqual(rules.rule_report(swarm), [item("unknown_kind", ["swarm"])])
        self.assertEqual(rules.run_check(swarm), {"status": "refused", "broken": [dict({"kind": "kind"}, **item("unknown_kind", ["swarm"]))]})
        # And: kind_cannot_run alone for the context graph
        self.assertEqual(rules.run_check(context), {"status": "refused", "broken": [dict({"kind": "kind"}, **item("kind_cannot_run", ["context"]))]})

    @mark.req("IF-301", "REQ-GTB-050", "REQ-GTB-051")
    @each_provider(IF, make=subject)
    def test_golden_30_inputs_given_or_not(self, rules):
        """TC-IF-301-33: chat without values is refused for input.text of step.converse; with "hello" and with None for input.text it is ready.

        Example: run_check(chat, {"input.text": None}) == {"status": "ready", "broken": []} (a given value of None counts as given).
        """
        # Given: the converted chat skill
        chat = converted_skill("chat.md")
        # When: it is run checked without values, with "hello" and with None for input.text
        # Then: refused with one unsupplied_input; ready twice
        self.assertEqual(rules.run_check(chat), {"status": "refused", "broken": [
            {"kind": "input", "rule": "unsupplied_input", "step": "step.converse", "input": "input.text", "parts": ["input.text"],
             "text": TEXT["unsupplied_input"]}]})
        self.assertEqual(rules.run_check(chat, {"input.text": "hello"}), {"status": "ready", "broken": []})
        self.assertEqual(rules.run_check(chat, {"input.text": None}), {"status": "ready", "broken": []})

    @mark.req("IF-301", "REQ-GTB-040")
    @each_provider(IF, make=subject)
    def test_golden_31_malformed_graphs(self, rules):
        """TC-IF-301-34: five malformed graphs each give a list with the items of "Malformed input", and nothing raises.

        Example: a step that is the number 5 -> [step_identity ["5"]]; nodes "x" -> [step_identity ["nodes"]].
        """
        cases = [  # label, the input, the expected report
            ("a step that is 5", graph([5], []), [item("step_identity", ["5"])]),
            ("connection data that is a list", graph([data("a"), transform("t")], [{"id": "e1", "from": "a", "to": "t", "data": []}]), []),
            ("a step without id", graph([{"data": {"type": "data"}}], []), [item("step_identity", ["None"])]),
            ("a connection without from", graph([data("a"), transform("t")], [{"id": "e1", "to": "t", "data": {}}]), [item("connection_endpoints", ["e1"])]),
            ("nodes that is a text", {"id": "g", "nodes": "x", "edges": []}, [item("step_identity", ["nodes"])]),
        ]
        for label, given, expected in cases:
            with self.subTest(case=label):
                # Given: one malformed graph; When: it is checked; Then: the items of the contract, and no exception
                self.assertEqual(rules.rule_report(given), expected)


if __name__ == "__main__":
    unittest.main()
