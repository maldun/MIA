"""PROTOTYPE CP11 (G-V4.REPLAY, FR-76, FR-77, FR-80): the record of the changes made to a graph, as entries that can be played back.

A change is {"op", "target", "before", "after", "reason"}:
  add_step / remove_step / change_step                 target = the step ID, before / after = the step's content (`data`); remove_step also lists the connections that went with it
  add_connection / remove_connection / change_connection   target = the connection ID, before / after = {"from", "to", "data"}
  restore                                              target = the version whose content was made current again (a restore is one entry)
apply_change(graph, change) -> a new graph; replay(start, changes) -> the graph after all of them; diff(before, after) -> the changes that lead from one graph to the other
(used when the editor sent none, and for the comparison of two versions). A graph is {"nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]}.
"""
import copy
import json

OPS = ("add_step", "remove_step", "change_step", "add_connection", "remove_connection", "change_connection", "restore")


def _clone(x):
    return copy.deepcopy(x)


def _link(e):
    return {"from": e["from"], "to": e["to"], "data": _clone(e.get("data") or {})}


def apply_change(graph, change, versions=None):
    """the graph after one change; ValueError names what does not fit (the change does not start from this graph). `versions(n)` gives an earlier version for a restore."""
    g = _clone(graph)
    op, target = change.get("op"), change.get("target")
    nodes = {n["id"]: n for n in g["nodes"]}
    edges = {e["id"]: e for e in g["edges"]}
    if op == "add_step":
        if target in nodes:
            raise ValueError("step %s exists" % target)
        g["nodes"].append({"id": target, "data": _clone(change["after"])})
    elif op == "remove_step":
        if target not in nodes:
            raise ValueError("no step %s" % target)
        g["nodes"] = [n for n in g["nodes"] if n["id"] != target]
        g["edges"] = [e for e in g["edges"] if e["from"] != target and e["to"] != target]
    elif op == "change_step":
        if target not in nodes:
            raise ValueError("no step %s" % target)
        nodes[target]["data"] = _clone(change["after"])
    elif op == "add_connection":
        if target in edges:
            raise ValueError("connection %s exists" % target)
        a = change["after"]
        g["edges"].append({"id": target, "from": a["from"], "to": a["to"], "data": _clone(a.get("data") or {})})
    elif op == "remove_connection":
        if target not in edges:
            raise ValueError("no connection %s" % target)
        g["edges"] = [e for e in g["edges"] if e["id"] != target]
    elif op == "change_connection":
        if target not in edges:
            raise ValueError("no connection %s" % target)
        a = change["after"]
        edges[target].update({"from": a["from"], "to": a["to"], "data": _clone(a.get("data") or {})})
    elif op == "restore":
        if versions is None:
            raise ValueError("a restore needs the earlier version")
        old = versions(target)
        g = {"nodes": _clone(old["nodes"]), "edges": _clone(old["edges"])}
    else:
        raise ValueError("unknown change %r" % (op,))
    return g


def replay(start, changes, versions=None):
    graph = {"nodes": _clone(start["nodes"]), "edges": _clone(start["edges"])}
    for change in changes:
        graph = apply_change(graph, change, versions)
    return graph


def canonical(graph):
    """the graph as text that does not depend on the order of its steps and connections"""
    return json.dumps({"nodes": sorted(({"id": n["id"], "data": n.get("data") or {}} for n in graph["nodes"]), key=lambda n: n["id"]),
                       "edges": sorted(({"id": e["id"], "from": e["from"], "to": e["to"], "data": e.get("data") or {}} for e in graph["edges"]), key=lambda e: e["id"])}, sort_keys=True)


def same(a, b):
    return canonical(a) == canonical(b)


def diff(before, after):
    """the changes that lead from `before` to `after`, in an order in which they can be applied: connections removed, steps removed, steps added, steps changed, connections added and changed"""
    bn, an = {n["id"]: n for n in before["nodes"]}, {n["id"]: n for n in after["nodes"]}
    be, ae = {e["id"]: e for e in before["edges"]}, {e["id"]: e for e in after["edges"]}
    out = []
    gone_steps = [i for i in bn if i not in an]
    for i, e in be.items():
        if (i not in ae) and e["from"] not in gone_steps and e["to"] not in gone_steps:
            out.append({"op": "remove_connection", "target": i, "before": _link(e), "after": None, "reason": None})
    for i in gone_steps:
        out.append({"op": "remove_step", "target": i, "before": _clone(bn[i].get("data") or {}), "after": None, "reason": None,
                    "connections": [{"id": k, **_link(e)} for k, e in be.items() if e["from"] == i or e["to"] == i]})
    for i in an:
        if i not in bn:
            out.append({"op": "add_step", "target": i, "before": None, "after": _clone(an[i].get("data") or {}), "reason": None})
    for i in an:
        if i in bn and (bn[i].get("data") or {}) != (an[i].get("data") or {}):
            out.append({"op": "change_step", "target": i, "before": _clone(bn[i].get("data") or {}), "after": _clone(an[i].get("data") or {}), "reason": None})
    for i, e in ae.items():
        if i not in be:
            out.append({"op": "add_connection", "target": i, "before": None, "after": _link(e), "reason": None})
        elif _link(be[i]) != _link(e):
            out.append({"op": "change_connection", "target": i, "before": _link(be[i]), "after": _link(e), "reason": None})
    return out


NAMES = {"add_step": "added step", "remove_step": "removed step", "change_step": "changed step", "add_connection": "added connection",
         "remove_connection": "removed connection", "change_connection": "changed connection", "restore": "restored version"}


def clean(change):
    """a change as it is recorded: only the known fields, text for the reason (anything the editor sent beyond that is dropped); ValueError if it is not a change"""
    if not isinstance(change, dict) or change.get("op") not in OPS or not isinstance(change.get("target"), (str, int)) or isinstance(change.get("target"), bool):
        raise ValueError("not a change")
    out = {"op": change["op"], "target": change["target"], "before": change.get("before"), "after": change.get("after")}
    reason = change.get("reason")
    out["reason"] = reason.strip() if isinstance(reason, str) and reason.strip() else None
    if change["op"] == "remove_step":
        out["connections"] = change.get("connections") if isinstance(change.get("connections"), list) else []
    if isinstance(change.get("note"), str):
        out["note"] = change["note"]
    return out
