"""
Offline tests for tools/make_external_suite.py and tools/label_agreement.py: the split, the false twins, the text cleaning, the cases made
from VitaminC and Wikidata rows (no network), the audit sample and the agreement.
Run with: python tests/test_external_suite.py
"""
import csv
import json
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "tools"))

import make_external_suite as M                          # noqa: E402
import label_agreement as LA                             # noqa: E402
import tag_ambiguous as TA                               # noqa: E402


class SplitAndTwins(unittest.TestCase):
    def test_split_is_stable_and_about_a_third(self):
        ids = ["p%d" % i for i in range(900)]
        first = [M.is_holdout(i) for i in ids]
        self.assertEqual(first, [M.is_holdout(i) for i in ids])
        self.assertTrue(250 < sum(first) < 350)

    def test_false_twin_is_wrong_and_near(self):
        for seed in range(300):
            rng = random.Random(seed)
            for value in (8, 330, 4806, 6650, 828):
                twin = M.false_twin(value, rng)
                self.assertNotEqual(twin, value)
                self.assertGreaterEqual(abs(twin - value), 0.05 * value)
                self.assertGreater(twin, 0)

    def test_false_twin_of_a_year_changes_by_a_few_years(self):
        for seed in range(100):
            twin = M.false_twin(1937, random.Random(seed), "year")
            self.assertTrue(0 < abs(twin - 1937) <= 10)

    def test_twin_is_reproducible(self):
        self.assertEqual(M.false_twin(4806, random.Random("a")), M.false_twin(4806, random.Random("a")))

    def test_swap_digits_never_makes_a_leading_zero(self):
        for n in (100, 1005, 4806, 90, 21):
            for seed in range(30):
                r = M.swap_digits(n, random.Random(seed))
                if r is not None:
                    self.assertEqual(len(str(r)), len(str(n)))


class Cleaning(unittest.TestCase):
    def test_clean_text(self):
        self.assertEqual(M.clean_text("Westlife ( BPI ) has 9.8�million singles , and more ."), "Westlife (BPI) has 9.8 million singles, and more.")


class Writing(unittest.TestCase):
    def cases(self):
        out = []
        for i in range(30):
            pair = "wd-Q%d-x" % i
            for truth in (True, False):
                out.append({"id": "%s-%s" % (pair, truth), "tags": ["number", "pair:" + pair, "label:people", "req:AC-2"],
                            "input": {"claim": "c%d" % i, "evidence": "", "rounds": 3, "experts": []}, "truth": truth, "pair": pair})
        out.append({"id": "vc-n", "tags": ["number", "pair:vc-9"], "input": {"claim": "x", "evidence": "e", "rounds": 3, "experts": []},
                    "truth": None, "expect": "inconclusive", "pair": "vc-9"})
        return out

    def test_pairs_stay_together_and_every_case_has_one_split(self):
        with tempfile.TemporaryDirectory() as d:
            out = M.pathlib.Path(d)
            dev, hold = M.write_suites(out, "s", self.cases(), "test")
            self.assertEqual(len(dev) + len(hold), 61)
            for rows in (dev, hold):
                for r in rows:
                    self.assertEqual(len([t for t in r["tags"] if t.startswith("split:")]), 1)
                    self.assertNotIn("pair", r)
            dev_pairs = {t for r in dev for t in r["tags"] if t.startswith("pair:")}
            hold_pairs = {t for r in hold for t in r["tags"] if t.startswith("pair:")}
            self.assertFalse(dev_pairs & hold_pairs)
            names = sorted(p.name for p in (out / "suites").iterdir())
            self.assertEqual(names, ["s", "s.holdout"])
            meta = json.load(open(out / "suites" / "s.holdout" / "suite.json"))
            self.assertEqual(meta["name"], "s.holdout")
            self.assertEqual(meta["target"], M.TARGET)

    def test_audit_sheet_has_no_truth_and_the_key_has(self):
        with tempfile.TemporaryDirectory() as d:
            out = M.pathlib.Path(d)
            n = M.write_audit(out, self.cases(), seed=7)
            self.assertGreater(n, 5)
            sheet = open(out / "audit" / "sample_sheet.csv", encoding="utf8").read()
            self.assertNotIn("True", sheet)
            self.assertNotIn("-x-", sheet)          # the case ids are not on the sheet
            self.assertNotIn("inconclusive", sheet)
            key = json.load(open(out / "audit" / "key.json"))
            self.assertEqual(len(key), n)
            self.assertTrue({v["truth"] for v in key.values()} <= {"true", "false", "unknown"})
            self.assertTrue(all(k.startswith("s") for k in key))


class Agreement(unittest.TestCase):
    def test_kappa(self):
        self.assertAlmostEqual(M.cohen_kappa(["true", "false"] * 10, ["true", "false"] * 10), 1.0)
        self.assertAlmostEqual(M.cohen_kappa(["true", "false"] * 10, ["false", "true"] * 10), -1.0)
        self.assertTrue(abs(M.cohen_kappa(["true"] * 5 + ["false"] * 5, ["true", "false"] * 5)) < 0.01 + 0.2)

    def test_agreement_tool_lists_the_differences(self):
        with tempfile.TemporaryDirectory() as d:
            sheet = os.path.join(d, "sheet.csv")
            key = os.path.join(d, "key.json")
            json.dump({k: {"case": "case-" + k, "truth": v} for k, v in {"a": "true", "b": "false", "c": "unknown", "d": "true"}.items()}, open(key, "w"))
            with open(sheet, "w", newline="", encoding="utf8") as f:
                w = csv.writer(f)
                w.writerow(["id", "claim", "evidence", "label (true / false / unknown)", "source or note"])
                w.writerows([["a", "x", "", "true", ""], ["b", "x", "", "true", ""], ["c", "x", "", "unknown", ""], ["d", "x", "", "", ""]])
            self.assertEqual(LA.main(sheet, key), 0)
            self.assertEqual(open(os.path.join(d, "ambiguous.txt")).read().split(), ["case-b"])


class TagAmbiguous(unittest.TestCase):
    def test_tags_listed_cases_once_and_leaves_the_others(self):
        with tempfile.TemporaryDirectory() as d:
            folder = os.path.join(d, "s")
            os.makedirs(folder)
            rows = [{"id": "a", "tags": ["number"], "truth": True, "note": "n"}, {"id": "b", "tags": ["number"], "truth": False}]
            with open(os.path.join(folder, "cases.jsonl"), "w") as f:
                f.write("".join(json.dumps(r) + "\n" for r in rows))
            amb = os.path.join(d, "ambiguous.txt")
            open(amb, "w").write("a\nmissing\n")
            self.assertEqual(TA.main(amb, [folder]), 0)
            self.assertEqual(TA.main(amb, [folder]), 0)           # repeating changes nothing more
            out = [json.loads(l) for l in open(os.path.join(folder, "cases.jsonl"))]
            self.assertEqual(out[0]["tags"], ["ambiguous", "number", "retired"])
            self.assertEqual(out[0]["note"].count("ambiguous:"), 1)
            self.assertEqual(out[1]["tags"], ["number"])


if __name__ == "__main__":
    unittest.main()
