"""
Acceptance tests of the number check (specs/number-gate/requirements.md: REQ-NUM-001 to REQ-NUM-006, IF-001), written before the code (Plan, step 4).
They call checks.number_check(claim, evidence) -> {"status": pass | fail | inconclusive | not_applicable, "check": "number_check", "detail": text, "evidence": [...]}.
Protected after the Plan gate: change only through an approved plan amendment. Run with: python tests/acceptance/test_number_check.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

import checks                                            # noqa: E402
from markers import mark                                 # noqa: E402

STATUSES = ("pass", "fail", "inconclusive", "not_applicable")


def status(claim, evidence):
    return checks.number_check(claim, evidence)["status"]


class NumberCheck(unittest.TestCase):
    @mark.req("REQ-NUM-001")
    def test_a_contradicting_number_fails_and_an_equal_one_passes(self):
        """TC-NUM-001: whole numbers must be equal; other values agree within 1 % or the rounding the claim shows (checked against checks._agrees on 2026-10-24)."""
        tower = "The tower is 1,200 m tall."
        self.assertEqual(status(tower, "The tower is 1,020 m tall."), "fail")
        self.assertEqual(status(tower, "The tower is 1,200 m tall."), "pass")
        self.assertEqual(status(tower, "The tower is 1,210 m tall."), "fail")                 # a whole number leaves nothing to round
        group = "The group sold 4.8 million records."
        self.assertEqual(status(group, "The group sold 4.83 million records."), "pass")
        self.assertEqual(status(group, "The group sold 4.9 million records."), "fail")

    @mark.req("REQ-NUM-002")
    def test_no_value_for_the_quantity_is_inconclusive(self):
        """TC-NUM-002: nothing found is never a fail."""
        hall = "The hall is 40 m long."
        self.assertEqual(status(hall, "The hall was built in 1901."), "inconclusive")
        self.assertEqual(status(hall, "The hall has 40 seats."), "inconclusive")

    @mark.req("REQ-NUM-003")
    def test_a_bound_is_compared_with_the_evidence_value(self):
        """TC-NUM-003: more than, at least, under; the bound itself counts for at least and not for more than."""
        views = "The video got more than 5 million views."
        self.assertEqual(status(views, "The video got 3.2 million views."), "fail")
        self.assertEqual(status(views, "The video got 7 million views."), "pass")
        self.assertEqual(status(views, "The video got 5 million views."), "fail")             # not strictly more
        self.assertEqual(status("The album has at least 3 tracks.", "The album has 3 tracks."), "pass")
        self.assertEqual(status("The group sold under 23.5 million records.", "The group sold more than 23 million records."), "inconclusive")

    @mark.req("REQ-NUM-004")
    def test_empty_evidence_is_not_applicable(self):
        """TC-NUM-004: the Wikidata claims carry no evidence."""
        for claim in ("The tower is 1,200 m tall.", "The river is 453 kilometres long.", "The bridge was built in 1937.",
                      "The group sold 4.8 million records.", "The village has no school."):
            self.assertEqual(status(claim, ""), "not_applicable", claim)

    @mark.req("REQ-NUM-005")
    def test_scale_words_and_units_are_converted(self):
        """TC-NUM-005"""
        self.assertEqual(status("The group sold 23.5 million records.", "The group sold 23,500,000 records."), "pass")
        self.assertEqual(status("The road is 5 km long.", "The road is 3.1 miles long."), "pass")
        self.assertEqual(status("The road is 5 km long.", "The road is 3.0 miles long."), "fail")
        self.assertEqual(status("The road is 1.2 km long.", "The road is 1,210 m long."), "pass")

    @mark.req("REQ-NUM-006")
    def test_only_a_number_of_the_same_quantity_decides(self):
        """TC-NUM-006: same unit dimension or the same noun in the three words after the number."""
        self.assertEqual(status("The hall is 40 m long.", "The hall has 40 seats."), "inconclusive")
        self.assertEqual(status("Westlife sold under 23.5 million records.", "Westlife has been certified for 13 million albums and 9.8 million singles."), "inconclusive")
        self.assertEqual(status("The hall is 40 m long.", "The hall has a length of 41 m."), "fail")

    @mark.req("IF-001")
    def test_the_result_has_a_status_of_the_vocabulary_and_a_short_detail(self):
        """TC-IF-001: the four statuses in turn, detail of at most 200 characters."""
        seen = set()
        for claim, evidence in (("The tower is 1,200 m tall.", "The tower is 1,020 m tall."),
                                ("The tower is 1,200 m tall.", "The tower is 1,200 m tall."),
                                ("The hall is 40 m long.", "The hall has 40 seats."),
                                ("The tower is 1,200 m tall.", "")):
            outcome = checks.number_check(claim, evidence)
            self.assertIn(outcome.get("status"), STATUSES, outcome)
            self.assertIsInstance(outcome.get("detail"), str)
            self.assertLessEqual(len(outcome["detail"]), 200)
            seen.add(outcome["status"])
        self.assertEqual(seen, {"fail", "pass", "inconclusive", "not_applicable"})


if __name__ == "__main__":
    unittest.main()
