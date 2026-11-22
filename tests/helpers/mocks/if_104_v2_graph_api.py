"""Mock of IF-104 v2, the graph API of the stored form for the Graph app (protected, amendment A-171).

Complexity 2: an in-process fake of the routes of `contracts/IF-104-graph-api.md` (v2), with the operations named as there. It keeps the
graphs, versions, arrangements and records of changes in dictionaries; it does not model concurrent requests, the login throttle or logout.

Fidelity (what the mock does NOT do like the real provider):
- rules: the mock knows three rules of IF-301 v4, in this order: `step_identity` (a step ID used twice), `connection_endpoints` (a connection
  to a step the graph does not have), `cycle`; the real provider asks IF-301 v4 `rule_report` with all rules of the kind. The rule texts are
  the mock's own; a contract case compares rule names and parts only.
- record checks: none (the real provider refuses with 422 `refused` where IF-301 `check_record` does).
- trust: a fixed toolbox (TOOLBOX below); the real provider asks the product's toolbox.
- rounding of a place: Python's round (half to even), as the real provider; the JavaScript mock rounds half up, so no contract case uses a half.
- time: a counter (`2026-01-01T00:00:01Z`, ...), not the clock.
Test setup (not routes): `seed(graph, author)` stores a version as that account; `unreachable = True` makes the store fail.
"""
import copy
import json
import math

try:
    from .errors import ApiError
except ImportError:
    from errors import ApiError

TOOLBOX = {"check.number": ("trusted", "tested"), "control.loop": ("trusted", "tested"), "tool.a": ("trusted", "draft")}
OPS = ("add_step", "remove_step", "change_step", "add_connection", "remove_connection", "change_connection", "restore")
RULE_TEXT = {"step_identity": "a step ID is used more than once", "connection_endpoints": "a connection names a step the graph does not have",
             "cycle": "the connections form a cycle"}
HEADER = ("context_graph_id", "testbench_id")


def _clone(x):
    return copy.deepcopy(x)


def _link(e):
    return {"from": e["from"], "to": e["to"], "data": _clone(e.get("data") or {})}


def canonical(graph):
    """the content of a graph independent of the order of its steps and connections (description, steps, connections)"""
    return json.dumps({"description": graph.get("description"),
                       "nodes": sorted(({"id": n["id"], "data": n.get("data") or {}} for n in graph["nodes"]), key=lambda n: str(n["id"])),
                       "edges": sorted(({"id": e["id"], "from": e["from"], "to": e["to"], "data": e.get("data") or {}} for e in graph["edges"]),
                                       key=lambda e: str(e["id"]))}, sort_keys=True)


def problems_of(graph):
    """what cannot be drawn: a step ID used twice, a connection to a step the graph does not have"""
    seen = {}
    for n in graph["nodes"]:
        seen[n["id"]] = seen.get(n["id"], 0) + 1
    found = [{"problem": "duplicate_step", "step": i} for i, count in seen.items() if count > 1]
    for e in graph["edges"]:
        for end in ("from", "to"):
            if e[end] not in seen:
                found.append({"problem": "missing_step", "connection": e["id"], "step": e[end], "end": end})
    return found


def rule_report(graph):
    """the mock's three rules (see Fidelity), every broken one in order, each with its parts"""
    out, ids, twice = [], set(), []
    for n in graph["nodes"]:
        if n["id"] in ids and n["id"] not in twice:
            twice.append(n["id"])
        ids.add(n["id"])
    if twice:
        out.append({"rule": "step_identity", "parts": twice, "text": RULE_TEXT["step_identity"]})
    loose = [e["id"] for e in graph["edges"] if e["from"] not in ids or e["to"] not in ids]
    if loose:
        out.append({"rule": "connection_endpoints", "parts": loose, "text": RULE_TEXT["connection_endpoints"]})
    if not twice and not loose:
        cycle = _cycle([n["id"] for n in graph["nodes"]], graph["edges"])
        if cycle:
            out.append({"rule": "cycle", "parts": cycle, "text": RULE_TEXT["cycle"]})
    return out


