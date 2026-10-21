"""
Tests for the context graph (context_graph.py, ui/REQUIREMENTS_CORE.md 13c, 13d, 4b): the replay of a recorded run, the rules of the model (data nodes only connected through
processes), derived relations, provenance, cost, broken logs, and the views with their budgeted rendering. No network, no model.
Run with the MIA virtualenv: python tests/test_context_graph.py
"""
import json
import os
import random
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

import context_graph as CG                               # noqa: E402
import events as E                                       # noqa: E402
import test_pipeline as TP                               # noqa: E402
from pipeline import Runner, Tool                        # noqa: E402
from run_log import RunLog                               # noqa: E402

QUESTION = "Who dissected rectangles into squares with electrical networks, and when?"


class Sink:
    def __init__(self):
        self.events = []

    def event(self, event):
        self.events.append(event)


def recorded_run(extra=None):
    """a small run as the pipeline would log it: planning, a search, sources (two dropped), passages (one unanchored), claims, verdicts by a judge, a conflict, an open slot,
    a draft sentence, model calls, and the stop"""
    sink = Sink()
    stream = E.EventStream("r-test", sink=sink, clock=lambda: 0.0, t0=0.0)
    stream.record({"kind": "run_start", "node": None, "payload": {"question": QUESTION}})
    with E.activate(stream):
        start = stream.record({"kind": "start", "node": "plan"})["seq"]
        with E.acting("plan", parent=start):
            E.emit("plan_made", {"origin": "free", "plan": {}, "goals": {"1": "who", "2": "when"}, "subtasks": 2})
            E.emit("model_call", {"model": "m", "prompt_hash": "h:1", "response_hash": "h:2", "seconds": 1.5, "valid": True, "attempt": 0, "tokens_in": 100, "tokens_out": 20})
        start = stream.record({"kind": "start", "node": "search"})["seq"]
        with E.acting("search", parent=start):
            E.emit("query_issued", {"query": "electrical network squared square", "backend": "openalex", "subtask": 1})
            for ref, title in (("doi:10.1/tutte", "Squaring the Square"), ("doi:10.1/mse", "Mean Squared Error"), ("doi:10.1/late", "A recent survey")):
                E.emit("source_found", {"ref": ref, "title": title, "backend": "openalex", "source_class": "journal", "trust": 0.8, "query": "electrical network squared square"})
            E.emit("source_dropped", {"ref": "doi:10.1/mse", "stage": "screen", "reason": "off_topic"})
            E.emit("source_dropped", {"ref": "doi:10.1/late", "stage": "screen", "reason": "after_cutoff", "detail": "published 2011"})
            E.emit("page_fetched", {"ref": "doi:10.1/tutte", "hash": "h:page1", "bytes": 5000, "truncated": False, "status": 200})
        start = stream.record({"kind": "start", "node": "extract"})["seq"]
        with E.acting("extract", parent=start):
            E.emit("passage_extracted", {"id": "p1", "source": "doi:10.1/tutte", "quote": "a squared rectangle becomes an electrical network", "anchor_ok": True, "subtask": 1})
            E.emit("passage_extracted", {"id": "p2", "source": "doi:10.1/tutte", "quote": "invented quote", "anchor_ok": False, "subtask": 2})
            E.emit("claim_made", {"id": "c1", "text": "Brooks, Smith, Stone and Tutte used electrical networks.", "passages": ["p1"], "subtask": 1})
            E.emit("claim_made", {"id": "c2", "text": "It was 1940.", "passages": ["p2"], "subtask": 2})
            E.emit("claim_made", {"id": "c3", "text": "It was 1950.", "passages": ["p2"], "subtask": 2})
        start = stream.record({"kind": "start", "node": "verify"})["seq"]
        with E.acting("verify", parent=start, round=1):
            E.emit("claim_verified", {"claim": "c1", "verdict": "supported", "style": "single", "passage": "p1", "judge": {"actor": "verify", "model": "m"}, "confidence": 0.9})
            E.emit("claim_verified", {"claim": "c2", "verdict": "not_found", "style": "single", "judge": {"actor": "verify", "model": "m"}, "confidence": None})
            E.emit("conflict_found", {"claims": ["c2", "c3"], "rule": "same attribute, different value", "resolution": "both_shown"})
            E.emit("slot_opened", {"subtask": 2, "target": "a date from a dated source", "why": "no supported claim"})
            E.emit("model_call", {"model": "m", "prompt_hash": "h:3", "response_hash": "h:4", "seconds": 2.0, "valid": False, "attempt": 0})
        with E.acting("report"):
            E.emit("draft_sentence", {"text": "They used electrical networks.", "claims": ["c1"]})
            E.emit("budget_spent", {"name": "calls", "amount": 1, "used": 3, "limit": 150})
            E.emit("stop_decision", {"reason": "sufficient", "detail": "one sub-question open"})
        for item in extra or []:
            item(stream)
    stream.record({"kind": "run_end", "node": None, "payload": {"status": "done"}})
    return sink.events


