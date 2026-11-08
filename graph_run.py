"""Run of a workflow graph in topological order (N-2.4.1, G-V2.MODEL T-03 and T-04): STUB, written in Plan step 4 so the red tests import.

Real behaviour comes with plan tasks T-03 and T-04 (REQ-RUN-016 to 019). The tests in tests/acceptance/test_graph_run.py fix this interface:
- GraphRunner(trust): `trust(node_id)` -> "trusted" or "untrusted" (stand-in for the toolbox of G-V2.TOOLBOX).
- run(graph, nodes, inputs) -> RunResult(status, named, named_status, values): `nodes` maps a transform or master node ID to a function
  of {input data node ID: value} that returns the value it writes; `inputs` maps data node IDs to their starting values.
  status is "done", "refused" (before any node ran: named = the node IDs, named_status = their status) or "failed" (named = [the failed node]);
  A graph the runner cannot put in an order is "refused" too, before any node ran (named = the edges to an unknown node, else the cycle as node IDs, named_status = None);
  `values` maps each data node ID to its value after the run.
"""

from collections import namedtuple

try:
    from .graph_model import _find_cycle, order_of
except ImportError:
    from graph_model import _find_cycle, order_of

RunResult = namedtuple("RunResult", "status named named_status values")


class GraphRunner:
    def __init__(self, trust):
        self.trust = trust

    def run(self, graph, nodes, inputs):
        kinds = {n["id"]: n["data"]["type"] for n in graph["nodes"]}
        # REQ-RUN-016: a graph without an order is not run (the writers of IF-102 do not run the graph rules, D-262)
        unknown = [e["id"] for e in graph["edges"] if e["from"] not in kinds or e["to"] not in kinds]
        cycle = None if unknown else _find_cycle(list(kinds), graph["edges"])
        if unknown or cycle:
            return RunResult("refused", unknown or cycle, None, _data_values(kinds, dict(inputs)))
        reads = {i: [] for i in kinds}
        for edge in graph["edges"]:
            reads[edge["to"]].append(edge["from"])
        # REQ-RUN-017: check every transform and master node before the first one runs. Any status except "trusted"
        # counts as untrusted, so an unknown status never lets a node run.
        refused = {i: self.trust(i) for i, k in kinds.items() if k != "data"}
        refused = {i: s for i, s in refused.items() if s != "trusted"}
        if refused:
            named = [i for i in order_of(graph) if i in refused]
            return RunResult("refused", named, refused[named[0]], _data_values(kinds, dict(inputs)))
        values = dict(inputs)
        for node_id in order_of(graph):
            if kinds[node_id] == "data":
                continue
            # A master node runs once, like a transform; its stop criterion is stored and unused until debates (FR-39).
            try:
                result = nodes[node_id]({d: values[d] for d in reads[node_id] if d in values})
            except Exception:
                return RunResult("failed", [node_id], None, _data_values(kinds, values))
            for edge in graph["edges"]:
                if edge["from"] == node_id:
                    values[edge["to"]] = result
        return RunResult("done", [], None, _data_values(kinds, values))


def _data_values(kinds, values):
    return {i: v for i, v in values.items() if kinds.get(i) == "data"}
