"""Adapter test of the skill record and the graph model on the real Storage layer (N-2.3, G-V2.MODEL T-05, TR-MODEL-001 as reworded by A-105).

The scenarios of TC-WFM-040, 041, 042, 044 and 049 of tests/acceptance/test_graph_model.py run twice, on FakeGraphTables and on the real Storage (file backend;
PostgreSQL on a throwaway postgres:16 where podman, the image and psycopg 3 exist). The answers are compared by IDs and version numbers, never by wording
(TR-MODEL-005). A difference that is not an adapter detail is a finding for TR-MODEL-001.
Run with the python that has psycopg:  python tests/test_skill_record_storage.py
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, HERE)

from markers import mark                                                                                    # noqa: E402
from graph_model_fakes import (FakeGraphTables, data_node, make_edge, make_graph, make_skill,               # noqa: E402
                               master_node, transform_node)
from graph_model import GraphModel                                                                          # noqa: E402
from skill_record import SkillCatalog, SkillRecords                                                         # noqa: E402
from storage import Storage, StorageError                                                                   # noqa: E402
from storage_files import FileBackend                                                                       # noqa: E402

AUTHOR = "anna"
HEADER = ("id", "context_graph_id", "testbench_id", "description")


class FakeSide(FakeGraphTables):
    """The fake with the `author` the caller now gives: the fake keeps no authors (adapter detail)."""

    def put(self, table, record_id, doc, author=None):
        return super().put(table, record_id, doc)


class RealGraphTables:
    """GraphModel's tables (put/get/versions of one `workflow_graphs` table) on the record tables of IF-301 v2: nodes, edges and a pinning header.
    The Storage layer has no such table, so this adapter splits a graph into records and joins them again (adapter detail)."""

    def __init__(self, storage):
        self.storage = storage

    def put(self, table, graph_id, graph):
        nodes = [{"id": n["id"], "version": self.storage.put("graph_nodes", n["id"], n, AUTHOR)["version"]} for n in graph["nodes"]]
        edges = [{"id": e["id"], "version": self.storage.put("graph_edges", e["id"], e, AUTHOR)["version"]} for e in graph["edges"]]
        data = {"kind": "workflow", "nodes": nodes, "edges": edges, **{key: graph[key] for key in HEADER[1:]}}
        return self.storage.put("graphs", graph_id, {"id": graph_id, "data": data}, AUTHOR)["version"]

    def get(self, table, graph_id, version=None):
        header = self.storage.get("graphs", graph_id, version)["doc"]
        data = header["data"]
        pinned = lambda name, members: [self.storage.get(name, m["id"], m["version"])["doc"] for m in members]    # noqa: E731
        return {"id": header["id"], **{key: data[key] for key in HEADER[1:]},
                "nodes": pinned("graph_nodes", data["nodes"]), "edges": pinned("graph_edges", data["edges"])}

    def versions(self, table, graph_id):
        return [h["version"] for h in self.storage.history("graphs", graph_id)]


def chain_graph(graph_id, **kwargs):
    nodes = [data_node("D1"), transform_node("T1"), data_node("D2"), master_node("M1"), data_node("D3")]
    edges = [make_edge("D1", "T1"), make_edge("T1", "D2"), make_edge("D2", "M1"), make_edge("M1", "D3")]
    return make_graph(graph_id, nodes, edges, **kwargs)


# Each scenario takes the tables and returns what it observed as IDs, flags and version numbers only.

def scenario_040(records):
    first = make_skill("lookup", "/lookup", workflow_graph_id="wf-lookup", context_graph_id="ctx-a")
    edited = make_skill("lookup", "/lookup", workflow_graph_id="wf-lookup", context_graph_id="ctx-b")
    stored = records.store(first)
    read_first = records.read("lookup")
    stored_again = records.store(edited)
    return {"first": (stored.stored, stored.version), "first_equal": read_first == first, "again": (stored_again.stored, stored_again.version),
            "v1": records.read("lookup", 1) == first, "v2": records.read("lookup", 2) == edited, "ids": records.ids()}


def scenario_041(records):
    records.store(make_skill("lookup", "/lookup", workflow_graph_id="wf-lookup"))
    legacy = {"skill_files": {"lookup": "/lk-file"}, "manifests": {"lookup": "/lk-manifest"}, "pipelines": {"lookup": "/lk-pipe"}}
    with_old = SkillCatalog(records, legacy).list()
    bare = SkillCatalog(records, {})
    return {"with_old": [(s["id"], s["command"]) for s in with_old], "without": [(s["id"], s["command"]) for s in bare.list()],
            "start": bare.start("lookup"), "start_unknown": bare.start("other")}


def scenario_042(records):
    records.store(make_skill("lookup", "/lookup"))
    clash = records.store(make_skill("review", "/lookup"))
    twin = records.store(make_skill("lookup", "/lookup", context_graph_id="ctx-new"))
    return {"clash": (clash.stored, clash.version, clash.named), "twin": (twin.stored, twin.version), "ids": records.ids()}


def scenario_044(model):
    empty_tb = chain_graph("wf-a", context_graph_id="ctx-a", testbench_id="", description="no testbench")
    with_tb = chain_graph("wf-b", context_graph_id="ctx-b", testbench_id="tb-1", description="with testbench")
    results = [model.save_graph(g) for g in (empty_tb, with_tb)]
    read = [model.read_graph(g["id"]) for g in (empty_tb, with_tb)]
    return {"saved": [(r.saved, r.version) for r in results], "fields": [{k: g.get(k) for k in HEADER} for g in read],
            "as_stored": [{k: g.get(k) for k in HEADER} for g in read] == [{k: g[k] for k in HEADER} for g in (empty_tb, with_tb)]}


def scenario_049(model):
    graph = make_graph("wf-params", [data_node("D1", value="text", parameters={"folder": "out"}), transform_node("T1"), data_node("D2")],
                       [make_edge("D1", "T1"), make_edge("T1", "D2")])
    saved = model.save_graph(graph)
    node = {n["id"]: n for n in model.read_graph("wf-params")["nodes"]}["D1"]
    return {"saved": (saved.saved, saved.version), "value": node["data"].get("value"), "parameters": node["data"].get("parameters")}


class SkillRecordOnRealStorage:
    """The five scenarios on both sides; new_storage() gives the real Storage of the backend under test."""

    def new_storage(self):
        raise NotImplementedError

    def setUp(self):
        self.storage = self.new_storage()
        self.records = SkillRecords(self.storage, AUTHOR)
        self.fake_records = SkillRecords(FakeSide(), AUTHOR)
        self.model = GraphModel(RealGraphTables(self.storage))
        self.fake_model = GraphModel(FakeSide())

    @mark.req("REQ-WFM-040")
    def test_a_skill_record_gives_the_same_versions_on_the_fake_and_the_real_storage(self):
        """TC-WFM-040 on both sides: stored and read back equal; an edit is version 2 and version 1 stays as first stored.

        Example: `lookup` with context graph `ctx-a`, edited to `ctx-b`: versions 1 and 2 on the fake and on the Storage layer, the ID list is ["lookup"].
        """
        # Given: the same scenario on the fake and on the real Storage layer
        # When: the record is stored, read back, edited and stored again on each side
        fake, real = scenario_040(self.fake_records), scenario_040(self.records)
        # Then: both sides give the same answers, and the answers are the expected ones
        self.assertEqual(real, fake)
        self.assertEqual(real, {"first": (True, 1), "first_equal": True, "again": (True, 2), "v1": True, "v2": True, "ids": ["lookup"]})

    @mark.req("REQ-WFM-041")
    def test_the_record_wins_over_the_old_forms_on_the_fake_and_the_real_storage(self):
        """TC-WFM-041 on both sides: the list shows the record's command with or without the old forms; the run is the record's workflow graph.

        Example: record `/lookup` against old forms `/lk-file`, `/lk-manifest`, `/lk-pipe` lists [("lookup", "/lookup")]; start gives `wf-lookup`; an unknown skill gives None.
        """
        # Given: a skill with a record and the same skill as old skill file, manifest and pipeline reference
        # When: the skills are listed with and without the old forms and a run is started, on each side
        fake, real = scenario_041(self.fake_records), scenario_041(self.records)
        # Then: both sides give the same answers
        self.assertEqual(real, fake)
        self.assertEqual(real, {"with_old": [("lookup", "/lookup")], "without": [("lookup", "/lookup")], "start": "wf-lookup", "start_unknown": None})

    @mark.req("REQ-WFM-042")
    def test_a_command_used_by_another_skill_is_refused_the_same_on_both_sides(self):
        """TC-WFM-042 on both sides: the clash is refused naming `lookup`; a new version of `lookup` is accepted.

        Example: `review` with /lookup is refused naming ["lookup"], nothing stored (no version); version 2 of `lookup` is accepted; the IDs stay ["lookup"].
        """
        # Given: the skill lookup with command /lookup on each side
        # When: review with the same command is stored, then version 2 of lookup
        fake, real = scenario_042(self.fake_records), scenario_042(self.records)
        # Then: both sides give the same answers
        self.assertEqual(real, fake)
        self.assertEqual(real, {"clash": (False, None, ["lookup"]), "twin": (True, 2), "ids": ["lookup"]})

    @mark.req("REQ-WFM-044")
    def test_the_four_fields_of_a_graph_read_back_the_same_on_both_sides(self):
        """TC-WFM-044 on both sides: ID, context graph ID, testbench ID and description read back as stored; an empty testbench ID is accepted.

        Example: testbench ID "" and "tb-1" both read back unchanged, both saved as version 1.
        """
        # Given: two workflow graphs, one with an empty testbench ID, on each side (the real side splits them into node, edge and header records)
        # When: both are saved and read back
        fake, real = scenario_044(self.fake_model), scenario_044(self.model)
        # Then: both sides give the same answers
        self.assertEqual(real, fake)
        self.assertEqual(real["saved"], [(True, 1), (True, 1)])
        self.assertTrue(real["as_stored"])

    @mark.req("REQ-WFM-049")
    def test_a_data_node_keeps_value_and_parameters_apart_on_both_sides(self):
        """TC-WFM-049 on both sides: a data node with a value and parameters reads back with both, in separate fields.

        Example: value "text" and parameters {"folder": "out"} read back as value "text" and parameters {"folder": "out"}.
        """
        # Given: a data node with a value and parameters on each side
        # When: the graph is saved and read back
        fake, real = scenario_049(self.fake_model), scenario_049(self.model)
        # Then: both sides give the same answers
        self.assertEqual(real, fake)
        self.assertEqual(real, {"saved": (True, 1), "value": "text", "parameters": {"folder": "out"}})

    @mark.req("REQ-WFM-040")
    def test_a_record_the_record_checks_refuse_is_not_stored(self):
        """Finding for TR-MODEL-001: the record checks of IF-301 v2 refuse a skill without a context graph ID; the fake takes it.

        Example: a skill with no `context_graph_id` raises StorageError invalid on the real side and the ID list stays empty; the fake lists it.
        """
        # Given: a skill record without context_graph_id
        broken = {"id": "lookup", "command": "/lookup", "workflow_graph_id": "wf-lookup"}
        # When: it is stored on the real side
        with self.assertRaises(StorageError) as caught:
            self.records.store(broken)
        # Then: it is refused as invalid and nothing is listed
        self.assertEqual(caught.exception.code, "invalid")
        self.assertEqual(self.records.ids(), [])
        # And: the fake accepts it (the known gap of the fake, which checks nothing)
        self.assertTrue(self.fake_records.store(broken).stored)


class FileStorageSkillRecords(SkillRecordOnRealStorage, unittest.TestCase):
    def new_storage(self):
        folder = tempfile.mkdtemp(prefix="skill-records-")
        self.addCleanup(shutil.rmtree, folder, True)
        return Storage(FileBackend(folder))


try:
    from test_storage_postgres import start_database, stop_database, PostgresBackend
except ImportError as error:        # psycopg 3 missing: the PostgreSQL class skips, as in test_storage_postgres.py
    start_database = None
    SKIP_REASON = str(error)


@unittest.skipIf(start_database is None, "psycopg 3 is not installed")
class PostgresSkillRecords(SkillRecordOnRealStorage, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = start_database()
        cls.addClassCleanup(stop_database)

    def new_storage(self):
        backend = PostgresBackend(self.url)
        backend._query("TRUNCATE records")
        self.addCleanup(backend.close)
        return Storage(backend)


if __name__ == "__main__":
    unittest.main()
