"""tools/stability_report.py on a saved run with repeats (REQ-STAB-002). Run with: python tests/test_stability_report.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))

import stability_report as S                                             # noqa: E402


def write_run(folder, statuses):
    path = os.path.join(folder, "suite__variant__stamp.jsonl")
    rows = [{"kind": "header", "suite": "suite", "variant": {"name": "variant"}, "repeats": 3}]
    for case, repeats in statuses.items():
        rows += [{"case": case, "repeat": i, "status": status} for i, status in enumerate(repeats)]
    with open(path, "w", encoding="utf-8") as fp:
        fp.write("".join(json.dumps(row) + "\n" for row in rows))
    return path


class StabilityReportTool(unittest.TestCase):
    def test_the_report_names_the_unstable_cases(self):
        with tempfile.TemporaryDirectory() as folder:
            path = write_run(folder, {"a": ["pass"] * 3, "b": ["pass", "pass", "fail"], "c": ["fail"] * 3, "d": ["pass", "inconclusive", "inconclusive"]})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                result = S.report(path)
        self.assertEqual((result["n"], result["unstable"]), (4, ["b", "d"]))
        self.assertIn("unstable: b", out.getvalue())
        self.assertIn("stable  50.0 %", out.getvalue())

    def test_latest_picks_the_newest_run_of_each_suite_for_a_variant(self):
        with tempfile.TemporaryDirectory() as folder:
            write_run(folder, {"a": ["pass"] * 3})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = S.main(["--latest", "variant", "--results", folder])
        self.assertEqual(code, 0)
        self.assertIn("suite / variant", out.getvalue())


if __name__ == "__main__":
    unittest.main()
