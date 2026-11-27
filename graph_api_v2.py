"""The graph API of the stored form for the Graph app (IF-104 v2, A-171): the HTTP routes under /api/v2 of contracts/IF-104-graph-api.md.

It stands beside the v1 routes of graph_api.py, which stay unchanged (REQ-API-030). The Graph app has no login of its own: the guard of accounts_api
sets g.account from the session cookie. Every v2 route needs that account, also when the accounts switch of the web application is off (REQ-API-045);
a change also needs an allowed Origin (REQ-API-047) and the owner. The backend is the store the configuration names (files or PostgreSQL, REQ-API-018);
while it does not answer, every graph route says store_unreachable and changes nothing (REQ-API-050).

create_app(backend, accounts_store, store, allowed_origins) is the same provider as a Flask app of its own, with the account routes and the guard: the
entry point the contract suite and the page checks run on.
"""
import json
import math

from flask import Blueprint, Flask, g, jsonify, request

try:
    from . import accounts, accounts_api, graph_model, graph_rule_set
    from .graph_store_transfer import lag_summary
    from .storage import Storage, StorageError
    from .toolbox import Toolbox, ToolboxError
    from .workflow_library import WorkflowLibrary
except ImportError:
    import accounts
    import accounts_api
    import graph_model
    import graph_rule_set
    from graph_store_transfer import lag_summary
    from storage import Storage, StorageError
    from toolbox import Toolbox, ToolboxError
    from workflow_library import WorkflowLibrary

STORES = ("files", "database")
EDITOR_OPS = ("add_step", "remove_step", "change_step", "add_connection", "remove_connection", "change_connection")      # `restore` is the restore route's
WRITES = ("POST", "PUT", "PATCH", "DELETE")
OPEN_ROUTES = ("graph_api_v2.me", "graph_api_v2.store")      # they answer while the store is down: `store` says so itself (REQ-API-021)


def store_setting(cfg):
    """the store the configuration names: files without a setting (REQ-API-019); any other value stops the start, naming the setting and the value (REQ-API-020)"""
    value = cfg.get("store", "files")
    if value not in STORES:
        raise ValueError('the setting "store" must be "files" or "database", not %s' % (_shown(value),))
    return value


def _shown(value):
    return '""' if value == "" else repr(value) if isinstance(value, str) else str(value)


def reachable(backend):
    """whether the store answers now; any failure of the backend counts as not answering, so a store that is down never breaks a route"""
    try:
        backend.ids("graphs")
        return True
    except Exception:      # a file system error, a lost database connection, a driver error: all mean the store cannot be read now
        return False


class NotFound(Exception):
    """a graph, or a version of it, that is not stored (REQ-API-049); `detail` is "version" for a version"""

    def __init__(self, detail=None):
        super().__init__(detail)
        self.detail = detail


def _stored(call, *args):
    try:
        return call(*args)
    except StorageError as err:
        if err.code == "not_found":
            raise NotFound() from err
        raise


def problems_of(graph):
    """what cannot be drawn (REQ-API-026): a connection to a step the graph does not have, a step ID used twice; never a rule report (D-425 A)"""
    seen, found = set(), []
    for node in graph["nodes"]:
        if node["id"] in seen and {"problem": "duplicate_step", "step": node["id"]} not in found:
            found.append({"problem": "duplicate_step", "step": node["id"]})
        seen.add(node["id"])
    for edge in graph["edges"]:
        found += [{"problem": "missing_step", "connection": edge["id"], "step": edge[end], "end": end} for end in ("from", "to") if edge[end] not in seen]
    return found


