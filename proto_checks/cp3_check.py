"""PROTOTYPE CP3 checks (not protected tests): the one-way sync (FR-93), a set of files on another machine (NFR-15), nothing half-stored (NFR-16).
Run: python proto_checks/cp3_check.py"""
import copy, json, os, shutil, subprocess, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_model, graph_proto_app, graph_store_move, graph_store_sync as sy
from storage import Storage, StorageError
from storage_files import FileBackend
from proto_checks.make_sample_store import populate, add_code, add_broken

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

TABLES = ("graph_nodes", "graph_edges", "graphs")
def snapshot(b): return {t: {i: b.versions(t, i) for i in b.ids(t)} for t in TABLES}
def write(backend, graph_id, who, edit):
    m = graph_model.GraphModel(Storage(backend), author=who); g = m.read_graph(graph_id); edit(g); r = m.save_graph(g); assert r.saved, r; return r.version
def set_value(step, value):
    def f(g): next(n for n in g["nodes"] if n["id"] == step)["data"]["value"] = value
    return f

tmp = tempfile.mkdtemp(); ASIDE = os.path.join(tmp, "aside")
live = FileBackend(os.path.join(tmp, "live")); populate(live); add_code(live)
copy_ = FileBackend(os.path.join(tmp, "copy")); graph_store_move.move_store(live, copy_)
check("a fresh copy of the live store is current everywhere", {r["state"] for r in sy.lag(live, copy_).values()} == {"current"})

# lag per graph
write(live, "cp2.multi", "elsewhere", lambda g: g["nodes"][0]["data"].update(value="a")); write(live, "cp2.multi", "elsewhere", lambda g: g["nodes"][0]["data"].update(value="b"))
l = sy.lag(live, copy_)
check("FR-93 the lag is shown per graph before a sync: which graph, how many versions", l["cp2.multi"] == {"live": 6, "copy": 4, "state": "behind"} and sum(r["state"] == "behind" for r in l.values()) == 1, json.dumps(l["cp2.multi"]))
out = sy.sync_store(live, copy_, ASIDE)
check("FR-93 the sync gives the copy the missing versions and it equals the live store", snapshot(copy_) == snapshot(live) and out["set_aside"] == {} and out["records"] > 0, json.dumps(out)[:120])
again = sy.sync_store(live, copy_, ASIDE)
check("NFR-16 a second sync changes nothing and sets nothing aside", again["records"] == 0 and again["set_aside"] == {} and not os.path.exists(ASIDE))

# the copy has a version of its own (the editor wrote to the copy by mistake), the live store has a different new one
write(copy_, "cp2.multi", "copy-writer", set_value("var.in", "only on the copy")) if False else write(copy_, "sample.code", "copy-writer", set_value("var.in", "only on the copy"))
write(live, "sample.code", "elsewhere", set_value("var.in", "live version"))
l = sy.lag(live, copy_)
check("FR-93 a graph that got different versions on both sides is shown as differing before the sync", l["sample.code"]["state"] == "differs", json.dumps(l["sample.code"]))
copy_before = copy_.versions("graphs", "sample.code")
out = sy.sync_store(live, copy_, ASIDE)
aside = out["set_aside"]
doc = json.load(open(aside["sample.code"]["file"]))
check("FR-93 the live store wins: the copy equals it and the differing version is named to the owner with the file it was saved in", snapshot(copy_) == snapshot(live) and list(aside) == ["sample.code"] and aside["sample.code"]["versions"] == [2], json.dumps(aside))
check("FR-93 nothing is lost: the set-aside file holds the copy's version with its author and the step content", doc["header"] == copy_before and any(v["author"] == "copy-writer" and v["doc"]["data"].get("value") == "only on the copy" for vs in doc["members"].values() for v in vs))
# the copy is only ahead (same first versions, one more)
write(copy_, "cp2.multi", "copy-writer", set_value("var.in", "extra")) if False else None
nv = write(copy_, "cp2.multi", "copy-writer", lambda g: g["nodes"][0]["data"].update(value="ahead"))
out = sy.sync_store(live, copy_, ASIDE)
check("FR-93 versions only the copy has, on top of the live history, are set aside too and the copy goes back to the live history", snapshot(copy_) == snapshot(live) and out["set_aside"]["cp2.multi"]["versions"] == [nv], json.dumps(out["set_aside"]))
# a graph only on the copy
only = os.path.join(tmp, "x"); fb = FileBackend(only); populate(fb)
graph_store_move.move_graph(fb, copy_, "cp2.multi") if False else None
m = graph_model.GraphModel(Storage(copy_), author="copy-writer"); g = m.read_graph("cp2.multi"); g["id"] = "copy.only"; m.save_graph(g)
check("FR-93 a graph that exists only on the copy is shown as such", sy.lag(live, copy_)["copy.only"]["state"] == "copy_only")
out = sy.sync_store(live, copy_, ASIDE)
check("FR-93 it is set aside and removed from the copy, which then equals the live store", "copy.only" in out["set_aside"] and snapshot(copy_) == snapshot(live) and os.path.exists(out["set_aside"]["copy.only"]["file"]))

