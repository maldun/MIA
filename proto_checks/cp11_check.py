"""PROTOTYPE CP11 checks (not protected tests): the record of changes (FR-76, FR-77), append-only (FR-80), moving with the graph (FR-81). Run: python proto_checks/cp11_check.py"""
import copy, json, os, shutil, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_changes as C, graph_model, graph_proto_app, graph_store_move, graph_store_sync as sy
from storage import Storage, StorageError
from storage_files import FileBackend
from proto_checks.make_sample_store import populate, add_code

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

ORIGIN = {"Origin": "http://127.0.0.1:8801"}
tmp = tempfile.mkdtemp()
live = FileBackend(os.path.join(tmp, "live")); populate(live); add_code(live)
copy_ = FileBackend(os.path.join(tmp, "copy")); graph_store_move.move_store(live, copy_)
acc = Storage(FileBackend(os.path.join(tmp, "a"))); accounts.create(acc, "owner", "secret", "cp11"); time.sleep(1.2); accounts.create(acc, "guest", "secret2", "cp11")
app = graph_proto_app.create_app(copy_, acc, live=live, aside=os.path.join(tmp, "aside")); o, gst = app.test_client(), app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN); gst.post("/api/login", json={"user": "guest", "password": "secret2"}, headers=ORIGIN)
U = "/api/v2/graphs/cp2.multi"
cur = o.get(U).get_json(); start = cur["graph"]; v0 = cur["current"]
nodes = {n["id"]: n for n in start["nodes"]}
tool_step = next(n for n in start["nodes"] if n["data"]["type"] == "transform")

# five changes of one session, two with a reason
five = []
g = copy.deepcopy(start)
def do(op, target, before, after, reason=None, **extra):
    global g
    ch = {"op": op, "target": target, "before": before, "after": after, "reason": reason, **extra}
    g = C.apply_change(g, ch); five.append(ch)
do("add_step", "new.in", None, {"type": "data", "value": "hello"}, "a start value for the test")
do("add_step", "new.step", None, {"type": "transform", "toolbox_id": "check.number"})
do("add_connection", "e90", None, {"from": "new.in", "to": "new.step", "data": {}})
do("change_step", tool_step["id"], tool_step["data"], {**tool_step["data"], "toolbox_id": "check.number"}, "the number check is enough here")
do("add_step", "tmp", None, {"type": "data"})
r = o.put(U, json={"graph": {"nodes": g["nodes"], "edges": g["edges"]}, "expected_version": v0, "changes": five}, headers=ORIGIN)
check("FR-76 a session of five changes keeps one version and records five entries", r.status_code == 200 and r.get_json()["entries"] == 5 and r.get_json()["logged"] is True, json.dumps(r.get_json())[:100])
log = {e["version"]: e for e in o.get(U + "/changes").get_json()}
rec = log[v0 + 1]
check("FR-76 each entry names the account and time of the keep, what it did with the value before and after, and the version it started from", rec["author"] == "owner" and rec["time"] and rec["from_version"] == v0 and [e["op"] for e in rec["entries"]] == [c["op"] for c in five] and rec["entries"][3]["before"] == tool_step["data"] and rec["entries"][3]["after"]["toolbox_id"] == "check.number")
check("FR-77 the reason is shown with its entry, and a change without a reason is shown as such", [e["reason"] for e in rec["entries"]] == ["a start value for the test", None, None, "the number check is enough here", None])
check("FR-78 (early) playing the entries on the starting version gives the saved version", C.same(C.replay(start, rec["entries"]), o.get(U).get_json()["graph"]))
check("NFR-20 the versions made before the record are listed as such, the new one as recorded", all(log[v]["kind"] == "before_the_record" for v in range(1, v0 + 1)) and rec["kind"] == "editor")

