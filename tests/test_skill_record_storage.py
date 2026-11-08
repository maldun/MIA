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
                               master_node, make_node, transform_node)
from graph_model import GraphModel, check_graph                                                             # noqa: E402
from graph_tables import check_record                                                                      # noqa: E402
from skill_record import SkillCatalog, SkillRecords                                                         # noqa: E402
from storage import Storage, StorageError                                                                   # noqa: E402
from storage_files import FileBackend                                                                       # noqa: E402

AUTHOR = "anna"
HEADER = ("id", "context_graph_id", "testbench_id", "description")


class FakeSide(FakeGraphTables):
    """The fake with the `author` the caller now gives: the fake keeps no authors (adapter detail)."""

    def put(self, table, record_id, doc, author=None):
        return super().put(table, record_id, doc)


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
        self.model = GraphModel(self.storage, AUTHOR)
        self.fake_model = GraphModel(FakeSide(), AUTHOR)

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
        # Given: two workflow graphs, one with an empty testbench ID, on each side (GraphModel itself splits them into node, edge and header records on the real side)
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
    def test_a_record_the_record_checks_refuse_is_a_refused_result_and_not_stored(self):
        """Finding for TR-MODEL-001: the record checks of IF-301 v2 refuse a skill without a context graph ID; the fake takes it.

        Example: a skill with no `context_graph_id` gives a refused result with the rule and detail of the Storage refusal, the ID stays unknown and the list empty; the fake stores it.
        """
        # Given: a skill record without context_graph_id, and the refusal the Storage layer itself gives for its document
        broken = {"id": "lookup", "command": "/lookup", "workflow_graph_id": "wf-lookup"}
        with self.assertRaises(StorageError) as expected:
            self.storage.put("skills", "lookup", {"id": "lookup", "data": {k: v for k, v in broken.items() if k != "id"}}, AUTHOR)
        self.assertEqual(expected.exception.code, "invalid")
        # When: it is stored on the real side
        result = self.records.store(broken)
        # Then: it is a refused result (no exception) carrying the rule and detail of the refusal, nothing stored
        self.assertEqual((result.stored, result.version, result.named), (False, None, []))
        self.assertEqual((result.rule, result.detail), (expected.exception.rule, expected.exception.detail))
        self.assertEqual(self.records.ids(), [])
        with self.assertRaises(StorageError) as unknown:
            self.records.read("lookup")
        self.assertEqual(unknown.exception.code, "not_found")
        # And: another refusal of the Storage layer (an unknown table) still raises
        with self.assertRaises(StorageError) as other:
            SkillRecords(self.storage, AUTHOR).tables.put("no_such_table", "x", {"id": "x"}, AUTHOR)
        self.assertEqual(other.exception.code, "unknown_table")
        # And: the fake accepts it (the known gap of the fake, which checks nothing)
        self.assertTrue(self.fake_records.store(broken).stored)

    @mark.req("REQ-WFM-043")
    def test_a_graph_the_record_checks_refuse_is_a_refused_result_and_the_header_is_not_stored(self):
        """A node with a field its type does not list is refused by the record checks of the Storage layer: a refused result with rule and detail, no header.

        Example: data node D1 with the extra field `foo` gives (False, None, [], "schema_break", "foo"); the graph stays unknown; the fake takes it.
        """
        # Given: a graph whose node D1 has a field that its type does not list, and the refusal the Storage layer itself gives for that node
        graph = chain_graph("wf-bad")
        graph["nodes"][0]["data"]["foo"] = 1
        with self.assertRaises(StorageError) as expected:
            self.storage.put("graph_nodes", "D1", graph["nodes"][0], AUTHOR)
        # When: the graph is saved on the real side
        result = self.model.save_graph(graph)
        # Then: a refused result (no exception) with the rule and detail of the refusal, and no header
        self.assertEqual((result.saved, result.version, result.named), (False, None, []))
        self.assertEqual((result.rule, result.detail), (expected.exception.rule, expected.exception.detail))
        self.assertEqual(self.storage.ids("graphs"), [])
        # And: the fake accepts it (known gap of the fake, which checks nothing)
        self.assertTrue(self.fake_model.save_graph(graph).saved)

    @mark.req("REQ-WFM-043")
    def test_a_rule_refusal_of_the_graph_is_checked_before_anything_is_written(self):
        """The rules of T-01 come first: a graph with a cycle names the cycle and writes no record at all.

        Example: D1 -> T1 -> D1 is refused naming ["D1", "T1", "D1"] (rule and detail empty); no node, edge or header is stored.
        """
        # Given: a graph with a cycle
        graph = make_graph("wf-cycle", [data_node("D1"), transform_node("T1")], [make_edge("D1", "T1"), make_edge("T1", "D1")])
        # When: it is saved on the real side
        result = self.model.save_graph(graph)
        # Then: it is refused naming the cycle, and the tables are empty
        self.assertEqual((result.saved, result.rule, result.detail), (False, None, None))
        self.assertEqual(result.named[0], result.named[-1])
        self.assertEqual([self.storage.ids(t) for t in ("graph_nodes", "graph_edges", "graphs")], [[], [], []])

    @mark.req("REQ-WFM-044")
    def test_a_header_naming_an_unknown_member_version_is_refused_with_the_storage_rule(self):
        """The header pins member versions; one that is not stored is refused by the Storage layer with `unknown_member`.

        Example: a header naming node D1 at version 5 (only version 1 stored) raises code `invalid`, rule `unknown_member`, detail `D1`.
        """
        # Given: a saved graph, so D1 is stored at version 1
        self.model.save_graph(chain_graph("wf-a", context_graph_id="c", testbench_id="", description=""))
        data = {"kind": "workflow", "nodes": [{"id": "D1", "version": 5}], "edges": [], "context_graph_id": "c", "testbench_id": "", "description": ""}
        # When: a header names version 5 of D1
        with self.assertRaises(StorageError) as refused:
            self.storage.put("graphs", "wf-x", {"id": "wf-x", "data": data}, AUTHOR)
        # Then: it is refused with the rule of the Storage layer, and nothing is stored
        self.assertEqual((refused.exception.code, refused.exception.rule, refused.exception.detail), ("invalid", "unknown_member", "D1"))
        self.assertEqual(self.storage.ids("graphs"), ["wf-a"])

    @mark.req("REQ-WFM-044")
    def test_an_old_version_of_a_graph_reads_back_with_the_members_of_that_version(self):
        """Version 1 of a graph keeps the node versions it pinned after the node is edited in version 2.

        Example: description "one" of D1 in version 1, "two" in version 2; read version 1 gives "one", the latest gives "two".
        """
        # Given: a graph saved twice, with the value of D1 changed
        first = chain_graph("wf-v", context_graph_id="c", testbench_id="", description="first")
        second = chain_graph("wf-v", context_graph_id="c", testbench_id="", description="second")
        second["nodes"][0] = data_node("D1", value="two")
        saved = [self.model.save_graph(first), self.model.save_graph(second)]
        # When: version 1 and the latest version are read
        old, latest = self.model.read_graph("wf-v", 1), self.model.read_graph("wf-v")
        # Then: version 1 has the first members, the latest the edited one, the order is the same
        self.assertEqual([(r.saved, r.version) for r in saved], [(True, 1), (True, 2)])
        self.assertEqual((old["description"], latest["description"]), ("first", "second"))
        self.assertEqual(old["nodes"][0], first["nodes"][0])
        self.assertEqual(latest["nodes"][0], second["nodes"][0])
        self.assertEqual(self.model.topological_order("wf-v"), ["D1", "T1", "D2", "M1", "D3"])


    def master_graph(self, graph_id, stop):
        nodes = [data_node("D1"), make_node("master", "M1", toolbox_id="m1", stop=stop), data_node("D2")]
        return make_graph(graph_id, nodes, [make_edge("D1", "M1"), make_edge("M1", "D2")])

    @mark.req("REQ-WFM-048")
    def test_the_stop_of_a_master_node_uses_the_field_names_of_if_301_on_both_sides(self):
        """F-01 (REQ-WFM-048): a master node with `max_seconds` only is accepted; `max_time` only and an empty stop are refused naming the node.

        Example: stop {"max_seconds": 5} is saved (version 1); {"max_repetitions": 3} is saved; {"max_time": 5} and {} are refused naming ["M1"] on the fake and the Storage layer.
        """
        # Given: the same master node with four different stops, on each side
        for model in (self.fake_model, self.model):
            # When: each graph is saved
            results = {name: model.save_graph(self.master_graph("wf-" + name, stop))
                       for name, stop in (("seconds", {"max_seconds": 5}), ("repetitions", {"max_repetitions": 3}), ("time", {"max_time": 5}), ("empty", {}))}
            # Then: max_seconds and max_repetitions are accepted, max_time and the empty stop are refused naming M1
            self.assertEqual([(n, results[n].saved) for n in ("seconds", "repetitions", "time", "empty")],
                             [("seconds", True), ("repetitions", True), ("time", False), ("empty", False)])
            self.assertEqual((results["seconds"].version, results["time"].named, results["empty"].named), (1, ["M1"], ["M1"]))

    @mark.req("REQ-WFM-042")
    def test_a_command_is_compared_in_the_form_the_loader_registers_on_both_sides(self):
        """F-02 (REQ-WFM-042): a command that differs only in the leading slash or in case counts as the command of the other skill.

        Example: `lookup` has `/lookup`; `review` with `/Lookup` and with `lookup` is refused naming ["lookup"]; `review` with `/review` is stored.
        """
        # Given: the skill lookup with /lookup, on each side
        for records in (self.fake_records, self.records):
            records.store(make_skill("lookup", "/lookup"))
            # When: review is stored with the command in another case and without the slash
            upper, bare = records.store(make_skill("review", "/Lookup")), records.store(make_skill("review", "lookup"))
            fine = records.store(make_skill("review", "/review"))
            # Then: both are refused naming lookup, a different command is stored
            self.assertEqual([(upper.stored, upper.named), (bare.stored, bare.named)], [(False, ["lookup"]), (False, ["lookup"])])
            self.assertTrue(fine.stored)

    @mark.req("REQ-WFM-041")
    def test_a_command_that_cannot_be_registered_is_refused_on_both_sides(self):
        """F-03 (REQ-WFM-041): empty, `/`, a command with a space, a second slash or an uppercase letter is a refused result with a rule, nothing stored.

        Example: commands "", "/", "/a b", "//a", "/Alpha", "/ς", "/µ", "/é" (F-15: only ASCII letters and digits) give stored False with rule "schema" and no ID in the list; "/alpha" and "beta" are stored.
        """
        # Given: records with bad commands, on each side
        for records in (self.fake_records, self.records):
            # When: each is stored
            results = [records.store(make_skill("alpha", command)) for command in ("", "/", "/a b", "//a", "/Alpha", "/ς", "/µ", "/ſ", "/ı", "/é", "/a-b", "/a.b", "/日本")]
            # Then: each is refused with a rule and a detail, and nothing is stored
            self.assertEqual([(r.stored, r.version, r.rule) for r in results], [(False, None, "schema")] * 13)
            self.assertTrue(all(r.detail for r in results))
            self.assertEqual(records.ids(), [])
            # And: the plain forms are stored
            self.assertTrue(records.store(make_skill("alpha", "/alpha")).stored)
            self.assertTrue(records.store(make_skill("beta", "beta")).stored)
            self.assertTrue(records.store(make_skill("gamma", "/ab12")).stored)

    @mark.req("REQ-WFM-048")
    def test_the_stop_rule_of_the_model_agrees_with_the_record_check_for_every_stop(self):
        """F-16 (REQ-WFM-048): the rule of T-01 (a limit is a positive number, an integer for the repetitions, not a boolean) accepts and refuses the same stops as the record check.

        Example: {"max_repetitions": -1}, {"max_seconds": True}, {"max_repetitions": 2.5}, {"max_seconds": "5"} and "x" are refused by both; {"max_seconds": 0.5} and {"max_repetitions": 2, "max_time": 1} by neither.
        """
        # Given: every stop made of two limits out of a pool of good and bad values (absent included), the stops with another key, and stops that are no object
        pool = [0, 1, -1, 2, 0.5, 2.0, 2.5, -0.5, True, False, "5", "", None, [], {}, 10 ** 12, float("inf"), float("-inf"), float("nan"), 1e308, 10 ** 400, -10 ** 400]
        absent = object()
        stops = []
        for first in pool + [absent]:
            for second in pool + [absent]:
                stops.append({k: v for k, v in (("max_repetitions", first), ("max_seconds", second)) if v is not absent})
        stops += [{"max_time": 5}, {"max_cycles": 3}, {"max_repetitions": 2, "max_time": 1}, {"max_seconds": 1, "x": None}, "x", "", 3, 0, None, [], [1], True, {"max_repetitions": 1, "max_seconds": 1}]
        disagreements = []
        for stop in stops:
            node = {"id": "M1", "data": {"type": "master", "toolbox_id": "m1", "stop": stop}}
            # When: the rule of the model and the record check judge the node
            by_model = check_graph(make_graph("wf-stop", [data_node("D1"), node, data_node("D2")], [make_edge("D1", "M1"), make_edge("M1", "D2")])) == []
            by_storage = check_record("graph_nodes", node, record_id="M1") is None
            if by_model != by_storage:
                disagreements.append((stop, by_model, by_storage))
        # Then: they never disagree
        self.assertEqual(disagreements, [])

    @mark.req("REQ-WFM-048")
    def test_an_integer_limit_beyond_the_float_range_gives_the_answer_of_the_record_check_and_no_exception(self):
        """F-19 (REQ-WFM-048): `check_graph` does not raise `OverflowError` for an integer above the float range; the answer is the one of the record check (a big positive integer is a valid limit).

        Example: stops {"max_seconds": 10**400}, {"max_repetitions": 10**400}, both together are accepted; {"max_seconds": -10**400} is refused naming ["M1"]; the record check agrees.
        """
        for stop, accepted in (({"max_seconds": 10 ** 400}, True), ({"max_repetitions": 10 ** 400}, True), ({"max_repetitions": 10 ** 400, "max_seconds": 10 ** 400}, True),
                               ({"max_seconds": -10 ** 400}, False), ({"max_repetitions": -10 ** 400}, False)):
            with self.subTest(stop=str(stop)[:12] + "..", accepted=accepted):
                # Given: a master node whose stop holds an integer that float() cannot take
                node = {"id": "M1", "data": {"type": "master", "toolbox_id": "m1", "stop": stop}}
                # When: the model checks the graph and the record check judges the node
                named = check_graph(make_graph("wf-big", [data_node("D1"), node, data_node("D2")], [make_edge("D1", "M1"), make_edge("M1", "D2")]))
                # Then: no exception, both answer alike, and the answer is the expected one
                self.assertEqual((named == [], check_record("graph_nodes", node, record_id="M1") is None), (accepted, accepted))
                self.assertEqual(named, [] if accepted else ["M1"])

    @mark.req("REQ-WFM-048")
    def test_a_stop_the_record_check_refuses_is_refused_by_the_model_on_both_sides(self):
        """F-16 (REQ-WFM-048): the fake and the Storage layer give the same answer for a negative, boolean, fractional or text limit, naming the master node.

        Example: stops {"max_repetitions": -1}, {"max_seconds": True}, {"max_repetitions": 2.5}, {"max_seconds": "5"} are refused naming ["M1"] on the fake and on the Storage layer.
        """
        # Given: master nodes with four bad stops, on each side
        for model in (self.fake_model, self.model):
            for name, stop in (("neg", {"max_repetitions": -1}), ("bool", {"max_seconds": True}), ("frac", {"max_repetitions": 2.5}), ("text", {"max_seconds": "5"})):
                # When: the graph is saved
                result = model.save_graph(self.master_graph("wf-bad-" + name, stop))
                # Then: it is refused naming M1, as a graph rule, and a good one next to it is saved
                self.assertEqual((result.saved, result.named), (False, ["M1"]))
            self.assertTrue(model.save_graph(self.master_graph("wf-good", {"max_seconds": 0.5})).saved)


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
