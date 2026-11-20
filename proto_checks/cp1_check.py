"""PROTOTYPE CP1 checks (not protected tests): scoped storage of graphs (FR-57, FR-60, NFR-16 of G-V4.GRAPHSTORE.CORE).
Run: python proto_checks/cp1_check.py [files|postgres]"""
import copy, glob, json, os, sys, tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO, os.path.join(REPO, "tests")]
os.chdir(REPO)
import graph_model, graph_tables, pipeline_graph
from library import Library
from skill_converter import _latest_nodes
from skill_store import load_skill
from storage import Storage, StorageError
from storage_files import FileBackend

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

def converted():
    nodes, lib, out = _latest_nodes("library/nodes"), Library("library"), []
    for path in sorted(glob.glob("skills/*.md")):
        skill = load_skill(path)
        found = pipeline_graph.convert({k: v for k, v in lib.resolve(skill["pipeline"], "pipeline").items() if not k.startswith("_")}, nodes, 300)
        out.append(pipeline_graph.bind_skill(found["graph"], nodes, skill, None))
    return out

def backend(kind):
    if kind == "postgres":
        import test_storage_postgres as tp
        from storage_postgres import PostgresBackend
        url = tp.start_database()
        return PostgresBackend(url), tp.stop_database
    return FileBackend(tempfile.mkdtemp()), (lambda: None)

def small(gid, write_description="a"):
    """a tiny graph whose step `step.write` has its own content"""
    return {"id": gid, "context_graph_id": "ctx", "testbench_id": "tb", "description": "cp1",
            "nodes": [{"id": "var.in", "data": {"type": "data", "value": write_description}},
                      {"id": "step.write", "data": {"type": "transform", "toolbox_id": "tool.write." + write_description}},
                      {"id": "var.out", "data": {"type": "data"}}],
            "edges": [{"id": "e1", "from": "var.in", "to": "step.write", "data": {}}, {"id": "e2", "from": "step.write", "to": "var.out", "data": {}}]}

def run(kind):
    be, stop = backend(kind)
    try:
        model = graph_model.GraphModel(Storage(be), author="cp1")
        graphs = converted()
        # 1. the converted graphs round-trip with local IDs
        ok = all(model.save_graph(g).saved for g in graphs)
        same = all(json.dumps(model.read_graph(g["id"]), sort_keys=True) == json.dumps(g, sort_keys=True) for g in graphs)
        check(f"[{kind}] {len(graphs)} converted graphs are saved and read back identical (local IDs)", ok and same)
        stored_ids = be.ids("graph_nodes")
        check(f"[{kind}] every step record ID is scoped `<graph>/<local>`", all(graph_tables.split_scoped(i) for i in stored_ids), f"{len(stored_ids)} step records")
        shared = {g["id"] + "/" + n["id"] for g in graphs for n in g["nodes"]}
        check(f"[{kind}] steps with the same local name in several graphs are separate records (one record per step per graph)", len(stored_ids) == len(shared) == sum(len(g["nodes"]) for g in graphs), f"{len(stored_ids)} records for 107 distinct local names")
        # 2. same local name, different graphs, independent histories
        a, b = small("cp1.a", "x"), small("cp1.b", "y")
        model.save_graph(a); model.save_graph(b)
        a2 = copy.deepcopy(a); a2["nodes"][1]["data"]["toolbox_id"] = "tool.write.changed"; a2["description"] = "cp1 changed"
        model.save_graph(a2)
        ha, hb = model.step_history("cp1.a", "step.write"), model.step_history("cp1.b", "step.write")
        check(f"[{kind}] a change of `step.write` in graph A leaves graph B and its step history untouched", len(ha) == 2 and len(hb) == 1 and model.read_graph("cp1.b") == b)
        # 3. versions and authors
        vs = model.graph_versions("cp1.a")
        check(f"[{kind}] versions are listed with author and time, none deleted", [v["version"] for v in vs] == [1, 2] and all(v["author"] == "cp1" and v["time"] for v in vs))
        # 4. an unchanged save is no new version
        r = model.save_graph(a2)
        check(f"[{kind}] saving an unchanged graph makes no new version", r.saved and r.version == 2 and len(model.graph_versions("cp1.a")) == 2)
        # 5. the storage refuses unscoped IDs
        refused = []
        for table, rid, doc in (("graph_nodes", "plain", {"id": "plain", "data": {"type": "data"}}),):
            try:
                model.tables.put(table, rid, doc, "cp1")
            except StorageError as e:
                refused.append(e.rule)
        head = model.tables.get("graphs", "cp1.a")["doc"]
        foreign = copy.deepcopy(head); foreign["data"]["nodes"][0]["id"] = "cp1.b/var.in"
        try:
            model.tables.put("graphs", "cp1.a", foreign, "cp1")
        except StorageError as e:
            refused.append(e.rule)
        check(f"[{kind}] the storage layer refuses an unscoped step ID and a header that pins a step of another graph", refused == ["unscoped_id", "unscoped_id"], str(refused))
        # 6. a refused save leaves nothing behind
        before = (sorted(be.ids("graph_nodes")), sorted(be.ids("graph_edges")), len(be.versions("graph_nodes", "cp1.a/step.write")), len(model.graph_versions("cp1.a")))
        bad = copy.deepcopy(a2); bad["edges"].append({"id": "e3", "from": "var.out", "to": "step.write", "data": {}})       # a cycle
        r1 = model.save_graph(bad)
        bad2 = copy.deepcopy(a2); bad2["nodes"][1]["data"]["toolbox_id"] = "tool.other"; bad2["edges"].append({"id": "e9", "from": "var.in", "to": "var.gone", "data": {}})  # an edge to a missing step
        r2 = model.save_graph(bad2)
        after = (sorted(be.ids("graph_nodes")), sorted(be.ids("graph_edges")), len(be.versions("graph_nodes", "cp1.a/step.write")), len(model.graph_versions("cp1.a")))
        check(f"[{kind}] a refused save (a cycle, an edge to a missing step) is no version and leaves no step version behind", not r1.saved and not r2.saved and before == after, f"{r1.named or r1.rule}, {r2.named or r2.rule}")
        # 7. an interrupted save (failure when the header is written) leaves the graph as it was
        c = copy.deepcopy(a2); c["nodes"][1]["data"]["toolbox_id"] = "tool.interrupted"
        real_put = model.tables.put
        def flaky(table, rid, doc, author, expected_version=None):
            if table == "graphs":
                raise RuntimeError("power cut")
            return real_put(table, rid, doc, author, expected_version)
        model.tables.put = flaky
        try:
            model.save_graph(c)
        except RuntimeError:
            pass
        model.tables.put = real_put
        check(f"[{kind}] after an interrupted save the graph reads as before and its step history shows no unused version",
              model.read_graph("cp1.a") == a2 and len(model.graph_versions("cp1.a")) == 2 and len(model.step_history("cp1.a", "step.write")) == 2)
        r = model.save_graph(c)
        check(f"[{kind}] the interrupted save can be run again to finish", r.saved and r.version == 3 and len(model.step_history("cp1.a", "step.write")) == 3)
    finally:
        stop()

if __name__ == "__main__":
    for kind in (sys.argv[1:] or ["files"]):
        run(kind)
    failed = [n for n, ok, _ in results if not ok]
    print("\n%d checks, %d failed" % (len(results), len(failed)))
    sys.exit(1 if failed else 0)
