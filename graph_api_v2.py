"""The graph API of the stored form for the Graph app (IF-104 v2, A-171): the HTTP routes under /api/v2 of contracts/IF-104-graph-api.md.

It stands beside the v1 routes of graph_api.py, which stay unchanged (REQ-API-030). The Graph app has no login of its own: the guard of accounts_api
sets g.account from the session cookie. Every v2 route needs that account, also when the accounts switch of the web application is off (REQ-API-045);
a change also needs an allowed Origin (REQ-API-047) and the owner. The backend is the store the configuration names (files or PostgreSQL, REQ-API-018);
while it does not answer, every graph route says store_unreachable and changes nothing (REQ-API-050).

create_app(backend, accounts_store, store, allowed_origins) is the same provider as a Flask app of its own, with the account routes and the guard: the
entry point the contract suite and the page checks run on.
"""
from flask import Blueprint, Flask, g, jsonify, request

try:
    from . import accounts, accounts_api, graph_model
    from .storage import Storage, StorageError
    from .toolbox import Toolbox, ToolboxError
    from .workflow_library import WorkflowLibrary
except ImportError:
    import accounts
    import accounts_api
    import graph_model
    from storage import Storage, StorageError
    from toolbox import Toolbox, ToolboxError
    from workflow_library import WorkflowLibrary

STORES = ("files", "database")
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


def create_graph_v2_blueprint(backend, store, is_owner, allowed_origins):
    """the v2 routes on `backend` (an IF-102 backend); `store` the configured name, `is_owner(account)`, `allowed_origins()` the origins of the page"""
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
        if request.endpoint not in OPEN_ROUTES and not reachable(backend):
            return error(503, "store_unreachable")
        return None

    @bp.get("/me")
    def me():
        return jsonify({"user": g.account, "owner": bool(is_owner(g.account))})

    @bp.get("/store", endpoint="store")
    def store_route():
        up = reachable(backend)
        # shown, live_reachable and lag are fixed until G-V4.GRAPHSTORE.TRANSFER brings the copy (REQ-API-022, D-460)
        return jsonify({"store": store, "reachable": up, "shown": "live", "live_reachable": up, "lag": {"graphs": 0, "since": None}})

    reader = GraphReader(backend)

    @bp.errorhandler(NotFound)
    def unknown(err):
        return error(404, "not_found", **({"detail": err.detail} if err.detail else {}))

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

    def not_built():
        return error(501, "not_built")              # the remaining routes come with T-03 to T-06 of G-V4.VIEW

    for rule, methods, name in (("/graphs/<graph_id>/changes", ["GET"], "changes"), ("/graphs/<graph_id>/check", ["POST"], "check"),
                                ("/graphs/<graph_id>", ["PUT"], "save"), ("/graphs/<graph_id>/restore", ["POST"], "restore"),
                                ("/graphs/<graph_id>/arrangement", ["PUT"], "save_arrangement")):
        bp.add_url_rule(rule, name, lambda graph_id=None: not_built(), methods=methods)
    return bp


def create_app(backend, accounts_store, store, allowed_origins):
    """IF-104 v2 as a Flask app of its own: the account routes of IF-101, the guard, and the v2 routes on `backend` (REQ-API-030); the owner is the first account"""
    if store not in STORES:
        raise ValueError('the setting "store" must be "files" or "database", not %s' % (_shown(store),))
    origins = list(allowed_origins)
    app = Flask(__name__)
    service = accounts_api.SessionService(accounts_store)
    app.register_blueprint(accounts_api.create_accounts_blueprint(service))
    accounts_api.install_guard(app, service, open_paths=(), open_prefixes=(), allowed_origins=lambda: origins)
    app.register_blueprint(create_graph_v2_blueprint(backend, store, accounts.owner_check({}, accounts_store), lambda: origins))
    return app
