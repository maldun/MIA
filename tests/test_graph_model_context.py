"""Context graphs on the save and read path of the Workflow management (G-V4.GRAPHSTORE.CORE T-04): the kind selects the tables, identity and
ends only, the kind on reading. Files backend in a fresh folder per test. Run with: python tests/test_graph_model_context.py"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                                            # noqa: E402
from graph_model_fakes import data_node, make_edge, make_graph, transform_node     # noqa: E402
from graph_model import GraphModel                                                  # noqa: E402
from storage import Storage                                                         # noqa: E402
from storage_files import FileBackend                                               # noqa: E402

TABLES = ("graph_nodes", "graph_edges", "context_nodes", "context_edges", "graphs")


def step(local_id, category="claim", **fields):
    return {"id": local_id, "data": dict({"type": category}, **fields)}


def link(edge_id, start, end):
    return {"id": edge_id, "from": start, "to": end, "data": {}}


def context(graph_id, nodes, edges, description="d"):
    return {"id": graph_id, "kind": "context", "context_graph_id": "", "testbench_id": "", "description": description, "nodes": nodes, "edges": edges}


def workflow(graph_id):
    return make_graph(graph_id, [data_node("D1"), transform_node("T1"), data_node("D2")], [make_edge("D1", "T1"), make_edge("T1", "D2")])


class ContextGraphs(unittest.TestCase):
    def setUp(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        self.storage = Storage(FileBackend(folder))
        self.model = GraphModel(self.storage, "anna")

    def counts(self):
        return {t: sum(len(self.storage.history(t, i)) for i in self.storage.ids(t)) for t in TABLES}

    @mark.req("REQ-WFM-152")
    def test_a_context_graph_is_stored_in_the_context_tables(self):
        """Steps and connections of a context graph go to context_nodes and context_edges under scoped IDs; the header has the kind context.

        Example: c with steps a, b and connection e1 -> context_nodes c/a, c/b; context_edges c/e1; graph_nodes empty; header kind context.
        """
        # When
        result = self.model.save_graph(context("c", [step("a"), step("b")], [link("e1", "a", "b")]))
        # Then
        self.assertEqual((result.saved, result.version), (True, 1))
        self.assertEqual((self.storage.ids("context_nodes"), self.storage.ids("context_edges"), self.storage.ids("graph_nodes")), (["c/a", "c/b"], ["c/e1"], []))
        self.assertEqual(self.storage.get("graphs", "c")["doc"]["data"]["kind"], "context")

    @mark.req("REQ-WFM-153", "REQ-WFM-157")
    def test_a_graph_without_a_kind_is_a_workflow_graph_and_reads_back_without_one(self):
        """No kind means workflow: the header says workflow, the graph read back keeps its shape without a kind.

        Example: workflow w saved without kind -> header kind workflow; read_graph("w") has no key kind.
        """
        # When
        self.model.save_graph(workflow("w"))
        # Then
        self.assertEqual(self.storage.get("graphs", "w")["doc"]["data"]["kind"], "workflow")
        self.assertNotIn("kind", self.model.read_graph("w"))

    @mark.req("REQ-WFM-154")
    def test_an_unknown_kind_is_refused_naming_kind(self):
        """A kind that is neither workflow nor context is schema_break naming kind, and nothing is stored; also a kind that is no text.

        Example: kind swarm -> (False, schema_break, kind); no table holds a record.
        """
        for kind in ("swarm", "", 3, None, ["context"]):
            with self.subTest(kind=kind):
                # Given
                graph = dict(workflow("w"), kind=kind)
                # When
                result = self.model.save_graph(graph)
                # Then
                self.assertEqual((result.saved, result.rule, result.detail), (False, "schema_break", "kind"))
                self.assertEqual(self.counts(), {t: 0 for t in TABLES})

    @mark.req("REQ-WFM-155")
    def test_identity_and_ends_are_checked_and_named(self):
        """A repeated step, a repeated connection and a connection to a missing step are refused naming the IDs; nothing is written.

        Example: step a twice -> named ["a"]; connection e1 twice -> ["e1"]; e1 to ghost -> ["e1"].
        """
        cases = [("step twice", [step("a"), step("a")], [], ["a"]),
                 ("connection twice", [step("a"), step("b")], [link("e1", "a", "b"), link("e1", "b", "a")], ["e1"]),
                 ("missing end", [step("a")], [link("e1", "a", "ghost")], ["e1"])]
        for name, nodes, edges, named in cases:
            with self.subTest(name):
                # When
                result = self.model.save_graph(context("c", nodes, edges))
                # Then
                self.assertEqual((result.saved, result.named), (False, named))
                self.assertEqual(self.counts(), {t: 0 for t in TABLES})

    @mark.req("REQ-WFM-156")
    def test_the_workflow_rules_do_not_apply(self):
        """Two connected steps of one category in a cycle are accepted: no order, alternation, writer or stop rule for a context graph.

        Example: a -> b -> a, both claim -> (True, 1, []).
        """
        # When
        result = self.model.save_graph(context("c", [step("a"), step("b")], [link("e1", "a", "b"), link("e2", "b", "a")]))
        # Then
        self.assertEqual((result.saved, result.version, result.named), (True, 1, []))

    @mark.req("REQ-WFM-157", "REQ-WFM-159", "REQ-WFM-145")
    def test_a_context_graph_reads_back_with_its_kind_and_history(self):
        """Each version reads back as saved, with the kind context; a step's history lists its pinned versions.

        Example: c saved with a.text x, then y -> version 1 has x, version 2 has y, both kind context; history of a: [1, 2].
        """
        # Given
        saved = [context("c", [step("a", text=t), step("b")], [link("e1", "a", "b")], description=t) for t in ("x", "y")]
        for graph in saved:
            self.model.save_graph(graph)
        # When / Then
        for version, graph in enumerate(saved, start=1):
            with self.subTest(version=version):
                self.assertEqual(self.model.read_graph("c", version), graph)
        self.assertEqual([v["version"] for v in self.model.step_history("c", "a")], [1, 2])
        self.assertEqual([v["version"] for v in self.model.step_history("c", "e1")], [1])

    @mark.req("REQ-WFM-161")
    def test_an_empty_context_graph_is_one_header_version(self):
        """A context graph without steps and connections is stored as one header and no member record.

        Example: empty context graph e -> (True, 1); graphs holds one version, the four member tables none.
        """
        # When
        result = self.model.save_graph(context("e", [], []))
        # Then
        self.assertEqual((result.saved, result.version), (True, 1))
        self.assertEqual(self.counts(), {"graph_nodes": 0, "graph_edges": 0, "context_nodes": 0, "context_edges": 0, "graphs": 1})


if __name__ == "__main__":
    unittest.main()
