"""PROTOTYPE CP5 (G-V4.VIEW): a backend for graphs behind the account login, and the viewer page.

python graph_proto_app.py --store files:<folder> | postgres:<url> [--accounts <folder>] [--user name:password] [--port 8801]

Routes (a draft of IF-104 v2, read side; the frozen v1 stays working):
  POST /api/login, GET /api/whoami, POST /api/logout          the existing accounts (accounts_api), session cookie
  GET  /api/v2/graphs                                          the stored graphs: id, kind, version, author, time, description, steps, connections
  GET  /api/v2/graphs/<id>[?version=n]                         one graph with its local IDs, its version, and what cannot be drawn
  GET  /api/v2/graphs/<id>/versions                            the versions with author and time
Everything except the login and the page needs a session (NFR-12). The page is graph_app_v2/ (its own files first, then graph_app/).
"""
import argparse
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
from flask import Flask, g, jsonify, request, send_from_directory

import accounts
import accounts_api
import graph_model
import tempfile
from toolbox import Toolbox, ToolboxError
from workflow_library import WorkflowLibrary
from api_sessions import SessionService
from storage import Storage, StorageError
from storage_files import FileBackend


def open_store(spec):
    kind, _, rest = spec.partition(":")
    if kind == "files":
        return FileBackend(rest)
    if kind == "postgres":
        from storage_postgres import PostgresBackend
        return PostgresBackend(rest)
    raise SystemExit("--store is files:<folder> or postgres:<url>")


def problems_of(graph):
    """what cannot be drawn: a connection to a step that does not exist, a step or connection ID used twice"""
    found, ids = [], {}
    for n in graph["nodes"]:
        ids[n["id"]] = ids.get(n["id"], 0) + 1
    found += [{"problem": "duplicate_step", "step": i} for i, c in ids.items() if c > 1]
    for e in graph["edges"]:
        for end in ("from", "to"):
            if e[end] not in ids:
                found.append({"problem": "missing_step", "connection": e["id"], "step": e[end], "end": end})
    return found


class _NoEvents:
    def record(self, event):
        return None


def make_toolbox():
    """the shipped transforms and the three controllers in a throw-away store: it answers what the trust and the lifecycle of a toolbox ID are (the viewer never changes it)"""
    box = Toolbox(WorkflowLibrary(Storage(FileBackend(tempfile.mkdtemp(prefix="viewer-toolbox-")))), lambda account: True, _NoEvents())
    box.seed_shipped(os.path.join(REPO, "library", "nodes"))
    box.seed_controls()
    return box


def steps_info(graph, box):
    """per step: its kind, for a processing or loop-controlling step the trust and lifecycle of its toolbox entry, and whether it holds code (an input connection with the role `code`)"""
    code_targets = {e["to"] for e in graph["edges"] if (e.get("data") or {}).get("role") == "code"}
    out = {}
    for n in graph["nodes"]:
        data, info = n.get("data") or {}, {"kind": (n.get("data") or {}).get("type", "unknown")}
        if info["kind"] in ("transform", "master"):
            try:
                found = box.look_up(data.get("toolbox_id", ""))
                info.update(trust=found["trust"], lifecycle=found["lifecycle"], reason=found["reason"])
            except ToolboxError:
                info.update(trust="untrusted", lifecycle=None, reason="it is not in the toolbox")
            info["code"] = n["id"] in code_targets
            info["changed_since_trusted"] = False       # CP6: nothing records the trusted content yet (FR-67 of GRAPHAPI.CODE); the page shows the mark when this is true
        out[n["id"]] = info
    return out


def create_app(backend, accounts_store, port=8801):
    app = Flask(__name__, static_folder=None)
    model = graph_model.GraphModel(Storage(backend), author="viewer")
    service = SessionService(accounts_store)
    box = make_toolbox()
    app.register_blueprint(accounts_api.create_accounts_blueprint(service))
    # a browser sends the Origin of the page with every login and change; the guard refuses every other one (bad_origin), so the pages of this host are allowed
    origins = ["http://127.0.0.1:%d" % port, "http://localhost:%d" % port]
    accounts_api.install_guard(app, service, open_paths=("/",), open_prefixes=("/static/", "/page/"), allowed_origins=lambda: origins)

    def summary(graph_id):
        head = model.tables.get("graphs", graph_id)
        data = head["doc"]["data"]
        return {"id": graph_id, "kind": data["kind"], "version": head["version"], "author": head["author"], "time": head["time"],
                "description": data["description"], "steps": len(data["nodes"]), "connections": len(data["edges"])}

    @app.get("/api/v2/graphs")
    def list_graphs():
        return jsonify(sorted((summary(i) for i in backend.ids("graphs")), key=lambda s: s["id"]))

    @app.get("/api/v2/graphs/<path:graph_id>/versions")
    def versions(graph_id):
        try:
            return jsonify(model.graph_versions(graph_id))
        except StorageError:
            return jsonify({"error": "not_found"}), 404

    @app.get("/api/v2/graphs/<path:graph_id>")
    def one(graph_id):
        version = request.args.get("version", type=int)
        try:
            graph = model.read_graph(graph_id, version)
            head = {e["version"]: e for e in model.graph_versions(graph_id)}
            shown = version or max(head)
        except StorageError:
            return jsonify({"error": "not_found"}), 404
        return jsonify({"graph": graph, "version": shown, "current": max(head), "author": head[shown]["author"], "time": head[shown]["time"],
                        "problems": problems_of(graph), "steps": steps_info(graph, box)})

    @app.get("/")
    def index():
        return send_from_directory(os.path.join(REPO, "graph_app_v2"), "index.html")

    @app.get("/page/<path:name>")
    def page(name):
        for folder in ("graph_app_v2", "graph_app"):
            if os.path.exists(os.path.join(REPO, folder, name)):
                return send_from_directory(os.path.join(REPO, folder), name)
        return jsonify({"error": "not_found"}), 404

    app.config["model"] = model
    return app


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--accounts", default=os.path.join(REPO, "data", "proto_accounts"))
    ap.add_argument("--user", default="owner:secret")
    ap.add_argument("--port", type=int, default=8801)
    a = ap.parse_args()
    acc = Storage(FileBackend(a.accounts))
    name, _, password = a.user.partition(":")
    if not accounts.verify(acc, name, password):
        try:
            accounts.create(acc, name, password, "prototype")
        except Exception as err:      # the account exists with another password
            print("account", name, "exists:", err)
    print("viewer: http://127.0.0.1:%d/  (login %s)" % (a.port, name))
    create_app(open_store(a.store), acc, a.port).run("127.0.0.1", a.port)
