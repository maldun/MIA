"""
Acceptance tests of the skill record and the graph model (N-2.3, G-V2.MODEL): TC-WFM-040 to TC-WFM-049 (REQ-WFM-040 to -049) against GraphModel,
SkillRecords and SkillCatalog on the minimal fake of the graph tables (TR-MODEL-001).
Run with: python tests/acceptance/test_graph_model.py
"""

import os
import random
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
from graph_model_fakes import (FakeGraphTables, data_node, make_edge, make_graph, make_node, make_skill,   # noqa: E402
                               master_node, transform_node)
from graph_model import GraphModel                                    # noqa: E402
from skill_record import SkillCatalog, SkillRecords                   # noqa: E402

HEADER = ("id", "context_graph_id", "testbench_id", "description")


def chain_graph(graph_id="wf", **kwargs):
    """D1 -> T1 -> D2 -> M1 -> D3, all rules kept: the accepted base graph of the rule checks."""
    nodes = [data_node("D1"), transform_node("T1"), data_node("D2"), master_node("M1"), data_node("D3")]
    edges = [make_edge("D1", "T1"), make_edge("T1", "D2"), make_edge("D2", "M1"), make_edge("M1", "D3")]
    return make_graph(graph_id, nodes, edges, **kwargs)


class SkillRecordAcceptance(unittest.TestCase):
    def setUp(self):
        self.tables = FakeGraphTables()
        self.records = SkillRecords(self.tables)

    @mark.req("REQ-WFM-040")
    def test_a_skill_record_is_stored_read_back_and_an_edit_is_a_new_version(self):
        """TC-WFM-040: a skill record is stored and read back equal; an edit is version 2 and version 1 stays as first stored.

        Example: `lookup` with context graph `ctx-a` -> edited to `ctx-b` gives version 2; version 1 still names `ctx-a`.
        """
        # Given: the fake storage and a skill record with ID lookup, command /lookup, a workflow graph ID and a context graph ID
        first = make_skill("lookup", "/lookup", workflow_graph_id="wf-lookup", context_graph_id="ctx-a")
        # When: the record is stored, read back, then edited (another context graph ID) and stored again
        stored = self.records.store(first)
        read_first = self.records.read("lookup")
        edited = make_skill("lookup", "/lookup", workflow_graph_id="wf-lookup", context_graph_id="ctx-b")
        stored_again = self.records.store(edited)
        # Then: the first read equals what was stored
        self.assertEqual((stored.stored, stored.version), (True, 1))
        self.assertEqual(read_first, first)
        # And: the edit is version 2; version 1 still reads as first stored
        self.assertEqual((stored_again.stored, stored_again.version), (True, 2))
        self.assertEqual(self.records.read("lookup", 1), first)
        self.assertEqual(self.records.read("lookup", 2), edited)

    @mark.req("REQ-WFM-041")
    def test_the_record_wins_over_the_old_forms_of_a_skill(self):
        """TC-WFM-041: with a record, the command and the run come from the record, with or without the old skill file, manifest and pipeline.

        Example: record `/lookup`, old forms `/lk-file`, `/lk-manifest`, `/lk-pipe` -> the list shows `/lookup`, also after the old forms are removed.
        """
        # Given: a skill with a record, and the same skill still present as skill file, extension manifest and pipeline reference, each naming a different command
        self.records.store(make_skill("lookup", "/lookup", workflow_graph_id="wf-lookup"))
        legacy = {"skill_files": {"lookup": "/lk-file"}, "manifests": {"lookup": "/lk-manifest"}, "pipelines": {"lookup": "/lk-pipe"}}
        # When: the skills are listed, then the old files are removed and the list is made and a run started
        with_old = SkillCatalog(self.records, legacy).list()
        without_old = SkillCatalog(self.records, {})
        listed = without_old.list()
        started = without_old.start("lookup")
        # Then: both lists show the record's command
        self.assertEqual([(s["id"], s["command"]) for s in with_old], [("lookup", "/lookup")])
        self.assertEqual([(s["id"], s["command"]) for s in listed], [("lookup", "/lookup")])
        # And: the run is the one of the record's workflow graph
        self.assertEqual(started, "wf-lookup")

    @mark.req("REQ-WFM-042")
    def test_a_command_used_by_another_skill_is_refused_naming_that_skill(self):
        """TC-WFM-042: a record whose command another skill uses is refused naming that skill; a new version of the same skill is accepted.

        Example: `lookup` has /lookup; `review` with /lookup is refused naming `lookup`; version 2 of `lookup` with /lookup is accepted.
        """
        # Given: the skill lookup with command /lookup stored
        self.records.store(make_skill("lookup", "/lookup"))
        # When: a record review with command /lookup is stored; then version 2 of lookup with command /lookup is stored
        clash = self.records.store(make_skill("review", "/lookup"))
        twin = self.records.store(make_skill("lookup", "/lookup", context_graph_id="ctx-new"))
        # Then: the first is refused and the refusal names lookup
        self.assertFalse(clash.stored)
        self.assertEqual(clash.named, ["lookup"])
        # And: the second is accepted (the twin differs only in the broken rule, TR-MODEL-002)
        self.assertEqual((twin.stored, twin.version), (True, 2))


