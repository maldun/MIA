"""The controllers of the converted skills: control.branch, control.map and control.loop (G-V2.CONVERT, D-258; REQ-WFM-058).

A pipeline's construct (the JSON of a branch, map or loop, with the nodes below it) is ONE node of the graph; the toolbox entries `control.<kind>` hand it to run_construct.
The semantics are those of the old runner (pipeline.py): references, conditions and `on_error` are the same functions, a loop tests `until` after its body, a map collects
`collect` (else `as`) per item in order, a missing `else` is an empty part. Only the calls of library nodes are injected (`call(use, args)`), so the module needs no toolbox and no model.
Not done here, as in the rest of the converted path so far: events, token counting.
"""
import contextvars
import time
from concurrent.futures import ThreadPoolExecutor

try:
    from .pipeline import BudgetExceeded, NodeError, Stopped, resolve, test_condition
except ImportError:
    from pipeline import BudgetExceeded, NodeError, Stopped, resolve, test_condition


class Limits:
    """the stop rules of the old runner for the nodes of one construct: seconds since the start, steps (every node that runs counts, a construct too) and a stop request"""

    def __init__(self, seconds=None, steps=None, should_stop=None, clock=time.monotonic):
        self.seconds, self.steps, self.should_stop, self.clock = seconds, steps, should_stop, clock
        self.started, self.used = clock(), 0

    def guard(self):
        if self.should_stop is not None and self.should_stop():
            raise Stopped()
        if self.seconds is not None and self.clock() - self.started > self.seconds:
            raise BudgetExceeded("seconds")
        if self.steps is not None and self.used >= self.steps:
            raise BudgetExceeded("steps")
        self.used += 1


def context_of(inputs):
    """the references of a pipeline read `$name.path`; an edge name `input.<field>` is a field of the input"""
    ctx = {}
    for name, value in inputs.items():
        if name.startswith("input."):
            ctx.setdefault("input", {})[name[len("input."):]] = value
        else:
            ctx[name] = value
    return ctx


def run_construct(construct, inputs, outputs, call, limits=None):
    """runs the construct on the variables `inputs` and returns {"outputs": {name: value}} for every name of `outputs` (a name nothing wrote keeps the value it was read with, else None)"""
    ctx = context_of(inputs)
    _run_nodes([construct], ctx, call, limits or Limits(), None)
    return {"outputs": {name: ctx.get(name) for name in outputs}}


def _run_nodes(nodes, ctx, call, limits, item):
    for node in nodes:
        _run_node(node, ctx, call, limits, item)


def _run_node(node, ctx, call, limits, item):
    limits.guard()
    try:
        if "use" in node:
            value = call(node["use"], resolve(node.get("wire") or {}, ctx))
        else:
            value = _CONSTRUCTS[node["kind"]](node, ctx, call, limits, item)
    except (Stopped, BudgetExceeded):
        raise
    except Exception as exc:
        message = str(exc) if isinstance(exc, NodeError) else "%s: %s" % (type(exc).__name__, exc)
        policy = node.get("on_error", "fail")
        if policy == "fail":
            raise NodeError("%s: %s" % (node["id"], message))
        value = node.get("default") if policy == "default" else None
    if node.get("output") and node.get("kind") != "map":
        ctx[node["output"]] = value


def _branch(node, ctx, call, limits, item):
    _run_nodes(node.get("then" if test_condition(node["if"], ctx) else "else") or [], ctx, call, limits, item)


def _loop(node, ctx, call, limits, item):
    for _ in range(node["max"]):
        _run_nodes(node["body"], ctx, call, limits, item)
        if node.get("until") is not None and test_condition(node["until"], ctx):
            break


def _map(node, ctx, call, limits, item):
    values = resolve(node["over"], ctx)
    if not isinstance(values, (list, tuple)):
        raise NodeError("'over' must be a list")
    results = [None] * len(values)

    def one(index):
        sub = dict(ctx)
        sub[node["as"]] = values[index]
        sub["index"] = index
        _run_nodes(node["body"], sub, call, limits, index)
        results[index] = sub.get(node.get("collect")) if node.get("collect") else sub.get(node["as"])
    workers = max(1, int(node.get("workers", 1)))
    if workers == 1 or len(values) < 2:
        for index in range(len(values)):
            one(index)
    else:
        contexts = [contextvars.copy_context() for _ in values]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for future in [pool.submit(contexts[i].run, one, i) for i in range(len(values))]:
                future.result()          # the first error, stop or budget end ends the run
    if node.get("output"):
        ctx[node["output"]] = results
    return results


_CONSTRUCTS = {"branch": _branch, "loop": _loop, "map": _map}
