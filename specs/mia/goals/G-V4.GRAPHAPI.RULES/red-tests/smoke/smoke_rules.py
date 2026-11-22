"""SMOKE-RULES-001 (G-V4.GRAPHAPI.RULES, run in Phase 6 on the owner's host with the installed release): the 15 skills pass the run check with their
usual inputs, and the round 04 sample `sample.broken` is refused naming `e2` with no step run (REQ-RUN-036, HR-006).

It writes nothing: the run check is pure, and the sample is run with marker functions on a throw-away folder that is removed afterwards; MIA's own
store is not opened. Exit code 0 when every line passes.

Run with: python tests/smoke/smoke_rules.py
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))

from graph_rule_set import run_check                      # noqa: E402
from graph_run import GraphRunner                         # noqa: E402
from graph_model_fakes import Script                      # noqa: E402
from rules_graphs import connection, converted_skills, data, graph, transform   # noqa: E402

failures = []
for name, g in converted_skills():
    given = {b["input"]: "x" for b in run_check(g)["broken"] if b.get("kind") == "input"}
    said = run_check(g, given)
    print("%-28s %s" % (name, said["status"]))
    if said != {"status": "ready", "broken": []}:
        failures.append(name)

# sample.broken of round 04: a connection e2 from a step that does not exist
broken = graph([data("q", value="why?"), transform("answer"), data("out")],
               [connection("e1", "q", "answer"), connection("e2", "ghost", "answer"), connection("e3", "answer", "out")], graph_id="sample.broken")
script = Script()
try:
    result = GraphRunner(lambda node_id: "trusted").run(broken, {"answer": script.marker_node("answer")}, {})
finally:
    shutil.rmtree(script.folder, True)
print("sample.broken                %s %s, steps run: %s" % (result.status, result.named, script.order))
if (result.status, result.named, script.order) != ("refused", ["e2"], []):
    failures.append("sample.broken")
print("SMOKE-RULES-001:", "pass" if not failures else "FAIL " + ", ".join(failures))
sys.exit(1 if failures else 0)
