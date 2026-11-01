"""
TC-EVL-003 (N-4.1 T-03): the verdicts of a model used as judge count only after a calibration against the users' ratings (Cohen's kappa 0.6 or more, OPEN-7).
Protected since A-63 (D-164). Run: python tests/acceptance/test_judge_calibration.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

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
        """TC-EVL-003: a judge without a calibration record does not count; records without a judge are untouched.

        Example: 4 records of judge-light and 2 without a judge, no calibration -> counted False for the 4, the 2 unmarked.
        """
        marked = H.mark_judge_verdicts(records(), {})
        self.assertEqual([r.get("counted") for r in marked if "judge" in r], [False] * 4)
        self.assertTrue(all(r.get("counted", True) for r in marked if "judge" not in r))      # what no judge said is untouched

    @mark.req("REQ-EVL-003")
    def test_kappa_07_counts_and_kappa_04_does_not(self):
        """TC-EVL-003: a judge counts only with a calibration of Cohen's kappa 0.6 or more (OPEN-7).

        Example: kappa 0.7 -> counted; 0.4 -> not; the limit 0.6 counts, 0.59 does not; a record without kappa is no calibration.
        """
        # Given / When: the records marked with a calibration of 0.7, then of 0.4
        counted = H.mark_judge_verdicts(records(), {"judge-light": {"kappa": 0.7, "n": 60}})
        self.assertEqual([r["counted"] for r in counted if "judge" in r], [True] * 4)
        not_counted = H.mark_judge_verdicts(records(), {"judge-light": {"kappa": 0.4, "n": 60}})
        self.assertEqual([r["counted"] for r in not_counted if "judge" in r], [False] * 4)
        # Then: the limit itself
        self.assertTrue(H.judge_counts({"kappa": 0.6}))                                       # the limit itself is enough
        self.assertFalse(H.judge_counts({"kappa": 0.59}))
        self.assertFalse(H.judge_counts({"n": 60}))                                            # a record without a kappa is no calibration

    @mark.req("REQ-EVL-003")
    def test_a_not_counted_verdict_is_left_out_of_the_numbers(self):
        """TC-EVL-003: the match numbers leave a not counted verdict out.

        Example: 4 not counted judged records and 2 plain ones, all expecting pass -> match n 2.
        """
        marked = H.mark_judge_verdicts(records(), {})
        self.assertEqual(M.match_metrics([dict(r, expect="pass") for r in marked])["match"]["n"], 2)

    @mark.req("REQ-EVL-003")
    def test_a_run_of_the_harness_marks_the_judged_records(self):
        """TC-EVL-003 (regression, Verify F6, mutant of Harness.run): Harness.run marks every record that names a judge with the calibrations of the harness.

        Example: a judged record and judge-light calibrated at kappa 0.4 -> counted False; at 0.7 -> counted True.
        """
        # Given: a harness whose records name a judge (no target sets `judge` yet, so the test adds it to each record)
        class Judged(H.Harness):
            def _run_case(self, *args):
                return dict(super()._run_case(*args), judge="judge-light")
        suite = H.Suite("judged", "", {"kind": "fake"}, [{"id": "c0", "expect": "pass"}])
        harness = Judged(targets={"fake": lambda case, variant, s: ("pass", {})})
        for kappa, counted in ((0.4, False), (0.7, True)):
            harness.calibrations = {"judge-light": {"kappa": kappa, "n": 60}}
            # When: the harness runs
            run = harness.run(suite)
            # Then: the record is marked by the calibration
            self.assertEqual(run.records[0]["counted"], counted, kappa)

    @mark.req("REQ-EVL-003")
    def test_a_not_counted_verdict_is_left_out_of_the_verification_numbers(self):
        """TC-EVL-003 (regression, Verify F6, mutant of metrics.verification_metrics): a judge's verdict that is not counted is not in n, coverage or accuracy.

        Example: 4 judged true claims (not counted, all wrongly failed) and 2 plain passes -> n 2, accuracy 2 of 2.
        """
        # Given: four not counted verdicts that would all be wrong, and two plain right ones
        marked = H.mark_judge_verdicts([dict(r, status="fail") if "judge" in r else r for r in records()], {})
        # When: the verification numbers are computed
        numbers = M.verification_metrics(marked)
        # Then: only the two plain records count
        self.assertEqual(numbers["n"], 2)
        self.assertEqual((numbers["accuracy_overall"]["k"], numbers["accuracy_overall"]["n"]), (2, 2))

    @mark.req("REQ-EVL-003")
    def test_is_right_has_no_answer_for_a_not_counted_verdict(self):
        """TC-EVL-003 (regression, Verify F6, mutant of metrics.is_right): a not counted verdict is neither right nor wrong.

        Example: status pass, expect pass, counted False -> None (counted True -> True).
        """
        record = {"case": "c", "status": "pass", "expect": "pass", "judge": "judge-light"}
        self.assertIsNone(M.is_right(dict(record, counted=False)))
        self.assertTrue(M.is_right(dict(record, counted=True)))

    @mark.req("REQ-EVL-003")
    def test_the_calibration_record_is_written_and_read(self):
        """TC-EVL-003: tools/label_agreement.py writes the calibration record that the harness reads; no folder means no calibration.

        Example: judge-light, kappa 0.71, n 60 -> {"judge-light": {..., "against": "users' ratings"}}; a missing folder -> {}.
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "judge-light.json")
            LA.write_calibration(path, judge="judge-light", kappa=0.71, n=60)
            self.assertEqual(H.load_calibrations(tmp), {"judge-light": {"judge": "judge-light", "kappa": 0.71, "n": 60, "against": "users' ratings"}})
            self.assertEqual(H.load_calibrations(os.path.join(tmp, "nothing")), {})            # no folder, no calibration


if __name__ == "__main__":
    unittest.main()
