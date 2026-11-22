"""PROTOTYPE round 04 CP19: the same broken rules everywhere (OC-1: saving, the check route of the editor, keeping, before a run) and the refusal before
any step runs (OC-2: broken rules, inputs nobody supplies, a kind that cannot run, a kind the program does not know). Not a protected test.

Run: python proto_checks/cp19_check.py   (files backend in a temporary folder)
"""
import copy
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path[:0] = [REPO]
os.chdir(REPO)

import accounts, graph_model, graph_proto_app, graph_rules_proto as R    # noqa: E401,E402
from storage import Storage                                                 # noqa: E402
from storage_files import FileBackend                                       # noqa: E402
from proto_checks.make_sample_store import populate, add_code, add_broken  # noqa: E402
from proto_checks.cp1_check import converted                               # noqa: E402

results = []


def ctx(gid):
    """the context graph of cp13_check (copied: importing that module runs it)"""
    return {"id": gid, "kind": "context", "context_graph_id": "", "testbench_id": "", "description": "context graph of cp19",
            "nodes": [{"id": "claim", "data": {"type": "claim", "text": "water boils at 100 C"}}, {"id": "source", "data": {"type": "source", "url": "local:book-1"}},
                      {"id": "step.write", "data": {"type": "note", "text": "ctx"}}],
            "edges": [{"id": "e1", "from": "source", "to": "claim", "data": {"relation": "supports"}}, {"id": "e2", "from": "claim", "to": "step.write", "data": {}}]}


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (" - " + str(detail)[:400] if detail and not ok else ""))


D = lambda i, **k: {"id": i, "data": {"type": "data", **k}}                                      # noqa: E731
T = lambda i: {"id": i, "data": {"type": "transform", "toolbox_id": "check.number"}}            # noqa: E731
E = lambda i, a, b, **d: {"id": i, "from": a, "to": b, "data": d}                                # noqa: E731
pairs = lambda items: [(r.get("rule"), r["parts"]) for r in items]                              # noqa: E731

# OC-1: two graphs that break several rules (the cycle is only asked when every connection has both ends, CP4, so it needs a graph of its own)
WITH_CYCLE = {"nodes": [D("q"), T("s1"), T("s2"), D("w"), D("back")],
              "edges": [E("e1", "q", "s1"), E("e2", "q", "s1"), E("e3", "s1", "w"), E("e4", "s2", "w"), E("e5", "w", "s2"), E("e6", "s2", "back"), E("e7", "back", "s1")]}
WITH_GAP = {"nodes": [D("q"), T("s1"), T("s2"), D("w")],
            "edges": [E("e1", "q", "s1"), E("e2", "q", "s1"), E("e3", "s1", "w"), E("e4", "s2", "w"), E("e5", "s2", "gone")]}

tmp = tempfile.mkdtemp()
live = FileBackend(os.path.join(tmp, "s"))
populate(live)
add_code(live)
add_broken(live)
saved_ctx = graph_model.GraphModel(Storage(live), author="cp19").save_graph(ctx("ctx.one"))
acc = Storage(FileBackend(os.path.join(tmp, "a")))
accounts.create(acc, "owner", "secret", "cp19")
ORIGIN = {"Origin": "http://127.0.0.1:8801"}
app = graph_proto_app.create_app(live, acc)
o = app.test_client()
o.post("/api/login", json={"user": "owner", "password": "secret"}, headers=ORIGIN)
U = "/api/v2/graphs/"
before = sorted(Storage(live).ids("graph_nodes"))

for label, broken, expected in (("cycle, duplicate, two writers", WITH_CYCLE, ["duplicate_connection", "single_writer", "cycle"]),
                                ("missing step, duplicate, two writers", WITH_GAP, ["connection_endpoints", "duplicate_connection", "single_writer"])):
    body = {"graph": copy.deepcopy(broken)}
    by_function = R.check(broken)
    by_save = graph_model.GraphModel(Storage(live), author="cp19").save_graph({**graph_model.GraphModel(Storage(live)).read_graph("cp2.multi"), **copy.deepcopy(broken)})
    by_check = o.post(U + "cp2.multi/check", json=body, headers=ORIGIN).get_json()["rules"]
    kept = o.put(U + "cp2.multi", json=body, headers=ORIGIN)
    ran = o.post(U + "cp2.multi/run", json=body, headers=ORIGIN)
    run_rules = [b for b in ran.get_json()["broken"] if b["kind"] == "rule"]
    lists = {"function": pairs(by_function), "save": pairs(by_save.rules or []), "check route": pairs(by_check),
             "keep route": pairs(kept.get_json().get("rules") or []), "run route": pairs(run_rules)}
    check("OC-1 (%s): saving, the check route, keeping and the run route list the same broken rules in the same order with the same parts" % label,
          [r for r, _ in lists["function"]] == expected and all(v == lists["function"] for v in lists.values()), json.dumps(lists))
    check("OC-1 (%s): five checks in a row give the same list" % label, all(pairs(R.check(copy.deepcopy(broken))) == lists["function"] for _ in range(5)))
    check("OC-2 (%s): the run is refused and no step ran; keeping is refused" % label,
          ran.status_code == 422 and ran.get_json()["status"] == "refused" and ran.get_json()["ran"] == [] and kept.status_code == 422)
