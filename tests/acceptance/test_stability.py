"""
Acceptance tests of the stability metric and of the stored sources (specs/number-gate/requirements.md: REQ-STAB-001 to REQ-STAB-003), written before the code (Plan, step 4).
A fact is a dict {"entity", "number", "unit", "quote"}; two facts are the same when the normalised entity, the number with its unit and the hash of the normalised quote agree.
A repeat is {"status": ..., "facts": [...], "text": ...}; the text is the wording of the answer and never counts. API: metrics.same_facts(a, b),
metrics.case_is_stable(repeats), metrics.stability_report(records) -> {"n", "share", "low", "high", "unstable": [case ids]}.
Protected after the Plan gate. Run with: python tests/acceptance/test_stability.py
"""
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.dirname(HERE)
REPO = os.path.dirname(TESTS)
sys.path.insert(0, REPO)
sys.path.insert(0, TESTS)
sys.path.insert(0, os.path.join(TESTS, "helpers"))

import metrics                                           # noqa: E402
import reproduce as RP                                   # noqa: E402
from markers import mark                                 # noqa: E402


def fact(entity, number, unit="m", quote="the source says so"):
    return {"entity": entity, "number": number, "unit": unit, "quote": quote}


def repeat(facts, text="an answer", status="pass"):
    return {"status": status, "facts": list(facts), "text": text}


class SameFacts(unittest.TestCase):
    @mark.req("REQ-STAB-001")
    def test_order_and_wording_do_not_matter_numbers_and_counts_do(self):
        """TC-STAB-001: another order and other wording, stable; 3 facts against 4, not; one number different, not; the word approximately added, stable."""
        f1, f2, f3, f4 = fact("Rivertown Bridge", 412), fact("Rivertown Bridge", 38, "million euros", "cost 38 million"), fact("Tarn Museum", 1950, "", "founded 1950"), fact("Tarn Museum", 12400, "works")
        a = [repeat([f1, f2, f3], "The bridge is 412 m long and cost 38 million euros; the museum was founded in 1950."),
             repeat([f3, f1, f2], "Founded in 1950 is the museum. The bridge: 412 m, 38 million euros.")]
        self.assertTrue(metrics.case_is_stable(a))
        self.assertFalse(metrics.case_is_stable([repeat([f1, f2, f3]), repeat([f1, f2, f3, f4])]))
        changed = fact("Rivertown Bridge", 1020)
        self.assertFalse(metrics.case_is_stable([repeat([fact("Rivertown Bridge", 1200)]), repeat([changed])]))
        self.assertTrue(metrics.case_is_stable([repeat([f1], "The bridge is 412 m long."), repeat([f1], "The bridge is approximately 412 m long.")]))
        self.assertFalse(metrics.case_is_stable([repeat([f1], status="pass"), repeat([f1], status="fail")]), "a different verdict is never stable")

    @mark.req("REQ-STAB-001")
    def test_the_same_fact_is_decided_by_normalised_parts(self):
        """TC-STAB-001 (parts): case and diacritics of the entity, thousands marks of the number, spaces of the quote are normalised."""
        self.assertTrue(metrics.same_facts([fact("Gröbner Basis", 1200, "m", "A  quote")], [fact("grobner basis", "1,200", "m", "a quote")]))
        self.assertFalse(metrics.same_facts([fact("A", 1200)], [fact("B", 1200)]))
        self.assertFalse(metrics.same_facts([fact("A", 1200, "m")], [fact("A", 1200, "km")]))

    @mark.req("REQ-STAB-002")
    def test_the_report_has_the_share_the_interval_and_the_unstable_cases(self):
        """TC-STAB-002: 10 cases with 3 repeats, 2 of them unstable: share 0.8, Wilson interval 0.49 to 0.94 (by hand: centre 0.7167, half width 0.2266), the 2 identifiers."""
        records = []
        for i in range(10):
            for r in range(3):
                status = "fail" if i in (3, 7) and r == 2 else "pass"
                records.append({"case": "case-%d" % i, "repeat": r, "status": status, "facts": [fact("E", 1)]})
        report = metrics.stability_report(records)
        self.assertEqual(report["n"], 10)
        self.assertAlmostEqual(report["share"], 0.8, places=2)
        self.assertAlmostEqual(report["low"], 0.49, places=2)
        self.assertAlmostEqual(report["high"], 0.94, places=2)
        self.assertEqual(sorted(report["unstable"]), ["case-3", "case-7"])

    @mark.req("REQ-STAB-001")
    def test_property_permutations_and_rewordings_never_break_stability(self):
        """TC-STAB-004: 1000 generated fact sets, each in 3 random orders with 3 rewordings, seeds 1 to 1000: no pair is judged not stable."""
        entities = ["Rivertown Bridge", "Tarn Museum", "Harbour Tower", "Eiffel Tower", "Nile", "Mount Fitz Roy"]
        units = ["m", "km", "million euros", "", "works"]
        for seed in range(1, 1001):
            rng = random.Random(seed)
            facts = [fact(rng.choice(entities), rng.randint(1, 50000), rng.choice(units), "quote %d" % rng.randint(1, 99)) for _ in range(rng.randint(1, 6))]
            repeats = []
            for k in range(3):
                shuffled = list(facts)
                rng.shuffle(shuffled)
                repeats.append(repeat(shuffled, "wording %d %s" % (k, rng.random())))
            self.assertTrue(metrics.case_is_stable(repeats), seed)


class StoredSources(unittest.TestCase):
    @mark.req("REQ-STAB-003")
    def test_every_fetched_page_is_stored_by_its_hash_and_the_run_is_reproduced(self):
        """TC-STAB-003: a lookup on the recorded web; every page_fetched event names a hash that is in the content store; the offline reproduction has the same events. Existing behaviour, a regression test."""
        from test_run_explain import Lab                                      # the recorded web of the research suite
        lab = Lab()
        self.addCleanup(lab.close)
        record = lab.baseline("reader")
        pages = [e for e in record["events"] if e.get("kind") == "event" and e.get("type") == "page_fetched"]
        self.assertTrue(pages, "the run fetched no page")
        for event in pages:
            self.assertTrue(lab.store.get(event["payload"]["hash"]), event["payload"]["ref"])
        result = RP.reproduce(record, lab.store, lab.factory())
        self.assertTrue(result["reproduced"], result)
        self.assertEqual(result["divergences"], [])


if __name__ == "__main__":
    unittest.main()
