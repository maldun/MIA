"""PROTOTYPE CP8 checks (not protected tests): the rules and the keep route behind the editor (FR-69, FR-70 of G-V4.EDIT; core of FR-63 of GRAPHAPI.RULES).
Run: python proto_checks/cp8_check.py"""
import copy, json, os, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_proto_app, graph_rules_proto
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate
from proto_checks.cp1_check import small

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

def names(g): return [r["rule"] for r in graph_rules_proto.rule_report(g)]
base = small("r", "x")           # var.in -> step.write -> var.out
check("FR-63 a graph that keeps every rule has an empty report", names(base) == [])
bad = copy.deepcopy(base); bad["nodes"].append({"id": "var.in", "data": {"type": "data"}})
check("rule 1: a step name used twice and an empty name; a name with a slash is allowed (round 04 CP17, as CORE: REQ-GTB-029)", names(bad) == ["step_identity"] and graph_rules_proto.rule_report({"nodes": [{"id": "", "data": {"type": "data"}}, {"id": "a/b", "data": {"type": "data"}}], "edges": []})[0]["parts"] == [""])
bad = copy.deepcopy(base); bad["nodes"][1]["data"]["type"] = "wizard"
check("rule 2: a step of an unknown kind", "step_kind" in names(bad))
bad = copy.deepcopy(base); bad["edges"].append({"id": "e9", "from": "step.write", "to": "var.gone", "data": {}})
r = graph_rules_proto.rule_report(bad)
check("rule 3: a connection to a missing step is named", r[0]["rule"] == "connection_endpoints" and r[0]["parts"] == ["e9"])
bad = copy.deepcopy(base); bad["edges"].append({"id": "e3", "from": "var.in", "to": "step.write", "data": {}})
check("rule 4: the same connection twice", names(bad) == ["duplicate_connection"])
bad = copy.deepcopy(base); bad["edges"].append({"id": "e3", "from": "var.in", "to": "var.out", "data": {}})
check("rule 5: a connection between two data steps", "adjacency" in names(bad))
bad = copy.deepcopy(base); bad["nodes"] += [{"id": "step.two", "data": {"type": "transform", "toolbox_id": "t"}}]; bad["edges"] += [{"id": "e3", "from": "var.in", "to": "step.two", "data": {}}, {"id": "e4", "from": "step.two", "to": "var.out", "data": {}}]
r = graph_rules_proto.rule_report(bad)
check("rule 6: a piece of data written by two steps is named", [x["rule"] for x in r] == ["single_writer"] and r[0]["parts"] == ["var.out"])
bad = copy.deepcopy(base); bad["nodes"][1]["data"] = {"type": "master", "toolbox_id": "control.loop"}
check("rule 7: a loop-controlling step without a stop limit", names(bad) == ["stop_limit"])
bad = copy.deepcopy(base); bad["nodes"] += [{"id": "var.back", "data": {"type": "data"}}]; bad["edges"] += [{"id": "e3", "from": "step.write", "to": "var.back", "data": {}}, {"id": "e4", "from": "var.back", "to": "step.write", "data": {}}]
check("rule 8: a cycle is named with its steps", names(bad) == ["cycle"])
bad = copy.deepcopy(base); bad["nodes"][1]["data"]["type"] = "wizard"; bad["edges"].append({"id": "e9", "from": "var.in", "to": "var.in", "data": {}})
check("FR-63 several broken rules are all named, in the fixed order", names(bad) == ["step_kind", "adjacency", "cycle"], str(names(bad)))