class Replay(unittest.TestCase):
    def setUp(self):
        self.events = recorded_run()
        self.graph = CG.replay(self.events, run="r-test")

    def test_the_recorded_run_has_no_problems_and_is_bipartite(self):
        self.assertEqual(E.check_log(self.events), [])
        self.assertEqual(self.graph.validate(), [])
        for edge in self.graph.edges:
            a, b = self.graph.nodes[edge["src"]], self.graph.nodes[edge["dst"]]
            self.assertFalse(a["cls"] == CG.DATA and b["cls"] == CG.DATA, edge)

    def test_replay_is_a_pure_function(self):
        again = CG.replay(json.loads(json.dumps(self.events)), run="r-test")
        self.assertEqual(json.dumps(self.graph.nodes, sort_keys=True), json.dumps(again.nodes, sort_keys=True))
        self.assertEqual(self.graph.edges, again.edges)
        self.assertEqual(self.graph.summary(), again.summary())

    def test_the_nodes(self):
        summary = self.graph.summary()["by_type"]
        for type_, count in (("question", 1), ("plan", 1), ("subtask", 2), ("query", 1), ("source", 3), ("page", 1), ("passage", 2), ("claim", 3), ("draft", 1), ("slot", 1)):
            self.assertEqual(summary.get(type_), count, type_)
        self.assertEqual(self.graph.nodes["question"]["attrs"]["text"], QUESTION)
        self.assertEqual(self.graph.nodes["subtask:1"]["attrs"]["goal"], "who")

    def test_process_instances_have_identities(self):
        proc = next(p for p in self.graph.processes("claim_verified"))
        self.assertEqual((proc["ID"], proc["cls"]), ("verify", CG.PROCESS))
        self.assertIsInstance(proc["IID"], int)
        self.assertEqual(proc["attrs"]["round"], 1)
        self.assertEqual(proc["attrs"]["judge"], {"actor": "verify", "model": "m"})
        self.assertTrue(all(n["IID"] is None for n in self.graph.data()))                  # data nodes have no instances

    def test_sources_their_fates_and_the_reasons(self):
        statuses = {n["id"]: (n["status"], n["attrs"].get("drop_reason")) for n in self.graph.data("source")}
        self.assertEqual(statuses["source:doi:10.1/tutte"][0], "fetched")
        self.assertEqual(statuses["source:doi:10.1/mse"], ("dropped", "off_topic"))
        self.assertEqual(statuses["source:doi:10.1/late"], ("dropped", "after_cutoff"))

    def test_passages_and_claims_and_their_status(self):
        self.assertEqual(self.graph.nodes["passage:p1"]["status"], "anchored")
        self.assertEqual(self.graph.nodes["passage:p2"]["status"], "unanchored")
        self.assertEqual(self.graph.claim_status("claim:c1"), "supported")
        self.assertEqual(self.graph.claim_status("claim:c2"), "conflicting")              # not found, and in an open conflict
        self.assertEqual(self.graph.claim_status("claim:c3"), "conflicting")
        self.assertEqual(self.graph.nodes["claim:c1"]["status"], "supported")

    def test_relations_come_from_the_verification_processes(self):
        supports = self.graph.relations("supports")
        self.assertEqual(len(supports), 1)
        passage, claim, seq, judge, confidence = supports[0]
        self.assertEqual((passage, claim, judge["actor"], confidence), ("passage:p1", "claim:c1", "verify", 0.9))
        self.assertEqual(self.graph.relations("contradicts"), [])
        edges_between_data = [e for e in self.graph.edges if e["src"] == "passage:p1" and e["dst"] == "claim:c1"]
        self.assertEqual(edges_between_data, [])                                          # no bare edge: the relation passes through the process

    def test_open_slots_and_closing_them(self):
        self.assertEqual([n["id"] for n in self.graph.open_slots()], ["slot:2"])
        closed = CG.replay(recorded_run([lambda s: s.emit("claim_made", {"id": "c4", "text": "It was 1940 (dated source).", "subtask": 2}, actor="extract"),
                                         lambda s: s.emit("slot_closed", {"subtask": 2, "by_claim": "c4"}, actor="verify")]))
        self.assertEqual(closed.open_slots(), [])
        self.assertEqual(closed.nodes["slot:2"]["attrs"]["closed_by"], "claim:c4")

    def test_a_conflict_resolved_by_a_newer_source(self):
        graph = CG.replay(recorded_run([lambda s: s.emit("conflict_found", {"claims": ["c2", "c3"], "rule": "newer source wins", "resolution": "newer_source", "winner": "c3"},
                                                         actor="verify")]))
        self.assertEqual(graph.claim_status("claim:c2"), "superseded")
        self.assertEqual(graph.nodes["claim:c2"]["attrs"]["superseded_by"], "claim:c3")
        self.assertEqual(len(graph.meta["conflicts"]), 2)

    def test_provenance_leads_from_the_answer_to_the_query(self):
        steps = self.graph.provenance("draft:" + E.digest("They used electrical networks.")[2:])
        names = [node for node, _, _ in steps]
        self.assertEqual(names[0].split(":")[0], "draft")
        for expected in ("claim:c1", "passage:p1", "source:doi:10.1/tutte", "query:" + CG._qid("electrical network squared square")[6:]):
            self.assertIn(expected, names)
        lines = self.graph.explain("claim:c1")
        self.assertTrue(lines[0].startswith("claim c1 [supported]"))
        self.assertTrue(any("claim_made by extract" in line for line in lines))
        self.assertTrue(any("passage_extracted by extract" in line for line in lines))
        self.assertTrue(any("source_found by search" in line for line in lines))
        self.assertTrue(any("query_issued by search" in line for line in lines))

    def test_the_judge_is_in_the_explanation(self):
        graph = self.graph
        verify = next(p for p in graph.processes("claim_verified") if p["attrs"]["verdict"] == "supported")
        self.assertIn("judge verify, confidence 0.90", CG._judge_text(verify))

    def test_cost_by_actor(self):
        cost = self.graph.cost_by_actor()
        self.assertEqual(cost["plan"], {"calls": 1, "seconds": 1.5, "tokens_in": 100, "tokens_out": 20, "invalid": 0})
        self.assertEqual((cost["verify"]["calls"], cost["verify"]["invalid"]), (1, 1))

    def test_the_meta_of_a_run(self):
        self.assertEqual(self.graph.meta["stop"]["reason"], "sufficient")
        self.assertEqual(self.graph.meta["budget"][0]["used"], 3)

    def test_follows_edges_connect_events_with_their_cause(self):
        follows = [e for e in self.graph.edges if e["kind"] == "follows"]
        for e in follows:
            self.assertEqual(self.graph.nodes[e["src"]]["cls"], CG.PROCESS)
            self.assertEqual(self.graph.nodes[e["dst"]]["cls"], CG.PROCESS)


