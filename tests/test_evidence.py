"""
Tests for the evidence events (evidence.py, ui/REQUIREMENTS_CORE.md 13d step 4): complete lookup runs over the recorded web of the research suite, with strict events, then replayed
into the context graph. The graph of a real run must be consistent: every reference of an event meets a node that an earlier event made. Run with the MIA virtualenv:
python tests/test_evidence.py
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
import events as E                                       # noqa: E402
import evidence as EV                                    # noqa: E402
import harness as H                                      # noqa: E402
import research_chat as RC                               # noqa: E402
import source_trust                                      # noqa: E402
import test_research as TR                               # noqa: E402
import web_tools                                         # noqa: E402
from content_store import ContentStore                   # noqa: E402
from core import Core                                    # noqa: E402
from library import Library                              # noqa: E402
from pipeline import Tool                                # noqa: E402

WORLD = json.load(open(os.path.join(REPO, "eval", "suites", "research", "web.json"), encoding="utf-8"))
QUESTION = "When did the Rivertown Bridge open to traffic?"


class RealRuns(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ContentStore(os.path.join(self.tmp.name, "store"))

    def tearDown(self):
        self.tmp.cleanup()

    def core(self, model):
        session = H.FixtureWebSession(WORLD)
        tools, _, _ = web_tools.build_web_tools({"search_backends": ["searxng"]}, None, session=session, resolver=lambda host: ["93.184.216.34"],
                                                store=self.store, trust=source_trust.TrustTable.load().for_url)
        core = Core(os.path.join(REPO, "skills"), Library(os.path.join(REPO, "library")), os.path.join(self.tmp.name, "runs"), model=model,
                    tools={name: Tool(*pair) for name, pair in tools.items()}, store=self.store)
        core.runner.strict_events = True                      # an event that does not fit its schema fails the node
        return core

    def graph_of(self, core):
        record = core.run_log.read()[-1]
        self.assertEqual(E.check_log(record["events"]), [])
        return CG.replay_run(record), record

    def test_a_baseline_lookup_leaves_a_consistent_graph(self):
        core = self.core(TR.Scripted("reader"))
        text = RC.run_research(core, QUESTION, pipeline="research.baseline@1")
        self.assertIn("3 May 2021", text)
        graph, record = self.graph_of(core)
        self.assertEqual(graph.validate(), [])                                                  # every reference meets a node an earlier event made
        types = {n["type"] for n in graph.nodes.values()}
        for expected in ("question", "query", "source", "page", "passage", "claim", "draft", "search_calls") if False else ("question", "query", "source", "page", "passage", "claim", "draft"):
            self.assertIn(expected, types, expected)
        self.assertEqual(graph.nodes["question"]["attrs"]["text"], QUESTION)

    def test_the_sources_of_the_answer_are_reported_with_their_trust(self):
        """REQ-CHA-016: the chat keeps the sources behind a lookup answer with their trust, to tell a fact (a reputable source) from an opinion"""
        core, seen = self.core(TR.Scripted("reader")), []
        text = RC.run_research(core, QUESTION, pipeline="research.baseline@1", on_sources=seen.append, trust=source_trust.TrustTable.load().for_url)
        self.assertIn("3 May 2021", text)
        self.assertEqual(len(seen), 1)
        self.assertTrue(seen[0])
        self.assertTrue(all(s["url"].startswith("http") and 0 <= s["trust"] <= 1 for s in seen[0]))
        self.assertEqual([s["url"] for s in seen[0]], [s["url"] for s in core.run("research", {"question": QUESTION}, pipeline="research.baseline@1").answer["sources"]])

    def test_sources_pages_and_trust(self):
        core = self.core(TR.Scripted("reader"))
        RC.run_research(core, QUESTION, pipeline="research.baseline@1")
        graph, _ = self.graph_of(core)
        sources = graph.data("source")
        self.assertTrue(sources)
        fetched = [s for s in sources if s["status"] == "fetched"]
        self.assertTrue(fetched)
        self.assertTrue(all(s["attrs"].get("source_class") for s in sources))                     # classified by the trust table
        self.assertTrue(all(s["attrs"].get("rank") for s in sources))
        for page in graph.data("page"):
            text = self.store.get(page["id"][len("page:"):])
            self.assertTrue(text and len(text) > 50)                                              # the page text is in the store under the hash of the event
        dropped = [s for s in sources if s["status"] == "dropped"]
        self.assertTrue(all(s["attrs"]["drop_reason"] in ("not_selected", "duplicate", "fetch_failed") for s in dropped))

    def test_the_answer_leads_back_to_the_query(self):
        core = self.core(TR.Scripted("reader"))
        RC.run_research(core, QUESTION, pipeline="research.baseline@1")
        graph, _ = self.graph_of(core)
        claims = graph.data("claim")
        self.assertEqual(len(claims), 1)
        self.assertEqual(graph.claim_status(claims[0]["id"]), "supported")
        supports = graph.relations("supports")
        self.assertEqual(len(supports), 1)
        self.assertEqual((supports[0][3]["actor"], supports[0][4]), ("rule:anchor_answer", None))
        draft = graph.data("draft")[0]["id"]
        lines = graph.explain(draft)
        self.assertTrue(any("claim_made" in line for line in lines))
        self.assertTrue(any("passage_extracted" in line for line in lines))
        self.assertTrue(any("source_found" in line for line in lines))
        self.assertTrue(any("query_issued" in line for line in lines))

    def test_a_model_that_invents_a_quote_leaves_a_failed_check_and_an_unsupported_claim(self):
        core = self.core(TR.Scripted("invent"))
        text = RC.run_research(core, QUESTION, pipeline="research.baseline@1")
        self.assertIn(RC.NO_ANSWER, text)
        graph, record = self.graph_of(core)
        self.assertEqual(graph.validate(), [])
        claims = graph.data("claim")
        self.assertEqual(len(claims), 1)
        self.assertEqual(graph.claim_status(claims[0]["id"]), "not_found")
        failed = [p for p in graph.processes("check_run") if p["attrs"].get("name") == "quote_in_source" and p["attrs"].get("result") == "fail"]
        self.assertTrue(failed)
        self.assertEqual(graph.data("draft"), [])                                                 # nothing was stated

    def test_the_model_that_says_unknown_claims_nothing(self):
        core = self.core(TR.Scripted("unknown"))
        RC.run_research(core, "Who designed the Rivertown Bridge?", pipeline="research.baseline@1")
        graph, _ = self.graph_of(core)
        self.assertEqual(graph.validate(), [])
        self.assertEqual(graph.data("claim"), [])

    def test_the_generic_events_of_the_runner(self):
        core = self.core(TR.Scripted("reader"))
        RC.run_research(core, QUESTION, pipeline="research.baseline@1")
        graph, record = self.graph_of(core)
        self.assertEqual(graph.meta["stop"]["reason"], "sufficient")
        budget = {b["name"] for b in graph.meta["budget"]}
        self.assertTrue({"search_calls", "fetch_calls"} <= budget)
        calls = graph.cost_by_actor()
        self.assertTrue(calls)                                                                    # the model call of the node that wrote the answer
        self.assertTrue(all(row["calls"] >= 1 for row in calls.values()))

    def test_a_decomposed_lookup_has_a_plan_subtasks_and_slots(self):
        plan = {"subquestions": [{"question": "When did the Rivertown Bridge open to traffic?", "query": "Rivertown Bridge opened traffic"},
                                 {"question": "Who designed the Rivertown Bridge?", "query": "Rivertown Bridge designer"}], "needs_calculation": False}
        model = TR.Decompose.Model(plan, queries=["Rivertown Bridge architect engineer"], needles={"When did the Rivertown Bridge open to traffic?": "opened to traffic"})
        core = self.core(model)
        RC.run_research(core, "When did the Rivertown Bridge open to traffic, and who designed it?", pipeline="research.decompose@1")
        graph, record = self.graph_of(core)
        self.assertEqual(graph.validate(), [])
        plans = graph.data("plan")
        self.assertTrue(plans)
        self.assertEqual(plans[0]["attrs"]["origin"], "free")
        goals = {n["id"]: n["attrs"]["goal"] for n in graph.data("subtask") if "goal" in n["attrs"]}
        self.assertEqual(len(goals), 2)
        self.assertTrue(any(p["attrs"].get("subtask") == 1 for p in graph.processes()))        # the work of the first sub-question carries its number
        decisions = [p["attrs"].get("strategy") for p in graph.processes("router_decision")]
        self.assertTrue(decisions)                                                                # the branches took their way and said so
        self.assertEqual([n["id"] for n in graph.open_slots()], ["slot:2"])                       # the designer was not found: an open slot, named after the sub-question
        self.assertEqual(graph.nodes["slot:2"]["attrs"]["target"], "Who designed the Rivertown Bridge?")
        supported = [c for c in graph.data("claim") if graph.claim_status(c["id"]) == "supported"]
        self.assertTrue(supported)

    def test_outside_a_run_the_helpers_do_nothing(self):
        self.assertIsNone(EV.search_done("x", {"results": []}))
        self.assertIsNone(EV.answer_checked({}, {"status": "unknown", "sources": []}, []))
        self.assertIsNone(E.emit("query_issued", {"query": "x", "backend": "b"}))
        # and the research functions work as before
        import research
        self.assertEqual(research.top_urls({"results": [{"url": "https://a.example/1"}, {"url": "https://a.example/2"}]}, n=1), ["https://a.example/1"])

    def test_passage_and_claim_names_are_stable(self):
        self.assertEqual(EV.passage_id("https://a", "text"), EV.passage_id("https://a", "text"))
        self.assertNotEqual(EV.passage_id("https://a", "text"), EV.passage_id("https://b", "text"))
        self.assertEqual(EV.claim_id("It was 1940."), EV.claim_id("It was 1940."))


if __name__ == "__main__":
    unittest.main()
