"""Run of a workflow graph in topological order (N-2.4.1, G-V2.MODEL T-03 and T-04, G-V2.CONVERT T-CV-03a).

REQ-RUN-016 to 019 (order, refusals, failure) and REQ-RUN-030 to 034 (Stage: three-argument call, per-output writes, wiring checks, start values). The tests in tests/acceptance/test_graph_run.py fix this interface:
- GraphRunner(trust): `trust(node_id)` -> "trusted" or "untrusted" (stand-in for the toolbox of G-V2.TOOLBOX).
- run(graph, nodes, inputs) -> RunResult(status, named, named_status, values): `nodes` maps a transform or master node ID to a function
  of {input data node ID: value} that returns the value it writes; `inputs` maps data node IDs to their starting values.
  status is "done", "refused" (before any node ran: named = the node IDs, named_status = their status) or "failed" (named = [the failed node]);
  A graph the runner cannot put in an order is "refused" too, before any node ran (named = the edges to an unknown node, else the cycle as node IDs, named_status = None);
  `values` maps each data node ID to its value after the run.
- A function wrapped as Stage(function, prepare=None) is called as function(inputs, outputs, node) (A-124): inputs and outputs map the name
  (edge field `as`, else the data node ID) to the value of the data node, node is the settings object (the value of the input data node whose edge has
  `role: "settings"`, else {}). Start value of a data node: the run's `inputs`, else what `prepare(inputs, outputs, node)` returned under "inputs" or "outputs", else the
  `value` of the graph node, else None. A result {"outputs": {name: value}} (no other key) writes each output by name, any other result goes to every output node.
"""

from collections import namedtuple

try:
    from .graph_model import find_cycle, order_of
except ImportError:
    from graph_model import find_cycle, order_of

RunResult = namedtuple("RunResult", "status named named_status values")


class Stage:
    """Marks a function that wants the call function(inputs, outputs, node) instead of function({input data node id: value}) (A-124, REQ-RUN-030).
    `prepare(inputs, outputs, node)` may give default inputs and start values of outputs (REQ-RUN-034)."""

    def __init__(self, function, prepare=None):
        self.function, self.prepare = function, prepare


class GraphRunner:
    def __init__(self, trust):
        self.trust = trust

    def run(self, graph, nodes, inputs):
        kinds = {n["id"]: n["data"]["type"] for n in graph["nodes"]}
        # REQ-RUN-016: a graph without an order is not run (the writers of IF-102 do not run the graph rules, D-262)
        unknown = [e["id"] for e in graph["edges"] if e["from"] not in kinds or e["to"] not in kinds]
        cycle = None if unknown else find_cycle(list(kinds), graph["edges"])
        if unknown or cycle:
            return RunResult("refused", unknown or cycle, None, _data_values(kinds, dict(inputs)))
        reads = {i: [] for i in kinds}
        for edge in graph["edges"]:
            reads[edge["to"]].append(edge["from"])
        # REQ-RUN-017: check every transform and master node before the first one runs. Any status except "trusted"
        # counts as untrusted, so an unknown status never lets a node run.
        refused = {i: self.trust(i) for i, k in kinds.items() if k != "data"}
        refused = {i: s for i, s in refused.items() if s != "trusted"}
        if refused:
            named = [i for i in order_of(graph) if i in refused]
            return RunResult("refused", named, refused[named[0]], _data_values(kinds, dict(inputs)))
        bad = [i for i in order_of(graph) if isinstance(nodes.get(i), Stage) and _bad_wiring(graph["edges"], i)]
        if bad:
            return RunResult("refused", bad, None, _data_values(kinds, dict(inputs)))
        defaults = {n["id"]: n["data"].get("value") for n in graph["nodes"] if kinds[n["id"]] == "data"}
        values = dict(inputs)
        for node_id in order_of(graph):
            if kinds[node_id] == "data":
                continue
            # A master node runs once, like a transform; its stop criterion is stored and unused until debates (FR-39).
            try:
                if isinstance(nodes[node_id], Stage):
                    written = _run_stage(nodes[node_id], graph["edges"], node_id, values, defaults)
                else:
                    result = nodes[node_id]({d: values[d] for d in reads[node_id] if d in values})
                    written = {e["to"]: result for e in graph["edges"] if e["from"] == node_id}
            except Exception:
                return RunResult("failed", [node_id], None, _data_values(kinds, values))
            values.update(written)
        return RunResult("done", [], None, _data_values(kinds, values))


def _data_values(kinds, values):
    return {i: v for i, v in values.items() if kinds.get(i) == "data"}


def _is_settings(edge):
    return edge.get("data", {}).get("role") == "settings"


def _bad_wiring(edges, node_id):
    """REQ-RUN-033: more than one settings edge into the transform, or two output edges with the same name."""
    settings = [e for e in edges if e["to"] == node_id and _is_settings(e)]
    names = [_name(e, e["to"]) for e in edges if e["from"] == node_id]
    return len(settings) > 1 or len(names) != len(set(names))


def _name(edge, data_id):
    return edge.get("data", {}).get("as", data_id)


def _run_stage(stage, edges, node_id, values, defaults):
    """Build inputs, outputs and settings, call prepare once, call the function; returns {output data node id: value} to write."""
    reads = [(_name(e, e["from"]), e["from"]) for e in edges if e["to"] == node_id and not _is_settings(e)]
    writes = [(_name(e, e["to"]), e["to"]) for e in edges if e["from"] == node_id]
    settings = next((e["from"] for e in edges if e["to"] == node_id and _is_settings(e)), None)

    def start(data_id):     # the run beats prepare beats the graph (REQ-RUN-034); key presence counts, so a given None stays None
        return values[data_id] if data_id in values else defaults.get(data_id)

    inputs = {name: start(d) for name, d in reads}
    outputs = {name: start(d) for name, d in writes}
    node = start(settings) if settings else None
    node = {} if node is None else node
    if stage.prepare:
        prepared = stage.prepare(dict(inputs), dict(outputs), node) or {}
        for name, d in reads:
            if d not in values and name in (prepared.get("inputs") or {}):
                inputs[name] = prepared["inputs"][name]
        for name, d in writes:
            if d not in values and name in (prepared.get("outputs") or {}):
                outputs[name] = prepared["outputs"][name]
    result = stage.function(inputs, outputs, node)
    if isinstance(result, dict) and set(result) == {"outputs"}:
        by_name = dict(writes)
        # an unknown name raises, so the run fails this node (REQ-RUN-019)
        return {by_name[name]: value for name, value in result["outputs"].items()}
    return {d: result for _, d in writes}
