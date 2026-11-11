"""Graph model of a workflow graph (N-2.3, G-V2.MODEL T-01): the rules of REQ-WFM-043 to 049 and the stored graph.

- GraphModel(tables): `tables` has put(table, id, doc) -> version, get(table, id, version=None), versions(table, id).
- save_graph(graph) -> SaveResult(saved, version, named): `named` lists the IDs a refusal names (a node, an edge, a data node, or a cycle as IDs).
- read_graph(graph_id, version=None) -> the stored graph dict.
- topological_order(graph_id) -> the node IDs of a stored graph in an order in which every edge points forward.

Node fields are the proposal of goal.md: data nodes `value`, `parameters`; transform and master `toolbox_id`; master `stop`
({"max_repetitions": n} and/or {"max_seconds": s}, the names of IF-301 v2). The cycle search is a plain depth-first search, so no new dependency is needed.
"""

import math
from collections import namedtuple

try:
    from . import graph_tables
    from .storage import StorageError
except ImportError:  # used as plain script / in tests
    import graph_tables
    from storage import StorageError

# `rule` and `detail` are those of a StorageError("invalid") of the record checks (as StoreResult of skill_record.py); None for a refusal of the graph rules.
SaveResult = namedtuple("SaveResult", "saved version named rule detail", defaults=(None, None))

TABLE = "workflow_graphs"      # the table of the fake; the real Storage keeps the graph as records
HEADER = ("context_graph_id", "testbench_id", "description")
NODE_TYPES = ("data", "transform", "master")


def _refuse(named):
    return SaveResult(False, None, list(named))


def _node_type(node):
    return node.get("data", {}).get("type")


def find_cycle(ids, edges):
    """One cycle as node IDs, first ID repeated at the end, or None. Iterative, so a long chain does not depend on the Python stack (F-12)."""
    following = {i: [] for i in ids}
    for edge in edges:
        following[edge["from"]].append(edge["to"])
    state = {}      # 1 = on the current path, 2 = done
    path = []
    for root in ids:
        if root in state:
            continue
        state[root] = 1
        path.append(root)
        walk = [iter(following[root])]      # one iterator of followers per node on the path
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
    """A positive limit: a whole number from 1 when `whole` (2.0 counts, as in the Storage layer), else a finite number above 0; a boolean is none."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if whole:
        return value >= 1 and (isinstance(value, int) or value.is_integer())
    # an int is finite by nature and float() fails for one above the float range, so only a float is asked (F-19); the Storage layer accepts such a number
    return value > 0 and (isinstance(value, int) or math.isfinite(value))


def stop_is_valid(stop):
    """True when `stop` is a valid stop of a master node (IF-301 v2, REQ-WFM-048): an object with `max_repetitions` (whole number, at least 1) and/or
    `max_seconds` (finite number above 0), at least one of them, each one that is there valid (null is not valid); other keys are ignored. Kept here, not
    taken from the Storage layer: T-01 does not depend on STORE (D-262)."""
    if not isinstance(stop, dict) or not ({"max_repetitions", "max_seconds"} & stop.keys()):
        return False
    return ("max_repetitions" not in stop or _limit(stop["max_repetitions"], True)) and ("max_seconds" not in stop or _limit(stop["max_seconds"], False))


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
    # REQ-WFM-048: a master node has a maximum of repetitions or a maximum time (`max_seconds`)
    bad = [i for i, n in nodes.items() if _node_type(n) == "master" and not stop_is_valid(n["data"].get("stop"))]
    if bad:
        return bad
    # REQ-WFM-047: no cycle
    return find_cycle(list(nodes), edges) or []


def order_of(graph):
    """The node IDs of a graph dict in an order in which every edge points forward (also used by the run, N-2.4.1)."""
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


class GraphModel:
    """`tables` is the real Storage layer (IF-102, tables graph_nodes, graph_edges and graphs of IF-301 v2) or the minimal fake of the red tests (TR-MODEL-001).
    On the Storage layer a graph is node records, edge records and a header that pins the version of each member; the caller gives the `author` of a write."""

    def __init__(self, tables, author=None):
        self.tables = tables
        self.author = author
        self.real = hasattr(tables, "ids")

    def save_graph(self, graph):
        named = check_graph(graph)
        if named:
            return _refuse(named)
        if not self.real:
            return SaveResult(True, self.tables.put(TABLE, graph["id"], graph), [])
        # A record the record checks refuse is a refused result like a broken graph rule; other errors raise. Members written before the refusal stay as
        # unused versions of their records (the header, which makes them a graph, is not written).
        for node in graph["nodes"]:     # a broken node is found before anything is written
            broken = graph_tables.check_record("graph_nodes", node, record_id=node["id"])
            if broken:
                return SaveResult(False, None, [], broken["rule"], broken["detail"])
        try:
            members = {name: [{"id": m["id"], "version": self.tables.put(table, m["id"], m, self.author)["version"]} for m in graph[name]]
                       for name, table in (("nodes", "graph_nodes"), ("edges", "graph_edges"))}
            data = {"kind": "workflow", **members, **{key: graph[key] for key in HEADER}}
            version = self.tables.put("graphs", graph["id"], {"id": graph["id"], "data": data}, self.author)["version"]
        except StorageError as refusal:
            if refusal.code != "invalid":
                raise
            return SaveResult(False, None, [], refusal.rule, refusal.detail)
        return SaveResult(True, version, [])

    def read_graph(self, graph_id, version=None):
        if not self.real:
            return self.tables.get(TABLE, graph_id, version)
        header = self.tables.get("graphs", graph_id, version)["doc"]
        data = header["data"]
        pinned = lambda table, members: [self.tables.get(table, m["id"], m["version"])["doc"] for m in members]    # noqa: E731
        return {"id": header["id"], **{key: data[key] for key in HEADER},
                "nodes": pinned("graph_nodes", data["nodes"]), "edges": pinned("graph_edges", data["edges"])}

    def topological_order(self, graph_id):
        return order_of(self.read_graph(graph_id))
