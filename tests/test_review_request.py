"""TC-WFM-019 (REQ-WFM-019): the review works in time slices; the first slice is 60 s; the run goes on only when the user agrees, and then every used-up limit grows by its first size.
Run with: python tests/test_review_request.py"""
import datetime
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extensions.review.review_request import MAX_DOMAIN_EXPERTS, Budget, RequestError, ReviewRequest, recommend
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))
from markers import mark                                  # noqa: E402


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def started(limits=None):
    clock = Clock()
    budget = Budget(limits, clock=clock)
    budget.start()
    return budget, clock


class TestSlices(unittest.TestCase):
    def test_the_first_slice_is_sixty_seconds(self):
        budget, clock = started()
        clock.now = 59
        self.assertIsNone(budget.exhausted())
        clock.now = 60
        self.assertEqual(budget.exhausted(), "seconds")

    def test_a_continue_adds_one_more_slice(self):
        budget, clock = started()
        clock.now = 61
        self.assertEqual(budget.exhausted(), "seconds")
        grown = budget.continue_run()
        self.assertEqual(grown["seconds"], 120)
        self.assertIsNone(budget.exhausted())
        self.assertEqual(budget.slices(), 2)
        self.assertIsNone(budget.hit)

    def test_a_refused_spend_is_remembered_and_counts_nothing(self):
        budget, clock = started({"screen": 2})
        self.assertTrue(budget.spend("screen"))
        self.assertTrue(budget.spend("screen"))
        self.assertFalse(budget.spend("screen"))
        self.assertEqual(budget.hit, "screen")
        self.assertEqual(budget.used["screen"], 2)

    def test_a_continue_renews_the_limit_that_was_used_up(self):
        budget, clock = started({"screen": 1})
        budget.spend("screen")
        self.assertEqual(budget.exhausted(), "screen")
        budget.continue_run()
        self.assertEqual(budget.limits["screen"], 2)
        self.assertTrue(budget.spend("screen"))

    def test_unknown_and_too_small_limits_are_refused(self):
        with self.assertRaises(RequestError):
            Budget({"nonsense": 5})
        with self.assertRaises(RequestError):
            Budget({"seconds": 0})

    @mark.req("REQ-WFM-019")
    def test_the_number_of_domain_experts_is_bounded(self):          # TC-WFM-019 (N5, first Verify of N-2.3)
        """A review asks for at most 10 domain experts; 10 is accepted, 11 is refused, and so is a boolean.

        Example: domain_experts=10 -> accepted; 11 -> RequestError; True -> RequestError.
        """
        # Given: a day for the request
        day = datetime.date(2026, 1, 1)
        # When / Then: the bound holds on both sides
        self.assertEqual(ReviewRequest("how to schedule with graphs", until=day, today=day, domain_experts=MAX_DOMAIN_EXPERTS).domain_experts, 10)
        for wrong in (MAX_DOMAIN_EXPERTS + 1, True):
            with self.assertRaises(RequestError):
                ReviewRequest("how to schedule with graphs", until=day, today=day, domain_experts=wrong)

    def test_the_recommendation_follows_the_progress(self):
        self.assertEqual(recommend({"new_sources": 3}, open_items=2)["action"], "continue")
        self.assertEqual(recommend({}, open_items=2)["action"], "stop")
        self.assertEqual(recommend({"new_sources": 3}, open_items=0)["action"], "stop")
        self.assertEqual(recommend({}, sufficient=True)["action"], "stop")


if __name__ == '__main__':
    unittest.main()
