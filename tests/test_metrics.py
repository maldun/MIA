"""
Tests for the evaluation numbers: Wilson intervals, the exact sign test, the verification metrics (with hand-counted examples), exact-behaviour matches, breakdown by tag, stability and the
paired comparison. Run with the MIA virtualenv: python tests/test_metrics.py
"""
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import metrics as M                                   # noqa: E402


def rec(case, status, truth=None, expect=None, tags=None, repeat=0, **kw):
    return dict({"case": case, "status": status, "truth": truth, "expect": expect, "tags": tags or [], "repeat": repeat}, **kw)


class IntervalTests(unittest.TestCase):
    def test_wilson_known_values(self):
        low, high = M.wilson(8, 10)                      # textbook: 0.4902 to 0.9433
        self.assertAlmostEqual(low, 0.490, places=2)
        self.assertAlmostEqual(high, 0.943, places=2)
        low, high = M.wilson(0, 10)
        self.assertEqual(low, 0.0)
        self.assertAlmostEqual(high, 0.278, places=2)
        low, high = M.wilson(10, 10)
        self.assertAlmostEqual(low, 0.722, places=2)
        self.assertEqual(high, 1.0)
        self.assertEqual(M.wilson(0, 0), (0.0, 1.0))
        low, high = M.wilson(15, 30)
        self.assertLess(low, 0.5)                         # n = 30: still a wide interval
        self.assertGreater(high, 0.5)
        self.assertGreater(high - low, 0.3)

    def test_intervals_shrink_with_more_cases(self):
        small = M.wilson(8, 10)
        large = M.wilson(800, 1000)
        self.assertLess(large[1] - large[0], (small[1] - small[0]) / 4)

    def test_rate(self):
        r = M.rate(3, 4)
        self.assertEqual((r["k"], r["n"], r["rate"]), (3, 4, 0.75))
        self.assertLess(r["low"], 0.75)
        self.assertGreater(r["high"], 0.75)
        empty = M.rate(0, 0)
        self.assertIsNone(empty["rate"])
        self.assertIsNone(empty["low"])


class SignTestTests(unittest.TestCase):
    def test_exact_values(self):
        self.assertEqual(M.sign_test(0, 0), 1.0)
        self.assertEqual(M.sign_test(5, 5), 1.0)
        self.assertAlmostEqual(M.sign_test(0, 5), 2 / 32)                         # 0.0625
        self.assertAlmostEqual(M.sign_test(5, 0), 2 / 32)
        self.assertAlmostEqual(M.sign_test(1, 9), 2 * (1 + 10) / 1024)           # 0.0215
        self.assertAlmostEqual(M.sign_test(2, 8), 2 * (1 + 10 + 45) / 1024)
        self.assertLessEqual(M.sign_test(0, 20), 1e-5)
        self.assertEqual(M.sign_test(3, 4), M.sign_test(4, 3))

    def test_never_above_one(self):
        for a in range(8):
            for b in range(8):
                self.assertLessEqual(M.sign_test(a, b), 1.0)


class DecisionTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual([M.decision(s) for s in ("pass", "fail", "open", "inconclusive", "none", "not_applicable", "error:budget")], ["pass", "fail"] + ["abstain"] * 5)
        self.assertEqual(M.normalize_status("inconclusive"), "open")
        self.assertEqual(M.normalize_status("none"), "open")
        self.assertEqual(M.normalize_status("pass"), "pass")


class VerificationTests(unittest.TestCase):
    def setUp(self):
        # 10 claims: 6 true, 4 false. true: 4 passed, 1 refuted (false fail), 1 open. false: 2 refuted, 1 passed (false pass), 1 inconclusive.
        self.records = ([rec("t%d" % i, "pass", True) for i in range(4)] + [rec("t4", "fail", True), rec("t5", "open", True)]
                        + [rec("f0", "fail", False), rec("f1", "fail", False), rec("f2", "pass", False), rec("f3", "inconclusive", False)])
        self.m = M.verification_metrics(self.records)

    def test_counts_and_rates(self):
        self.assertEqual(self.m["counts"], {"tp": 4, "fp": 1, "tn": 2, "fn": 1, "abstain_true": 1, "abstain_false": 1})
        self.assertEqual((self.m["n"], self.m["true_claims"], self.m["false_claims"]), (10, 6, 4))
        self.assertEqual((self.m["coverage"]["k"], self.m["coverage"]["rate"]), (8, 0.8))
        self.assertEqual((self.m["accuracy_decided"]["k"], self.m["accuracy_decided"]["n"]), (6, 8))
        self.assertEqual((self.m["accuracy_overall"]["k"], self.m["accuracy_overall"]["n"]), (6, 10))
        self.assertEqual((self.m["false_pass"]["k"], self.m["false_pass"]["n"]), (1, 4))                       # one of the four wrong claims passed
        self.assertEqual((self.m["false_fail"]["k"], self.m["false_fail"]["n"]), (1, 6))
        self.assertEqual((self.m["precision_pass"]["k"], self.m["precision_pass"]["n"]), (4, 5))
        self.assertEqual((self.m["precision_fail"]["k"], self.m["precision_fail"]["n"]), (2, 3))
        self.assertEqual((self.m["abstain_rate"]["k"], self.m["abstain_rate"]["n"]), (2, 10))

    def test_unlabelled_records_do_not_count(self):
        m = M.verification_metrics(self.records + [rec("x", "pass", None), rec("y", "fail", None, expect="fail")])
        self.assertEqual(m["n"], 10)

    def test_errors_are_abstentions_and_counted(self):
        m = M.verification_metrics([rec("a", "error:budget", True), rec("b", "pass", True)])
        self.assertEqual((m["errors"]["k"], m["counts"]["abstain_true"], m["counts"]["tp"]), (1, 1, 1))

    def test_nothing_to_judge(self):
        m = M.verification_metrics([])
        self.assertEqual(m["n"], 0)
        self.assertIsNone(m["coverage"]["rate"])
        self.assertIsNone(m["false_pass"]["rate"])