class GraphModelAcceptance(unittest.TestCase):
    def setUp(self):
        self.tables = FakeGraphTables()
        self.model = GraphModel(self.tables)

    @mark.req("REQ-WFM-043")
    def test_a_node_of_another_type_is_refused_naming_the_node(self):
        """TC-WFM-043: a graph with a data, a transform and a master node is accepted; a copy with one node of type `sink` is refused naming it.

        Example: the chain D1 -> T1 -> D2 -> M1 -> D3 plus the loose node X1: type `data` is accepted, type `sink` is refused naming `X1`.
        """
        # Given: a graph with one data, one transform and one master node, and a copy where one node has the type sink
        good = chain_graph("wf-good")
        good["nodes"].append(data_node("X1"))
        bad = chain_graph("wf-bad")
        bad["nodes"].append(make_node("sink", "X1"))
        # When: both are saved
        saved_good = self.model.save_graph(good)
        saved_bad = self.model.save_graph(bad)
        # Then: the first is accepted
        self.assertTrue(saved_good.saved)
        # And: the second is refused and names the node
        self.assertFalse(saved_bad.saved)
        self.assertEqual(saved_bad.named, ["X1"])

    @mark.req("REQ-WFM-044")
    def test_the_four_fields_of_a_graph_read_back_as_stored(self):
        """TC-WFM-044: ID, context graph ID, testbench ID and description read back as stored; an empty testbench ID is accepted.

        Example: testbench ID "" and "tb-1" both read back unchanged.
        """
        # Given: a workflow graph with ID, context graph ID, description and an empty testbench ID, and one with a testbench ID
        empty_tb = chain_graph("wf-a", context_graph_id="ctx-a", testbench_id="", description="no testbench")
        with_tb = chain_graph("wf-b", context_graph_id="ctx-b", testbench_id="tb-1", description="with testbench")
        # When: both are stored and read back
        results = [self.model.save_graph(g) for g in (empty_tb, with_tb)]
        read = [self.model.read_graph(g["id"]) for g in (empty_tb, with_tb)]
        # Then: all four fields read back as stored
        self.assertEqual([{k: g.get(k) for k in HEADER} for g in read], [{k: g[k] for k in HEADER} for g in (empty_tb, with_tb)])
        # And: the empty testbench ID is accepted
        self.assertTrue(results[0].saved)

    @mark.req("REQ-WFM-045")
    def test_an_edge_between_two_data_or_two_other_nodes_is_refused_naming_the_edge(self):
        """TC-WFM-045: data->data and transform->master are refused naming the edge; data->transform and master->data are accepted.

        Example: the edge `D1>D2` of two data nodes is refused naming `D1>D2`; `D1>T1` is accepted.
        """
        # Given: graphs with one edge each: data to data, transform to master, data to transform, master to data
        def one_edge(graph_id, start, end):
            nodes = {"D1": data_node("D1"), "D2": data_node("D2"), "T1": transform_node("T1"), "M1": master_node("M1")}
            return make_graph(graph_id, [nodes[start], nodes[end]], [make_edge(start, end)])
        cases = [("wf-dd", "D1", "D2", False), ("wf-tm", "T1", "M1", False), ("wf-dt", "D1", "T1", True), ("wf-md", "M1", "D2", True)]
        # When: each is saved
        results = [(self.model.save_graph(one_edge(i, a, b)), a, b, ok) for i, a, b, ok in cases]
        # Then: the first two are refused naming the edge
        for result, start, end, accepted in results[:2]:
            self.assertFalse(result.saved)
            self.assertEqual(result.named, ["%s>%s" % (start, end)])
        # And: the last two are accepted
        for result, start, end, accepted in results[2:]:
            self.assertTrue(result.saved)

    @mark.req("REQ-WFM-046")
    def test_a_data_node_with_two_writers_is_refused_naming_it(self):
        """TC-WFM-046: a data node written by a transform and a master node is refused naming it; one read by two transforms is accepted.

        Example: T1 and M1 both write D1 -> refused naming `D1`; D2 read by T1 and T2 -> accepted.
        """
        # Given: a data node written by a transform and by a master node; another data node read by two transforms
        two_writers = make_graph("wf-two-writers", [transform_node("T1"), master_node("M1"), data_node("D1")],
                                 [make_edge("T1", "D1"), make_edge("M1", "D1")])
        two_readers = make_graph("wf-two-readers", [data_node("D2"), transform_node("T1"), transform_node("T2")],
                                 [make_edge("D2", "T1"), make_edge("D2", "T2")])
        # When: each graph is saved
        refused = self.model.save_graph(two_writers)
        accepted = self.model.save_graph(two_readers)
        # Then: the first is refused naming the data node
        self.assertFalse(refused.saved)
        self.assertEqual(refused.named, ["D1"])
        # And: the second is accepted
        self.assertTrue(accepted.saved)

    @mark.req("REQ-WFM-047")
    def test_a_cycle_is_refused_with_its_ids_and_every_accepted_graph_has_a_forward_order(self):
        """TC-WFM-047: a graph with a cycle of 2 or 4 nodes is refused with the cycle as IDs; a 5-node cycle is refused too; every accepted graph has a forward order.

        Example: d1->t1, t1->d1 is refused with a cycle such as ["d1","t1","d1"] (first ID repeated at the end, any start of the cycle).
        """
        # Given: 200 generated graphs (seeds 1 to 200), about half with one cycle of 2 or 4 nodes added; and one fixed 5-node cycle
        with_cycle = without_cycle = 0
        for seed in range(1, 201):
            graph, cycle = generated_graph(seed)
            # When: each is saved
            result = self.model.save_graph(graph)
            if cycle:
                with_cycle += 1
                # Then: each graph with a cycle is refused with the cycle as IDs, the first ID repeated at the end
                self.assertFalse(result.saved, "seed %d: a cycle was accepted" % seed)
                self.assertEqual(result.named[0], result.named[-1], "seed %d: first ID not repeated" % seed)
                self.assertEqual(sorted(set(result.named)), sorted(cycle), "seed %d: wrong nodes" % seed)
                self.assertEqual(len(result.named), len(cycle) + 1, "seed %d: wrong length" % seed)
                edges = {(e["from"], e["to"]) for e in graph["edges"]}
                self.assertTrue(all((a, b) in edges for a, b in zip(result.named, result.named[1:])), "seed %d: not a path of edges" % seed)
            else:
                without_cycle += 1
                # And: each accepted graph has a topological order in which every edge points forward (checked here, not by the function again)
                self.assertTrue(result.saved, "seed %d: a graph without a cycle was refused" % seed)
                order = self.model.topological_order(graph["id"])
                self.assertEqual(sorted(order), sorted(n["id"] for n in graph["nodes"]), "seed %d: order lacks nodes" % seed)
                place = {node_id: i for i, node_id in enumerate(order)}
                self.assertTrue(all(place[e["from"]] < place[e["to"]] for e in graph["edges"]), "seed %d: an edge points backward" % seed)
        # TR-MODEL-003: both outcomes are covered
        self.assertGreaterEqual(with_cycle, 60)
        self.assertGreaterEqual(without_cycle, 60)
        # And: the graph with the 5-node cycle is refused; it breaks REQ-WFM-045 as well, so it need not name the cycle
        self.assertFalse(self.model.save_graph(five_node_cycle()).saved)

    @mark.req("REQ-WFM-048")
    def test_a_master_node_without_a_stop_is_refused_naming_it(self):
        """TC-WFM-048: a master node with neither a maximum of repetitions nor a maximum time is refused naming it; with 1 repetition it is accepted.

        Example: M1 without `stop` -> refused naming `M1`; M1 with max_repetitions 1 -> accepted.
        """
        # Given: a graph with a master node without a maximum of repetitions and without a maximum time; the same with a maximum of 1 repetition
        def with_master(graph_id, max_repetitions):
            return make_graph(graph_id, [data_node("D1"), master_node("M1", max_repetitions=max_repetitions), data_node("D2")],
                              [make_edge("D1", "M1"), make_edge("M1", "D2")])
        # When: each is saved
        refused = self.model.save_graph(with_master("wf-no-stop", None))
        accepted = self.model.save_graph(with_master("wf-stop", 1))
        # Then: the first is refused naming the master node
        self.assertFalse(refused.saved)
        self.assertEqual(refused.named, ["M1"])
        # And: the second is accepted
        self.assertTrue(accepted.saved)

    @mark.req("REQ-WFM-049")
    def test_a_data_node_keeps_its_parameters_apart_from_its_value(self):
        """TC-WFM-049: a data node with a value and parameters reads back with both, in separate fields.

        Example: value "text" and parameters {"folder": "out"} read back as value "text" and parameters {"folder": "out"}.
        """
        # Given: a data node with the value "text" and the parameters {"folder": "out"}
        graph = make_graph("wf-params", [data_node("D1", value="text", parameters={"folder": "out"}), transform_node("T1"), data_node("D2")],
                           [make_edge("D1", "T1"), make_edge("T1", "D2")])
        # When: it is stored and read back
        self.model.save_graph(graph)
        read = self.model.read_graph("wf-params")
        node = {n["id"]: n for n in read.get("nodes", [])}.get("D1", {"data": {}})
        # Then: the value reads "text" and the parameters read {"folder": "out"}, in separate fields
        self.assertEqual(node["data"].get("value"), "text")
        self.assertEqual(node["data"].get("parameters"), {"folder": "out"})


