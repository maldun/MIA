"""
TC-WFM-038 (REQ-WFM-038): the LaTeX file of a review report is made by code from the report record: English headings, every work with its decision, special characters escaped.
Run: python tests/test_report_tex.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from report_tex import report_tex, tex_escape  # noqa: E402

REPORT = {
    "ended_by": "complete",
    "flow": {"found": 6, "duplicates": 1, "dropped": 1, "screened": 4, "excluded_abstract": 1, "excluded_full": 0, "included": 2, "maybe": 1, "undecided": 0},
    "keywords": [{"keyword": "graph colouring", "query": "q", "origin": "question", "hits": 3}, {"keyword": "R&D_x", "query": "q", "origin": "extension", "hits": 1}],
    "gaps": ["R&D_x"],
    "works": [
        {"doi": "10.1/a", "title": "Costs of 100% & more_", "keywords": ["graph colouring"], "decision": "include", "grade": 3, "reason": "", "abstract_only": False, "notes": ["on topic [quote a]"], "verified": True},
        {"doi": None, "title": "Maybe a paper", "keywords": [], "decision": "maybe", "grade": 1, "reason": "", "abstract_only": True, "notes": [], "verified": True},
        {"doi": "10.1/c", "title": "Off topic work", "keywords": [], "decision": "exclude", "grade": 0, "reason": "off_topic", "abstract_only": True, "notes": [], "verified": True},
    ],
    "dropped": [{"work": {"title": "Gone work", "doi": "10.1/d"}, "reason": "retracted"}],
}


class ReportTex(unittest.TestCase):
    def test_special_characters_are_escaped(self):
        self.assertEqual(tex_escape("a\\b{c}~^#$%&_"), r"a\textbackslash{}b\{c\}\textasciitilde{}\textasciicircum{}\#\$\%\&\_")

    def test_the_document_has_english_headings_and_the_question(self):
        text = report_tex(REPORT, "Do canary releases help?", "2026-10-29")
        self.assertTrue(text.startswith("\\documentclass{article}"))
        self.assertIn("\\begin{document}", text)
        self.assertTrue(text.rstrip().endswith("\\end{document}"))
        for heading in ("Literature review", "How the works were selected", "Included", "Maybe", "Excluded", "Dropped before screening"):
            self.assertIn("\\section*{%s}" % heading, text)
        self.assertIn("Do canary releases help?", text)
        self.assertIn("2026-10-29", text)

    def test_every_work_is_there_with_its_decision_and_the_text_is_escaped(self):
        text = report_tex(REPORT, "Do canary releases help?", "2026-10-29")
        self.assertIn(r"Costs of 100\% \& more\_", text)
        self.assertNotIn("100% &", text)
        for title in ("Maybe a paper", "Off topic work", "Gone work"):
            self.assertIn(title, text)
        self.assertIn(r"off\_topic", text)
        self.assertIn("relevance 3", text)
        self.assertIn("abstract only", text)
        self.assertIn(r"R\&D\_x", text)

    def test_the_summary_is_included_when_the_report_has_one(self):
        summary = {"figures": {"level": "thin"}, "coverage": "Only one work.", "found": [{"point": "colouring works", "works": ["10.1/a"]}], "gaps": [{"gap": "no field study", "works": []}], "dropped_points": 0}
        text = report_tex(dict(REPORT, summary=summary), "Do canary releases help?", "2026-10-29")
        self.assertIn("colouring works", text)
        self.assertIn("no field study", text)
        self.assertIn("thin", text)
        self.assertNotIn("Summary", report_tex(REPORT, "Do canary releases help?", "2026-10-29"))


if __name__ == "__main__":
    unittest.main()
