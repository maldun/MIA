"""Acceptance tests of the order of steps and the run order (G-V4.GRAPHAPI.RUN, protected after the Plan gate): TC-WFM-185, TC-WFM-186 (REQ-WFM-166,
REQ-WFM-167) against `graph_model.order_of`, and TC-RUN-041, TC-RUN-042, TC-RUN-043 (REQ-RUN-016, REQ-RUN-040, REQ-RUN-041) against GraphRunner, and TC-RUN-049 (REQ-RUN-047, A-190) on the imports. They guard
the order of today (the oracle): green from the start, except TC-RUN-043 (the run reads the loaded graph), which is red until the runner task.
Run with: python tests/acceptance/test_run_graph_order.py
"""
import ast
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tests", "helpers"))
sys.path.insert(0, os.path.join(REPO, "tests", "helpers", "mocks"))

from markers import mark                                                      # noqa: E402
from graph_model_fakes import Script, data_node, make_edge, make_graph, transform_node   # noqa: E402
from rules_graphs import connection, converted_skills, graph, transform       # noqa: E402
from run_graphs import acyclic, random_graphs                                 # noqa: E402
from run_store import git, oracle                                             # noqa: E402
from graph_model import order_of                                              # noqa: E402
from graph_run import GraphRunner                                             # noqa: E402


def steps(*ids, reads=()):
    """transforms listed in the order of `ids`; `reads` is a list of (reader, written-by) pairs: the reader comes after the writer, over a connection"""
    return graph([transform(i) for i in ids], [connection("e%d" % n, start, end) for n, (end, start) in enumerate(reads, 1)])


class OrderOfSteps(unittest.TestCase):
    @mark.req("REQ-WFM-166")
    def test_every_step_once_after_the_steps_it_reads_from(self):
        """TC-WFM-185: the order of each converted skill graph and each acyclic random graph lists every step once, every connection forward.

        Example: steps x, y, z with x reading from z: order y, z, x (z before x).
        """
        # Given: the 15 converted skill graphs and the acyclic ones of the 500 random graphs
        started = time.monotonic()
        graphs = [stored for _, stored in converted_skills()] + [g for g in random_graphs() if acyclic(g, order_of)]
        self.assertGreaterEqual(len(graphs), 15 + 100)
        # When: the order of each is asked; Then: every step once, and for every connection the step it comes from is earlier
        for stored in graphs:
            order = order_of(stored)
            self.assertEqual(sorted(order), sorted(n["id"] for n in stored["nodes"]), stored["id"])
            for e in stored["edges"]:
                self.assertLess(order.index(e["from"]), order.index(e["to"]), "%s: %s" % (stored["id"], e["id"]))
        print("order of %d graphs in %.3f s" % (len(graphs), time.monotonic() - started))     # the smoke number of the test spec, printed for the record

    @mark.req("REQ-WFM-167", "HR-006")
    def test_ties_in_the_order_steps_became_ready_and_the_order_as_before(self):
        """TC-WFM-186: independent steps keep their listed order; the ready steps go in the order they became ready; every recorded order is kept.

        Example: x, y, z with x reading from z: y, z, x; with x reading from y: y, z, x; b, a stays b, a.
        """
        # Given: two independent steps listed b, a and a, b; x, y, z with x reading from z; x, y, z with x reading from y
        # When: the order of each is asked; Then: the listed order for the independent steps, and the order the steps became ready otherwise
        self.assertEqual(order_of(steps("b", "a")), ["b", "a"])
        self.assertEqual(order_of(steps("a", "b")), ["a", "b"])
        self.assertEqual(order_of(steps("x", "y", "z", reads=[("x", "z")])), ["y", "z", "x"])
        self.assertEqual(order_of(steps("x", "y", "z", reads=[("x", "y")])), ["y", "z", "x"])
        # And: the order of every converted and every acyclic random graph equals the order recorded at goal/v4 (0 differences)
        recorded = oracle()
        differences = [name for name, stored in converted_skills() if order_of(stored) != recorded["converted"][name]["order"]]
        differences += ["random-%03d" % i for i, (stored, was) in enumerate(zip(random_graphs(), recorded["random"])) if was["order"] is not None and order_of(stored) != was["order"]]
        self.assertEqual(differences, [])