def steps_of(graph, toolbox):
    """the kind of each step and, for a processing or loop-controlling step, the marks of its toolbox entry (REQ-API-027, 028); a context graph's steps carry the kind only"""
    if graph.get("kind") == "context":
        return {n["id"]: {"kind": (n.get("data") or {}).get("type", "unknown")} for n in graph["nodes"]}
    coded = {e["to"] for e in graph["edges"] if (e.get("data") or {}).get("role") == "code"}
    steps = {}
    for node in graph["nodes"]:
        data = node.get("data") or {}
        info = {"kind": data.get("type", "unknown")}
        if info["kind"] in ("transform", "master"):
            try:
                entry = toolbox.look_up(data.get("toolbox_id"))
                marks = {"trust": entry["trust"], "lifecycle": entry["lifecycle"], "reason": entry["reason"] or "it is in the toolbox"}
            except ToolboxError:
                marks = {"trust": "untrusted", "lifecycle": None, "reason": "it is not in the toolbox"}
            # changed_since_trusted is fixed until G-V4.GRAPHAPI.CODE records the trusted content (REQ-API-028)
            info.update(marks, code=node["id"] in coded, changed_since_trusted=False)
        steps[node["id"]] = info
    return steps


class Refused(Exception):
    """a save the API refuses: the status, the error code and its fields of IF-104 v2; nothing is written"""

    def __init__(self, status, code, **fields):
        super().__init__(code)
        self.status, self.code, self.fields = status, code, fields


def _member(item):
    return {"id": item["id"], "data": item.get("data") or {}}


def _link(edge):
    return {"from": edge["from"], "to": edge["to"], "data": edge.get("data") or {}}


def content(graph):
    """what a save compares: the description, the steps and the connections, in any order and with any order of keys (REQ-API-033)"""
    return json.dumps({"description": graph.get("description"), "nodes": sorted((_member(n) for n in graph["nodes"]), key=lambda n: str(n["id"])),
                       "edges": sorted(({**_link(e), "id": e["id"]} for e in graph["edges"]), key=lambda e: str(e["id"]))}, sort_keys=True)


def derive(before, after):
    """the entries that lead from one graph to the other, without `n` (REQ-API-037): connections removed, steps removed (each with the connections
    that go with it), steps added, steps changed, then connections added and changed; the order of IF-104 v2's mock, so the record plays back"""
    bn, an = {n["id"]: _member(n)["data"] for n in before["nodes"]}, {n["id"]: _member(n)["data"] for n in after["nodes"]}
    be, ae = {e["id"]: _link(e) for e in before["edges"]}, {e["id"]: _link(e) for e in after["edges"]}
    gone = [i for i in bn if i not in an]
    entry = lambda op, target, old, new: {"op": op, "target": target, "before": old, "after": new, "reason": None}      # noqa: E731
    out = [entry("remove_connection", i, e, None) for i, e in be.items() if i not in ae and e["from"] not in gone and e["to"] not in gone]
    out += [{**entry("remove_step", i, bn[i], None), "connections": [{"id": k, **e} for k, e in be.items() if i in (e["from"], e["to"])]} for i in gone]
    out += [entry("add_step", i, None, d) for i, d in an.items() if i not in bn]
    out += [entry("change_step", i, bn[i], d) for i, d in an.items() if i in bn and bn[i] != d]
    for i, e in ae.items():
        if i not in be:
            out.append(entry("add_connection", i, None, e))
        elif be[i] != e:
            out.append(entry("change_connection", i, be[i], e))
    return out


def apply_change(graph, change):
    """the graph after one entry of the editor; ValueError when the entry does not fit the graph, its `before` included (REQ-API-038, V-4)"""
    op, target = change["op"], change["target"]
    nodes, edges = {n["id"]: n for n in graph["nodes"]}, {e["id"]: e for e in graph["edges"]}
    if change.get("before") != _value_before(op, target, nodes, edges):
        raise ValueError("%s %s: before is not the stored value" % (op, target))
    if op == "add_step" and target not in nodes:
        return {**graph, "nodes": graph["nodes"] + [{"id": target, "data": change["after"]}]}
    if op == "remove_step" and target in nodes:
        return {**graph, "nodes": [n for n in graph["nodes"] if n["id"] != target], "edges": [e for e in graph["edges"] if target not in (e["from"], e["to"])]}
    if op == "change_step" and target in nodes:
        return {**graph, "nodes": [{"id": n["id"], "data": change["after"]} if n["id"] == target else n for n in graph["nodes"]]}
    if op == "add_connection" and target not in edges:
        return {**graph, "edges": graph["edges"] + [{"id": target, **_link(change["after"])}]}
    if op == "remove_connection" and target in edges:
        return {**graph, "edges": [e for e in graph["edges"] if e["id"] != target]}
    if op == "change_connection" and target in edges:
        return {**graph, "edges": [{"id": target, **_link(change["after"])} if e["id"] == target else e for e in graph["edges"]]}
    raise ValueError("%s %s does not fit" % (op, target))


