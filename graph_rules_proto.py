"""PROTOTYPE (CP8, CP17 of round 04; the core of G-V4.GRAPHAPI.RULES): every broken rule of a graph, in one fixed order, the rule set chosen by the kind of the graph.

KINDS is the one place (D-404, FR-63): per kind of graph its rules in their fixed order, and whether a graph of that kind can run (FR-64).
  workflow: the eight rules, local facts first and the cycle last (D-375)
  1 step_identity          a step ID that is empty or used twice (a slash is allowed: REQ-GTB-029)
  2 step_kind              a step that is neither data, processing nor loop-controlling
  3 connection_endpoints   a connection to a step that does not exist
  4 duplicate_connection   a connection ID or an identical connection used twice
  5 adjacency              a connection between two data steps, or between two steps that are not data
  6 single_writer          a data step that more than one step writes
  7 stop_limit             session settings: a data step that carries a session setting (`stop` or `session`), a step with more than one settings connection,
                           a loop-controlling step without a valid stop limit (ASM-3)
  8 cycle                  the steps cannot be put in an order
  context: identity and ends (REQ-WFM-155, 156) as rules 1, 3 and 4 of the same definitions; a context graph cannot run
A graph of a kind not in KINDS gives one item, `unknown_kind`, naming the kind (D-404).

check(graph) -> [{"rule", "parts", "text"}] for each broken rule, in order (an empty list: the graph keeps all rules); `rule_report` is the older name.
`graph` is {"kind"?, "nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]} with local IDs; no `kind` is `workflow` (REQ-WFM-153).
"""
try:
    from .graph_model import find_cycle, stop_is_valid
except ImportError:
    from graph_model import find_cycle, stop_is_valid

STEP_KINDS = ("data", "transform", "master")
KINDS = {
    "workflow": {"rules": ("step_identity", "step_kind", "connection_endpoints", "duplicate_connection", "adjacency", "single_writer", "stop_limit", "cycle"),
                 "runs": True},
    "context": {"rules": ("step_identity", "connection_endpoints", "duplicate_connection"), "runs": False},
}
TEXTS = {
    "step_identity": "a step has an empty name or a name used twice",
    "step_kind": "a step is not a data, processing or loop-controlling step",
    "connection_endpoints": "a connection leads to or from a step that does not exist",
    "duplicate_connection": "the same connection is there twice",
    "adjacency": "a connection joins two data steps or two steps that are not data",
    "single_writer": "a piece of data is written by more than one step",
    "stop_limit": "a session setting is wrong: a data step holds a stop or session setting, a step has more than one settings connection, or a loop-controlling step has no valid stop limit",
    "cycle": "the steps run in a circle",
    "unknown_kind": "the program does not know this kind of graph",
    "kind_cannot_run": "a graph of this kind cannot run",
}


def _data(item):
    """the data of a step or connection as an object; anything else counts as empty here, the record checks refuse it (CP17: a rule never raises)"""
    data = item.get("data") if isinstance(item, dict) else None
    return data if isinstance(data, dict) else {}


def _kind(node):
    return _data(node).get("type")


def graph_kind(graph):
    """the kind of a graph: `workflow` when it names none, None when the kind is not in KINDS"""
    kind = graph.get("kind", "workflow")
    return kind if isinstance(kind, str) and kind in KINDS else None


def _step_identity(nodes, edges, found):
    seen, bad = set(), []
    for i in (n.get("id") for n in nodes):
        # CP17: a slash is allowed in a local ID, as in CORE (REQ-GTB-029: the graph ID ends at the first slash); CP8 refused it
        if not isinstance(i, str) or not i or i in seen:
            bad.append(str(i))
        seen.add(i)
    return bad


def _step_kind(nodes, edges, found):
    return [str(n.get("id")) for n in nodes if _kind(n) not in STEP_KINDS]


def _connection_endpoints(nodes, edges, found):
    known = {n.get("id") for n in nodes}
    return [e.get("id") for e in edges if e.get("from") not in known or e.get("to") not in known]


def _duplicate_connection(nodes, edges, found):
    seen_edges, seen_ids, dup = set(), set(), []
    for e in edges:
        key = (e.get("from"), e.get("to"), _data(e).get("role"), _data(e).get("as"))
        if key in seen_edges or e.get("id") in seen_ids:
            dup.append(e.get("id"))
        seen_edges.add(key)
        seen_ids.add(e.get("id"))
    return dup


def _adjacency(nodes, edges, found):
    kinds = {n.get("id"): _kind(n) for n in nodes}
    return [e.get("id") for e in edges if e.get("from") in kinds and e.get("to") in kinds and (kinds[e.get("from")] == "data") == (kinds[e.get("to")] == "data")]


