"""The graph rules of the Graph tables (N-3.2 T-01): TC-GTB-002, TC-GTB-003 and the 500-node bound of IF-301. Run with: python tests/test_graph_rules.py"""
import graphlib
import os
import random
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from graph_rules import violation  # noqa: E402
from markers import mark           # noqa: E402

LOOKUP = {"nodes": [{"id": "question", "kind": "data"}, {"id": "search", "kind": "process"}, {"id": "hits", "kind": "data"},
                    {"id": "judge", "kind": "process"}, {"id": "verdict", "kind": "data"}],
          "edges": [{"from": "question", "to": "search"}, {"from": "search", "to": "hits"}, {"from": "hits", "to": "judge"}, {"from": "judge", "to": "verdict"}]}


def doc(nodes, edges=()):
    return {"nodes": [{"id": i, "kind": k, **extra} for i, k, extra in nodes], "edges": [{"from": a, "to": b} for a, b in edges]}


class GraphRules(unittest.TestCase):
    @mark.req("REQ-GTB-002")
    def test_a_valid_graph_has_no_violation(self):
        """TC-GTB-002: the lookup graph is valid."""
        self.assertIsNone(violation(LOOKUP))

    @mark.req("REQ-GTB-002")
    def test_each_rule_is_named(self):
        """TC-GTB-002: one minimal document per rule gives its name in turn."""
        cases = [
            ("node_identity", doc([("a", "data", {}), ("a", "process", {})])),
            ("node_identity", doc([("a", "data", {})], [("a", "ghost")])),
            ("adjacent_data_nodes", doc([("a", "data", {}), ("b", "data", {})], [("a", "b")])),
            ("adjacent_process_nodes", doc([("a", "process", {}), ("b", "process", {})], [("a", "b")])),
            ("session_stopping_criterion", doc([("s", "process", {"session": True, "stop": {"max_cycles": 0}})])),
            ("cycle", doc([("p", "process", {}), ("d", "data", {})], [("p", "d"), ("d", "p")])),
        ]
        for rule, document in cases:
            with self.subTest(rule=rule):
                self.assertEqual(violation(document)[0], rule)

    @mark.req("REQ-GTB-002")
    def test_a_cycle_is_named_by_its_ids_with_the_first_repeated(self):
        """TC-GTB-002: p->d->p is the cycle [p, d, p]; a self-loop of a process is adjacent processes, not a cycle."""
        self.assertEqual(violation(doc([("p", "process", {}), ("d", "data", {})], [("p", "d"), ("d", "p")])), ("cycle", ["p", "d", "p"]))
        self.assertEqual(violation(doc([("a", "process", {})], [("a", "a")]))[0], "adjacent_process_nodes")

    @mark.req("REQ-GTB-002")
    def test_a_session_needs_a_cycle_count_or_a_time_limit(self):
        """TC-GTB-002: max_cycles or max_seconds alone is enough; neither is refused."""
        for stop, expected in (({"max_cycles": 3}, None), ({"max_seconds": 60}, None), ({}, "session_stopping_criterion"), ({"max_cycles": 0, "max_seconds": 0}, "session_stopping_criterion")):
            with self.subTest(stop=stop):
                result = violation(doc([("s", "process", {"session": True, "stop": stop})]))
                self.assertEqual(result and result[0], expected)

    @mark.req("REQ-GTB-002")
    def test_a_document_that_is_not_a_graph_is_refused(self):
        """A missing or non-list nodes/edges is node_identity, never an exception."""
        for bad in ({}, {"nodes": "x", "edges": []}, {"nodes": [], "edges": None}, [], None):
            with self.subTest(bad=bad):
                self.assertEqual(violation(bad)[0], "node_identity")

    @mark.req("REQ-GTB-002")
    def test_a_graph_of_500_nodes_is_checked_within_200_ms(self):
        """IF-301 bound: validate a graph of 500 nodes in at most 200 ms."""
        nodes = [(("d%d" if n % 2 == 0 else "p%d") % n, "data" if n % 2 == 0 else "process", {}) for n in range(500)]
        edges = [(nodes[n][0], nodes[n + 1][0]) for n in range(499)]
        document = doc(nodes, edges)
        started = time.perf_counter()
        self.assertIsNone(violation(document))
        self.assertLess(time.perf_counter() - started, 0.2)


def generated(seed):
    """A random graph with shared inputs, session nodes, and now and then a broken rule; returns (doc, reference_ok)."""
    rng = random.Random(seed)
    count = rng.randint(2, 12)
    kinds = [rng.choice(("data", "process")) for _ in range(count)]
    ids = ["n%d" % i for i in range(count)]
    nodes = []
    for i, kind in enumerate(kinds):
        node = {"id": ids[i], "kind": kind}
        if kind == "process" and rng.random() < 0.3:
            node["session"] = True
            node["stop"] = rng.choice(({"max_cycles": 3}, {"max_seconds": 30}, {}, {"max_cycles": 0}))
        nodes.append(node)
    edges = []
    for _ in range(rng.randint(1, count * 2)):
        a, b = rng.randrange(count), rng.randrange(count)
        if rng.random() < 0.85 and kinds[a] == kinds[b]:                 # mostly alternate data and process, so cycles and sessions decide
            continue
        edges.append({"from": ids[a], "to": ids[b]})
    document = {"nodes": nodes, "edges": edges}
    kind = dict(zip(ids, kinds))
    adjacent = any(kind[e["from"]] == kind[e["to"]] for e in edges)
    session_bad = any(n.get("session") and not (n["stop"].get("max_cycles") or n["stop"].get("max_seconds")) for n in nodes if n["kind"] == "process")
    graph = {i: set() for i in ids}
    for e in edges:
        graph[e["to"]].add(e["from"])
    try:
        order = list(graphlib.TopologicalSorter(graph).static_order())
        cyclic = False
    except graphlib.CycleError:
        order, cyclic = None, True
    return document, not (adjacent or session_bad or cyclic), order


class Property(unittest.TestCase):
    @mark.req("REQ-GTB-002")
    @mark.statistical
    def test_accepted_exactly_when_the_reference_accepts(self):
        """TC-GTB-003: 1000 generated graphs (seeds 1 to 1000): accepted exactly when graphlib finds no cycle and no other rule is broken."""
        failures, accepted = [], 0
        for seed in range(1, 1001):
            document, reference_ok, order = generated(seed)
            result = violation(document)
            accepted += result is None
            if (result is None) != reference_ok:
                failures.append((seed, result))
            elif result is None:
                self.assertEqual(len(order), len(document["nodes"]))     # every accepted graph has a topological order, each node once
        self.assertEqual(failures, [])
        self.assertGreater(accepted, 100)                                # the generator does produce valid graphs, otherwise the test says nothing

    @mark.req("REQ-GTB-002")
    def test_a_named_cycle_follows_real_edges(self):
        """TC-GTB-003: when only a cycle is broken, the ids named are a path along the edges that ends where it starts."""
        checked = 0
        for seed in range(1, 1001):
            document, reference_ok, _ = generated(seed)
            result = violation(document)
            if result and result[0] == "cycle":
                ids = result[1]
                edges = {(e["from"], e["to"]) for e in document["edges"]}
                self.assertEqual(ids[0], ids[-1])
                self.assertTrue(all((a, b) in edges for a, b in zip(ids, ids[1:])), (seed, ids))
                checked += 1
        self.assertGreater(checked, 20)


if __name__ == "__main__":
    unittest.main()
