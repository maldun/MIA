"""Tests of score_marks.py. Run: python3 -I test_score_marks.py"""
import io, json, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_marks as sm


def items(spec):  # spec: list of (doc, decision)
    return [dict(id=f"I{k:03d}", doc=d, decision=x, comment="") for k, (d, x) in enumerate(spec, 1)]


class Score(unittest.TestCase):
    def test_kappa_perfect_and_chance(self):
        self.assertEqual(sm.kappa([("right", "right"), ("wrong", "wrong")], sm.CLASSES), 1.0)
        self.assertAlmostEqual(sm.kappa([(True, True), (True, False), (False, True), (False, False)], [True, False]), 0.0)

    def test_report_pass_and_fail(self):
        def run(spec):
            with tempfile.TemporaryDirectory() as t:
                p = Path(t) / "m.json"
                p.write_text(json.dumps(dict(items=items(spec), missing=[dict(doc="A", note="x")])))
                buf = io.StringIO()
                with redirect_stdout(buf):
                    sm.main(["s", str(p)])
                return buf.getvalue()
        good = run([("A", "right")] * 7 + [("A", "trivial")] * 3)
        self.assertIn("right >= 68 % -> PASS", good)
        self.assertIn("invented <= 5 % -> PASS", good)
        self.assertIn("missing items, A: x", good)
        bad = run([("A", "right")] * 6 + [("A", "invented")] * 4)
        self.assertIn("right >= 68 % -> FAIL", bad)
        self.assertIn("invented <= 5 % -> FAIL", bad)

    def test_unmarked_items_are_left_out(self):
        its = items([("A", "right")]) + [dict(id="I002", doc="A", decision=None, comment="")]
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "m.json"
            p.write_text(json.dumps(dict(items=its, missing=[])))
            buf = io.StringIO()
            with redirect_stdout(buf):
                sm.main(["s", str(p)])
        self.assertIn("1 of 2 items marked", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
