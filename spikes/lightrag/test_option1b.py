"""Tests of option1b.py with a scripted model (no Ollama). Run: python3 -I test_option1b.py"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import option1b

DOC = ("PubMed is a free database of biomedical literature. Boolean operators help literature searches "
       "and PubMed supports them. The PRIMSA flow diagram shows the flow of studies.")


def ent(name, description, quote):
    return dict(name=name, description=description, quote=quote)


class EntityRules(unittest.TestCase):
    def test_a_description_that_restates_the_quote_is_accepted(self):
        p = ent("PubMed", "A free database of biomedical literature", "PubMed is a free database of biomedical literature.")
        self.assertIsNone(option1b.validate(p, DOC))

    def test_a_description_with_words_not_in_the_quote_is_refused(self):
        p = ent("PubMed", "A database run by the US National Library of Medicine", "PubMed is a free database of biomedical literature.")
        self.assertIn("not in the quote", option1b.validate(p, DOC))

    def test_the_allowance_for_ungrounded_words_is_a_parameter(self):
        p = ent("PubMed", "A free database of biomedical literature online", "PubMed is a free database of biomedical literature.")
        self.assertIsNotNone(option1b.validate(p, DOC))
        self.assertIsNone(option1b.validate(p, DOC, max_ungrounded=1))

    def test_a_quote_of_two_sentences_or_a_fragment_is_refused(self):
        two = "PubMed is a free database of biomedical literature. Boolean operators help literature searches"
        self.assertIsNotNone(option1b.validate(ent("PubMed", "database", two), DOC))
        self.assertEqual(option1b.validate(ent("PubMed", "free database", "PubMed is a free database"), DOC),
                         "quote is not one whole sentence of the document")

    def test_a_wiki_heading_or_a_list_line_before_the_sentence_does_not_make_it_a_fragment(self):
        doc = "== Concept ==\nA citation is a reference to a source.\nCitations help readers. Notes follow here."
        p = ent("citation", "a reference to a source", "A citation is a reference to a source.")
        self.assertIsNone(option1b.validate(p, doc))

    def test_a_quote_that_starts_in_the_middle_of_a_sentence_is_refused(self):
        p = ent("PubMed", "supports them", "and PubMed supports them.")
        self.assertEqual(option1b.validate(p, DOC), "quote is not one whole sentence of the document")

    def test_no_description_is_refused(self):
        p = ent("PubMed", "  ", "PubMed is a free database of biomedical literature.")
        self.assertEqual(option1b.validate(p, DOC), "entity has no description")

    def test_the_rules_of_option_1_still_hold(self):
        mangled = ent("SA Flow Diagram", "flow of studies", "The PRIMSA flow diagram shows the flow of studies.")
        self.assertIn("name not in the document", option1b.validate(mangled, DOC))

    def test_a_relation_is_checked_as_in_option_1(self):
        r = dict(source="Boolean operators", relation="help", target="literature searches",
                 quote="Boolean operators help literature searches and PubMed supports them.")
        self.assertIsNone(option1b.validate(r, DOC))


class Build(unittest.TestCase):
    def test_build_splits_accepted_and_refused_with_a_reason(self):
        good = ent("PubMed", "free database of biomedical literature", "PubMed is a free database of biomedical literature.")
        bad = ent("PubMed", "run by the national library", "PubMed is a free database of biomedical literature.")
        got = option1b.build(DOC, ask_fn=lambda c: dict(entities=[good, bad], relations=[]))
        self.assertEqual(len(got["accepted"]), 1)  # the second is the same entity: seen once
        got = option1b.build(DOC, ask_fn=lambda c: dict(entities=[bad], relations=[]))
        self.assertEqual(len(got["refused"]), 1)
        self.assertIn("not in the quote", got["refused"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
