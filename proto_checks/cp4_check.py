"""PROTOTYPE CP4 checks (not protected tests): the eight rules in one place (FR-63) and the refusal before a run (FR-64). Run: python proto_checks/cp4_check.py"""
import copy, json, os, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_model, graph_proto_app, graph_rules_proto as R
from graph_run import GraphRunner
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate, add_code, add_broken

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

D = lambda i, **k: {"id": i, "data": {"type": "data", **k}}
T = lambda i, tool="check.number": {"id": i, "data": {"type": "transform", "toolbox_id": tool}}
M = lambda i, stop=None: {"id": i, "data": {"type": "master", "toolbox_id": "control.loop", **({"stop": stop} if stop is not None else {})}}
E = lambda i, a, b, **d: {"id": i, "from": a, "to": b, "data": d}
G = lambda nodes, edges: {"nodes": nodes, "edges": edges}
good = G([D("in", value="x"), T("s"), D("out")], [E("e1", "in", "s"), E("e2", "s", "out")])

class Spy:
    def __init__(self): self.calls = []
    def nodes(self, graph): return {n["id"]: (lambda v, _i=n["id"]: self.calls.append(_i) or "r") for n in graph["nodes"] if n["data"]["type"] != "data"}
runner = GraphRunner(lambda step: "trusted")
def attempt(graph, given=None):
    spy = Spy(); result, said = R.run_guarded(runner, graph, spy.nodes(graph), given or {}); return result, said, spy.calls

# ---- the eight rules, one fixed order ----
two = G([D("a", value=1), T("s1"), T("s2"), D("w"), D("w")], [E("e1", "a", "s1"), E("e1", "a", "s1"), E("e3", "s1", "w"), E("e4", "s2", "w")])
rules = lambda g: [r["rule"] for r in R.rule_report(g)]
check("FR-63 the eight rules are one list in one place, in the order ids, kind, missing connection, duplicate, adjacency, one writer, session setting and stop limit, cycle", list(R.TEXTS) == ["step_identity", "step_kind", "connection_endpoints", "duplicate_connection", "adjacency", "single_writer", "stop_limit", "cycle"])
check("FR-63 a graph that breaks two rules lists them in that order, with their parts, every time", rules(two) == ["step_identity", "duplicate_connection", "single_writer"] and [r["parts"] for r in R.rule_report(two)] == [["w"], ["e1"], ["w"]] and all(rules(two) == rules(copy.deepcopy(two)) for _ in range(5)), json.dumps(rules(two)))
# session setting and stop limit
check("FR-63 a loop-controlling step without a valid stop limit breaks the rule", rules(G([D("a", value=1), M("m"), D("o")], [E("e1", "a", "m"), E("e2", "m", "o")])) == ["stop_limit"])
check("FR-63 a loop-controlling step with a limit is fine", rules(G([D("a", value=1), M("m", {"max_repetitions": 3}), D("o")], [E("e1", "a", "m"), E("e2", "m", "o")])) == [])
check("FR-63 a session setting on a data step breaks the rule, and names the step", [(r["rule"], r["parts"]) for r in R.rule_report(G([D("a", value=1, stop={"max_repetitions": 2}), T("s"), D("o")], [E("e1", "a", "s"), E("e2", "s", "o")]))] == [("stop_limit", ["a"])])
check("FR-63 two settings connections into one step break the rule", [(r["rule"], r["parts"]) for r in R.rule_report(G([D("a", value=1), D("c1", value={}), D("c2", value={}), T("s"), D("o")], [E("e1", "a", "s"), E("e2", "c1", "s", role="settings"), E("e3", "c2", "s", role="settings"), E("e4", "s", "o")]))] == [("stop_limit", ["s"])])

