"""Run of a workflow graph in topological order (N-2.4.1, G-V2.MODEL T-03 and T-04): STUB, written in Plan step 4 so the red tests import.

Real behaviour comes with plan tasks T-03 and T-04 (REQ-RUN-016 to 019). The tests in tests/acceptance/test_graph_run.py fix this interface:
- GraphRunner(trust): `trust(node_id)` -> "trusted" or "untrusted" (stand-in for the toolbox of G-V2.TOOLBOX).
- run(graph, nodes, inputs) -> RunResult(status, named, named_status, values): `nodes` maps a transform or master node ID to a function
  of {input data node ID: value} that returns the value it writes; `inputs` maps data node IDs to their starting values.
  status is "done", "refused" (before any node ran: named = the node IDs, named_status = their status) or "failed" (named = [the failed node]);
  `values` maps each data node ID to its value after the run.
"""

from collections import namedtuple

RunResult = namedtuple("RunResult", "status named named_status values")


class GraphRunner:
    def __init__(self, trust):
        self.trust = trust

    def run(self, graph, nodes, inputs):
        return RunResult("not_run", [], None, {})