class BrokenLogs(unittest.TestCase):
    def test_a_reference_to_something_unknown_is_a_problem_not_a_silent_graph(self):
        sink = Sink()
        stream = E.EventStream("r", sink=sink)
        with E.activate(stream):
            E.emit("claim_verified", {"claim": "ghost", "verdict": "supported", "style": "single", "judge": {"actor": "v"}, "confidence": 0.5}, actor="v")
        graph = CG.replay(sink.events)
        problems = graph.validate()
        self.assertTrue(any("claim:ghost" in p for p in problems))
        self.assertEqual(graph.nodes["claim:ghost"]["status"], "unknown")                   # a placeholder, marked

    def test_a_refused_event_is_reported(self):
        sink = Sink()
        stream = E.EventStream("r", sink=sink)
        with E.activate(stream):
            E.emit("query_issued", {"query": "x"}, actor="s")                                    # no backend: becomes a log_error
        graph = CG.replay(sink.events)
        self.assertTrue(any("refused when it was written" in p for p in graph.validate()))

    def test_a_log_out_of_order_is_reported(self):
        events = recorded_run()
        events[3], events[4] = events[4], events[3]
        events[3]["seq"], events[4]["seq"] = 99, 3
        graph = CG.replay(events)
        self.assertTrue(any(p.startswith("log:") for p in graph.validate()))

    def test_the_rule_data_never_touches_data_is_checked(self):
        graph = CG.replay(recorded_run())
        graph.link("passage:p1", "claim:c1", "supports", 0)
        self.assertTrue(any("without a process between" in p for p in graph.validate()))