def _single_writer(nodes, edges, found):
    kinds = {n.get("id"): _kind(n) for n in nodes}
    writers = {}
    for e in edges:
        if kinds.get(e.get("to")) == "data" and e.get("from") in kinds:
            writers.setdefault(e.get("to"), set()).add(e.get("from"))
    return [d for d, w in writers.items() if len(w) > 1]


def _stop_limit(nodes, edges, found):
    settings_in = {}
    for e in edges:
        if _data(e).get("role") == "settings":
            settings_in.setdefault(e.get("to"), []).append(e.get("id"))
    return ([n.get("id") for n in nodes if _kind(n) == "master" and not stop_is_valid(_data(n).get("stop"))]
            + [n.get("id") for n in nodes if _kind(n) == "data" and ({"stop", "session"} & set(_data(n)))]
            + [t for t, ids in settings_in.items() if len(ids) > 1])


def _cycle(nodes, edges, found):
    # an order needs known, unique steps: with identity or ends broken the cycle is not asked (as in CP4)
    if {"connection_endpoints", "step_identity"} & {r["rule"] for r in found}:
        return []
    ids = [n.get("id") for n in nodes if isinstance(n.get("id"), str)]
    known = set(ids)
    return find_cycle(ids, [e for e in edges if e.get("from") in known and e.get("to") in known]) or []


RULES = {"step_identity": _step_identity, "step_kind": _step_kind, "connection_endpoints": _connection_endpoints,
         "duplicate_connection": _duplicate_connection, "adjacency": _adjacency, "single_writer": _single_writer,
         "stop_limit": _stop_limit, "cycle": _cycle}


def check(graph):
    kind = graph_kind(graph)
    if kind is None:
        return [{"rule": "unknown_kind", "parts": [str(graph.get("kind"))], "text": TEXTS["unknown_kind"]}]
    nodes, edges = graph.get("nodes", []), graph.get("edges", [])
    report = []
    for rule in KINDS[kind]["rules"]:
        parts = RULES[rule](nodes, edges, report)
        if parts:   # a cycle keeps its first step repeated at the end (REQ-WFM-047); other parts are named once
            report.append({"rule": rule, "parts": parts if rule == "cycle" else list(dict.fromkeys(parts)), "text": TEXTS[rule]})
    return report


rule_report = check


def missing_inputs(graph, given=None):
    """[{"step", "input"}]: an input of a processing or loop-controlling step (a connection from a data step that is neither a settings nor an order connection) whose data step
    has no writer (no connection into it), no start value in the graph and no value given with the run. Settings are optional (the step gets {} without them)."""
    given = given or {}
    nodes = {n.get("id"): n for n in graph.get("nodes", [])}
    edges = [e for e in graph.get("edges", []) if e.get("from") in nodes and e.get("to") in nodes]
    written = {e["to"] for e in edges}
    found = []
    for e in edges:
        if _kind(nodes[e["to"]]) not in ("transform", "master") or _kind(nodes[e["from"]]) != "data":
            continue
        if (e.get("data") or {}).get("role") in ("settings", "order"):
            continue
        source = nodes[e["from"]]
        has_value = (source.get("data") or {}).get("value") is not None
        if e["from"] not in written and not has_value and e["from"] not in given:
            found.append({"step": e["to"], "input": e["from"]})
    return found


def refusal(graph, given=None):
    """what stops a run, before any step runs: {"status": "refused" | "ready", "broken": [...]}.
    A kind the program does not know, or a kind that cannot run, is the only item (its rules say nothing about a run); otherwise every broken rule
    (in the fixed order), then every input nobody supplies."""
    kind = graph_kind(graph)
    if kind is None or not KINDS[kind]["runs"]:
        rule = "unknown_kind" if kind is None else "kind_cannot_run"
        named = str(graph.get("kind"))
        return {"status": "refused", "broken": [{"kind": "kind", "rule": rule, "parts": [named], "text": TEXTS[rule]}]}
    broken = [{"kind": "rule", **r} for r in check(graph)]
    broken += [{"kind": "input", "step": m["step"], "input": m["input"], "text": "an input of the step has no writer, no start value in the graph and no value given with the run", "parts": [m["input"]]}
               for m in missing_inputs(graph, given)]
    return {"status": "refused" if broken else "ready", "broken": broken}


def run_guarded(runner, graph, nodes, inputs):
    """the run of the existing runner behind the refusal: nothing is called when the graph is refused. Returns (result, refusal); the result is RunResult("refused", ...) then."""
    try:
        from .graph_run import RunResult
    except ImportError:
        from graph_run import RunResult
    said = refusal(graph, inputs)
    if said["status"] == "refused":
        named = list(dict.fromkeys(part for b in said["broken"] for part in b["parts"]))
        return RunResult("refused", named, None, {}), said
    return runner.run(graph, nodes, inputs), said
