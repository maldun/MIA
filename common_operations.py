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
import functools
import json

try:
    from . import behaviour, checks, extraction, number_gate, research, verification, web_tools
    from .pipeline import NodeError, render, _strip_fence
    from .schema_check import check as check_schema
except ImportError:
    import behaviour
    import checks
    import extraction
    import number_gate
    import research
    import verification
    import web_tools
    from pipeline import NodeError, render, _strip_fence
    from schema_check import check as check_schema


class DescriptorRefused(Exception):
    """a descriptor names something MIA did not register, or sets what the registered thing did not declare"""


class ToolMissing(DescriptorRefused):
    pass


class ModelMissing(DescriptorRefused):
    pass


class FunctionUnbound(Exception):
    """a function the app builds from its wiring was called before the app bound it"""


_BOUND = {}
_TOOLS = {}      # name -> (function, declared setting keys)
_MODELS = {}     # profile -> chat object


def _late(name):
    def unbound(**args):
        if name not in _BOUND:
            raise FunctionUnbound("%s is built by the app and has not been bound here" % name)
        return _BOUND[name](**args)
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
    _BOUND[name] = function


def call(name, args):
    return FUNCTIONS[name](**args)


def register_tool(name, function, settings=()):
    _TOOLS[name] = (function, tuple(settings))


def register_model(profile, chat):
    _MODELS[profile] = chat


def reset():
    _TOOLS.clear()
    _MODELS.clear()
    _BOUND.clear()


def resolve_tool(descriptor):
    name = descriptor.get("tool") if isinstance(descriptor, dict) else None
    if not isinstance(name, str) or name not in _TOOLS:
        raise ToolMissing("the tool %r is not registered" % (name,))
    function, declared = _TOOLS[name]
    settings = descriptor.get("settings") or {}
    undeclared = sorted(set(settings) - set(declared))
    if undeclared:
        raise DescriptorRefused("the tool %s does not declare the settings %s" % (name, ", ".join(undeclared)))
    return functools.partial(function, **settings)


def resolve_model(descriptor):
    profile = descriptor.get("model") if isinstance(descriptor, dict) else None
    if not isinstance(profile, str) or profile not in _MODELS:
        raise ModelMissing("the model %r is not registered" % (profile,))
    return _MODELS[profile], profile, descriptor.get("options") or {}


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
    function = resolve_tool(inputs.get("tool"))
    return function(**{key: value for key, value in inputs.items() if key != "tool"})