check("OC-2 nothing was written by the refused saves and keeps", sorted(Storage(live).ids("graph_nodes")) == before)

# OC-2: an input nobody supplies, named after the rules
gap = {"nodes": [D("question"), T("answer"), D("reply")], "edges": [E("e1", "question", "answer"), E("e2", "answer", "reply")]}
ran = o.post(U + "cp2.multi/run", json={"graph": gap}, headers=ORIGIN).get_json()
check("OC-2 an input with no writer, no start value and no value given is named with its step; no step runs",
      ran["status"] == "refused" and ran["ran"] == [] and [(b["kind"], b.get("step"), b.get("input")) for b in ran["broken"]] == [("input", "answer", "question")], ran)
ran = o.post(U + "cp2.multi/run", json={"graph": gap, "inputs": {"question": "why?"}}, headers=ORIGIN).get_json()
check("OC-2 the same graph with the value given runs", ran["status"] != "refused" and ran["ran"] == ["answer"], ran)

# OC-2 and D-404: kinds
ctx_read = graph_model.GraphModel(Storage(live)).read_graph("ctx.one")
r_check = o.post(U + "ctx.one/check", json={"graph": {"nodes": ctx_read["nodes"], "edges": ctx_read["edges"]}}, headers=ORIGIN).get_json()
check("D-404 the check route checks a stored context graph with the context rule set (it keeps its rules)", saved_ctx.saved and r_check["rules"] == [], r_check)
dup = copy.deepcopy(ctx_read)
dup["edges"].append(dict(dup["edges"][0], id="e9"))
r_check = o.post(U + "ctx.one/check", json={"graph": {"nodes": dup["nodes"], "edges": dup["edges"]}}, headers=ORIGIN).get_json()
check("D-404 a broken context graph is named by the context rule set only (no workflow rule about kinds of steps or adjacency)", pairs(r_check["rules"]) == [("duplicate_connection", ["e9"])], r_check)
ran = o.post(U + "ctx.one/run", json={}, headers=ORIGIN)
check("FR-64 a stored context graph cannot run: refused naming the kind, no step ran",
      ran.status_code == 422 and pairs(ran.get_json()["broken"]) == [("kind_cannot_run", ["context"])] and ran.get_json()["ran"] == [], ran.get_json())
said = R.refusal({"kind": "plan", "nodes": [T("x")], "edges": []})
check("FR-64 a graph of a kind the program does not know is refused naming the kind (function; the Storage layer refuses to store such a header today, see the finding)",
      said == {"status": "refused", "broken": [{"kind": "kind", "rule": "unknown_kind", "parts": ["plan"], "text": R.TEXTS["unknown_kind"]}]}, said)
# what CORE does with a stored header of an unknown kind (a finding for Plan, not a check)
try:
    Storage(live).put("graphs", "odd.one", {"id": "odd.one", "data": {"kind": "plan", "nodes": [], "edges": [], "context_graph_id": "", "testbench_id": "", "description": "unknown kind"}}, "cp19")
    outcome = "stored"
except Exception as error:      # noqa: BLE001 -- the outcome is what is reported
    outcome = "refused by the Storage layer (%s: %s %s)" % (type(error).__name__, getattr(error, "rule", ""), getattr(error, "detail", ""))
print("FINDING a header of kind 'plan' written straight to the Storage layer -> %s" % outcome)

# regression: every converted skill graph is ready once the values of its open inputs are given
blocked = []
for g in converted():
    given = {m["input"]: "x" for m in R.missing_inputs(g)}
    said = R.refusal(g, given)
    if said["status"] != "ready":
        blocked.append((g["id"], pairs(said["broken"])))
check("FR-64 regression: each of the 15 converted skill graphs is ready with its inputs given (none is refused by the eight rules)", not blocked, blocked)

started = time.perf_counter()
for _ in range(100):
    R.refusal(WITH_CYCLE)
print("refusal of a 5-step graph: %.2f ms" % ((time.perf_counter() - started) * 10))
print("\n%d checks, %d failed" % (len(results), results.count(False)))
sys.exit(0 if all(results) else 1)
