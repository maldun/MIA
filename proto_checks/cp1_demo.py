"""PROTOTYPE CP1 demo (a story the owner can read): scoped storage of graphs. Run: python proto_checks/cp1_demo.py"""
import copy, os, sys, tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO]
os.chdir(REPO)
import graph_model
from storage import Storage
from storage_files import FileBackend
from proto_checks.cp1_check import small

be = FileBackend(tempfile.mkdtemp())
m = graph_model.GraphModel(Storage(be), author="owner")
a, b = small("lookup", "x"), small("review", "y")
m.save_graph(a); m.save_graph(b)
print("Two graphs, each with a step named `step.write` (different content):")
print("  stored step records:", sorted(be.ids("graph_nodes")))
a2 = copy.deepcopy(a); a2["nodes"][1]["data"]["toolbox_id"] = "tool.write.changed"
m.save_graph(a2)
print("\nI change `step.write` in `lookup` and save:")
print("  versions of graph lookup:", [v["version"] for v in m.graph_versions("lookup")], " review:", [v["version"] for v in m.graph_versions("review")])
print("  history of step.write in lookup:", [v["version"] for v in m.step_history("lookup", "step.write")], " in review:", [v["version"] for v in m.step_history("review", "step.write")])
print("  review is unchanged:", m.read_graph("review") == b)
print("\nSaving the same graph again changes nothing:", m.save_graph(a2).version == 2)
bad = copy.deepcopy(a2); bad["edges"].append({"id": "e3", "from": "var.out", "to": "step.write", "data": {}})
r = m.save_graph(bad)
print("\nA graph with a cycle is refused:", not r.saved, "naming", r.named, "- versions still", [v["version"] for v in m.graph_versions("lookup")])
try:
    m.tables.put("graph_nodes", "step.write", {"id": "step.write", "data": {"type": "data"}}, "owner")
except Exception as e:
    print("\nA step record without its graph in the ID is refused:", getattr(e, "rule", e))
