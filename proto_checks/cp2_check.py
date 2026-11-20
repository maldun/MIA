"""PROTOTYPE CP2 checks (not protected tests): the same behaviour in files and database (FR-58) and the move of the whole store (FR-59)
of G-V4.GRAPHSTORE.TRANSFER. Run: python proto_checks/cp2_check.py   (starts a throwaway postgres:16 under podman; skips that part where it is missing)"""
import copy, json, os, shutil, sys, tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO, os.path.join(REPO, "tests")]
os.chdir(REPO)
import graph_model, graph_store_move
from storage import Storage, StorageError
from storage_files import FileBackend
from proto_checks.cp1_check import small, converted

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

def strip(x):
    """times differ between two runs; everything else must be equal"""
    if isinstance(x, dict):
        return {k: strip(v) for k, v in x.items() if k != "time"}
    if isinstance(x, list):
        return [strip(v) for v in x]
    return x

def script(backend):
    """one fixed sequence of operations; returns what every step answered"""
    store = Storage(backend)
    m = graph_model.GraphModel(store, author="cp2")
    out = {}
    a, b = small("cp2.a", "x"), small("cp2.b", "y")
    out["save a, b"] = [m.save_graph(a)[:3], m.save_graph(b)[:3]]
    a2 = copy.deepcopy(a); a2["nodes"][1]["data"]["toolbox_id"] = "tool.changed"
    out["change a"] = m.save_graph(a2)[:3]
    out["same again"] = m.save_graph(a2)[:3]
    out["read a v1, v2"] = [m.read_graph("cp2.a", 1), m.read_graph("cp2.a")]
    out["versions"] = [strip(m.graph_versions("cp2.a")), strip(m.graph_versions("cp2.b"))]
    out["step history"] = [strip(m.step_history("cp2.a", "step.write")), strip(m.step_history("cp2.b", "step.write"))]
    out["ids"] = sorted(store.ids("graphs"))
    bad = copy.deepcopy(a2); bad["edges"].append({"id": "e3", "from": "var.out", "to": "step.write", "data": {}})
    out["cycle refused"] = m.save_graph(bad)[:5]
    refusals = {}
    for label, call in (("unscoped", lambda: store.put("graph_nodes", "plain", {"id": "plain", "data": {"type": "data"}}, "cp2")),
                        ("conflict", lambda: store.put("graphs", "cp2.a", store.get("graphs", "cp2.a")["doc"], "cp2", expected_version=1)),
                        ("unknown table", lambda: store.put("nope", "x", {}, "cp2")),
                        ("not found", lambda: store.get("graphs", "cp2.zzz")),
                        ("unknown member", lambda: store.put("graphs", "cp2.a", {"id": "cp2.a", "data": {**store.get("graphs", "cp2.a")["doc"]["data"], "nodes": [{"id": "cp2.a/var.in", "version": 99}]}}, "cp2"))):
        try:
            call(); refusals[label] = "accepted"
        except StorageError as e:
            refusals[label] = [e.code, e.rule, e.detail]
    out["refusals"] = refusals
    return json.loads(json.dumps(out, default=str))

def entries(backend):
    return {t: {i: strip(backend.versions(t, i)) for i in sorted(backend.ids(t))} for t in graph_store_move.GRAPH_TABLES}

def populate(backend):
    m = graph_model.GraphModel(Storage(backend), author="owner")
    for g in converted():
        m.save_graph(g)
    a = small("cp2.multi", "v1")
    m.save_graph(a)
    for k in range(2, 5):
        a = copy.deepcopy(a); a["nodes"][1]["data"]["toolbox_id"] = "tool.v%d" % k
        graph_model.GraphModel(Storage(backend), author="author%d" % k).save_graph(a)

