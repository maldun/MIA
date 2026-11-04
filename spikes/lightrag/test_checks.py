"""Tests of checks.py. Run: python3 -I test_checks.py"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import entity_in_source, relation_in_source

TEXT = "The PRIMSA flow diagram details the flow. Boolean operators help. A number of databases exist (e.g., PubMed, Embase)."


class Checks(unittest.TestCase):
    def test_case_and_hyphen(self):
        self.assertTrue(entity_in_source("Boolean Operators", [TEXT]))
        self.assertTrue(entity_in_source("pre-training", ["Pre training of the retriever"]))

    def test_name_inside_a_longer_word_does_not_count(self):  # the "SA Flow Diagram" case
        self.assertFalse(entity_in_source("SA Flow Diagram", [TEXT]))

    def test_parenthetical_and_plural(self):
        self.assertTrue(entity_in_source("Large Language Models (LLMs)", ["large language model (LLM) systems"]))
        self.assertTrue(entity_in_source("Database", [TEXT]))

    def test_relation_window(self):
        self.assertTrue(relation_in_source("Boolean operators", "PubMed", [TEXT]))
        far = "Alpha. " + "x " * 400 + "Beta."
        self.assertTrue(relation_in_source("Alpha", "Beta", [far]))
        self.assertFalse(relation_in_source("Alpha", "Beta", [far], window=300))
        self.assertFalse(relation_in_source("Alpha", "Gamma", [far]))


if __name__ == "__main__":
    unittest.main(verbosity=0)
