"""Graph model of a workflow graph (N-2.3, G-V2.MODEL T-01): the rules of REQ-WFM-043 to 049 and the stored graph.

- GraphModel(tables): `tables` has put(table, id, doc) -> version, get(table, id, version=None), versions(table, id).
- save_graph(graph) -> SaveResult(saved, version, named): `named` lists the IDs a refusal names (a node, an edge, a data node, or a cycle as IDs).
- read_graph(graph_id, version=None) -> the stored graph dict.
- topological_order(graph_id) -> the node IDs of a stored graph in an order in which every edge points forward.

Node fields are the proposal of goal.md: data nodes `value`, `parameters`; transform and master `toolbox_id`; master `stop`
({"max_repetitions": n} and/or {"max_time": s}). The cycle search is a plain depth-first search, so no new dependency is needed.
"""

from collections import namedtuple

SaveResult = namedtuple("SaveResult", "saved version named")

TABLE = "workflow_graphs"
NODE_TYPES = ("data", "transform", "master")


def _refuse(named):
    return SaveResult(False, None, list(named))


def _node_type(node):
    return node.get("data", {}).get("type")


def _find_cycle(ids, edges):
    """One cycle as node IDs, first ID repeated at the end, or None."""
    following = {i: [] for i in ids}
    for edge in edges:
        following[edge["from"]].append(edge["to"])
    state = {}      # 1 = on the current path, 2 = done
    path = []

    def visit(node):
        state[node] = 1
        path.append(node)
        for nxt in following[node]:
            if state.get(nxt) == 1:
                return path[path.index(nxt):] + [nxt]
            if nxt not in state:
                found = visit(nxt)
                if found:
                    return found
        path.pop()
        state[node] = 2
        return None

    for node in ids:
        if node not in state:
            found = visit(node)
            if found:
                return found
    return None


def check_graph(graph):
    """IDs a refusal names, or [] when the graph keeps all rules."""
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    # REQ-WFM-043: only data, transform and master nodes
    bad = [i for i, n in nodes.items() if _node_type(n) not in NODE_TYPES]
    if bad:
        return bad
    # REQ-WFM-045: data nodes alternate with transform or master nodes
    bad = [e["id"] for e in edges
           if e["from"] not in nodes or e["to"] not in nodes
           or (_node_type(nodes[e["from"]]) == "data") == (_node_type(nodes[e["to"]]) == "data")]
    if bad:
        return bad
    # REQ-WFM-046: a data node has at most one writer
    writers = {}
    for e in edges:
        if _node_type(nodes[e["to"]]) == "data":
            writers.setdefault(e["to"], set()).add(e["from"])
    bad = [i for i, w in writers.items() if len(w) > 1]
    if bad:
        return bad
    # REQ-WFM-048: a master node has a maximum of repetitions or a maximum time
    bad = [i for i, n in nodes.items()
           if _node_type(n) == "master" and not (n["data"].get("stop") or {}).get("max_repetitions")
           and not (n["data"].get("stop") or {}).get("max_time")]
    if bad:
        return bad
    # REQ-WFM-047: no cycle
    return _find_cycle(list(nodes), edges) or []


class GraphModel:
    def __init__(self, tables):
        self.tables = tables

    def save_graph(self, graph):
        named = check_graph(graph)
        if named:
            return _refuse(named)
        return SaveResult(True, self.tables.put(TABLE, graph["id"], graph), [])

    def read_graph(self, graph_id, version=None):
        return self.tables.get(TABLE, graph_id, version)

    def topological_order(self, graph_id):
        graph = self.read_graph(graph_id)
        waiting = {n["id"]: 0 for n in graph["nodes"]}
        following = {i: [] for i in waiting}
        for e in graph["edges"]:
            waiting[e["to"]] += 1
            following[e["from"]].append(e["to"])
        order = [i for i, w in waiting.items() if w == 0]
        for node in order:      # the list grows while it is walked
            for nxt in following[node]:
                waiting[nxt] -= 1
                if waiting[nxt] == 0:
                    order.append(nxt)
        return order
