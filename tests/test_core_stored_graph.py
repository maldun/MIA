"""
Unit tests of the stored-graph path of Core (G-V4.GRAPHAPI.RUN T-03, REQ-RUN-042 to 045): the model setting of the stored graph reaches every model call
(finding F-6), a store without the graph or with another storage error, and the text of a refusal.
Run: python tests/test_core_stored_graph.py
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "tests", "helpers"), os.path.join(REPO, "tests", "helpers", "mocks")):
    sys.path.insert(0, path)

from rules_graphs import converted_skill                 # noqa: E402
from run_store import ThrowAwayStore, run_record, stored_run   # noqa: E402
from storage import StorageError                          # noqa: E402
import core                                               # noqa: E402
import run_explain                                        # noqa: E402


def with_temperature(graph, value):
    changed = json.loads(json.dumps(graph))
    next(n for n in changed["nodes"] if n["id"] == "descriptor.model")["data"]["value"]["options"] = {"temperature": value}
    return changed


class StoreCase(unittest.TestCase):
    def setUp(self):
        self.store = ThrowAwayStore()
        self.addCleanup(self.store.close)
        self.runs = tempfile.mkdtemp(prefix="run-log-")
        self.addCleanup(shutil.rmtree, self.runs, True)


class ModelSettingOfTheStoredGraph(StoreCase):
    def test_every_model_call_takes_the_options_of_the_stored_graph(self):
        """F-6: a model call inside a map or loop step takes the options of the stored descriptor.model too, not those of the skill file.

        Example: research with temperature 0.2 stored: all 5 model calls carry temperature 0.2.
        """
        for skill, graph_file in (("research", "research.md"), ("verify_computable", "verify_computable.md")):
            with self.subTest(skill=skill):
                # Given: the skill's converted graph stored with temperature 0.2 in descriptor.model
                store = ThrowAwayStore()
                self.addCleanup(store.close)
                store.save(with_temperature(converted_skill(graph_file), 0.2))
                # When: the skill runs from the store on scripted replies
                result, rec, _ = stored_run(skill, store, self.runs)
                # Then: every model call carries the stored option
                options = [call.get("options") for call in rec.model_calls()]
                self.assertEqual(result.status, "done", result.error)
                self.assertGreater(len(options), 1)
                self.assertEqual([o for o in options if (o or {}).get("temperature") != 0.2], [])


class WhichGraphRuns(StoreCase):
    def test_a_storage_error_other_than_not_found_is_not_hidden(self):
        """REQ-RUN-043 applies only to a graph that is not in the store; a broken store is no reason to run the old way.

        Example: graph_versions raises StorageError("invalid"): the run raises it.
        """
        # Given: a store whose version list fails with another code than not_found
        def broken(graph_id):
            raise StorageError("invalid")
        self.store.model.graph_versions = broken
        # When / Then: the run raises that error
        with self.assertRaises(StorageError):
            stored_run("verify_claim", self.store, self.runs)


class ShownByRunExplain(StoreCase):
    def test_show_names_the_graph_and_version_that_ran(self):
        """REQ-RUN-044 (T-03 demonstrator): `run_explain show` of a run from the store names the graph and its version; a run without one names none.

        Example: "graph verify.single@1, version 2" after two saves.
        """
        # Given: verify.single@1 saved twice; a run from the store and one with an empty store
        graph = converted_skill("verify_claim.md")
        self.store.save(graph)
        self.store.save(dict(graph, description="changed"))
        result, _, ran = stored_run("verify_claim", self.store, self.runs)
        empty = ThrowAwayStore()
        self.addCleanup(empty.close)
        bare, _, other = stored_run("verify_claim", empty, tempfile.mkdtemp(prefix="run-log-"))
        # When: both records are shown
        shown, plain = [], []
        run_explain.cmd_show(run_record(ran, result), shown.append)
        run_explain.cmd_show(run_record(other, bare), plain.append)
        # Then: the first names graph and version, the second has no such line
        self.assertIn("graph verify.single@1, version 2", shown)
        self.assertFalse([line for line in plain if line.startswith("graph verify")])


class RefusalText(unittest.TestCase):
    def test_the_refusal_names_rule_parts_graph_and_version(self):
        """REQ-RUN-045: the error names each broken rule with its parts, the graph ID and the version; a graph that can run gives None.

        Example: an input never given: "the stored graph g@1 version 3 cannot run: unsupplied_input (...)".
        """
        # Given: verify_claim's converted graph
        graph = converted_skill("verify_claim.md")
        # When: it is checked without its inputs, and with them
        refused = core._refusal("verify.single@1", 3, graph, {})
        ready = core._refusal("verify.single@1", 3, graph, {"claim": "x", "evidence": "", "rounds": 3, "experts": []})
        # Then: the refusal names graph and version and a rule with its part; with the inputs there is none
        self.assertTrue(refused.startswith("the stored graph verify.single@1 version 3 cannot run: "), refused)
        self.assertIn("input.claim", refused)
        self.assertIsNone(ready)


if __name__ == "__main__":
    unittest.main()
