"""Tests of debate_spike.py loops with a scripted model (no Ollama). Run: python3 -I test_debate_spike.py"""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import debate_spike as d


def scripted(replies):
    it = iter(replies)
    return lambda prompt, schema, seed: next(it)


def v(x): return dict(verdict=x, reason="r")
def pts(): return dict(points="p")
def judge(x, decided): return dict(verdict=x, decided=decided, reason="r")


class Loops(unittest.TestCase):
    def test_single(self):
        r = d.single("c", scripted([v("refuted")]), 1, d.Budget())
        self.assertEqual((r["verdict"], r["rounds"]), ("refuted", 1))

    def test_cops_stops_when_judge_decides(self):
        b = d.Budget()
        r = d.cops("c", scripted([pts(), pts(), judge("refuted", True)]), 1, b)
        self.assertEqual((r["verdict"], r["rounds"], r["stop"], b.calls), ("refuted", 1, "judge", 3))

    def test_cops_runs_to_round_cap_and_counts_calls(self):
        b = d.Budget()
        rep = [pts(), pts(), judge("supported", False)] * 3
        r = d.cops("c", scripted(rep), 1, b)
        self.assertEqual((r["rounds"], r["stop"], b.calls, r["history"]), (3, "cap", 9, ["supported"] * 3))

    def test_cops_call_budget_ends_with_last_verdict(self):
        b = d.Budget(max_calls=4)
        rep = [pts(), pts(), judge("refuted", False)] * 3
        r = d.cops("c", scripted(rep), 1, b)
        self.assertEqual((r["rounds"], r["stop"], r["verdict"]), (1, "budget", "refuted"))

    def test_jury_agreement_in_round_one(self):
        r = d.jury("c", scripted([v("refuted")] * 3), 1, d.Budget())
        self.assertEqual((r["verdict"], r["rounds"], r["stop"]), ("refuted", 1, "agreement"))

    def test_jury_changes_mind_in_round_two(self):
        r = d.jury("c", scripted([v("refuted"), v("supported"), v("refuted"), v("refuted"), v("refuted"), v("refuted")]), 1, d.Budget())
        self.assertEqual((r["verdict"], r["rounds"], r["stop"]), ("refuted", 2, "agreement"))

    def test_jury_split_is_unclear(self):
        rep = [v("refuted"), v("supported"), v("unclear")] * 3
        r = d.jury("c", scripted(rep), 1, d.Budget())
        self.assertEqual((r["verdict"], r["stop"], r["rounds"]), ("unclear", "cap", 3))

    def test_time_budget(self):
        t = iter([0, 999])
        b = d.Budget(clock=lambda: next(t))
        self.assertFalse(b.left(1))


if __name__ == "__main__":
    unittest.main()