# ---- refusal before a run ----
res, said, calls = attempt(good)
check("FR-64 a graph that keeps the rules and has its inputs runs", res.status == "done" and said["status"] == "ready" and calls == ["s"])
cases = {
 "a cycle": (G([D("a", value=1), T("s1"), D("b"), T("s2")], [E("e1", "a", "s1"), E("e2", "s1", "b"), E("e3", "b", "s2"), E("e4", "s2", "a")]), "cycle"),
 "two writers of one piece of data": (G([D("a", value=1), T("s1"), T("s2"), D("w")], [E("e1", "a", "s1"), E("e2", "a", "s2"), E("e3", "s1", "w"), E("e4", "s2", "w")]), "single_writer"),
 "a connection to a missing step": (G([D("a", value=1), T("s")], [E("e1", "a", "s"), E("e2", "s", "gone")]), "connection_endpoints"),
 "two identical connections": (G([D("a", value=1), T("s"), D("o")], [E("e1", "a", "s"), E("e2", "a", "s"), E("e3", "s", "o")]), "duplicate_connection"),
}
for name, (g, rule) in cases.items():
    res, said, calls = attempt(g)
    check("FR-64 %s: no step runs, the run is refused and names the broken part" % name, res.status == "refused" and calls == [] and said["status"] == "refused" and rule in [b.get("rule") for b in said["broken"]] and all(b["parts"] for b in said["broken"]), json.dumps(said["broken"])[:110])
needs = G([D("question"), T("s"), D("o")], [E("e1", "question", "s"), E("e2", "s", "o")])
res, said, calls = attempt(needs)
check("FR-64 an input with no writer, no start value and no value given with the run refuses the run before any step, naming the step and the input", res.status == "refused" and calls == [] and said["broken"] == [{"kind": "input", "step": "s", "input": "question", "text": said["broken"][0]["text"], "parts": ["question"]}], json.dumps(said["broken"])[:120])
res, said, calls = attempt(needs, {"question": "why?"})
check("FR-64 the same graph runs when the value is given with the run", res.status == "done" and calls == ["s"])
check("FR-64 a start value in the graph supplies the input too", attempt(G([D("question", value="q"), T("s"), D("o")], [E("e1", "question", "s"), E("e2", "s", "o")]))[0].status == "done")
check("FR-64 an input that another step writes is supplied", attempt(G([D("a", value=1), T("s1"), D("b"), T("s2"), D("o")], [E("e1", "a", "s1"), E("e2", "s1", "b"), E("e3", "b", "s2"), E("e4", "s2", "o")]))[0].status == "done")
check("FR-64 settings and order connections are not inputs nobody supplies", R.missing_inputs(G([D("a", value=1), D("cfg"), D("ord"), T("s"), D("o")], [E("e1", "a", "s"), E("e2", "cfg", "s", role="settings"), E("e3", "ord", "s", role="order"), E("e4", "s", "o")])) == [])
res, said, calls = attempt(G([D("a"), T("s1"), T("s2"), D("w"), D("w2")], [E("e1", "a", "s1"), E("e2", "s1", "w"), E("e3", "s2", "w"), E("e4", "s1", "gone")]))
check("FR-64 every broken part is named at once, rules first in their order, then the inputs", [b["kind"] for b in said["broken"]] == ["rule", "rule", "input"] and [b.get("rule") for b in said["broken"][:2]] == ["connection_endpoints", "single_writer"], json.dumps([(b["kind"], b.get("rule") or b.get("input")) for b in said["broken"]]))

