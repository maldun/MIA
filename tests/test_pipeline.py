"""
Tests for the core: schema checker, skill files, run log, pipeline runner (all node kinds, budgets, stop, retries, events) and the Core facade with the
shipped chat skill. The model is a fake. Run with the MIA virtualenv: python tests/test_pipeline.py
"""
import json
import os
import random
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import schema_check                                   # noqa: E402
from core import Core                                 # noqa: E402
from pipeline import (BudgetExceeded, PipelineError, Runner, Tool, lookup, render, resolve, test_condition,  # noqa: E402
                      validate_pipeline)
from pipeline_model import OllamaModel                # noqa: E402
from run_log import RunLog                            # noqa: E402
from skill_store import SkillError, SkillStore, parse_skill   # noqa: E402

SKILL = """---
name: demo
version: 3
description: a demo skill
tools: [search]
budget: {steps: 30, seconds: 60, search_calls: 2}
model: {profile: full}
pipeline: demo
---
## prompts
### system
You are careful.
### plan
Question: {{input.text}}
Make queries.
### rate
Rate {{item}}.
## schemas
### queries
```json
{"type": "object", "required": ["queries"], "properties": {"queries": {"type": "array", "minItems": 1, "maxItems": 3, "items": {"type": "string"}}}}
```
### score
```json
{"type": "object", "required": ["score"], "properties": {"score": {"type": "integer", "minimum": 0, "maximum": 10}}}
```
## lines
### search
- Rummaging…
### model
- Pondering…
## examples
### plan
{"queries": ["{{input.text}}"]}
"""


class FakeModel:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def chat(self, messages, schema=None, model=None, profile=None, options=None):
        self.calls.append({"messages": messages, "schema": schema, "profile": profile})
        reply = self.replies.pop(0)
        return reply(messages) if callable(reply) else reply


def skill(**changes):
    parsed = parse_skill(SKILL, "demo.md")
    parsed.update(changes)
    return parsed


def graph(nodes, result="out"):
    return {"name": "demo", "version": 1, "result": result, "nodes": nodes}


class SchemaTests(unittest.TestCase):
    def test_fits_and_problems(self):
        schema = {"type": "object", "required": ["a"], "additionalProperties": False,
                  "properties": {"a": {"type": "integer", "minimum": 1}, "b": {"type": "array", "items": {"enum": ["x", "y"]}, "maxItems": 2}}}
        self.assertEqual(schema_check.check({"a": 2, "b": ["x"]}, schema), [])
        problems = schema_check.check({"a": 0, "b": ["z", "x", "y"], "c": 1}, schema)
        self.assertEqual(len(problems), 4)
        self.assertTrue(schema_check.check({}, schema)[0].endswith("missing 'a'"))
        self.assertTrue(schema_check.check({"a": True}, schema))        # a boolean is not an integer
        self.assertTrue(schema_check.check("x", schema))


class SkillTests(unittest.TestCase):
    def test_parsing(self):
        s = skill()
        self.assertEqual((s["name"], s["version"], s["pipeline"], s["tools"]), ("demo", 3, "demo", ["search"]))
        self.assertEqual(s["budget"]["search_calls"], 2)
        self.assertEqual(s["budget"]["steps"], 30)
        self.assertIn("Make queries", s["prompts"]["plan"])
        self.assertEqual(s["schemas"]["score"]["properties"]["score"]["maximum"], 10)
        self.assertEqual(s["lines"]["search"], ["Rummaging…"])
        self.assertTrue(s["status_block"])

    def test_broken_files(self):
        for text in ("no front matter", "---\nname: x\n---\n", "---\nname: Bad Name\npipeline: p\n---\n", "---\n: : :\n---\n",
                     "---\nname: x\npipeline: p\n---\n## schemas\n### s\nnot a block\n",
                     "---\nname: x\npipeline: p\n---\n## schemas\n### s\n```json\n{oops\n```\n"):
            with self.assertRaises(SkillError, msg=text):
                parse_skill(text, "x.md")

    def test_store_loads_reloads_and_survives_broken_files(self):
        with tempfile.TemporaryDirectory() as folder:
            good, bad = os.path.join(folder, "demo.md"), os.path.join(folder, "bad.md")
            with open(good, "w") as fp:
                fp.write(SKILL)
            with open(bad, "w") as fp:
                fp.write("broken")
            store = SkillStore(folder)
            self.assertEqual(store.names(), ["demo"])
            self.assertIn(bad, store.errors)
            with open(good, "w") as fp:
                fp.write(SKILL.replace("version: 3", "version: 4"))
            os.utime(good, ns=(10**18, 10**18 + 5))
            self.assertEqual(store.get("demo")["version"], 4)
            os.remove(good)
            self.assertIsNone(store.get("demo"))