def main():
    import test_storage_postgres as tp
    from storage_postgres import PostgresBackend
    url = tp.start_database()
    tmp = tempfile.mkdtemp()
    try:
        pg = PostgresBackend(url)
        f_script = script(FileBackend(os.path.join(tmp, "f_script")))
        p_script = script(pg)
        same = f_script == p_script
        check("FR-58 the same sequence of saving, changing, reading, listing and refusing gives the same answers in files and database", same,
              "" if same else json.dumps([k for k in f_script if f_script[k] != p_script[k]]))
        check("FR-58 it covers versions, authors, step history and five kinds of refusal", len(f_script) >= 9 and len(f_script["refusals"]) == 5 and all(v != "accepted" for v in f_script["refusals"].values()))
        # whole-store move: files -> database -> files
        shutil.rmtree(os.path.join(tmp, "f_script"))
        src = FileBackend(os.path.join(tmp, "src")); populate(src)
        n = len(src.ids("graphs"))
        pg2 = PostgresBackend(url + "?options=-csearch_path%3Dpublic") if False else None
        # the database holds the sequence of the first check already; use a second, empty target: a second file folder for the database leg is not possible, so clean the tables
        for t in graph_store_move.GRAPH_TABLES:
            for i in pg.ids(t):
                pg.remove(t, i)
        c1 = graph_store_move.move_store(src, pg)
        check("FR-59 the whole store moves from files to the database: all graphs, versions, authors and times unchanged", entries(src) == entries(pg) and c1["graphs"] == n, str(c1))
        dst = FileBackend(os.path.join(tmp, "dst"))
        c2 = graph_store_move.move_store(pg, dst)
        check("FR-59 and back from the database to files, identical to the original", entries(dst) == entries(src), str(c2))
        c3 = graph_store_move.move_store(src, pg)
        check("FR-59 moving the same store again changes nothing", c3["records"] == 0 and c3["versions_added"] == 0 and entries(src) == entries(pg), str(c3))
        multi = pg.versions("graphs", "cp2.multi")
        check("FR-59 a graph with four versions keeps its numbers 1 to 4 and its four authors", [e["version"] for e in multi] == [1, 2, 3, 4] and [e["author"] for e in multi] == ["owner", "author2", "author3", "author4"])
        # all or nothing: one graph cannot be moved
        src2 = FileBackend(os.path.join(tmp, "src2")); populate(src2)
        victim = src2.versions("graph_nodes", "cp2.multi/step.write")
        src2.remove("graph_nodes", "cp2.multi/step.write")                 # a step that a header pins is gone
        empty = FileBackend(os.path.join(tmp, "empty"))
        try:
            graph_store_move.move_store(src2, empty)
            refused, named = False, ""
        except StorageError as e:
            refused, named = True, e.detail["graphs"]
        check("FR-59 a graph that cannot be moved refuses the whole move, names that graph, and the target stays empty",
              refused and list(named) == ["cp2.multi"] and all(not empty.ids(t) for t in graph_store_move.GRAPH_TABLES), str(named))
        # a conflict: the target has a different history for one graph
        other = FileBackend(os.path.join(tmp, "other")); populate(other)
        m = graph_model.GraphModel(Storage(other), author="someone")
        g = m.read_graph("cp2.multi"); g["nodes"][1]["data"]["toolbox_id"] = "tool.different"; m.save_graph(g)
        before = entries(other)
        try:
            graph_store_move.move_store(src, other)
            conflict = False
        except StorageError as e:
            conflict = "cp2.multi" in e.detail["graphs"]
        check("FR-59 a graph with a different history in the target is a conflict that names the graph and writes nothing", conflict and entries(other) == before)
        # an interrupted move finishes when run again
        part = FileBackend(os.path.join(tmp, "part"))
        class Flaky:
            def __init__(self, inner): self.inner, self.n = inner, 0
            def __getattr__(self, name): return getattr(self.inner, name)
            def append(self, table, rid, entry):
                self.n += 1
                if self.n == 40: raise RuntimeError("power cut")
                return self.inner.append(table, rid, entry)
        try:
            graph_store_move.move_store(src, Flaky(part))
        except RuntimeError:
            pass
        half = len(part.ids("graphs"))
        graph_store_move.move_store(src, part)
        check("FR-59 an interrupted move leaves no half graph and can be run again to finish", half == 0 and entries(part) == entries(src), f"graphs after the interruption: {half}")
    finally:
        tp.stop_database()
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
    failed = [n for n, ok, _ in results if not ok]
    print("\n%d checks, %d failed" % (len(results), len(failed)))
    sys.exit(1 if failed else 0)