def _cycle(ids, edges):
    out = {i: [] for i in ids}
    for e in edges:
        out[e["from"]].append(e["to"])
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


def apply_change(graph, change):
    """the graph after one entry; ValueError when the entry does not fit the graph"""
    g = _clone(graph)
    op, target = change["op"], change["target"]
    nodes, edges = {n["id"]: n for n in g["nodes"]}, {e["id"]: e for e in g["edges"]}
    if op == "add_step" and target not in nodes:
        g["nodes"].append({"id": target, "data": _clone(change["after"])})
    elif op == "remove_step" and target in nodes:
        g["nodes"] = [n for n in g["nodes"] if n["id"] != target]
        g["edges"] = [e for e in g["edges"] if target not in (e["from"], e["to"])]
    elif op == "change_step" and target in nodes:
        nodes[target]["data"] = _clone(change["after"])
    elif op == "add_connection" and target not in edges:
        a = change["after"]
        g["edges"].append({"id": target, "from": a["from"], "to": a["to"], "data": _clone(a.get("data") or {})})
    elif op == "remove_connection" and target in edges:
        g["edges"] = [e for e in g["edges"] if e["id"] != target]
    elif op == "change_connection" and target in edges:
        a = change["after"]
        edges[target].update({"from": a["from"], "to": a["to"], "data": _clone(a.get("data") or {})})
    else:
        raise ValueError("%s %s does not fit" % (op, target))
    return g


def derive(before, after):
    """the entries from one graph to the other: connections removed, steps removed, steps added, steps changed, connections added and changed"""
    bn, an = {n["id"]: n for n in before["nodes"]}, {n["id"]: n for n in after["nodes"]}
    be, ae = {e["id"]: e for e in before["edges"]}, {e["id"]: e for e in after["edges"]}
    gone = [i for i in bn if i not in an]
    out = [{"op": "remove_connection", "target": i, "before": _link(e), "after": None, "reason": None}
           for i, e in be.items() if i not in ae and e["from"] not in gone and e["to"] not in gone]
    out += [{"op": "remove_step", "target": i, "before": _clone(bn[i].get("data") or {}), "after": None, "reason": None,
             "connections": [{"id": k, **_link(e)} for k, e in be.items() if i in (e["from"], e["to"])]} for i in gone]
    out += [{"op": "add_step", "target": i, "before": None, "after": _clone(an[i].get("data") or {}), "reason": None} for i in an if i not in bn]
    out += [{"op": "change_step", "target": i, "before": _clone(bn[i].get("data") or {}), "after": _clone(an[i].get("data") or {}), "reason": None}
            for i in an if i in bn and (bn[i].get("data") or {}) != (an[i].get("data") or {})]
    for i, e in ae.items():
        if i not in be:
            out.append({"op": "add_connection", "target": i, "before": None, "after": _link(e), "reason": None})
        elif _link(be[i]) != _link(e):
            out.append({"op": "change_connection", "target": i, "before": _link(be[i]), "after": _link(e), "reason": None})
    return out


def _number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _version_number(x):
    return isinstance(x, int) and not isinstance(x, bool)