# a record that does not give the kept version is refused, nothing is written
bad = copy.deepcopy(five[:2]); g2 = C.replay(o.get(U).get_json()["graph"], [])
g2["nodes"].append({"id": "other", "data": {"type": "data"}})
vb = len(live.versions("graphs", "cp2.multi"))
r = o.put(U, json={"graph": {"nodes": g2["nodes"], "edges": g2["edges"]}, "expected_version": v0 + 1, "changes": [{"op": "add_step", "target": "somewhere.else", "before": None, "after": {"type": "data"}}]}, headers=ORIGIN)
check("FR-76 entries that do not lead to the kept graph are refused and nothing is written", r.status_code == 422 and r.get_json()["error"] == "changes_do_not_match" and len(live.versions("graphs", "cp2.multi")) == vb and not live.versions("graph_changes", "cp2.multi/%d" % (vb + 1)))
# without entries: worked out
cur = o.get(U).get_json(); g3 = copy.deepcopy(cur["graph"]); g3["nodes"] = [n for n in g3["nodes"] if n["id"] != "tmp"]; nd = next(n for n in g3["nodes"] if n["id"] == "new.in"); nd["data"] = {"type": "data", "value": "bye"}
r = o.put(U, json={"graph": {"nodes": g3["nodes"], "edges": g3["edges"]}, "expected_version": cur["current"]}, headers=ORIGIN)
rec2 = {e["version"]: e for e in o.get(U + "/changes").get_json()}[cur["current"] + 1]
check("FR-76 a keep without entries from the editor gets the entries worked out from the difference, marked as such", r.status_code == 200 and rec2["kind"] == "derived" and [e["op"] for e in rec2["entries"]] == ["remove_step", "change_step"] and C.same(C.replay(cur["graph"], rec2["entries"]), g3))
# moves are not entries
n_before = len(o.get(U + "/changes").get_json()); lv = len(live.versions("graphs", "cp2.multi"))
o.put(U + "/arrangement", json={"positions": {"new.in": {"x": 1, "y": 2}}}, headers=ORIGIN)
check("FR-76 moving a step is not an entry and makes no version", len(o.get(U + "/changes").get_json()) == n_before and len(live.versions("graphs", "cp2.multi")) == lv)
# restore
cv = o.get(U).get_json()["current"]
r = o.post(U + "/restore", json={"version": 2, "reason": "back to the first working state"}, headers=ORIGIN)
rr = {e["version"]: e for e in o.get(U + "/changes").get_json()}[r.get_json()["version"]]
check("FR-76 a restore is one entry that names the version it restored, with its reason", rr["kind"] == "restore" and rr["from_version"] == cv and rr["entries"][0]["op"] == "restore" and rr["entries"][0]["target"] == 2 and rr["entries"][0]["reason"] == "back to the first working state")
# copy a step
r = o.post("/api/v2/graphs/sample.code/copy-step", json={"step": "step.check", "target": "cp2.multi", "name": "copied.in"}, headers=ORIGIN)
rc = {e["version"]: e for e in o.get(U + "/changes").get_json()}[r.get_json()["version"]]
check("FR-76 a step copied into the graph is an entry of that graph, naming where it came from", rc["entries"][0]["op"] == "add_step" and "copied from sample.code: step.check" in rc["entries"][0]["note"])
# every recorded version replays from the one it started from
allv = o.get(U + "/changes").get_json(); gm = graph_model.GraphModel(Storage(copy_))
ok = all(C.same(C.replay(gm.read_graph("cp2.multi", e["from_version"]), e["entries"], lambda n: gm.read_graph("cp2.multi", n)), gm.read_graph("cp2.multi", e["version"])) for e in allv if e["kind"] != "before_the_record")
check("NFR-20 every recorded version is given again by playing its entries on the version it started from", ok and sum(e["kind"] != "before_the_record" for e in allv) == 4)