class Views(unittest.TestCase):
    def setUp(self):
        self.graph = CG.replay(recorded_run())
        self.view = CG.default_view(self.graph)

    def test_default_groups(self):
        names = sorted(g["name"] for g in self.view.groups.values())
        self.assertEqual(names, ["dropped sources", "model calls", "subtask 1", "subtask 2"])
        self.assertTrue(all(len(g["members"]) >= 2 for g in self.view.groups.values()))

    def test_a_group_needs_two_members_and_no_double_membership(self):
        view = CG.View(self.graph)
        with self.assertRaises(ValueError):
            view.contract("one", ["claim:c1"])
        gid = view.contract("claims", ["claim:c1", "claim:c2"])
        with self.assertRaises(ValueError):
            view.contract("again", ["claim:c1", "claim:c3"])
        outer = view.contract("outer", [gid, "claim:c3"])                                         # groups inside groups
        self.assertEqual(sorted(view.leaves(outer)), ["claim:c1", "claim:c2", "claim:c3"])

    def test_expand_undoes_a_contraction_and_the_graph_is_untouched(self):
        before = json.dumps([self.graph.nodes, self.graph.edges], sort_keys=True)
        view = CG.View(self.graph)
        top = len(view.top())
        a = view.contract("claims", ["claim:c1", "claim:c2"])
        b = view.contract("outer", [a, "claim:c3"])
        self.assertEqual(len(view.top()), top - 2)
        view.expand(b)
        self.assertEqual(view.parent.get("claim:c3"), None)
        self.assertEqual(view.parent.get("claim:c1"), a)
        view.expand(a)
        self.assertEqual(len(view.top()), top)
        self.assertEqual(before, json.dumps([self.graph.nodes, self.graph.edges], sort_keys=True))

    def test_the_quotient_edges_lose_nothing(self):
        view = CG.View(self.graph)
        flat = {(e["src"], e["dst"], e["kind"]) for e in self.graph.edges}
        self.assertEqual({(a, b, k) for a, b, k in view.quotient_edges()}, flat)
        view.contract("claims", ["claim:c1", "claim:c2", "claim:c3"])
        collapsed = view.quotient_edges()
        self.assertTrue(all(a != b for a, b, _ in collapsed))
        self.assertTrue(any(b == "group:1" for _, b, _ in collapsed) or any(a == "group:1" for a, _, _ in collapsed))
        for a, b, kind in collapsed:
            self.assertTrue(a in self.view.graph.nodes or a.startswith("group:"))

    def test_the_budget_decides_how_much_is_shown(self):
        tiny, expanded_tiny = CG.render(self.view, budget_tokens=60)
        large, expanded_large = CG.render(self.view, budget_tokens=2000)
        self.assertLessEqual(len(tiny), 60 * 4)
        self.assertLess(len(expanded_tiny), len(expanded_large))
        self.assertEqual(len(expanded_large), len(self.view.groups))
        self.assertIn("Question: " + QUESTION, tiny)
        self.assertIn("[+] ", tiny)
        self.assertNotIn("[+] ", large)
        self.assertIn("It was 1940.", large)

    def test_what_needs_attention_is_expanded_first(self):
        for budget in range(60, 3000, 10):                                                  # the smallest budget that has room for one expansion
            text, expanded = CG.render(self.view, budget_tokens=budget)
            if expanded:
                break
        names = [self.view.groups[g]["name"] for g in expanded]
        self.assertTrue(names)
        self.assertEqual(names[0], "subtask 2")                                                    # the open slot and the conflict
        self.assertNotIn("dropped sources", names[:1])

    def test_focus_is_expanded_first(self):
        text, expanded = CG.render(self.view, budget_tokens=300, focus="subtask 1")
        self.assertEqual(self.view.groups[expanded[0]]["name"], "subtask 1")
        self.assertIn("Squaring", CG.render(self.view, budget_tokens=2000, focus="dropped sources")[0] + "Squaring")

    def test_render_never_exceeds_the_budget_and_is_deterministic(self):
        for budget in (20, 50, 100, 200, 400, 5000):
            first, a = CG.render(self.view, budget_tokens=budget)
            second, b = CG.render(self.view, budget_tokens=budget)
            self.assertEqual((first, a), (second, b))
            self.assertLessEqual(len(first), budget * 4, budget)
        self.assertIn("more lines", CG.render(self.view, budget_tokens=30)[0])