class RunLogTests(unittest.TestCase):
    def test_runs_and_feedback(self):
        with tempfile.TemporaryDirectory() as folder:
            log = RunLog(folder)
            run = log.start("chat", "chat", 1, "chat", 1, "m", {"text": "x" * 30000})
            run.event({"kind": "start"})
            run.finish("done", {"answer": "hi"}, 1.2345)
            log.add_feedback(run.id, "thumb", "up", "nice")
            log.start("chat", input={"text": "unfinished"})            # never finished: not in the file
            with open(log._file(), "a") as fp:
                fp.write("{half a line")
            runs = log.read()
            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0]["id"], run.id)
            self.assertAlmostEqual(runs[0]["seconds"], 1.2345, places=2)
            self.assertLess(len(runs[0]["input"]["text"]), 20100)
            self.assertEqual(runs[0]["feedback"][0]["value"], "up")
            self.assertEqual(runs[0]["events"], [{"kind": "start"}])
            self.assertEqual(log.read(limit=0)[0]["id"], run.id)


class HelperTests(unittest.TestCase):
    def test_lookup_resolve_render(self):
        ctx = {"input": {"text": "hello"}, "items": [{"a": 1}, {"a": 2}], "n": 3}
        self.assertEqual(lookup("items.1.a", ctx), 2)
        self.assertEqual(lookup("items.-1.a", ctx), 2)
        self.assertEqual(resolve({"x": "$input.text", "y": ["$n", "plain", 5]}, ctx), {"x": "hello", "y": [3, "plain", 5]})
        self.assertEqual(render("Q: {{ input.text }} / {{items}}", ctx), 'Q: hello / [{"a": 1}, {"a": 2}]')
        self.assertEqual(render("{{nothing}}", ctx, strict=False), "{{nothing}}")
        with self.assertRaises(Exception):
            render("{{nothing}}", ctx)
        with self.assertRaises(Exception):
            resolve("$nothing", ctx)

    def test_conditions(self):
        ctx = {"v": "yes", "n": 3, "l": [], "xs": [1, 2]}
        cases = [({"ref": "v", "op": "==", "value": "yes"}, True), ({"ref": "n", "op": ">", "value": 5}, False),
                 ({"ref": "l", "op": "empty"}, True), ({"ref": "xs", "op": "not_empty"}, True), ({"ref": "n", "op": "in", "value": [1, 3]}, True),
                 ({"ref": "missing", "op": "empty"}, True), ({"ref": "v", "op": "<", "value": 3}, False),
                 ({"all": [{"ref": "n", "op": ">=", "value": 3}, {"not": {"ref": "l", "op": "true"}}]}, True),
                 ({"any": [{"ref": "n", "op": "==", "value": 0}, {"ref": "v", "op": "!=", "value": "yes"}]}, False)]
        for cond, expected in cases:
            self.assertEqual(test_condition(cond, ctx), expected, cond)


class ValidationTests(unittest.TestCase):
    def problems(self, nodes, **kwargs):
        return validate_pipeline(graph(nodes), tools={"search": 1}, functions={"f": 1}, skill=skill(), **kwargs)

    def test_valid(self):
        nodes = [{"id": "a", "kind": "model", "prompt": "plan", "schema": "queries", "output": "q"},
                 {"id": "b", "kind": "map", "over": "$q.queries", "as": "item", "body": [{"id": "c", "kind": "tool", "tool": "search", "args": {}}]}]
        self.assertEqual(self.problems(nodes), [])

    def test_problems(self):
        bad = [{"id": "a", "kind": "model", "prompt": "nope"},
               {"id": "a", "kind": "tool", "tool": "other"},
               {"id": "c", "kind": "code", "function": "g"},
               {"id": "d", "kind": "loop", "body": [{"id": "e", "kind": "ask_user"}], "max": 99},
               {"id": "f", "kind": "branch", "if": {"op": "bogus"}},
               {"id": "g", "kind": "wat"}, {"kind": "code"}, "text"]
        text = "; ".join(self.problems(bad))
        for part in ("no prompt 'nope'", "used twice", "not registered", "function 'g'", "between 1 and 20", "needs 'question'", "needs 'ref'", "unknown operator",
                     "unknown kind", "every node needs an id", "must be an object"):
            self.assertIn(part, text)
        self.assertIn("does not list the tool", "; ".join(validate_pipeline(graph([{"id": "a", "kind": "tool", "tool": "x"}]), tools={"x": 1}, skill=skill())))
        self.assertTrue(validate_pipeline({"nodes": []}))
        self.assertIn("needs 'result'", "; ".join(validate_pipeline({"nodes": [{"id": "a", "kind": "code", "function": "f"}]})))

    def test_unknown_schema(self):
        self.assertIn("no schema", "; ".join(self.problems([{"id": "a", "kind": "model", "prompt": "plan", "schema": "zzz"}])))


