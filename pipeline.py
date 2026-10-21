"""
The pipeline runner (ui/REQUIREMENTS_CORE.md 4, 5): a pipeline is a tree of nodes in JSON, the runner executes it, keeps the budgets, checks the stop flag, emits an event
for each node and writes the run log. It knows nothing about Flask, Ollama or the UI: the model, the tools and the functions are given to it, which makes it testable with fakes.

A pipeline file:  {"name": "research", "version": 1, "result": "answer", "nodes": [ node, ... ]}
A node:           {"id", "kind", "plain": "text for the status block with {{variables}}", "output": "name in the context", "on_error": "fail" | "skip" | "default", ...}
  model     "prompt" (stage of the skill), "schema" (optional, name in the skill), "inputs" {var: ref}, "retries" (default 1)
  tool      "tool" (registered tool, must be listed in the skill), "args" {name: ref}
  code      "function" (registered function), "args" {name: ref}
  script    "script" (Python text), "data" {name: ref} (the input of the script), "web" (may use the web broker), "operation" {kind, origin, tainted, stakes}, "limits": runs in the sandbox;
            the output is {status, result, stdout, error, backend, tier ...}; a script that does not end with status ok is an error of the node
  map       "over" ref, "as" name, "body" [nodes], "collect" name (taken from each item's context), "workers" (default 1)
  branch    "if" condition, "then" [nodes], "else" [nodes]
  loop      "body" [nodes], "until" condition (checked after each pass), "max" (1..20)
  ask_user  "question", "options" (optional): the answer of the user
A reference is the string "$name" or "$name.field.0" into the context ("$input" is what the run was started with). A condition is
{"ref", "op" (==, !=, <, <=, >, >=, in, not_in, empty, not_empty, true, false), "value"} or {"all": [..]}, {"any": [..]}, {"not": cond}. No code is evaluated.
"""
import contextvars
import json
import random
import re
import threading
import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

try:
    from . import events as ev
    from .schema_check import check as check_schema
    from .sandbox import Operation
except ImportError:  # used as plain script / in tests
    import events as ev
    from schema_check import check as check_schema
    from sandbox import Operation

Tool = namedtuple("Tool", "func budget_key")

KINDS = ("model", "tool", "code", "script", "map", "branch", "loop", "ask_user")
MAX_LOOP = 20
MAX_PLAIN = 160
ON_ERROR = ("fail", "skip", "default")
OPS = ("==", "!=", "<", "<=", ">", ">=", "in", "not_in", "empty", "not_empty", "true", "false")
DEFAULT_LINES = {"model": ["Thinking…"], "tool": ["Working on it…"], "code": ["Calculating…"], "map": ["One by one…"], "ask_user": ["Over to you…"]}


class PipelineError(Exception):
    """the pipeline file is not valid"""


class BudgetExceeded(Exception):
    pass


class Stopped(Exception):
    pass


class NodeError(Exception):
    pass


# --- references, templates, conditions -----------------------------------------------------------------------------

_MISSING = object()


def lookup(path, ctx):
    """"name.field.0" in the context; _MISSING when it is not there"""
    value = ctx
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, (list, tuple)) and part.lstrip("-").isdigit() and -len(value) <= int(part) < len(value):
            value = value[int(part)]
        else:
            return _MISSING
    return value


def resolve(value, ctx):
    """"$ref" strings are replaced by the value they point to (recursively in lists and dicts); everything else stays as it is"""
    if isinstance(value, str) and value.startswith("$") and len(value) > 1:
        found = lookup(value[1:], ctx)
        if found is _MISSING:
            raise NodeError("unknown reference %s" % value)
        return found
    if isinstance(value, dict):
        return {k: resolve(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, ctx) for v in value]
    return value


