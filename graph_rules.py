"""
The graph rules of FR-7, shared by the Graph tables (IF-301) and the workflow management (REQ-GTB-002).

A workflow or context graph is {"nodes": [{"id", "kind": "process" | "data", "session": bool, "stop": {"max_cycles", "max_seconds"}}],
                                "edges": [{"from", "to"}]}.

  R1  node_identity               every node has a unique, non-empty text id and a kind; every edge joins two known ids
  R2  adjacent_data_nodes         no edge joins two data nodes (two processes that read the same input share one data node)
  R3  adjacent_process_nodes      no edge joins two process nodes
  R4  session_stopping_criterion  a session node has a positive max_cycles or max_seconds
  R5  cycle                       the graph is a DAG; a cycle is reported by its ids, the first repeated at the end

violation() reports the first broken rule in this order, so the caller (and the user) always sees the same one.
"""

KINDS = ("process", "data")


def violation(doc):
    """Return (rule, detail) for the first broken rule, or None for a valid graph."""
    nodes = doc.get("nodes") if isinstance(doc, dict) else None
    edges = doc.get("edges") if isinstance(doc, dict) else None
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return "node_identity", "nodes and edges must be lists"
    kind = {}
    for node in nodes:
        nid = node.get("id") if isinstance(node, dict) else None
        if not nid or not isinstance(nid, str) or nid in kind or node.get("kind") not in KINDS:
            return "node_identity", nid
        kind[nid] = node
    for edge in edges:
        a, b = (edge.get("from"), edge.get("to")) if isinstance(edge, dict) else (None, None)
        if a not in kind or b not in kind:
            return "node_identity", "%s->%s" % (a, b)
        if kind[a]["kind"] == kind[b]["kind"]:
            return ("adjacent_data_nodes" if kind[a]["kind"] == "data" else "adjacent_process_nodes"), "%s->%s" % (a, b)
    for nid, node in kind.items():
        stop = node.get("stop") or {}
        if node["kind"] == "process" and node.get("session") and not (stop.get("max_cycles") or stop.get("max_seconds")):
            return "session_stopping_criterion", nid
    cycle = _cycle(list(kind), edges)
    return ("cycle", cycle) if cycle else None


def _cycle(ids, edges):
    """A cycle as a list of ids with the first repeated at the end, or None. Iterative, so a long chain does not hit the recursion limit."""
    out = {i: [] for i in ids}
    for edge in edges:
        out[edge["from"]].append(edge["to"])
    state, path = {}, []                                   # state: 1 on the current path, 2 finished
    for start in ids:
        if start in state:
            continue
        stack = [(start, iter(out[start]))]
        state[start] = 1
        path.append(start)
        while stack:
            node, successors = stack[-1]
            for nxt in successors:
                if state.get(nxt) == 1:
                    return path[path.index(nxt):] + [nxt]
                if nxt not in state:
                    state[nxt] = 1
                    path.append(nxt)
                    stack.append((nxt, iter(out[nxt])))
                    break
            else:
                state[node] = 2
                path.pop()
                stack.pop()
    return None