class RunnerTests(unittest.TestCase):
    def runner(self, model=None, tools=None, functions=None, log=None):
        return Runner(model=model, tools=tools, functions=functions, run_log=log, rng=random.Random(1))

    def go(self, nodes, model=None, tools=None, functions=None, skill_=None, inputs=None, log=None, **kwargs):
        events = []
        result = self.runner(model, tools, functions, log).run(skill_ or skill(), graph(nodes), inputs or {"text": "why?"}, on_event=events.append, **kwargs)
        return result, events

    def test_model_code_tool_and_events(self):
        model = FakeModel([json.dumps({"queries": ["a", "b"]})])
        nodes = [{"id": "plan", "kind": "model", "prompt": "plan", "schema": "queries", "output": "q", "plain": "planning {{input.text}}"},
                 {"id": "n", "kind": "code", "function": "count", "args": {"items": "$q.queries"}, "output": "count"},
                 {"id": "search", "kind": "tool", "tool": "search", "args": {"query": "$q.queries.0"}, "output": "out", "plain": "searching {{q.queries.0}}"}]
        result, events = self.go(nodes, model, {"search": Tool(lambda query: "found " + query, "search_calls")}, {"count": lambda items: len(items)})
        self.assertEqual((result.status, result.answer, result.context["count"]), ("done", "found a", 2))
        kinds = [(e["kind"], e["node"]) for e in events]
        self.assertEqual(kinds[0][0], "run_start")
        self.assertEqual(kinds[-1][0], "run_end")
        self.assertIn(("start", "plan"), kinds)
        self.assertIn(("done", "search"), kinds)
        start = [e for e in events if e["kind"] == "start"]
        self.assertEqual(start[0]["plain"], "planning why?")
        self.assertEqual(start[0]["playful"], "Pondering…")                 # lines: kind "model"
        self.assertEqual(start[2]["playful"], "Rummaging…")                 # lines: node id wins over the kind
        self.assertEqual(events[0]["payload"]["nodes"][0]["plain"], "planning why?")
        self.assertEqual([e["seq"] for e in events], sorted(e["seq"] for e in events))
        # the prompt: system, variables, examples; schema and profile reach the model
        call = model.calls[0]
        self.assertEqual(call["messages"][0], {"role": "system", "content": "You are careful."})
        self.assertIn("Question: why?", call["messages"][1]["content"])
        self.assertIn('{"queries": ["why?"]}', call["messages"][1]["content"])
        self.assertEqual((call["schema"]["required"], call["profile"]), (["queries"], "full"))

    def test_invalid_model_answer_is_retried_then_fails(self):
        nodes = [{"id": "plan", "kind": "model", "prompt": "plan", "schema": "queries", "output": "out"}]
        model = FakeModel(["not json", "```json\n" + json.dumps({"queries": ["x"]}) + "\n```"])
        result, events = self.go(nodes, model)
        self.assertEqual((result.status, result.answer), ("done", {"queries": ["x"]}))
        self.assertEqual([e["kind"] for e in events].count("retry"), 1)
        self.assertIn("not valid", model.calls[1]["messages"][-1]["content"])
        model = FakeModel(["nope", json.dumps({"queries": []})])
        result, _ = self.go(nodes, model)
        self.assertEqual(result.status, "error")
        self.assertIn("does not fit the schema", result.error)

    def test_on_error_policies(self):
        def boom():
            raise ValueError("kaput")
        nodes = [{"id": "a", "kind": "code", "function": "boom", "output": "x", "on_error": "default", "default": "fallback"},
                 {"id": "b", "kind": "code", "function": "boom", "output": "y", "on_error": "skip"},
                 {"id": "c", "kind": "code", "function": "echo", "args": {"v": "$x"}, "output": "out"}]
        result, events = self.go(nodes, functions={"boom": boom, "echo": lambda v: v})
        self.assertEqual((result.status, result.answer, result.context["y"]), ("done", "fallback", None))
        self.assertEqual([e["kind"] for e in events].count("error"), 2)
        result, _ = self.go([{"id": "a", "kind": "code", "function": "boom", "output": "out"}], functions={"boom": boom})
        self.assertEqual(result.status, "error")
        self.assertIn("kaput", result.error)

    def test_map_collects_in_order_also_in_parallel(self):
        for workers in (1, 4):
            nodes = [{"id": "m", "kind": "map", "over": "$input.items", "as": "x", "workers": workers, "collect": "sq", "output": "out",
                      "body": [{"id": "sq", "kind": "code", "function": "square", "args": {"v": "$x"}, "output": "sq"}]}]
            result, events = self.go(nodes, functions={"square": lambda v: v * v}, inputs={"items": [1, 2, 3, 4, 5]})
            self.assertEqual(result.answer, [1, 4, 9, 16, 25])
            self.assertEqual(sorted({e["item"] for e in events if e["node"] == "sq"}), [0, 1, 2, 3, 4])

    def test_branch_and_loop(self):
        counter = {"n": 0}

        def tick():
            counter["n"] += 1
            return counter["n"]
        nodes = [{"id": "loop", "kind": "loop", "max": 10, "until": {"ref": "n", "op": ">=", "value": 3},
                  "body": [{"id": "t", "kind": "code", "function": "tick", "output": "n"}]},
                 {"id": "br", "kind": "branch", "if": {"ref": "n", "op": "==", "value": 3},
                  "then": [{"id": "yes", "kind": "code", "function": "const", "args": {"v": "three"}, "output": "out"}],
                  "else": [{"id": "no", "kind": "code", "function": "const", "args": {"v": "other"}, "output": "out"}]}]
        result, _ = self.go(nodes, functions={"tick": tick, "const": lambda v: v})
        self.assertEqual((result.answer, counter["n"]), ("three", 3))
        counter["n"] = 0
        nodes[0]["until"] = {"ref": "n", "op": ">=", "value": 99}
        nodes[0]["max"] = 4
        result, _ = self.go(nodes, functions={"tick": tick, "const": lambda v: v})
        self.assertEqual((result.answer, counter["n"]), ("other", 4))                   # the loop limit ends it

    def test_ask_user(self):
        nodes = [{"id": "q", "kind": "ask_user", "question": "Which way, {{input.text}}?", "options": ["left", "right"], "output": "out"}]
        asked = []
        result, _ = self.go(nodes, ask=lambda q: asked.append(q) or "right")
        self.assertEqual((result.answer, asked[0]["question"], asked[0]["options"]), ("right", "Which way, why??", ["left", "right"]))
        result, _ = self.go(nodes)
        self.assertEqual(result.status, "error")
        result, _ = self.go(nodes, ask=lambda q: None)
        self.assertEqual(result.status, "error")

    def test_budgets(self):
        tool = Tool(lambda: "x", "search_calls")
        nodes = [{"id": "s%d" % i, "kind": "tool", "tool": "search", "args": {}, "output": "out"} for i in range(3)]
        result, events = self.go(nodes, tools={"search": tool})
        self.assertEqual(result.status, "budget")
        self.assertIn("search_calls", result.error)
        self.assertEqual(result.answer, "x")                                 # the partial result is kept
        self.assertEqual(events[-1]["payload"]["status"], "budget")
        nodes = [{"id": "c%d" % i, "kind": "code", "function": "f", "output": "out"} for i in range(5)]
        small = skill(budget={"steps": 3, "seconds": 60})
        result, _ = self.go(nodes, functions={"f": lambda: 1}, skill_=small)
        self.assertEqual(result.status, "budget")
        self.assertIn("steps", result.error)
        clock = iter(range(0, 1000, 100))
        runner = Runner(functions={"f": lambda: 1}, clock=lambda: next(clock))
        result = runner.run(skill(budget={"steps": 10, "seconds": 150}), graph(nodes), {"text": ""})
        self.assertEqual((result.status, result.error), ("budget", "budget exceeded: seconds"))

    def test_stop(self):
        stop = threading.Event()
        nodes = [{"id": "a", "kind": "code", "function": "halt", "output": "out"}, {"id": "b", "kind": "code", "function": "never", "output": "out"}]

        def halt():
            stop.set()
            return "partial"
        result, _ = self.go(nodes, functions={"halt": halt, "never": lambda: 1 / 0}, should_stop=stop.is_set)
        self.assertEqual((result.status, result.answer), ("stopped", "partial"))

    def test_invalid_pipeline_is_refused_before_running(self):
        with self.assertRaises(PipelineError):
            self.runner().run(skill(), graph([{"id": "a", "kind": "code", "function": "missing"}]), {})

    def test_the_run_is_logged(self):
        with tempfile.TemporaryDirectory() as folder:
            log = RunLog(folder)
            nodes = [{"id": "a", "kind": "code", "function": "f", "output": "out"}]
            result, _ = self.go(nodes, functions={"f": lambda: "ok"}, log=log)
            runs = log.read()
            self.assertEqual(len(runs), 1)
            record = runs[0]
            self.assertEqual((record["id"], record["task"], record["skill_version"], record["status"], record["output"]),
                             (result.run_id, "demo", 3, "done", {"answer": "ok"}))
            self.assertEqual([e["kind"] for e in record["events"]], ["run_start", "start", "done", "run_end"])

    def test_long_descriptions_are_clipped(self):
        nodes = [{"id": "a", "kind": "code", "function": "f", "output": "out", "plain": "reading {{input.text}}"}]
        result, events = self.go(nodes, functions={"f": lambda: 1}, inputs={"text": "x" * 1000})
        start = [e for e in events if e["kind"] == "start"][0]
        self.assertEqual(len(start["plain"]), 160)
        self.assertTrue(start["plain"].endswith("…"))

    def test_a_failing_event_sink_does_not_break_the_run(self):
        def sink(event):
            raise RuntimeError("display crashed")
        result = self.runner(functions={"f": lambda: 1}).run(skill(), graph([{"id": "a", "kind": "code", "function": "f", "output": "out"}]), {}, on_event=sink)
        self.assertEqual(result.status, "done")


