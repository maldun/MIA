"""The common operations of the shipped library nodes (part of the converted skills, G-V2.CONVERT, task T-CV-03b, A-123, D-248): STUB until T-CV-03b.

The functions the library nodes name today (the FUNCTIONS registries of research, extraction, behaviour, verification, number_gate and checks) live here once; the thin
entries of the toolbox call them by name, so no function exists twice. The stub returns wrong values and never raises, so the acceptance tests fail on an assertion.
The interface the red tests of T-CV-03b assume:
- FUNCTIONS: {name: function}, every function a shipped code node names; call(name, args) runs FUNCTIONS[name](**args).
- A tool or the model reaches a transform as a JSON descriptor in a data node (D-248): {"tool": name, "settings": {...}} or {"model": profile, "options": {...}}. A descriptor
  is resolved only against what MIA registered (D-248 D): register_tool(name, function, settings=(declared keys,)), register_model(profile, chat), reset() empties both.
  resolve_tool(descriptor) -> function with the settings applied; ToolMissing for an unknown name, DescriptorRefused for a setting the tool did not declare;
  resolve_model(descriptor) -> (chat, profile, options); ModelMissing for an unknown profile.
- model_step(system, template, schema, inputs, retries=1) and tool_step(inputs): what a thin entry's `stage(inputs, outputs, node)` calls; the descriptor sits in
  inputs["model"] or inputs["tool"], every other input is an argument of the step.
"""
FUNCTIONS = {}


class DescriptorRefused(Exception):
    """a descriptor names something MIA did not register, or sets what the registered thing did not declare"""


class ToolMissing(DescriptorRefused):
    pass


class ModelMissing(DescriptorRefused):
    pass


def call(name, args):
    """STUB (T-CV-03b)"""
    return None


def register_tool(name, function, settings=()):
    """STUB (T-CV-03b)"""


def register_model(profile, chat):
    """STUB (T-CV-03b)"""


def reset():
    """STUB (T-CV-03b)"""


def resolve_tool(descriptor):
    """STUB (T-CV-03b)"""
    return None


def resolve_model(descriptor):
    """STUB (T-CV-03b)"""
    return None


def model_step(system, template, schema, inputs, retries=1):
    """STUB (T-CV-03b)"""
    return None


def tool_step(inputs):
    """STUB (T-CV-03b)"""
    return None