def _value_before(op, target, nodes, edges):
    """what an entry's `before` must be: the step's data or the connection's ends and data as derive() writes them, none for an addition"""
    if op in ("remove_step", "change_step") and target in nodes:
        return _member(nodes[target])["data"]
    if op in ("remove_connection", "change_connection") and target in edges:
        return _link(edges[target])
    return None


def editor_entries(current, graph, changes):
    """the editor's entries as recorded, when playing them back on `current` gives `graph`; else `changes_do_not_match` (REQ-API-038, 051)"""
    try:
        if not isinstance(changes, list) or any(not isinstance(c, dict) or c.get("op") not in EDITOR_OPS for c in changes):
            raise ValueError("not a list of entries")
        played = current
        for change in changes:
            played = apply_change(played, change)
    except (ValueError, KeyError, TypeError):
        raise Refused(422, "changes_do_not_match") from None
    if content({**played, "description": graph.get("description")}) != content(graph):
        raise Refused(422, "changes_do_not_match")
    trimmed = lambda r: r.strip() if isinstance(r, str) and r.strip() else None      # noqa: E731
    return [{"op": c["op"], "target": c["target"], "before": c.get("before"), "after": c.get("after"), "reason": trimmed(c.get("reason"))} for c in changes]


class GraphReader:
    """the read routes on the Storage layer of the backend (REQ-API-023 to 029, 043, 049)"""

    def __init__(self, backend):
        self.storage = Storage(backend)
        self.model = graph_model.GraphModel(self.storage)
        self.toolbox = Toolbox(WorkflowLibrary(self.storage), lambda account: False, None)       # look_up only: no events, no owner needed

    def list_graphs(self):
        out = []
        for graph_id in self.storage.ids("graphs"):
            head = self.storage.get("graphs", graph_id)
            data = head["doc"]["data"]
            out.append({"id": graph_id, "kind": data["kind"], "version": head["version"], "author": head["author"], "time": head["time"],
                        "description": data.get("description"), "steps": len(data["nodes"]), "connections": len(data["edges"])})
        return out

    def read_graph(self, graph_id, version=None):
        current = len(_stored(self.storage.history, "graphs", graph_id))
        if version is not None and not 1 <= version <= current:
            raise NotFound("version")
        entry = self.storage.get("graphs", graph_id, version)
        graph = self.model.read_graph(graph_id, entry["version"])
        return {"graph": graph, "version": entry["version"], "current": current, "author": entry["author"], "time": entry["time"],
                "problems": problems_of(graph), "steps": steps_of(graph, self.toolbox)}

    def versions(self, graph_id):
        return _stored(self.storage.history, "graphs", graph_id)

    def read_arrangement(self, graph_id):
        _stored(self.storage.history, "graphs", graph_id)
        try:
            entry = self.storage.get("arrangements", graph_id)
        except StorageError as err:
            if err.code == "not_found":
                return {"positions": None}
            raise
        return {"positions": entry["doc"]["positions"], "version": entry["version"], "author": entry["author"], "time": entry["time"]}

    def changes(self, graph_id):
        """one item per version, oldest first: its record of changes, or `before_the_record` for a version kept without one (REQ-API-042)"""
        items = []
        for entry in self.versions(graph_id):
            try:
                doc = self.storage.get("graph_changes", "%s/%d" % (graph_id, entry["version"]))["doc"]
                record = {"kind": doc["kind"], "from_version": doc["from_version"], "entries": doc["entries"]}
            except StorageError as err:
                if err.code != "not_found":
                    raise
                record = {"kind": "before_the_record", "entries": []}
            items.append({"version": entry["version"], **record, "author": entry["author"], "time": entry["time"]})
        return items

    def sent_graph(self, graph_id, body):
        """the graph a request describes: the sent steps and connections under the stored header; `description` taken when sent (IF-104 v2 save body)"""
        stored = self.read_graph(graph_id)
        graph = body.get("graph") if isinstance(body, dict) else None
        if not isinstance(graph, dict) or not isinstance(graph.get("nodes"), list) or not _connections_with_ids(graph.get("edges")):
            raise Refused(422, "invalid", detail="graph")
        header = {k: v for k, v in stored["graph"].items() if k not in ("nodes", "edges", "description")}
        return stored, {**header, "description": graph.get("description", stored["graph"].get("description")), "nodes": graph["nodes"], "edges": graph["edges"]}


