"""The rule set of graphs in stored form (N-3.2 Graph tables, IF-301 v4, A-170; G-V4.GRAPHAPI.RULES T-01, REQ-GTB-033 to REQ-GTB-052).

The registry of kinds is the one place where the rules of a stored graph are written (FR-63, D-404): per kind its rules in a fixed order, and whether
a graph of that kind can run (FR-64).
  workflow: eight rules, local facts first and the cycle last (D-375); the cycle is asked only while rules 1 and 3 are kept (Q-5)
  context:  rules 1, 3 and 4 of the same definitions (Q-3); a context graph cannot run

kinds()                       -> {kind: {"rules": [...], "runs": bool}}, a copy
rule_report(graph)            -> [{"rule", "parts", "text"}], every broken rule in the registry's order; [] when every rule is kept
run_check(graph, given=None)  -> {"status": "refused" | "ready", "broken": [{"kind", "rule", "parts", "text", ...}]}

`graph` is {"kind"?, "nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]} with local IDs; no `kind` means workflow (REQ-GTB-038).
Any input gives an answer, never an exception (REQ-GTB-040, D-418 (2)). The document form keeps graph_rules.py (Q-6).
Adapted from the prototype graph_rules_proto.py (reuse map R3).
"""
import copy
import math

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


# find_cycle and the stop limit are copies of those in graph_model: importing them would tie N-3.2 to N-2.3 (plan T-01).
def _find_cycle(ids, edges):
    """One cycle as step IDs, first ID repeated at the end, or None. Iterative, so a long chain does not depend on the Python stack (F-12)."""
    following = {i: [] for i in ids}
    for edge in edges:
        following[edge["from"]].append(edge["to"])
    state, path = {}, []      # state: 1 = on the current path, 2 = done
    for root in ids:
        if root in state:
            continue
        state[root] = 1
        path.append(root)
        walk = [iter(following[root])]
        while walk:
            for nxt in walk[-1]:
                if state.get(nxt) == 1:
                    return path[path.index(nxt):] + [nxt]
                if nxt not in state:
                    state[nxt] = 1
                    path.append(nxt)
                    walk.append(iter(following[nxt]))
                    break
            else:
                state[path.pop()] = 2
                walk.pop()
    return None


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
    """(parts of rule 3, the connections that are objects, the connections between existing steps)."""
    bad, objects, valid = [], [], []
    for edge in edges:
        ends_known = isinstance(edge, dict) and isinstance(edge.get("from"), str) and isinstance(edge.get("to"), str) \
            and edge["from"] in types and edge["to"] in types
        if not ends_known:
            bad.append(_text(edge.get("id") if isinstance(edge, dict) else edge))
        if isinstance(edge, dict):
            objects.append(edge)
        if ends_known:
            valid.append(edge)
    return bad, objects, valid


def _view(graph):
    """The graph read once for every rule; `nodes` or `edges` that is not a list is rule 1 or rule 3 with that part (D-418 (2))."""
    nodes, edges = graph.get("nodes", []), graph.get("edges", [])
    identity, endpoints = [], []
    if not isinstance(nodes, list):
        identity, nodes = ["nodes"], []
    if not isinstance(edges, list):
        endpoints, edges = ["edges"], []
    bad_steps, steps = _steps(nodes)
    types = {s["id"]: _type(s) for s in steps}
    bad_edges, objects, valid = _connections(edges, types)
    return {"identity": identity + bad_steps, "endpoints": endpoints + bad_edges, "steps": steps, "types": types, "edges": objects, "valid": valid}


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


def _adjacency(view):
    types = view["types"]
    return [_text(e.get("id")) for e in view["valid"] if (types[e["from"]] == "data") == (types[e["to"]] == "data")]


def _single_writer(view):
    writers = {}
    for edge in view["valid"]:
        if view["types"][edge["to"]] == "data":
            writers.setdefault(edge["to"], set()).add(edge["from"])
    return [d for d, w in writers.items() if len(w) > 1]


def _stop_limit(view):
    """Three passes in the order of IF-301 v4: masters without a valid stop, data steps with a session setting, steps with two settings connections."""
    settings_in = {}
    for edge in view["edges"]:
        if _data(edge).get("role") == "settings":
            settings_in.setdefault(_key(edge.get("to")), []).append(edge.get("id"))
    steps = view["steps"]
    return ([s["id"] for s in steps if _type(s) == "master" and not _stop_is_valid(_data(s).get("stop"))]
            + [s["id"] for s in steps if _type(s) == "data" and ({"stop", "session"} & set(_data(s)))]
            + [_text(t[1] if isinstance(t, tuple) else t) for t, ids in settings_in.items() if len(ids) > 1])


def _cycle(view):
    """Only while rules 1 and 3 are kept: an order needs known, unique steps (Q-5, REQ-GTB-048)."""
    if view["identity"] or view["endpoints"]:
        return []
    return _find_cycle([s["id"] for s in view["steps"]], view["valid"]) or []


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
    view = _view(graph)
    steps = {s["id"]: s for s in view["steps"]}
    written = {e["to"] for e in view["valid"]}
    found = []
    for edge in view["valid"]:
        source, target = edge["from"], edge["to"]
        if _type(steps[target]) not in ("transform", "master") or _type(steps[source]) != "data":
            continue
        if _data(edge).get("role") in ("settings", "order"):
            continue
        if source not in written and _data(steps[source]).get("value") is None and source not in given:
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


def load(graph):
    """IF-301 v5: the stored form as one networkx MultiDiGraph (A-187). Not built yet: the stub of the red tests of G-V4.GRAPHAPI.RUN (REQ-GTB-053 to 058)."""
    raise NotImplementedError("load of IF-301 v5 is built in the loader task of G-V4.GRAPHAPI.RUN")
