"""
Acceptance tests of the harness features that the baselines need (specs/number-gate/requirements.md: REQ-EVAL-001 to REQ-EVAL-004), written before the code (Plan, step 4).
API: Harness.run(suite, variant, repeats, ..., pin=None, include_retired=False); Suite.select(..., include_retired=False); harness.sample_cases(cases, n, seed);
the pin is {"name", "digest", "seed", "temperature"}. The saved run header gets "pin" (the four fields), "repeats", "pipeline", "skill_version" and "suite_sha1" {file name: SHA-1}.
Protected after the Plan gate. Run with: python tests/acceptance/test_harness_pin.py
"""
import hashlib
import json
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

import harness                                           # noqa: E402
from core import Core                                    # noqa: E402
from gate_lab import Scripted, vote                      # noqa: E402
from library import Library                              # noqa: E402
from markers import mark                                 # noqa: E402

PIN = {"name": "gemma4:12b-it-qat", "digest": "sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3", "seed": 7, "temperature": 0}


def write_suite(folder, cases, target=None):
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "suite.json"), "w", encoding="utf-8") as fp:
        json.dump({"name": os.path.basename(folder), "description": "test", "target": target or {"kind": "pipeline", "skill": "verify_claim"}}, fp)
    with open(os.path.join(folder, "cases.jsonl"), "w", encoding="utf-8") as fp:
        for case in cases:
            fp.write(json.dumps(case) + "\n")


def claim_case(n, tags=()):
    return {"id": "c%d" % n, "tags": list(tags), "input": {"claim": "The tower is %d m tall." % (100 + n), "evidence": "", "rounds": 3, "experts": []}, "truth": True}


class Pinned(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def harness_with(self, cases, **suite_kw):
        folder = os.path.join(self.tmp.name, "suite")
        write_suite(folder, cases, **suite_kw)
        model = Scripted(lambda p, n: vote("supported"))
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), os.path.join(self.tmp.name, "runs"), model=model)
        return harness.Harness(core), harness.load_suite(folder), model, folder

    @mark.req("REQ-EVAL-001")
    def test_the_run_header_names_what_ran(self):
        """TC-EVAL-001: the header has the pipeline, the skill version, the pin name, digest, seed and temperature, the repeats and the SHA-1 of each suite file."""
        runner, suite, model, folder = self.harness_with([claim_case(n) for n in range(3)])
        run = runner.run(suite, {"name": "single", "pipeline": "verify.single@1"}, repeats=3, pin=PIN)
        header = run.header
        self.assertEqual(header.get("pipeline"), "verify.single@1")
        self.assertIn("skill_version", header)
        self.assertEqual({k: header.get("pin", {}).get(k) for k in PIN}, PIN)
        self.assertEqual(header.get("repeats"), 3)
        expected = {name: hashlib.sha1(open(os.path.join(folder, name), "rb").read()).hexdigest() for name in ("suite.json", "cases.jsonl")}
        self.assertEqual(header.get("suite_sha1"), expected)

    @mark.req("REQ-EVAL-002")
    def test_retired_cases_are_not_run_and_not_counted(self):
        """TC-EVAL-002: a suite of 5 cases with 2 retired: 3 cases; with include_retired 5."""
        cases = [claim_case(0), claim_case(1, ["retired"]), claim_case(2), claim_case(3, ["ambiguous", "retired"]), claim_case(4)]
        runner, suite, model, folder = self.harness_with(cases)
        self.assertEqual(len(suite.select()), 3)
        self.assertEqual(len(suite.select(include_retired=True)), 5)
        run = runner.run(suite, {"name": "single", "pipeline": "verify.single@1"})
        self.assertEqual((run.header["cases"], len(run.records)), (3, 3))
        run = runner.run(suite, {"name": "single", "pipeline": "verify.single@1"}, include_retired=True)
        self.assertEqual((run.header["cases"], len(run.records)), (5, 5))

    @mark.req("REQ-EVAL-003")
    def test_seed_and_temperature_reach_every_model_call(self):
        """TC-EVAL-003: with the fake model that remembers its options, every call of a run has the seed and the temperature of the pin."""
        runner, suite, model, folder = self.harness_with([claim_case(n) for n in range(3)])
        runner.run(suite, {"name": "single", "pipeline": "verify.single@1"}, repeats=2, pin=PIN)
        self.assertGreaterEqual(len(model.options), 6)
        for options in model.options:
            self.assertIsInstance(options, dict)
            self.assertEqual((options.get("seed"), options.get("temperature")), (7, 0))


class Sample(unittest.TestCase):
    def pairs(self, n=30):
        cases = []
        for i in range(n):
            for half in ("true", "false"):
                cases.append({"id": "p%d-%s" % (i, half), "tags": ["number", "pair:p%d" % i], "truth": half == "true"})
        return cases

    def split_pairs(self, sample):
        halves = {}
        for case in sample:
            pair = next(t for t in case["tags"] if t.startswith("pair:"))
            halves[pair] = halves.get(pair, 0) + 1
        return [p for p, count in halves.items() if count != 2]

    @mark.req("REQ-EVAL-004")
    def test_the_same_seed_gives_the_same_sample_and_no_pair_is_split(self):
        """TC-EVAL-004: sample 20 with seed 7 on 30 pairs, twice."""
        cases = self.pairs()
        first = harness.sample_cases(cases, 20, 7)
        second = harness.sample_cases(cases, 20, 7)
        self.assertEqual(len(first), 20)
        self.assertEqual([c["id"] for c in first], [c["id"] for c in second])
        self.assertEqual(self.split_pairs(first), [])
        self.assertNotEqual([c["id"] for c in first], [c["id"] for c in harness.sample_cases(cases, 20, 8)])

    @mark.req("REQ-EVAL-004")
    @mark.statistical
    def test_property_no_pair_is_split_in_any_sample(self):
        """TC-EVAL-005: samples of 10 to 60 cases (even) with the seeds 1 to 200."""
        cases = self.pairs()
        for seed in range(1, 201):
            n = random.Random(seed).choice(range(10, 61, 2))
            sample = harness.sample_cases(cases, n, seed)
            self.assertEqual(len(sample), n, seed)
            self.assertEqual(self.split_pairs(sample), [], seed)


if __name__ == "__main__":
    unittest.main()
