"""IF-102 storage interface: the contract suite runs against the mock (stage 1) and the real provider (stage 2, skipped until N-3 is integrated).
Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_102_storage.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HELPERS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers")
sys.path.insert(0, HELPERS)

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import StorageError               # noqa: E402

IF = "IF-102"


def workflow(*extra_edges, nodes=None):
    base = nodes or [{"id": "claim", "kind": "data"}, {"id": "check", "kind": "process"}, {"id": "verdict", "kind": "data"}]
    edges = [{"from": "claim", "to": "check"}, {"from": "check", "to": "verdict"}] + list(extra_edges)
    return {"nodes": base, "edges": edges}


def refused(test, store, doc, rule):
    with test.assertRaises(StorageError) as caught:
        store.put("workflows", "bad", doc, "anna")
    test.assertEqual((caught.exception.code, caught.exception.rule), ("invalid", rule))
    test.assertEqual(store.ids("workflows"), [])


@contract
class StorageContract(unittest.TestCase):
    @mark.req("IF-102", "REQ-DB-003")
    @each_provider(IF)
    def test_every_put_is_a_new_immutable_version(self, store):
        """TC-IF-102-01 golden 1: version 1, version 2, and version 1 reads back unchanged."""
        first, second = workflow(), workflow()
        second["nodes"][1]["note"] = "edited"
        self.assertEqual(store.put("workflows", "lookup", first, "anna"), {"version": 1})
        self.assertEqual(store.put("workflows", "lookup", second, "ben"), {"version": 2})
        self.assertEqual(store.get("workflows", "lookup", version=1)["doc"], first)
        self.assertEqual(store.get("workflows", "lookup")["doc"], second)
        self.assertEqual([(h["version"], h["author"]) for h in store.history("workflows", "lookup")], [(1, "anna"), (2, "ben")])

    @mark.req("IF-102", "REQ-DB-004")
    @each_provider(IF)
    def test_graph_rules_are_checked_on_write(self, store):
        """TC-IF-102-02 golden 2: each broken rule is refused with its name and nothing is stored."""
        refused(self, store, workflow({"from": "claim", "to": "verdict"}), "adjacent_data_nodes")
        refused(self, store, workflow({"from": "check", "to": "check2"}, nodes=[{"id": "claim", "kind": "data"}, {"id": "check", "kind": "process"},
                                                                             {"id": "verdict", "kind": "data"}]), "node_identity")
        refused(self, store, {"nodes": [{"id": "a", "kind": "data"}, {"id": "a", "kind": "data"}], "edges": []}, "node_identity")
        refused(self, store, {"nodes": [{"id": "p", "kind": "process"}, {"id": "q", "kind": "process"}], "edges": [{"from": "p", "to": "q"}]},
                "adjacent_process_nodes")
        refused(self, store, {"nodes": [{"id": "debate", "kind": "process", "session": True}], "edges": []}, "session_stopping_criterion")

    @mark.req("IF-102", "REQ-DB-004")
    @each_provider(IF)
    def test_a_cycle_is_named(self, store):
        """TC-IF-102-03 golden 3: a cycle p->d->p is refused as a cycle and named by its ids, first id repeated at the end."""
        doc = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
        with self.assertRaises(StorageError) as caught:
            store.put("workflows", "loop", doc, "anna")
        self.assertEqual((caught.exception.code, caught.exception.rule), ("invalid", "cycle"))
        self.assertEqual(caught.exception.detail[0], caught.exception.detail[-1])
        self.assertEqual(set(caught.exception.detail), {"p", "d"})
        doc = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}, {"id": "q", "kind": "process"}],
               "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "q"}, {"from": "q", "to": "d"}]}
        with self.assertRaises(StorageError) as caught:
            store.put("workflows", "loop2", doc, "anna")
        self.assertEqual(caught.exception.rule, "cycle")
        self.assertEqual(set(caught.exception.detail), {"d", "q"})
        self.assertEqual(store.ids("workflows"), [])

    @mark.req("IF-102")
    @each_provider(IF)
    def test_expected_version_and_unknown_things(self, store):
        """TC-IF-102-04: conflict names the current version; unknown id, version and table are refused; a new record accepts expected_version 0."""
        self.assertEqual(store.put("workflows", "w", workflow(), "anna", expected_version=0), {"version": 1})
        with self.assertRaises(StorageError) as caught:
            store.put("workflows", "w", workflow(), "anna", expected_version=3)
        self.assertEqual((caught.exception.code, caught.exception.detail), ("conflict", {"current": 1}))
        for call in (lambda: store.get("workflows", "none"), lambda: store.get("workflows", "w", version=2), lambda: store.history("workflows", "none")):
            with self.assertRaises(StorageError) as caught:
                call()
            self.assertEqual(caught.exception.code, "not_found")
        with self.assertRaises(StorageError) as caught:
            store.get("nonsense", "x")
        self.assertEqual(caught.exception.code, "unknown_table")

    @mark.req("IF-102", "REQ-DB-014")
    @each_provider(IF)
    def test_delete_only_where_allowed(self, store):
        """TC-IF-102-05: versioned tables refuse delete; a memory record can be deleted and is gone."""
        store.put("workflows", "w", workflow(), "anna")
        with self.assertRaises(StorageError) as caught:
            store.delete("workflows", "w", "anna")
        self.assertEqual(caught.exception.code, "immutable")
        store.put("memory", "m1", {"text": "likes tea", "source": "chat"}, "anna")
        store.delete("memory", "m1", "anna")
        self.assertEqual(store.ids("memory"), [])

    @mark.req("IF-102", "REQ-DB-006")
    @each_provider(IF)
    def test_subscribers_are_told_of_every_write(self, store):
        """TC-IF-102-06: a subscriber gets one notice per write; after unsubscribe none."""
        seen = []
        stop = store.subscribe("presets", seen.append)
        store.put("presets", "smile", {"weight": 1}, "anna")
        store.put("presets", "smile", {"weight": 2}, "ben")
        stop()
        store.put("presets", "smile", {"weight": 3}, "anna")
        self.assertEqual([(s["id"], s["version"], s["author"]) for s in seen], [("smile", 1, "anna"), ("smile", 2, "ben")])

    @mark.req("IF-102", "REQ-DB-014")
    @each_provider(IF)
    def test_tasks_and_memos_read_back_exactly(self, store):
        """TC-IF-102-07: text with odd characters comes back byte for byte (the word-for-word recital of FR-28)."""
        text = "Call Zoë at 9:00 – bring \"the\" notes\n\tdone ✓"
        store.put("memos", "x", {"text": text}, "anna")
        self.assertEqual(store.get("memos", "x")["doc"]["text"], text)

    @mark.req("IF-102", "REQ-DB-010", "REQ-DB-015")
    @each_provider(IF)
    def test_run_results_and_source_trust_are_tables(self, store):
        """TC-IF-102-08 (F-5): a run result and a source trust value are written and read back as versions; the second write of a source is version 2."""
        run = {"workflow": "lookup", "workflow_version": 1, "model_pin": "MP-light", "benchmark_version": "B1"}
        self.assertEqual(store.put("runs", "r1", run, "harness"), {"version": 1})
        self.assertEqual(store.get("runs", "r1")["doc"], run)
        self.assertEqual(store.put("source_trust", "example.org", {"trust": 0.5}, "owner"), {"version": 1})
        self.assertEqual(store.put("source_trust", "example.org", {"trust": 0.7}, "owner"), {"version": 2})
        self.assertEqual(store.get("source_trust", "example.org", version=1)["doc"], {"trust": 0.5})


if __name__ == "__main__":
    unittest.main()