def _connections_with_ids(edges):
    """a list whose connection objects carry a text `id`: derive() keys them by it and broke with a 500 (REQ-API-048, V-5); every other
    wrong form of a step or connection is answered by the rule report (`rules_broken`) as before"""
    return isinstance(edges, list) and all(not isinstance(e, dict) or isinstance(e.get("id"), str) for e in edges)


def a_place(xy):
    """a place of the arrangement body: x and y finite numbers, a boolean is none (IF-104 v2, REQ-API-048)"""
    number = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)      # noqa: E731
    return isinstance(xy, dict) and number(xy.get("x")) and number(xy.get("y"))


class GraphWriter:
    """the routes that check or change (REQ-API-031 to 037, 041, 044, 048): a new version authored by the account with its record of changes,
    or a refusal that writes nothing"""

    def __init__(self, backend, reader):
        self.storage, self.reader = Storage(backend), reader

    def check(self, graph_id, body):
        """the rule report of a working copy under the stored graph's kind; nothing is stored (REQ-API-031)"""
        return {"rules": graph_rule_set.rule_report(self.reader.sent_graph(graph_id, body)[1])}

    def save(self, graph_id, body, author):
        stored, graph = self.reader.sent_graph(graph_id, body)
        current = stored["current"]
        if body.get("expected_version") is not None and body["expected_version"] != current:
            raise Refused(409, "conflict", current=current)
        if body.get("changes") is None:
            kind, entries_of = "derived", lambda: derive(stored["graph"], graph)
        else:
            kind, entries_of = "editor", lambda: editor_entries(stored["graph"], graph, body["changes"])
        kept = self._keep(graph_id, stored, graph, author, kind, entries_of)
        if kept is None:
            return {"version": current, "changed": False, "logged": None, "entries": 0}
        version, entries, logged = kept
        return {"version": version, "changed": True, "logged": logged, "entries": entries}

    def restore(self, graph_id, body, author):
        """the content of an earlier version as a new version with one `restore` entry; nothing is deleted (REQ-API-041)"""
        version = body.get("version") if isinstance(body, dict) else None
        if not isinstance(version, int) or isinstance(version, bool):
            raise NotFound("version")
        old = self.reader.read_graph(graph_id, version)["graph"]
        reason = body.get("reason").strip() if isinstance(body.get("reason"), str) and body["reason"].strip() else None
        entry = {"op": "restore", "target": version, "before": None, "after": None, "reason": reason}
        stored = self.reader.read_graph(graph_id)
        kept = self._keep(graph_id, stored, old, author, "restore", lambda: [entry])
        return {"version": kept[0] if kept else stored["current"], "restored": version, "changed": kept is not None}

    def _keep(self, graph_id, stored, graph, author, kind, entries_of):
        """`graph` as the version after `stored` with its record of changes (`entries_of()`, which may refuse); (new version, number of entries,
        whether the record was written), or None when the content is the same. The rules come first: a graph that breaks one may not even have
        steps that can be compared (REQ-API-033, 035, 036)."""
        rules = graph_rule_set.rule_report(graph)
        if rules:
            raise Refused(422, "rules_broken", rules=rules)
        entries = [{"n": n, **e} for n, e in enumerate(entries_of(), 1)]
        if content(graph) == content(stored["graph"]):
            return None
        result = graph_model.GraphModel(self.storage, author=author).save_graph(graph)
        if not result.saved:
            raise Refused(422, "refused", rule=result.rule, detail=result.detail)
        record = {"graph": graph_id, "version": result.version, "from_version": stored["current"], "kind": kind, "entries": entries}
        return result.version, len(entries), self._log(graph_id, result.version, record, author)

    def _log(self, graph_id, version, record, author):
        """write the record of changes once (REQ-API-039): never over a record with its ID; a record that cannot be written leaves the version kept
        and listed as made before the record (REQ-API-040)"""
        try:
            self.storage.put("graph_changes", "%s/%d" % (graph_id, version), record, author, expected_version=0)      # 0: only while no record has this ID
            return True
        except Exception:      # `conflict` (a record is there already), a lost connection or a failing disk: the version stays without this record
            return False

    def save_arrangement(self, graph_id, body, author):
        """the places of the graph's steps, rounded, as the one arrangement record of the graph; places of unknown steps ignored (REQ-API-044)"""
        steps = {n["id"] for n in self.reader.read_graph(graph_id)["graph"]["nodes"]}
        positions = body.get("positions") if isinstance(body, dict) else None
        if not isinstance(positions, dict):
            raise Refused(422, "invalid", detail="positions")
        kept = {}
        for step, xy in positions.items():
            if step in steps:
                if not a_place(xy):
                    raise Refused(422, "invalid", detail=step)
                kept[step] = {"x": round(xy["x"]), "y": round(xy["y"])}
        saved = self.storage.put("arrangements", graph_id, {"graph": graph_id, "positions": kept}, author)
        return {"version": saved["version"], "saved": len(kept)}


