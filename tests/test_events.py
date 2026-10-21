"""
Tests for the events of a run (events.py, ui/REQUIREMENTS_CORE.md 13d): removal of secrets, the schema of every type, the stream with shared sequence numbers, the context
(actor, parent, threads), the check of a log, and the integration with the pipeline runner, the web log and the chat display. No network, no model.
Run with the MIA virtualenv: python tests/test_events.py
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

import events as E                                       # noqa: E402
import test_pipeline as TP                               # noqa: E402
import web_tools as W                                    # noqa: E402
from pipeline import NodeError, Runner, Tool             # noqa: E402
from run_log import RunLog                               # noqa: E402

EXAMPLES = {
    "plan_made": {"origin": "typed", "template": None, "plan": {"steps": []}, "checks": [{"name": "coverage", "result": "pass"}], "subtasks": 2},
    "router_decision": {"strategy": "decompose", "markers": ["older than"]},
    "query_issued": {"query": "squared squares", "backend": "openalex", "purpose": "history", "subtask": 1},
    "source_found": {"ref": "doi:10.1/a", "title": "A title", "date": "1940", "source_class": "journal", "trust": 0.8, "backend": "crossref", "rank": 1},
    "source_dropped": {"ref": "doi:10.1/b", "stage": "screen", "reason": "after_cutoff", "detail": "published 2011"},
    "page_fetched": {"ref": "https://example.org/p", "hash": "h:abc", "bytes": 1200, "truncated": False, "status": 200},
    "passage_extracted": {"id": "p1", "source": "doi:10.1/a", "quote": "a verbatim quote", "start": 10, "end": 26, "anchor_ok": True, "subtask": 1, "by": "extract"},
    "claim_made": {"id": "c1", "text": "Squares can be wires.", "subtask": 1, "passages": ["p1"], "by": "synthesize"},
    "claim_verified": {"claim": "c1", "verdict": "supported", "style": "single", "passage": "p1", "judge": {"actor": "verify", "model": "gemma4:12b"}, "confidence": 0.8},
    "conflict_found": {"claims": ["c1", "c2"], "rule": "newer_source", "resolution": "newer_source"},
    "slot_opened": {"subtask": 2, "target": "a number with a unit", "why": "no claim yet"},
    "slot_closed": {"subtask": 2, "by_claim": "c3"},
    "draft_sentence": {"text": "Squares are wires.", "claims": ["c1"]},
    "check_run": {"name": "quote_in_page", "target": "p1", "result": "pass"},
    "template_used": {"template": "lp-to-network-flow", "version": "1", "problem_class": "linear_program", "test_passed": True},
    "escalation": {"from": "cheap", "to": "decompose", "trigger": "unsupported answer"},
    "budget_spent": {"name": "calls", "amount": 1, "used": 5, "limit": 150},
    "checkpoint": {"sources_checked": 10, "report_hash": None, "decision": "pending"},
    "stop_decision": {"reason": "budget", "limit": "calls", "detail": "150 calls used"},
    "model_call": {"model": "gemma4:12b", "profile": None, "digest": None, "options": {"num_ctx": 8192}, "prompt_hash": "h:1", "response_hash": "h:2", "prompt_chars": 100,
                   "response_chars": 20, "seconds": 1.5, "tokens_in": None, "tokens_out": None, "schema": "queries", "valid": True, "attempt": 0},
    "user_feedback": {"kind": "thumbs", "value": "up", "note": "good", "claim": "c1"},
    "log_error": {"problem": "something", "original_type": "claim_made"},
}


class Secrets(unittest.TestCase):
    def test_secret_fields_and_text(self):
        data = {"query": "squares", "editor_token": "abc123", "X-MIA-Token": "t0k", "semantic_scholar_key": "k", "password": "p", "mailto": "me@example.org",
                "email": "me@example.org", "tokens_in": 12, "tokens": 5, "nested": {"api_key": "zzz", "keep": "yes"}, "items": [{"authorization": "Bearer abcdef123456"}],
                "text": "write to me@example.org with Bearer abcdefgh12345678 please"}
        out = E.redact(data)
        self.assertEqual(out["query"], "squares")
        for key in ("editor_token", "X-MIA-Token", "semantic_scholar_key", "password", "mailto", "email"):
            self.assertEqual(out[key], E.REDACTED, key)
        self.assertEqual((out["tokens_in"], out["tokens"]), (12, 5))                     # counts of model tokens are not secrets
        self.assertEqual(out["nested"], {"api_key": E.REDACTED, "keep": "yes"})
        self.assertEqual(out["items"][0]["authorization"], E.REDACTED)
        self.assertNotIn("me@example.org", out["text"])
        self.assertNotIn("abcdefgh12345678", out["text"])
        self.assertIn("write to", out["text"])
        self.assertEqual(data["editor_token"], "abc123")                                 # a copy; the original is untouched

    def test_empty_and_non_text_values_stay(self):
        out = E.redact({"token": "", "email": None, "password": False, "key": 1})
        self.assertEqual(out["token"], "")
        self.assertIsNone(out["email"])
        self.assertIs(out["password"], False)

    def test_digest(self):
        self.assertEqual(E.digest("a"), E.digest("a"))
        self.assertNotEqual(E.digest("a"), E.digest("b"))
        self.assertEqual(E.digest({"a": 1, "b": 2}), E.digest({"b": 2, "a": 1}))
        self.assertTrue(E.digest("a").startswith("h:"))


class Schemas(unittest.TestCase):
    def test_every_type_has_an_example_that_fits(self):
        self.assertEqual(set(EXAMPLES), set(E.SCHEMAS))              # a new type needs an example here
        for name, payload in EXAMPLES.items():
            self.assertEqual(E.validate(name, payload), [], name)

    def test_what_does_not_fit(self):
        self.assertTrue(E.validate("nonsense", {}))
        self.assertTrue(E.validate("query_issued", {"query": "x"}))                                           # backend missing
        self.assertTrue(E.validate("query_issued", {"query": "x", "backend": "b", "extra": 1}))               # no free extra fields
        self.assertTrue(E.validate("source_dropped", {**EXAMPLES["source_dropped"], "reason": "because"}))      # reasons are a fixed list
        self.assertTrue(E.validate("claim_verified", {**EXAMPLES["claim_verified"], "confidence": 1.5}))
        self.assertTrue(E.validate("passage_extracted", {**EXAMPLES["passage_extracted"], "anchor_ok": "yes"}))
        self.assertTrue(E.validate("query_issued", "not an object"))

    def test_who_judged_and_how_sure_are_part_of_a_verdict(self):
        base = dict(EXAMPLES["claim_verified"])
        for missing in ("judge", "confidence", "style"):
            broken = {k: v for k, v in base.items() if k != missing}
            self.assertTrue(E.validate("claim_verified", broken), missing)
        self.assertEqual(E.validate("claim_verified", {**base, "confidence": None}), [])             # a judge that gives no figure says so explicitly
        self.assertEqual(E.validate("claim_verified", {**base, "judge": {"actor": "rule:date_check", "model": None}}), [])


class Stream(unittest.TestCase):
    def make(self, **kw):
        sink = []

        class Sink:
            def event(self, event):
                sink.append(event)
        stream = E.EventStream("r-1", sink=Sink(), **kw)
        return stream, sink

    def test_sequence_is_shared_and_secrets_are_removed(self):
        stream, sink = self.make()
        stream.record({"kind": "start", "node": "a", "plain": "token is abc", "payload": {"editor_token": "abc"}})
        stream.emit("query_issued", EXAMPLES["query_issued"], actor="search", plain="asking me@example.org")
        stream.record({"kind": "done", "node": "a", "payload": {}})
        self.assertEqual([e["seq"] for e in sink], [1, 2, 3])
        self.assertEqual({e["run"] for e in sink}, {"r-1"})
        self.assertEqual(sink[0]["payload"]["editor_token"], E.REDACTED)
        self.assertNotIn("me@example.org", sink[1]["plain"])
        self.assertEqual((sink[1]["kind"], sink[1]["type"], sink[1]["actor"], sink[1]["schema"]), ("event", "query_issued", "search", E.ENVELOPE_VERSION))

    def test_a_payload_that_does_not_fit_becomes_a_log_error(self):
        stream, sink = self.make()
        event = stream.emit("query_issued", {"query": "x"})
        self.assertEqual(event["type"], "log_error")
        self.assertEqual(event["payload"]["original_type"], "query_issued")
        self.assertIn("backend", event["payload"]["problem"])
        self.assertEqual(len(stream.problems), 1)
        self.assertEqual(E.check_log(sink), [])                  # the log itself is consistent

    def test_strict_mode_raises(self):
        stream, _ = self.make(strict=True)
        with self.assertRaises(E.EventError):
            stream.emit("query_issued", {"query": "x"})
        with self.assertRaises(E.EventError):
            stream.emit("unknown_type", {})

    def test_the_display_cannot_break_the_run(self):
        def broken(event):
            raise RuntimeError("display")
        stream, sink = self.make(on_event=broken)
        stream.record({"kind": "start"})
        self.assertEqual(len(sink), 1)

    def test_check_log(self):
        stream, sink = self.make()
        stream.record({"kind": "start"})
        stream.emit("check_run", EXAMPLES["check_run"], parent=1)
        self.assertEqual(E.check_log(sink), [])
        self.assertTrue(E.check_log([{"seq": 2, "kind": "start"}, {"seq": 1, "kind": "done"}]))                      # not increasing
        self.assertTrue(E.check_log([{"seq": 1, "kind": "start", "parent": 5}]))                                     # parent from the future
        self.assertTrue(E.check_log([{"seq": 1, "kind": "event", "type": "query_issued", "payload": {}}]))           # does not fit

    def test_the_round_of_a_session_is_inherited(self):
        stream, sink = self.make()
        with E.activate(stream):
            with E.acting("session", round=2):
                inner = E.emit("check_run", EXAMPLES["check_run"])
                with E.acting("expert"):
                    nested = E.emit("check_run", EXAMPLES["check_run"])
                with E.acting("judge", round=3):
                    own = E.emit("check_run", EXAMPLES["check_run"])
            outside = E.emit("check_run", EXAMPLES["check_run"])
        self.assertEqual([e["round"] for e in (inner, nested, own, outside)], [2, 2, 3, None])
        self.assertEqual(stream.emit("check_run", EXAMPLES["check_run"], round=7)["round"], 7)

    def test_no_stream_no_effect(self):
        self.assertIsNone(E.emit("query_issued", EXAMPLES["query_issued"]))
        self.assertEqual(E.current_ids(), {})

    def test_actor_and_parent_come_from_the_context(self):
        stream, sink = self.make()
        with E.activate(stream):
            with E.acting("extract", parent=4):
                event = E.emit("check_run", EXAMPLES["check_run"])
                self.assertEqual(E.current_ids(), {"run": "r-1", "actor": "extract"})
            self.assertEqual(E.current_ids(), {"run": "r-1"})
            outside = E.emit("check_run", EXAMPLES["check_run"])
        self.assertEqual((event["actor"], event["parent"]), ("extract", 4))
        self.assertIsNone(outside["actor"])
        self.assertEqual(E.current_ids(), {})

    def test_model_digests(self):
        class Client:
            def list(self):
                return {"models": [{"model": "gemma4:26b", "digest": "sha256:aaa"}, {"model": "tiny:latest", "digest": "sha256:bbb"}]}

        self.assertEqual(E.model_digests(Client(), ["gemma4:26b", "tiny", "missing:1", None]),
                         [{"name": "gemma4:26b", "digest": "sha256:aaa"}, {"name": "tiny", "digest": "sha256:bbb"}, {"name": "missing:1", "digest": None}])

        class Down:
            def list(self):
                raise ConnectionError("no server")

        self.assertEqual(E.model_digests(Down(), ["m"]), [{"name": "m", "digest": None}])

    def test_environment(self):
        env = E.environment({"editor_token": "secret", "port": 1}, root=REPO, models=[{"name": "m", "digest": "sha256:1"}], versions={"skill": 3})
        self.assertEqual(env["models"], [{"name": "m", "digest": "sha256:1"}])
        self.assertEqual(E.environment({"port": 1})["config_hash"], E.environment({"port": 1})["config_hash"])
        self.assertEqual(E.environment({"port": 1, "editor_token": "a"})["config_hash"], E.environment({"port": 1, "editor_token": "b"})["config_hash"])      # secrets do not change the hash
        self.assertNotEqual(E.environment({"port": 1})["config_hash"], E.environment({"port": 2})["config_hash"])


class InThePipeline(unittest.TestCase):
    def runner(self, model=None, tools=None, log=None, **kw):
        return Runner(model=model, tools=tools, run_log=log, rng=random.Random(1), **kw)

    def run_nodes(self, nodes, model=None, tools=None, log=None, functions=None, **kw):
        events = []
        result = self.runner(model, tools, log, **kw).run(TP.skill(), TP.graph(nodes), {"text": "why?"}, on_event=events.append, functions=functions)
        return result, events

    def test_domain_events_follow_their_node(self):
        def search(query):
            E.emit("query_issued", {"query": query, "backend": "test"})
            return "found " + query
        nodes = [{"id": "plan", "kind": "model", "prompt": "plan", "schema": "queries", "output": "q"},
                 {"id": "search", "kind": "tool", "tool": "search", "args": {"query": "$q.queries.0"}, "output": "out"}]
        result, events = self.run_nodes(nodes, TP.FakeModel([json.dumps({"queries": ["a"]})]), {"search": Tool(search, "search_calls")}, strict_events=True)
        self.assertEqual(result.status, "done")
        self.assertEqual([e["seq"] for e in events], list(range(1, len(events) + 1)))
        self.assertEqual(E.check_log(events), [])
        query = next(e for e in events if e.get("type") == "query_issued")
        start = next(e for e in events if e["kind"] == "start" and e["node"] == "search")
        self.assertEqual((query["actor"], query["parent"], query["node"]), ("search", start["seq"], "search"))
        call = next(e for e in events if e.get("type") == "model_call")
        self.assertEqual((call["actor"], call["payload"]["valid"], call["payload"]["attempt"], call["payload"]["schema"]), ("plan", True, 0, "queries"))
        self.assertTrue(call["payload"]["prompt_hash"].startswith("h:"))
        self.assertEqual({e["run"] for e in events}, {None})                                 # no run log: no run id, still one consistent sequence

    def test_a_retry_is_two_model_calls(self):
        nodes = [{"id": "plan", "kind": "model", "prompt": "plan", "schema": "queries", "output": "out", "retries": 1}]
        _, events = self.run_nodes(nodes, TP.FakeModel(["not json", json.dumps({"queries": ["a"]})]))
        calls = [e["payload"] for e in events if e.get("type") == "model_call"]
        self.assertEqual([(c["attempt"], c["valid"]) for c in calls], [(0, False), (1, True)])
        self.assertNotEqual(calls[0]["prompt_hash"], calls[1]["prompt_hash"])               # the second prompt includes the complaint

    def test_an_event_that_does_not_fit_fails_the_node_when_strict(self):
        def bad(query):
            E.emit("query_issued", {"query": query})
            return "x"
        nodes = [{"id": "search", "kind": "tool", "tool": "search", "args": {"query": "q"}, "output": "out"}]
        result, _ = self.run_nodes(nodes, None, {"search": Tool(bad, "search_calls")}, strict_events=True)
        self.assertEqual(result.status, "error")
        loose, events = self.run_nodes(nodes, None, {"search": Tool(bad, "search_calls")})
        self.assertEqual(loose.status, "done")                                              # in production the run goes on and the problem is in the log
        types = [e["type"] for e in events if e.get("kind") == "event" and e["type"] not in ("budget_spent", "stop_decision")]     # the runner's own events are not the point here
        self.assertEqual(types, ["log_error"])

    def test_threads_of_a_map_keep_run_and_actor(self):
        def work(item):
            E.emit("check_run", {"name": "n", "target": str(item), "result": "pass"})
            return item
        nodes = [{"id": "m", "kind": "map", "over": "$input.items", "as": "x", "workers": 3, "output": "out", "collect": "r",
                  "body": [{"id": "w", "kind": "code", "function": "work", "args": {"item": "$x"}, "output": "r"}]}]
        events = []
        with tempfile.TemporaryDirectory() as folder:
            log = RunLog(folder)
            result = self.runner(log=log, strict_events=True).run(TP.skill(), TP.graph(nodes, result="out"), {"items": [1, 2, 3, 4]}, on_event=events.append, functions={"work": work})
            self.assertEqual(result.status, "done")
            checks = [e for e in events if e.get("type") == "check_run"]
            self.assertEqual(len(checks), 4)
            self.assertEqual({(e["actor"], e["run"]) for e in checks}, {("w", result.run_id)})
            self.assertEqual(E.check_log(log.read()[0]["events"]), [])

    def test_the_environment_is_in_run_start(self):
        _, events = self.run_nodes([{"id": "c", "kind": "code", "function": "f", "output": "out"}], functions={"f": lambda: 1}, environment=lambda: {"commit": "abc", "models": []})
        self.assertEqual(events[0]["payload"]["env"], {"commit": "abc", "models": []})
        _, plain = self.run_nodes([{"id": "c", "kind": "code", "function": "f", "output": "out"}], functions={"f": lambda: 1})
        self.assertNotIn("env", plain[0]["payload"])

    def test_the_web_log_knows_the_run_and_loses_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            web = W.WebLog(folder)

            def fetch(url):
                web.record("fetch", url=url, token="secret-token", note="mail me@example.org")
                return "ok"
            nodes = [{"id": "get", "kind": "tool", "tool": "search", "args": {"url": "https://example.org"}, "output": "out"}]
            log_dir = os.path.join(folder, "runs")
            result = self.runner(tools={"search": Tool(fetch, "search_calls")}, log=RunLog(log_dir)).run(TP.skill(), TP.graph(nodes), {"text": "x"})
            web.record("fetch", url="https://outside.example")
            files = [n for n in os.listdir(folder) if n.startswith("web-")]
            with open(os.path.join(folder, files[0]), encoding="utf-8") as fp:
                lines = [json.loads(line) for line in fp]
        inside, outside = lines
        self.assertEqual((inside["run"], inside["actor"]), (result.run_id, "get"))
        self.assertEqual(inside["token"], E.REDACTED)
        self.assertNotIn("me@example.org", inside["note"])
        self.assertNotIn("run", outside)

    def test_the_chat_block_does_not_get_domain_events(self):
        import chat_service
        shown = []

        class Probe(chat_service.ChatService):
            def __init__(self):
                self._lock = __import__("threading").Lock()
                self._message_id, self._show_pipeline, self._pipeline = "m1", True, []
                self._emit = lambda name, payload: shown.append((name, payload))
        probe = Probe()
        probe.pipeline_event({"kind": "start", "node": "a"})
        probe.pipeline_event({"kind": "event", "type": "query_issued", "payload": {}})
        self.assertEqual([p["event"]["kind"] for _, p in shown], ["start"])
        self.assertEqual(probe._pipeline, [{"kind": "start", "node": "a"}])


if __name__ == "__main__":
    unittest.main()
