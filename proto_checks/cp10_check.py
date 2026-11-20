"""PROTOTYPE CP10 checks (not protected tests): the arrangement saved without a new version, the same for everyone, last move counts (FR-74); copy a step into another graph (FR-94).
Run: python proto_checks/cp10_check.py"""
import copy, json, os, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_proto_app, graph_store_move
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate, add_code

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

class Down:
    def __init__(self, inner): self.inner = inner
    def __getattr__(self, name):
        def fail(*a, **k): raise ConnectionError("the live store is gone")
        return fail

ORIGIN = {"Origin": "http://127.0.0.1:8801"}
tmp = tempfile.mkdtemp()
live = FileBackend(os.path.join(tmp, "live")); populate(live); add_code(live)
copy_ = FileBackend(os.path.join(tmp, "copy")); graph_store_move.move_store(live, copy_)
acc = Storage(FileBackend(os.path.join(tmp, "a")))
accounts.create(acc, "owner", "secret", "cp10"); time.sleep(1.2); accounts.create(acc, "guest", "secret2", "cp10")
app = graph_proto_app.create_app(copy_, acc, live=live)
o, gst = app.test_client(), app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN); gst.post("/api/login", json={"user": "guest", "password": "secret2"}, headers=ORIGIN)
versions = lambda b, gid: [e["version"] for e in b.versions("graphs", gid)]

# ---- FR-74 the arrangement ----
U = "/api/v2/graphs/sample.code"
before = versions(live, "sample.code")
r = o.put(U + "/arrangement", json={"positions": {"var.in": {"x": 10.4, "y": 20}, "step.check": {"x": -5, "y": 7}, "ghost": {"x": 1, "y": 1}}}, headers=ORIGIN)
a = gst.get(U + "/arrangement").get_json()
check("FR-74 the owner saves where the steps are; a place for a step the graph does not have is ignored", r.status_code == 200 and r.get_json()["saved"] == 2 and set(a["positions"]) == {"var.in", "step.check"} and a["positions"]["var.in"] == {"x": 10, "y": 20})
check("FR-74 anyone opening the graph gets the same places, and the version list is unchanged", a["author"] == "owner" and versions(live, "sample.code") == before and versions(copy_, "sample.code") == before and o.get(U + "/versions").get_json() == gst.get(U + "/versions").get_json())
o.put(U + "/arrangement", json={"positions": {"var.in": {"x": 99, "y": 99}}}, headers=ORIGIN)
check("FR-74 the last move counts", gst.get(U + "/arrangement").get_json()["positions"] == {"var.in": {"x": 99, "y": 99}} and gst.get(U + "/arrangement").get_json()["version"] == 2)
check("FR-74 only the owner saves an arrangement", gst.put(U + "/arrangement", json={"positions": {}}, headers=ORIGIN).status_code == 403 and gst.get(U + "/arrangement").get_json()["positions"] == {"var.in": {"x": 99, "y": 99}})
check("FR-74 a place that is not a number is refused", o.put(U + "/arrangement", json={"positions": {"var.in": {"x": "a", "y": 1}}}, headers=ORIGIN).status_code == 422)

# ---- FR-94 copy a step into another graph ----
SRC, DST = "/api/v2/graphs/sample.code", "/api/v2/graphs/cp2.multi"
src_graph = o.get(SRC).get_json()["graph"]; dst_before = o.get(DST).get_json()
step = next(n for n in src_graph["nodes"] if n["id"] == "step.check")
dst_versions = versions(live, "cp2.multi")
r = o.post(SRC + "/copy-step", json={"step": "step.check", "target": "cp2.multi", "name": "copied.check"}, headers=ORIGIN)
dst_after = o.get(DST).get_json()
new = next((n for n in dst_after["graph"]["nodes"] if n["id"] == "copied.check"), None)
check("FR-94 the other graph has a step with the same content, as a new version of that graph", r.status_code == 200 and new is not None and new["data"] == step["data"] and dst_after["current"] == dst_before["current"] + 1 and r.get_json()["version"] == dst_after["current"], json.dumps(r.get_json()))
check("FR-94 the copy is its own step: it has no connections, and the earlier versions of the other graph do not have it", all("copied.check" not in (e["from"], e["to"]) for e in dst_after["graph"]["edges"]) and all(n["id"] != "copied.check" for n in o.get(DST + "?version=%d" % dst_before["current"]).get_json()["graph"]["nodes"]))
check("FR-94 the source graph is unchanged: no new version", versions(live, "sample.code") == before and o.get(SRC).get_json()["graph"] == src_graph)
check("FR-94 the copy reached the copy store at once", r.get_json()["synced"] is True and versions(copy_, "cp2.multi") == versions(live, "cp2.multi") == dst_versions + [dst_versions[-1] + 1])
# a later change to either step does not reach the other
changed = copy.deepcopy(src_graph); next(n for n in changed["nodes"] if n["id"] == "step.check")["data"]["toolbox_id"] = "check.claim"
rk = o.put(SRC, json={"graph": {"nodes": changed["nodes"], "edges": changed["edges"]}, "expected_version": o.get(SRC).get_json()["current"]}, headers=ORIGIN)
check("FR-94 a later change to the source step does not change the copy", rk.status_code == 200 and next(n for n in o.get(DST).get_json()["graph"]["nodes"] if n["id"] == "copied.check")["data"] == step["data"])
d2 = o.get(DST).get_json()["graph"]; nd = copy.deepcopy(d2); next(n for n in nd["nodes"] if n["id"] == "copied.check")["data"]["toolbox_id"] = "check.other"
o.put(DST, json={"graph": {"nodes": nd["nodes"], "edges": nd["edges"]}, "expected_version": o.get(DST).get_json()["current"]}, headers=ORIGIN)
check("FR-94 a later change to the copy does not change the source step", next(n for n in o.get(SRC).get_json()["graph"]["nodes"] if n["id"] == "step.check")["data"]["toolbox_id"] == "check.claim")
# names, targets, rules
check("FR-94 a name that is used in the other graph is refused, naming it; nothing is written", o.post(SRC + "/copy-step", json={"step": "step.check", "target": "cp2.multi", "name": "copied.check"}, headers=ORIGIN).get_json() == {"error": "name_taken", "name": "copied.check"} and versions(live, "cp2.multi")[-1] == o.get(DST).get_json()["current"])
r = o.post(SRC + "/copy-step", json={"step": "var.code", "target": "cp2.multi"}, headers=ORIGIN)
check("FR-94 without a name the copy keeps the step's name", r.status_code == 200 and r.get_json()["step"] == "var.code", json.dumps(r.get_json()))
check("FR-94 the same graph, an unknown step, an unknown graph and a name with a slash are clean refusals",
      [o.post(SRC + "/copy-step", json=j, headers=ORIGIN).status_code for j in ({"step": "var.in", "target": "sample.code"}, {"step": "nope", "target": "cp2.multi"}, {"step": "var.in", "target": "nope"}, {"step": "var.in", "target": "cp2.multi", "name": "a/b"}, {"target": "cp2.multi"})] == [422, 404, 404, 422, 422])
