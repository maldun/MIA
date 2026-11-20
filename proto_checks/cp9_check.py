"""PROTOTYPE CP9 checks (not protected tests): restore (FR-73), changes written to the live store (FR-95, FR-71), the editor refused when the live store cannot be reached (FR-95),
a first sync (FR-93 of TRANSFER, early). Run: python proto_checks/cp9_check.py"""
import copy, json, os, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_proto_app, graph_store_move
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

class Down:
    """a live store that cannot be reached: every call fails like a lost connection"""
    def __init__(self, inner): self.inner = inner
    def __getattr__(self, name):
        def fail(*a, **k): raise ConnectionError("the live store is gone")
        return fail

ORIGIN = {"Origin": "http://127.0.0.1:8801"}
tmp = tempfile.mkdtemp()
live = FileBackend(os.path.join(tmp, "live")); populate(live)
copy_ = FileBackend(os.path.join(tmp, "copy")); graph_store_move.move_store(live, copy_)
acc = Storage(FileBackend(os.path.join(tmp, "a")))
accounts.create(acc, "owner", "secret", "cp9"); time.sleep(1.2); accounts.create(acc, "guest", "secret2", "cp9")
def clients(app):
    o, gst = app.test_client(), app.test_client()
    o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN); gst.post("/api/login", json={"user": "guest", "password": "secret2"}, headers=ORIGIN)
    return o, gst
app = graph_proto_app.create_app(copy_, acc, live=live)
o, gst = clients(app)
U = "/api/v2/graphs/cp2.multi"
body = lambda g, **kw: {"graph": {"nodes": g["nodes"], "edges": g["edges"]}, **kw}
cur = o.get(U).get_json()["graph"]

check("FR-95 with a live store and a copy, the status says both are there and the copy is not behind", o.get("/api/v2/status").get_json() == {"split": True, "live": "reachable", "lag": 0})
changed = copy.deepcopy(cur); changed["nodes"][1]["data"]["toolbox_id"] = "check.number"
r = o.put(U, json=body(changed, expected_version=4), headers=ORIGIN)
live_versions = [e["version"] for e in live.versions("graphs", "cp2.multi")]
copy_versions = [e["version"] for e in copy_.versions("graphs", "cp2.multi")]
check("FR-95 a kept change is stored in the live store, not in the copy", r.status_code == 200 and live_versions == [1, 2, 3, 4, 5] and copy_versions == [1, 2, 3, 4])
check("FR-95 the viewer still shows the copy until the sync, and says how far it is behind", o.get(U).get_json()["current"] == 4 and o.get("/api/v2/status").get_json()["lag"] == 1)
more = copy.deepcopy(changed); more["nodes"][0]["data"]["value"] = "other"
check("FR-72 a change made on the version of the copy is refused when the live store has moved on: nothing is overwritten", o.put(U, json=body(more, expected_version=4), headers=ORIGIN).status_code == 409 and [e["version"] for e in live.versions("graphs", "cp2.multi")] == [1, 2, 3, 4, 5])
check("a sync is for the owner only", gst.post("/api/v2/sync", headers=ORIGIN).status_code == 403)
s = o.post("/api/v2/sync", headers=ORIGIN)
check("FR-93 the sync brings the copy up to date, as the whole move: nothing lost, repeatable", s.status_code == 200 and [e["version"] for e in copy_.versions("graphs", "cp2.multi")] == [1, 2, 3, 4, 5] and o.get("/api/v2/status").get_json()["lag"] == 0 and o.post("/api/v2/sync", headers=ORIGIN).get_json()["records"] == 0, json.dumps(s.get_json()))
check("FR-93 after the sync the viewer shows the kept change", o.get(U).get_json()["graph"]["nodes"][1]["data"]["toolbox_id"] == "check.number" and o.get(U).get_json()["author"] == "owner")

# restore
r = o.post(U + "/restore", json={"version": 2}, headers=ORIGIN)
v = [e["version"] for e in live.versions("graphs", "cp2.multi")]
old2 = json.loads(json.dumps(live and graph_proto_app.graph_model.GraphModel(Storage(live)).read_graph("cp2.multi", 2)))
check("FR-73 restoring version 2 makes a new version with its content; versions 1 to 5 are unchanged", r.status_code == 200 and r.get_json() == {"version": 6, "restored": 2, "changed": True} and v == [1, 2, 3, 4, 5, 6])
check("FR-73 the new version equals version 2, and the versions before it are as they were", graph_proto_app.graph_model.GraphModel(Storage(live)).read_graph("cp2.multi", 6) == old2 and graph_proto_app.graph_model.GraphModel(Storage(live)).read_graph("cp2.multi", 5)["nodes"][1]["data"]["toolbox_id"] == "check.number")
check("FR-73 restoring what is already current changes nothing", o.post(U + "/restore", json={"version": 6}, headers=ORIGIN).get_json()["changed"] is False and len(live.versions("graphs", "cp2.multi")) == 6)
check("FR-73 only the owner restores; an unknown version is a clean not-found", gst.post(U + "/restore", json={"version": 2}, headers=ORIGIN).status_code == 403 and o.post(U + "/restore", json={"version": 99}, headers=ORIGIN).status_code == 404 and o.post(U + "/restore", json={"version": "x"}, headers=ORIGIN).status_code == 404)

# the live store cannot be reached
down_app = graph_proto_app.create_app(copy_, acc, live=Down(live))
od, _ = clients(down_app)
st = od.get("/api/v2/status").get_json()
check("FR-95 when the live store cannot be reached the status says so", st == {"split": True, "live": "unreachable", "lag": None})
check("FR-95 the owner can still look at the graphs of the copy", od.get("/api/v2/graphs").status_code == 200 and od.get(U).status_code == 200 and od.get(U + "/versions").status_code == 200)
before = [len(copy_.versions("graphs", g)) for g in sorted(copy_.ids("graphs"))]
r1 = od.put(U, json=body(changed), headers=ORIGIN); r2 = od.post(U + "/restore", json={"version": 1}, headers=ORIGIN); r3 = od.post(U + "/check", json=body(changed), headers=ORIGIN); r4 = od.post("/api/v2/sync", headers=ORIGIN)
check("FR-95 changing is not possible: keep, restore, check and sync answer that the live store is unreachable, and nothing is written",
      [r.status_code for r in (r1, r2, r3, r4)] == [503] * 4 and all(r.get_json()["error"] == "store_unreachable" for r in (r1, r2, r3, r4)) and before == [len(copy_.versions("graphs", g)) for g in sorted(copy_.ids("graphs"))])
single = graph_proto_app.create_app(Down(copy_), acc)
os_, _ = clients(single)
check("a store that cannot be reached is an answer, not a crash: 503 for every read", os_.get("/api/v2/graphs").status_code == 503 and os_.get(U).get_json() == {"error": "store_unreachable"})
check("an unknown address is still a plain not-found", o.get("/api/v2/nothing").status_code == 404)
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