class GraphApiV2Mock:
    def __init__(self, accounts=None, store="files"):
        self.accounts = accounts or {"anna": "pw-anna", "ben": "pw-ben"}      # the first account is the owner (as the real accounts: made first)
        self.owner = next(iter(self.accounts))
        self.store_kind = store
        self.unreachable = False
        self._sessions, self._graphs, self._arrangements, self._changes, self._tick = {}, {}, {}, {}, 0

    # --- test setup -------------------------------------------------------------------------------------------------------------
    def seed(self, graph, author):
        """stores `graph` (stored form, local IDs) as a new version by `author`; returns the version"""
        return self._put(graph["id"], _clone(graph), author)

    # --- helpers ----------------------------------------------------------------------------------------------------------------
    def _now(self):
        self._tick += 1
        return "2026-01-01T00:%02d:%02dZ" % (self._tick // 60, self._tick % 60)

    def _put(self, graph_id, graph, author):
        versions = self._graphs.setdefault(graph_id, [])
        versions.append({"version": len(versions) + 1, "author": author, "time": self._now(), "graph": graph})
        return len(versions)

    def _user(self, session, owner=False):
        if session not in self._sessions:
            raise ApiError(401, "unauthenticated")
        user = self._sessions[session]
        if owner and user != self.owner:
            raise ApiError(403, "not_owner")
        if self.unreachable:
            raise ApiError(503, "store_unreachable")
        return user

    def _versions(self, graph_id):
        if graph_id not in self._graphs:
            raise ApiError(404, "not_found")
        return self._graphs[graph_id]

    def _entry(self, graph_id, version=None):
        versions = self._versions(graph_id)
        if version is None:
            return versions[-1]
        if not _version_number(version) or not 1 <= version <= len(versions):
            raise ApiError(404, "not_found", detail={"detail": "version"})
        return versions[version - 1]

    def _sent(self, graph_id, body_graph):
        """the graph a request describes: the sent steps and connections with the header of the stored graph"""
        stored = self._entry(graph_id)["graph"]
        if not isinstance(body_graph, dict) or not isinstance(body_graph.get("nodes"), list) or not isinstance(body_graph.get("edges"), list):
            raise ApiError(422, "invalid", detail={"detail": "graph"})
        out = {k: _clone(v) for k, v in stored.items() if k not in ("nodes", "edges", "description")}
        out.update(description=body_graph.get("description", stored.get("description")), nodes=_clone(body_graph["nodes"]), edges=_clone(body_graph["edges"]))
        return out

    def _steps(self, graph):
        code = {e["to"] for e in graph["edges"] if (e.get("data") or {}).get("role") == "code"}
        out = {}
        for n in graph["nodes"]:
            data = n.get("data") or {}
            info = {"kind": data.get("type", "unknown")}
            if graph.get("kind", "workflow") == "workflow" and info["kind"] in ("transform", "master"):
                trust, lifecycle = TOOLBOX.get(data.get("toolbox_id"), ("untrusted", None))
                reason = "it is in the toolbox" if data.get("toolbox_id") in TOOLBOX else "it is not in the toolbox"
                info.update(trust=trust, lifecycle=lifecycle, reason=reason, code=n["id"] in code, changed_since_trusted=False)
            out[n["id"]] = info
        return out

    def _record(self, graph_id, from_version, version, kind, entries, author):
        self._changes[(graph_id, version)] = {"from_version": from_version, "kind": kind, "author": author, "time": self._entry(graph_id, version)["time"],
                                              "entries": [{"n": i + 1, **e} for i, e in enumerate(entries)]}

    # --- routes -----------------------------------------------------------------------------------------------------------------
    def login(self, user, password):
        """POST /api/login (IF-101): a session; 401 bad_credentials"""
        if self.accounts.get(user) != password:
            raise ApiError(401, "bad_credentials")
        token = "s%d" % (len(self._sessions) + 1)
        self._sessions[token] = user
        return token

    def me(self, session):
        if session not in self._sessions:
            raise ApiError(401, "unauthenticated")
        user = self._sessions[session]
        return {"user": user, "owner": user == self.owner}

    def store(self, session):
        if session not in self._sessions:
            raise ApiError(401, "unauthenticated")
        reachable = not self.unreachable
        return {"store": self.store_kind, "reachable": reachable, "shown": "live", "live_reachable": reachable, "lag": {"graphs": 0, "since": None}}

    def list_graphs(self, session):
        self._user(session)
        out = []
        for graph_id in sorted(self._graphs):
            head = self._graphs[graph_id][-1]
            g = head["graph"]
            out.append({"id": graph_id, "kind": g.get("kind", "workflow"), "version": head["version"], "author": head["author"], "time": head["time"],
                        "description": g.get("description"), "steps": len(g["nodes"]), "connections": len(g["edges"])})
        return out

    def read_graph(self, session, graph_id, version=None):
        self._user(session)
        entry = self._entry(graph_id, version)
        graph = _clone(entry["graph"])
        return {"graph": graph, "version": entry["version"], "current": len(self._graphs[graph_id]), "author": entry["author"], "time": entry["time"],
                "problems": problems_of(graph), "steps": self._steps(graph)}

    def versions(self, session, graph_id):
        self._user(session)
        return [{"version": e["version"], "author": e["author"], "time": e["time"]} for e in self._versions(graph_id)]

    def read_arrangement(self, session, graph_id):
        self._user(session)
        self._versions(graph_id)
        return _clone(self._arrangements.get(graph_id, {"positions": None}))

    def changes(self, session, graph_id):
        self._user(session)
        out = []
        for e in self._versions(graph_id):
            rec = self._changes.get((graph_id, e["version"]))
            if rec is None:
                out.append({"version": e["version"], "kind": "before_the_record", "author": e["author"], "time": e["time"], "entries": []})
            else:
                out.append({"version": e["version"], **_clone(rec)})
        return out

    def check(self, session, graph_id, graph):
        self._user(session, owner=True)
        return {"rules": rule_report(self._sent(graph_id, graph))}

    def save(self, session, graph_id, graph, expected_version=None, changes=None):
        user = self._user(session, owner=True)
        current = self._entry(graph_id)
        sent = self._sent(graph_id, graph)
        if expected_version is not None and expected_version != current["version"]:
            raise ApiError(409, "conflict", detail={"current": current["version"]})
        broken = rule_report(sent)
        if broken:
            raise ApiError(422, "rules_broken", detail={"rules": broken})
        if changes is not None:
            try:
                if not isinstance(changes, list) or any(not isinstance(c, dict) or c.get("op") not in OPS[:-1] for c in changes):
                    raise ValueError("not a list of entries")
                replayed = current["graph"]
                for c in changes:
                    replayed = apply_change(replayed, c)
            except (ValueError, KeyError, TypeError):
                raise ApiError(422, "changes_do_not_match")
            if canonical({**replayed, "description": sent["description"]}) != canonical(sent):
                raise ApiError(422, "changes_do_not_match")
            entries, kind = [{"op": c["op"], "target": c["target"], "before": c.get("before"), "after": c.get("after"),
                              "reason": c["reason"].strip() if isinstance(c.get("reason"), str) and c["reason"].strip() else None} for c in changes], "editor"
        else:
            entries, kind = derive(current["graph"], sent), "derived"
        if canonical(sent) == canonical(current["graph"]):
            return {"version": current["version"], "changed": False, "logged": None, "entries": len(entries)}
        version = self._put(graph_id, sent, user)
        self._record(graph_id, current["version"], version, kind, entries, user)
        return {"version": version, "changed": True, "logged": True, "entries": len(entries)}

    def restore(self, session, graph_id, version, reason=None):
        user = self._user(session, owner=True)
        current = self._entry(graph_id)
        old = self._entry(graph_id, version)["graph"]
        if canonical(old) == canonical(current["graph"]):
            return {"version": current["version"], "restored": version, "changed": False}
        new = self._put(graph_id, _clone(old), user)
        why = reason.strip() if isinstance(reason, str) and reason.strip() else None
        self._record(graph_id, current["version"], new, "restore", [{"op": "restore", "target": version, "before": None, "after": None, "reason": why}], user)
        return {"version": new, "restored": version, "changed": True}

    def save_arrangement(self, session, graph_id, positions):
        user = self._user(session, owner=True)
        steps = {n["id"] for n in self._entry(graph_id)["graph"]["nodes"]}
        if not isinstance(positions, dict):
            raise ApiError(422, "invalid", detail={"detail": "positions"})
        kept = {}
        for step, xy in positions.items():
            if step not in steps:
                continue
            if not isinstance(xy, dict) or not (_number(xy.get("x")) and _number(xy.get("y"))):
                raise ApiError(422, "invalid", detail={"detail": step})
            kept[step] = {"x": round(xy["x"]), "y": round(xy["y"])}
        version = self._arrangements.get(graph_id, {}).get("version", 0) + 1
        self._arrangements[graph_id] = {"positions": kept, "version": version, "author": user, "time": self._now()}
        return {"version": version, "saved": len(kept)}
