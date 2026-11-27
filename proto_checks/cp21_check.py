"""PROTOTYPE round 05 CP21 checks (not protected tests): the editor profile per kind of graph from the backend (FR-92, D-403, D-404, D-471 (2), D-602).
Run: python proto_checks/cp21_check.py [--write]   (--write renews proto_checks/kinds_answer.json, the copy of the answer the JS checks read)"""
import json, os, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_proto_app, graph_rule_set
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
accounts.create(acc, "owner", "secret", "cp21"); time.sleep(1.2); accounts.create(acc, "guest", "secret2", "cp21")
app = graph_proto_app.create_app(be, acc)
o, gst = app.test_client(), app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN); gst.post("/api/login", json={"user": "guest", "password": "secret2"}, headers=ORIGIN)

# Given the registry of kinds of the product (RULES), when the page asks for the kinds, then every kind is answered with its rules and its profile
answer = o.get("/api/v2/kinds").get_json()
registry = graph_rule_set.kinds()
check("every kind of the registry is answered, no other", set(answer["kinds"]) == set(registry), str(sorted(answer["kinds"])))
check("the rules and 'runs' of each kind are the registry's, in its order",
      all(answer["kinds"][k]["rules"] == list(registry[k]["rules"]) and answer["kinds"][k]["runs"] == registry[k]["runs"] for k in registry))
wf, cx = answer["kinds"]["workflow"], answer["kinds"]["context"]
check("workflow is editable with the three types of IF-301 (data, processing, loop-controlling)",
      wf["editable"] is True and [t["type"] for t in wf["node_types"]] == list(graph_rule_set.STEP_TYPES))
check("context is not editable in EDIT and says why (D-602)", cx["editable"] is False and "G-V4.CONTEXT" in cx["reason"] and cx["node_types"] == [])
check("an unknown kind has its own words for the page", bool(answer.get("unknown_reason")))
check("the kinds are answered to any logged-in account (reading), not without a login",
      gst.get("/api/v2/kinds").status_code == 200 and app.test_client().get("/api/v2/kinds").status_code == 401)

# Given the start content of each type, when one step of it stands alone, then the rules accept the type and its stop limit
for t in wf["node_types"]:
    lone = {"kind": "workflow", "nodes": [{"id": "s", "data": t["start"]}], "edges": []}
    broken = [r["rule"] for r in graph_rule_set.rule_report(lone)]
    check(f"the start content of '{t['type']}' breaks no rule of the step itself", not ({"step_kind", "stop_limit"} & set(broken)), str(broken))

# Given the toolbox answer, when a choice field filters it, then each filter finds entries (processing tools; controllers)
tools = o.get("/api/v2/toolbox").get_json()
check("the toolbox answer names id, trust, lifecycle and controller per entry", tools and all({"id", "trust", "lifecycle", "controller"} <= set(x) for x in tools))
for t in wf["node_types"]:
    for f in t["fields"]:
        if f.get("list") == "toolbox":
            hit = [x for x in tools if all(x.get(k) == v for k, v in f.get("filter", {}).items())]
            check(f"the tool field of '{t['type']}' finds entries ({len(hit)})", len(hit) > 0)

# Given every field of every profile, when its description is read, then it is one the page knows (no field the editor would have to guess)
INPUTS = {"text", "json", "number", "choice"}
fields = [f for k in answer["kinds"].values() for t in k["node_types"] for f in t["fields"]] + [f for k in answer["kinds"].values() for f in k["connection_fields"]]
check("every field has a name, a label and a known input", all(f.get("name") and f.get("label") and f.get("input") in INPUTS for f in fields))
check("every choice field has options or a list", all(("options" in f) != ("list" in f) for f in fields if f["input"] == "choice"))

# The JS checks read the same answer from a file; it must not drift from the route
path = os.path.join(REPO, "proto_checks", "kinds_answer.json")
if "--write" in sys.argv or not os.path.exists(path):
    with open(path, "w") as fh: json.dump(answer, fh, indent=1, sort_keys=True); fh.write("\n")
with open(path) as fh: check("proto_checks/kinds_answer.json equals the route's answer", json.load(fh) == answer)

failed = [r for r in results if not r[1]]
print(f"\n{len(results)} checks, {len(failed)} failed")
sys.exit(1 if failed else 0)