class RunOrder(unittest.TestCase):
    @mark.req("REQ-RUN-016", "REQ-WFM-167")
    def test_the_run_follows_the_listed_order_of_independent_steps(self):
        """TC-RUN-041: two independent transforms run in their listed order; a sound twin shows the markers can fire (TR-RUN-006).

        Example: listed T2, T1 -> the markers record T2, T1; listed T1, T2 -> T1, T2.
        """
        # Given: two independent transforms with a marker each, listed T2, T1, and the same listed T1, T2
        for listed in (("T2", "T1"), ("T1", "T2")):
            script = Script()
            self.addCleanup(__import__("shutil").rmtree, script.folder, True)
            stored = make_graph("wf-%s" % "".join(listed), [data_node("D1"), data_node("D2"), data_node("D3")] + [transform_node(i) for i in listed],
                                [make_edge("D1", listed[0]), make_edge(listed[0], "D2"), make_edge("D1", listed[1]), make_edge(listed[1], "D3")])
            # When: the graph is run
            result = GraphRunner(lambda node_id: "trusted").run(stored, {i: script.node(i) for i in listed}, {"D1": "s"})
            # Then: the markers record the listed order
            self.assertEqual(result.status, "done")
            self.assertEqual(script.order, list(listed))

    @mark.req("REQ-RUN-040")
    def test_one_step_at_a_time(self):
        """TC-RUN-042: each of four independent steps starts at or after the end of the step before it (monotonic clock, 0.05 s each).

        Example: starts and ends of T1..T4 interleave never: start(Tn+1) >= end(Tn).
        """
        # Given: four independent transforms whose functions record start and end on time.monotonic() and sleep 0.05 s
        spans = {}

        def timed(node_id):
            def run(inputs):
                started = time.monotonic()
                time.sleep(0.05)
                spans[node_id] = (started, time.monotonic())
                return node_id
            return run
        ids = ["T1", "T2", "T3", "T4"]
        stored = make_graph("wf-time", [data_node("D0")] + [data_node("D%d" % n) for n in range(1, 5)] + [transform_node(i) for i in ids],
                            [make_edge("D0", i) for i in ids] + [make_edge(i, "D%d" % n) for n, i in enumerate(ids, 1)])
        # When: the graph is run
        result = GraphRunner(lambda node_id: "trusted").run(stored, {i: timed(i) for i in ids}, {"D0": "s"})
        # Then: every start is at or after the end of the step before it in the order, with no tolerance
        self.assertEqual(result.status, "done")
        for before, after in zip(ids, ids[1:]):
            self.assertGreaterEqual(spans[after][0], spans[before][1], "%s started before %s ended" % (after, before))

    @mark.req("REQ-RUN-041")
    def test_the_run_reads_the_loaded_graph(self):
        """TC-RUN-043 (the search of TR-RUN-008; the checklist is read by a person): graph_run.py scans no node or edge list; the older run checks are unchanged.

        Example: no `graph["nodes"]`, `graph["edges"]`, `graph.get("nodes")` or `graph.get("edges")` in graph_run.py.
        """
        # Given: the source of graph_run.py; When: it is searched; Then: no list of steps or connections is scanned in it
        with open(os.path.join(REPO, "graph_run.py"), encoding="utf-8") as fp:
            source = fp.read()
        for forbidden in ('graph["nodes"]', 'graph["edges"]', 'graph.get("nodes")', 'graph.get("edges")'):
            self.assertFalse(forbidden in source, "graph_run.py still contains %r" % forbidden)
        # And: the files of TC-RUN-016 to 019 and 030 to 039 are unchanged against goal/v4
        commit = oracle()["header"]["commit"]
        diff = git("diff", "--stat", commit, "HEAD", "--", "tests/acceptance/test_graph_run.py", "tests/acceptance/test_graph_run_stages.py")
        self.assertEqual(diff.stdout.strip(), "")


ALONE = {"networkx", "graph_rule_set", "graph_run"}


def foreign_imports(source):
    """the top-level names of every module the source imports (inside functions and try blocks too) that are not of the standard library or ALONE"""
    names = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            # `from . import x` names x; `from .m import y` and `from m import y` name m
            names += [alias.name for alias in node.names] if node.level and not node.module else [node.module]
    return sorted({n.split(".")[0] for n in names} - set(sys.stdlib_module_names) - ALONE)


class StandsOnItsOwn(unittest.TestCase):
    @mark.req("REQ-RUN-047")
    def test_the_graph_run_imports_only_the_standard_library_networkx_and_the_rule_set(self):
        """TC-RUN-049 (A-190): graph_run.py and graph_rule_set.py import only the standard library, networkx and each other.

        Example: `from .graph_model import order_of` in graph_run.py is reported as ["graph_model"].
        """
        # Given: the sound twin, a module that imports graph_model (TR-RUN-007)
        self.assertEqual(foreign_imports("try:\n    from .graph_model import order_of\nexcept ImportError:\n    import graph_rule_set\n"), ["graph_model"])
        for module in ("graph_run.py", "graph_rule_set.py"):
            with self.subTest(module=module):
                # When: every import statement of the module is read
                with open(os.path.join(REPO, module), encoding="utf-8") as fp:
                    found = foreign_imports(fp.read())
                # Then: none names a module outside the standard library, networkx and the two
                self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
