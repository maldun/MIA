"""
tools/promote_labelled.py: only labelled cases move, by suite tag and split tag; nothing is overwritten; a bad tag stops it.
Run: python tests/test_promote_labelled.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import promote_labelled as P                          # noqa: E402


def case(i, suite, split, label=True):
    tags = ["rt:RT-9", "suite:" + suite, "split:" + split] + (["label:people"] if label else ["source:draft"])
    return {"id": "c%d" % i, "tags": tags, "input": {}, "truth": None, "expect": "pass", "note": ""}


class Promote(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.drafts = os.path.join(self.tmp.name, "d.jsonl")
        self.suites = os.path.join(self.tmp.name, "suites")
        os.makedirs(self.suites)
        rows = [case(0, "rt_a", "dev"), case(1, "rt_a", "holdout"), case(2, "rt_b", "dev"), case(3, "rt_a", "dev", label=False)]
        with open(self.drafts, "w") as fp:
            fp.writelines(json.dumps(r) + "\n" for r in rows)

    def run_tool(self, *extra):
        return P.main([self.drafts, "--suites", self.suites, *extra])

    def test_without_do_nothing_is_written(self):
        self.assertEqual(self.run_tool(), 0)
        self.assertEqual(os.listdir(self.suites), [])

    def test_labelled_cases_move_by_suite_and_split_and_the_rest_stays(self):
        self.assertEqual(self.run_tool("--do"), 0)
        self.assertEqual(sorted(os.listdir(self.suites)), ["rt_a", "rt_a.holdout", "rt_b"])
        ids = lambda folder: [json.loads(l)["id"] for l in open(os.path.join(self.suites, folder, "cases.jsonl"))]    # noqa: E731
        self.assertEqual((ids("rt_a"), ids("rt_a.holdout"), ids("rt_b")), (["c0"], ["c1"], ["c2"]))
        self.assertEqual(json.load(open(os.path.join(self.suites, "rt_a", "suite.json")))["name"], "rt_a")
        self.assertEqual([json.loads(l)["id"] for l in open(self.drafts)], ["c3"])                                     # the unlabelled draft stays

    def test_only_and_no_overwrite(self):
        self.assertEqual(self.run_tool("--do", "--only", "rt_b"), 0)
        self.assertEqual(os.listdir(self.suites), ["rt_b"])
        self.assertEqual(self.run_tool("--do", "--only", "rt_b"), 0)               # c2 is gone from the drafts, nothing left for rt_b
        self.assertEqual(self.run_tool("--do"), 0)
        with open(self.drafts, "w") as fp:
            fp.write(json.dumps(case(7, "rt_a", "dev")) + "\n")
        self.assertEqual(self.run_tool("--do"), 1)                                  # rt_a exists already: refused, nothing changed
        self.assertEqual(len(open(self.drafts).readlines()), 1)

    def test_a_labelled_case_without_a_split_stops_the_tool(self):
        bad = case(9, "rt_a", "dev")
        bad["tags"] = [t for t in bad["tags"] if not t.startswith("split:")]
        with open(self.drafts, "a") as fp:
            fp.write(json.dumps(bad) + "\n")
        self.assertEqual(self.run_tool("--do"), 1)
        self.assertEqual(os.listdir(self.suites), [])


if __name__ == "__main__":
    unittest.main()