def _text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def render(template, ctx, strict=True):
    """{{name}} in a text is replaced by the value (JSON for lists and dicts); an unknown name is an error, or stays visible when not strict"""
    def fill(match):
        found = lookup(match.group(1).strip(), ctx)
        if found is _MISSING:
            if strict:
                raise NodeError("the text uses {{%s}} which has no value" % match.group(1).strip())
            return match.group(0)
        return _text(found)
    return re.sub(r"\{\{\s*([A-Za-z_][\w.\-]*)\s*\}\}", fill, template)


def test_condition(cond, ctx):
    if "all" in cond:
        return all(test_condition(c, ctx) for c in cond["all"])
    if "any" in cond:
        return any(test_condition(c, ctx) for c in cond["any"])
    if "not" in cond:
        return not test_condition(cond["not"], ctx)
    value = lookup(cond["ref"], ctx)
    if value is _MISSING:
        value = None
    op, other = cond.get("op", "true"), cond.get("value")
    try:
        if op == "==":
            return value == other
        if op == "!=":
            return value != other
        if op == "<":
            return value < other
        if op == "<=":
            return value <= other
        if op == ">":
            return value > other
        if op == ">=":
            return value >= other
        if op == "in":
            return value in other
        if op == "not_in":
            return value not in other
    except TypeError:
        return False
    if op == "empty":
        return value in (None, "", [], {})
    if op == "not_empty":
        return value not in (None, "", [], {})
    if op == "true":
        return bool(value)
    if op == "false":
        return not value
    raise NodeError("unknown condition operator %r" % op)


def _condition_problems(cond, where):
    if not isinstance(cond, dict):
        return ["%s: a condition must be an object" % where]
    problems = []
    for key in ("all", "any"):
        if key in cond:
            for sub in cond[key]:
                problems.extend(_condition_problems(sub, where))
            return problems
    if "not" in cond:
        return _condition_problems(cond["not"], where)
    if "ref" not in cond:
        problems.append("%s: a condition needs 'ref'" % where)
    if cond.get("op", "true") not in OPS:
        problems.append("%s: unknown operator %r" % (where, cond.get("op")))
    return problems


# --- validation of a pipeline file ----------------------------------------------------------------------------------

def validate_pipeline(graph, tools=None, functions=None, skill=None):
    """returns the problems of a pipeline (empty = valid); tools/functions: names that exist (None = not checked); skill: the prompts, schemas and tools are checked against it"""
    problems = []
    if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list) or not graph["nodes"]:
        return ["the pipeline needs a non-empty list 'nodes'"]
    seen = set()

    def walk(nodes, where):
        for node in nodes:
            if not isinstance(node, dict):
                problems.append("%s: a node must be an object" % where)
                continue
            nid, kind = node.get("id"), node.get("kind")
            label = "node '%s'" % nid
            if not isinstance(nid, str) or not re.fullmatch(r"[A-Za-z][\w\-]{0,39}", nid):
                problems.append("%s: every node needs an id (letters, digits, _ and -)" % where)
                continue
            if nid in seen:
                problems.append("%s: the id is used twice" % label)
            seen.add(nid)
            if kind not in KINDS:
                problems.append("%s: unknown kind %r" % (label, kind))
                continue
            if node.get("on_error", "fail") not in ON_ERROR:
                problems.append("%s: on_error must be one of %s" % (label, ", ".join(ON_ERROR)))
            if kind == "model":
                if node.get("template"):
                    pass                                                  # prompt and schema come with the node (library entries)
                elif skill is not None:
                    if node.get("prompt") not in skill["prompts"]:
                        problems.append("%s: the skill has no prompt '%s'" % (label, node.get("prompt")))
                    if node.get("schema") is not None and node["schema"] not in skill["schemas"]:
                        problems.append("%s: the skill has no schema '%s'" % (label, node["schema"]))
                elif not node.get("prompt"):
                    problems.append("%s: a model node needs 'prompt'" % label)
            elif kind == "tool":
                name = node.get("tool")
                if not name:
                    problems.append("%s: a tool node needs 'tool'" % label)
                if tools is not None and name not in tools:
                    problems.append("%s: the tool '%s' is not registered" % (label, name))
                if skill is not None and name not in skill["tools"]:
                    problems.append("%s: the skill does not list the tool '%s'" % (label, name))
            elif kind == "script":
                if not isinstance(node.get("script"), str) or not node["script"].strip():
                    problems.append("%s: a script node needs 'script'" % label)
            elif kind == "code":
                if not node.get("function"):
                    problems.append("%s: a code node needs 'function'" % label)
                elif functions is not None and node["function"] not in functions:
                    problems.append("%s: the function '%s' is not registered" % (label, node["function"]))
            elif kind == "map":
                for key in ("over", "as", "body"):
                    if not node.get(key):
                        problems.append("%s: a map node needs '%s'" % (label, key))
                walk(node.get("body") or [], label)
            elif kind == "branch":
                problems.extend(_condition_problems(node.get("if"), label))
                walk(node.get("then") or [], label)
                walk(node.get("else") or [], label)
            elif kind == "loop":
                limit = node.get("max")
                if not isinstance(limit, int) or not 1 <= limit <= MAX_LOOP:
                    problems.append("%s: a loop needs 'max' between 1 and %d" % (label, MAX_LOOP))
                if node.get("until") is not None:
                    problems.extend(_condition_problems(node["until"], label))
                if not node.get("body"):
                    problems.append("%s: a loop needs a 'body'" % label)
                walk(node.get("body") or [], label)
            elif kind == "ask_user" and not node.get("question"):
                problems.append("%s: an ask_user node needs 'question'" % label)

    walk(graph["nodes"], "pipeline")
    if not graph.get("result"):
        problems.append("the pipeline needs 'result' (the context name of the final answer)")
    return problems


