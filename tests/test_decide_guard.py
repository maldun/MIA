"""
TC-EVL-002 (N-4.1 T-02): a verdict is decided only on held-out cases. The guard refuses a dev-split run, decides a holdout run with eval_decide.py of the agent-app skill,
and the harness leaves cases tagged split:holdout out of a dev run.
Run: python tests/test_decide_guard.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(HERE, "helpers"))

import decide_guard as G                              # noqa: E402
import harness as H                                   # noqa: E402
from markers import mark                              # noqa: E402

DECIDE = os.path.expanduser("~/.claude/skills/agent-app/scripts/eval_decide.py")


def write_run(folder, name, suite, rights, tag=None):
    """a run file: a header and one record per case; rights = list of True (status pass, truth true) or False (status fail, truth true)"""
    path = os.path.join(folder, name)
    with open(path, "w") as fp:
        fp.write(json.dumps({"kind": "header", "suite": suite, "variant": {"name": "v"}, "repeats": 1}) + "\n")
        for i, right in enumerate(rights):
            record = {"kind": "record", "case": "c%d" % i, "repeat": 0, "status": "pass" if right else "fail", "truth": True, "tags": [tag] if tag else []}
            fp.write(json.dumps(record) + "\n")
    return path


class Guard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    @mark.req("REQ-EVL-002")
    def test_a_dev_split_run_is_refused(self):
        run = write_run(self.tmp.name, "dev.jsonl", "verdicts", [True] * 20)
        verdict = G.check_runs([run])
        self.assertFalse(verdict["ok"])
        self.assertIn("dev split", verdict["reason"])

    @mark.req("REQ-EVL-002")
    def test_a_mixed_or_unlabelled_run_is_refused_too(self):
        dev = write_run(self.tmp.name, "dev.jsonl", "verdicts", [True] * 5)
        hold = write_run(self.tmp.name, "hold.jsonl", "verdicts.holdout", [True] * 5)
        self.assertFalse(G.check_runs([hold, dev])["ok"])           # one dev run among the holdout runs spoils the decision
        self.assertFalse(G.check_runs([])["ok"])

    @mark.req("REQ-EVL-002")
    def test_holdout_runs_are_accepted_by_the_suite_name_or_the_tag(self):
        by_name = write_run(self.tmp.name, "a.jsonl", "verdicts.holdout", [True] * 5)
        by_tag = write_run(self.tmp.name, "b.jsonl", "verdicts", [True] * 5, tag="split:holdout")
        self.assertTrue(G.check_runs([by_name, by_tag])["ok"])

    @unittest.skipUnless(os.path.exists(DECIDE), "eval_decide.py of the agent-app skill is not installed")
    @mark.req("REQ-EVL-002")
    def test_a_holdout_run_is_decided_by_the_rule_and_a_dev_run_is_not_decided(self):
        good = write_run(self.tmp.name, "good.jsonl", "verdicts.holdout", [True] * 40)
        bad = write_run(self.tmp.name, "bad.jsonl", "verdicts.holdout", [False] * 40)
        dev = write_run(self.tmp.name, "dev.jsonl", "verdicts", [True] * 40)
        self.assertEqual(G.decide([good], ["--metric", "right", "--min", "0.9", "--low", "0.8", "--fold", "majority"])["decision"], "PASS")
        self.assertEqual(G.decide([bad], ["--metric", "right", "--min", "0.9", "--low", "0.8"])["decision"], "FAIL")
        refused = G.decide([dev], ["--metric", "right", "--min", "0.9"])
        self.assertEqual(refused["decision"], "NOT DECIDED")
        self.assertIn("dev split", refused["reason"])


class HarnessKeepsHoldoutOut(unittest.TestCase):
    def test_a_dev_run_never_selects_a_case_tagged_split_holdout(self):
        cases = [{"id": "a", "tags": []}, {"id": "b", "tags": ["split:holdout"]}, {"id": "c", "tags": ["split:dev"]}]
        dev = H.Suite("verdicts", "", {"kind": "fake"}, cases)
        self.assertEqual([c["id"] for c in dev.select()], ["a", "c"])
        self.assertEqual([c["id"] for c in dev.select(only=["b"])], [])        # not even by name
        holdout = H.Suite("verdicts.holdout", "", {"kind": "fake"}, cases)
        self.assertEqual([c["id"] for c in holdout.select()], ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