check("FR-94 only the owner copies a step", gst.post(SRC + "/copy-step", json={"step": "var.in", "target": "cp2.multi", "name": "x"}, headers=ORIGIN).status_code == 403)
# an older version of the source is what the owner is looking at
old = o.get(SRC + "?version=1").get_json()["graph"]
r = o.post(SRC + "/copy-step", json={"step": "step.check", "target": "cp2.multi", "name": "from.v1", "version": 1}, headers=ORIGIN)
check("FR-94 the step is taken from the version the owner is looking at", r.status_code == 200 and next(n for n in o.get(DST).get_json()["graph"]["nodes"] if n["id"] == "from.v1")["data"] == next(n for n in old["nodes"] if n["id"] == "step.check")["data"])
# a copy that breaks a rule is not made
rules_at = o.get(DST).get_json()["current"]
real = graph_proto_app.graph_rules_proto.rule_report
graph_proto_app.graph_rules_proto.rule_report = lambda graph: [{"rule": "adjacency", "text": "stand-in rule", "parts": ["loop.copy"]}]      # no single added step breaks a rule of today's eight, so the refusal is shown with a stand-in
r = o.post(SRC + "/copy-step", json={"step": "loop.review", "target": "cp2.multi", "name": "loop.copy"}, headers=ORIGIN)
graph_proto_app.graph_rules_proto.rule_report = real
check("FR-94 a copy that would break a rule of the other graph is not made: the rule is named and nothing is written", r.status_code == 422 and r.get_json()["rules"][0]["rule"] == "adjacency" and o.get(DST).get_json()["current"] == rules_at)
r = o.post(SRC + "/copy-step", json={"step": "loop.review", "target": "cp2.multi", "name": "loop.copy"}, headers=ORIGIN)
check("FR-94 a loop-controlling step with its limit can be copied", r.status_code == 200 and next(n for n in o.get(DST).get_json()["graph"]["nodes"] if n["id"] == "loop.copy")["data"]["stop"] == {"max_repetitions": 3})
# the live store cannot be reached
down = graph_proto_app.create_app(copy_, acc, live=Down(live)); od = down.test_client(); od.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN)
check("FR-95 with the live store out of reach a copy of a step is refused with that reason", od.post(SRC + "/copy-step", json={"step": "var.in", "target": "cp2.multi", "name": "z"}, headers=ORIGIN).get_json() == {"error": "store_unreachable"})
# the copy store cannot take it: the change stays in the live store and the answer says so
c2 = FileBackend(os.path.join(tmp, "c2")); graph_store_move.move_store(live, c2)
first = c2.versions("graphs", "cp2.multi"); first[0] = {**first[0], "author": "intruder"}; c2.remove("graphs", "cp2.multi")
for e in first: c2.append("graphs", "cp2.multi", e)
app2 = graph_proto_app.create_app(c2, acc, live=live); o2 = app2.test_client(); o2.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN)
n_live = len(live.versions("graphs", "cp2.multi"))
r = o2.post(SRC + "/copy-step", json={"step": "var.in", "target": "cp2.multi", "name": "late"}, headers=ORIGIN)
check("FR-95 when the copy store cannot take the change it stays in the live store and the answer says so", r.status_code == 200 and r.get_json()["synced"] is False and "cp2.multi" in r.get_json()["sync_problem"] and len(live.versions("graphs", "cp2.multi")) == n_live + 1)
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