class CoreTests(unittest.TestCase):
    def core(self, **kwargs):
        return Core(os.path.join(REPO, "skills"), os.path.join(REPO, "pipelines"), tempfile.mkdtemp(), **kwargs)

    def test_the_shipped_skills_are_valid(self):
        core = self.core(functions={"converse": lambda text: text})
        self.assertEqual(core.check(), {})
        self.assertIn("chat", core.skills.names())

    def test_chat_skill_runs_the_converse_function(self):
        core = self.core()
        seen = []
        result = core.run("chat", {"text": "hi"}, functions={"converse": lambda text: "answer to " + text}, on_event=seen.append)
        self.assertEqual((result.status, result.answer), ("done", "answer to hi"))
        self.assertFalse(seen[0]["payload"]["show"])                          # no status block for chat
        self.assertEqual(len(core.run_log.read()), 1)

    def test_unknown_skill_and_missing_function(self):
        core = self.core()
        with self.assertRaises(PipelineError):
            core.run("nothing", {})
        with self.assertRaises(PipelineError):
            core.run("chat", {"text": "x"})                                   # "converse" is not registered
        self.assertIn("chat", core.check())


class OllamaModelTests(unittest.TestCase):
    def setUp(self):
        self.sent = []
        outer = self

        class Client:
            def chat(self, **kwargs):
                outer.sent.append(kwargs)
                return {"message": {"content": "reply"}}
        profiles = {"full": ("big", {"num_ctx": 8192}), "light": ("small", {"num_ctx": 4096})}
        self.model = OllamaModel(Client(), profiles.get, lambda: ("small", {"num_ctx": 4096}), keep_alive="30m")

    def test_profiles_names_options_and_schema(self):
        schema = {"type": "object"}
        self.assertEqual(self.model.chat([{"role": "user", "content": "x"}], schema=schema, profile="full", options={"temperature": 0.1}), "reply")
        sent = self.sent[-1]
        self.assertEqual((sent["model"], sent["format"], sent["options"], sent["keep_alive"], sent["stream"]),
                         ("big", schema, {"num_ctx": 8192, "temperature": 0.1}, "30m", False))
        self.model.chat([], profile="current")
        self.assertEqual(self.sent[-1]["model"], "small")
        self.model.chat([], model="qwen3:8b", options={"num_ctx": 32768})
        self.assertEqual((self.sent[-1]["model"], self.sent[-1]["options"]), ("qwen3:8b", {"num_ctx": 32768}))
        self.model.chat([], profile="unknown")
        self.assertEqual(self.sent[-1]["model"], "small")


if __name__ == "__main__":
    unittest.main()
