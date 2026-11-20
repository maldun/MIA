"""PROTOTYPE CP12 checks (not protected tests): playback and comparison (FR-78, FR-79, NFR-20) with the page's own code (node) against what the backend stored.
Run: python proto_checks/cp12_check.py"""
import copy, json, os, subprocess, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_changes as C, graph_model, graph_proto_app
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

ORIGIN = {"Origin": "http://127.0.0.1:8801"}
tmp = tempfile.mkdtemp(); store = FileBackend(os.path.join(tmp, "s")); populate(store)
acc = Storage(FileBackend(os.path.join(tmp, "a"))); accounts.create(acc, "owner", "secret", "cp12")
app = graph_proto_app.create_app(store, acc); o = app.test_client(); o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN)
U = "/api/v2/graphs/cp2.multi"
def keep(edit, reasons=None):
    cur = o.get(U).get_json(); g = copy.deepcopy(cur["graph"]); changes = edit(g)
    r = o.put(U, json={"graph": {"nodes": g["nodes"], "edges": g["edges"]}, "expected_version": cur["current"], "changes": changes}, headers=ORIGIN); assert r.status_code == 200, r.get_json(); return r.get_json()["version"]
step = next(n for n in o.get(U).get_json()["graph"]["nodes"] if n["data"]["type"] == "transform")
def e1(g):
    ch = [{"op": "add_step", "target": "a1", "before": None, "after": {"type": "data", "value": "1"}, "reason": "first"},
          {"op": "change_step", "target": step["id"], "before": step["data"], "after": {**step["data"], "toolbox_id": "check.number"}, "reason": None}]
    for c in ch: g.update(C.apply_change(g, c)); 
    return ch
v5 = keep(e1)
def e2(g):
    first_edge = g["edges"][0]
    ch = [{"op": "remove_connection", "target": first_edge["id"], "before": {"from": first_edge["from"], "to": first_edge["to"], "data": first_edge.get("data") or {}}, "after": None}]
    for c in ch: g.update(C.apply_change(g, c))
    return ch
v6 = keep(e2)
r = o.post(U + "/restore", json={"version": 2, "reason": "back"}, headers=ORIGIN); v7 = r.get_json()["version"]
gm = graph_model.GraphModel(Storage(store)); n_versions = len(store.versions("graphs", "cp2.multi"))
dump = {"versions": {n: gm.read_graph("cp2.multi", n) for n in range(1, n_versions + 1)}, "records": o.get(U + "/changes").get_json()}
path = os.path.join(tmp, "dump.json"); json.dump(dump, open(path, "w"))
out = json.loads(subprocess.run(["node", os.path.join(REPO, "proto_checks", "cp12_replay.mjs"), path], capture_output=True, text=True, check=True).stdout)
check("FR-78 the page's own playback of every recorded version (two keeps and a restore) gives exactly the saved version", [x["version"] for x in out["replay"]] == [v5, v6, v7] and all(x["ok"] for x in out["replay"]), json.dumps(out["replay"]))
check("FR-78 a playback has one position per entry", [x["steps"] for x in out["replay"]] == [2, 1, 1])
check("NFR-20 versions made before the record have no entries to play, and are listed as such", [r["kind"] for r in dump["records"][:4]] == ["before_the_record"] * 4)
ok = True
for c in out["compare"]:
    py = C.diff(dump["versions"][str(c["a"])] if str(c["a"]) in dump["versions"] else dump["versions"][c["a"]], dump["versions"][str(c["b"])] if str(c["b"]) in dump["versions"] else dump["versions"][c["b"]])
    ok &= (c["lines"] == len(py)) and (c["none"] == (len(py) == 0))
check("FR-79 for every pair of versions the page lists as many differences as the backend's own difference finds, and says when there are none", ok and len(out["compare"]) == n_versions * (n_versions - 1) // 2, str(len(out["compare"])))
pair = next(c for c in out["compare"] if c["a"] == 1 and c["b"] == v5)
check("FR-79 versions made before the record can be compared too: the differences are found without any record", pair["lines"] >= 2 and pair["marks"] >= 2)
same = [c for c in out["compare"] if c["a"] == 2 and c["b"] == v7]
check("FR-79 a restored version and the version it restored have no difference", same and same[0]["none"] is True, str(same))
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
