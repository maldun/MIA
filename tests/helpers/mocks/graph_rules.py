"""The graph rules of FR-7 for the mocks of IF-102 and IF-104 (protected).

A workflow is {"nodes": [{"id", "kind": "process" | "data", "session": bool, "stop": {"max_cycles", "max_seconds"}}],
               "edges": [{"from", "to"}]}.
This is the mock's own small copy of the rules; the real implementation is written in N-2.3 and tested against the same suite.
"""


def violation(doc):
    """Return (rule, detail) for the first broken rule, or None. Rules: node_identity, adjacent_data_nodes,
    adjacent_process_nodes, session_stopping_criterion, cycle (detail: the cycle as a list of ids)."""
    nodes = doc.get("nodes") if isinstance(doc, dict) else None
    edges = doc.get("edges") if isinstance(doc, dict) else None
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return "node_identity", "nodes and edges must be lists"
    kind = {}
    for node in nodes:
        nid = node.get("id") if isinstance(node, dict) else None
        if not nid or not isinstance(nid, str) or nid in kind or node.get("kind") not in ("process", "data"):
            return "node_identity", nid
        kind[nid] = node
    for edge in edges:
        a, b = edge.get("from"), edge.get("to")
        if a not in kind or b not in kind:
            return "node_identity", "%s->%s" % (a, b)
        if kind[a]["kind"] == "data" and kind[b]["kind"] == "data":
            return "adjacent_data_nodes", "%s->%s" % (a, b)
        if kind[a]["kind"] == "process" and kind[b]["kind"] == "process":
            return "adjacent_process_nodes", "%s->%s" % (a, b)
    for nid, node in kind.items():
        stop = node.get("stop") or {}
        if node["kind"] == "process" and node.get("session") and not (stop.get("max_cycles") or stop.get("max_seconds")):
            return "session_stopping_criterion", nid
    cycle = _cycle(list(kind), edges)
    if cycle:
        return "cycle", cycle
    return None


def _cycle(ids, edges):
    out = {i: [] for i in ids}
    for edge in edges:
        out[edge["from"]].append(edge["to"])
    state, stack = {}, []

    def visit(i):
        state[i] = 1
        stack.append(i)
        for j in out[i]:
            if state.get(j) == 1:
                return stack[stack.index(j):] + [j]
            if j not in state:
                found = visit(j)
                if found:
                    return found
        stack.pop()
        state[i] = 2
        return None

    for i in ids:
        if i not in state:
            found = visit(i)
            if found:
                return found
    return None
