"""
Tests for the speech rules (behaviour.py): every detector and repair on hand-made texts, the exemption of code, idempotence, the signals in the run log, the rule block of the library entries
(and that the library nodes agree with the code), the text_rules target of the harness and the behaviour suite as a regression. Run with the MIA virtualenv: python tests/test_behaviour.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import behaviour as B                                 # noqa: E402
import harness as H                                   # noqa: E402
import metrics as M                                   # noqa: E402
from core import Core                                 # noqa: E402
from library import Library, validate_node            # noqa: E402
from run_log import RunLog                            # noqa: E402


def rules_of(text):
    return B.check_text(text)["rules"]


class Detectors(unittest.TestCase):
    def test_bold(self):
        self.assertEqual(rules_of("This is **really** important."), ["speech.no_bold"])
        self.assertEqual(B.repair_text("**Tea** or **coffee**?")["text"], "Tea or coffee?")

    def test_powers_and_names_are_not_bold(self):
        for text in ("x**2 + y**2 is a sum", "In Python 2 ** 3 is 8.", "The __init__ method.", "A lone ** is nothing."):
            self.assertEqual(rules_of(text), [], text)

    def test_emphasis_and_actions(self):
        self.assertEqual(rules_of("That is *very* kind."), ["speech.no_emphasis"])
        self.assertEqual(rules_of("*smiles* Hi! *waves* Welcome."), [])
        self.assertEqual(rules_of("*smiles* Hi! *waves* Look, *nods* ok."), ["speech.sparing_actions"])

    def test_third_action_is_cut_not_the_first(self):
        self.assertEqual(B.repair_text("*smiles* Hi! *waves* Look, *nods* ok.")["text"], "*smiles* Hi! *waves* Look, ok.")

    def test_times(self):
        self.assertEqual(B.repair_text("2*3 is 6 and 2 * 3 * 4 is 24.")["text"], "2 times 3 is 6 and 2 times 3 times 4 is 24.")
        for text in ("3 ** 2 is nine.", "Files like *.txt match.", "a * b and 5*x"):
            self.assertEqual(rules_of(text), [], text)

    def test_stage_directions(self):
        self.assertEqual(rules_of("Hello! (smiles)"), ["speech.no_stage_directions"])
        self.assertEqual(rules_of("Hello there. I wave and walk over."), ["speech.no_stage_directions"])
        self.assertEqual(rules_of("**Wow!** I smile."), ["speech.no_bold", "speech.no_stage_directions"])
        for text in ("I laughed yesterday.", "She smiles.", "If I smile at you, you smile back.", "The meeting (starts at five) is long."):
            self.assertEqual(rules_of(text), [], text)

    def test_narration_cannot_be_repaired_by_code(self):
        result = B.repair_text("I smile and say hello.")
        self.assertEqual(result["text"], "I smile and say hello.")
        self.assertEqual(result["remaining"], ["speech.no_stage_directions"])

    def test_repair_keeps_the_ends(self):
        self.assertEqual(B.repair_text("Line one.\n(smiles)")["text"], "Line one.")
        self.assertEqual(B.repair_text("(Smiles warmly) Hello.")["text"], "Hello.")
        self.assertEqual(B.repair_text("Line one.\n")["text"], "Line one.\n")

    def test_code_is_exempt(self):
        for text in ("Use `**kwargs` here.", "Example:\n```\nprint('**bold** 2*3 (smiles)')\n```\nDone."):
            self.assertEqual(rules_of(text), [], text)
            self.assertEqual(B.repair_text(text)["text"], text)
        self.assertEqual(B.repair_text("Use `a*b` and be **careful**; 3*3.")["text"], "Use `a*b` and be careful; 3 times 3.")

    def test_spans_point_into_the_text(self):
        text = "Say **this** now."
        v = B.check_text(text)["violations"][0]
        self.assertEqual(text[v["start"]:v["end"]], "**this**")
        self.assertEqual(v["rule"], "speech.no_bold")

    def test_idempotent_and_selective(self):
        text = "**Wow!** *a* *b* *c* 2*3 (smiles)"
        once = B.repair_text(text)["text"]
        self.assertEqual(B.repair_text(once)["text"], once)
        only = B.check_text(text, ["speech.no_bold"])
        self.assertEqual(only["rules"], ["speech.no_bold"])

    def test_empty(self):
        self.assertEqual(B.check_text("")["violations"], [])
        self.assertEqual(B.repair_text("")["text"], "")


class Functions(unittest.TestCase):
    def test_apply_rules(self):
        result = B.apply_rules("**Hi.** I wave. 2*3")
        self.assertEqual(result["text"], "Hi. I wave. 2 times 3")
        self.assertIn("speech.no_bold", result["fixed"])
        self.assertEqual(result["remaining"], ["speech.no_stage_directions"])
        only_check = B.apply_rules("**Hi**", repair=False)
        self.assertEqual(only_check["text"], "**Hi**")

    def test_describe_lists_every_rule(self):
        self.assertEqual([r["name"] for r in B.describe()], list(B.RULES))


class Signals(unittest.TestCase):
    def test_signals_in_the_run_log(self):
        with tempfile.TemporaryDirectory() as folder:
            log = RunLog(folder)
            run = log.start("chat", input="hi")
            found = B.record_signals(log, run.id, "**Hi** *smiles* *waves* *nods*", node="converse")
            self.assertEqual(sorted(v["rule"] for v in found), ["speech.no_bold", "speech.sparing_actions"])
            table = log.signals_by_rule()
            self.assertEqual(table["speech.no_bold"], {"penalty": 1, "reward": 0, "runs": 1})
            run.finish("done", "x")
            joined = [r for r in log.read() if r["id"] == run.id]
            self.assertEqual(len(joined[0]["signals"]), 2)

    def test_clean_text_leaves_no_signal(self):
        with tempfile.TemporaryDirectory() as folder:
            log = RunLog(folder)
            self.assertEqual(B.record_signals(log, "r-1", "Hello there."), [])
            self.assertEqual(log.signals_by_rule(), {})

    def test_logging_never_raises(self):
        class Broken:
            def add_signal(self, *a, **k):
                raise OSError("disk full")
        self.assertEqual(B.record_signals(Broken(), "r-1", "**x**"), [])
        self.assertEqual(B.record_signals(None, "r-1", "**x**"), [])


class LibraryRules(unittest.TestCase):
    def setUp(self):
        self.library = Library(os.path.join(REPO, "library"))

    def test_rule_nodes_exist_and_validate(self):
        ids = sorted(e["id"] for e in self.library.rules())
        self.assertEqual(ids, sorted("rule." + n for n in B.RULES))

    def test_nodes_agree_with_the_code(self):
        by_name = {e["id"]: e for e in self.library.rules()}
        for rule in B.describe():
            node = by_name.get("rule." + rule["name"])
            self.assertIsNotNone(node, rule["name"])
            self.assertEqual(node["rule"]["severity"], rule["severity"], rule["name"])
            self.assertEqual(node["rule"]["bad"], rule["bad"], rule["name"])
            self.assertEqual(node["rule"]["good"], rule["good"], rule["name"])

    def test_examples_of_the_rules_behave(self):
        for rule in B.RULES.values():
            for bad in rule.bad:
                self.assertIn(rule.name, rules_of(bad), bad)
            for good in rule.good:
                self.assertNotIn(rule.name, rules_of(good), good)

    def test_rule_block_is_checked(self):
        node = {"id": "rule.x", "version": 1, "kind": "code", "tags": ["rule"], "function": "apply_rules", "rule": {"severity": "loud", "wanted": "x", "bad": [], "good": []}}
        self.assertTrue(any("severity" in p for p in validate_node(node)))
        node["rule"]["severity"] = "warn"
        node["tags"] = []
        self.assertTrue(any("tag" in p for p in validate_node(node)))

    def test_the_pipeline_runs_without_a_model(self):
        with tempfile.TemporaryDirectory() as folder:
            core = Core(os.path.join(REPO, "skills"), self.library, folder, model=None)
            result = core.run("check_speech", {"text": "**Hi** 2*3"})
            self.assertEqual(result.status, "done", result.error)
            self.assertIn("Hi 2 times 3", json.dumps(result.answer))


class HarnessTarget(unittest.TestCase):
    def test_suite_is_a_regression(self):
        cases = H.load_suite(os.path.join(REPO, "eval", "suites", "behaviour")).cases
        self.assertGreaterEqual(len(cases), 60)
        wrong = []
        for case in cases:
            text, gold = case["input"]["text"], case["gold"]
            if B.check_text(text)["rules"] != gold["rules"] or B.repair_text(text)["remaining"] != gold["remaining"]:
                wrong.append(case["id"])
            if "repaired" in gold and B.repair_text(text)["text"] != gold["repaired"]:
                wrong.append(case["id"])
        self.assertEqual(wrong, [])

    def test_rule_metrics(self):
        records = [{"score": {"expected": ["speech.no_bold"], "found": ["speech.no_bold"], "ok": True, "remaining_ok": True, "repair_ok": True, "idempotent": True, "matches_ok": True, "repaired": True}},
                   {"score": {"expected": [], "found": ["speech.no_bold"], "ok": False, "remaining_ok": True, "repair_ok": True, "idempotent": True, "matches_ok": True, "repaired": True}}]
        table = M.rule_metrics(records)
        self.assertIsInstance(table, dict)


if __name__ == "__main__":
    unittest.main()
