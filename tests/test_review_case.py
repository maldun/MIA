"""
Tests for building a reference case from a published review (review_case.py): the rows of a literature matrix, the matching of a title and authors (R1), what stays unresolved (R2), the
report and the case file. No network: the scholarly clients are replaced by small fakes.
Run with the MIA virtualenv: python tests/test_review_case.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import review_case as RC                                     # noqa: E402
from web_tools import WebError                               # noqa: E402

MATRIX = """Table 2: Literature matrix
001._DevOps_a_definition    Banica, Logica  Journal  2017  x
002._What_is_DevOps    Georges Bou Ghantous;Asif Gill   y
not a row at all
003._The Path to DevOps  Smith  z
"""


class Client:
    def __init__(self, name, works=None, fail=False):
        self.name, self.works, self.fail, self.queries = name, works or [], fail, []

    def search(self, query, limit=5, until=None):
        self.queries.append(query)
        if self.fail:
            raise WebError("down")
        return self.works


def work(title, authors, doi="10.1/x", year=2017, date="2017-05-01"):
    return {"title": title, "authors": authors, "doi": doi, "year": year, "date": date, "work_type": "article", "oa_url": None}


class Parsing(unittest.TestCase):
    def test_rows_of_a_matrix(self):
        rows = RC.parse_matrix(MATRIX)
        self.assertEqual([r["id"] for r in rows], ["001", "002", "003"])
        self.assertEqual(rows[0]["title"], "DevOps a definition")
        self.assertEqual(rows[0]["authors"], "Banica, Logica")
        self.assertEqual(rows[1]["authors"], "Georges Bou Ghantous;Asif Gill")

    def test_no_rows_in_plain_text(self):
        self.assertEqual(RC.parse_matrix("just text\nmore text"), [])


class Matching(unittest.TestCase):
    def test_similarity(self):
        self.assertEqual(RC.title_similarity("The Path to DevOps", "Path to devops"), 1.0)
        self.assertLess(RC.title_similarity("DevOps", "Quantum gravity"), 0.1)
        self.assertEqual(RC.title_similarity("", "x"), 0.0)

    def test_authors(self):
        self.assertTrue(RC.authors_match("Banica, Logica", ["Logica Banica", "D. Radulescu"]))
        self.assertFalse(RC.authors_match("Banica", ["Smith"]))
        self.assertFalse(RC.authors_match(None, ["Smith"]))

    def test_r1_a_generic_title_needs_a_matching_author(self):
        entry = {"title": "DevOps", "authors": "Banica"}
        self.assertEqual(RC.accept(entry, work("DevOps", ["Someone Else"])), None)
        self.assertEqual(RC.accept(entry, work("DevOps", ["Logica Banica"])), 1.0)

    def test_r1_a_long_title_is_enough(self):
        entry = {"title": "Software security in DevOps synthesizing practitioners perceptions", "authors": "Rahman"}
        self.assertEqual(RC.accept(entry, work("Software security in DevOps: synthesizing practitioners' perceptions", ["Other Person"])), 1.0)

    def test_a_similar_but_other_title_is_refused(self):
        entry = {"title": "What is DevOps a systematic mapping study", "authors": "Jabbari"}
        self.assertIsNone(RC.accept(entry, work("What is machine learning a survey", ["Jabbari"])))


class Resolving(unittest.TestCase):
    def test_resolved_by_the_first_client_that_knows_it(self):
        entry = {"id": "001", "title": "DevOps a definition", "authors": "Banica"}
        first, second = Client("openalex"), Client("crossref", [work("DevOps: a definition", ["Logica Banica"], doi="10.1/d")])
        out = RC.resolve(entry, [first, second])
        self.assertTrue(out["resolved"])
        self.assertEqual((out["doi"], out["matched_by"]), ("10.1/d", "crossref"))
        self.assertEqual(len(first.queries), 1)

    def test_r2_unresolved_stays_as_it_is(self):
        entry = {"id": "003", "title": "The Path to DevOps", "authors": "Smith"}
        out = RC.resolve(entry, [Client("openalex"), Client("crossref", fail=True)])
        self.assertFalse(out["resolved"])
        self.assertNotIn("doi", out)
        self.assertEqual(out["title"], "The Path to DevOps")

    def test_the_best_candidate_wins(self):
        entry = {"id": "1", "title": "Continuous delivery pipelines in practice", "authors": "Lee"}
        out = RC.resolve(entry, [Client("openalex", [work("Continuous delivery pipelines", ["A Lee"], doi="10.1/weak"),
                                                       work("Continuous delivery pipelines in practice", ["A Lee"], doi="10.1/best")])])
        self.assertEqual(out["doi"], "10.1/best")


class Building(unittest.TestCase):
    def test_report(self):
        entries = RC.parse_matrix(MATRIX)
        client = Client("openalex", [work("DevOps: a definition", ["Logica Banica"], doi="10.1/d", date="2017-05-01"),
                                     work("What is DevOps", ["Asif Gill"], doi="10.1/d", year=2020, date="2020-01-01")])
        seen = []
        included, report = RC.build_included(entries, [client], until="2019-04-30", progress=lambda n, total, item: seen.append((n, total)))
        self.assertEqual(seen, [(1, 3), (2, 3), (3, 3)])
        self.assertEqual(report["entries"], 3)
        self.assertEqual(report["resolved"], 2)
        self.assertEqual(report["unresolved"], ["The Path to DevOps"])
        self.assertEqual(report["duplicates"], ["10.1/d"])
        self.assertEqual([x["title"] for x in report["after_cutoff"]], ["What is DevOps"])
        self.assertEqual(len(included), 3)


class CaseFile(unittest.TestCase):
    def test_gold_entry_and_case(self):
        resolved = {"title": "DevOps a definition", "matched_title": "DevOps: a definition", "authors": "Banica", "resolved": True, "doi": "10.1/d", "year": 2017, "date": "2017-05-01"}
        lost = {"title": "The Path to DevOps", "authors": "Smith", "resolved": False}
        self.assertEqual(RC.gold_entry(resolved), {"title": "DevOps: a definition", "authors": "Banica", "doi": "10.1/d", "year": 2017, "date": "2017-05-01"})
        self.assertEqual(RC.gold_entry(lost), {"title": "The Path to DevOps", "authors": "Smith", "unresolved": True})
        q = [{"id": "q1", "question": "Is there a standard?", "answer": "does_not_support", "evidence": [], "confirmed": False}]
        case = RC.draft_case("c1", ["devops"], "What is known about DevOps?", "2019-04-30", ["DevOps"], [resolved, lost], q, "the review", notes="draft")
        self.assertEqual(case["input"], {"question": "What is known about DevOps?", "until": "2019-04-30", "key_terms": ["DevOps"]})
        self.assertEqual(len(case["gold"]["included"]), 2)
        self.assertFalse(case["gold"]["questions"][0]["confirmed"])
        self.assertEqual((case["expect"], case["note"]), ("pass", "draft"))


if __name__ == "__main__":
    unittest.main()
