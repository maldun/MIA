"""The fixture graphs of G-V4.VIEW (TR-VIEW-002) for the Python checks: read `tests/fixtures/graph_view/graphs.json` and store its versions.

`seed(backend)` stores every version that is not `js_only`, in file order: `model` versions through CORE's GraphModel as their author,
`raw` versions as raw records around the checks (as `sample.broken` in the IF-104 v2 suite). The JS checks read the same file
(`graph_view_data.mjs`), so Python, JS and browser checks see the same graphs.
"""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(os.path.dirname(HERE), "fixtures", "graph_view", "graphs.json")
HOSTILE = '<img src=x onerror=alert(1)> step "quoted" & more'


def versions():
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)["versions"]


def graph(graph_id, version=None):
    """the graph of a fixture as stored: the last version, or the version-th version of that ID (1 = first)"""
    found = [copy.deepcopy(v["graph"]) for v in versions() if v["graph"]["id"] == graph_id]
    return found[-1] if version is None else found[version - 1]


def _seed_raw(backend, g, author):
    gid = g["id"]

    def put(table, rid, doc):
        backend.append(table, rid, {"id": rid, "version": 1, "author": author, "time": "2026-11-20T12:00:00Z", "doc": doc})
    for n in g["nodes"]:
        put("graph_nodes", "%s/%s" % (gid, n["id"]), {"id": "%s/%s" % (gid, n["id"]), "data": n["data"]})
    for e in g["edges"]:
        put("graph_edges", "%s/%s" % (gid, e["id"]),
            {"id": "%s/%s" % (gid, e["id"]), "from": "%s/%s" % (gid, e["from"]), "to": "%s/%s" % (gid, e["to"]), "data": e["data"]})
    put("graphs", gid, {"id": gid, "data": {"kind": g.get("kind", "workflow"), "context_graph_id": g["context_graph_id"], "testbench_id": g["testbench_id"],
                                            "description": g["description"],
                                            "nodes": [{"id": "%s/%s" % (gid, n["id"]), "version": 1} for n in g["nodes"]],
                                            "edges": [{"id": "%s/%s" % (gid, e["id"]), "version": 1} for e in g["edges"]]}})


def seed(backend, ids=None):
    """store the fixture versions (all, or only those of the graph IDs in `ids`) in `backend`; returns {graph ID: number of versions}"""
    import graph_model
    from storage import Storage
    counts = {}
    for v in versions():
        g = copy.deepcopy(v["graph"])
        if v["seed"] == "js_only" or (ids is not None and g["id"] not in ids):
            continue
        if v["seed"] == "raw":
            _seed_raw(backend, g, v["author"])
        else:
            saved = graph_model.GraphModel(Storage(backend), author=v["author"]).save_graph(g)
            assert saved.saved, (g["id"], saved)
        counts[g["id"]] = counts.get(g["id"], 0) + 1
    return counts
