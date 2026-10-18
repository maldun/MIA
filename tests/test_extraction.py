"""
Tests for the extraction stage: the shape of a claim, the scorer (every kind of success and failure, with hand-made predictions), the equivalences it accepts (the same arithmetic written differently,
unit names, date formats), the rule-based baseline, the extraction target of the harness and the metrics. Run with the MIA virtualenv: python tests/test_extraction.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import extraction as E                                # noqa: E402
import harness as H                                   # noqa: E402
import metrics as M                                   # noqa: E402
from core import Core                                 # noqa: E402
from library import Library                           # noqa: E402

SOURCE = "The Eiffel Tower is 330 metres tall. It was completed in 1889. 12 * 1.5 + 3 = 21."
S1, S2, S3 = "The Eiffel Tower is 330 metres tall.", "It was completed in 1889.", "12 * 1.5 + 3 = 21."
GOLD = [{"type": "fact", "anchor": S1, "data": {"entities": ["Eiffel Tower"], "facts": ["330 metres"]}},
        {"type": "numeric", "anchor": S3, "data": {"expression": "12*1.5+3", "value": 21}}]


def fact(text=S1, entities=("Eiffel Tower",), facts=("330 metres",)):
    return {"type": "fact", "text": text, "data": {"entities": list(entities), "facts": list(facts)}}


def numeric(text=S3, expression="12*1.5+3", value=21):
    return {"type": "numeric", "text": text, "data": {"expression": expression, "value": value}}


class ClaimShape(unittest.TestCase):
    def test_valid_claims(self):
        for claim in (fact(), numeric(), {"type": "unit", "text": "x", "data": {"value": 1, "from_unit": "km", "to_unit": "mi", "result_value": 0.6}},
                      {"type": "date", "text": "x", "data": {"kind": "weekday"}}, {"type": "quotation", "text": "x", "data": {"quote": "q"}}, {"type": "citation", "text": "x", "data": {"url": "u"}}):
            self.assertEqual(E.validate_claim(claim), [], claim)

    def test_problems(self):
        cases = [("text", "must be an object"), ({"type": "gossip", "text": "x", "data": {}}, "type must be"), ({"type": "fact", "text": "", "data": {"entities": ["a"]}}, "text"),
                 ({"type": "fact", "text": "x", "data": "no"}, "data must be"), ({"type": "numeric", "text": "x", "data": {"expression": "1+1"}}, "data.value"),
                 ({"type": "fact", "text": "x", "data": {"entities": []}}, "data.entities"), ({"type": "unit", "text": "x", "data": {"value": 1}}, "data.from_unit")]
        for claim, expected in cases:
            self.assertIn(expected, " ".join(E.validate_claim(claim)), claim)


class Scoring(unittest.TestCase):
    def score(self, predicted, gold=GOLD, source=SOURCE):
        return E.score_extraction(source, predicted, gold)

    def test_a_perfect_extraction(self):
        s = self.score([fact(), numeric()])
        self.assertTrue(s["ok"])
        self.assertEqual((s["gold"], s["predicted"], s["matched"]), (2, 2, 2))
        self.assertTrue(self.score([numeric(), fact()])["ok"])                              # the order does not matter

    def test_a_shorter_span_of_the_same_sentence_is_fine(self):
        self.assertTrue(self.score([fact(text="Eiffel Tower is 330 metres tall"), numeric(text="12 * 1.5 + 3 = 21")])["ok"])

    def test_missed(self):
        s = self.score([fact()])
        self.assertFalse(s["ok"])
        self.assertEqual([m["anchor"] for m in s["missed"]], [S3])
        self.assertEqual(s["matched"], 1)

    def test_wrong_type(self):
        s = self.score([fact(), dict(numeric(), type="fact", data={"entities": ["x"], "facts": ["21"]})])
        self.assertEqual([(w["wanted"], w["got"]) for w in s["wrong_type"]], [("numeric", "fact")])
        self.assertFalse(s["ok"])

    def test_wrong_data(self):
        s = self.score([fact(), numeric(value=22)])
        self.assertEqual([(w["type"], w["keys"]) for w in s["wrong_data"]], [("numeric", ["value"])])
        s = self.score([fact(facts=("331 metres",)), numeric()])
        self.assertEqual(s["wrong_data"][0]["keys"], ["facts"])
        s = self.score([{"type": "fact", "text": S1, "data": {"entities": ["Eiffel Tower"]}}, numeric()])
        self.assertEqual(s["wrong_data"][0]["keys"], ["facts"])                           # a missing key is wrong data

    def test_spurious_duplicates_and_unanchored(self):
        s = self.score([fact(), numeric(), fact(text=S2, entities=("Eiffel Tower",), facts=("1889",))])
        self.assertEqual([x["text"] for x in s["spurious"]], [S2])                       # a claim where the person found none
        s = self.score([fact(), numeric(), fact()])
        self.assertEqual(len(s["duplicates"]), 1)
        self.assertFalse(s["ok"])
        s = self.score([fact(text="The Eiffel Tower stands 330 metres high."), numeric()])
        self.assertEqual([x["text"] for x in s["unanchored"]], ["The Eiffel Tower stands 330 metres high."])   # paraphrased: not a verbatim span
        invalid = self.score([fact(), numeric(), {"type": "fact", "text": S2, "data": {}}])
        self.assertEqual(len(invalid["invalid"]), 1)

    def test_texts_without_claims(self):
        self.assertTrue(self.score([], gold=[], source="I like it.")["ok"])
        s = self.score([fact(text="I like it.")], gold=[], source="I like it.")
        self.assertEqual((len(s["spurious"]), s["ok"]), (1, False))
        self.assertFalse(self.score([], gold=GOLD)["ok"])
        self.assertTrue(self.score(None, gold=[], source="x")["ok"])
        self.assertEqual(self.score(["junk", 5], gold=[], source="x")["predicted"], 0)       # things that are no claims at all are ignored

    def test_two_claims_in_one_sentence(self):
        text = "The area is 7 * 8 = 56 and the perimeter is 2 * (7 + 8) = 30."
        gold = [{"type": "numeric", "anchor": text, "data": {"expression": "7*8", "value": 56}}, {"type": "numeric", "anchor": text, "data": {"expression": "2*(7+8)", "value": 30}}]
        both = [numeric(text, "7*8", 56), numeric(text, "2*(7+8)", 30)]
        self.assertTrue(E.score_extraction(text, both, gold)["ok"])
        self.assertTrue(E.score_extraction(text, both[::-1], gold)["ok"])
        one = E.score_extraction(text, both[:1], gold)
        self.assertEqual((one["matched"], len(one["missed"])), (1, 1))
        twice = E.score_extraction(text, [both[0], both[0]], gold)
        self.assertEqual((twice["matched"], len(twice["wrong_data"])), (1, 1))             # the same claim twice does not find the second one

    def test_equivalent_data_is_accepted(self):
        def check(claim_type, data, gold_data, source="A sentence with a claim."):
            claim = {"type": claim_type, "text": source, "data": data}
            return E.score_extraction(source, [claim], [{"type": claim_type, "anchor": source, "data": gold_data}])["ok"]
        self.assertTrue(check("numeric", {"expression": "3 + 12*1.5", "value": "21.0"}, {"expression": "12*1.5+3", "value": 21}))                       # same arithmetic, number as text
        self.assertTrue(check("numeric", {"expression": "(12*1.5)+3", "value": 21.0}, {"expression": "12*1.5+3", "value": 21}))
        self.assertFalse(check("numeric", {"expression": "12*1.5-3", "value": 21}, {"expression": "12*1.5+3", "value": 21}))
        self.assertTrue(check("unit", {"value": "5", "from_unit": "kilometers", "to_unit": "miles", "result_value": 3.1}, {"value": 5, "from_unit": "km", "to_unit": "mi", "result_value": 3.1}))
        self.assertTrue(check("unit", {"value": 100, "from_unit": "°C", "to_unit": "°F", "result_value": "212"}, {"value": 100, "from_unit": "C", "to_unit": "F", "result_value": 212}))
        self.assertFalse(check("unit", {"value": 5, "from_unit": "km", "to_unit": "kg", "result_value": 3.1}, {"value": 5, "from_unit": "km", "to_unit": "mi", "result_value": 3.1}))
        self.assertTrue(check("date", {"kind": "weekday", "date": "1 January 2000", "weekday": "saturday"}, {"kind": "weekday", "date": "2000-01-01", "weekday": "Saturday"}))
        self.assertTrue(check("date", {"kind": "weekday", "date": "01.01.2000", "weekday": "Sat"}, {"kind": "weekday", "date": "2000-01-01", "weekday": "Saturday"}))
        self.assertFalse(check("date", {"kind": "weekday", "date": "2000-01-02", "weekday": "Saturday"}, {"kind": "weekday", "date": "2000-01-01", "weekday": "Saturday"}))
        self.assertTrue(check("fact", {"entities": ["the Eiffel Tower", "Paris"], "facts": ["330 metres tall"]}, {"entities": ["Eiffel Tower"], "facts": ["330 metres"]}))   # more and longer is fine
        self.assertFalse(check("fact", {"entities": ["Paris"], "facts": ["330 metres"]}, {"entities": ["Eiffel Tower"], "facts": ["330 metres"]}))
        self.assertTrue(check("quotation", {"quote": "We shall build a tower", "attributed_to": "Gustave Eiffel"}, {"quote": "we shall build a tower.", "attributed_to": "Eiffel"}))
        self.assertTrue(check("citation", {"url": "https://a.example/x/"}, {"url": "https://a.example/x"}))
        self.assertTrue(check("fact", {"entities": ["A"], "facts": ["1083"], "extra": "ignored"}, {"entities": ["A"], "facts": ["1083"]}))


class RulesBaseline(unittest.TestCase):
    def claims(self, text):
        return E.extract_claims_rules(text)["claims"]

    def test_arithmetic(self):
        c = self.claims("Quick check: 12 * 1.5 + 3 = 21.")
        self.assertEqual((c[0]["type"], c[0]["data"]), ("numeric", {"expression": "12*1.5+3", "value": 21.0}))
        self.assertEqual(self.claims("15 plus 27 is 42.")[0]["data"], {"expression": "15+27", "value": 42.0})
        self.assertEqual(self.claims("It is 1,000 / 4 = 250.")[0]["data"]["expression"], "1000/4")

    def test_units(self):
        c = self.claims("Note that 100 C is 212 F.")
        self.assertEqual((c[0]["type"], c[0]["data"]), ("unit", {"value": 100.0, "from_unit": "C", "to_unit": "F", "result_value": 212.0}))
        self.assertEqual(self.claims("2 hours equals 120 minutes.")[0]["data"]["to_unit"], "minutes")

    def test_dates_and_leap_years(self):
        self.assertEqual(self.claims("January 1, 2000 was a Saturday.")[0]["data"], {"kind": "weekday", "date": "January 1, 2000", "weekday": "Saturday"})
        self.assertEqual(self.claims("1900 was not a leap year.")[0]["data"], {"kind": "leap_year", "year": 1900, "leap": False})
        self.assertEqual(self.claims("2024 is a leap year.")[0]["data"]["leap"], True)

    def test_quotations_and_citations(self):
        q = self.claims("“The only thing we have to fear is fear itself,” said Franklin Roosevelt in 1933.")[0]
        self.assertEqual((q["type"], q["data"]["attributed_to"]), ("quotation", "Franklin Roosevelt"))
        c = self.claims("Read https://example.com/a/b. It is long.")[0]
        self.assertEqual((c["type"], c["data"]["url"]), ("citation", "https://example.com/a/b"))                 # the full stop is not part of the address
        c = self.claims("The numbers come from the census (https://census.example.gov/results).")[0]
        self.assertEqual(c["data"]["url"], "https://census.example.gov/results")

    def test_facts(self):
        c = self.claims("The Eiffel Tower is 330 metres tall.")[0]
        self.assertEqual((c["type"], c["data"]["entities"], c["data"]["facts"]), ("fact", ["Eiffel Tower"], ["330 metres"]))
        self.assertEqual(self.claims("Python was first released in 1991 by Guido van Rossum.")[0]["data"]["entities"], ["Python", "Guido van Rossum"])

    def test_hedges_questions_and_advice_are_not_claims(self):
        for text in ("The tower might be 330 metres tall.", "How tall is the Eiffel Tower in 2024?", "I think Paris has 2 million people.", "You should visit Paris for 3 days."):
            self.assertEqual(self.claims(text), [], text)

    def test_every_text_is_a_verbatim_span_and_sentences_are_split_sensibly(self):
        text = "The Eiffel Tower is 330 metres tall. Mount Everest rises 8,849 metres above sea level. It costs 2.5 euros."
        found = self.claims(text)
        self.assertEqual([c["text"] for c in found[:2]], ["The Eiffel Tower is 330 metres tall.", "Mount Everest rises 8,849 metres above sea level."])    # 8,849 and 2.5 do not split a sentence
        for claim in found:
            self.assertIn(claim["text"], text)
            self.assertEqual(E.validate_claim(claim), [])

    def test_empty_and_odd_input(self):
        for text in ("", "   ", "...", "!!!"):
            self.assertEqual(self.claims(text), [])


class Anchoring(unittest.TestCase):
    TEXT = "The Eiffel Tower is 330 metres tall. It was completed in 1889. Nobody enjoys cold showers."

    def anchor(self, claims):
        return E.anchor_claims(self.TEXT, claims)

    def test_verbatim_claims_stay(self):
        out = self.anchor([fact(), fact(text="Eiffel Tower is 330 metres tall")])
        self.assertEqual([c["text"] for c in out["claims"]], [S1, "Eiffel Tower is 330 metres tall"])
        self.assertEqual((out["dropped"], out["snapped"]), ([], 0))

    def test_a_reworded_claim_is_snapped_to_its_sentence(self):
        out = self.anchor([fact(text="The Eiffel Tower is 330 metres high.")])
        self.assertEqual([c["text"] for c in out["claims"]], [S1])
        self.assertEqual(out["snapped"], 1)

    def test_invented_and_badly_shaped_claims_are_dropped_with_the_reason(self):
        out = self.anchor([fact(text="The Colosseum was built in 80 AD and holds 50,000 spectators."), {"type": "fact", "text": S1, "data": {}}, "junk", {"type": "mystery", "text": S1, "data": {}}, fact()])
        self.assertEqual([c["text"] for c in out["claims"]], [S1])
        reasons = " | ".join(d["reason"] for d in out["dropped"])
        for part in ("not in the source", "data.entities", "must be an object", "type must be"):
            self.assertIn(part, reasons)

    def test_duplicates_go_and_odd_input_is_safe(self):
        self.assertEqual(len(self.anchor([fact(), fact(), fact()])["claims"]), 1)
        self.assertEqual(self.anchor(None)["claims"], [])
        self.assertEqual(self.anchor("not a list")["claims"], [])
        self.assertEqual(E.anchor_claims("", [fact()])["claims"], [])

    def test_the_result_is_always_scorable_and_anchored(self):
        out = self.anchor([fact(text="The Eiffel Tower is 330 metres high."), fact(text="Something never said in the text at all.")])
        score = E.score_extraction(self.TEXT, out["claims"], [{"type": "fact", "anchor": S1, "data": {"entities": ["Eiffel Tower"], "facts": ["330 metres"]}}])
        self.assertTrue(score["ok"])
        self.assertEqual(score["unanchored"], [])


class Tidying(unittest.TestCase):
    def tidy(self, text, claims):
        return E.tidy_claims(text, claims)

    @staticmethod
    def claim(claim_type, text, **data):
        return {"type": claim_type, "text": text, "data": data}

    def test_a_fact_gives_way_to_a_specific_claim_of_its_sentence(self):
        text = "The route is 5 km long, which is 3.1 mi."
        unit = self.claim("unit", text, value=5, from_unit="km", to_unit="mi", result_value=3.1)
        out = self.tidy(text, [self.claim("fact", "The route is 5 km long", entities=["route"]), unit])
        self.assertEqual(out["claims"], [unit])
        self.assertEqual(out["dropped"][0]["reason"], "the sentence has a more specific claim")

    def test_of_several_facts_the_longest_stays(self):
        text = "The tower was built for the 1889 World's Fair in Paris."
        long_fact = self.claim("fact", text, entities=["tower"])
        out = self.tidy(text, [self.claim("fact", "in Paris", entities=["Paris"]), long_fact, self.claim("fact", "for the 1889 World's Fair", entities=["Fair"])])
        self.assertEqual(out["claims"], [long_fact])

    def test_a_date_claim_the_sentence_does_not_talk_about_goes(self):
        text = "Marie Curie won the Nobel Prize in Physics in 1903."
        fact_claim = self.claim("fact", text, entities=["Marie Curie"])
        out = self.tidy(text, [fact_claim, self.claim("date", "1903", kind="leap_year", year=1903, leap=False)])
        self.assertEqual(out["claims"], [fact_claim])
        self.assertIn("leap year", out["dropped"][0]["reason"])
        leap = self.claim("date", "1900 was not a leap year.", kind="leap_year", year=1900, leap=False)
        self.assertEqual(self.tidy("1900 was not a leap year.", [leap])["claims"], [leap])

    def test_two_calculations_in_one_sentence_stay_but_not_the_same_one_twice(self):
        text = "2 + 3 = 5 and 4 * 4 = 16."
        a, b = self.claim("numeric", "2 + 3 = 5", expression="2+3", value=5), self.claim("numeric", "4 * 4 = 16", expression="4*4", value=16)
        self.assertEqual(self.tidy(text, [a, b])["claims"], [a, b])
        again = self.claim("numeric", "2 + 3", expression="2+3", value=5)
        self.assertEqual(self.tidy(text, [a, again, b])["claims"], [a, b])

    def test_claims_of_different_sentences_do_not_touch_each_other(self):
        text = "The tower is 330 metres tall. It was completed in 1889."
        claims = [self.claim("fact", "The tower is 330 metres tall.", entities=["tower"]), self.claim("date", "It was completed in 1889.", kind="age")]
        self.assertEqual(self.tidy(text, claims)["claims"], [claims[0]])        # the age claim has no support in its sentence; the fact stays
        facts = [self.claim("fact", "The tower is 330 metres tall.", entities=["tower"]), self.claim("fact", "It was completed in 1889.", entities=["tower"])]
        self.assertEqual(self.tidy(text, facts)["claims"], facts)

    def test_odd_input_is_safe(self):
        self.assertEqual(self.tidy("", [])["claims"], [])
        self.assertEqual(self.tidy("text", None)["claims"], [])
        self.assertEqual(self.tidy("text", ["junk", self.claim("fact", "text", entities=["x"])])["claims"], [self.claim("fact", "text", entities=["x"])])


class ModelPipeline(unittest.TestCase):
    TEXT = "The Eiffel Tower is 330 metres tall. I think it is pretty."

    def run_with(self, reply):
        outer = self

        class Model:
            calls = []

            def chat(self, messages, schema=None, model=None, profile=None, options=None):
                self.calls.append((messages, schema, profile))
                return reply if isinstance(reply, str) else json.dumps(reply)
        model = Model()
        tmp = tempfile.mkdtemp()
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tmp, model=model)
        return core.run("extract_claims", {"text": self.TEXT}), model

    def test_a_model_answer_goes_through_the_anchoring(self):
        result, model = self.run_with({"claims": [{"type": "fact", "text": "The Eiffel Tower is 330 metres high.", "data": {"entities": ["Eiffel Tower"], "facts": ["330 metres"]}},
                                                 {"type": "fact", "text": "The tower was a gift from Mars.", "data": {"entities": ["Mars"], "facts": ["gift"]}}]})
        self.assertEqual(result.status, "done")
        self.assertEqual([c["text"] for c in result.answer["claims"]], ["The Eiffel Tower is 330 metres tall."])
        self.assertEqual((result.answer["snapped"], len(result.answer["dropped"])), (1, 1))
        prompt = model.calls[0][0][1]["content"]
        self.assertIn(self.TEXT, prompt)
        self.assertIn(E.EXTRACTION_GUIDE, prompt)
        schema = model.calls[0][1]
        self.assertEqual(schema["properties"]["claims"]["items"]["properties"]["type"]["enum"], list(E.CLAIM_TYPES))

    def test_an_answer_that_does_not_fit_the_schema_is_an_error(self):
        result, _ = self.run_with("this is not json at all")
        self.assertEqual(result.status, "error")

    def test_the_guide_in_the_library_is_the_guide_of_the_code(self):
        library = Library(os.path.join(REPO, "library"))
        self.assertEqual(library.resolve("view.extract_claims@1", "node")["params"]["guide"]["default"], E.EXTRACTION_GUIDE)
        for claim_type in E.CLAIM_TYPES:
            if claim_type != "computable":
                self.assertIn("- %s:" % claim_type, E.EXTRACTION_GUIDE)


class ExtractionMetrics(unittest.TestCase):
    def record(self, case, gold, predicted, matched, **problems):
        score = {"gold": gold, "predicted": predicted, "matched": matched, "ok": not any(problems.values()) and gold == matched == predicted,
                 **{k: problems.get(k, []) for k in ("missed", "wrong_data", "wrong_type", "spurious", "duplicates", "unanchored", "invalid")}}
        return {"case": case, "status": "pass" if score["ok"] else "fail", "score": score, "expect": "pass", "truth": None, "tags": []}

    def test_micro_averages_and_empty_cases(self):
        records = [self.record("a", 2, 2, 2), self.record("b", 2, 1, 1, missed=[{}]), self.record("c", 0, 0, 0), self.record("d", 0, 2, 0, spurious=[{}, {}]), self.record("e", 1, 2, 1, duplicates=[{}], unanchored=[{}])]
        m = M.extraction_metrics(records)
        self.assertEqual((m["cases"], m["gold"], m["predicted"], m["matched"]), (5, 5, 7, 4))
        self.assertEqual((m["precision"]["k"], m["precision"]["n"], m["recall"]["k"], m["recall"]["n"]), (4, 7, 4, 5))
        self.assertAlmostEqual(m["f1"], 2 * (4 / 7) * (4 / 5) / (4 / 7 + 4 / 5))
        self.assertEqual((m["perfect"]["k"], m["perfect"]["n"]), (2, 5))
        self.assertEqual((m["empty_cases"], m["empty_clean"]["k"]), (2, 1))                       # c is clean, d invented two claims
        self.assertEqual(m["problems"]["spurious"], 2)
        self.assertEqual((m["unanchored"]["k"], m["unanchored"]["n"]), (1, 7))

    def test_no_scored_records(self):
        m = M.extraction_metrics([{"case": "x", "status": "pass"}])
        self.assertEqual((m["cases"], m["f1"]), (0, None))


class HarnessTarget(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def suite(self, cases):
        folder = os.path.join(self.tmp.name, "ext")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "suite.json"), "w") as fp:
            json.dump({"name": "ext", "description": "t", "target": {"kind": "extraction", "skill": "extract_claims_rules"}}, fp)
        with open(os.path.join(folder, "cases.jsonl"), "w") as fp:
            for case in cases:
                fp.write(json.dumps(case) + "\n")
        return H.load_suite(folder)

    def test_validation_of_gold(self):
        for bad, text in (({"id": "a", "input": {"text": "x"}, "expect": "pass"}, "needs 'gold'"), ({"id": "a", "input": {"text": "x"}, "expect": "pass", "gold": [{"type": "fact"}]}, "'type' and 'anchor'"),
                          ({"id": "a", "input": {"text": "Hello there"}, "expect": "pass", "gold": [{"type": "fact", "anchor": "Goodbye"}]}, "verbatim part")):
            with self.assertRaises(H.SuiteError) as raised:
                self.suite([bad])
            self.assertIn(text, str(raised.exception))
        self.assertEqual(len(self.suite([{"id": "a", "input": {"text": "Nothing here."}, "expect": "pass", "gold": []}]).cases), 1)

    def test_a_run_scores_the_claims(self):
        text = "The Eiffel Tower is 330 metres tall. I think it is pretty."
        suite = self.suite([{"id": "ok", "input": {"text": text}, "expect": "pass",
                             "gold": [{"type": "fact", "anchor": "The Eiffel Tower is 330 metres tall.", "data": {"entities": ["Eiffel Tower"], "facts": ["330 metres"]}}]},
                            {"id": "missed", "input": {"text": text}, "expect": "pass",
                             "gold": [{"type": "fact", "anchor": "The Eiffel Tower is 330 metres tall.", "data": {"entities": ["Eiffel Tower"], "facts": ["330 metres"]}},
                                      {"type": "fact", "anchor": "I think it is pretty.", "data": {"entities": ["x"]}}]}])
        run = H.Harness(self.core).run(suite)
        self.assertEqual([r["status"] for r in run.records], ["pass", "fail"])
        self.assertTrue(run.records[0]["score"]["ok"])
        self.assertEqual(run.records[1]["score"]["missed"][0]["anchor"], "I think it is pretty.")
        text_report = H.format_report(run)
        for part in ("as an extractor", "precision", "recall", "NOT PERFECT missed"):
            self.assertIn(part, text_report)

    def test_a_pipeline_without_claims_is_an_error_status(self):
        suite = self.suite([{"id": "a", "input": {"text": "x"}, "expect": "pass", "gold": []}])
        run = H.Harness(self.core).run(suite, {"name": "summarizer", "skill": "summarize"})            # answers {summary, key_points}: no claims
        self.assertTrue(run.records[0]["status"].startswith("error:"))


class ShippedSuite(unittest.TestCase):
    def test_the_suite_is_valid_and_balanced(self):
        suite = H.load_suite(os.path.join(REPO, "eval", "suites", "extraction"))
        self.assertGreaterEqual(len(suite.cases), 45)
        empty = [c for c in suite.cases if not c["gold"]]
        self.assertGreaterEqual(len(empty), 8)                                                           # texts with nothing to find are half of the difficulty
        types = {g["type"] for c in suite.cases for g in c["gold"]}
        self.assertEqual(types, {"numeric", "unit", "date", "fact", "quotation", "citation"})
        for case in suite.cases:
            for g in case["gold"]:
                self.assertEqual(E.validate_claim({"type": g["type"], "text": g["anchor"], "data": g.get("data", {})}), [], case["id"])

    def test_the_rules_baseline_does_not_get_worse(self):
        """the floor for any model-based extractor: documented in eval/baselines; a drop means the rules or the scorer broke"""
        suite = H.load_suite(os.path.join(REPO, "eval", "suites", "extraction"))
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), tempfile.mkdtemp())
        run = H.Harness(core).run(suite)
        m = M.extraction_metrics(run.records)
        self.assertGreaterEqual(m["f1"], 0.70)
        self.assertGreaterEqual(m["perfect"]["k"], 32)
        self.assertEqual(m["unanchored"]["k"], 0)                                                          # rules only ever return spans of the text
        self.assertEqual(M.stability(H.Harness(core).run(suite, repeats=2).records)["rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
