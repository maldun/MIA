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
MEMBER_TABLES = {"workflow": ("graph_nodes", "graph_edges"), "context": ("context_nodes", "context_edges")}     # the kind selects the tables (REQ-WFM-152)
NODE_TYPES = ("data", "transform", "master")


def context_problems(graph):
    """The IDs a refusal names for a context graph: a step ID used twice, a connection ID used twice, a connection to a step that is not there
    (REQ-WFM-155). Nothing else: the order, alternation, writer and stop rules are those of workflow graphs (REQ-WFM-156); CONTEXT may add rules."""
    seen, bad = set(), []
    for node in graph["nodes"]:
        if node["id"] in seen:
            bad.append(node["id"])
        seen.add(node["id"])
    used = set()
    for edge in graph["edges"]:
        if edge["id"] in used or edge["from"] not in seen or edge["to"] not in seen:
            bad.append(edge["id"])
        used.add(edge["id"])
    return list(dict.fromkeys(bad))


def _kind(graph):
    """The kind of a graph: `workflow` when it has none (REQ-WFM-153), None when it is not one of the two kinds (REQ-WFM-154)."""
    kind = graph.get("kind", "workflow")
    return kind if isinstance(kind, str) and kind in MEMBER_TABLES else None


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
        kind = _kind(graph)
        if kind is None:
            return SaveResult(False, None, [], "schema_break", "kind")
        named = check_graph(graph) if kind == "workflow" else context_problems(graph)
        if named:
            return _refuse(named)
        if not self.real:
            return SaveResult(True, self.tables.put(TABLE, graph["id"], graph), [])
        nodes, edges = self._scoped(graph)
        refused = self._first_refusal(graph, kind, nodes, edges)
        if refused:
            return refused
        try:
            return self._write(graph, kind, nodes, edges)
        except StorageError as refusal:     # a record the Storage layer refuses after all is a refused result; other errors raise
            if refusal.code != "invalid":
                raise
            return SaveResult(False, None, [], refusal.rule, refusal.detail)

    def _scoped(self, graph):
        """The record form of the steps and connections: every ID, and the ends of a connection, as `<graph id>/<local id>` (REQ-WFM-144, REQ-GTB-029)."""
        scoped = lambda local: graph_tables.scoped(graph["id"], local)      # noqa: E731
        nodes = [{**n, "id": scoped(n["id"])} for n in graph["nodes"]]
        edges = [{**e, "id": scoped(e["id"]), "from": scoped(e["from"]), "to": scoped(e["to"])} for e in graph["edges"]]
        return nodes, edges

    def _first_refusal(self, graph, kind, nodes, edges):
        """The refused result for the first record the Storage layer would refuse, or None, found before anything is written (REQ-WFM-146, REQ-WFM-150).
        The header is tried with every member at version 1: that catches a graph ID with a slash through its steps (REQ-WFM-160)."""
        node_table, edge_table = MEMBER_TABLES[kind]
        stored = {("context_nodes" if kind == "context" else "nodes"): {n["id"]: [1] for n in nodes}}
        checks = [(node_table, n, None) for n in nodes] + [(edge_table, e, stored) for e in edges]
        trial = {"kind": kind, "nodes": [{"id": n["id"], "version": 1} for n in nodes], "edges": [{"id": e["id"], "version": 1} for e in edges],
                 **{key: graph[key] for key in HEADER}}
        checks.append(("graphs", {"id": graph["id"], "data": trial}, None))
        for table, record, known in checks:
            broken = graph_tables.check_record(table, record, record_id=record["id"], stored=known)
            if broken:
                return SaveResult(False, None, [], broken["rule"], broken["detail"])
        return None

    def _write(self, graph, kind, nodes, edges):
        """Members first, each only when it differs from its newest version (REQ-WFM-148), the header last (REQ-WFM-147); an unchanged graph writes
        nothing (REQ-WFM-149). Repeating an interrupted save finds the members already written and adds the one header version (REQ-WFM-151)."""
        pins = {}
        for key, table, records in zip(("nodes", "edges"), MEMBER_TABLES[kind], (nodes, edges)):
            pins[key] = []
            for record in records:
                latest = self._latest(table, record["id"])
                same = latest is not None and latest["doc"] == record
                pins[key].append({"id": record["id"], "version": latest["version"] if same else self.tables.put(table, record["id"], record, self.author)["version"]})
        data = {"kind": kind, **pins, **{key: graph[key] for key in HEADER}}
        head = self._latest("graphs", graph["id"])
        if head is not None and head["doc"]["data"] == data:
            return SaveResult(True, head["version"], [])
        return SaveResult(True, self.tables.put("graphs", graph["id"], {"id": graph["id"], "data": data}, self.author)["version"], [])

    def _latest(self, table, record_id):
        """The newest version of a record, or None when it is not stored."""
        try:
            return self.tables.get(table, record_id)
        except StorageError as err:
            if err.code == "not_found":
                return None
            raise

    def read_graph(self, graph_id, version=None):
        if not self.real:
            return self.tables.get(TABLE, graph_id, version)
        # the members exactly as the header of that version pinned them (REQ-WFM-159), with the graph ID taken off every ID and end (REQ-WFM-144)
        header = self.tables.get("graphs", graph_id, version)["doc"]
        data = header["data"]
        local = lambda record_id: graph_tables.split_scoped(record_id)[1]      # noqa: E731

        def member(table, pin):
            doc = self.tables.get(table, pin["id"], pin["version"])["doc"]
            ends = {end: local(doc[end]) for end in ("from", "to") if end in doc}
            return {**doc, "id": local(doc["id"]), **ends}
        node_table, edge_table = MEMBER_TABLES[data["kind"]]
        kind = {"kind": "context"} if data["kind"] == "context" else {}        # a workflow graph keeps the shape it had before (REQ-WFM-157)
        return {"id": header["id"], **kind, **{key: data[key] for key in HEADER},
                "nodes": [member(node_table, pin) for pin in data["nodes"]], "edges": [member(edge_table, pin) for pin in data["edges"]]}

    def graph_versions(self, graph_id):
        """The versions of a stored graph, oldest first: [{"version", "author", "time"}] (REQ-WFM-158)."""
        return self.tables.history("graphs", graph_id)

    def step_history(self, graph_id, local_id):
        """The versions of one step or connection of ONE graph as the headers of that graph pinned them, oldest first, with account and time
        (REQ-WFM-145): a step of another graph with the same local ID, and a version an interrupted save left unused, are not listed."""
        record_id = graph_tables.scoped(graph_id, local_id)
        pinned = []
        for entry in self.tables.history("graphs", graph_id):
            data = self.tables.get("graphs", graph_id, entry["version"])["doc"]["data"]
            for key, table in zip(("nodes", "edges"), MEMBER_TABLES[data["kind"]]):
                pinned += [(table, pin["version"]) for pin in data[key] if pin["id"] == record_id and (table, pin["version"]) not in pinned]
        stored = {table: {e["version"]: e for e in self.tables.history(table, record_id)} for table in {t for t, _ in pinned}}
        return [stored[table][version] for table, version in sorted(pinned, key=lambda p: p[1])]

    def topological_order(self, graph_id):
        return order_of(self.read_graph(graph_id))
