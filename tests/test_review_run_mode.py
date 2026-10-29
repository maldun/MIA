"""TC-WFM-034 (REQ-WFM-034) and TC-WFM-032 (REQ-WFM-032): the mode run asks no question at a used-up limit and ends at a hard cap (the limit times a factor, default 10) with the cap named; the mode slice
is the old behaviour; the review reports the sources on the list, processed, still to process, included, maybe, excluded and dropped, and the limits with what is used, to its monitor.
Run with: python tests/test_review_run_mode.py"""
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extensions.review import review_stages as rs
from extensions.review.review_request import Budget, ReviewRequest
from test_review_stages import CRITERIA, TODAY, Clock, judge, work


class Monitor:
    def __init__(self):
        self.phase, self.budget, self.counts, self.updates = None, {}, {}, []

    def update(self, phase=None, budget=None, counts=None):
        self.phase = phase or self.phase
        for name, figures in (budget or {}).items():
            self.budget.setdefault(name, {}).update(figures)
        self.counts.update(counts or {})
        self.updates.append((dict(self.counts), {k: dict(v) for k, v in self.budget.items()}))


def run_with(works, abstract=None, limits=None, mode="run", cap_factor=10, clock=None, monitor=None, agree=None):
    clock = clock or Clock()
    request = ReviewRequest("how to schedule with graphs", until=TODAY, today=TODAY, budget=limits, clock=clock, mode=mode, cap_factor=cap_factor)
    asked = []

    def recording_agree(report):
        asked.append(report["asking"])
        return True if agree is None else agree(report)
    run = rs.ReviewRun(request, ["graph"], CRITERIA, search=lambda keyword, query: [dict(w) for w in works], screen_abstract=abstract or (lambda w: judge(w)),
                       screen_full=lambda w, t: None, full_text=lambda w: None, agree=recording_agree, approve_terms=lambda proposals: [], monitor=monitor)
    return run.run(), asked


class BudgetModes(unittest.TestCase):
    def test_the_mode_run_has_hard_caps_of_the_limits_times_the_factor(self):          # TC-WFM-034
        clock = Clock()
        budget = Budget({"screen": 2, "seconds": 60}, clock=clock, mode="run", cap_factor=10)
        budget.start()
        self.assertTrue(all(budget.spend("screen") for _ in range(20)))
        self.assertFalse(budget.spend("screen"))
        self.assertEqual((budget.hit, budget.state()["limits"]["screen"]), ("screen", 20))
        budget = Budget({"seconds": 60}, clock=clock, mode="run", cap_factor=10)
        budget.start()
        clock.now = 599
        self.assertIsNone(budget.exhausted())
        clock.now = 600
        self.assertEqual(budget.exhausted(), "seconds")

    def test_the_mode_slice_keeps_the_limits_as_they_are(self):                        # TC-WFM-034
        budget = Budget({"screen": 2}, clock=Clock())
        budget.start()
        self.assertEqual([budget.spend("screen") for _ in range(3)], [True, True, False])


class RunMode(unittest.TestCase):
    WORKS = [work("10.1/%d" % i, "T%d" % i) for i in range(4)]

    def slow(self, clock):
        def screen(w):
            clock.now += 40
            return judge(w)
        return screen

    def test_no_question_at_a_used_up_limit_in_the_mode_run(self):                     # TC-WFM-034
        clock = Clock()
        report, asked = run_with(self.WORKS, abstract=self.slow(clock), clock=clock, mode="run")
        self.assertEqual(report["flow"]["screened"], 4)
        self.assertEqual(asked, ["checkpoint"])             # 160 s are over the slice of 60 s, and nothing was asked about it

    def test_the_slice_mode_still_asks_at_the_limit(self):                             # TC-WFM-019
        clock = Clock()
        report, asked = run_with(self.WORKS, abstract=self.slow(clock), clock=clock, mode="slice")
        self.assertTrue(any(a.startswith("limit:") for a in asked))

    def test_the_run_ends_at_the_hard_cap_with_the_cap_named_and_asks_nothing(self):   # TC-WFM-034
        clock = Clock()
        report, asked = run_with(self.WORKS, abstract=self.slow(clock), clock=clock, mode="run", cap_factor=1)
        self.assertEqual((report["ended_by"], report["flow"]["screened"]), ("budget:seconds", 2))
        self.assertEqual(asked, [])


class Figures(unittest.TestCase):
    def test_the_figures_add_up_after_every_step_and_the_limits_show_what_is_used(self):      # TC-WFM-032
        works = [work("10.1/%d" % i, "T%d" % i) for i in range(5)] + [work("10.1/x", "Gone", retracted=True)]
        decisions = {"10.1/0": (3, "include", ""), "10.1/1": (2, "include", ""), "10.1/2": (1, "maybe", ""), "10.1/3": (0, "exclude", "off_topic"), "10.1/4": (2, "include", "")}
        monitor = Monitor()
        report, _ = run_with(works, abstract=lambda w: judge(w, *decisions[w["doi"]]), monitor=monitor)
        for counts, _budget in monitor.updates:
            if "on_list" in counts and "included" in counts:
                self.assertEqual(counts["on_list"], counts["processed"] + counts["to_process"])
                self.assertEqual(counts["included"] + counts["maybe"] + counts["excluded"], counts["processed"])
        self.assertEqual(monitor.counts, {"on_list": 5, "processed": 5, "to_process": 0, "included": 3, "maybe": 1, "excluded": 1, "dropped": 1})
        self.assertEqual(monitor.budget["screen"], {"used": 5, "limit": 400})
        self.assertEqual(monitor.budget["api_requests"]["used"], 1)
        self.assertEqual(monitor.budget["seconds"], {"limit": 600})
        for name in ("read", "calls", "tokens"):
            self.assertIn("limit", monitor.budget[name])
        self.assertIn("to_process", [c for c, _ in monitor.updates if c.get("processed") == 2][0])


if __name__ == "__main__":
    unittest.main()
