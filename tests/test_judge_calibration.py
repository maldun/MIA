"""
TC-EVL-003 (N-4.1 T-03): the verdicts of a model used as judge count only after a calibration against the users' ratings (Cohen's kappa 0.6 or more, OPEN-7).
Run: python tests/test_judge_calibration.py
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

import harness as H                                   # noqa: E402
import label_agreement as LA                          # noqa: E402
import metrics as M                                   # noqa: E402
from markers import mark                              # noqa: E402


def records():
    judged = [{"case": "j%d" % i, "status": "pass", "truth": True, "judge": "judge-light"} for i in range(4)]
    plain = [{"case": "p%d" % i, "status": "pass", "truth": True} for i in range(2)]
    return judged + plain


class JudgeCalibration(unittest.TestCase):
    @mark.req("REQ-EVL-003")
    def test_without_a_record_the_verdicts_are_not_counted(self):
        marked = H.mark_judge_verdicts(records(), {})
        self.assertEqual([r.get("counted") for r in marked if "judge" in r], [False] * 4)
        self.assertTrue(all(r.get("counted", True) for r in marked if "judge" not in r))      # what no judge said is untouched

    @mark.req("REQ-EVL-003")
    def test_kappa_07_counts_and_kappa_04_does_not(self):
        counted = H.mark_judge_verdicts(records(), {"judge-light": {"kappa": 0.7, "n": 60}})
        self.assertEqual([r["counted"] for r in counted if "judge" in r], [True] * 4)
        not_counted = H.mark_judge_verdicts(records(), {"judge-light": {"kappa": 0.4, "n": 60}})
        self.assertEqual([r["counted"] for r in not_counted if "judge" in r], [False] * 4)
        self.assertTrue(H.judge_counts({"kappa": 0.6}))                                       # the limit itself is enough
        self.assertFalse(H.judge_counts({"kappa": 0.59}))
        self.assertFalse(H.judge_counts({"n": 60}))                                            # a record without a kappa is no calibration

    @mark.req("REQ-EVL-003")
    def test_a_not_counted_verdict_is_left_out_of_the_numbers(self):
        marked = H.mark_judge_verdicts(records(), {})
        self.assertEqual(M.match_metrics([dict(r, expect="pass") for r in marked])["match"]["n"], 2)

    def test_the_calibration_record_is_written_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "judge-light.json")
            LA.write_calibration(path, judge="judge-light", kappa=0.71, n=60)
            self.assertEqual(H.load_calibrations(tmp), {"judge-light": {"judge": "judge-light", "kappa": 0.71, "n": 60, "against": "users' ratings"}})
            self.assertEqual(H.load_calibrations(os.path.join(tmp, "nothing")), {})            # no folder, no calibration


if __name__ == "__main__":
    unittest.main()
