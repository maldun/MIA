"""PROTOTYPE round 04 CP17: one rule set chosen by kind (D-404, FR-63), used by the save path; the older five rules mapped onto it.

Run: python proto_checks/cp17_check.py   (no database; prints one line per check, then the mapping tables for the report)
"""
import collections
import copy
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path[:0] = [REPO, os.path.join(REPO, "tests"), os.path.join(REPO, "tests", "helpers")]

import graph_rules_proto as R            # noqa: E402
from graph_rules import violation        # noqa: E402
from graph_model import GraphModel, context_problems   # noqa: E402
from test_graph_rules import doc, generated, LOOKUP     # noqa: E402

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (" - " + str(detail)[:300] if detail and not ok else ""))


def to_graph(document):
    """an old document (kind process|data, session, stop max_cycles) in the stored form (type transform|master|data, stop max_repetitions), edges numbered"""
    nodes = []
    for n in document["nodes"]:
        kind = n.get("kind")
        if kind == "process":
            data = {"type": "master" if n.get("session") else "transform"}
            if n.get("session"):
                stop = n.get("stop")
                data["stop"] = {("max_repetitions" if k == "max_cycles" else k): v for k, v in stop.items()} if isinstance(stop, dict) else stop
        else:
            data = {"type": kind}
        nodes.append({"id": n.get("id"), "data": data})
    edges = [{"id": "e%d" % i, "from": e["from"], "to": e["to"], "data": {}} for i, e in enumerate(document["edges"], 1)]
    return {"nodes": nodes, "edges": edges}


names = lambda g: [r["rule"] for r in R.check(g)]       # noqa: E731

# ---- the one place ----
check("FR-63 the registry names the workflow rules in the fixed order of D-375, and a workflow graph can run",
      R.KINDS["workflow"] == {"rules": ("step_identity", "step_kind", "connection_endpoints", "duplicate_connection", "adjacency", "single_writer", "stop_limit", "cycle"), "runs": True})
check("FR-63 the context rule set is taken from the same definitions (identity and ends), and a context graph cannot run",
      R.KINDS["context"] == {"rules": ("step_identity", "connection_endpoints", "duplicate_connection"), "runs": False} and all(r in R.RULES for r in R.KINDS["context"]["rules"]))
check("D-404 a graph of an unknown kind gives one item naming the kind, whatever its steps",
      [(r["rule"], r["parts"]) for r in R.check({"kind": "plan", "nodes": [{"id": "x"}], "edges": [{"id": "e", "from": "x", "to": "y"}]})] == [("unknown_kind", ["plan"])])
check("REQ-WFM-153 a graph without a kind is a workflow graph", R.check({"nodes": [{"id": "a", "data": {"type": "data"}}, {"id": "b", "data": {"type": "data"}}],
                                                                        "edges": [{"id": "e", "from": "a", "to": "b", "data": {}}]})[0]["rule"] == "adjacency")
check("CP17 a rule never raises: data that is not an object, steps without IDs, connections without ends",
      isinstance(R.check({"nodes": [{"data": "x"}, {"id": "a", "data": [1]}], "edges": [{"data": "x"}, {}]}), list))

# ---- the save path asks the same function ----
broken = {"id": "g", "toolbox_id": "t", "context_graph_id": None, "testbench_id": None, "description": "d",
          "nodes": [{"id": "a", "data": {"type": "data", "value": 1}}, {"id": "s1", "data": {"type": "transform"}}, {"id": "s2", "data": {"type": "transform"}},
                    {"id": "w", "data": {"type": "data"}}],
          "edges": [{"id": "e1", "from": "a", "to": "s1", "data": {}}, {"id": "e2", "from": "a", "to": "s1", "data": {}}, {"id": "e3", "from": "s1", "to": "w", "data": {}},
                    {"id": "e4", "from": "s2", "to": "w", "data": {}}, {"id": "e5", "from": "w", "to": "s1", "data": {}}]}
saved = GraphModel(object()).save_graph(copy.deepcopy(broken))
check("FR-63 a refused save lists the same broken rules, in the same order and with the same parts, as the check",
      not saved.saved and saved.rules == R.check(broken) and [r["rule"] for r in saved.rules] == ["duplicate_connection", "single_writer", "cycle"],
      saved)
check("CP17 the save names the parts of every broken rule in order; a cycle keeps its first step at the end", saved.named == [p for r in saved.rules for p in r["parts"]] and saved.rules[-1]["parts"][0] == saved.rules[-1]["parts"][-1], saved.named)

