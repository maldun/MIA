"""Tests of option1.py with a scripted model (no Ollama). Run: python3 -I test_option1.py"""
import sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import option1

DOC = ("The PRIMSA flow diagram shows the flow of studies.\n\nBoolean operators help literature searches. "
       "PubMed is a database. Bluebook systems are used by courts.")


class Chunker(unittest.TestCase):
    def test_never_cuts_inside_a_sentence(self):
        text = " ".join(f"Sentence number {i} is here." for i in range(200))
        chunks = option1.chunk(text, 300)
        self.assertGreater(len(chunks), 5)
        self.assertTrue(all(c.endswith(".") and c.startswith("Sentence") for c in chunks))
        self.assertEqual(" ".join(chunks), text)

    def test_long_sentence_is_its_own_chunk(self):
        self.assertEqual(len(option1.chunk("A " * 500 + "end. Next one.", 100)), 2)


class Validate(unittest.TestCase):
    def test_accepts_stated_entity_and_relation(self):
        self.assertIsNone(option1.validate(dict(name="PubMed", quote="PubMed is a database."), DOC))
        self.assertIsNone(option1.validate(dict(source="Boolean operators", relation="help", target="literature searches",
                                                quote="Boolean operators help literature searches."), DOC))

    def test_mangled_name_refused(self):  # the "SA Flow Diagram" case
        why = option1.validate(dict(name="SA Flow Diagram", quote="The PRIMSA flow diagram shows the flow of studies."), DOC)
        self.assertIn("name not in the document", why)

    def test_invented_quote_refused(self):
        why = option1.validate(dict(name="PubMed", quote="PubMed indexes Embase."), DOC)
        self.assertIn("not a passage", why)

    def test_relation_quote_must_hold_both_ends(self):
        why = option1.validate(dict(source="Boolean operators", relation="use", target="PubMed",
                                    quote="Boolean operators help literature searches."), DOC)
        self.assertEqual(why, "quote does not contain both ends")


class Build(unittest.TestCase):
    def test_scripted_model_and_dedup(self):
        reply = {"entities": [{"name": "PubMed", "quote": "PubMed is a database."},
                              {"name": "pubmed", "quote": "PubMed is a database."},
                              {"name": "Embase", "quote": "Embase is a database."}], "relations": []}
        res = option1.build(DOC, ask_fn=lambda _: reply)
        self.assertEqual([a["name"] for a in res["accepted"]], ["PubMed"])
        self.assertEqual(len(res["refused"]), 1)

    def test_model_failure_is_recorded(self):
        def boom(_):
            raise RuntimeError("down")
        res = option1.build(DOC, ask_fn=boom)
        self.assertIn("model step failed", res["refused"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
