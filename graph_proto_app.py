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
import json
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
import math
from flask import Flask, g, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import accounts
import accounts_api
import graph_model
import graph_changes
import graph_rules_proto
import graph_run
import graph_store_move
import graph_store_sync
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


UNREACHABLE = (OSError, ConnectionError, TimeoutError)


def _unreachable(error):
    """the live store cannot be reached: a file or network error, or a database driver error (named by class, so the viewer needs no driver)"""
    return isinstance(error, UNREACHABLE) or type(error).__name__ in ("OperationalError", "InterfaceError", "AdminShutdown", "ConnectionTimeout")


def create_app(backend, accounts_store, port=8801, live=None, aside=None):
    """backend: the store that is read (the copy MIA runs on); live: the live store that every change is written to (the same store when it is None)"""
    app = Flask(__name__, static_folder=None)
    model = graph_model.GraphModel(Storage(backend), author="viewer")
    live_backend = live if live is not None else backend
    aside = aside or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "proto_aside")
    wmodel = model if live is None else graph_model.GraphModel(Storage(live_backend), author="viewer")   # writes go to the live store (FR-95)
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

    @app.errorhandler(Exception)
    def failed(error):
        if isinstance(error, HTTPException):
            return error
        if isinstance(error, StorageError) or not _unreachable(error):
            raise error
        return jsonify({"error": "store_unreachable"}), 503

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

    def is_owner(account):
        return account is not None and account == accounts.first_account(accounts_store)

    @app.get("/api/v2/graphs/<path:graph_id>/arrangement")
    def get_arrangement(graph_id):
        """where the owner put the steps of the graph: one arrangement per graph, the same for everyone; not part of a graph version (D-363, D-369)"""
        try:
            head = model.tables.get("arrangements", graph_id)
        except StorageError:
            return jsonify({"positions": None})
        return jsonify({"positions": head["doc"]["positions"], "version": head["version"], "author": head["author"], "time": head["time"]})

    @app.put("/api/v2/graphs/<path:graph_id>/arrangement")
    def put_arrangement(graph_id):
        if not is_owner(getattr(g, "account", None)):
            return jsonify({"error": "not_owner"}), 403
        try:
            steps = {n["id"] for n in model.read_graph(graph_id)["nodes"]}
        except StorageError:
            return jsonify({"error": "not_found"}), 404
        body = request.get_json(silent=True) or {}
        raw = body.get("positions")
        if not isinstance(raw, dict):
            return jsonify({"error": "invalid", "detail": "positions"}), 422
        positions = {}
        for step, xy in raw.items():
            if step not in steps:
                continue                                    # a place for a step the graph does not have is ignored
            ok = isinstance(xy, dict) and all(isinstance(xy.get(k), (int, float)) and not isinstance(xy.get(k), bool) and math.isfinite(xy[k]) for k in ("x", "y"))
            if not ok:
                return jsonify({"error": "invalid", "detail": step}), 422
            positions[step] = {"x": round(xy["x"]), "y": round(xy["y"])}
        saved = model.tables.put("arrangements", graph_id, {"graph": graph_id, "positions": positions}, g.account)
        return jsonify({"version": saved["version"], "saved": len(positions)})

    def record_changes(graph_id, from_version, version, entries, kind):
        """the record of how a version came about (FR-76): written once, after the version is stored; False when it could not be written (the version stays, it is listed as having no record)"""
        doc = {"graph": graph_id, "version": version, "from_version": from_version, "kind": kind,
               "entries": [{"n": i + 1, **entry} for i, entry in enumerate(entries)]}
        try:
            wmodel.tables.put("graph_changes", "%s/%d" % (graph_id, version), doc, g.account)
            return True
        except StorageError:
            return False

    @app.get("/api/v2/graphs/<path:graph_id>/changes")
    def changes_of(graph_id):
        """how each version came about: its entries (who, when, what, before and after, reason, the version it started from); a version without a record is listed as made before the record"""
        try:
            versions = model.graph_versions(graph_id)
        except StorageError:
            return jsonify({"error": "not_found"}), 404
        out = []
        for v in versions:
            try:
                rec = model.tables.get("graph_changes", "%s/%d" % (graph_id, v["version"]))
            except StorageError:
                out.append({"version": v["version"], "kind": "before_the_record", "author": v["author"], "time": v["time"], "entries": []})
                continue
            out.append({"version": v["version"], "kind": rec["doc"]["kind"], "from_version": rec["doc"]["from_version"], "author": rec["author"], "time": rec["time"], "entries": rec["doc"]["entries"]})
        return jsonify(out)

    def owner_only():
        return None if is_owner(getattr(g, "account", None)) else (jsonify({"error": "not_owner"}), 403)

    def full_graph(graph_id, body):
        """the graph a request describes: its steps and connections, with the header of the stored graph"""
        stored = wmodel.read_graph(graph_id)
        sent = body.get("graph") if isinstance(body.get("graph"), dict) else {}
        if not isinstance(sent.get("nodes"), list) or not isinstance(sent.get("edges"), list):
            return None
        return {"id": graph_id, "context_graph_id": stored["context_graph_id"], "testbench_id": stored["testbench_id"],
                "description": sent.get("description", stored["description"]), "nodes": sent["nodes"], "edges": sent["edges"]}

    @app.post("/api/v2/graphs/<path:graph_id>/restore")
    def restore(graph_id):
        """makes an earlier version the current one again: its content is saved as a new version; nothing is deleted (FR-73)"""
        denied = owner_only()
        if denied:
            return denied
        body = request.get_json(silent=True) or {}
        version = body.get("version")
        try:
            versions = [e["version"] for e in wmodel.graph_versions(graph_id)]
            if not isinstance(version, int) or isinstance(version, bool) or version not in versions:
                return jsonify({"error": "not_found", "detail": "version"}), 404
            current = max(versions)
            old = wmodel.read_graph(graph_id, version)
        except StorageError:
            return jsonify({"error": "not_found"}), 404
        wmodel.author = g.account
        saved = wmodel.save_graph(old)
        if not saved.saved:
            return jsonify({"error": "refused", "rule": saved.rule, "detail": saved.detail}), 422
        if saved.version != current:
            reason = body.get("reason") if isinstance(body.get("reason"), str) and body["reason"].strip() else None
            record_changes(graph_id, current, saved.version, [{"op": "restore", "target": version, "before": None, "after": None, "reason": reason}], "restore")
        return jsonify({"version": saved.version, "restored": version, "changed": saved.version != current, **sync_graph(graph_id)})

    @app.get("/api/v2/status")
    def status():
        """whether the live store can be reached, and how far the copy is behind it (versions of graphs the copy does not have yet)"""
        if live is None:
            return jsonify({"split": False, "live": "reachable", "lag": 0})
        try:
            lag, behind, differs = 0, {}, {}
            for graph_id, row in graph_store_sync.lag(live_backend, backend).items():
                if row["state"] == "behind":
                    lag += row["live"] - row["copy"]
                    behind[graph_id] = {"live": row["live"], "copy": row["copy"]}      # which graphs the copy is behind on, and by how much
                elif row["state"] in ("differs", "copy_only"):
                    differs[graph_id] = row["reason"]                                  # the live store wins at the next sync: the copy's version is set aside, named
            return jsonify({"split": True, "live": "reachable", "lag": lag, "behind": behind, "differs": differs})
        except Exception as error:                                  # noqa: BLE001 - only an unreachable store is told, anything else is a bug
            if not _unreachable(error):
                raise
            return jsonify({"split": True, "live": "unreachable", "lag": None})

    @app.post("/api/v2/sync")
    def sync():
        """brings the copy up to date with the live store (one way, the live store wins; CP3): what only the copy has is written to a file in the aside folder and named in the answer"""
        denied = owner_only()
        if denied:
            return denied
        if live is None:
            return jsonify({"error": "no_live_store"}), 409
        try:
            return jsonify(graph_store_sync.sync_store(live_backend, backend, aside))
        except StorageError as error:
            if error.rule == "move_refused":
                return jsonify({"error": "move_refused", "graphs": error.detail["graphs"]}), 409
            raise

    @app.get("/api/v2/toolbox")
    def toolbox():
        """the tools a processing step can use: every entry of the toolbox that is not retired, with its trust and lifecycle; the controllers are the ones for loop-controlling steps"""
        out = []
        for tid in box.offer():
            found = box.look_up(tid)
            out.append({"id": tid, "trust": found["trust"], "lifecycle": found["lifecycle"], "controller": tid.startswith("control.")})
        return jsonify(out)

    def sync_graph(graph_id):
        """after a change in the live store the copy gets that graph at once (the owner expects to see what was just done); {"synced": bool, "sync_problem": text}"""
        if live is None:
            return {"synced": True}
        try:
            graph_store_move.move_graph(live_backend, backend, graph_id)
            return {"synced": True}
        except StorageError as error:
            return {"synced": False, "sync_problem": json.dumps(error.detail.get("graphs", error.detail)) if isinstance(error.detail, dict) else str(error.detail)}

    @app.get("/api/v2/me")
    def me():
        account = getattr(g, "account", None)
        return jsonify({"user": account, "owner": is_owner(account)})

    @app.post("/api/v2/graphs/<path:graph_id>/check")
    def check_graph(graph_id):
        """the rules of a graph that has not been kept yet: the editor asks it after every change (D-363)"""
        denied = owner_only()
        if denied:
            return denied
        try:
            graph = full_graph(graph_id, request.get_json(silent=True) or {})
        except StorageError:
            return jsonify({"error": "not_found"}), 404
        if graph is None:
            return jsonify({"error": "invalid", "detail": "graph"}), 422
        return jsonify({"rules": graph_rules_proto.rule_report(graph)})

    @app.put("/api/v2/graphs/<path:graph_id>")
    def keep_graph(graph_id):
        """keeps a change as a new version when every rule holds; otherwise nothing is written and the broken rules are named"""
        denied = owner_only()
        if denied:
            return denied
        body = request.get_json(silent=True) or {}
        try:
            current = max(e["version"] for e in wmodel.graph_versions(graph_id))
            graph = full_graph(graph_id, body)
        except StorageError:
            return jsonify({"error": "not_found"}), 404
        if graph is None:
            return jsonify({"error": "invalid", "detail": "graph"}), 422
        if body.get("expected_version") is not None and body["expected_version"] != current:
            return jsonify({"error": "conflict", "current": current}), 409
        rules = graph_rules_proto.rule_report(graph)
        if rules:
            return jsonify({"error": "rules_broken", "rules": rules}), 422
        start = wmodel.read_graph(graph_id)
        kind = "editor"
        try:
            if isinstance(body.get("changes"), list):
                entries = [graph_changes.clean(c) for c in body["changes"]]
                if not graph_changes.same(graph_changes.replay(start, entries), graph):
                    return jsonify({"error": "changes_do_not_match"}), 422         # a record that does not give the kept version would explain nothing (NFR-20)
            else:
                entries, kind = graph_changes.diff(start, graph), "derived"
        except (ValueError, KeyError, TypeError):
            return jsonify({"error": "changes_do_not_match"}), 422
        wmodel.author = g.account                         # the version names the account that kept it (the prototype serves one request at a time)
        saved = wmodel.save_graph(graph)
        if not saved.saved:
            return jsonify({"error": "refused", "rule": saved.rule, "detail": saved.detail, "named": saved.named}), 422
        logged = None
        if saved.version != current:
            logged = record_changes(graph_id, current, saved.version, entries, kind)
        return jsonify({"version": saved.version, "changed": saved.version != current, "logged": logged, "entries": len(entries), **sync_graph(graph_id)})

    @app.post("/api/v2/graphs/<path:graph_id>/run")
    def run_graph(graph_id):
        """a run behind the refusal (FR-64): a graph that breaks a rule, or has an input nobody supplies, is refused before any step runs and every broken part is named.
        The steps here are stand-ins that only note that they ran (the runner of G-V4.GRAPHAPI.RUN is not part of this prototype)."""
        denied = owner_only()
        if denied:
            return denied
        body = request.get_json(silent=True) or {}
        inputs = body.get("inputs") if isinstance(body.get("inputs"), dict) else {}
        try:
            if "graph" in body:                                # the working copy of the editor: what is on the screen is what is tried, kept or not
                graph = full_graph(graph_id, body)
                if graph is None:
                    return jsonify({"error": "invalid", "detail": "graph"}), 422
            else:
                version = body.get("version") if isinstance(body.get("version"), int) and not isinstance(body.get("version"), bool) else None
                graph = model.read_graph(graph_id, version)
        except StorageError:
            return jsonify({"error": "not_found"}), 404
        ran = []
        def stand_in(step_id):
            def f(values):
                ran.append(step_id)
                return "ran " + step_id
            return f
        steps = {n["id"]: stand_in(n["id"]) for n in graph["nodes"] if (n.get("data") or {}).get("type") != "data"}
        result, said = graph_rules_proto.run_guarded(graph_run.GraphRunner(lambda step: "trusted"), graph, steps, inputs)
        out = {"status": result.status, "ran": ran, "broken": said["broken"], "order": ran}
        return jsonify(out), (422 if result.status == "refused" else 200)

    @app.post("/api/v2/graphs/<path:graph_id>/copy-step")
    def copy_step(graph_id):
        """copies one step into another graph as an independent copy (FR-94): the same content under a name that is free there, no connections, saved as a new version of the other graph when every rule holds"""
        denied = owner_only()
        if denied:
            return denied
        body = request.get_json(silent=True) or {}
        step_id, target_id = body.get("step"), body.get("target")
        if not isinstance(step_id, str) or not isinstance(target_id, str):
            return jsonify({"error": "invalid", "detail": "step and target"}), 422
        if target_id == graph_id:
            return jsonify({"error": "same_graph"}), 422
        name = body.get("name") if body.get("name") not in (None, "") else step_id
        try:
            version = body.get("version") if isinstance(body.get("version"), int) and not isinstance(body.get("version"), bool) else None
            source = wmodel.read_graph(graph_id, version)         # the version the owner is looking at
            target = wmodel.read_graph(target_id)
            current = max(e["version"] for e in wmodel.graph_versions(target_id))
        except StorageError:
            return jsonify({"error": "not_found"}), 404
        step = next((n for n in source["nodes"] if n["id"] == step_id), None)
        if step is None:
            return jsonify({"error": "not_found", "detail": "step"}), 404
        if not isinstance(name, str) or not name.strip() or "/" in name:
            return jsonify({"error": "invalid", "detail": "name"}), 422
        if any(n["id"] == name for n in target["nodes"]):
            return jsonify({"error": "name_taken", "name": name}), 409
        target["nodes"] = target["nodes"] + [{"id": name, "data": json.loads(json.dumps(step.get("data") or {}))}]   # a deep copy: a later change to either step never reaches the other
        rules = graph_rules_proto.rule_report(target)
        if rules:
            return jsonify({"error": "rules_broken", "rules": rules}), 422
        wmodel.author = g.account
        saved = wmodel.save_graph(target)
        if not saved.saved:
            return jsonify({"error": "refused", "rule": saved.rule, "detail": saved.detail}), 422
        if saved.version != current:
            record_changes(target_id, current, saved.version, [{"op": "add_step", "target": name, "before": None, "after": json.loads(json.dumps(step.get("data") or {})), "reason": None, "note": "copied from %s: %s" % (graph_id, step_id)}], "editor")
        return jsonify({"graph": target_id, "step": name, "version": saved.version, "changed": saved.version != current, **sync_graph(target_id)})

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
    ap.add_argument("--live", default=None, help="the live store the changes are written to (files:<folder> or postgres:<url>); --store is then the copy that is read")
    ap.add_argument("--accounts", default=os.path.join(REPO, "data", "proto_accounts"))
    ap.add_argument("--user", default="owner:secret")
    ap.add_argument("--port", type=int, default=8801)
    ap.add_argument("--aside", default=os.path.join(REPO, "data", "proto_aside"), help="where copy versions that the live store replaces are written (sync)")
    ap.add_argument("--auto-sync", action="store_true", help="with --live: sync when the viewer starts and when it stops in an orderly way (Ctrl+C or SIGTERM), as MIA does")
    a = ap.parse_args()
    acc = Storage(FileBackend(a.accounts))
    name, _, password = a.user.partition(":")
    if not accounts.verify(acc, name, password):
        try:
            accounts.create(acc, name, password, "prototype")
        except Exception as err:      # the account exists with another password
            print("account", name, "exists:", err)
    print("viewer: http://127.0.0.1:%d/  (login %s)" % (a.port, name))
    copy_store, live_store = open_store(a.store), (open_store(a.live) if a.live else None)
    server = create_app(copy_store, acc, a.port, live_store, a.aside)
    if a.auto_sync and live_store is not None:
        import signal
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
        auto = graph_store_sync.AutoSync(live_store, copy_store, a.aside)
        try:
            with auto:
                print("sync at start:", json.dumps(auto.reports[-1]), flush=True)
                server.run("127.0.0.1", a.port)
        finally:
            print("sync at stop:", json.dumps(auto.reports[-1]), flush=True)
    else:
        server.run("127.0.0.1", a.port)
