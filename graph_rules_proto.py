"""PROTOTYPE (CP8; the core of G-V4.GRAPHAPI.RULES, pulled forward because the editor needs it): every broken rule of a graph, in one fixed order.

rule_report(graph) -> [{"rule", "parts", "text"}] for each broken rule, in this order (an empty list: the graph keeps all rules):
  1 step_identity          a step ID that is empty, contains a slash, or is used twice
  2 step_kind              a step that is neither data, processing nor loop-controlling
  3 connection_endpoints   a connection to a step that does not exist
  4 duplicate_connection   a connection ID or an identical connection used twice
  5 adjacency              a connection between two data steps, or between two steps that are not data
  6 single_writer          a data step that more than one step writes
  7 stop_limit             a loop-controlling step without a valid stop limit
  8 cycle                  the steps cannot be put in an order
`graph` is {"nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]} with local IDs.
"""
try:
    from .graph_model import find_cycle, stop_is_valid
except ImportError:
    from graph_model import find_cycle, stop_is_valid

KINDS = ("data", "transform", "master")
TEXTS = {
    "step_identity": "a step has an empty name, a name with a slash, or a name used twice",
    "step_kind": "a step is not a data, processing or loop-controlling step",
    "connection_endpoints": "a connection leads to or from a step that does not exist",
    "duplicate_connection": "the same connection is there twice",
    "adjacency": "a connection joins two data steps or two steps that are not data",
    "single_writer": "a piece of data is written by more than one step",
    "stop_limit": "a loop-controlling step has no valid stop limit",
    "cycle": "the steps run in a circle",
}


def _kind(node):
    return (node.get("data") or {}).get("type")


def rule_report(graph):
    nodes, edges = graph.get("nodes", []), graph.get("edges", [])
    report = []

    def add(rule, parts):
        if parts:
            report.append({"rule": rule, "parts": list(dict.fromkeys(parts)), "text": TEXTS[rule]})

    ids = [n.get("id") for n in nodes]
    seen, bad = set(), []
    for i in ids:
        if not isinstance(i, str) or not i or "/" in i or i in seen:
            bad.append(str(i))
        seen.add(i)
    add("step_identity", bad)
    add("step_kind", [str(n.get("id")) for n in nodes if _kind(n) not in KINDS])
    known = set(ids)
    add("connection_endpoints", [e.get("id") for e in edges if e.get("from") not in known or e.get("to") not in known])
    seen_edges, seen_ids, dup = set(), set(), []
    for e in edges:
        key = (e.get("from"), e.get("to"), (e.get("data") or {}).get("role"), (e.get("data") or {}).get("as"))
        if key in seen_edges or e.get("id") in seen_ids:
            dup.append(e.get("id"))
        seen_edges.add(key); seen_ids.add(e.get("id"))
    add("duplicate_connection", dup)
    kinds = {n.get("id"): _kind(n) for n in nodes}
    add("adjacency", [e["id"] for e in edges if e.get("from") in kinds and e.get("to") in kinds and (kinds[e["from"]] == "data") == (kinds[e["to"]] == "data")])
    writers = {}
    for e in edges:
        if kinds.get(e.get("to")) == "data" and e.get("from") in kinds:
            writers.setdefault(e["to"], set()).add(e["from"])
    add("single_writer", [d for d, w in writers.items() if len(w) > 1])
    add("stop_limit", [n["id"] for n in nodes if _kind(n) == "master" and not stop_is_valid((n.get("data") or {}).get("stop"))])
    if not report or all(r["rule"] != "connection_endpoints" and r["rule"] != "step_identity" for r in report):
        cycle = find_cycle([i for i in ids if isinstance(i, str)], [e for e in edges if e.get("from") in known and e.get("to") in known])
        add("cycle", cycle or [])
    return report
