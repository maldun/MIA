"""
Acceptance tests of the pipeline-to-graph converter (G-V2.CONVERT, task T-CV-03d, A-123 P2 and P3, D-246): TC-WFM-125 to TC-WFM-129 and TC-WFM-144, preconditions of REQ-WFM-058.
RED until T-CV-03d: `pipeline_graph.py` is a stub. No model, no network: the converter only reads the pipeline JSON of library/pipelines and the node JSON of library/nodes.

Interface under test (a proposal, reviewed with the tests): `pipeline_graph.convert(pipeline, library_nodes, budget_seconds)` -> {"graph", "inputs", "result", "notes", "refused"}.
- `graph` is a workflow graph (the make_graph form) of data, transform and master nodes that keeps check_graph; `refused` is a list of {"node", "reason"} and the graph is None when it is
  not empty (the skill then stays on the old runner, REQ-WFM-057).
- Node IDs: a transform is `step.<id>`, a variable is the data node `var.<name>` (written again later: `var.<name>#2`, `#3`), a pipeline input is `input.<field>`, a literal in a wire is
  `literal.<step id>.<parameter>` with the literal as the node's `value`, the settings of a construct are `settings.<step id>`.
- A call (`use: <node id>@<version>`) is a transform with toolbox_id `<node id>`; its wire becomes edges into it named by the parameter (`as`); its `output` is a data node it writes.
  A reference with a field (`$raw.claims`: variable raw, path claims) goes through a pick transform `pick.<step id>.<parameter>` (toolbox_id code.pick_field) that reads the variable as
  `value` and has a settings data node `settings.pick.<step id>.<parameter>` with {"path": "claims"}; it writes the data node `var.pick.<step id>.<parameter>`, which the step reads
  under the parameter name (owner, D-252). Steps (picks included, each just before its step) are chained in the order of the pipeline (graph_order.order_steps).
- A construct (`branch`, `map`, `loop`) is ONE node with toolbox_id `control.<kind>` and a settings data node (edge role settings) whose value is {"construct": kind, "node": <the JSON of
  the construct as in the pipeline>}. It is a master node when it contains a map or a loop (stop: `max_repetitions` = the largest `max` of a loop inside, if any; `max_seconds` =
  budget_seconds), otherwise a transform (A-123 P2). It reads every variable its JSON refers to and writes every variable assigned inside it.
Run with: python tests/acceptance/test_pipeline_graph.py
"""
import glob
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark                                              # noqa: E402
from graph_model import check_graph, order_of                         # noqa: E402
import pipeline_graph                                                 # noqa: E402

BUDGET_SECONDS = 120


def load_pipeline(pipeline_id, version):
    with open(os.path.join(REPO, "library", "pipelines", pipeline_id, "%d.json" % version), encoding="utf-8") as handle:
        return json.load(handle)


def library_nodes():
    latest = {}
    for path in sorted(glob.glob(os.path.join(REPO, "library", "nodes", "*", "*.json"))):
        with open(path, encoding="utf-8") as handle:
            node = json.load(handle)
        if node["version"] > latest.get(node["id"], {"version": 0})["version"]:
            latest[node["id"]] = node
    return latest


def edges_of(graph):
    return {(e["from"], e["to"]): e["data"] for e in graph["edges"]}


def nodes_of(graph):
    return {n["id"]: n["data"] for n in graph["nodes"]}


def step_order(graph):
    kinds = nodes_of(graph)
    return [i for i in order_of(graph) if kinds[i]["type"] in ("transform", "master")]


def real_steps(graph):
    """the steps of the pipeline in order, without the pick transforms of field references"""
    return [i for i in step_order(graph) if not i.startswith("pick.")]


def contains(node, kinds):
    if node.get("kind") in kinds:
        return True
    return any(isinstance(x, dict) and contains(x, kinds) for key in ("body", "then", "else") for x in node.get(key) or [])


def loop_maxima(node):
    found = [node["max"]] if node.get("kind") == "loop" and "max" in node else []
    for key in ("body", "then", "else"):
        for child in node.get(key) or []:
            if isinstance(child, dict):
                found += loop_maxima(child)
    return found


