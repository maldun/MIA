"""Fakes and builders for the acceptance tests of G-V2.MODEL (N-2.3 graph model and skill record, N-2.4.1 graph run).

Test requirements TR-MODEL-001 and TR-MODEL-004 (specs/mia/test-requirements.md):
- FakeGraphTables is a minimal fake of the graph tables: a dict per table keyed by ID, versions 1..n, nothing else. It is run against the
  contract suite of IF-301 v2 as soon as G-V2.STORE has that suite (plan task T-05). Known gap: it checks nothing and enforces no rule.
- Script gives scripted nodes (no model server). A run is observed by an ordered list of node IDs and a marker file in a fresh folder.

Every node and edge of a test is built here, so a change of a field name (the proposal of the node types is not decided yet, see
specs/mia/goals/G-V2.MODEL/goal.md) is a change in this one file.
"""

import copy
import os
import tempfile


class FakeGraphTables:
    def __init__(self):
        self._rows = {}

    def put(self, table, record_id, doc):
        rows = self._rows.setdefault((table, record_id), [])
        rows.append(copy.deepcopy(doc))
        return len(rows)

    def get(self, table, record_id, version=None):
        rows = self._rows[(table, record_id)]
        return copy.deepcopy(rows[-1 if version is None else version - 1])

    def versions(self, table, record_id):
        return list(range(1, len(self._rows.get((table, record_id), [])) + 1))


def make_node(node_type, node_id, **fields):
    return {"id": node_id, "data": dict(type=node_type, **fields)}


def data_node(node_id, **fields):
    return make_node("data", node_id, **fields)


def transform_node(node_id, toolbox_id=None):
    return make_node("transform", node_id, toolbox_id=toolbox_id or node_id.lower())


def master_node(node_id, max_repetitions=1, toolbox_id=None):
    fields = {"toolbox_id": toolbox_id or node_id.lower()}
    if max_repetitions is not None:
        fields["stop"] = {"max_repetitions": max_repetitions}
    return make_node("master", node_id, **fields)


def make_edge(start, end):
    return {"id": "%s>%s" % (start, end), "from": start, "to": end, "data": {}}


def make_graph(graph_id, nodes, edges, context_graph_id=None, testbench_id="", description="a test graph"):
    return {"id": graph_id, "context_graph_id": context_graph_id or "ctx-" + graph_id, "testbench_id": testbench_id,
            "description": description, "nodes": nodes, "edges": edges}


def make_skill(skill_id, command, workflow_graph_id=None, context_graph_id=None):
    return {"id": skill_id, "command": command, "workflow_graph_id": workflow_graph_id or "wf-" + skill_id,
            "context_graph_id": context_graph_id or "ctx-" + skill_id}


class Script:
    """Scripted nodes of one run: `order` lists the IDs in the order they ran; a marker node also writes a file in a fresh folder."""

    def __init__(self):
        self.order = []
        self.folder = tempfile.mkdtemp(prefix="graph-run-")

    def _result(self, node_id, inputs):
        return "%s(%s)" % (node_id, ",".join(str(inputs[key]) for key in sorted(inputs)))

    def node(self, node_id):
        def run(inputs):
            self.order.append(node_id)
            return self._result(node_id, inputs)
        return run

    def marker_node(self, node_id):
        def run(inputs):
            self.order.append(node_id)
            open(self.marker_path(node_id), "w").close()
            return self._result(node_id, inputs)
        return run

    def failing_node(self, node_id):
        def run(inputs):
            self.order.append(node_id)
            raise RuntimeError("scripted failure of " + node_id)
        return run

    def marker_path(self, node_id):
        return os.path.join(self.folder, node_id + ".marker")

    def marker_exists(self, node_id):
        return os.path.exists(self.marker_path(node_id))
