"""PROTOTYPE (Status: Prototype, never merged): serves the graph app and reads stored record-form graphs from files or PostgreSQL.
Usage: python serve.py files|postgres [port]   (postgres starts a throwaway postgres:16 under podman, like tests/test_storage_postgres.py)"""
import glob, os, sys, tempfile
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), *[".."] * 6))
sys.path[:0] = [REPO, os.path.join(REPO, "tests")]
os.chdir(REPO)
from flask import Flask, jsonify, request, send_from_directory
import graph_model, pipeline_graph
from library import Library
from skill_converter import _latest_nodes
from skill_store import load_skill
from storage import Storage
from storage_files import FileBackend

def seed(model):
    nodes, lib = _latest_nodes("library/nodes"), Library("library")
    for path in sorted(glob.glob("skills/*.md")):
        skill = load_skill(path)
        found = pipeline_graph.convert({k: v for k, v in lib.resolve(skill["pipeline"], "pipeline").items() if not k.startswith("_")}, nodes, 300)
        assert model.save_graph(pipeline_graph.bind_skill(found["graph"], nodes, skill, None)).saved

def make_app(model, graph_ids):
    app = Flask(__name__, static_folder=None)
    here = os.path.dirname(__file__)
    @app.get("/proto/graphs")
    def ids(): return jsonify(sorted(graph_ids))
    @app.get("/proto/graphs/<path:gid>")
    def one(gid): return jsonify(model.read_graph(gid, request.args.get("version", type=int)))
    @app.get("/")
    def index(): return send_from_directory(here, "index.html")
    @app.get("/<path:name>")
    def files(name):   # the prototype's own files first, then the graph app's
        return send_from_directory(here if os.path.exists(os.path.join(here, name)) else os.path.join(REPO, "graph_app"), name)
    return app

if __name__ == "__main__":
    kind, port = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8765
    if kind == "postgres":
        import test_storage_postgres as tp
        from storage_postgres import PostgresBackend
        backend = PostgresBackend(tp.start_database())
    else:
        backend = FileBackend(tempfile.mkdtemp())
    model = graph_model.GraphModel(Storage(backend), author="prototype")
    seed(model)
    make_app(model, backend.ids("graphs")).run("127.0.0.1", port)
