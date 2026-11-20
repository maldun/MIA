"""PROTOTYPE CP7 checks (not protected tests): the shared arrangement (FR-52) and the versions behind the history list (FR-55) of G-V4.VIEW,
and a first look at speed (NFR-11). Run: python proto_checks/cp7_check.py"""
import json, os, statistics, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_proto_app
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

ORIGIN = {"Origin": "http://127.0.0.1:8801"}
tmp = tempfile.mkdtemp()
be = FileBackend(os.path.join(tmp, "s")); populate(be)
acc = Storage(FileBackend(os.path.join(tmp, "a")))
accounts.create(acc, "owner", "secret", "cp7"); time.sleep(1.2); accounts.create(acc, "guest", "secret2", "cp7")   # the owner is the account made first
app = graph_proto_app.create_app(be, acc)
owner, guest = app.test_client(), app.test_client()
owner.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN)
guest.post("/api/login", json={"user": "guest", "password": "secret2"}, headers=ORIGIN)
URL = "/api/v2/graphs/cp2.multi/arrangement"

check("FR-52 a graph that was never arranged has no saved arrangement", owner.get(URL).get_json() == {"positions": None})
r = owner.put(URL, json={"positions": {"var.in": {"x": 10.4, "y": 20.6}, "step.write": {"x": 150, "y": 20}, "nope": {"x": 1, "y": 1}}}, headers=ORIGIN)
check("FR-52 the owner saves an arrangement; a place for a step the graph does not have is ignored", r.status_code == 200 and r.get_json()["saved"] == 2)
got = owner.get(URL).get_json()
check("FR-52 the saved places come back as whole numbers with who saved them", got["positions"] == {"var.in": {"x": 10, "y": 21}, "step.write": {"x": 150, "y": 20}} and got["author"] == "owner" and got["version"] == 1)
check("FR-52 the arrangement is the same for everyone: another account sees it", guest.get(URL).get_json()["positions"] == got["positions"])
check("FR-52 only the owner saves: another account is refused and nothing changes", guest.put(URL, json={"positions": {"var.in": {"x": 0, "y": 0}}}, headers=ORIGIN).status_code == 403 and owner.get(URL).get_json()["version"] == 1)
owner.put(URL, json={"positions": {"var.in": {"x": 1, "y": 2}}}, headers=ORIGIN)
check("FR-52 the last saved arrangement counts", owner.get(URL).get_json()["positions"] == {"var.in": {"x": 1, "y": 2}} and owner.get(URL).get_json()["version"] == 2)
check("FR-52 a place that is not a pair of numbers is refused", owner.put(URL, json={"positions": {"var.in": {"x": "a", "y": 1}}}, headers=ORIGIN).status_code == 422 and owner.put(URL, json={"positions": [1]}, headers=ORIGIN).status_code == 422)
check("FR-52 saving an arrangement is no new version of the graph", len(owner.get("/api/v2/graphs/cp2.multi/versions").get_json()) == 4)
check("FR-52 an arrangement for an unknown graph is refused", owner.put("/api/v2/graphs/nope/arrangement", json={"positions": {}}, headers=ORIGIN).status_code == 404)
check("FR-52 without a login the arrangement is not shown", app.test_client().get(URL).status_code == 401)

v = owner.get("/api/v2/graphs/cp2.multi/versions").get_json()
check("FR-55 the history lists every version with author and time, none missing", [e["version"] for e in v] == [1, 2, 3, 4] and all(e["author"] and e["time"] for e in v))
check("FR-55 any version can be shown, and an earlier one differs from the current", owner.get("/api/v2/graphs/cp2.multi?version=1").get_json()["graph"] != owner.get("/api/v2/graphs/cp2.multi").get_json()["graph"])
check("FR-55 a version that does not exist is a clean not-found", owner.get("/api/v2/graphs/cp2.multi?version=9").status_code == 404)

# NFR-11: a first look at speed on the backend side; the drawing in the browser is the owner's to judge
big = "research.escalate@1"
times = []
for _ in range(20):
    t0 = time.perf_counter(); owner.get("/api/v2/graphs/" + big); times.append((time.perf_counter() - t0) * 1000)
times.sort()
check("NFR-11 the backend answers the 54-step graph quickly (median over 20 calls, test client, files)", statistics.median(times) < 100, f"median {statistics.median(times):.1f} ms, worst {times[-1]:.1f} ms")
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