# ---- the route, on stored graphs ----
tmp = tempfile.mkdtemp(); live = FileBackend(os.path.join(tmp, "s")); populate(live); add_code(live); add_broken(live)
acc = Storage(FileBackend(os.path.join(tmp, "a"))); accounts.create(acc, "owner", "secret", "cp4"); time.sleep(1.2); accounts.create(acc, "guest", "secret2", "cp4")
ORIGIN = {"Origin": "http://127.0.0.1:8801"}
app = graph_proto_app.create_app(live, acc); o, gst = app.test_client(), app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN); gst.post("/api/login", json={"user": "guest", "password": "secret2"}, headers=ORIGIN)
U = "/api/v2/graphs/"
r = o.post(U + "sample.broken/run", json={}, headers=ORIGIN)
check("FR-64 a stored graph with a connection to a missing step is refused by the route: 422, no step ran, the connection named", r.status_code == 422 and r.get_json()["ran"] == [] and r.get_json()["status"] == "refused" and "e2" in [p for b in r.get_json()["broken"] for p in b["parts"]], json.dumps(r.get_json())[:140])
r = o.post(U + "chat@1/run", json={}, headers=ORIGIN)
check("FR-64 a stored graph whose input nobody supplies is refused, and names the step and the input", r.status_code == 422 and r.get_json()["ran"] == [] and {"step": "step.converse", "input": "input.text"} == {k: r.get_json()["broken"][0][k] for k in ("step", "input")}, json.dumps(r.get_json()["broken"])[:120])
r = o.post(U + "chat@1/run", json={"inputs": {"input.text": "hello"}}, headers=ORIGIN)
check("FR-64 the same graph runs when the value is given with the run (stand-in steps, in order)", r.status_code == 200 and r.get_json()["status"] == "done" and r.get_json()["ran"] == ["step.converse"], json.dumps(r.get_json())[:120])
rc = o.post(U + "cp2.multi/check", json={"graph": o.get(U + "cp2.multi").get_json()["graph"]}, headers=ORIGIN)
check("FR-63 the check route and the run route agree: a graph that keeps the rules gets no rule from either", rc.get_json()["rules"] == [] and o.post(U + "cp2.multi/run", json={}, headers=ORIGIN).status_code == 200)
check("FR-64 only the owner tries a run; an unknown graph is a clean not-found", gst.post(U + "chat@1/run", json={"inputs": {"input.text": "x"}}, headers=ORIGIN).status_code == 403 and o.post(U + "nothing/run", json={}, headers=ORIGIN).status_code == 404)
bad = o.get(U + "sample.broken").get_json()["graph"]
rk = o.put(U + "sample.broken", json={"graph": {"nodes": bad["nodes"], "edges": bad["edges"]}}, headers=ORIGIN)
check("FR-63 keeping the same broken graph is refused with the same rules the run named", rk.status_code == 422 and [r["rule"] for r in rk.get_json()["rules"]] == [b["rule"] for b in o.post(U + "sample.broken/run", json={}, headers=ORIGIN).get_json()["broken"] if b["kind"] == "rule"])
rc2 = o.post(U + "sample.broken/check", json={"graph": {"nodes": bad["nodes"], "edges": bad["edges"]}}, headers=ORIGIN).get_json()["rules"]
check("FR-63 while editing (the check route), while keeping and before a run the same broken rules come in the same order", [r["rule"] for r in rc2] == [r["rule"] for r in rk.get_json()["rules"]] == [b["rule"] for b in o.post(U + "sample.broken/run", json={}, headers=ORIGIN).get_json()["broken"] if b["kind"] == "rule"] and len(rc2) >= 1)
cp = o.get(U + "cp2.multi").get_json()["graph"]; loop = copy.deepcopy(cp); loop["edges"].append(E("e99", "var.out", "step.write"))
r1 = o.post(U + "cp2.multi/run", json={"inputs": {}, "graph": {"nodes": loop["nodes"], "edges": loop["edges"]}}, headers=ORIGIN)
r2 = o.post(U + "cp2.multi/run", json={"inputs": {}}, headers=ORIGIN)
check("FR-64 a run tried from the editor uses the working copy: a cycle that was not kept is refused, while the stored graph still runs", r1.status_code == 422 and r1.get_json()["ran"] == [] and "cycle" in [b.get("rule") for b in r1.get_json()["broken"]] and r2.status_code == 200, json.dumps(r1.get_json())[:120])
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