# a live graph that cannot be moved: nothing is written
bad = FileBackend(os.path.join(tmp, "badlive")); populate(bad); bad.remove("graph_nodes", bad.ids("graph_nodes")[0])      # a step the header pins is gone
c3 = FileBackend(os.path.join(tmp, "c3")); before = snapshot(c3)
try: sy.sync_store(bad, c3, ASIDE); refused = None
except StorageError as e: refused = e
check("NFR-16 a graph of the live store that cannot be moved refuses the sync, names the graph and writes nothing", refused is not None and len(refused.detail["graphs"]) >= 1 and snapshot(c3) == before)

# interrupted
class Fails:
    def __init__(self, inner, after): self.inner, self.after, self.n = inner, after, 0
    def __getattr__(self, name):
        f = getattr(self.inner, name)
        if name not in ("append", "remove"): return f
        def counted(*a, **k):
            self.n += 1
            if self.n > self.after: raise OSError("the disk is gone")
            return f(*a, **k)
        return counted
write(live, "sample.code", "elsewhere", set_value("var.in", "second live version")); write(copy_, "sample.code", "copy-writer", set_value("var.in", "copy again"))
write(live, "cp2.multi", "elsewhere", lambda g: g["nodes"][0]["data"].update(value="c"))
stops = []
for after in (1, 3, 6):
    victim = FileBackend(os.path.join(tmp, "victim%d" % after)); shutil.copytree(copy_.root if hasattr(copy_, "root") else os.path.join(tmp, "copy"), victim.root if hasattr(victim, "root") else os.path.join(tmp, "victim%d" % after), dirs_exist_ok=True)
    try: sy.sync_store(live, Fails(victim, after), ASIDE)
    except OSError: pass
    listed = [g for g in victim.ids("graphs")]
    whole = all(all(victim.versions(t, m["id"]) for v in victim.versions("graphs", g) for t, k in (("graph_nodes", "nodes"), ("graph_edges", "edges")) for m in v["doc"]["data"][k]) for g in listed)
    sy.sync_store(live, victim, ASIDE)
    stops.append((whole, snapshot(victim) == snapshot(live)))
check("NFR-16 a sync interrupted after 1, 3 or 6 writes never lists a graph with missing steps, and running it again finishes it", all(a and b for a, b in stops), str(stops))
sy.sync_store(live, copy_, ASIDE)

# automatic at start and stop
write(live, "cp2.multi", "elsewhere", lambda g: g["nodes"][0]["data"].update(value="d"))
with sy.AutoSync(live, copy_, ASIDE) as auto:
    at_start = snapshot(copy_) == snapshot(live)
    write(live, "cp2.multi", "elsewhere", lambda g: g["nodes"][0]["data"].update(value="e"))
    during = snapshot(copy_) != snapshot(live)
check("FR-93 the copy is synced when MIA starts, and again when it stops in an orderly way", at_start and during and snapshot(copy_) == snapshot(live) and [r["when"] for r in auto.reports] == ["start", "stop"])
class Down:
    def __getattr__(self, name):
        def fail(*a, **k): raise ConnectionError("the live store is gone")
        return fail
