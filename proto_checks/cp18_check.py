"""PROTOTYPE round 04 CP18: rule 7 (session setting and stop limit, ASM-3) and the candidate rule "a processing step needs a tool", counted on every graph the
prototype stores (the 15 converted skill graphs, cp2.multi, sample.code, sample.broken). Counts only: the decisions are the owner's (validation sheet of round 04).

Run: python proto_checks/cp18_check.py
"""
import collections
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path[:0] = [REPO]
os.chdir(REPO)

import graph_rules_proto as R                                    # noqa: E402
from toolbox import CONTROLS                                       # noqa: E402
from proto_checks.cp1_check import converted, _latest_nodes       # noqa: E402
from proto_checks.cp2_check import small                          # noqa: E402

results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(("PASS " if ok else "FAIL ") + name + (" - " + str(detail)[:300] if detail and not ok else ""))


def sample_code():
    """the graph of make_sample_store.add_code, without storing it"""
    hostile = '<img src=x onerror=alert(1)> step "quoted" & more'
    return {"id": "sample.code",
            "nodes": [{"id": "var.in", "data": {"type": "data", "value": "x"}}, {"id": "var.code", "data": {"type": "data", "value": "print('hello')"}},
                      {"id": hostile, "data": {"type": "transform", "toolbox_id": "import.demo"}}, {"id": "var.mid", "data": {"type": "data"}},
                      {"id": "loop.review", "data": {"type": "master", "toolbox_id": "control.loop", "stop": {"max_repetitions": 3}}},
                      {"id": "var.out", "data": {"type": "data"}}, {"id": "step.check", "data": {"type": "transform", "toolbox_id": "check.number"}}],
            "edges": [{"id": "e1", "from": "var.in", "to": hostile, "data": {}}, {"id": "e2", "from": "var.code", "to": hostile, "data": {"role": "code"}},
                      {"id": "e3", "from": hostile, "to": "var.mid", "data": {}}, {"id": "e4", "from": "var.mid", "to": "loop.review", "data": {}},
                      {"id": "e5", "from": "loop.review", "to": "var.out", "data": {}}, {"id": "e6", "from": "var.mid", "to": "step.check", "data": {}}]}


graphs = converted() + [small("cp2.multi", "v1"), sample_code()]
known_tools = set(_latest_nodes("library/nodes")) | set(CONTROLS)

clauses = collections.Counter()
settings_steps, masters, steps = 0, 0, 0
tool_missing, tool_unknown = [], []
for g in graphs:
    nodes, edges = g["nodes"], g["edges"]
    settings_in = collections.Counter(e["to"] for e in edges if (e.get("data") or {}).get("role") == "settings")
    settings_steps += len(settings_in)
    for n in nodes:
        data = n.get("data") or {}
        if data.get("type") == "data" and {"stop", "session"} & set(data):
            clauses["a data step holds a stop or session setting"] += 1
        if data.get("type") == "master":
            masters += 1
            if not R.stop_is_valid(data.get("stop")):
                clauses["a loop-controlling step without a valid stop limit"] += 1
        if data.get("type") in ("transform", "master"):
            steps += 1
            tool = data.get("toolbox_id")
            if not isinstance(tool, str) or not tool:
                tool_missing.append("%s: %s" % (g["id"], n["id"]))
            elif tool not in known_tools:
                tool_unknown.append("%s: %s (%s)" % (g["id"], n["id"], tool))
    clauses["a step with more than one settings connection"] += sum(1 for c in settings_in.values() if c > 1)

print("graphs: %d; processing and loop-controlling steps: %d; loop-controlling: %d; steps with a settings connection: %d" % (len(graphs), steps, masters, settings_steps))
print("rule 7 (ASM-3), broken parts by clause:", dict(clauses) or "none")
print("candidate rule 'a processing step needs a tool': no tool named: %d %s; a tool the toolbox does not know: %d %s"
      % (len(tool_missing), tool_missing[:5], len(tool_unknown), tool_unknown[:8]))

check("ASM-3 no stored graph breaks rule 7 as the prototype defines it (so the definition refuses nothing that runs today)", sum(clauses.values()) == 0, dict(clauses))
check("ASM-3 the settings clause is not empty: some stored steps take their settings through a settings connection", settings_steps > 0, settings_steps)
check("candidate rule: every processing step of a converted skill names a tool", not [t for t in tool_missing if not t.startswith(("cp2.", "sample."))], tool_missing)
print("\n%d checks, %d failed" % (len(results), results.count(False)))
sys.exit(0 if all(results) else 1)