def generated_graph(seed):
    """Graph of seed `seed`: a random forward-only (acyclic) chain of alternating data and transform nodes; even seeds get one separate cycle of 2 or 4 nodes.

    Returns (graph, cycle node IDs or None). Each data node has at most one writer and the roles alternate, so only the cycle can break a rule.
    """
    rng = random.Random(seed)
    size = rng.randint(3, 8)
    nodes = [data_node("n%d" % i) if i % 2 == 0 else transform_node("n%d" % i) for i in range(size)]
    edges = []
    for i in range(size):
        for j in range(i + 1, size):
            if (i % 2) != (j % 2) and rng.random() < 0.4:
                edges.append(make_edge("n%d" % i, "n%d" % j))
    writers = {}
    kept = []
    for e in edges:
        end_is_data = int(e["to"][1:]) % 2 == 0
        if end_is_data and writers.setdefault(e["to"], e["from"]) != e["from"]:
            continue
        kept.append(e)
    cycle = None
    if seed % 2 == 0:
        length = rng.choice([2, 4])
        cycle = ["c%d" % i for i in range(length)]
        nodes += [data_node(c) if i % 2 == 0 else transform_node(c) for i, c in enumerate(cycle)]
        kept += [make_edge(cycle[i], cycle[(i + 1) % length]) for i in range(length)]
    return make_graph("wf-seed-%d" % seed, nodes, kept), cycle


def five_node_cycle():
    ids = ["k%d" % i for i in range(5)]
    nodes = [data_node(i) if n % 2 == 0 else transform_node(i) for n, i in enumerate(ids)]
    return make_graph("wf-five", nodes, [make_edge(ids[i], ids[(i + 1) % 5]) for i in range(5)])


if __name__ == "__main__":
    unittest.main()