class MatchTests(unittest.TestCase):
    def test_exact_behaviour(self):
        records = [rec("a", "pass", expect="pass"), rec("b", "inconclusive", expect="open"), rec("c", "open", expect="inconclusive"), rec("d", "fail", expect="pass"), rec("e", "pass")]
        m = M.match_metrics(records)
        self.assertEqual((m["n"], m["match"]["k"]), (4, 3))                       # open and inconclusive are the same status
        self.assertEqual([r["case"] for r in m["mismatches"]], ["d"])

    def test_is_right(self):
        self.assertTrue(M.is_right(rec("a", "pass", expect="pass")))
        self.assertFalse(M.is_right(rec("a", "pass", truth=False)))
        self.assertTrue(M.is_right(rec("a", "fail", truth=False)))
        self.assertFalse(M.is_right(rec("a", "open", truth=True)))                # abstaining is not right
        self.assertTrue(M.is_right(rec("a", "open", truth=False, expect="open")))  # unless the case asks for exactly that
        self.assertIsNone(M.is_right(rec("a", "pass")))


class BreakdownTests(unittest.TestCase):
    def test_by_tag(self):
        records = [rec("a", "pass", True, tags=["numeric", "trap"]), rec("b", "fail", True, tags=["numeric"]), rec("c", "pass", True, tags=["date"]), rec("d", "pass", expect="pass")]
        table = M.breakdown(records)
        self.assertEqual((table["numeric"]["k"], table["numeric"]["n"]), (1, 2))
        self.assertEqual((table["trap"]["k"], table["trap"]["n"]), (1, 1))
        self.assertEqual((table["date"]["k"], table["(none)"]["k"]), (1, 1))
        self.assertEqual(list(table), sorted(table))


class CostAndStabilityTests(unittest.TestCase):
    def test_cost(self):
        c = M.cost([rec("a", "pass", seconds=2.0, calls=2, chars_in=100, chars_out=40), rec("b", "pass", seconds=4.0, calls=1, chars_in=50, chars_out=10)])
        self.assertEqual((c["runs"], c["seconds"], c["seconds_per_run"], c["calls"], c["chars_in"], c["chars_out"]), (2, 6.0, 3.0, 3, 150, 50))
        self.assertEqual(M.cost([])["seconds_per_run"], 0.0)

    def test_stability_over_repeats(self):
        records = [rec("a", "pass", repeat=0), rec("a", "pass", repeat=1), rec("b", "pass", repeat=0), rec("b", "fail", repeat=1), rec("c", "open", repeat=0), rec("c", "inconclusive", repeat=1),
                   rec("single", "pass", repeat=0)]
        s = M.stability(records)
        self.assertEqual((s["k"], s["n"]), (2, 3))                               # a and c (open = inconclusive) are stable, b is not; a case run once says nothing
        self.assertIsNone(M.stability([rec("a", "pass")])["rate"])


class CompareTests(unittest.TestCase):
    def test_paired(self):
        a = [rec("c%d" % i, "pass", True) for i in range(10)]                                          # a: all 10 right
        b = [rec("c%d" % i, "pass" if i < 6 else "fail", True) for i in range(10)] + [rec("extra", "pass", True)]       # b: right on 6
        c = M.compare(a, b)
        self.assertEqual((c["cases"], c["a_right"], c["b_right"]), (10, 10, 6))
        self.assertEqual((len(c["only_a"]), len(c["only_b"])), (4, 0))
        self.assertAlmostEqual(c["p_value"], 2 / 16)
        self.assertEqual((c["missing_in_a"], c["missing_in_b"]), (["extra"], []))

    def test_repeats_count_as_shares(self):
        a = [rec("x", "pass", True, repeat=0), rec("x", "pass", True, repeat=1)]
        b = [rec("x", "pass", True, repeat=0), rec("x", "fail", True, repeat=1)]
        c = M.compare(a, b)
        self.assertEqual((c["a_right"], c["b_right"], c["only_a"]), (1, 0.5, ["x"]))

    def test_identical_runs(self):
        a = [rec("c%d" % i, "pass", True) for i in range(5)]
        c = M.compare(a, list(a))
        self.assertEqual((c["only_a"], c["only_b"], c["p_value"]), ([], [], 1.0))


if __name__ == "__main__":
    unittest.main()
