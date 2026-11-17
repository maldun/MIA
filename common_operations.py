"""The common operations of the shipped library nodes (part of the converted skills, G-V2.CONVERT, task T-CV-03b, A-123, D-248).

The functions the library nodes name (the FUNCTIONS registries of research, extraction, behaviour, verification, number_gate and the offline checks) live here once, as the
same function objects; the thin entries of the toolbox call them by name, so no function exists twice. The old registries stay in their modules and keep working.
- FUNCTIONS: {name: function}, every function a shipped code node names; call(name, args) runs FUNCTIONS[name](**args). Some functions are built by the app from its
  wiring (the web checks, the script checks, hard_checks_*, converse): FUNCTIONS holds a placeholder for them that raises FunctionUnbound until the app calls
  bind(name, function), so a missing wiring is a clear refusal and never a silent wrong value.
- A tool or the model reaches a transform as a JSON descriptor in a data node (D-248): {"tool": name, "settings": {...}} or {"model": profile, "options": {...}}. A descriptor
  is resolved only against what MIA registered (D-248 D): register_tool(name, function, settings=(declared keys,)), register_model(profile, chat), reset() empties both.
  resolve_tool(descriptor) -> function with the settings applied; ToolMissing for an unknown name, DescriptorRefused for a setting the tool did not declare;
  resolve_model(descriptor) -> (chat, profile, options); ModelMissing for an unknown profile. Untrusted text never becomes a name: only the registry decides.
- model_step(system, template, schema, inputs, retries=1) and tool_step(inputs): what a thin entry's `stage(inputs, outputs, node)` calls; the descriptor sits in
  inputs["model"] or inputs["tool"], every other input is an argument of the step.
"""
import contextvars
import functools
import json
import threading

try:
    from . import behaviour, checks, extraction, number_gate, research, verification, web_tools
    from . import control_flow
    from .pipeline import BudgetExceeded, NodeError, NOT_COUNTED, render, _strip_fence
    from .schema_check import check as check_schema
except ImportError:
    import control_flow
    import behaviour
    import checks
    import extraction
    import number_gate
    import research
    import verification
    import web_tools
    from pipeline import BudgetExceeded, NodeError, NOT_COUNTED, render, _strip_fence
    from schema_check import check as check_schema


class DescriptorRefused(Exception):
    """a descriptor names something MIA did not register, or sets what the registered thing did not declare"""


class ToolMissing(DescriptorRefused):
    pass


class ModelMissing(DescriptorRefused):
    pass


class FunctionUnbound(Exception):
    """a function the app builds from its wiring was called before the app bound it"""


class _State:
    """what one converted run needs besides its arguments (F-01): the registries, the tool budgets with the door and the events (T-CV-06a), the stop rules of the controllers (D-258).
    One object per run, kept in a context variable: a run in another thread has its own, and the threads of a parallel map copy the context of their run, so they share it."""
    def __init__(self):
        self.bound = {}
        self.tools = {}       # name -> (function, declared setting keys)
        self.models = {}      # profile -> chat object
        self.run = {}         # the tool budgets, the door and the events; empty outside run_converted: then nothing is counted
        self.control = {}     # "call" (use, args) -> value of a library node, "limits": the stop rules of this run (control_flow.Limits)


_STATE = contextvars.ContextVar("common_operations_state")


def _state():
    try:
        return _STATE.get()
    except LookupError:
        state = _State()
        _STATE.set(state)
        return state


def _late(name):
    def unbound(**args):
        bound = _state().bound
        if name not in bound:
            raise FunctionUnbound("%s is built by the app and has not been bound here" % name)
        return bound[name](**args)
    return unbound


def pick_field(value, path=""):
    """the part of `value` at a dot-separated path (dict keys, list indexes as numbers); the pick transform of a field reference like `$raw.claims`"""
    here = value
    for part in [p for p in str(path).split(".") if p]:
        try:
            here = here[int(part)] if isinstance(here, list) else here[part]
        except (KeyError, IndexError, ValueError, TypeError):
            raise KeyError("pick_field: no %r at path %r" % (part, path)) from None
    return here


# The old registries are merged without copying a function; the rest are plain functions of web_tools or built by the app (core.py, web_app.py).
FUNCTIONS = {**checks.OFFLINE_FUNCTIONS, **extraction.FUNCTIONS, **behaviour.FUNCTIONS, **verification.FUNCTIONS, **number_gate.FUNCTIONS, **research.FUNCTIONS,
             "pick_field": pick_field, "chunk_text": web_tools.chunk_text, "untrusted": web_tools.untrusted, "injection_signals": web_tools.injection_signals}
APP_BUILT = ("citation_check", "web_confirm", "script_check", "script_check_web", "hard_checks_offline", "hard_checks_web", "converse")
for _name in APP_BUILT:
    FUNCTIONS[_name] = _late(_name)


def bind(name, function):
    """gives a function the app builds (a name of APP_BUILT) its implementation"""
    if name not in APP_BUILT:
        raise ValueError("%s is not a function that waits for the app" % name)
    _state().bound[name] = function


def call(name, args):
    return FUNCTIONS[name](**args)


def register_tool(name, function, settings=()):
    _state().tools[name] = (function, tuple(settings))


def register_model(profile, chat):
    _state().models[profile] = chat


def register_run(budget=None, tool_keys=None, door=None, door_tools=None, run_id="converted"):
    """the budget of the run (skill budget keys), the budget key of each tool, and the IF-402 door (`call(run, tool, args)`) with the tools that go through it"""
    run = _state().run
    run.clear()
    run.update(budget=dict(budget or {}), tool_keys=dict(tool_keys or {}), door=door, door_tools=dict(door_tools or {}), run_id=run_id,
                calls={}, events=[], lock=threading.Lock(), budget_end=None)


