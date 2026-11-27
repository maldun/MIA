"""PROTOTYPE round 05 CP22 checks (not protected tests): graphs of kinds the editor cannot change (FR-72, FR-73, OC-9 of G-V4.EDIT; D-404, D-602).
A context graph (a known kind without an editable profile) and a graph of a kind the program does not know are drawn, and every write sent anyway is
refused with the kind named, nothing written. Run: python proto_checks/cp22_check.py"""
import copy, os, sys, tempfile, time
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import accounts, graph_model, graph_proto_app
from storage import Storage
from storage_files import FileBackend
from proto_checks.make_sample_store import populate

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

def ctx(gid):
    """the context graph of cp19 (copied: importing that module runs it)"""
    return {"id": gid, "kind": "context", "context_graph_id": "", "testbench_id": "", "description": "context graph of cp22",
            "nodes": [{"id": "claim", "data": {"type": "claim", "text": "water boils at 100 C"}}, {"id": "source", "data": {"type": "source", "url": "local:book-1"}}],
            "edges": [{"id": "e1", "from": "source", "to": "claim", "data": {"relation": "supports"}}]}

def put_unknown(backend, gid, kind, versions):
    """a graph of a kind the program does not know, written around the Storage layer (which refuses such a header, cp19's finding): as a newer store would hold it"""
    def put(table, rid, version, doc):
        backend.append(table, rid, {"id": rid, "version": version, "author": "newer", "time": "2026-11-27T12:00:0%dZ" % version, "doc": doc})
    put("graph_nodes", "%s/n1" % gid, 1, {"id": "%s/n1" % gid, "data": {"type": "step", "text": "one"}})
    put("graph_nodes", "%s/n2" % gid, 1, {"id": "%s/n2" % gid, "data": {"type": "step", "text": "two"}})
    for v in range(1, versions + 1):
        nodes = [{"id": "%s/n1" % gid, "version": 1}] + ([{"id": "%s/n2" % gid, "version": 1}] if v > 1 else [])
        put("graphs", gid, v, {"id": gid, "data": {"kind": kind, "context_graph_id": "", "testbench_id": "", "description": "a kind from a newer program", "nodes": nodes, "edges": []}})

ORIGIN = {"Origin": "http://127.0.0.1:8801"}
tmp = tempfile.mkdtemp()
be = FileBackend(os.path.join(tmp, "s")); populate(be)
saved = graph_model.GraphModel(Storage(be), author="cp22").save_graph(ctx("ctx.one"))
second = copy.deepcopy(ctx("ctx.one")); second["nodes"][0]["data"]["text"] = "water boils at 100 C at sea level"
saved2 = graph_model.GraphModel(Storage(be), author="cp22").save_graph(second)
put_unknown(be, "odd.plan", "plan", 2)
acc = Storage(FileBackend(os.path.join(tmp, "a")))
accounts.create(acc, "owner", "secret", "cp22")
app = graph_proto_app.create_app(be, acc)
o = app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN)
check("fixture: the context graph is stored in two versions", saved.saved and saved2.saved and saved2.version == 2, str(saved2))

def state(gid):
    """what a refusal must leave as it was: the version list and the record of changes"""
    return o.get("/api/v2/graphs/%s/versions" % gid).get_json(), o.get("/api/v2/graphs/%s/changes" % gid).get_json()

# Given a context graph and a graph of an unknown kind, when they are opened, then they are drawn with their kind
r_ctx, r_odd = o.get("/api/v2/graphs/ctx.one").get_json(), o.get("/api/v2/graphs/odd.plan")
check("a context graph opens with its kind and all its steps", r_ctx["graph"].get("kind") == "context" and len(r_ctx["graph"]["nodes"]) == 2)
check("a graph of an unknown kind opens (read-only in the page) with its kind named", r_odd.status_code == 200 and r_odd.get_json()["graph"].get("kind") == "plan"
      and len(r_odd.get_json()["graph"]["nodes"]) == 2, "%s %s" % (r_odd.status_code, (r_odd.get_json() or {}).get("graph", {}).get("kind")))
kinds = o.get("/api/v2/kinds").get_json()["kinds"]
check("the kinds answer says the page may not edit a context graph, and has no entry for the unknown kind", kinds["context"]["editable"] is False and "plan" not in kinds)

# When a change of each is sent anyway, then it is refused with the kind named and nothing is written
for gid, code, kind in (("ctx.one", "not_editable", "context"), ("odd.plan", "unknown_kind", "plan")):
    before = state(gid)
    graph = o.get("/api/v2/graphs/%s" % gid).get_json()["graph"]
    changed = copy.deepcopy(graph); changed["nodes"][0]["data"]["text"] = "changed"
    kept = o.put("/api/v2/graphs/%s" % gid, json={"graph": {"nodes": changed["nodes"], "edges": changed["edges"]}, "expected_version": 2}, headers=ORIGIN)
    body = kept.get_json()
    check("FR-72 a change of a %s graph is refused: 422 %s naming the kind" % (kind, code),
          kept.status_code == 422 and body.get("error") == code and body.get("kind") == kind, "%s %s" % (kept.status_code, body))
    if code == "not_editable":
        check("FR-72 the refusal of a context graph gives the reason the page shows (D-602)", "G-V4.CONTEXT" in (body.get("reason") or ""), str(body))
    restored = o.post("/api/v2/graphs/%s/restore" % gid, json={"version": 1}, headers=ORIGIN)
    body = restored.get_json()
    check("FR-73 a restore of a %s graph is refused: 422 %s naming the kind" % (kind, code),
          restored.status_code == 422 and body.get("error") == code and body.get("kind") == kind, "%s %s" % (restored.status_code, body))
    check("nothing was written for the %s graph (versions and record of changes as before)" % kind, state(gid) == before)

# Regression: a workflow graph is still kept, and the check route still answers the context rules for a context graph (RULES, D-404)
cur = o.get("/api/v2/graphs/cp2.multi").get_json()
wf = copy.deepcopy(cur["graph"]); wf["description"] = "changed by cp22"
kept = o.put("/api/v2/graphs/cp2.multi", json={"graph": {"description": wf["description"], "nodes": wf["nodes"], "edges": wf["edges"]}, "expected_version": cur["current"]}, headers=ORIGIN)
check("a workflow graph is still kept as a new version", kept.status_code == 200 and kept.get_json()["changed"] is True, str(kept.get_json()))
checked = o.post("/api/v2/graphs/ctx.one/check", json={"graph": {"nodes": r_ctx["graph"]["nodes"], "edges": r_ctx["graph"]["edges"]}}, headers=ORIGIN)
check("the check route still checks a context graph with the context rules", checked.status_code == 200 and checked.get_json()["rules"] == [], str(checked.get_json()))

failed = [r for r in results if not r[1]]
print(f"\n{len(results)} checks, {len(failed)} failed")
sys.exit(1 if failed else 0)
