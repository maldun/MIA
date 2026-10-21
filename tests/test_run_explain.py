"""
Tests for the tool that explains runs (run_explain.py) and for the offline reproduction of a run (reproduce.py), over complete lookup runs on the recorded web of the research suite.
Run with the MIA virtualenv: python tests/test_run_explain.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

import context_graph as CG                               # noqa: E402
import harness as H                                      # noqa: E402
import reproduce as RP                                   # noqa: E402
import research_chat as RC                               # noqa: E402
import run_explain as RE                                 # noqa: E402
import source_trust                                      # noqa: E402
import test_research as TR                               # noqa: E402
import web_tools                                         # noqa: E402
from content_store import ContentStore                   # noqa: E402
from core import Core                                    # noqa: E402
from library import Library                              # noqa: E402
from pipeline import Tool                                # noqa: E402

WORLD = json.load(open(os.path.join(REPO, "eval", "suites", "research", "web.json"), encoding="utf-8"))
QUESTION = "When did the Rivertown Bridge open to traffic?"
COMPOUND = "When did the Rivertown Bridge open to traffic, and who designed it?"
PLAN = {"subquestions": [{"question": "When did the Rivertown Bridge open to traffic?", "query": "Rivertown Bridge opened traffic"},
                         {"question": "Who designed the Rivertown Bridge?", "query": "Rivertown Bridge designer"}], "needs_calculation": False}


class Lab:
    """a folder with a run log and a store, and the means to make runs and to build a Core"""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runs = os.path.join(self.tmp.name, "runs")
        self.store_dir = os.path.join(self.tmp.name, "store")
        self.store = ContentStore(self.store_dir)

    def close(self):
        self.tmp.cleanup()

    def core(self, model):
        session = H.FixtureWebSession(WORLD)
        tools, _, _ = web_tools.build_web_tools({"search_backends": ["searxng"]}, None, session=session, resolver=lambda host: ["93.184.216.34"], store=self.store,
                                                trust=source_trust.TrustTable.load().for_url)
        return Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), self.runs, model=model, tools={n: Tool(*p) for n, p in tools.items()}, store=self.store)

    def baseline(self, mode="reader", question=QUESTION):
        RC.run_research(self.core(TR.Scripted(mode)), question, pipeline="research.baseline@1")
        return self.last()

    def decomposed(self):
        model = TR.Decompose.Model(PLAN, queries=["Rivertown Bridge architect engineer"], needles={"When did the Rivertown Bridge open to traffic?": "opened to traffic"})
        RC.run_research(self.core(model), COMPOUND, pipeline="research.decompose@1")
        return self.last()

    def last(self):
        return RE.RunLog(self.runs).read()[-1]

    def factory(self):
        """a Core for the reproduction: the same skills and library, no network, a throw-away run log"""
        def make(model, tools):
            scratch = tempfile.mkdtemp(dir=self.tmp.name)
            return Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), scratch, model=model, tools=tools)
        return make


class Tool_(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()
        self.first = self.lab.baseline("reader")
        self.second = self.lab.baseline("invent")
        self.lines = []

    def tearDown(self):
        self.lab.close()

    def run_cli(self, *args, **kwargs):
        self.lines = []
        code = RE.main(["--runs-dir", self.lab.runs, "--store-dir", self.lab.store_dir, *args], out=self.lines.append, **kwargs)
        return code, "\n".join(self.lines)

    def test_find_run(self):
        runs = RE.RunLog(self.lab.runs).read()
        self.assertEqual(RE.find_run(runs, "last")["id"], self.second["id"])
        self.assertEqual(RE.find_run(runs, self.first["id"])["id"], self.first["id"])
        self.assertEqual(RE.find_run(runs, self.first["id"][:-1] + self.first["id"][-1])["id"], self.first["id"])
        with self.assertRaises(RE.ExplainError):
            RE.find_run(runs, "r-0000")
        with self.assertRaises(RE.ExplainError):
            RE.find_run(runs, "r-")                                                    # all runs start like this: not enough
        with self.assertRaises(RE.ExplainError):
            RE.find_run([], "last")

    def test_list(self):
        code, text = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn(self.first["id"], text)
        self.assertIn(self.second["id"], text)
        self.assertIn("When did the Rivertown Bridge open to traffic?", text)
        self.assertEqual(len([l for l in self.lines if l.startswith("r-")]), 2)

    def test_show_gives_the_summary_and_the_view_within_the_budget(self):
        code, text = self.run_cli("show", self.first["id"], "--budget", "400")
        self.assertEqual(code, 0)
        self.assertIn("run %s" % self.first["id"], text)
        self.assertIn("supported", text)
        self.assertIn("ended: sufficient", text)
        self.assertIn("Question: " + QUESTION, text)
        self.assertLessEqual(len(text.split("Question:", 1)[1]), 400 * 4 + 200)
        code, small = self.run_cli("show", "last", "--budget", "40")
        self.assertIn("more lines", small)

    def test_explain_follows_a_sentence_back_to_the_query(self):
        code, text = self.run_cli("explain", self.first["id"])
        self.assertEqual(code, 0)
        for expected in ("draft ", "claim_made", "passage_extracted", "source_found", "query_issued"):
            self.assertIn(expected, text)
        claim = CG.replay_run(self.first).data("claim")[0]["id"]
        code, text = self.run_cli("explain", self.first["id"], claim[:12])
        self.assertIn("[supported]", text)
        code, text = self.run_cli("explain", self.second["id"])
        self.assertIn("[not_found]" if "draft" not in text else "draft", text)           # the run that invented a quote claimed nothing: its claim is explained instead
        code, text = self.run_cli("explain", self.first["id"], "nonsense:node")
        self.assertEqual(code, 2)
        self.assertIn("error:", text)

    def test_cost_problems_and_diff(self):
        code, text = self.run_cli("cost", "last")
        self.assertEqual(code, 0)
        self.assertIn("calls", text)
        code, text = self.run_cli("problems", self.first["id"])
        self.assertEqual((code, text), (0, "0 problem(s)"))
        code, text = self.run_cli("diff", self.first["id"], self.first["id"])
        self.assertEqual((code, text), (0, "the same"))
        code, text = self.run_cli("diff", self.first["id"], self.second["id"])
        self.assertEqual(code, 1)
        self.assertIn("only in the first run: claim", text)                                # the invented answer is another claim ...
        self.assertIn("only in the second run: claim", text)
        self.assertIn("supports only in the first run", text)                              # ... and it is not supported by anything
        self.assertIn("difference(s)", text)

    def test_export_as_dot_and_mermaid(self):
        code, dot = self.run_cli("export", "last", "--format", "dot")
        self.assertTrue(dot.startswith("digraph run {") and dot.rstrip().endswith("}"))
        self.assertIn("shape=box", dot)
        self.assertEqual(dot.count("{"), dot.count("}"))
        code, mermaid = self.run_cli("export", "last", "--format", "mermaid")
        self.assertTrue(mermaid.startswith("flowchart LR"))
        self.assertIn("-->", mermaid)

    def test_call_shows_prompt_and_answer_from_the_store(self):
        seq = next(e["seq"] for e in self.first["events"] if e.get("type") == "model_call")
        code, text = self.run_cli("call", self.first["id"], str(seq))
        self.assertEqual(code, 0)
        self.assertIn("[user]", text)
        self.assertIn("[answer]", text)
        self.assertIn("Rivertown", text)
        code, text = self.run_cli("call", self.first["id"], "1")
        self.assertEqual(code, 2)
        other = ContentStore(os.path.join(self.lab.tmp.name, "empty"))
        lines = []
        self.assertEqual(RE.cmd_call(self.first, lines.append, other, seq), 1)             # texts not in this store
        self.assertIn("not in the store", lines[-1])

    def test_a_run_log_without_runs(self):
        with tempfile.TemporaryDirectory() as folder:
            lines = []
            self.assertEqual(RE.main(["--runs-dir", folder, "--store-dir", folder, "list"], out=lines.append), 0)
            self.assertEqual(lines, ["(no runs)"])
            self.assertEqual(RE.main(["--runs-dir", folder, "--store-dir", folder, "show"], out=lines.append), 2)


class Reproduction(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def test_a_baseline_run_is_reproduced_offline(self):
        record = self.lab.baseline("reader")
        result = RP.reproduce(record, self.lab.store, self.lab.factory())
        self.assertEqual(result["divergences"], [])
        self.assertEqual(result["differences"], [])
        self.assertTrue(result["reproduced"])
        self.assertEqual(result["model_calls"], (1, 1))
        self.assertEqual(result["status"], ("done", "done"))

    def test_a_run_whose_model_invented_a_quote_is_reproduced_with_the_same_failure(self):
        record = self.lab.baseline("invent")
        result = RP.reproduce(record, self.lab.store, self.lab.factory())
        self.assertTrue(result["reproduced"], result)

    def test_a_decomposed_run_with_a_second_search_round_is_reproduced(self):
        record = self.lab.decomposed()
        result = RP.reproduce(record, self.lab.store, self.lab.factory())
        self.assertEqual(result["divergences"], [])
        self.assertEqual(result["differences"], [])
        self.assertTrue(result["reproduced"])
        self.assertGreaterEqual(result["model_calls"][1], 4)
        self.assertEqual(result["model_calls"][0], result["model_calls"][1])

    def test_nothing_leaves_the_machine(self):
        record = self.lab.baseline("reader")
        calls = []
        original = RP.ReplayTools.web_search
        RP.ReplayTools.web_search = lambda self, *a, **k: (calls.append(a), original(self, *a, **k))[1]
        try:
            RP.reproduce(record, self.lab.store, self.lab.factory())
        finally:
            RP.ReplayTools.web_search = original
        self.assertEqual(len(calls), 1)                                                    # only the recording was asked

    def test_a_changed_input_diverges_and_shows_the_difference_of_the_prompts(self):
        record = self.lab.baseline("reader")
        changed = json.loads(json.dumps(record))
        new = "When did the Rivertown Bridge close to traffic?"
        changed["input"]["question"] = new
        for e in changed["events"]:                                                         # the recorded search is for the new question too, so only the prompt differs
            if e.get("type") == "query_issued":
                e["payload"]["query"] = new
            elif e.get("type") == "source_found":
                e["payload"]["query"] = new
        result = RP.reproduce(changed, self.lab.store, self.lab.factory())
        self.assertFalse(result["reproduced"])
        self.assertTrue(result["divergences"])
        first = result["divergences"][0]
        self.assertIn("not one of the recorded prompts", first["what"])
        self.assertIn("close to traffic", first["diff"])                                    # the prompt now differs from the recorded one in the question
        self.assertIn("open to traffic", first["diff"])

    def test_a_search_that_was_not_recorded_is_a_divergence_not_a_request(self):
        record = self.lab.baseline("reader")
        changed = json.loads(json.dumps(record))
        for e in changed["events"]:
            if e.get("type") == "query_issued":
                e["payload"]["query"] = "something else entirely"
        result = RP.reproduce(changed, self.lab.store, self.lab.factory())
        self.assertFalse(result["reproduced"])
        self.assertTrue(any("search that was not recorded" in d["what"] for d in result["divergences"]))

    def test_texts_that_were_not_stored_cannot_be_reproduced_and_it_says_so(self):
        record = self.lab.baseline("reader")
        empty = ContentStore(os.path.join(self.lab.tmp.name, "empty-store"))
        result = RP.reproduce(record, empty, self.lab.factory())
        self.assertFalse(result["reproduced"])
        self.assertTrue(any("not in the store" in d["what"] for d in result["divergences"]))

    def test_the_command_line_reproduces(self):
        record = self.lab.baseline("reader")
        lines = []
        code = RE.main(["--runs-dir", self.lab.runs, "--store-dir", self.lab.store_dir, "reproduce", record["id"]], out=lines.append, core_factory=self.lab.factory())
        self.assertEqual(code, 0)
        self.assertIn("reproduced: the same status, the same graph", lines[-1])
        record = json.loads(json.dumps(record))


if __name__ == "__main__":
    unittest.main()
