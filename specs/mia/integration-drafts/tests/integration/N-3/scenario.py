"""Scenario of N-3 (Database): tables defined by N-3.2 and N-3.3, the one door of N-3.1 (protected).
Workflows are written, edited and refused when broken; votes, memory and history records are stored, read back and deleted where allowed; a listener hears
every write. Step 0 runs it on the mocks; steps 1 to 3 swap in the Graph tables, the Record tables and the Storage layer. The real PostgreSQL stack
(container, scrypt hash, backup) is covered by the stage 3 cases TC-N3-001, -005 to -008 and -012, which need podman and are not in this scenario."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "helpers", "mocks"))
from errors import StorageError  # noqa: E402

LOOKUP = {"nodes": [{"id": "question", "kind": "data"}, {"id": "search", "kind": "process"}, {"id": "hits", "kind": "data"}],
          "edges": [{"from": "question", "to": "search"}, {"from": "search", "to": "hits"}]}
CYCLE = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}

MARKS = {0: [], 1: ["REQ-DB-004", "REQ-DB-011"], 2: ["REQ-DB-010", "REQ-DB-012", "REQ-DB-013", "REQ-DB-014", "REQ-DB-015"],
         3: ["REQ-DB-001", "REQ-DB-002", "REQ-DB-003", "REQ-DB-004", "REQ-DB-016", "REQ-DB-017"]}


def code_of(call):
    try:
        call()
    except StorageError as err:
        return err.code, err.rule
    raise AssertionError("no StorageError raised")


def run(p, t):
    storage, graphs, records = p["IF-102"], p["IF-301"], p["IF-302"]

    # the table definitions: workflows and context graphs are versioned and never deleted
    t.assertEqual({k for k, v in graphs.definitions().items() if v["versioned"] and not v["deletable"]}, {"workflows", "context_graphs"})
    t.assertIsNone(graphs.validate("workflows", LOOKUP))
    t.assertEqual(graphs.validate("workflows", CYCLE)["rule"], "cycle")

    # a workflow: version 1, an edit is version 2, the former version is unchanged, history names the authors
    t.assertEqual(storage.put("workflows", "lookup", LOOKUP, "anna"), {"version": 1})
    edited = dict(LOOKUP, note="second")
    t.assertEqual(storage.put("workflows", "lookup", edited, "ben"), {"version": 2})
    t.assertEqual(storage.get("workflows", "lookup", 1)["doc"], LOOKUP)
    t.assertEqual([(h["version"], h["author"]) for h in storage.history("workflows", "lookup")], [(1, "anna"), (2, "ben")])

    # a broken workflow is refused with the rule named and changes nothing (TB-edit)
    t.assertEqual(code_of(lambda: storage.put("workflows", "bad", CYCLE, "anna")), ("invalid", "cycle"))
    t.assertEqual(storage.ids("workflows"), ["lookup"])
    t.assertEqual(code_of(lambda: storage.delete("workflows", "lookup", "anna"))[0], "immutable")

    # record tables: a complete vote is accepted, an unknown category and a missing field are named
    vote = {"user": "anna", "subject": "m2", "category": "answer_quality", "value": 1}
    t.assertIsNone(records.validate("votes", vote))
    t.assertEqual(records.validate("votes", dict(vote, category="mood"))["rule"], "category")
    t.assertEqual(records.validate("memory", {"text": "likes tea"})["detail"], "source")

    # records are stored, read back equal and deleted where the table allows it
    for n in range(100):
        storage.put("votes", "v%03d" % n, dict(vote, subject="m%d" % n), "anna")
    t.assertEqual(len(storage.ids("votes")), 100)
    t.assertEqual(storage.get("votes", "v007")["doc"]["subject"], "m7")
    run = {"workflow": "lookup", "workflow_version": 1, "model_pin": "MP-light", "benchmark_version": "B1"}
    t.assertIsNone(records.validate("runs", run))
    t.assertEqual(records.validate("runs", {k: v for k, v in run.items() if k != "benchmark_version"})["detail"], "benchmark_version")
    t.assertEqual(storage.put("runs", "r1", run, "harness"), {"version": 1})
    t.assertEqual(storage.get("runs", "r1")["doc"], run)
    storage.put("memory", "k1", {"text": "likes tea", "source": "chat"}, "anna")
    storage.delete("memory", "k1", "anna")
    t.assertEqual(code_of(lambda: storage.get("memory", "k1"))[0], "not_found")

    # a second connection hears every write
    heard = []
    stop = storage.subscribe("tasks", heard.append)
    storage.put("tasks", "t1", {"text": "water the plants"}, "anna")
    stop()
    storage.put("tasks", "t2", {"text": "later"}, "anna")
    t.assertEqual([(e["id"], e["author"]) for e in heard], [("t1", "anna")])
