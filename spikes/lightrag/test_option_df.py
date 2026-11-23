"""Tests of option_df.py (definitions and stated facts) with a scripted model (no Ollama). Run: python3 -I test_option_df.py"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import option_df

DOC = ("A meta-analysis is a statistical analysis that combines the results of multiple studies.\n\n"
       "The term was coined in 1976 by the statistician Gene Glass. Peer review is the evaluation of work by colleagues.")


class Validate(unittest.TestCase):
    def test_accepts_a_stated_definition_and_fact(self):
        self.assertIsNone(option_df.validate(dict(term="meta-analysis", definition="a statistical analysis combining studies",
                                                  quote="A meta-analysis is a statistical analysis that combines the results of multiple studies."), DOC))
        self.assertIsNone(option_df.validate(dict(statement="Gene Glass coined the term in 1976.",
                                                  quote="The term was coined in 1976 by the statistician Gene Glass."), DOC))

    def test_a_quote_not_in_the_document_is_refused(self):
        why = option_df.validate(dict(statement="Glass coined it in 1977.", quote="The term was coined in 1977 by Gene Glass."), DOC)
        self.assertIn("not a passage", why)

    def test_a_definition_whose_term_is_not_in_the_document_is_refused(self):
        why = option_df.validate(dict(term="systematic review", definition="x",
                                      quote="Peer review is the evaluation of work by colleagues."), DOC)
        self.assertIn("term not in the document", why)

    def test_a_definition_whose_quote_does_not_hold_the_term_is_refused(self):
        why = option_df.validate(dict(term="peer review", definition="x",
                                      quote="The term was coined in 1976 by the statistician Gene Glass."), DOC)
        self.assertIn("quote does not contain the term", why)

    def test_an_empty_quote_is_refused(self):
        self.assertIn("not a passage", option_df.validate(dict(statement="Glass coined it.", quote=""), DOC))


class Build(unittest.TestCase):
    def test_kinds_duplicates_and_a_failed_chunk(self):
        replies = iter([{"definitions": [dict(term="Peer review", definition="evaluation by colleagues",
                                              quote="Peer review is the evaluation of work by colleagues.")] * 2,
                         "facts": [dict(statement="Coined in 1976.", quote="coined in 1976 by the statistician Gene Glass"),
                                   dict(statement="Coined in 1980.", quote="coined in 1980")]}])
        result = option_df.build(DOC, ask_fn=lambda text: next(replies))
        kinds = sorted(a["kind"] for a in result["accepted"])
        self.assertEqual(kinds, ["definition", "fact"])
        self.assertEqual([r["reason"] for r in result["refused"]], ["quote is not a passage of the document"])
        failing = option_df.build(DOC, ask_fn=lambda text: (_ for _ in ()).throw(TimeoutError("slow")))
        self.assertIn("model step failed", failing["refused"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