# --- the run -----------------------------------------------------------------------------------------------------------

class RunResult:
    def __init__(self, run_id, status, answer, context, seconds, error=None, events=None):
        self.run_id, self.status, self.answer, self.context = run_id, status, answer, context
        self.seconds, self.error, self.events = seconds, error, events or []

    @property
    def ok(self):
        return self.status == "done"


class _State:
    def __init__(self, runner, skill, graph, ctx, on_event, should_stop, ask, run, functions, tools):
        self.runner, self.skill, self.graph, self.ctx = runner, skill, graph, ctx
        self.on_event, self.should_stop, self.ask, self.run = on_event, should_stop, ask, run
        self.functions, self.tools = functions, tools
        self.t0 = runner.clock()
        self.steps = 0
        self.calls = {}
        self.stream = ev.EventStream(run.id if run else None, sink=run, on_event=on_event, clock=runner.clock, t0=self.t0, strict=runner.strict_events)
        self.lock = threading.Lock()
        self.budget = skill["budget"]


class Runner:
    def __init__(self, model=None, tools=None, functions=None, run_log=None, rng=None, clock=time.monotonic, sandbox=None, broker_factory=None, environment=None, strict_events=False):
        """model: object with chat(messages, schema=None, model=None, profile=None, options=None) -> text; tools: {name: callable | Tool};
        functions: {name: callable}; run_log: RunLog or None; environment: a dict or a function returning one (events.environment()), written into run_start;
        strict_events: a domain event that does not fit its schema raises (tests) instead of becoming a log_error event"""
        self.model = model
        self.tools = {k: v if isinstance(v, Tool) else Tool(v, None) for k, v in (tools or {}).items()}
        self.functions = dict(functions or {})
        self.run_log = run_log
        self.environment, self.strict_events = environment, strict_events
        self.sandbox, self.broker_factory = sandbox, broker_factory      # sandbox.SandboxRouter and a function that makes a web broker per script
        self.rng = rng or random.Random()
        self.clock = clock

    # -- public ----
    def run(self, skill, graph, inputs, on_event=None, should_stop=None, ask=None, functions=None, tools=None, task=None):
        all_functions = {**self.functions, **(functions or {})}
        all_tools = {**self.tools, **{k: v if isinstance(v, Tool) else Tool(v, None) for k, v in (tools or {}).items()}}
        problems = validate_pipeline(graph, tools=all_tools, functions=all_functions, skill=skill)
        if problems:
            raise PipelineError("; ".join(problems))
        run = None
        if self.run_log is not None:
            model = (skill["model"] or {}).get("name") or (skill["model"] or {}).get("profile")
            run = self.run_log.start(task or skill["name"], skill["name"], skill["version"], graph.get("name"), graph.get("version"), model, inputs,
                                     uses=graph.get("uses"))
        ctx = {"input": inputs}
        st = _State(self, skill, graph, ctx, on_event, should_stop, ask, run, all_functions, all_tools)
        with ev.activate(st.stream):
            return self._run_state(st, skill, graph, ctx, run)

    def _start_payload(self, skill, graph, ctx):
        payload = {"skill": skill["name"], "show": skill["status_block"], "nodes": self._outline(graph["nodes"], ctx)}
        env = self.environment() if callable(self.environment) else self.environment
        if env:
            payload["env"] = env
        return payload

    def _run_state(self, st, skill, graph, ctx, run):
        self._emit(st, "run_start", None, plain=skill.get("description", skill["name"]),
                   payload=self._start_payload(skill, graph, ctx))
        status, error = "done", None
        try:
            self._run_nodes(st, graph["nodes"], ctx)
        except Stopped:
            status = "stopped"
        except BudgetExceeded as exc:
            status, error = "budget", "budget exceeded: %s" % exc
            self._emit(st, "error", None, plain=error)
        except NodeError as exc:
            status, error = "error", str(exc)
        except Exception as exc:                    # a bug in a tool or function must not take MIA down
            status, error = "error", "%s: %s" % (type(exc).__name__, exc)
            self._emit(st, "error", None, plain=error)
        seconds = self.clock() - st.t0
        answer = lookup(graph["result"], ctx)
        answer = None if answer is _MISSING else answer
        self._emit(st, "run_end", None, plain=status, payload={"status": status, "seconds": round(seconds, 3)})
        if run is not None:
            run.finish(status, {"answer": answer}, seconds, error)
        return RunResult(run.id if run else None, status, answer, ctx, seconds, error, run.events if run else [])

    # -- events ----
    def _outline(self, nodes, ctx):
        return [{"id": n["id"], "kind": n["kind"], "plain": render(n.get("plain", n["id"]), ctx, strict=False)} for n in nodes]

    def _playful(self, st, node):
        lines = st.skill["lines"].get(node["id"]) or st.skill["lines"].get(node["kind"]) or DEFAULT_LINES.get(node["kind"]) or [""]
        return self.rng.choice(lines)

    def _emit(self, st, kind, node, plain=None, payload=None, item=None, ctx=None):
        """a lifecycle event; the stream gives it run, seq and time and removes secrets. Returns the event written."""
        ctx = st.ctx if ctx is None else ctx
        text = plain
        if text is None and node is not None:
            try:
                text = render(node.get("plain", node["id"]), ctx, strict=False)
            except Exception:
                text = node["id"]
        if text and len(text) > MAX_PLAIN:
            text = text[:MAX_PLAIN - 1] + "…"                 # the status line shows what happens, not whole documents
        return st.stream.record({"node": node["id"] if node else None, "node_kind": node["kind"] if node else None, "library": node.get("library") if node else None,
                                 "kind": kind, "item": item, "playful": self._playful(st, node) if node and kind == "start" else "", "plain": text or "",
                                 "payload": payload or {}, "actor": node["id"] if node else None})

    # -- execution ----
    def _guard(self, st):
        if st.should_stop is not None and st.should_stop():
            raise Stopped()
        with st.lock:
            st.steps += 1
            steps = st.steps
        if steps > st.budget.get("steps", 50):
            raise BudgetExceeded("steps")
        if self.clock() - st.t0 > st.budget.get("seconds", 600):
            raise BudgetExceeded("seconds")

    def _run_nodes(self, st, nodes, ctx, item=None):
        for node in nodes:
            self._run_node(st, node, ctx, item)

    def _run_node(self, st, node, ctx, item=None):
        self._guard(st)
        kind = node["kind"]
        start = self._emit(st, "start", node, item=item, ctx=ctx)
        with ev.acting(node["id"], parent=start["seq"]):
            try:
                value = getattr(self, "_do_" + kind)(st, node, ctx, item)
            except (Stopped, BudgetExceeded):
                raise
            except Exception as exc:
                message = str(exc) if isinstance(exc, NodeError) else "%s: %s" % (type(exc).__name__, exc)
                self._emit(st, "error", node, plain="%s failed: %s" % (node["id"], message), item=item, ctx=ctx)
                policy = node.get("on_error", "fail")
                if policy == "fail":
                    raise NodeError("%s: %s" % (node["id"], message))
                value = node.get("default") if policy == "default" else None
        if node.get("output") and kind not in ("map",):
            ctx[node["output"]] = value
        self._emit(st, "done", node, item=item, payload={"output": _brief(value)} if value is not None else None, ctx=ctx)

    def _do_code(self, st, node, ctx, item):
        function = st.functions[node["function"]]
        return function(**resolve(node.get("args", {}), ctx))

    def _do_script(self, st, node, ctx, item):
        if self.sandbox is None:
            raise NodeError("no sandbox is configured, scripts cannot run")
        operation = Operation(**{k: v for k, v in (node.get("operation") or {}).items() if k in ("kind", "origin", "tainted", "stakes")})
        data = resolve(node.get("data", {}), ctx)
        limits = {k: v for k, v in (node.get("limits") or {}).items() if k in ("timeout", "memory_mb", "cpu_seconds", "max_output")}
        broker = None
        if node.get("web"):
            if self.broker_factory is None:
                raise NodeError("web access for scripts is not configured")
            broker = self.broker_factory()
        if broker is not None:
            with broker:
                run = self.sandbox.run(node["script"], data, operation=operation, broker=broker, **{"timeout": 60, **limits})
        else:
            run = self.sandbox.run(node["script"], data, operation=operation, **limits)
        if run.status != "ok":
            detail = (run.error or {}).get("message") or "; ".join(run.problems) or run.status
            raise NodeError("the script %s: %s" % (run.status, detail))
        return run.as_dict()

    def _do_tool(self, st, node, ctx, item):
        tool = st.tools[node["tool"]]
        if tool.budget_key:
            with st.lock:
                st.calls[tool.budget_key] = st.calls.get(tool.budget_key, 0) + 1
                count = st.calls[tool.budget_key]
            limit = st.budget.get(tool.budget_key)
            if limit is not None and count > limit:
                raise BudgetExceeded(tool.budget_key)
        return tool.func(**resolve(node.get("args", {}), ctx))

    def _do_ask_user(self, st, node, ctx, item):
        if st.ask is None:
            raise NodeError("the pipeline asks the user, but nobody can answer")
        answer = st.ask({"node": node["id"], "question": render(node["question"], ctx), "options": resolve(node.get("options"), ctx)})
        if answer is None:
            raise NodeError("no answer from the user")
        return answer

    def _do_branch(self, st, node, ctx, item):
        self._run_nodes(st, node.get("then" if test_condition(node["if"], ctx) else "else") or [], ctx, item)

    def _do_loop(self, st, node, ctx, item):
        for _ in range(node["max"]):
            self._run_nodes(st, node["body"], ctx, item)
            if node.get("until") is not None and test_condition(node["until"], ctx):
                break

    def _do_map(self, st, node, ctx, item):
        values = resolve(node["over"], ctx)
        if not isinstance(values, (list, tuple)):
            raise NodeError("'over' must be a list")
        results = [None] * len(values)

        def one(index):
            sub = dict(ctx)
            sub[node["as"]] = values[index]
            sub["index"] = index
            self._run_nodes(st, node["body"], sub, index)
            results[index] = sub.get(node.get("collect")) if node.get("collect") else sub.get(node["as"])
        workers = max(1, int(node.get("workers", 1)))
        if workers == 1 or len(values) < 2:
            for index in range(len(values)):
                one(index)
        else:
            contexts = [contextvars.copy_context() for _ in values]          # the run id and the actor reach the threads
            with ThreadPoolExecutor(max_workers=workers) as pool:
                for future in [pool.submit(contexts[i].run, one, i) for i in range(len(values))]:
                    future.result()          # the first error / stop / budget ends the run
        if node.get("output"):
            ctx[node["output"]] = results
        return results

    def _do_model(self, st, node, ctx, item):
        skill = st.skill
        variables = {**ctx, **resolve(node.get("inputs", {}), ctx)}
        if node.get("template"):
            prompt = render(node["template"], variables)
            system = node.get("system")
            schema = node.get("schema_def")
        else:
            prompt = render(skill["prompts"][node["prompt"]], variables)
            example = skill["examples"].get(node["prompt"])
            if example:
                prompt += "\n\nExamples:\n" + render(example, variables, strict=False)
            system = skill["prompts"].get("system")
            schema = skill["schemas"].get(node["schema"]) if node.get("schema") else None
        messages = [{"role": "system", "content": render(system, variables, strict=False)}] if system else []
        messages.append({"role": "user", "content": prompt})
        settings = skill["model"] or {}
        for attempt in range(int(node.get("retries", 1)) + 1):
            prompt_hash, started = ev.digest(messages), self.clock()
            reply = self.model.chat(messages, schema=schema, model=settings.get("name"), profile=settings.get("profile"), options=settings.get("options"))
            seconds = self.clock() - started
            if schema is None:
                self._model_call(settings, prompt_hash, reply, seconds, True, attempt, None)
                return reply
            try:
                value = json.loads(_strip_fence(reply))
                problems = check_schema(value, schema)
            except ValueError as exc:
                value, problems = None, ["the reply is not valid JSON (%s)" % exc]
            self._model_call(settings, prompt_hash, reply, seconds, not problems, attempt, node.get("schema"))
            if not problems:
                return value
            if attempt >= int(node.get("retries", 1)):
                raise NodeError("the model's answer does not fit the schema: %s" % "; ".join(problems[:3]))
            self._emit(st, "retry", node, plain="%s: answer did not fit (%s), asking again" % (node["id"], problems[0]), item=item, ctx=ctx)
            messages = messages + [{"role": "assistant", "content": reply},
                                   {"role": "user", "content": "Your reply was not valid: %s. Answer again with only valid JSON that fits the schema." % "; ".join(problems[:5])}]


    def _model_call(self, settings, prompt_hash, reply, seconds, valid, attempt, schema_name):
        """the model_call event (13d): what was asked and answered by hash, how long it took, whether the answer fitted; the digest of the model is filled in by the environment"""
        text = reply if isinstance(reply, str) else _text(reply)
        ev.emit("model_call", {"model": settings.get("name"), "profile": settings.get("profile"), "digest": None, "options": settings.get("options"),
                               "prompt_hash": prompt_hash, "response_hash": ev.digest(text), "response_chars": len(text), "seconds": round(seconds, 3), "tokens_in": None,
                               "tokens_out": None, "schema": schema_name, "valid": bool(valid), "attempt": attempt})


def _strip_fence(text):
    found = re.match(r"\s*```(?:json)?\s*\n(.*?)```\s*$", text, re.S)
    return found.group(1) if found else text


def _brief(value, limit=200):
    text = _text(value) if not isinstance(value, str) else value
    return text if len(text) <= limit else text[:limit] + "…"
