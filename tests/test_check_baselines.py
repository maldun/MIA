"""
TC-EVL-005 (N-4.1 T-04): every library workflow with status tested or trusted has a baseline file eval/baselines/<suite>__<variant>__baseline.jsonl;
the link from a workflow to its suite and variant is library/baselines.json. The check names the ones that lack it.
Run: python tests/test_check_baselines.py
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

import check_baselines as C                           # noqa: E402
from markers import mark                              # noqa: E402

LIBRARY = os.path.join(REPO, "library")


class Baselines(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.baselines = os.path.join(self.tmp.name, "baselines")
        os.makedirs(self.baselines)
        self.registry = os.path.join(self.tmp.name, "baselines.json")

    def missing(self):
        return {m["workflow"]: m["reason"] for m in C.missing_baselines(LIBRARY, self.baselines, self.registry)}

    @mark.req("REQ-EVL-005")
    def test_only_tested_and_trusted_workflows_are_checked_and_all_lack_a_baseline_at_first(self):
        missing = self.missing()
        self.assertEqual(sorted(missing), ["behaviour.speech", "chat", "extract.rules", "summarize", "verify.computable"])     # no draft, no retired
        self.assertTrue(all("baselines.json" in reason for reason in missing.values()))                                       # no registry yet

    @mark.req("REQ-EVL-005")
    def test_a_registered_workflow_needs_its_file_and_is_fine_with_it(self):
        with open(self.registry, "w") as fp:
            json.dump({"summarize": {"suite": "review", "variant": "single"}}, fp)
        self.assertIn("review__single__baseline.jsonl", self.missing()["summarize"])                  # registered, file missing: the file is named
        open(os.path.join(self.baselines, "review__single__baseline.jsonl"), "w").close()
        self.assertNotIn("summarize", self.missing())
        self.assertIn("chat", self.missing())                                                         # the others are still named

    def test_a_workflow_that_has_no_suite_says_so_and_still_counts_as_missing(self):
        with open(self.registry, "w") as fp:
            json.dump({"chat": None}, fp)
        self.assertIn("no suite", self.missing()["chat"])


if __name__ == "__main__":
    unittest.main()