ran = []
with sy.AutoSync(Down(), copy_, ASIDE) as auto:
    ran.append(True)
check("FR-93 a live store that cannot be reached is reported at start and stop and keeps MIA from neither", ran == [True] and all("unreachable" in r for r in auto.reports) and len(auto.reports) == 2, json.dumps(auto.reports)[:100])

# viewer routes
acc = Storage(FileBackend(os.path.join(tmp, "a"))); accounts.create(acc, "owner", "secret", "cp3"); time.sleep(1.2); accounts.create(acc, "guest", "secret2", "cp3")
ORIGIN = {"Origin": "http://127.0.0.1:8801"}
app = graph_proto_app.create_app(copy_, acc, live=live, aside=ASIDE); o, gst = app.test_client(), app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN); gst.post("/api/login", json={"user": "guest", "password": "secret2"}, headers=ORIGIN)
write(live, "cp2.multi", "elsewhere", lambda g: g["nodes"][0]["data"].update(value="f")); write(copy_, "sample.code", "copy-writer", set_value("var.in", "again on the copy")); write(live, "sample.code", "elsewhere", set_value("var.in", "again live"))
st = o.get("/api/v2/status").get_json()
check("FR-93 the status names the graph the copy is behind on and the graph that differs", st["behind"] == {"cp2.multi": {"live": len(live.versions("graphs", "cp2.multi")), "copy": len(copy_.versions("graphs", "cp2.multi"))}} and len(live.versions("graphs", "cp2.multi")) == len(copy_.versions("graphs", "cp2.multi")) + 1 and list(st["differs"]) == ["sample.code"] and st["lag"] == 1, json.dumps(st))
check("FR-93 only the owner syncs", gst.post("/api/v2/sync", headers=ORIGIN).status_code == 403)
r = o.post("/api/v2/sync", headers=ORIGIN).get_json()
st = o.get("/api/v2/status").get_json()
check("FR-93 the sync on command answers with what was set aside, and afterwards nothing lags or differs", list(r["set_aside"]) == ["sample.code"] and st["lag"] == 0 and st["differs"] == {} and snapshot(copy_) == snapshot(live), json.dumps(r)[:140])

# NFR-15 a set of files on another machine
elsewhere = os.path.join(tmp, "other-machine", "mia-graphs"); os.makedirs(os.path.dirname(elsewhere))
shutil.copytree(os.path.join(tmp, "copy"), elsewhere)
moved = FileBackend(elsewhere); mm, om = graph_model.GraphModel(Storage(moved)), graph_model.GraphModel(Storage(copy_))
same = snapshot(moved) == snapshot(copy_) and all(mm.read_graph(g, v["version"]) == om.read_graph(g, v["version"]) for g in copy_.ids("graphs") for v in copy_.versions("graphs", g))
leak = [os.path.join(d, f) for d, _, fs in os.walk(os.path.join(tmp, "copy")) for f in fs if os.path.join(tmp, "copy").encode() in open(os.path.join(d, f), "rb").read()]
check("NFR-15 a set of files moved to another folder lists every graph with the same versions and content, and holds no path of where it was made", same and not leak and len(moved.ids("graphs")) == len(copy_.ids("graphs")), str(leak[:1]))
cli = subprocess.run([sys.executable, os.path.join(REPO, "graph_store_sync.py"), "files:" + os.path.join(tmp, "live"), "files:" + elsewhere, "--lag"], cwd="/", capture_output=True, text=True)
check("the command line shows the lag per graph from any folder", cli.returncode == 0 and "cp2.multi" in cli.stdout and "current" in cli.stdout, cli.stderr[-100:])
fresh = os.path.join(tmp, "fresh")
cli = subprocess.run([sys.executable, os.path.join(REPO, "graph_store_sync.py"), "files:" + os.path.join(tmp, "live"), "files:" + fresh, "--aside", ASIDE], cwd="/", capture_output=True, text=True)
check("the command line syncs a live store into a new set of files, and the set equals the live store", cli.returncode == 0 and snapshot(FileBackend(fresh)) == snapshot(live), cli.stderr[-100:])
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
