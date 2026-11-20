"""PROTOTYPE: builds a sample store of graphs in a folder (the 15 converted skill graphs and one graph with four versions by four authors).
Usage: python proto_checks/make_sample_store.py <folder> [--broken]   (--broken adds a graph with a connection to a missing step)"""
import os, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
from storage_files import FileBackend
from proto_checks.cp2_check import populate

def add_broken(backend):
    """a graph written around the checks of the storage layer: a connection to a step that does not exist (to show what the viewer does with it)"""
    def put(table, rid, doc):
        backend.append(table, rid, {"id": rid, "version": 1, "author": "sample", "time": "2026-11-20T12:00:00Z", "doc": doc})
    g = "sample.broken"
    steps = {"var.in": {"type": "data", "value": "x"}, "step.a": {"type": "transform", "toolbox_id": "tool.a"}}
    for local, data in steps.items():
        put("graph_nodes", "%s/%s" % (g, local), {"id": "%s/%s" % (g, local), "data": data})
    for local, a, b in (("e1", "var.in", "step.a"), ("e2", "step.a", "var.gone")):
        put("graph_edges", "%s/%s" % (g, local), {"id": "%s/%s" % (g, local), "from": "%s/%s" % (g, a), "to": "%s/%s" % (g, b), "data": {}})
    put("graphs", g, {"id": g, "data": {"kind": "workflow", "context_graph_id": "ctx", "testbench_id": "tb", "description": "a connection to a missing step",
                                       "nodes": [{"id": "%s/%s" % (g, k), "version": 1} for k in steps], "edges": [{"id": "%s/e1" % g, "version": 1}, {"id": "%s/e2" % g, "version": 1}]}})


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    backend = FileBackend(args[0])
    populate(backend)
    if "--broken" in sys.argv:
        add_broken(backend)
    print("sample store in %s: %d graphs, %d step records" % (args[0], len(backend.ids("graphs")), len(backend.ids("graph_nodes"))))
