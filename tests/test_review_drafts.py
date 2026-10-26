"""
tools/review_drafts.py: keep adds label:people and removes source:draft, drop removes the case, skip and quit change nothing, a file without changes is not rewritten.
Run: python tests/test_review_drafts.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import review_drafts as R                             # noqa: E402


def case(i, tags):
    return {"id": "c%d" % i, "tags": tags, "input": {"x": i}, "truth": None, "expect": "pass", "note": "n"}


class Review(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "d.jsonl")
        rows = [case(0, ["rt:RT-1", "split:dev", "source:draft"]), case(1, ["rt:RT-1", "split:dev", "source:draft"]),
                case(2, ["rt:RT-1", "split:holdout", "source:draft"]), case(3, ["rt:RT-1", "split:dev", "label:people"])]
        with open(self.path, "w") as fp:
            fp.writelines(json.dumps(r) + "\n" for r in rows)

    def run_with(self, answers, **kw):
        asked = iter(answers)
        result = R.review(self.path, ask=lambda prompt: next(asked), show=lambda *_: None, **kw)
        with open(self.path) as fp:
            return result, [json.loads(line) for line in fp]

    def test_keep_drop_skip(self):
        (kept, dropped), rows = self.run_with(["k", "d", "s"])
        self.assertEqual((kept, dropped), (1, 1))
        self.assertEqual([r["id"] for r in rows], ["c0", "c2", "c3"])
        self.assertEqual(rows[0]["tags"], ["label:people", "rt:RT-1", "split:dev"])         # labelled, no longer a draft
        self.assertIn("source:draft", rows[1]["tags"])                                     # skipped: unchanged
        self.assertTrue(os.path.exists(self.path + ".bak"))

    def test_quit_saves_what_was_decided_and_keeps_the_rest(self):
        _, rows = self.run_with(["k", "q"])
        self.assertEqual([r["id"] for r in rows], ["c0", "c1", "c2", "c3"])
        self.assertNotIn("source:draft", rows[0]["tags"])
        self.assertIn("source:draft", rows[1]["tags"])

    def test_nothing_decided_nothing_written_and_list_asks_nothing(self):
        before = open(self.path).read()
        self.run_with(["s", "s", "s"])
        self.assertEqual(open(self.path).read(), before)
        self.assertFalse(os.path.exists(self.path + ".bak"))
        self.run_with([], list_only=True)
        self.assertEqual(open(self.path).read(), before)


if __name__ == "__main__":
    unittest.main()