class PipelineGraph(unittest.TestCase):
    def setUp(self):
        self.library = library_nodes()

    def convert(self, pipeline):
        found = pipeline_graph.convert(pipeline, self.library, BUDGET_SECONDS)
        self.assertIsNotNone(found, "convert gave nothing")
        return found

    @mark.req("REQ-WFM-058")
    def test_the_three_simple_pipelines_become_flat_graphs_of_transforms_in_pipeline_order(self):
        """TC-WFM-125: plan.free@1, verify.single@1 and extract.llm@1: no refusal, a graph that keeps the rules, one transform `step.<id>` per call with its node ID as toolbox ID,
        the transforms in the order of the pipeline, a data node per pipeline input, per output variable, the inputs and the result named."""
        expected = {("plan.free", 1): (["plan", "norm"], ["view.research_plan", "code.normalize_plan"], {"question": "input.question"}, "var.plan"),
                    ("verify.single", 1): (["judge", "count"], ["view.verdict", "code.tally"], {"claim": "input.claim", "evidence": "input.evidence"}, "var.verdict"),
                    ("extract.llm", 1): (["ask", "anchor"], ["view.extract_claims", "code.anchor_claims"], {"text": "input.text"}, "var.answer")}
        for (pipeline_id, version), (steps, toolbox, inputs, result_node) in expected.items():
            with self.subTest(pipeline=pipeline_id):
                found = self.convert(load_pipeline(pipeline_id, version))
                self.assertEqual(found["refused"], [])
                graph = found["graph"]
                self.assertEqual(check_graph(graph), [])
                kinds = nodes_of(graph)
                self.assertEqual(real_steps(graph), ["step." + s for s in steps])
                self.assertEqual([kinds["step." + s]["toolbox_id"] for s in steps], toolbox)
                self.assertEqual((found["inputs"], found["result"]), (inputs, result_node))
                for node in list(inputs.values()) + [result_node]:
                    self.assertEqual(kinds[node]["type"], "data")

    @mark.req("REQ-WFM-058")
    def test_wires_become_named_edges_with_literals_and_field_references_through_a_pick_transform(self):
        """TC-WFM-126: in verify.single@1 the literal "an impartial checker" is a data node `literal.judge.context` with that value, read as `context`; the input `claim` is read
        as `claim`; the output variable `one` is written by the step and read by `count` as `verdicts`. In extract.llm@1 `$raw.claims` is a pick transform `pick.anchor.claims`
        (code.pick_field) that reads var.raw as `value`, has the settings node {"path": "claims"}, writes var.pick.anchor.claims, which step.anchor reads as `claims`; the pick comes
        after `ask` and before `anchor`."""
        graph = self.convert(load_pipeline("verify.single", 1))["graph"]
        edges, kinds = edges_of(graph), nodes_of(graph)
        self.assertEqual(kinds["literal.judge.context"]["value"], "an impartial checker")
        self.assertEqual(edges[("literal.judge.context", "step.judge")], {"as": "context"})
        self.assertEqual(edges[("input.claim", "step.judge")], {"as": "claim"})
        self.assertIn(("step.judge", "var.one"), edges)
        self.assertEqual(edges[("var.one", "step.count")], {"as": "verdicts"})
        graph = self.convert(load_pipeline("extract.llm", 1))["graph"]
        edges, kinds = edges_of(graph), nodes_of(graph)
        self.assertEqual(kinds["pick.anchor.claims"]["toolbox_id"], "code.pick_field")
        self.assertEqual(edges[("var.raw", "pick.anchor.claims")], {"as": "value"})
        self.assertEqual(kinds["settings.pick.anchor.claims"]["value"], {"path": "claims"})
        self.assertEqual(edges[("settings.pick.anchor.claims", "pick.anchor.claims")], {"role": "settings"})
        self.assertIn(("pick.anchor.claims", "var.pick.anchor.claims"), edges)
        self.assertEqual(edges[("var.pick.anchor.claims", "step.anchor")], {"as": "claims"})
        self.assertEqual(edges[("input.text", "step.anchor")], {"as": "text"})
        self.assertEqual(step_order(graph), ["step.ask", "pick.anchor.claims", "step.anchor"])
        self.assertEqual(check_graph(graph), [])

    @mark.req("REQ-WFM-058")
    def test_a_branch_with_a_loop_is_one_master_node_with_the_construct_as_its_settings(self):
        """TC-WFM-127: verify.computable@2: shape, write and run are transforms, then ONE master node `step.repair` with toolbox_id control.branch whose stop is the loop's
        maximum (2) and the budget seconds, a settings node holding the branch JSON exactly as in the pipeline, reading the variables the branch uses and writing the variables it
        assigns as new versions; the result is the last version of `verdict`."""
        pipeline = load_pipeline("verify.computable", 2)
        found = self.convert(pipeline)
        self.assertEqual(found["refused"], [])
        graph = found["graph"]
        self.assertEqual(check_graph(graph), [])
        kinds, edges = nodes_of(graph), edges_of(graph)
        self.assertEqual(real_steps(graph), ["step.shape", "step.write", "step.run", "step.repair"])
        self.assertIn("pick.run.script", step_order(graph))      # run reads `$written.script`
        master = kinds["step.repair"]
        self.assertEqual((master["type"], master["toolbox_id"]), ("master", "control.branch"))
        self.assertEqual(master["stop"], {"max_repetitions": 2, "max_seconds": BUDGET_SECONDS})
        repair = next(n for n in pipeline["nodes"] if n["id"] == "repair")
        self.assertEqual(kinds["settings.repair"]["value"], {"construct": "branch", "node": repair})
        self.assertEqual(edges[("settings.repair", "step.repair")], {"role": "settings"})
        for variable in ("var.described", "var.written", "var.verdict", "input.claim", "input.data"):
            self.assertIn((variable, "step.repair"), edges)
        self.assertIn(("step.repair", "var.verdict#2"), edges)
        self.assertIn(("step.repair", "var.written#2"), edges)
        self.assertEqual(found["result"], "var.verdict#2")

    @mark.req("REQ-WFM-058")
    def test_research_escalate_keeps_its_calls_as_transforms_and_wraps_every_map_and_loop(self):
        """TC-WFM-128: research.escalate@3: no refusal, a valid graph; every top-level call is a transform with its toolbox ID, in the order of the pipeline; the top-level map `read` is
        a master node control.map with stop max_seconds only (it has no bound of its own, noted in `notes`); the branch `escalate` that contains maps and a loop is a master node
        control.branch with the loop's largest maximum and the budget seconds; no map or loop is a node of its own."""
        pipeline = load_pipeline("research.escalate", 3)
        found = self.convert(pipeline)
        self.assertEqual(found["refused"], [])
        graph = found["graph"]
        self.assertEqual(check_graph(graph), [])
        kinds = nodes_of(graph)
        self.assertEqual(real_steps(graph), ["step." + n["id"] for n in pipeline["nodes"]])
        for node in pipeline["nodes"]:
            data = kinds["step." + node["id"]]
            if "use" in node:
                self.assertEqual((data["type"], data["toolbox_id"]), ("transform", node["use"].split("@")[0]))
            else:
                wrapped = contains(node, ("map", "loop"))
                self.assertEqual((data["type"], data["toolbox_id"]), ("master" if wrapped else "transform", "control." + node["kind"]))
        self.assertEqual(kinds["step.read"]["stop"], {"max_seconds": BUDGET_SECONDS})
        maxima = loop_maxima(next(n for n in pipeline["nodes"] if n["id"] == "escalate"))
        self.assertEqual(kinds["step.escalate"]["stop"], dict({"max_repetitions": max(maxima)} if maxima else {}, max_seconds=BUDGET_SECONDS))
        self.assertTrue(any("read" in note for note in found["notes"]), "the unbounded map is not noted")
        self.assertEqual(sum(1 for d in kinds.values() if d["type"] == "master"), 2)

    @mark.req("REQ-WFM-058")
    def test_what_cannot_be_placed_is_refused_by_name_and_a_plain_branch_is_a_transform(self):
        """TC-WFM-129: a call of a node that is not in the library, and a node kind the converter does not know, are refused naming the node and giving a reason; the graph is None.
        The same pipeline without them converts. A branch of fixed alternatives with plain calls inside is a transform node control.branch with a settings node, not a master."""
        base = {"id": "t.p", "version": 1, "result": "out", "nodes": [{"id": "a", "use": "code.tally@1", "wire": {"verdicts": "$input.v"}, "output": "out"}]}
        found = self.convert(base)
        self.assertEqual((found["refused"], check_graph(found["graph"])), ([], []))
        for label, extra, name in (("unknown library node", {"id": "b", "use": "code.not_there@1", "wire": {}, "output": "x"}, "b"),
                                   ("unknown kind", {"id": "c", "kind": "ask_user", "question": "which?"}, "c")):
            with self.subTest(case=label):
                found = self.convert(dict(base, nodes=base["nodes"] + [extra]))
                self.assertIsNone(found["graph"])
                self.assertEqual([r["node"] for r in found["refused"]], [name])
                self.assertTrue(found["refused"][0]["reason"])
        branch = {"id": "pick", "kind": "branch", "if": {"ref": "out.status", "op": "==", "value": "x"},
                  "then": [{"id": "d", "use": "code.tally@1", "wire": {"verdicts": "$out"}, "output": "out2"}]}
        found = self.convert(dict(base, result="out2", nodes=base["nodes"] + [branch]))
        data = nodes_of(found["graph"])["step.pick"]
        self.assertEqual((data["type"], data["toolbox_id"]), ("transform", "control.branch"))
        self.assertIn("settings.pick", nodes_of(found["graph"]))

    @mark.req("REQ-WFM-058")
    def test_converted_names_never_clash_and_no_data_node_has_two_writers(self):
        """TC-WFM-144: a step and a variable with the same name (plan.free has step `plan` and variable `plan`) and a variable named like an order node (`order-step.a`) give a graph
        with unique node IDs in which every data node has at most one writer, or a refusal; never a graph that breaks the rules."""
        pipeline = {"id": "t.clash", "version": 1, "result": "plan", "nodes": [
            {"id": "plan", "use": "code.tally@1", "wire": {"verdicts": "$input.v"}, "output": "order-step.plan"},
            {"id": "a", "use": "code.tally@1", "wire": {"verdicts": "$order-step.plan"}, "output": "plan"}]}
        found = self.convert(pipeline)
        if found["graph"] is None:
            self.assertTrue(found["refused"])
            return
        ids = [n["id"] for n in found["graph"]["nodes"]]
        self.assertEqual(len(ids), len(set(ids)), "a node ID is used twice")
        self.assertEqual(check_graph(found["graph"]), [])
        self.assertEqual(real_steps(found["graph"]), ["step.plan", "step.a"])


if __name__ == "__main__":
    unittest.main()
