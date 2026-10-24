"""
Acceptance tests of the interfaces (specs/number-gate/requirements.md: REQ-ARG-001, IF-002, IF-004, IF-005, IF-006), written before the code (Plan, step 4).
The schemas of view.argue@1, view.judge@1 and view.verdict@1 exist in the library; these tests pin what they must accept and reject. The harness interfaces are
metrics.repeat_lists(records) (IF-004) and harness.case_input(case, pin) (IF-005).
Protected after the Plan gate. Run with: python tests/acceptance/test_contracts.py
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

import checks                                            # noqa: E402
import harness                                           # noqa: E402
import metrics                                           # noqa: E402
from markers import mark                                 # noqa: E402


def schema_of(node):
    entry = json.load(open(os.path.join(REPO, "library", "nodes", node, "1.json"), encoding="utf-8"))
    return entry["body"]["schema"]


def accepts(schema, value):
    return checks.schema_valid(value, schema)["status"] == "pass"


class Schemas(unittest.TestCase):
    @mark.req("REQ-ARG-001")
    def test_argue_points(self):
        """TC-ARG-001: 1 to 4 points of 3 to 400 characters."""
        schema = schema_of("view.argue")
        point = lambda n: "x" * n
        for ok in ({"points": [point(3)]}, {"points": [point(400), point(3)]}, {"points": [point(5)] * 4}):
            self.assertTrue(accepts(schema, ok), ok)
        for bad in ({"points": []}, {"points": [point(5)] * 5}, {"points": [point(2)]}, {"points": [point(401)]}, {}):
            self.assertFalse(accepts(schema, bad), bad)

    def judge_examples(self):
        ok = [{"verdict": v, "reason": "x" * n} for v in ("supported", "refuted", "unclear") for n in (3, 600)]
        ok += [{"verdict": "supported", "reason": "abc", "confidence": c} for c in (0, 1, 0.5)]
        bad = [{"verdict": "maybe", "reason": "abc"}, {"verdict": "supported", "reason": "ab"}, {"verdict": "supported", "reason": "x" * 601},
               {"verdict": "supported", "reason": "abc", "confidence": 1.1}, {"verdict": "supported"}]
        return ok, bad

    @mark.req("IF-002")
    def test_the_ruling_of_the_judge(self):
        """TC-IF-002: verdict supported, refuted or unclear; reason of 3 to 600 characters; confidence 0 to 1."""
        ok, bad = self.judge_examples()
        schema = schema_of("view.judge")
        for value in ok:
            self.assertTrue(accepts(schema, value), value)
        for value in bad:
            self.assertFalse(accepts(schema, value), value)

    @mark.req("IF-006")
    def test_the_single_voice_ruling_has_the_same_format(self):
        """TC-IF-006: view.verdict@1 accepts and rejects the same examples as the judge."""
        ok, bad = self.judge_examples()
        schema = schema_of("view.verdict")
        for value in ok:
            self.assertTrue(accepts(schema, value), value)
        for value in bad:
            self.assertFalse(accepts(schema, value), value)


class HarnessInterfaces(unittest.TestCase):
    @mark.req("IF-004")
    def test_the_stability_metric_gets_the_repeats_of_each_case(self):
        """TC-IF-004: 4 cases with 3 repeats and 1 case with 1 repeat: 4 lists of 3 entries with status and facts."""
        records = []
        for case in ("a", "b", "c", "d"):
            for repeat in range(3):
                records.append({"case": case, "repeat": repeat, "status": "pass", "facts": [{"entity": "e", "number": 1.0, "unit": "m", "quote": "q"}]})
        records.append({"case": "single", "repeat": 0, "status": "pass", "facts": []})
        lists = metrics.repeat_lists(records)
        self.assertEqual(sorted(lists), ["a", "b", "c", "d"])
        for case, repeats in lists.items():
            self.assertEqual(len(repeats), 3)
            for entry in repeats:
                self.assertEqual(set(entry), {"status", "facts"})

    @mark.req("IF-005")
    def test_the_gate_gets_claim_evidence_seed_and_temperature(self):
        """TC-IF-005: 4 fields per case, with the seed 7 and the temperature 0 of the pin."""
        pin = {"name": "gemma4:12b-it-qat", "digest": "sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3", "seed": 7, "temperature": 0}
        for n in range(3):
            case = {"id": "c%d" % n, "input": {"claim": "The tower is %d m tall." % (100 + n), "evidence": "e%d" % n, "rounds": 3, "experts": []}}
            handed = harness.case_input(case, pin)
            self.assertEqual(set(handed) & {"claim", "evidence", "seed", "temperature"}, {"claim", "evidence", "seed", "temperature"})
            self.assertEqual((handed["claim"], handed["evidence"], handed["seed"], handed["temperature"]), (case["input"]["claim"], "e%d" % n, 7, 0))


if __name__ == "__main__":
    unittest.main()
