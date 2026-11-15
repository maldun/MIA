"""
Acceptance tests of the common operations and the thin toolbox entries (G-V2.CONVERT, task T-CV-03b, A-123 P1b, D-246, revised by D-248): TC-WFM-116 to TC-WFM-121,
preconditions of REQ-WFM-058 (the converted skill runs its stages as transforms of the toolbox). RED until T-CV-03b: `common_operations.py` is a stub and `seed_shipped`
stores shipped nodes without code text.
What they fix: the functions the shipped library nodes name live once in `common_operations`; every shipped transform runs from the toolbox and gives what the old runner's
function gives; a tool or the model reaches a transform as a JSON descriptor in an input node ({"tool": ...}, {"model": ...}, D-248) and is resolved only against what MIA
registered. A plain entry defines run(args); an entry that needs outputs or settings defines stage(inputs, outputs, node), which `Toolbox.run_stage` calls (the Stage call
of the graph runner, A-124). No model, no network.
Run with: python tests/acceptance/test_common_operations.py
"""
import glob
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
for path in (REPO, os.path.join(REPO, "tests", "helpers"), os.path.join(REPO, "tests", "helpers", "mocks")):
    sys.path.insert(0, path)

from markers import mark                                           # noqa: E402
from if_203_transforms import TransformLibraryMock                 # noqa: E402
from toolbox_fakes import EventRecord                              # noqa: E402
from call_recording import Recording, RecordingModel, ScriptedModel   # noqa: E402
import common_operations as ops                                    # noqa: E402
import extraction                                                  # noqa: E402
import verification                                                # noqa: E402
import research                                                    # noqa: E402
from pipeline import render                                        # noqa: E402
from toolbox import Toolbox, ToolboxError                          # noqa: E402

NODES = os.path.join(REPO, "library", "nodes")
LIGHT = {"model": "light", "options": {"temperature": 0}}


def latest_nodes():
    """{id: node} of the highest version of every shipped node that is not retired (the rule of Toolbox.seed_shipped)"""
    latest = {}
    for path in sorted(glob.glob(os.path.join(NODES, "*", "*.json"))):
        with open(path, encoding="utf-8") as handle:
            node = json.load(handle)
        if node.get("status") != "retired" and node["version"] > latest.get(node["id"], {"version": 0})["version"]:
            latest[node["id"]] = node
    return latest


