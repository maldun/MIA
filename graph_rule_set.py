"""The rule set of graphs in stored form (N-3.2 Graph tables, IF-301 v4, A-170; G-V4.GRAPHAPI.RULES T-01, REQ-GTB-033 to REQ-GTB-052).

The registry of kinds is the one place where the rules of a stored graph are written (FR-63, D-404): per kind its rules in a fixed order, and whether
a graph of that kind can run (FR-64).
  workflow: eight rules, local facts first and the cycle last (D-375); the cycle is asked only while rules 1 and 3 are kept (Q-5)
  context:  rules 1, 3 and 4 of the same definitions (Q-3); a context graph cannot run

kinds()                       -> {kind: {"rules": [...], "runs": bool}}, a copy
rule_report(graph)            -> [{"rule", "parts", "text"}], every broken rule in the registry's order; [] when every rule is kept
run_check(graph, given=None)  -> {"status": "refused" | "ready", "broken": [{"kind", "rule", "parts", "text", ...}]}
load(graph)                   -> networkx.MultiDiGraph of the well-formed steps and connections (IF-301 v5, A-187)
order_of(graph)               -> the step IDs, every step after the steps it reads from (REQ-WFM-166, 167; moved here by A-190)

`graph` is {"kind"?, "nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]} with local IDs; no `kind` means workflow (REQ-GTB-038).
Any input gives an answer, never an exception (REQ-GTB-040, D-418 (2)). The document form keeps graph_rules.py (Q-6).
Since IF-301 v5 (G-V4.GRAPHAPI.RUN): rules 1 to 4 read the stored form, where malformed items are seen; the others and the unsupplied inputs read
the loaded graph of `load` (REQ-GTB-059), its connections in their stored order.
Adapted from the prototype graph_rules_proto.py (reuse map R3).
"""
import copy
import math

import networkx

KINDS = {
    "workflow": {"rules": ["step_identity", "step_kind", "connection_endpoints", "duplicate_connection", "adjacency", "single_writer", "stop_limit", "cycle"],
                 "runs": True},
    "context": {"rules": ["step_identity", "connection_endpoints", "duplicate_connection"], "runs": False},
}
TEXTS = {
    "step_identity": "a step has an empty name or a name used twice",
    "step_kind": "a step is not a data, processing or loop-controlling step",
    "connection_endpoints": "a connection leads to or from a step that does not exist",
    "duplicate_connection": "the same connection is there twice",
    "adjacency": "a connection joins two data steps or two steps that are not data",
    "single_writer": "a piece of data is written by more than one step",
    "stop_limit": "a session setting is wrong: a data step holds a stop or session setting, a step has more than one settings connection, "
                  "or a loop-controlling step has no valid stop limit",
    "cycle": "the steps run in a circle",
    "unknown_kind": "the program does not know this kind of graph",
    "kind_cannot_run": "a graph of this kind cannot run",
    "unsupplied_input": "an input of the step has no writer, no start value in the graph and no value given with the run",
}
STEP_TYPES = ("data", "transform", "master")


def kinds():
    """The registry of kinds (REQ-GTB-033 to 036); a copy, so a caller's change does not reach it."""
    return copy.deepcopy(KINDS)


def _text(value):
    return value if isinstance(value, str) else str(value)


def _data(item):
    """The data of a step or connection; data that is not an object counts as empty here (the record checks refuse it on save)."""
    data = item.get("data") if isinstance(item, dict) else None
    return data if isinstance(data, dict) else {}


def _type(step):
    return _data(step).get("type")


def _graph_kind(graph):
    """The kind of a graph: workflow when it names none, None when the kind is not in the registry."""
    kind = graph.get("kind", "workflow")
    return kind if isinstance(kind, str) and kind in KINDS else None


