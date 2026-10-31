"""The workflow and graph API for the Graph app (IF-104 v1, REQ-API-014, REQ-API-016): the HTTP routes of contracts/IF-104-graph-api.md.

The Graph app has no login of its own (D-47): the guard of accounts_api reads the session cookie and sets g.account, which becomes the author of a
version. Every operation goes to the workflow library (IF-203), which leaves the versions and the graph rules to the Storage layer (IF-102); this
module only translates between HTTP and the library. Without accounts (the switch is off) the author is "page", as for the other routes.
"""
from flask import Blueprint, g, jsonify, request

try:
    from .workflow_library import KINDS, WorkflowLibraryError
except ImportError:
    from workflow_library import KINDS, WorkflowLibraryError

STATUS = {"not_found": 404, "conflict": 409, "immutable": 409, "invalid": 422}
READ_FIELDS = ("id", "version", "author", "time", "doc")            # the library adds the lifecycle status; IF-104 names these five


def _number(text):
    """a version from the query or the body; anything else is a version that does not exist"""
    try:
        return int(text)
    except (TypeError, ValueError):
        return -1


def create_graph_blueprint(library):
    bp = Blueprint("graph_api", __name__)

    def author():
        return getattr(g, "account", None) or "page"

    def answer(kind, call):
        if kind not in KINDS:
            return jsonify({"error": "unknown_kind"}), 404
        try:
            return jsonify(call())
        except WorkflowLibraryError as err:
            body = {"error": err.code}
            if err.code == "invalid":
                body.update(rule=err.rule, detail=err.detail)
            elif err.code == "conflict":
                body["detail"] = err.detail
            return jsonify(body), STATUS.get(err.code, 500)

    def read(kind, record_id, version):
        entry = library.read(kind, record_id, version)
        return {field: entry[field] for field in READ_FIELDS}

    @bp.get("/api/<kind>")
    def list_ids(kind):
        return answer(kind, lambda: library.list_ids(kind))

    @bp.get("/api/<kind>/<record_id>")
    def read_one(kind, record_id):
        version = request.args.get("version")
        return answer(kind, lambda: read(kind, record_id, None if version is None else _number(version)))

    @bp.put("/api/<kind>/<record_id>")
    def save(kind, record_id):
        body = request.get_json(silent=True)
        body = body if isinstance(body, dict) else {}
        return answer(kind, lambda: library.save(kind, record_id, body.get("doc"), author(), body.get("expected_version")))

    @bp.get("/api/<kind>/<record_id>/history")
    def history(kind, record_id):
        return answer(kind, lambda: library.history(kind, record_id))

    @bp.get("/api/<kind>/<record_id>/diff")
    def diff(kind, record_id):
        return answer(kind, lambda: library.diff(kind, record_id, _number(request.args.get("a")), _number(request.args.get("b"))))

    @bp.post("/api/<kind>/<record_id>/restore")
    def restore(kind, record_id):
        body = request.get_json(silent=True)
        version = body.get("version") if isinstance(body, dict) else None
        return answer(kind, lambda: library.restore(kind, record_id, _number(version), author()))

    return bp
