"""TC-WFM-028 (REQ-WFM-028): the full text of a work is cut by code into sections that fit a model, headings found by name.
Run with: python tests/test_fulltext_sections.py"""
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fulltext import cut_sections


class TestCutSections(unittest.TestCase):
    def test_headings_become_sections_and_references_are_dropped(self):
        text = "Title line\n\nAbstract\nWe study graphs.\n\n1. Introduction\nIntro words here.\n\n2 Methods\nWe colour graphs.\n\n3. Results\nColouring wins.\n\n4. Conclusions\nColouring is good.\n\nReferences\n[1] Someone."
        out = cut_sections(text)
        self.assertEqual([s["name"] for s in out["sections"]], ["Start", "Abstract", "Introduction", "Methods", "Results", "Conclusions"])
        self.assertEqual(out["sections"][3]["text"], "We colour graphs.")
        self.assertEqual(out["conclusion"], "Colouring is good.")
        self.assertNotIn("Someone", " ".join(s["text"] for s in out["sections"]))

    def test_without_headings_the_text_is_split_at_blank_lines(self):
        out = cut_sections("para one.\n\npara two.\n\npara three.", max_chars=12)
        self.assertEqual([s["name"] for s in out["sections"]], ["Part 1", "Part 2", "Part 3"])
        self.assertEqual(out["conclusion"], "para three.")

    def test_a_long_section_is_split_into_numbered_parts(self):
        out = cut_sections("Results\naaaa aaaa\n\nbbbb bbbb\n\ncccc cccc", max_chars=20)
        self.assertEqual([s["name"] for s in out["sections"]], ["Results (1)", "Results (2)"])
        self.assertEqual(out["sections"][0]["text"], "aaaa aaaa\n\nbbbb bbbb")
        self.assertEqual(out["sections"][1]["text"], "cccc cccc")

    def test_a_sentence_with_a_heading_word_is_not_a_heading(self):
        out = cut_sections("Abstract\nShort.\n\nThe results were good and we discuss them.\n\nConclusion\nDone here.")
        self.assertEqual([s["name"] for s in out["sections"]], ["Abstract", "Conclusion"])
        self.assertEqual(out["sections"][0]["text"], "Short.\n\nThe results were good and we discuss them.")

    def test_the_last_section_is_the_conclusion_when_none_is_named_and_empty_text_gives_nothing(self):
        out = cut_sections("Introduction\nIntro here.\n\nResults\nOnly results.")
        self.assertEqual(out["conclusion"], "Only results.")
        self.assertEqual(cut_sections(""), {"sections": [], "conclusion": ""})


if __name__ == '__main__':
    unittest.main()