def run_events():
    return list(_state().run.get("events", []))


def budget_end():
    """the reason of the budget end of the run (a budget key, seconds or steps), else None"""
    return _state().run.get("budget_end")


def note_budget_end(exc):
    run = _state().run
    if run and run["budget_end"] is None:
        run["budget_end"] = str(exc.args[0]) if exc.args else "budget"


def register_control(call, limits=None):
    """what the controllers need of the run: the call of a library node by its ID and the stop rules (D-258)"""
    _state().control.update(call=call, limits=limits)


def control_step(inputs, outputs, node):
    """what the thin entries control.branch, control.map and control.loop run: `node` is the settings {"construct": kind, "node": the JSON of the construct}"""
    control = _state().control
    if "call" not in control:
        raise RuntimeError("no node call is registered: the controllers run only inside run_converted")
    try:
        return control_flow.run_construct(node["node"], inputs, outputs, control["call"], control.get("limits"))
    except BudgetExceeded as exc:
        note_budget_end(exc)
        raise


def reset():
    """a fresh state for the run that starts in this context (F-01: never clears what another run uses)"""
    _STATE.set(_State())


def resolve_tool(descriptor):
    name = descriptor.get("tool") if isinstance(descriptor, dict) else None
    tools = _state().tools
    if not isinstance(name, str) or name not in tools:
        raise ToolMissing("the tool %r is not registered" % (name,))
    function, declared = tools[name]
    settings = descriptor.get("settings") or {}
    undeclared = sorted(set(settings) - set(declared))
    if undeclared:
        raise DescriptorRefused("the tool %s does not declare the settings %s" % (name, ", ".join(undeclared)))
    return functools.partial(function, **settings)


def resolve_model(descriptor):
    profile = descriptor.get("model") if isinstance(descriptor, dict) else None
    models = _state().models
    if not isinstance(profile, str) or profile not in models:
        raise ModelMissing("the model %r is not registered" % (profile,))
    return models[profile], profile, descriptor.get("options") or None


def model_step(system, template, schema, inputs, retries=1):
    """the call the old runner makes for a library node of kind model (pipeline.Runner._do_model), without budgets and events, which belong to the runner"""
    chat, profile, options = resolve_model(inputs.get("model"))
    variables = {key: value for key, value in inputs.items() if key != "model"}
    messages = [{"role": "system", "content": render(system, variables, strict=False)}] if system else []
    messages.append({"role": "user", "content": render(template, variables)})
    for attempt in range(int(retries) + 1):
        reply = chat.chat(messages, schema=schema, model=None, profile=profile, options=options)
        if schema is None:
            return reply
        try:
            value = json.loads(_strip_fence(reply))
            problems = check_schema(value, schema)
        except ValueError as error:
            value, problems = None, ["the reply is not valid JSON (%s)" % error]
        if not problems:
            return value
        if attempt >= int(retries):
            raise NodeError("the model's answer does not fit the schema: %s" % "; ".join(problems[:3]))
        messages = messages + [{"role": "assistant", "content": reply},
                               {"role": "user", "content": "Your reply was not valid: %s. Answer again with only valid JSON that fits the schema." % "; ".join(problems[:5])}]


def tool_step(inputs):
    """a tool node (T-CV-06a): counted against the budget key of the tool before it runs (one counter per run, also for parallel map items), through the IF-402 door when the app
    gave one for this tool, with tool_call and budget_spent events; outside run_converted (no run registered) it only calls the tool"""
    descriptor = inputs.get("tool")
    name = descriptor.get("tool") if isinstance(descriptor, dict) else None
    args = {key: value for key, value in inputs.items() if key != "tool"}
    run = _state().run
    door = run.get("door") is not None and name in run.get("door_tools", {})
    function = None if door else resolve_tool(descriptor)
    key, count, limit = run.get("tool_keys", {}).get(name), None, None
    if key:
        with run["lock"]:                       # reserved before the call: map items run in parallel
            run["calls"][key] = run["calls"].get(key, 0) + 1
            count = run["calls"][key]
        limit = run["budget"].get(key)
        if limit is not None:
            _event({"kind": "budget_spent", "name": key, "amount": 1, "used": count, "limit": limit})
        if limit is not None and count > limit:
            exc = BudgetExceeded(key)
            note_budget_end(exc)
            raise exc
    trust = None
    try:
        if door:
            limits = {tool: run["budget"][k] for tool, k in run["door_tools"].items() if k in run["budget"]}
            try:
                found = run["door"].call({"id": run["run_id"], "limits": limits}, name, args)
            except Exception as exc:
                if getattr(exc, "code", None) == "budget":
                    ended = BudgetExceeded(run["door_tools"].get(name) or name)
                    note_budget_end(ended)
                    raise ended from exc
                raise
            output, trust = found["output"], found["trust"]
        else:
            output = function(**args)
    except Exception as exc:
        refusal = exc.__cause__ if isinstance(exc, BudgetExceeded) else exc
        if key and getattr(refusal, "code", None) in NOT_COUNTED:
            with run["lock"]:                   # IF-402: a call the door refuses counts nothing
                run["calls"][key] -= 1
        raise
    _event({"kind": "tool_call", "tool": name, "trust": trust})
    return output


def _event(event):
    run = _state().run
    if run:
        with run["lock"]:
            run["events"].append(event)
