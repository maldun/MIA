"""
Acceptance tests of the common operations and the thin toolbox entries (G-V2.CONVERT, task T-CV-03b, A-123 P1b, D-246): TC-WFM-116 to TC-WFM-120, preconditions of
REQ-WFM-058 (the converted skill runs its stages as transforms of the toolbox). RED until T-CV-03b: `common_operations.py` is a stub and `seed_shipped` stores shipped
nodes without code text.
What they fix: the functions the shipped library nodes name live once in `common_operations`; every shipped transform runs from the toolbox (`Toolbox.run`) and gives
what the old runner's function gives; model views and tools get the model and the tools through `common_operations.use(...)`, not through arguments. No model, no network.
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
SETTINGS = {"profile": "light", "options": {"temperature": 0}}


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
        self.library = TransformLibraryMock()
        self.box = Toolbox(self.library, lambda account: True, EventRecord())
        self.box.seed_shipped(NODES)
        self.nodes = latest_nodes()

    def run_ok(self, tid, args):
        """the result of the transform, or a failure that names the error (a stub or a missing entry must not look like an error of the test)"""
        try:
            return self.box.run(tid, args)
        except (ToolboxError, KeyError, NameError, ImportError, TypeError) as error:
            self.fail("%s does not run from the toolbox: %s %s" % (tid, type(error).__name__, error))

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
        """TC-WFM-118: after seeding, every shipped entry of kind code, model, tool or script holds code text that defines run(args); an entry whose function is in the
        common module is at most 12 lines (it calls the module, it does not hold the function)."""
        empty, long_entries = [], []
        for tid, node in sorted(self.nodes.items()):
            if node.get("kind") not in ("code", "model", "tool", "script"):
                continue
            code = self.library.read("transforms", tid)["doc"].get("code") or ""
            if "def run" not in code:
                empty.append(tid)
            elif node.get("kind") == "code" and node["body"]["function"] in ops.FUNCTIONS and len(code.strip().splitlines()) > 12:
                long_entries.append(tid)
        self.assertEqual(empty, [], "shipped entries without a run function (no code text)")
        self.assertEqual(long_entries, [], "entries of common functions that are not thin")

    @mark.req("REQ-WFM-058")
    def test_a_model_view_makes_the_one_call_the_old_runner_makes(self):
        """TC-WFM-119: view.verdict run through the toolbox inside common_operations.use(model, settings) asks the model once, with the messages of the old runner (system
        text rendered not strict, user text = the template rendered strict), the schema of the node and the settings of the skill, and returns the parsed reply."""
        node = self.nodes["view.verdict"]
        args = {"claim": "The Rivertown Bridge opened in 2021.", "evidence": "It opened on 3 May 2021.", "context": "a careful reader"}
        reply = {"verdict": "supported", "reason": "the evidence says so", "confidence": 0.9}
        recording = Recording()
        model = RecordingModel(ScriptedModel([json.dumps(reply)]), recording)
        with ops.use(model=model, settings=SETTINGS):
            result = self.run_ok("view.verdict", args)
        calls = recording.model_calls()
        self.assertEqual(len(calls), 1, "a model view makes exactly one call when the reply fits")
        expected = [{"role": "system", "content": render(node["body"]["system"], args, strict=False)}, {"role": "user", "content": render(node["body"]["template"], args)}]
        self.assertEqual(calls[0]["messages"], expected)
        self.assertEqual(calls[0]["schema"], node["body"]["schema"])
        self.assertEqual((calls[0]["profile"], calls[0]["options"]), ("light", {"temperature": 0}))
        self.assertEqual(result, reply)

    @mark.req("REQ-WFM-058")
    def test_a_tool_transform_calls_the_handed_tool_and_refuses_without_one(self):
        """TC-WFM-120: tool.web_search inside common_operations.use(tools={...}) calls that function with the args as keywords and returns its result; without a handed tool
        the run is refused with ToolMissing (the toolbox does not search the web by itself)."""
        seen = []

        def web_search(query):
            seen.append(query)
            return [{"url": "https://a.example/1", "title": "A"}]

        with ops.use(tools={"web_search": web_search}):
            result = self.run_ok("tool.web_search", {"query": "rivertown bridge"})
        self.assertEqual((seen, result), (["rivertown bridge"], [{"url": "https://a.example/1", "title": "A"}]))
        with self.assertRaises(ops.ToolMissing):
            self.box.run("tool.web_search", {"query": "rivertown bridge"})


if __name__ == "__main__":
    unittest.main()
