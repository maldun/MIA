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
    from . import accounts, accounts_api
except ImportError:
    import accounts
    import accounts_api

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

    def not_built():
        return error(501, "not_built")              # the remaining routes come with T-03 to T-06 of G-V4.VIEW

    for rule, methods, name in (("/graphs", ["GET"], "list_graphs"), ("/graphs/<graph_id>", ["GET"], "read_graph"),
                                ("/graphs/<graph_id>/versions", ["GET"], "versions"), ("/graphs/<graph_id>/arrangement", ["GET"], "read_arrangement"),
                                ("/graphs/<graph_id>/changes", ["GET"], "changes"), ("/graphs/<graph_id>/check", ["POST"], "check"),
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
