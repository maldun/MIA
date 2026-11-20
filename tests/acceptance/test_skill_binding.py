"""
Acceptance tests of defaults in thin entries, the skill binder and the adapter between toolbox and runner (G-V2.CONVERT, task T-CV-04a, A-125 Q2 to Q4, D-253): TC-WFM-145 to
TC-WFM-148, preconditions of REQ-WFM-058. RED until T-CV-04a: `bind_skill` and `stages_from_toolbox` are stubs and the thin entries do not apply the parameter defaults of their node.
No model, no network: scripted model, recording.
Interface under test (reviewed, D-253):
- `pipeline_graph.bind_skill(graph, library_nodes, skill, changes=None)` -> a NEW graph (the input is not changed): a data node `descriptor.model` with the value
  {"model": profile, "options": options} of the skill's `model` setting (`changes["model"]` replaces profile and options where it gives them) and an edge with data {"as": "model"} into every
  transform whose library node is of kind model; for every library node of kind tool a data node `descriptor.tool.<tool name>` with the value {"tool": name, "settings": {}} and an
  edge {"as": "tool"} into each such transform. No descriptor node is added where no step needs it.
- `skill_converter.stages_from_toolbox(graph, toolbox)` -> (nodes, trust): `nodes` is the map `{node id: Stage(function)}` for GraphRunner.run, `trust(node id)` the trust of the toolbox entry of that node.
Run with: python tests/acceptance/test_skill_binding.py
"""
import copy
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
sys.path.insert(0, os.path.join(REPO, "tests", "helpers", "mocks"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers", "mocks"))

from markers import mark                                              # noqa: E402
from if_203_transforms import TransformLibraryMock                    # noqa: E402
from toolbox_fakes import EventRecord                                 # noqa: E402
from call_recording import Recording, RecordingModel, ScriptedModel, schema_reply   # noqa: E402
from graph_model import check_graph, order_of                         # noqa: E402
from graph_run import GraphRunner                                     # noqa: E402
from pipeline import render                                           # noqa: E402
from toolbox import Toolbox                                           # noqa: E402
import common_operations as ops                                       # noqa: E402
import pipeline_graph                                                 # noqa: E402
import skill_converter                                                # noqa: E402
import skill_store                                                    # noqa: E402

LIBRARY = os.path.join(REPO, "library")
LIGHT = {"model": "light", "options": {"temperature": 0}}
SKILL = {"name": "verify_claim", "model": {"profile": "light", "options": {"num_ctx": 4096}}}


def library_nodes():
    latest = {}
    for path in sorted(glob.glob(os.path.join(LIBRARY, "nodes", "*", "*.json"))):
        with open(path, encoding="utf-8") as handle:
            node = json.load(handle)
        if node["version"] > latest.get(node["id"], {"version": 0})["version"]:
            latest[node["id"]] = node
    return latest


def pipeline_of(pipeline_id, version):
    with open(os.path.join(LIBRARY, "pipelines", pipeline_id, "%d.json" % version), encoding="utf-8") as handle:
        return json.load(handle)


def edges_of(graph):
    return {(e["from"], e["to"]): e["data"] for e in graph["edges"]}


class SkillBinding(unittest.TestCase):
    def setUp(self):
        ops.reset()
        self.addCleanup(ops.reset)
        self.nodes = library_nodes()
        self.library = TransformLibraryMock()
        self.box = Toolbox(self.library, lambda account: True, EventRecord())
        self.box.seed_shipped(os.path.join(LIBRARY, "nodes"))
        self.recording = Recording()

    def ok(self, call, what):
        try:
            return call()
        except Exception as error:      # a stub or a missing piece must show as a failure of this test, with its name
            self.fail("%s: %s %s" % (what, type(error).__name__, error))

    @mark.req("REQ-WFM-058")
    def test_a_thin_entry_applies_the_parameter_defaults_of_its_node_and_a_given_value_wins(self):
        """TC-WFM-145: view.extract_claims has the default `guide` (a long text in the template); run as a stage without a `guide` it renders the template with that default, with a
        `guide` given it renders the given one. rule.speech.no_bold has the default rules ["speech.no_bold"]: run on "**Hello** and *emphasis* here" it removes only the bold markup
        (the function alone, without the default, removes both); with `rules` given the given rules apply."""
        view = self.nodes["view.extract_claims"]
        text = "Paris is the capital of France."
        ops.register_model("light", RecordingModel(ScriptedModel([json.dumps({"claims": []}), json.dumps({"claims": []})]), self.recording))
        self.ok(lambda: self.box.run_stage("view.extract_claims", {"text": text, "model": LIGHT}, {}, {}), "view.extract_claims default")
        self.ok(lambda: self.box.run_stage("view.extract_claims", {"text": text, "guide": "my guide", "model": LIGHT}, {}, {}), "view.extract_claims override")
        calls = self.recording.model_calls()
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["messages"][-1]["content"], render(view["body"]["template"], {"text": text, "guide": view["params"]["guide"]["default"]}))
        self.assertEqual(calls[1]["messages"][-1]["content"], render(view["body"]["template"], {"text": text, "guide": "my guide"}))
        apply_rules = ops.FUNCTIONS["apply_rules"]
        said = "**Hello** and *emphasis* here"
        self.assertEqual(self.ok(lambda: self.box.run("rule.speech.no_bold", {"text": said}), "rule default"), apply_rules(said, rules=["speech.no_bold"], repair=True))
        both = ["speech.no_bold", "speech.no_emphasis"]
        self.assertEqual(self.ok(lambda: self.box.run("rule.speech.no_bold", {"text": said, "rules": both}), "rule override"), apply_rules(said, rules=both, repair=True))
        self.assertNotEqual(apply_rules(said, rules=["speech.no_bold"], repair=True), apply_rules(said), "the default makes no difference in this example")

    @mark.req("REQ-WFM-058")
    def test_the_binder_adds_the_model_and_tool_descriptors_and_changes_replace_options(self):
        """TC-WFM-146: verify.single@1 (a model step `judge`, a code step `count`) bound to a skill with model {profile light, options {num_ctx 4096}} gets the data node
        `descriptor.model` with {"model": "light", "options": {"num_ctx": 4096}} and one edge {"as": "model"} into step.judge, none into step.count; the input graph is unchanged and the
        bound one keeps the rules and the order. changes {"model": {"options": {"temperature": 0.2}}} give options {"temperature": 0.2} (replaced, the profile stays). A pipeline with a
        tool step gets `descriptor.tool.web_search` {"tool": "web_search", "settings": {}} and an edge {"as": "tool"} into it and no model node."""
        found = pipeline_graph.convert(pipeline_of("verify.single", 1), self.nodes, 300)
        graph = found["graph"]
        before = copy.deepcopy(graph)
        bound = self.ok(lambda: pipeline_graph.bind_skill(graph, self.nodes, SKILL), "bind_skill")
        self.assertIsNotNone(bound, "bind_skill gave no graph")
        self.assertEqual(graph, before, "bind_skill changed its input graph")
        nodes = {n["id"]: n["data"] for n in bound["nodes"]}
        self.assertEqual(nodes["descriptor.model"]["value"], {"model": "light", "options": {"num_ctx": 4096}})
        edges = edges_of(bound)
        self.assertEqual(edges[("descriptor.model", "step.judge")], {"as": "model"})
        self.assertNotIn(("descriptor.model", "step.count"), edges)
        self.assertEqual(check_graph(bound), [])
        transforms = lambda g: [i for i in order_of(g) if i.startswith("step.")]      # noqa: E731
        self.assertEqual(transforms(bound), transforms(graph))
        changed = pipeline_graph.bind_skill(graph, self.nodes, SKILL, {"model": {"options": {"temperature": 0.2}}})
        self.assertEqual({n["id"]: n["data"] for n in changed["nodes"]}["descriptor.model"]["value"], {"model": "light", "options": {"temperature": 0.2}})
        tool_pipeline = {"id": "t.tool", "version": 1, "result": "hits", "nodes": [{"id": "s", "use": "tool.web_search@1", "wire": {"query": "$input.q"}, "output": "hits"}]}
        tool_graph = pipeline_graph.bind_skill(pipeline_graph.convert(tool_pipeline, self.nodes, 300)["graph"], self.nodes, SKILL)
        tool_nodes = {n["id"]: n["data"] for n in tool_graph["nodes"]}
        self.assertEqual(tool_nodes["descriptor.tool.web_search"]["value"], {"tool": "web_search", "settings": {}})
        self.assertEqual(edges_of(tool_graph)[("descriptor.tool.web_search", "step.s")], {"as": "tool"})
        self.assertNotIn("descriptor.model", tool_nodes)

    def converted_plan(self):
        skill = skill_store.load_skill(os.path.join(REPO, "skills", "plan_question.md"))
        pipeline = pipeline_of("plan.free", 1)
        graph = pipeline_graph.convert(pipeline, self.nodes, skill["budget"]["seconds"])["graph"]
        bound = pipeline_graph.bind_skill(graph, self.nodes, skill)
        self.assertIsNotNone(bound, "bind_skill gave no graph")
        return skill, bound

    @mark.req("REQ-WFM-058")
    def test_a_converted_graph_runs_on_the_toolbox_with_a_scripted_model(self):
        """TC-WFM-147: plan.free@1 of the skill plan_question, converted, bound and handed to GraphRunner with `stages_from_toolbox`, runs with a scripted registered model: status
        done, one model call whose user message is the template rendered with the question, and the result node var.plan holds what normalize_plan gives for the parsed reply."""
        skill, bound = self.converted_plan()
        view = self.nodes["view.research_plan"]
        question = "When did the Rivertown Bridge open to traffic?"
        reply = json.loads(schema_reply(view["body"]["schema"]))
        ops.register_model("light", RecordingModel(ScriptedModel([json.dumps(reply)]), self.recording))
        nodes, trust = self.ok(lambda: skill_converter.stages_from_toolbox(bound, self.box), "stages_from_toolbox")
        result = GraphRunner(trust).run(bound, nodes, {"input.question": question})
        self.assertEqual(result.status, "done")
        calls = self.recording.model_calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["messages"][-1]["content"], render(view["body"]["template"], {"question": question}))
        self.assertEqual(calls[0]["profile"], skill["model"]["profile"])
        self.assertEqual(result.values["var.plan"], ops.FUNCTIONS["normalize_plan"](plan=reply, question=question))

    @mark.req("REQ-WFM-058")
    def test_an_untrusted_entry_refuses_the_run_before_any_node_ran(self):
        """TC-WFM-148: with the toolbox entry code.normalize_plan untrusted, the run of the converted graph is refused naming step.norm before the model was asked; trusted again, the
        same graph runs to done."""
        skill, bound = self.converted_plan()
        view = self.nodes["view.research_plan"]
        ops.register_model("light", RecordingModel(ScriptedModel([schema_reply(view["body"]["schema"])] * 2), self.recording))
        nodes, trust = self.ok(lambda: skill_converter.stages_from_toolbox(bound, self.box), "stages_from_toolbox")
        self.box.set_trust("code.normalize_plan", "untrusted", "anna")
        refused = GraphRunner(trust).run(bound, nodes, {"input.question": "q"})
        self.assertEqual((refused.status, refused.named), ("refused", ["step.norm"]))
        self.assertEqual(self.recording.model_calls(), [])
        self.box.set_trust("code.normalize_plan", "trusted", "anna")
        self.assertEqual(GraphRunner(trust).run(bound, nodes, {"input.question": "q"}).status, "done")


if __name__ == "__main__":
    unittest.main()
