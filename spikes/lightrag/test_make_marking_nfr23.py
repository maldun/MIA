"""Tests of the NFR-23 draw (no model, no files). Run: python3 -I test_make_marking_nfr23.py"""
import random, sys, unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_marking_nfr23 import draw


def runs(n_docs, n_def, n_fact):
    return [(f"doc{d:02d}", [dict(kind="definition", i=i) for i in range(n_def)] + [dict(kind="fact", i=i) for i in range(n_fact)])
            for d in range(n_docs)]


class Draw(unittest.TestCase):
    def test_per_document_counts_then_top_up_to_120(self):
        # 13 documents with 3 definitions and 20 facts: 13 x (3 + 5) = 104 by the counts, 16 topped up from the rest
        got = draw(runs(13, 3, 20), {"definition": 5, "fact": 5}, random.Random(1))
        self.assertEqual(len(got), 120)
        self.assertEqual(Counter(p["kind"] for _, p in got)["definition"], 39)
        self.assertEqual(len({(d, p["kind"], p["i"]) for d, p in got}), 120)     # nothing drawn twice

    def test_a_short_pool_gives_all_and_no_more(self):
        got = draw(runs(2, 1, 1), {"definition": 5, "fact": 5}, random.Random(1))
        self.assertEqual(len(got), 4)

    def test_the_same_seed_gives_the_same_draw(self):
        a = draw(runs(13, 9, 9), {"definition": 5, "fact": 5}, random.Random(20261123))
        b = draw(runs(13, 9, 9), {"definition": 5, "fact": 5}, random.Random(20261123))
        self.assertEqual(a, b)
        self.assertEqual(len(a), 130)                                             # counts give 130; no top-up, no cut


if __name__ == "__main__":
    unittest.main()