# The stop limit is a copy of check_record's in graph_model: importing it would tie N-3.2 to N-2.3 (plan T-01 of RULES).
def _limit(value, whole):
    """A positive limit: a whole number from 1 when `whole` (2.0 counts), else a finite number above 0; a boolean is none."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if whole:
        return value >= 1 and (isinstance(value, int) or value.is_integer())
    return value > 0 and (isinstance(value, int) or math.isfinite(value))


def _stop_is_valid(stop):
    """A valid stop of a master step, as check_record (REQ-WFM-048): max_repetitions and/or max_seconds, each one that is there valid."""
    if not isinstance(stop, dict) or not ({"max_repetitions", "max_seconds"} & stop.keys()):
        return False
    return ("max_repetitions" not in stop or _limit(stop["max_repetitions"], True)) and ("max_seconds" not in stop or _limit(stop["max_seconds"], False))


def _steps(nodes):
    """(parts of rule 1, the existing steps): a step that is not an object, has no non-empty text ID or repeats an earlier ID is rule 1."""
    bad, steps, seen = [], [], set()
    for node in nodes:
        sid = node.get("id") if isinstance(node, dict) else node
        if isinstance(node, dict) and isinstance(sid, str) and sid and sid not in seen:
            steps.append(node)
        else:
            bad.append(_text(sid))
        if isinstance(sid, str):
            seen.add(sid)
    return bad, steps


def _connections(edges, types):
    """(parts of rule 3, the connections that are objects): rule 3 is a connection that is not an object, whose ID is not a non-empty text
    (A-189: `load` leaves it out, so the rules on the loaded graph would not see it) or whose ends name no existing step."""
    bad, objects = [], []
    for edge in edges:
        well_formed = isinstance(edge, dict) and _loaded_id(edge) is not None and isinstance(edge.get("from"), str) \
            and isinstance(edge.get("to"), str) and edge["from"] in types and edge["to"] in types
        if not well_formed:
            bad.append(_text(edge.get("id") if isinstance(edge, dict) else edge))
        if isinstance(edge, dict):
            objects.append(edge)
    return bad, objects


def _view(graph):
    """The stored form read once for the rules that see malformed items (1 to 4), and the loaded graph for the others (REQ-GTB-059);
    `nodes` or `edges` that is not a list is rule 1 or rule 3 with that part (D-418 (2))."""
    nodes, edges = graph.get("nodes", []), graph.get("edges", [])
    identity, endpoints = [], []
    if not isinstance(nodes, list):
        identity, nodes = ["nodes"], []
    if not isinstance(edges, list):
        endpoints, edges = ["edges"], []
    bad_steps, steps = _steps(nodes)
    bad_edges, objects = _connections(edges, {s["id"] for s in steps})
    return {"identity": identity + bad_steps, "endpoints": endpoints + bad_edges, "steps": steps, "edges": objects, "loaded": load(graph)}


def _step_identity(view):
    return view["identity"]


def _step_kind(view):
    return [s["id"] for s in view["steps"] if _type(s) not in STEP_TYPES]


def _connection_endpoints(view):
    return view["endpoints"]


def _key(value):
    """A value of a connection as a set or dict key: text and numbers as they are, anything else (a list, an object) by its repr, so a malformed
    connection is compared instead of raising (REQ-GTB-040, Verify V-1)."""
    return value if value is None or isinstance(value, (str, int, float, bool)) else ("unhashable", repr(value))


def _duplicate_connection(view):
    seen_keys, seen_ids, doubled = set(), set(), []
    for edge in view["edges"]:
        key = tuple(_key(v) for v in (edge.get("from"), edge.get("to"), _data(edge).get("role"), _data(edge).get("as")))
        if key in seen_keys or _key(edge.get("id")) in seen_ids:
            doubled.append(_text(edge.get("id")))
        seen_keys.add(key)
        seen_ids.add(_key(edge.get("id")))
    return doubled


def _in_stored_order(loaded):
    """The connections of a loaded graph as (start, end, ID, attributes) in their stored order: networkx lists them grouped by start step."""
    return sorted(loaded.edges(keys=True, data=True), key=lambda edge: edge[3]["position"])


def _is_data(loaded, step_id):
    return loaded.nodes[step_id]["data"].get("type") == "data"


def _adjacency(view):
    loaded = view["loaded"]
    return [key for start, end, key, _ in _in_stored_order(loaded) if _is_data(loaded, start) == _is_data(loaded, end)]


def _single_writer(view):
    """Data steps with more than one writing step, in the order of the first connection into each (as v4)."""
    loaded = view["loaded"]
    written = [end for _, end, _, _ in _in_stored_order(loaded) if _is_data(loaded, end)]
    return [d for d in dict.fromkeys(written) if len(set(loaded.predecessors(d))) > 1]


def _stop_limit(view):
    """Three passes in the order of IF-301 v4: masters without a valid stop, data steps with a session setting, steps with two settings connections."""
    loaded = view["loaded"]
    steps = list(loaded.nodes(data="data"))
    settings = [end for _, end, _, attributes in _in_stored_order(loaded) if attributes["data"].get("role") == "settings"]
    return ([i for i, data in steps if data.get("type") == "master" and not _stop_is_valid(data.get("stop"))]
            + [i for i, data in steps if data.get("type") == "data" and ({"stop", "session"} & set(data))]
            + [i for i in dict.fromkeys(settings) if settings.count(i) > 1])


def _cycle(view):
    """Only while rules 1 and 3 are kept: an order needs known, unique steps (Q-5, REQ-GTB-048). The cycle as step IDs, first repeated at the end."""
    if view["identity"] or view["endpoints"]:
        return []
    try:
        found = networkx.find_cycle(view["loaded"])
    except networkx.NetworkXNoCycle:
        return []
    return [start for start, *_ in found] + [found[0][0]]


RULES = {"step_identity": _step_identity, "step_kind": _step_kind, "connection_endpoints": _connection_endpoints,
         "duplicate_connection": _duplicate_connection, "adjacency": _adjacency, "single_writer": _single_writer,
         "stop_limit": _stop_limit, "cycle": _cycle}


def _item(rule, parts):
    return {"rule": rule, "parts": parts, "text": TEXTS[rule]}


def rule_report(graph):
    """Every broken rule of the graph's kind, in the registry's order, never only the first (REQ-GTB-037 to 048)."""
    if not isinstance(graph, dict):
        return [_item("step_identity", ["graph"])]
    kind = _graph_kind(graph)
    if kind is None:
        return [_item("unknown_kind", [_text(graph.get("kind"))])]
    view = _view(graph)
    report = []
    for rule in KINDS[kind]["rules"]:
        parts = RULES[rule](view)
        if parts:   # a cycle keeps its first step repeated at the end; other parts are named once
            report.append(_item(rule, parts if rule == "cycle" else list(dict.fromkeys(parts))))
    return report


def _unsupplied(graph, given):
    """Every input of a transform or master step (a connection from a data step, not settings or order) whose data step has no writer, no value
    other than null in the graph and is not given; in the order of the connections, repeats kept (REQ-GTB-051)."""
    loaded = load(graph)
    found = []
    for source, target, _, attributes in _in_stored_order(loaded):
        if loaded.nodes[target]["data"].get("type") not in ("transform", "master") or not _is_data(loaded, source):
            continue
        if attributes["data"].get("role") in ("settings", "order"):
            continue
        if loaded.in_degree(source) == 0 and loaded.nodes[source]["data"].get("value") is None and source not in given:
            found.append({"kind": "input", **_item("unsupplied_input", [source]), "step": target, "input": source})
    return found


def _given_ids(given):
    """The data step IDs a run gives values for: the keys of a mapping, the items of a list or set. Anything else, and any item that cannot be an ID,
    counts as nothing given, so run_check never raises on the caller's argument either (IF-301 v4: "never raises"; T-01 finding, D-423)."""
    try:
        items = list(given or ())
    except TypeError:
        return set()
    return {i for i in items if isinstance(i, str)}


