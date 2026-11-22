"""The save path of the Workflow management on the real Storage layer (G-V4.GRAPHSTORE.CORE T-02): scoped step IDs, checked first, header last,
changed members only. Files backend in a fresh folder per test. Run with: python tests/test_graph_model_save.py"""
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

TABLES = ("graph_nodes", "graph_edges", "graphs")


class Interrupted(Exception):
    pass


class WatchedTables:
    """The Storage layer, with the order of its writes recorded and an optional interruption before write number `stop_at` (counted from 1)."""

    def __init__(self, storage, stop_at=None):
        self.storage, self.stop_at, self.writes = storage, stop_at, []

    def put(self, table, record_id, doc, author=None):
        if self.stop_at is not None and len(self.writes) + 1 == self.stop_at:
            raise Interrupted(record_id)
        self.writes.append((table, record_id))
        return self.storage.put(table, record_id, doc, author)

    def __getattr__(self, name):
        return getattr(self.storage, name)


def chain(graph_id, toolbox_id="t1"):
    return make_graph(graph_id, [data_node("D1"), transform_node("T1", toolbox_id), data_node("D2")], [make_edge("D1", "T1"), make_edge("T1", "D2")])


class SavePath(unittest.TestCase):
    def setUp(self):
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        self.storage = Storage(FileBackend(folder))
        self.model = GraphModel(self.storage, "anna")

    def counts(self):
        return {t: sum(len(self.storage.history(t, i)) for i in self.storage.ids(t)) for t in TABLES}

    @mark.req("REQ-WFM-144")
    def test_steps_and_connections_are_stored_under_scoped_ids(self):
        """A saved graph's records are named `<graph id>/<local id>`; the ends of a connection too.

        Example: graph g with step D1 -> record g/D1; connection D1>T1 -> record g/D1>T1 from g/D1 to g/T1.
        """
        # Given / When
        result = self.model.save_graph(chain("g"))
        # Then
        self.assertEqual((result.saved, result.version), (True, 1))
        self.assertEqual(sorted(self.storage.ids("graph_nodes")), ["g/D1", "g/D2", "g/T1"])
        edge = self.storage.get("graph_edges", "g/D1>T1")["doc"]
        self.assertEqual((edge["id"], edge["from"], edge["to"]), ("g/D1>T1", "g/D1", "g/T1"))

    @mark.req("REQ-WFM-146", "REQ-WFM-150")
    def test_a_broken_last_connection_writes_nothing(self):
        """Every record is checked before the first write; a refusal names the rule and nothing is stored.

        Example: the last connection's data is not an object -> refused (schema_break, data); no table holds a record.
        """
        # Given: a graph whose last connection breaks the record rules
        graph = chain("g")
        graph["edges"][-1]["data"] = "x"
        # When
        result = self.model.save_graph(graph)
        # Then
        self.assertEqual((result.saved, result.rule, result.detail), (False, "schema_break", "data"))
        self.assertEqual(self.counts(), {t: 0 for t in TABLES})

    @mark.req("REQ-WFM-160")
    def test_a_graph_id_with_a_slash_is_refused(self):
        """A graph with steps under an ID with a slash is refused as unscoped_id naming a record ID; nothing is stored.

        Example: graph look/up with step D1 -> unscoped_id naming look/up/D1.
        """
        for graph_id, detail in (("look/up", "look/up/D1"), ("/lookup", "/lookup/D1")):
            with self.subTest(graph_id=graph_id):
                # When
                result = self.model.save_graph(chain(graph_id))
                # Then
                self.assertEqual((result.saved, result.rule, result.detail), (False, "unscoped_id", detail))
                self.assertEqual(self.counts(), {t: 0 for t in TABLES})

    @mark.req("REQ-WFM-147")
    def test_the_header_is_written_last(self):
        """Steps and connections are written before the header.

        Example: the writes of a new three-step graph end with ("graphs", "g").
        """
        # Given
        tables = WatchedTables(self.storage)
        # When
        GraphModel(tables, "anna").save_graph(chain("g"))
        # Then
        self.assertEqual(tables.writes[-1], ("graphs", "g"))
        self.assertNotIn("graphs", [t for t, _ in tables.writes[:-1]])

    @mark.req("REQ-WFM-149")
    def test_an_unchanged_graph_writes_nothing_and_answers_its_version(self):
        """Saving the newest version again writes no record and answers that version.

        Example: chain g saved twice -> (True, 1) both times; the record counts do not grow.
        """
        # Given
        self.model.save_graph(chain("g"))
        before = self.counts()
        # When
        again = self.model.save_graph(chain("g"))
        # Then
        self.assertEqual((again.saved, again.version), (True, 1))
        self.assertEqual(self.counts(), before)

    @mark.req("REQ-WFM-148")
    def test_one_changed_step_writes_one_step_version_and_one_header_version(self):
        """Only members that differ from their newest version get a new version.

        Example: T1's toolbox changed -> g/T1 at version 2, every other member at 1, header at 2.
        """
        # Given
        self.model.save_graph(chain("g"))
        before = self.counts()
        # When
        changed = self.model.save_graph(chain("g", toolbox_id="t2"))
        # Then
        self.assertEqual((changed.saved, changed.version), (True, 2))
        after = self.counts()
        self.assertEqual({t: after[t] - before[t] for t in TABLES}, {"graph_nodes": 1, "graph_edges": 0, "graphs": 1})
        pins = {m["id"]: m["version"] for m in self.storage.get("graphs", "g")["doc"]["data"]["nodes"]}
        self.assertEqual(pins, {"g/D1": 1, "g/T1": 2, "g/D2": 1})

    @mark.req("REQ-WFM-151")
    def test_an_interrupted_save_is_finished_by_repeating_it(self):
        """A save interrupted before any of its writes is completed by the same save, with exactly one header version.

        Example: interrupted before write 3 of 6 -> no header; the repeated save -> version 1 with all members.
        """
        for stop_at in range(1, 7):        # 3 steps, 2 connections, 1 header
            with self.subTest(stop_at=stop_at):
                # Given: a fresh store and a save interrupted before write number stop_at
                self.setUp()
                with self.assertRaises(Interrupted):
                    GraphModel(WatchedTables(self.storage, stop_at), "anna").save_graph(chain("g"))
                self.assertEqual(self.storage.ids("graphs"), [])
                # When: the same save is repeated
                result = self.model.save_graph(chain("g"))
                # Then: one header version naming every member
                self.assertEqual((result.saved, result.version), (True, 1))
                header = self.storage.get("graphs", "g")["doc"]["data"]
                self.assertEqual((len(header["nodes"]), len(header["edges"])), (3, 2))


if __name__ == "__main__":
    unittest.main()
