"""
IF-203 provider (workflow_library.py), REQ-WFM-002, REQ-WFM-003, REQ-WFM-004, REQ-WFM-026: versioned library with lifecycle, graph rules and estimate,
on the real Storage (IF-102) with the file backend. Run: python tests/test_workflow_library.py
"""
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from storage import Storage                      # noqa: E402
from storage_files import FileBackend            # noqa: E402
from workflow_library import WorkflowLibrary, WorkflowLibraryError   # noqa: E402

COSTS = {"search": {"seconds": 2.0, "calls": 0, "tokens": 0}, "judge": {"seconds": 5.0, "calls": 3, "tokens": 1500}}
LOOKUP = {"nodes": [{"id": "question", "kind": "data"}, {"id": "search", "kind": "process"}, {"id": "hits", "kind": "data"},
                    {"id": "judge", "kind": "process"}, {"id": "verdict", "kind": "data"}],
          "edges": [{"from": "question", "to": "search"}, {"from": "search", "to": "hits"}, {"from": "hits", "to": "judge"}, {"from": "judge", "to": "verdict"}]}


def edited(note):
    doc = {"nodes": [dict(n) for n in LOOKUP["nodes"]], "edges": list(LOOKUP["edges"])}
    doc["nodes"][3]["note"] = note
    return doc


def error_of(call):
    try:
        call()
    except WorkflowLibraryError as err:
        return err
    raise AssertionError("no WorkflowLibraryError raised")