def run_check(graph, given=None):
    """What stops a run before its first step, in the order kind, rules, inputs (REQ-GTB-049 to 051, D-416 (3)).
    A kind that is unknown or cannot run is the only item; `given` counts by its keys, so a value of None counts as given."""
    if isinstance(graph, dict):
        kind = _graph_kind(graph)
        if kind is None or not KINDS[kind]["runs"]:
            rule = "unknown_kind" if kind is None else "kind_cannot_run"
            return {"status": "refused", "broken": [{"kind": "kind", **_item(rule, [_text(graph.get("kind"))])}]}
    broken = [{"kind": "rule", **r} for r in rule_report(graph)]
    if isinstance(graph, dict):
        broken += _unsupplied(graph, _given_ids(given))
    return {"status": "refused" if broken else "ready", "broken": broken}


def order_of(graph):
    """The step IDs of a stored graph, every step after the steps it reads from (REQ-WFM-166; also used by the run, N-2.4.1; here since A-190, REQ-RUN-047).

    A queue over the loaded graph (D-480): first the steps that read from no step, in their stored position, then each step as soon as the last
    connection into it is passed, in the stored order of the connections, so ties go first-ready-first (REQ-WFM-167), as before the loaded graph.
    """
    loaded = load(graph)
    open_inputs = dict(loaded.in_degree())
    order = [step for step, count in open_inputs.items() if count == 0]
    for step in order:      # the list grows while it is walked
        for _, nxt, _ in sorted(loaded.out_edges(step, data="position"), key=lambda edge: edge[2]):
            open_inputs[nxt] -= 1
            if open_inputs[nxt] == 0:
                order.append(nxt)
    return order

def _loaded_id(item):
    value = item.get("id") if isinstance(item, dict) else None
    return value if isinstance(value, str) and value else None


def load(graph):
    """IF-301 v5 (A-187): the stored form as one networkx MultiDiGraph, built from copies (REQ-GTB-053 to 058).

    A step is a node keyed by its ID, a connection an edge keyed by its ID (two connections between the same steps stay two edges); both carry `data`
    ({} when it is no object, D-481) and `position`, their index in the stored form, which orders ties (REQ-WFM-167). Malformed items are left out and
    nothing raises: the rule report names them from the stored form (REQ-GTB-057).
    """
    loaded = networkx.MultiDiGraph()
    if not isinstance(graph, dict):
        return loaded
    loaded.graph.update(copy.deepcopy({k: v for k, v in graph.items() if k not in ("nodes", "edges")}))
    loaded.graph.setdefault("kind", "workflow")
    nodes, edges = graph.get("nodes"), graph.get("edges")
    for position, step in enumerate(nodes if isinstance(nodes, list) else []):
        step_id = _loaded_id(step)
        if step_id is not None and step_id not in loaded:
            loaded.add_node(step_id, data=copy.deepcopy(_data(step)), position=position)
    seen = set()
    for position, connection in enumerate(edges if isinstance(edges, list) else []):
        edge_id = _loaded_id(connection)
        if edge_id is None or edge_id in seen:
            continue
        seen.add(edge_id)
        start, end = connection.get("from"), connection.get("to")
        if isinstance(start, str) and isinstance(end, str) and start in loaded and end in loaded:
            loaded.add_edge(start, end, key=edge_id, data=copy.deepcopy(_data(connection)), position=position)
    return loaded