# ---- the context rule set against CORE's context_problems (REQ-WFM-155) ----
causes = collections.Counter()
rng = random.Random(17)
for _ in range(500):
    count = rng.randint(1, 6)
    ids = ["c%d" % i for i in range(count)] + rng.choice([[], ["c0"], [""]])
    nodes = [{"id": i, "data": {"type": "fact"}} for i in ids]
    edges = []
    for k in range(rng.randint(0, 6)):
        a, b = rng.choice(ids + ["gone"]), rng.choice(ids)
        edges.append({"id": rng.choice(["r%d" % k, "r0"]), "from": a, "to": b, "data": {}})
    graph = {"kind": "context", "nodes": nodes, "edges": edges}
    old, new = bool(context_problems(graph)), bool(R.check(graph))
    if old != new:
        if "" in ids and not old:
            causes["an empty step ID (new: step_identity; CORE: the record check refuses it later)"] += 1
        elif new and not old:
            causes["two identical connections with different IDs (new: duplicate_connection)"] += 1
        else:
            causes["other"] += 1
check("REQ-WFM-155 the context rule set refuses every context graph CORE refuses (500 generated graphs, seed 17); it refuses more only for the named causes",
      causes["other"] == 0, dict(causes))

# ---- the older five rules (graph_rules.py, TC-GTB-002) mapped onto the eight ----
CASES = [
    ("lookup graph", LOOKUP),
    ("a step ID used twice", doc([("a", "data", {}), ("a", "process", {})])),
    ("a connection to a missing step", doc([("a", "data", {})], [("a", "ghost")])),
    ("two data steps joined", doc([("a", "data", {}), ("b", "data", {})], [("a", "b")])),
    ("two processing steps joined", doc([("a", "process", {}), ("b", "process", {})], [("a", "b")])),
    ("a session with max_cycles 0", doc([("s", "process", {"session": True, "stop": {"max_cycles": 0}})])),
    ("a cycle p -> d -> p", doc([("p", "process", {}), ("d", "data", {})], [("p", "d"), ("d", "p")])),
    ("a self-loop of a processing step", doc([("a", "process", {})], [("a", "a")])),
    ("a step of kind tool", {"nodes": [{"id": "a", "kind": "tool"}], "edges": []}),
    ("an empty step ID", {"nodes": [{"id": "", "kind": "data"}], "edges": []}),
    ("a session with max_seconds 1.0", doc([("s", "process", {"session": True, "stop": {"max_seconds": 1.0}})])),
    ("a session with max_cycles True", doc([("s", "process", {"session": True, "stop": {"max_cycles": True}})])),
    ("a session with stop 'x'", doc([("s", "process", {"session": True, "stop": "x"})])),
    ("a 500-step chain", doc([(("d%d" if n % 2 == 0 else "p%d") % n, "data" if n % 2 == 0 else "process", {}) for n in range(500)],
                             [((("d%d" if n % 2 == 0 else "p%d") % n), (("d%d" if (n + 1) % 2 == 0 else "p%d") % (n + 1))) for n in range(499)])),
]
table = []
for label, document in CASES:
    old = violation(document)
    table.append((label, old[0] if old else "-", ", ".join(names(to_graph(document))) or "-"))
print("\ncontext graphs refused only by the new context rule set, by cause:", dict(causes))
chain500 = to_graph(CASES[-1][1])
import time   # noqa: E402
started = time.perf_counter()
R.check(chain500)
took = time.perf_counter() - started
check("IF-301 bound: the eight rules check a 500-step graph within 200 ms", took < 0.2, "%.3f s" % took)
print("500-step chain checked in %.1f ms" % (took * 1000))
print("\nold case | old rule (first only) | new rules (all, in order)")
for row in table:
    print(" | ".join(row))
silent = [row for row in table if row[1] != "-" and row[2] == "-"]
check("TC-GTB-002 cases: every case the five rules refuse is refused by the eight, except stop limits read by REQ-WFM-048 (max_seconds may be a float)",
      [row[0] for row in silent] == ["a session with max_seconds 1.0"], silent)

old_only, new_only = collections.Counter(), collections.Counter()
for seed in range(1, 1001):
    document, _ok, _order = generated(seed)
    old, new = violation(document), names(to_graph(document))
    if old and not new:
        old_only[old[0]] += 1
    elif new and not old:
        new_only[new[0]] += 1
print("\nTC-GTB-003 generator, seeds 1 to 1000: refused only by the eight rules, by first new rule:", dict(new_only), "; only by the five:", dict(old_only))
check("TC-GTB-003 generator (seeds 1 to 1000): no graph the five rules refuse is accepted by the eight", not old_only, dict(old_only))

print("\n%d checks, %d failed" % (len(results), results.count(False)))
sys.exit(0 if all(results) else 1)