class WorkflowLibraryTest(unittest.TestCase):
    def setUp(self):
        self.lib = WorkflowLibrary(Storage(FileBackend(tempfile.mkdtemp())), costs=COSTS)

    def test_versions_diff_and_restore(self):                       # REQ-WFM-002
        lib = self.lib
        self.assertEqual(lib.save("workflows", "lookup", LOOKUP, "anna"), {"version": 1})
        self.assertEqual(lib.save("workflows", "lookup", edited("x"), "ben"), {"version": 2})
        self.assertEqual(lib.diff("workflows", "lookup", 1, 2)["nodes_changed"], ["judge"])
        self.assertEqual(lib.restore("workflows", "lookup", 1, "anna"), {"version": 3})
        entry = lib.read("workflows", "lookup")
        self.assertEqual((entry["doc"], entry["status"]), (LOOKUP, "draft"))
        self.assertEqual([h["author"] for h in lib.history("workflows", "lookup")], ["anna", "ben", "anna"])
        self.assertEqual(lib.read("workflows", "lookup", 2)["doc"], edited("x"))      # old versions never change

    def test_a_stale_version_is_a_conflict_and_unknown_things_are_not_found(self):
        self.lib.save("workflows", "lookup", LOOKUP, "anna")
        err = error_of(lambda: self.lib.save("workflows", "lookup", edited("x"), "ben", expected_version=0))
        self.assertEqual((err.code, err.detail), ("conflict", {"current": 1}))
        self.assertEqual(error_of(lambda: self.lib.read("workflows", "nope")).code, "not_found")
        self.assertEqual(error_of(lambda: self.lib.list_ids("recipes")).code, "not_found")
        self.assertEqual(self.lib.list_ids("workflows"), ["lookup"])

    def test_a_broken_graph_is_refused_with_the_rule(self):         # REQ-WFM-003, REQ-WFM-004
        cyc = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
        adj = {"nodes": [{"id": "a", "kind": "data"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}]}
        ses = {"nodes": [{"id": "debate", "kind": "process", "session": True}], "edges": []}
        for doc, rule in ((cyc, "cycle"), (adj, "adjacent_data_nodes"), (ses, "session_stopping_criterion")):
            err = error_of(lambda: self.lib.save("workflows", "bad", doc, "anna"))
            self.assertEqual((err.code, err.rule), ("invalid", rule))
        self.assertEqual(error_of(lambda: self.lib.save("workflows", "bad", cyc, "anna")).detail, ["p", "d", "p"])     # the cycle is named
        self.assertEqual(self.lib.list_ids("workflows"), [])

    def test_every_accepted_generated_graph_has_a_topological_order(self):    # TC-WFM-003 property test; the generator is seeded, it is no statistical check
        import random
        rng = random.Random(7)
        accepted = refused = 0
        for n in range(300):
            nodes = [{"id": "n%d" % i, "kind": rng.choice(["process", "data"])} for i in range(rng.randint(2, 8))]
            edges = [{"from": a["id"], "to": b["id"]} for a in nodes for b in nodes if a is not b and a["kind"] != b["kind"] and rng.random() < 0.25]
            try:
                self.lib.save("workflows", "g%d" % n, {"nodes": nodes, "edges": edges}, "anna")
            except WorkflowLibraryError as err:
                self.assertEqual((err.code, err.rule), ("invalid", "cycle"))      # alternating kinds only, so a cycle is the one thing that can break
                refused += 1
                continue
            accepted += 1
            order = self.lib.estimate("g%d" % n)["order"]
            self.assertEqual(sorted(order), sorted(x["id"] for x in nodes if x["kind"] == "process"))
            position = {pid: i for i, pid in enumerate(order)}
            succ = {x["id"]: [e["to"] for e in edges if e["from"] == x["id"]] for x in nodes}
            for p in order:                                  # p -> data -> q: p comes before q
                for d in succ[p]:
                    for q in succ[d]:
                        self.assertLess(position[p], position[q])
        self.assertGreater(accepted, 20)
        self.assertGreater(refused, 20)

    def test_promotion_needs_specification_and_benchmark(self):     # REQ-WFM-002, REQ-WFM-006 (the gate itself)
        lib = self.lib
        lib.save("workflows", "lookup", LOOKUP, "anna")
        err = error_of(lambda: lib.set_status("lookup", "tested", "anna"))
        self.assertEqual((err.code, err.detail), ("not_promotable", ["specification", "benchmark"]))
        lib.attach("lookup", "specification", {"inputs": "question"})
        self.assertEqual(error_of(lambda: lib.set_status("lookup", "trusted", "anna")).detail, ["benchmark"])
        lib.attach("lookup", "benchmark", {"suite": "verdicts"})
        self.assertEqual(lib.set_status("lookup", "tested", "anna"), {"status": "tested"})
        self.assertEqual(lib.read("workflows", "lookup")["status"], "tested")
        self.assertEqual(lib.set_status("lookup", "retired", "anna"), {"status": "retired"})
        self.assertEqual(error_of(lambda: lib.set_status("lookup", "wild", "anna")).rule, "status")
        self.assertEqual(error_of(lambda: lib.set_status("nope", "draft", "anna")).code, "not_found")

    def test_the_lifecycle_survives_a_restart_and_every_change_is_kept(self):     # A-15: table workflow_meta
        storage = Storage(FileBackend(tempfile.mkdtemp()))
        first = WorkflowLibrary(storage, costs=COSTS)
        first.save("workflows", "lookup", LOOKUP, "anna")
        first.attach("lookup", "specification", {"inputs": "question"})
        first.attach("lookup", "benchmark", {"suite": "verdicts"})
        first.set_status("lookup", "tested", "ben")
        second = WorkflowLibrary(storage, costs=COSTS)
        self.assertEqual(second.read("workflows", "lookup")["status"], "tested")
        self.assertEqual(second.set_status("lookup", "trusted", "anna"), {"status": "trusted"})       # specification and benchmark were kept
        versions = storage.history("workflow_meta", "lookup")
        self.assertEqual([v["author"] for v in versions][-2:], ["ben", "anna"])
        self.assertEqual(storage.get("workflow_meta", "lookup", 1)["doc"]["status"], "draft")        # an old version never changes

    def test_the_time_from_idea_to_promotion_is_recorded(self):     # REQ-WFM-007, TC-WFM-007: the idea is the first version
        lib = self.lib
        lib.save("workflows", "lookup", LOOKUP, "anna")
        lib.save("workflows", "lookup", edited("x"), "ben")
        self.assertEqual(lib.promotion_record("lookup"), {"idea": lib.history("workflows", "lookup")[0]["time"], "promoted": None})
        lib.attach("lookup", "specification", {"inputs": "question"})
        lib.attach("lookup", "benchmark", {"suite": "verdicts"})
        self.assertIsNone(lib.promotion_record("lookup")["promoted"])             # attaching is no promotion
        lib.set_status("lookup", "tested", "anna")
        lib.set_status("lookup", "trusted", "anna")
        record = lib.promotion_record("lookup")
        meta = lib._storage.history("workflow_meta", "lookup")
        self.assertEqual(record["idea"], lib.history("workflows", "lookup")[0]["time"])
        self.assertEqual(record["promoted"], meta[-2]["time"])                    # the first step out of draft, not the later one
        self.assertLessEqual(record["idea"], record["promoted"])
        self.assertEqual(error_of(lambda: lib.promotion_record("nope")).code, "not_found")

    def test_an_estimate_above_the_budget_is_named_before_the_run(self):       # REQ-WFM-009, TC-WFM-009 (the refusal itself is the run of IF-202)
        lib = self.lib
        lib.save("workflows", "lookup", LOOKUP, "anna")
        self.assertEqual(lib.check_budget("lookup", {"seconds": 10, "calls": 3, "tokens": 1500})["exceeded"], [])        # equal fits
        self.assertEqual(lib.check_budget("lookup", {"calls": 1})["exceeded"], ["calls"])                                # absent keys are unlimited
        checked = lib.check_budget("lookup", {"seconds": 6, "calls": 2, "tokens": 9999})
        self.assertEqual(checked["exceeded"], ["seconds", "calls"])
        self.assertEqual(checked["estimate"], lib.estimate("lookup"))
        self.assertEqual(lib.check_budget("lookup", {})["exceeded"], [])
        self.assertEqual(error_of(lambda: lib.check_budget("nope", {})).code, "not_found")

    def test_a_workflow_names_a_character_variant_or_none(self):               # REQ-WFM-010, TC-WFM-010
        lib = self.lib
        lib.save("workflows", "lookup", LOOKUP, "anna")
        lib.save("workflows", "debate", dict(edited("x"), variant="serious"), "anna")
        self.assertIsNone(lib.variant_of("lookup"))
        self.assertEqual(lib.variant_of("debate"), "serious")
        lib.save("workflows", "debate", edited("y"), "anna")                       # version 2 names none, version 1 still names one
        self.assertEqual((lib.variant_of("debate", version=1), lib.variant_of("debate")), ("serious", None))
        err = error_of(lambda: lib.save("workflows", "bad", dict(LOOKUP, variant=7), "anna"))
        self.assertEqual((err.code, err.rule), ("invalid", "variant"))

    def test_estimate_order_critical_path_and_session_cycles(self):     # REQ-WFM-009 (the numbers), IF-203 golden 3
        lib = self.lib
        lib.save("workflows", "lookup", LOOKUP, "anna")
        est = lib.estimate("lookup")
        self.assertEqual((est["order"], est["critical_path"]), (["search", "judge"], ["search", "judge"]))
        self.assertEqual((est["seconds"], est["calls"], est["tokens"]), (7.0, 3, 1500))
        debate = {"nodes": [dict(n) for n in LOOKUP["nodes"]], "edges": list(LOOKUP["edges"])}
        debate["nodes"][3].update({"session": True, "stop": {"max_cycles": 4}})
        lib.save("workflows", "debate", debate, "anna")
        est = lib.estimate("debate")
        self.assertEqual((est["calls"], est["tokens"], est["seconds"]), (12, 6000, 22.0))

    def test_an_estimate_of_200_nodes_takes_under_a_second(self):      # IF-203 bound
        import time
        nodes, edges = [{"id": "d0", "kind": "data"}], []
        for i in range(1, 100):
            nodes += [{"id": "p%d" % i, "kind": "process"}, {"id": "d%d" % i, "kind": "data"}]
            edges += [{"from": "d%d" % (i - 1), "to": "p%d" % i}, {"from": "p%d" % i, "to": "d%d" % i}]
        self.lib.save("workflows", "long", {"nodes": nodes, "edges": edges}, "anna")
        started = time.time()
        self.assertEqual(len(self.lib.estimate("long")["order"]), 99)
        self.assertLess(time.time() - started, 1.0)


if __name__ == "__main__":
    unittest.main()