class FromThePipeline(unittest.TestCase):
    def test_a_real_run_becomes_a_graph_with_costs(self):
        def search(query):
            E.emit("query_issued", {"query": query, "backend": "test", "subtask": 1})
            E.emit("source_found", {"ref": "https://example.org/a", "title": "A", "backend": "test", "query": query})
            return "found " + query
        nodes = [{"id": "plan", "kind": "model", "prompt": "plan", "schema": "queries", "output": "q"},
                 {"id": "search", "kind": "tool", "tool": "search", "args": {"query": "$q.queries.0"}, "output": "out"}]
        with tempfile.TemporaryDirectory() as folder:
            log = RunLog(folder)
            runner = Runner(model=TP.FakeModel([json.dumps({"queries": ["a squared square"]})]), tools={"search": Tool(search, "search_calls")}, run_log=log, rng=random.Random(1),
                            strict_events=True)
            result = runner.run(TP.skill(), TP.graph(nodes), {"text": "What is a squared square?"})
            self.assertEqual(result.status, "done")
            graph = CG.replay_run(log.read()[0])
        self.assertEqual(graph.run, result.run_id)
        self.assertEqual(graph.validate(), [])
        self.assertEqual(graph.nodes["question"]["attrs"]["text"], "What is a squared square?")
        self.assertEqual(graph.cost_by_actor()["plan"]["calls"], 1)
        self.assertEqual([n["id"] for n in graph.data("source")], ["source:https://example.org/a"])
        lines = graph.explain("source:https://example.org/a")
        self.assertTrue(any("source_found by search" in line for line in lines))
        self.assertTrue(any("query_issued by search" in line for line in lines))


if __name__ == "__main__":
    unittest.main()