class CommonOperations(unittest.TestCase):
    def setUp(self):
        ops.reset()
        self.addCleanup(ops.reset)
        self.library = TransformLibraryMock()
        self.box = Toolbox(self.library, lambda account: True, EventRecord())
        self.box.seed_shipped(NODES)
        self.nodes = latest_nodes()

    def ok(self, call, what):
        """the result of the call, or a failure that names the error (a stub or a missing entry must not look like an error of the test)"""
        try:
            return call()
        except (ToolboxError, KeyError, NameError, ImportError, TypeError, AttributeError) as error:
            self.fail("%s does not run from the toolbox: %s %s" % (what, type(error).__name__, error))

    def run_ok(self, tid, args):
        return self.ok(lambda: self.box.run(tid, args), tid)

    def stage_ok(self, tid, inputs, outputs=None, node=None):
        return self.ok(lambda: self.box.run_stage(tid, inputs, outputs or {}, node or {}), tid)

    @mark.req("REQ-WFM-058")
    def test_every_function_a_shipped_code_node_names_is_in_the_common_module_once(self):
        """TC-WFM-116: for every shipped node of kind code, the function its body names is in common_operations.FUNCTIONS and callable; a function of the old registries
        of research, extraction and verification is the same object in the module (it exists once, nothing is copied)."""
        named = sorted({n["body"]["function"] for n in self.nodes.values() if n.get("kind") == "code"})
        self.assertGreater(len(named), 30, "the shipped code nodes name fewer functions than expected: the test reads the wrong folder")
        missing = [f for f in named if not callable(ops.FUNCTIONS.get(f))]
        self.assertEqual(missing, [], "functions named by shipped nodes but not in common_operations.FUNCTIONS")
        old = {**extraction.FUNCTIONS, **verification.FUNCTIONS, **research.FUNCTIONS}
        shared = [f for f in old if f in ops.FUNCTIONS]
        self.assertTrue(shared, "none of the old functions of research, extraction and verification is in the common module")
        self.assertEqual([f for f in shared if ops.FUNCTIONS[f] is not old[f]], [], "a function exists twice: the module holds another object than the old registry")

    @mark.req("REQ-WFM-058")
    def test_a_shipped_code_transform_gives_what_the_old_function_gives(self):
        """TC-WFM-117: top_urls, tally and tidy_claims, each run through Toolbox.run(<node id>, args), give exactly the value of the old function on the same input."""
        hits = [{"url": "https://a.example/1"}, {"url": "https://b.example/2"}, {"url": "https://a.example/1"}, {"url": "https://c.example/3"}]
        votes = [{"verdict": "supported", "reason": "a", "confidence": 0.9}, {"verdict": "refuted", "reason": "b"}, {"verdict": "supported", "reason": "c"}]
        text = "Paris is the capital of France. It has 2 million people."
        claims = [{"kind": "fact", "text": "Paris is the capital of France"}, {"kind": "numeric", "text": "2 million"}]
        for tid, old, args in (("code.top_urls", research.top_urls, {"hits": hits, "n": 2}),
                               ("code.tally", verification.tally, {"verdicts": votes}),
                               ("code.tidy_claims", extraction.tidy_claims, {"text": text, "claims": claims})):
            with self.subTest(transform=tid):
                self.assertEqual(self.run_ok(tid, dict(args)), old(**args))

    @mark.req("REQ-WFM-058")
    def test_the_entries_of_common_functions_are_thin_and_every_shipped_entry_has_code(self):
        """TC-WFM-118: after seeding, every shipped entry of kind code, model, tool or script holds code text that defines run(args) or stage(inputs, outputs, node); an
        entry whose function is in the common module is at most 12 lines (it calls the module, it does not hold the function)."""
        empty, long_entries = [], []
        for tid, node in sorted(self.nodes.items()):
            if node.get("kind") not in ("code", "model", "tool", "script"):
                continue
            code = self.library.read("transforms", tid)["doc"].get("code") or ""
            if "def run(" not in code and "def stage(" not in code:
                empty.append(tid)
            elif node.get("kind") == "code" and node["body"]["function"] in ops.FUNCTIONS and len(code.strip().splitlines()) > 12:
                long_entries.append(tid)
        self.assertEqual(empty, [], "shipped entries without a run or stage function (no code text)")
        self.assertEqual(long_entries, [], "entries of common functions that are not thin")

    @mark.req("REQ-WFM-058")
    def test_a_model_view_gets_its_model_as_a_descriptor_and_makes_the_one_call_the_old_runner_makes(self):
        """TC-WFM-119: view.verdict run as a stage with the model as an input descriptor {"model": "light", "options": {...}} asks the registered model once, with the
        messages of the old runner (system text rendered not strict, user text = the template rendered strict), the schema of the node, the profile and options of the
        descriptor, and returns the parsed reply. The descriptor is not an argument of the template."""
        node = self.nodes["view.verdict"]
        args = {"claim": "The Rivertown Bridge opened in 2021.", "evidence": "It opened on 3 May 2021.", "context": "a careful reader"}
        reply = {"verdict": "supported", "reason": "the evidence says so", "confidence": 0.9}
        recording = Recording()
        ops.register_model("light", RecordingModel(ScriptedModel([json.dumps(reply)]), recording))
        result = self.stage_ok("view.verdict", {**args, "model": LIGHT})
        calls = recording.model_calls()
        self.assertEqual(len(calls), 1, "a model view makes exactly one call when the reply fits")
        expected = [{"role": "system", "content": render(node["body"]["system"], args, strict=False)}, {"role": "user", "content": render(node["body"]["template"], args)}]
        self.assertEqual(calls[0]["messages"], expected)
        self.assertEqual(calls[0]["schema"], node["body"]["schema"])
        self.assertEqual((calls[0]["profile"], calls[0]["options"]), ("light", {"temperature": 0}))
        self.assertEqual(result, reply)

    @mark.req("REQ-WFM-058")
    def test_a_tool_transform_calls_the_registered_tool_named_by_its_descriptor(self):
        """TC-WFM-120: tool.web_search run as a stage with the input descriptor {"tool": "web_search", "settings": {...}} calls the registered function with the other
        inputs as keywords and the declared settings applied, and returns its result; without a descriptor input the stage is refused with ToolMissing."""
        seen = []

        def web_search(query, max_results=10):
            seen.append((query, max_results))
            return [{"url": "https://a.example/1", "title": "A"}]

        ops.register_tool("web_search", web_search, settings=("max_results",))
        result = self.stage_ok("tool.web_search", {"query": "rivertown bridge", "tool": {"tool": "web_search", "settings": {"max_results": 3}}})
        self.assertEqual((seen, result), ([("rivertown bridge", 3)], [{"url": "https://a.example/1", "title": "A"}]))
        with self.assertRaises(ops.ToolMissing):
            self.box.run_stage("tool.web_search", {"query": "rivertown bridge"}, {}, {})

    @mark.req("REQ-WFM-058")
    def test_a_descriptor_resolves_only_against_what_mia_registered(self):
        """TC-WFM-121 (D-248 D): an unknown tool name is refused with ToolMissing, a setting the tool did not declare with DescriptorRefused, an unknown model profile with
        ModelMissing, each before anything is called; the same descriptors with a registered name and a declared setting resolve."""
        calls = []
        ops.register_tool("web_search", lambda query, max_results=10: calls.append(query), settings=("max_results",))
        ops.register_model("light", ScriptedModel([]))
        with self.assertRaises(ops.ToolMissing):
            ops.resolve_tool({"tool": "shell", "settings": {}})
        with self.assertRaises(ops.DescriptorRefused) as undeclared:
            ops.resolve_tool({"tool": "web_search", "settings": {"timeout": 1}})
        self.assertNotIsInstance(undeclared.exception, ops.ToolMissing)
        with self.assertRaises(ops.ModelMissing):
            ops.resolve_model({"model": "full", "options": {}})
        self.assertEqual(calls, [])
        self.assertTrue(callable(ops.resolve_tool({"tool": "web_search", "settings": {"max_results": 3}})))
        chat, profile, options = ops.resolve_model(LIGHT)
        self.assertEqual((profile, options), ("light", {"temperature": 0}))
        self.assertTrue(hasattr(chat, "chat"))


if __name__ == "__main__":
    unittest.main()