ORIGIN = {"Origin": "http://127.0.0.1:8801"}
tmp = tempfile.mkdtemp()
be = FileBackend(os.path.join(tmp, "s")); populate(be)
acc = Storage(FileBackend(os.path.join(tmp, "a")))
accounts.create(acc, "owner", "secret", "cp8"); time.sleep(1.2); accounts.create(acc, "guest", "secret2", "cp8")
app = graph_proto_app.create_app(be, acc)
o, gst = app.test_client(), app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN); gst.post("/api/login", json={"user": "guest", "password": "secret2"}, headers=ORIGIN)
U = "/api/v2/graphs/cp2.multi"
cur = o.get(U).get_json()["graph"]
body = lambda g, **kw: {"graph": {"nodes": g["nodes"], "edges": g["edges"]}, **kw}
r = o.post(U + "/check", json=body(cur), headers=ORIGIN)
check("FR-69 the check route says a valid graph has no problem", r.status_code == 200 and r.get_json() == {"rules": []})
broken = copy.deepcopy(cur); broken["edges"].append({"id": "e9", "from": "var.out", "to": "step.write", "data": {}})
r = o.post(U + "/check", json=body(broken), headers=ORIGIN).get_json()
check("FR-69 the check route names the broken rule and its steps before anything is kept", [x["rule"] for x in r["rules"]] == ["cycle"] and len(o.get(U + "/versions").get_json()) == 4, json.dumps(r["rules"]))
r = o.put(U, json=body(broken), headers=ORIGIN)
check("FR-70 keeping a graph that breaks a rule is refused with the rule named, nothing written", r.status_code == 422 and r.get_json()["error"] == "rules_broken" and r.get_json()["rules"][0]["rule"] == "cycle" and len(o.get(U + "/versions").get_json()) == 4)
changed = copy.deepcopy(cur); changed["nodes"][1]["data"]["toolbox_id"] = "tool.edited"
r = o.put(U, json=body(changed, expected_version=4), headers=ORIGIN)
v = o.get(U + "/versions").get_json()
check("FR-70 a change that keeps every rule is kept as a new version by the account that kept it", r.status_code == 200 and {k: r.get_json()[k] for k in ("version", "changed")} == {"version": 5, "changed": True} and [e["version"] for e in v] == [1, 2, 3, 4, 5] and v[-1]["author"] == "owner")
check("FR-71 the earlier version is still there as it was", o.get(U + "?version=4").get_json()["graph"] == cur and o.get(U).get_json()["graph"]["nodes"][1]["data"]["toolbox_id"] == "tool.edited")
r = o.put(U, json=body(changed), headers=ORIGIN)
check("FR-71 keeping the same graph again makes no new version", {k: r.get_json()[k] for k in ("version", "changed")} == {"version": 5, "changed": False} and len(o.get(U + "/versions").get_json()) == 5)
more = copy.deepcopy(changed); more["nodes"].append({"id": "var.extra", "data": {"type": "data", "value": 1}}); more["edges"].append({"id": "e7", "from": "step.write", "to": "var.extra", "data": {}})
r = o.put(U, json=body(more), headers=ORIGIN)
check("FR-68 a new step and a new connection are kept together", r.status_code == 200 and r.get_json()["version"] == 6 and len(o.get(U).get_json()["graph"]["nodes"]) == 4)
less = copy.deepcopy(more); less["nodes"] = [n for n in less["nodes"] if n["id"] != "var.extra"]; less["edges"] = [e for e in less["edges"] if e["id"] != "e7"]
r = o.put(U, json=body(less), headers=ORIGIN)
check("FR-68 removing a step with its connection is kept", r.status_code == 200 and r.get_json()["version"] == 7 and len(o.get(U).get_json()["graph"]["nodes"]) == 3)
check("FR-72 a change made on an old version is refused, nothing is overwritten", o.put(U, json=body(changed, expected_version=3), headers=ORIGIN).status_code == 409 and len(o.get(U + "/versions").get_json()) == 7)
check("NFR-19 an account that is not the owner can neither check nor keep", gst.post(U + "/check", json=body(cur), headers=ORIGIN).status_code == 403 and gst.put(U, json=body(changed), headers=ORIGIN).status_code == 403)
check("FR-70 a request without a graph is refused cleanly", o.put(U, json={}, headers=ORIGIN).status_code == 422 and o.put("/api/v2/graphs/nope", json=body(cur), headers=ORIGIN).status_code == 404)
tb = o.get("/api/v2/toolbox").get_json()
byid = {t["id"]: t for t in tb}
check("FR-92 the toolbox lists the available tools with trust and lifecycle, controllers apart", len(tb) >= 70 and byid["check.number"] == {"id": "check.number", "trust": "trusted", "lifecycle": "tested", "controller": False} and byid["control.loop"]["controller"] is True and [t["id"] for t in tb] == sorted(byid), f"{len(tb)} tools")
check("the toolbox list is not shown without a login", app.test_client().get("/api/v2/toolbox").status_code == 401)
check("a keep without a login is not accepted", app.test_client().put(U, json=body(changed), headers=ORIGIN).status_code == 401)
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed" % (len(results), len(failed)))
sys.exit(1 if failed else 0)
