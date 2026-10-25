"""IF-405 scholarly sources (external; owned by the Tools and sandbox): the contract suite runs against the mock (stage 1) and the real APIs
(stage 2, skipped until the stage-2 run supplies recorded answers). Protected after the Plan gate.
Run with: python tests/acceptance/contract/test_if_405_scholarly_sources.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider, subject_for  # noqa: E402
from markers import mark                                    # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from if_405_scholarly_sources import ScholarMock            # noqa: E402

IF = "IF-405"


def make(**options):
    return lambda kind: ScholarMock(**options) if kind == "mock" else subject_for(IF, kind)


@contract
class ScholarContract(unittest.TestCase):
    @mark.req("IF-405", "REQ-BE-056")
    @each_provider(IF)
    def test_works_are_deduplicated_and_keep_all_sources(self, scholar):
        """TC-IF-405-01 golden 1: the same DOI from two sources appears once with both sources listed."""
        result = scholar.search("towers")
        dois = [w["doi"] for w in result["works"]]
        self.assertEqual(len(dois), len(set(dois)))
        exact = [w for w in result["works"] if w["doi"] == "10.1/a"][0]
        self.assertEqual(exact["sources"], ["crossref", "openalex"])
        self.assertEqual((result["errors"], result["dropped"]), ([], []))

    @mark.req("IF-405", "REQ-BE-056", "REQ-BE-055")
    @each_provider(IF)
    def test_the_cutoff_is_strict(self, scholar):
        """TC-IF-405-02 golden 3: until 2001-11-22 keeps the exact day, drops 'month only' and 'year only' (their last day is later) and the work without a date."""
        result = scholar.search("towers", until="2001-11-22")
        self.assertEqual([w["doi"] for w in result["works"]], ["10.1/a"])
        reasons = {d["ref"]: d["reason"] for d in result["dropped"]}
        self.assertEqual(reasons, {"10.1/b": "after_cutoff", "10.1/c": "after_cutoff", "10.1/d": "no_date"})

    @mark.req("IF-405")
    @each_provider(IF, make(failing=("openalex",)))
    def test_one_failing_source_does_not_stop_the_others(self, scholar):
        """TC-IF-405-03 golden 2: openalex fails: its error is listed, the works of the other sources are returned."""
        result = scholar.search("towers")
        self.assertEqual([e["source"] for e in result["errors"]], ["openalex"])
        self.assertTrue(result["works"])
        self.assertTrue(all("openalex" not in w["sources"] for w in result["works"]))

    @mark.req("IF-405")
    @each_provider(IF, make(failing=("openalex", "crossref", "pubmed")))
    def test_all_sources_failing_is_an_answer_not_an_exception(self, scholar):
        """TC-IF-405-04: if every source fails, works is empty and every failure is listed; nothing is raised."""
        result = scholar.search("towers")
        self.assertEqual(result["works"], [])
        self.assertEqual(sorted(e["source"] for e in result["errors"]), ["crossref", "openalex", "pubmed"])


if __name__ == "__main__":
    unittest.main()
