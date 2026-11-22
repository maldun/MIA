"""The read path of the Workflow management on the real Storage layer (G-V4.GRAPHSTORE.CORE T-03): local IDs, a version as saved, the versions
of a graph, the history of a step in its graph. Files backend in a fresh folder per test. Run with: python tests/test_graph_model_read.py"""
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


class Interrupted(Exception):
    pass


class StopBeforeHeader:
    """The Storage layer, interrupted at the first write of a header: the members of that save stay as unused versions."""

    def __init__(self, storage):
        self.storage = storage

    def put(self, table, record_id, doc, author=None):
        if table == "graphs":
            raise Interrupted(record_id)
        return self.storage.put(table, record_id, doc, author)

    def __getattr__(self, name):
        return getattr(self.storage, name)


def chain(graph_id, toolbox_id="t1", description="d"):
    return make_graph(graph_id, [data_node("D1"), transform_node("step.write", toolbox_id), data_node("a/b")],
                      [make_edge("D1", "step.write"), make_edge("step.write", "a/b")], description=description)


class ReadPath(unittest.TestCase):
    def setUp(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        self.storage = Storage(FileBackend(folder))

    def model(self, author="anna", tables=None):
        return GraphModel(tables or self.storage, author)

    @mark.req("REQ-WFM-144")
    def test_a_graph_reads_back_with_its_local_ids(self):
        """Steps, connections and their ends come back without the graph ID; a local ID with a slash keeps it (split at the first slash).

        Example: graph g with step a/b is stored as g/a/b and read back as a/b; connection step.write>a/b ends at a/b.
        """
        # Given
        graph = chain("g")
        self.model().save_graph(graph)
        # When
        read = self.model().read_graph("g")
        # Then
        self.assertEqual(read, graph)
        self.assertIn("g/a/b", self.storage.ids("graph_nodes"))

    @mark.req("REQ-WFM-159")
    def test_each_version_reads_back_as_it_was_saved(self):
        """Reading at a version gives that version's steps, connections and header fields.

        Example: three saves with toolboxes t1, t2, t3 -> version 2 reads back with t2 and description "v2".
        """
        # Given
        saved = [chain("g", toolbox_id="t%d" % i, description="v%d" % i) for i in (1, 2, 3)]
        for graph in saved:
            self.model().save_graph(graph)
        # When / Then
        for version, graph in enumerate(saved, start=1):
            with self.subTest(version=version):
                self.assertEqual(self.model().read_graph("g", version), graph)

    @mark.req("REQ-WFM-158")
    def test_the_versions_of_a_graph_name_account_and_time(self):
        """Every version of a graph, oldest first, with the account that saved it and a time.

        Example: saved by anna, ben, cleo -> versions [1, 2, 3] with authors [anna, ben, cleo].
        """
        # Given
        for i, author in enumerate(("anna", "ben", "cleo"), start=1):
            self.model(author).save_graph(chain("g", toolbox_id="t%d" % i))
        # When
        versions = self.model().graph_versions("g")
        # Then
        self.assertEqual([(v["version"], v["author"]) for v in versions], [(1, "anna"), (2, "ben"), (3, "cleo")])
        self.assertTrue(all(v["time"] for v in versions))

    @mark.req("REQ-WFM-145")
    def test_a_steps_history_lists_only_what_its_graphs_headers_pin(self):
        """The history of a step lists the versions its graph's headers pin: not another graph's step with the same local ID, not an unused version.

        Example: step.write of g changed once by ben -> history [1 anna, 2 ben]; step.write of h -> [1]; an interrupted save's version 3 is not listed.
        """
        # Given: two graphs with the step step.write; g changes it once; a save of g interrupted before its header leaves g/step.write version 3 unused
        self.model("anna").save_graph(chain("g"))
        self.model("anna").save_graph(chain("h"))
        self.model("ben").save_graph(chain("g", toolbox_id="t2"))
        with self.assertRaises(Interrupted):
            self.model("cleo", StopBeforeHeader(self.storage)).save_graph(chain("g", toolbox_id="t3"))
        self.assertEqual(len(self.storage.history("graph_nodes", "g/step.write")), 3)
        # When
        in_g = self.model().step_history("g", "step.write")
        in_h = self.model().step_history("h", "step.write")
        # Then
        self.assertEqual([(v["version"], v["author"]) for v in in_g], [(1, "anna"), (2, "ben")])
        self.assertEqual([v["version"] for v in in_h], [1])
        self.assertTrue(all(v["time"] for v in in_g + in_h))

    @mark.req("REQ-WFM-145")
    def test_a_connection_has_a_history_too(self):
        """A connection's history is read like a step's.

        Example: connection D1>step.write of g, never changed -> history [1].
        """
        # Given
        self.model().save_graph(chain("g"))
        self.model().save_graph(chain("g", toolbox_id="t2"))
        # When / Then
        self.assertEqual([v["version"] for v in self.model().step_history("g", "D1>step.write")], [1])


if __name__ == "__main__":
    unittest.main()
