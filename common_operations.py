"""The common operations of the shipped library nodes (part of the converted skills, G-V2.CONVERT, task T-CV-03b, A-123 P1b): STUB until T-CV-03b.

The functions the library nodes name today (the FUNCTIONS registries of research, extraction, behaviour, verification, number_gate and checks) live here once; the thin
entries of the toolbox call them by name, so no function exists twice. The stub returns wrong values and never raises, so the acceptance tests fail on an assertion.
The interface is the one the red tests of T-CV-03b assume:
- FUNCTIONS: {name: function}, every function a shipped code node names;
- call(name, args): FUNCTIONS[name](**args);
- use(model=None, tools=None, settings=None): context manager that hands the model (chat(messages, schema, model, profile, options)), the tools ({name: function(**args)})
  and the model settings ({"profile", "options"}) to the steps run inside it;
- model_step(system, template, schema, args, retries=1): one model call as the old runner makes it for a library node of kind model;
- tool_call(name, args): the handed tool of that name, called with the args as keywords; ToolMissing when none was handed.
"""
from contextlib import contextmanager

FUNCTIONS = {}


class ToolMissing(Exception):
    """a tool step ran and no tool of its name was handed to `use`"""


def call(name, args):
    """STUB (T-CV-03b)"""
    return None


@contextmanager
def use(model=None, tools=None, settings=None):
    """STUB (T-CV-03b)"""
    yield


def model_step(system, template, schema, args, retries=1):
    """STUB (T-CV-03b)"""
    return None


def tool_call(name, args):
    """STUB (T-CV-03b)"""
    return None
