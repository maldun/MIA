"""The five seed entries pass the graph rules (N-3.2 T-03): TC-GTB-005. Run with: python tests/test_seed_workflows.py

The entries are written in the example-workflow task of the root plan (T-10), not here. Until the folder exists the test is skipped with that reason;
it is not weakened. Provisional format (to be confirmed by T-10): library/workflows/<id>.json with the keys
  "workflow" (the graph: nodes and edges), "specification", "context_graph" (a graph too), "benchmark" (a reference to the suite), "enabled" (bool, default true).
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from graph_tables import validate  # noqa: E402
from markers import mark           # noqa: E402

SEEDS = ("lookup", "verify", "review", "search", "method_transfer")
FOLDER = os.path.join(ROOT, "library", "workflows")


@unittest.skipUnless(os.path.isdir(FOLDER), "the seed entries are written in root task T-10 (library/workflows does not exist yet)")
class SeedWorkflows(unittest.TestCase):
    def entry(self, name):
        with open(os.path.join(FOLDER, name + ".json"), encoding="utf-8") as handle:
            return json.load(handle)

    @mark.req("REQ-GTB-004")
    def test_all_five_entries_exist_and_pass_the_graph_rules(self):
        """TC-GTB-005: lookup, verify, review, search and method_transfer are valid workflows."""
        for name in SEEDS:
            with self.subTest(name=name):
                self.assertIsNone(validate("workflows", self.entry(name)["workflow"]))

    @mark.req("REQ-GTB-004")
    def test_each_entry_names_a_specification_a_context_graph_and_a_benchmark(self):
        """TC-GTB-005: the three parts are there; the context graph passes the rules too."""
        for name in SEEDS:
            with self.subTest(name=name):
                entry = self.entry(name)
                self.assertTrue(entry.get("specification"))
                self.assertTrue(entry.get("benchmark"))
                self.assertIsNone(validate("context_graphs", entry["context_graph"]))

    @mark.req("REQ-GTB-004")
    def test_method_transfer_is_off_by_default(self):
        """TC-GTB-005: only method_transfer is switched off."""
        self.assertIs(self.entry("method_transfer").get("enabled"), False)
        for name in SEEDS[:-1]:
            self.assertIsNot(self.entry(name).get("enabled", True), False, name)


if __name__ == "__main__":
    unittest.main()