def _opened(live):
    """the live store if it answers now, else None: `live()` may fail while the store is down (REQ-API-063)"""
    try:
        found = live()
    except Exception:      # an address nobody answers, a lost connection, a driver error: the store does not answer now
        return None
    return found if reachable(found) else None


def _store_answer(backend, store, live):
    """GET /store: with no copy the fixed fields of REQ-API-022; with a copy the copy is shown, the live store asked now (REQ-API-064)"""
    up = reachable(backend)
    if live is None:
        return {"store": store, "reachable": up, "shown": "live", "live_reachable": up, "lag": {"graphs": 0, "since": None}}
    found = _opened(live)
    lag = {"graphs": 0, "since": None}
    if found is not None and up:
        try:
            lag = lag_summary(found, backend)
        except Exception:      # the live store went away while it was read: answered as not reachable, like _opened
            found = None
    return {"store": store, "reachable": up, "shown": "copy", "live_reachable": found is not None, "lag": lag}


def create_graph_v2_blueprint(backend, store, is_owner, allowed_origins, *, live=None):
    """the v2 routes on `backend` (an IF-102 backend); `store` the configured name, `is_owner(account)`, `allowed_origins()` the origins of the page.
    `live`: with a copy set, `backend` is the copy the routes read (REQ-API-060) and `live()` opens the live store, which the writes go to (D-544)"""
    bp = Blueprint("graph_api_v2", __name__, url_prefix="/api/v2")

    def error(status, code, **fields):
        return jsonify({"error": code, **fields}), status

    @bp.before_request
    def guard():
        if request.method in WRITES and request.headers.get("Origin") not in allowed_origins():
            return error(403, "bad_origin")          # checked before the session, so a foreign page learns nothing about it (TC-API-024)
        if not getattr(g, "account", None):
            return error(401, "unauthenticated")
        if request.method in WRITES and not is_owner(g.account):
            return error(403, "not_owner")
        if request.endpoint not in OPEN_ROUTES:
            target = written() if request.method in WRITES else backend
            if target is None or not reachable(target):
                return error(503, "store_unreachable")
        return None

    @bp.get("/me")
    def me():
        return jsonify({"user": g.account, "owner": bool(is_owner(g.account))})

    @bp.get("/store", endpoint="store")
    def store_route():
        return jsonify(_store_answer(backend, store, live))

    reader = GraphReader(backend)
    writers = {}       # the live store's writer, made once the live store has answered

    def written():
        """the store the writes go to: the backend itself, or with a copy the live store if it answers now"""
        return backend if live is None else _opened(live)

    def writer():
        target = written()
        if id(target) not in writers:
            writers[id(target)] = GraphWriter(target, reader if target is backend else GraphReader(target))
        return writers[id(target)]

    @bp.errorhandler(NotFound)
    def unknown(err):
        return error(404, "not_found", **({"detail": err.detail} if err.detail else {}))

    @bp.errorhandler(Refused)
    def refused(err):
        return error(err.status, err.code, **err.fields)

    @bp.post("/graphs/<graph_id>/check", endpoint="check")
    def check(graph_id):
        return jsonify(writer().check(graph_id, request.get_json(silent=True)))

    @bp.put("/graphs/<graph_id>", endpoint="save")
    def save(graph_id):
        return jsonify(writer().save(graph_id, request.get_json(silent=True), g.account))

    @bp.post("/graphs/<graph_id>/restore", endpoint="restore")
    def restore(graph_id):
        return jsonify(writer().restore(graph_id, request.get_json(silent=True), g.account))

    @bp.put("/graphs/<graph_id>/arrangement", endpoint="save_arrangement")
    def save_arrangement(graph_id):
        return jsonify(writer().save_arrangement(graph_id, request.get_json(silent=True), g.account))

    @bp.get("/graphs", endpoint="list_graphs")
    def list_graphs():
        return jsonify(reader.list_graphs())

    @bp.get("/graphs/<graph_id>", endpoint="read_graph")
    def read_graph(graph_id):
        version = request.args.get("version")
        if version is not None and (not version.isdigit() or int(version) < 1):
            raise NotFound("version")
        return jsonify(reader.read_graph(graph_id, None if version is None else int(version)))

    @bp.get("/graphs/<graph_id>/versions", endpoint="versions")
    def versions(graph_id):
        return jsonify(reader.versions(graph_id))

    @bp.get("/graphs/<graph_id>/arrangement", endpoint="read_arrangement")
    def read_arrangement(graph_id):
        return jsonify(reader.read_arrangement(graph_id))

    @bp.get("/graphs/<graph_id>/changes", endpoint="changes")
    def changes(graph_id):
        return jsonify(reader.changes(graph_id))
    return bp


def create_app(backend, accounts_store, store, allowed_origins, *, live=None):
    """IF-104 v2 as a Flask app of its own: the account routes of IF-101, the guard, and the v2 routes on `backend` (REQ-API-030); the owner is the first account.
    `live`: see create_graph_v2_blueprint (keyword only, so the positional calls of VIEW cannot shift, D-470)"""
    if store not in STORES:
        raise ValueError('the setting "store" must be "files" or "database", not %s' % (_shown(store),))
    origins = list(allowed_origins)
    app = Flask(__name__)
    service = accounts_api.SessionService(accounts_store)
    app.register_blueprint(accounts_api.create_accounts_blueprint(service))
    accounts_api.install_guard(app, service, open_paths=(), open_prefixes=(), allowed_origins=lambda: origins)
    app.register_blueprint(create_graph_v2_blueprint(backend, store, accounts.owner_check({}, accounts_store), lambda: origins, live=live))
    return app
