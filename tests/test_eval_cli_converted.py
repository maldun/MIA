"""
`tools/eval.py run ... --converted` gives the harness the variant flag `converted` (T-CV-09 part, D-255).
Run: python tests/test_eval_cli_converted.py
"""
import json
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import test_eval_cli as T                             # noqa: E402


class Stop(Exception):
    pass


class ConvertedFlag(T.CommandLine):
    def run_variant(self, *extra):
        folder = os.path.join(T.EVAL_CLI.SUITES, "toy")
        os.makedirs(folder)
        with open(os.path.join(folder, "suite.json"), "w") as fp:
            json.dump({"name": "toy", "target": {"kind": "fake"}}, fp)
        with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
            fp.write(json.dumps({"id": "a", "input": {}, "expect": "pass"}) + "\n")
        seen = []

        class Harness:
            def run(self, suite, variant, *args, **kwargs):
                seen.append(variant)
                raise Stop()
        with mock.patch.object(T.EVAL_CLI, "build_core", lambda *a, **k: None), mock.patch.object(T.EVAL_CLI, "make_harness", lambda *a, **k: Harness()):
            try:
                message = self.main("run", "toy", "--pin", "MP-light", *extra)
            except Stop:
                message = None
        self.assertTrue(seen, "the run never reached the harness: %s" % (message,))
        return seen[0]

    def test_the_flag_sets_the_variant_key(self):
        """Example: run toy --pin MP-light --converted -> variant {"name": "default", "converted": True}."""
        # Given a suite and the flag
        # When the run starts
        variant = self.run_variant("--converted")
        # Then the harness gets the key
        self.assertTrue(variant.get("converted"))

    def test_without_the_flag_there_is_no_key(self):
        """Example: run toy --pin MP-light -> variant {"name": "default"}."""
        # Given a suite and no flag
        # When the run starts
        variant = self.run_variant()
        # Then the variant is as before
        self.assertEqual(variant, {"name": "default"})


if __name__ == "__main__":
    unittest.main()
