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

from extensions.review import review_case as RC                                     # noqa: E402
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


GOMES = """ACM Computing Surveys, Vol. 51, No. 3, Article 49. Publication date: May 2018.
[13] Andrés A. Alvarez Cabrera, Krijn Woestenenk, and Tetsuo Tomiyama. 2011. An architecture model to support
cooperative design for mechatronic products: A control design case. Mechatronics 21, 3 (Apr. 2011), 534–547.
DOI:http://dx.doi.org/10.1016/j.mechatronics.2011.01.009
49:27
[17] Fernando J. Barros. 1997. Modeling formalisms for dynamic structure systems. ACM Transactions on Modeling and
Computer Simulation 7, 4 (Oct. 1997), 501–515. DOI:http://dx.doi.org/10.1145/268403.268423
"""
NAYAK = """[1] S. Lu and S. V. Pereverzev, “Numerical differentiation from a viewpoint of regularization theory,” Math. Comp., vol. 75, no. 256, pp. 1853–1870, 2006.
[7] H. W. Engl, M. Hanke, and A. Neubauer, Regularization of inverse problems, vol. 375 of Mathematics and its Applications. Kluwer Academic Publishers Group, Dordrecht, 1996.
"""
ARGOUL = """[AE05]

P. Argoul and S. Erlicher. Mechanical modelling and computational
issues in civil engineering, volume 23 of Lecture Notes. Springer,
2005.
10
[Arg90]

P. Argoul. Identification des structures vibrantes. Thèse de doctorat, Ecole Nationale des Ponts et Chaussées, 1990. 283 pages.
"""


class References(unittest.TestCase):
    def test_name_year_style_with_a_doi_in_the_entry(self):
        refs = RC.parse_references(GOMES)
        self.assertEqual([r["key"] for r in refs], ["13", "17"])
        self.assertEqual(refs[0]["title"], "An architecture model to support cooperative design for mechatronic products: A control design case")
        self.assertEqual((refs[0]["year"], refs[0]["doi"]), (2011, "10.1016/j.mechatronics.2011.01.009"))
        self.assertEqual(refs[1]["authors"], "Fernando J. Barros")
        self.assertEqual(refs[1]["doi"], "10.1145/268403.268423")

    def test_initials_first_style_quoted_title_and_book(self):
        refs = RC.parse_references(NAYAK)
        self.assertEqual(refs[0]["authors"], "S. Lu and S. V. Pereverzev")
        self.assertEqual(refs[0]["title"], "Numerical differentiation from a viewpoint of regularization theory")
        self.assertEqual(refs[0]["year"], 2006)                                                      # not the page number 1853
        self.assertEqual((refs[1]["title"], refs[1]["year"]), ("Regularization of inverse problems", 1996))

    def test_keys_on_their_own_line_and_page_noise(self):
        refs = RC.parse_references(ARGOUL)
        self.assertEqual([r["key"] for r in refs], ["AE05", "Arg90"])
        self.assertEqual(refs[0]["authors"], "P. Argoul and S. Erlicher")
        self.assertEqual(refs[0]["title"], "Mechanical modelling and computational issues in civil engineering")
        self.assertEqual(refs[1]["year"], 1990)

    def test_citations_in_the_text(self):
        known = {"1", "5", "6", "7", "AE05", "TA77", "LA04"}
        text = "monographs such as [5], [6]; see [7] or [9]; on [0, 1] nothing; ([LA04, AE05] and [TA77][BG67])"
        self.assertEqual(RC.cited_keys(text, known), {"5", "6", "7", "LA04", "AE05", "TA77"})

    def test_a_work_must_be_published_within_the_time_of_the_review(self):
        self.assertTrue(RC.published_by({"year": 2017}, "2018-05-31"))
        self.assertFalse(RC.published_by({"year": 2018}, "2018-05-31"))                              # a bare year counts to its last day
        self.assertFalse(RC.published_by({"year": 2019}, "2018-05-31"))
        self.assertFalse(RC.published_by({"date": "2018-06-02", "year": 2018}, "2018-05-31"))
        self.assertFalse(RC.published_by({}, "2018-05-31"))                                          # undated is not within
        self.assertTrue(RC.published_by({}, None))


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