# ---- append-only (FR-80) ----
st = Storage(live); rid = "cp2.multi/%d" % (v0 + 1); before = live.versions("graph_changes", rid)
try: st.put("graph_changes", rid, {**before[0]["doc"], "entries": []}, "intruder"); put = None
except StorageError as e: put = e
try: st.delete("graph_changes", rid, "intruder"); dele = None
except StorageError as e: dele = e
check("FR-80 a recorded change cannot be altered: the write is refused (append_only) and the record is unchanged", put is not None and put.rule == "append_only" and live.versions("graph_changes", rid) == before)
check("FR-80 a recorded change cannot be deleted: the delete is refused and the record is unchanged", dele is not None and dele.code == "immutable" and live.versions("graph_changes", rid) == before)
check("FR-80 the page has no way to alter or delete a record: writing to the address of the record is refused (no such graph, or no such method) and nothing changes", all(c >= 400 for c in (o.put(U + "/changes", json={"graph": {"nodes": [], "edges": []}}, headers=ORIGIN).status_code, o.delete(U + "/changes", headers=ORIGIN).status_code, o.post(U + "/changes", json={}, headers=ORIGIN).status_code)) and live.versions("graph_changes", rid) == before)

# ---- moving with the graph (FR-81) ----
snap = lambda b: {i: b.versions("graph_changes", i) for i in b.ids("graph_changes")}
check("FR-81 the records are in the copy store too: the keep synced them with the graph", snap(live) == snap(copy_) and len(snap(live)) == 4)
files2 = FileBackend(os.path.join(tmp, "files2")); graph_store_move.move_store(live, files2)
check("FR-81 a whole-store move brings every entry unchanged", snap(files2) == snap(live))
one = FileBackend(os.path.join(tmp, "one")); graph_store_move.move_graph(live, one, "cp2.multi")
check("FR-81 moving one graph brings its records and no other", snap(one) == snap(live))
mm = graph_model.GraphModel(Storage(one))
check("FR-81 playback at the destination gives the same result", all(C.same(C.replay(mm.read_graph("cp2.multi", e["from_version"]), e["entries"], lambda n: mm.read_graph("cp2.multi", n)), mm.read_graph("cp2.multi", e["version"])) for e in [r for r in allv if r["kind"] != "before_the_record"]))
pg = FileBackend(os.path.join(tmp, "pg")); graph_store_move.move_store(live, pg)
# a copy with a different record of the same change: a conflict, set aside (the live store wins)
other = FileBackend(os.path.join(tmp, "other")); graph_store_move.move_store(live, other)
e1 = other.versions("graph_changes", rid)[0]; other.remove("graph_changes", rid); other.append("graph_changes", rid, {**e1, "author": "forger"})
l = sy.lag(live, other)
check("FR-81 a different record of the same change on the copy is a conflict of that graph", l["cp2.multi"]["state"] == "differs")
out = sy.sync_store(live, other, os.path.join(tmp, "aside2"))
aside = json.load(open(out["set_aside"]["cp2.multi"]["file"]))
check("FR-81 the live store wins: the copy's record is set aside with the graph and the copy equals the live store again", snap(other) == snap(live) and any(k.startswith("graph_changes|") and v[0]["author"] == "forger" for k, v in aside["members"].items()))
# the whole-store sync of a set of files made earlier brings the records of later changes
late = FileBackend(os.path.join(tmp, "late")); graph_store_move.move_store(live, late)
gmodel = graph_model.GraphModel(Storage(live), author="elsewhere"); gg = gmodel.read_graph("cp2.multi"); gg["nodes"][0]["data"]["value"] = "z"; gmodel.save_graph(gg)
Storage(live).put("graph_changes", "cp2.multi/%d" % (len(live.versions("graphs", "cp2.multi"))), {"graph": "cp2.multi", "version": len(live.versions("graphs", "cp2.multi")), "from_version": len(live.versions("graphs", "cp2.multi")) - 1, "kind": "editor", "entries": []}, "elsewhere")
sy.sync_store(live, late, os.path.join(tmp, "aside3"))
check("FR-81 the sync carries the records of later changes", snap(late) == snap(live))
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
