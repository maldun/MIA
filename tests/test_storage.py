"""The Storage layer on the file backend (N-3.1 T-01, T-02): TC-SLY-002, -003, -004, -006 (files) and the behaviour of IF-102. Run with: python tests/test_storage.py"""
import os
import random
import shutil
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from markers import mark                         # noqa: E402
from storage import Storage, StorageError, validate  # noqa: E402
from storage_files import FileBackend            # noqa: E402

LOOKUP = {"nodes": [{"id": "q", "kind": "data"}, {"id": "p", "kind": "process"}, {"id": "a", "kind": "data"}],
          "edges": [{"from": "q", "to": "p"}, {"from": "p", "to": "a"}]}
CYCLE = {"nodes": [{"id": "p", "kind": "process"}, {"id": "d", "kind": "data"}], "edges": [{"from": "p", "to": "d"}, {"from": "d", "to": "p"}]}
ONE_OF_EACH = {"workflows": LOOKUP, "context_graphs": LOOKUP, "history": {"role": "user", "text": "hi"}, "memory": {"text": "likes tea", "source": "chat"},
               "votes": {"user": "anna", "subject": "m1", "category": "service", "value": -1}, "tasks": {"text": "water the plants"}, "memos": {"text": "x\ty"},
               "accounts": {"name": "anna", "hash": "h"}, "presets": {"name": "calm"}, "gestures": {"name": "wave"},
               "runs": {"workflow": "lookup", "workflow_version": 1, "model_pin": "MP-light", "benchmark_version": "B1"}, "source_trust": {"trust": 0.5}}


def code_of(call):
    try:
        call()
    except StorageError as err:
        return err.code, err.rule
    raise AssertionError("no StorageError raised")


class StorageBehaviour:
    """The behaviour of the Storage layer, the same on every backend. A test class mixes it with unittest.TestCase and says
    new_backend(label): a backend that is empty (a different label is a different, independent store) and reopen(): a new backend on the same data."""

    def setUp(self):
        self.store = Storage(self.new_backend("main"))

    @mark.req("REQ-SLY-002")
    def test_a_record_of_each_table_reads_back_equal(self):
        """TC-SLY-002 (file backend)."""
        for table, doc in ONE_OF_EACH.items():
            self.store.put(table, "k1", doc, "anna")
            entry = self.store.get(table, "k1")
            self.assertEqual((entry["doc"], entry["version"], entry["author"], entry["id"]), (doc, 1, "anna", "k1"), table)

    @mark.req("REQ-SLY-002")
    def test_a_new_storage_on_the_same_folder_sees_the_records(self):
        """The records are on disk, not in memory."""
        self.store.put("memory", "m", {"text": "t", "source": "s"}, "anna")
        again = Storage(self.reopen())
        self.assertEqual(again.ids("memory"), ["m"])
        self.assertEqual(again.get("memory", "m")["doc"], {"text": "t", "source": "s"})

    @mark.req("REQ-SLY-002")
    def test_ids_with_odd_characters_and_text_byte_for_byte(self):
        """An id with a slash, a dot or a non-ASCII letter is a record, not a path; the text comes back unchanged."""
        text = "Call Zoë at 9:00 – bring \"the\" notes\n\tdone ✓"
        for record_id in ("a/b", "..", "ä ö", "x" * 150):
            self.store.put("memos", record_id, {"text": text}, "anna")
            self.assertEqual(self.store.get("memos", record_id)["doc"]["text"], text)
        self.assertEqual(sorted(self.store.ids("memos")), sorted(["a/b", "..", "ä ö", "x" * 150]))

    @mark.req("REQ-SLY-003")
    @mark.statistical
    def test_versions_run_without_gap_and_never_change(self):
        """TC-SLY-003: 500 random sequences (seeds 1 to 500) of put, get(version) and history."""
        for seed in range(1, 501):
            rng = random.Random(seed)
            store = Storage(self.new_backend("s%d" % seed))
            written = {}
            for _ in range(rng.randint(1, 8)):
                rid = rng.choice("abc")
                doc = {"text": "v%d" % rng.randint(0, 99)}
                number = store.put("tasks", rid, doc, rng.choice(("anna", "ben")))["version"]
                written.setdefault(rid, []).append(doc)
                self.assertEqual(number, len(written[rid]), seed)
                for rid_, docs in written.items():
                    self.assertEqual([h["version"] for h in store.history("tasks", rid_)], list(range(1, len(docs) + 1)), seed)
                    for k, expected in enumerate(docs, 1):
                        self.assertEqual(store.get("tasks", rid_, version=k)["doc"], expected, (seed, rid_, k))

    @mark.req("REQ-SLY-003")
    def test_conflict_not_found_and_unknown_table(self):
        """IF-102 errors: nothing changes after a refusal."""
        self.store.put("tasks", "t", {"text": "a"}, "anna")
        self.assertEqual(code_of(lambda: self.store.put("tasks", "t", {"text": "b"}, "anna", expected_version=3))[0], "conflict")
        self.assertEqual(self.store.get("tasks", "t")["version"], 1)
        self.assertEqual(self.store.put("tasks", "new", {"text": "x"}, "anna", expected_version=0), {"version": 1})
        self.assertEqual(code_of(lambda: self.store.get("tasks", "ghost"))[0], "not_found")
        self.assertEqual(code_of(lambda: self.store.get("tasks", "t", version=2))[0], "not_found")
        self.assertEqual(code_of(lambda: self.store.history("tasks", "ghost"))[0], "not_found")
        self.assertEqual(code_of(lambda: self.store.ids("nope"))[0], "unknown_table")
        self.assertEqual(code_of(lambda: self.store.put("nope", "x", {}, "anna"))[0], "unknown_table")

    @mark.req("REQ-SLY-003")
    def test_the_conflict_names_the_current_version(self):
        self.store.put("tasks", "t", {"text": "a"}, "anna")
        try:
            self.store.put("tasks", "t", {"text": "b"}, "anna", expected_version=5)
        except StorageError as err:
            self.assertEqual(err.detail, {"current": 1})

    @mark.req("REQ-SLY-003")
    def test_only_the_tables_that_allow_it_can_be_deleted(self):
        """The definitions of IF-301 and IF-302 decide: memory is deletable, workflows and votes are not."""
        self.store.put("memory", "m", {"text": "t", "source": "s"}, "anna")
        self.store.delete("memory", "m", "anna")
        self.assertEqual(self.store.ids("memory"), [])
        for table in ("workflows", "votes", "accounts"):
            self.store.put(table, "k", ONE_OF_EACH[table], "anna")
            self.assertEqual(code_of(lambda: self.store.delete(table, "k", "anna"))[0], "immutable", table)
            self.assertEqual(self.store.ids(table), ["k"])
        self.assertEqual(code_of(lambda: self.store.delete("memory", "m", "anna"))[0], "not_found")

    @mark.req("REQ-SLY-006")
    def test_a_subscriber_is_told_once_per_write_and_not_after_unsubscribe(self):
        """TC-SLY-006 (files, in process): table, id, version and author; one notice per write."""
        heard = []
        stop = self.store.subscribe("tasks", heard.append)
        self.store.put("tasks", "t", {"text": "a"}, "anna")
        self.store.put("tasks", "t", {"text": "b"}, "ben")
        self.store.put("memos", "m", {"text": "other table"}, "anna")
        self.assertEqual(heard, [{"table": "tasks", "id": "t", "version": 1, "author": "anna"}, {"table": "tasks", "id": "t", "version": 2, "author": "ben"}])
        stop()
        self.store.put("tasks", "t", {"text": "c"}, "anna")
        self.assertEqual(len(heard), 2)

    @mark.req("REQ-SLY-006")
    def test_a_raising_subscriber_does_not_stop_the_others_or_the_write(self):
        """Finding F2 of the verification: one bad subscriber is logged and skipped.
        Example: subscribers [raises, records]; put("tasks", "t") returns version 1 and the second one hears version 1."""
        # Given: a subscriber that raises before one that records
        def broken(event):
            raise RuntimeError("a bad page")
        heard = []
        self.store.subscribe("tasks", broken)
        self.store.subscribe("tasks", heard.append)
        # When: two writes
        with self.assertLogs("storage", "ERROR"):
            first = self.store.put("tasks", "t", {"text": "a"}, "anna")
            self.store.put("tasks", "t", {"text": "b"}, "anna")
        # Then: both writes return and the second subscriber hears both
        self.assertEqual(first, {"version": 1})
        self.assertEqual([e["version"] for e in heard], [1, 2])

    @mark.req("REQ-SLY-006")
    def test_a_delete_is_a_change_and_is_told_with_version_none(self):
        """Finding F7 of the verification, decision D-158: a delete sends a notice, as IF-102 says "after every write".
        Example: delete("memos", "m", "ben") tells a subscriber {"table": "memos", "id": "m", "version": None, "author": "ben"}."""
        # Given: a memo and a subscriber of the memos
        self.store.put("memos", "m", {"text": "x"}, "anna")
        heard = []
        self.store.subscribe("memos", heard.append)
        # When: the memo is deleted, and a refused delete follows
        self.store.delete("memos", "m", "ben")
        code_of(lambda: self.store.delete("memos", "m", "ben"))
        # Then: one notice, for the delete that happened
        self.assertEqual(heard, [{"table": "memos", "id": "m", "version": None, "author": "ben"}])

    @mark.req("REQ-SLY-006")
    def test_a_notice_reaches_a_subscriber_on_another_thread_within_2_s(self):
        """TC-SLY-006: the writer is on one thread, the subscriber's callback runs and is seen from another."""
        got, seen = [], threading.Event()
        self.store.subscribe("tasks", lambda event: (got.append(event), seen.set()))
        started = time.perf_counter()
        threading.Thread(target=lambda: self.store.put("tasks", "t", {"text": "a"}, "anna")).start()
        self.assertTrue(seen.wait(2))
        self.assertLess(time.perf_counter() - started, 2)
        self.assertEqual(got[0]["author"], "anna")

    @mark.req("REQ-SLY-003")
    def test_parallel_writers_never_get_the_same_version(self):
        """Ten threads put to one record: versions 1 to 10 each once."""
        results = []
        threads = [threading.Thread(target=lambda n=n: results.append(self.store.put("tasks", "t", {"text": str(n)}, "anna")["version"])) for n in range(10)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(sorted(results), list(range(1, 11)))

    @mark.req("REQ-SLY-004")
    def test_invalid_documents_are_refused_with_the_rule_and_nothing_is_stored(self):
        """TC-SLY-004: a cycle, two adjacent data nodes and a vote with category mood are refused; the valid workflow is version 1."""
        adjacent = {"nodes": [{"id": "a", "kind": "data"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}]}
        vote = dict(ONE_OF_EACH["votes"], category="mood")
        self.assertEqual(code_of(lambda: self.store.put("workflows", "bad", CYCLE, "anna")), ("invalid", "cycle"))
        self.assertEqual(code_of(lambda: self.store.put("context_graphs", "bad", adjacent, "anna")), ("invalid", "adjacent_data_nodes"))
        self.assertEqual(code_of(lambda: self.store.put("votes", "v", vote, "anna")), ("invalid", "category"))
        self.assertEqual((self.store.ids("workflows"), self.store.ids("context_graphs"), self.store.ids("votes")), ([], [], []))
        self.assertEqual(self.store.put("workflows", "lookup", LOOKUP, "anna"), {"version": 1})

    @mark.req("REQ-SLY-004")
    def test_a_nul_character_is_refused_on_every_backend(self):
        """Finding F9 of the verification: PostgreSQL cannot store NUL in text, so no backend takes it, and the error is the layer's own.
        Example: put("memos", "m", {"text": "a\\x00b"}) is ("invalid", "schema") and nothing is stored."""
        # Given: NUL in a text, in a key, in the id and in the author
        calls = [lambda: self.store.put("memos", "m", {"text": "a\x00b"}, "anna"), lambda: self.store.put("memos", "m", {"te\x00xt": "a"}, "anna"),
                 lambda: self.store.put("memos", "m\x00", {"text": "a"}, "anna"), lambda: self.store.put("memos", "m", {"text": "a"}, "an\x00na")]
        # When / Then: each is refused and nothing is stored
        for call in calls:
            self.assertEqual(code_of(call), ("invalid", "schema"))
        self.assertEqual(self.store.ids("memos"), [])

    @mark.req("REQ-SLY-012", "IF-102")
    def test_the_vote_categories_are_an_operation_of_the_storage(self):
        """D-162: IF-102 offers categories(), read from the record tables inside N-3, so a consumer imports no constant of IF-302.
        Example: categories() gives ["answer_quality", "reactions", "character_behaviour", "service"]."""
        # Given / When: the storage is asked
        categories = self.store.categories()
        # Then: the four vote categories in their order, and a vote of each is accepted
        self.assertEqual(categories, ["answer_quality", "reactions", "character_behaviour", "service"])
        for category in categories:
            self.store.put("votes", category, dict(ONE_OF_EACH["votes"], category=category), "anna")

    @mark.req("REQ-SLY-004")
    def test_a_non_finite_number_or_an_id_that_is_not_text_is_refused_on_every_backend(self):
        """Finding R2 of the re-verification, D-168: the file backend stored NaN and PostgreSQL raised its own error; an id that is not text
        raised a TypeError. Both are the layer's ("invalid", "schema") now, and nothing is stored.
        Example: put("memos", "m", {"text": "a", "score": float("nan")}) and put("memos", 7, {"text": "a"}) are ("invalid", "schema")."""
        # Given: NaN, inf and -inf in a document (also nested in a list), and ids that are not text
        docs = [{"text": "a", "score": float("nan")}, {"text": "a", "score": float("inf")}, {"text": "a", "scores": [1, float("-inf")]}]
        calls = [lambda doc=doc: self.store.put("memos", "m", doc, "anna") for doc in docs]
        calls += [lambda record_id=record_id: self.store.put("memos", record_id, {"text": "a"}, "anna") for record_id in (7, None, b"m", ("m",))]
        # When / Then: each is refused by the layer and nothing is stored
        for call in calls:
            self.assertEqual(code_of(call), ("invalid", "schema"))
        self.assertEqual(self.store.ids("memos"), [])

    @mark.req("REQ-SLY-004")
    def test_a_refused_edit_consumes_no_version(self):
        self.store.put("workflows", "w", LOOKUP, "anna")
        code_of(lambda: self.store.put("workflows", "w", CYCLE, "anna"))
        self.assertEqual(self.store.put("workflows", "w", LOOKUP, "ben"), {"version": 2})

    def refusal_of(self, table, record_id, record):
        """Writes a record that must be refused: returns (rule, detail) and checks that the stored versions stayed as they were."""
        before = {t: {i: len(self.store.history(t, i)) for i in self.store.ids(t)} for t in ("graph_nodes", "graph_edges", "graphs", "skills")}
        with self.assertRaises(StorageError) as caught:
            self.store.put(table, record_id, record, "anna")
        self.assertEqual(caught.exception.code, "invalid")
        after = {t: {i: len(self.store.history(t, i)) for i in self.store.ids(t)} for t in before}
        self.assertEqual(after, before)
        return caught.exception.rule, caught.exception.detail

    @mark.req("REQ-GTB-005", "REQ-GTB-006", "REQ-GTB-013")
    def test_the_graph_records_are_stored_as_versions_and_never_deleted(self):
        """TC-GTB-013 and TC-GTB-016 on the Storage layer: a node, an edge, a header and a skill read back equal; an edit is version 2 and version 1 is unchanged; none can be deleted.

        Example: node n1 with toolbox "t-old" edited to "t-new" -> history [1, 2], version 1 still names "t-old"; delete of n1 -> immutable.
        """
        # Given: one record of each of the four tables
        n1, n2 = {"id": "n1", "data": {"type": "transform", "toolbox_id": "t-old"}}, {"id": "n2", "data": {"type": "data"}}
        e1 = {"id": "e1", "from": "n1", "to": "n2", "data": {"label": "x"}}
        wf = {"id": "wf1", "data": {"kind": "workflow", "context_graph_id": "ctx", "testbench_id": "", "description": "d",
                                    "nodes": [{"id": "n1", "version": 1}, {"id": "n2", "version": 1}], "edges": [{"id": "e1", "version": 1}]}}
        skill = {"id": "lookup", "data": {"command": "/lookup", "workflow_graph_id": "wf1", "context_graph_id": "ctx"}}
        # When: each is written and read back
        for table, record in (("graph_nodes", n1), ("graph_nodes", n2), ("graph_edges", e1), ("graphs", wf), ("skills", skill)):
            self.assertEqual(self.store.put(table, record["id"], record, "anna"), {"version": 1})
            # Then: it reads back equal
            self.assertEqual(self.store.get(table, record["id"])["doc"], record)
        # When: n1 is edited
        n1b = {"id": "n1", "data": {"type": "transform", "toolbox_id": "t-new"}}
        self.assertEqual(self.store.put("graph_nodes", "n1", n1b, "ben"), {"version": 2})
        # Then: both versions exist and version 1 is unchanged
        self.assertEqual([h["version"] for h in self.store.history("graph_nodes", "n1")], [1, 2])
        self.assertEqual(self.store.get("graph_nodes", "n1", version=1)["doc"], n1)
        # And: none of the four tables allows a delete
        for table, record_id in (("graph_nodes", "n1"), ("graph_edges", "e1"), ("graphs", "wf1"), ("skills", "lookup")):
            self.assertEqual(code_of(lambda: self.store.delete(table, record_id, "anna")), ("immutable", None))

    @mark.req("REQ-GTB-016", "REQ-GTB-011", "REQ-GTB-010")
    def test_a_refused_graph_edit_changes_nothing(self):
        """TC-GTB-017 on the Storage layer: an unknown type, a schema break and a member named twice are refused with rule and detail, and the latest version stays 1.

        Example: node n1 edited to type x.unknown -> invalid, unknown_type, "x.unknown"; history of n1 is still [1].
        """
        # Given: a stored graph at version 1
        n1, n2 = {"id": "n1", "data": {"type": "transform", "toolbox_id": "t"}}, {"id": "n2", "data": {"type": "data"}}
        e1 = {"id": "e1", "from": "n1", "to": "n2", "data": {}}
        wf = {"id": "wf1", "data": {"kind": "workflow", "context_graph_id": "ctx", "testbench_id": "", "description": "d",
                                    "nodes": [{"id": "n1", "version": 1}, {"id": "n2", "version": 1}], "edges": [{"id": "e1", "version": 1}]}}
        for table, record in (("graph_nodes", n1), ("graph_nodes", n2), ("graph_edges", e1), ("graphs", wf)):
            self.store.put(table, record["id"], record, "anna")
        # When/Then: each breaking edit is refused with its rule and detail
        self.assertEqual(self.refusal_of("graph_nodes", "n1", {"id": "n1", "data": {"type": "x.unknown"}}), ("unknown_type", "x.unknown"))
        self.assertEqual(self.refusal_of("graph_edges", "e1", {"id": "e1", "from": "n1", "to": "n2", "data": "x"}), ("schema_break", "data"))
        twice = {"id": "wf1", "data": dict(wf["data"], nodes=[{"id": "n1", "version": 1}, {"id": "n1", "version": 1}])}
        self.assertEqual(self.refusal_of("graphs", "wf1", twice)[0], "record_identity")
        # And: the latest versions are still 1 with their content, and a refused write took no number (the next edit is version 2)
        for table, record in (("graph_nodes", n1), ("graph_edges", e1), ("graphs", wf)):
            self.assertEqual(self.store.get(table, record["id"]), dict(self.store.get(table, record["id"]), version=1, doc=record))
        self.assertEqual(self.store.put("graph_nodes", "n1", {"id": "n1", "data": {"type": "transform", "toolbox_id": "t2"}}, "ben"), {"version": 2})

    @mark.req("REQ-GTB-019", "REQ-GTB-020")
    def test_an_edge_and_a_header_must_name_stored_things(self):
        """TC-GTB-020 and TC-GTB-021 on the Storage layer: an edge to a node that is not stored and a header naming a version that is not stored are refused naming the ID; the twins are accepted.

        Example: edge e1 from n1 to n9 with only n1 stored -> unknown_endpoint "n9"; header naming n1 at version 5 of [1, 2] -> unknown_member "n1".
        """
        # Given: n1 stored with versions 1 and 2
        self.store.put("graph_nodes", "n1", {"id": "n1", "data": {"type": "data"}}, "anna")
        self.store.put("graph_nodes", "n1", {"id": "n1", "data": {"type": "data", "value": 1}}, "anna")
        edge = {"id": "e1", "from": "n1", "to": "n9", "data": {}}
        def header(version):
            return {"id": "wf1", "data": {"kind": "workflow", "context_graph_id": "c", "testbench_id": "", "description": "d",
                                          "nodes": [{"id": "n1", "version": version}], "edges": []}}
        # When/Then: the edge to the missing node and the header with version 5 are refused, naming the ID
        self.assertEqual(self.refusal_of("graph_edges", "e1", edge), ("unknown_endpoint", "n9"))
        self.assertEqual(self.refusal_of("graphs", "wf1", header(5)), ("unknown_member", "n1"))
        # And: the same edge after n9 is stored, and the header naming version 2, are accepted
        self.store.put("graph_nodes", "n9", {"id": "n9", "data": {"type": "data"}}, "anna")
        self.assertEqual(self.store.put("graph_edges", "e1", edge, "anna"), {"version": 1})
        self.assertEqual(self.store.put("graphs", "wf1", header(2), "anna"), {"version": 1})

    @mark.req("REQ-GTB-020")
    def test_a_header_names_the_member_that_is_not_stored_not_the_first(self):
        """F-06(a): the second member of a header names a version that is not stored; the refusal names that member.

        Example: nodes n1 v1 (stored) and n2 v5 (n2 has only v1) -> unknown_member "n2"; n2 v1 is accepted.
        """
        # Given: n1 and n2 stored at version 1
        for node_id in ("n1", "n2"):
            self.store.put("graph_nodes", node_id, {"id": node_id, "data": {"type": "data"}}, "anna")
        def header(version):
            return {"id": "wf1", "data": {"kind": "workflow", "context_graph_id": "c", "testbench_id": "", "description": "d",
                                          "nodes": [{"id": "n1", "version": 1}, {"id": "n2", "version": version}], "edges": []}}
        # When/Then
        self.assertEqual(self.refusal_of("graphs", "wf1", header(5)), ("unknown_member", "n2"))
        self.assertEqual(self.store.put("graphs", "wf1", header(1), "anna"), {"version": 1})

    @mark.req("REQ-GTB-011")
    def test_validate_refuses_an_unknown_node_type(self):
        """F-06(b): storage.validate checks the shape of a record alone.

        Example: validate("graph_nodes", {"id": "n", "data": {"type": "zz"}}) -> invalid, unknown_type, "zz".
        """
        # Given/When
        with self.assertRaises(StorageError) as caught:
            validate("graph_nodes", {"id": "n", "data": {"type": "zz"}})
        # Then
        self.assertEqual((caught.exception.code, caught.exception.rule, caught.exception.detail), ("invalid", "unknown_type", "zz"))

    @mark.req("REQ-GTB-021")
    def test_a_graph_record_is_stored_under_its_own_id(self):
        """TC-GTB-022 on the Storage layer, for each of the four tables: a record written under a record ID that differs from the ID inside it is refused naming id, and nothing is stored under that ID.

        Example: {"id": "n1", "data": {"type": "data"}} written under "x" -> invalid, record_identity, "id"; under "n1" -> version 1.
        """
        # Given: two stored nodes and one record of each table, each with its own ID
        for node_id in ("n1", "n2"):
            self.store.put("graph_nodes", node_id, {"id": node_id, "data": {"type": "data"}}, "anna")
        records = {"graph_nodes": {"id": "n3", "data": {"type": "data"}},
                   "graph_edges": {"id": "e1", "from": "n1", "to": "n2", "data": {}},
                   "graphs": {"id": "wf1", "data": {"kind": "workflow", "context_graph_id": "c", "testbench_id": "", "description": "d",
                                                   "nodes": [{"id": "n1", "version": 1}], "edges": []}},
                   "skills": {"id": "lookup", "data": {"command": "/lookup", "workflow_graph_id": "wf1", "context_graph_id": "c"}}}
        for table, record in records.items():
            with self.subTest(table=table):
                # When: the record is written under the record ID x
                with self.assertRaises(StorageError) as caught:
                    self.store.put(table, "x", record, "anna")
                # Then: it is refused as record_identity naming id, and nothing is stored under x
                self.assertEqual((caught.exception.code, caught.exception.rule, caught.exception.detail), ("invalid", "record_identity", "id"))
                self.assertNotIn("x", self.store.ids(table))
                # And: under its own ID the same record is accepted (the twin differs only in the broken rule)
                self.assertEqual(self.store.put(table, record["id"], record, "anna"), {"version": 1})

    @mark.req("REQ-GTB-023", "REQ-GTB-024", "REQ-GTB-025", "REQ-GTB-026")
    def test_the_context_graph_records_are_versioned_checked_for_shape_and_name_stored_context_records(self):
        """TC-GTB-024 to TC-GTB-027 on the Storage layer: context nodes and edges are versioned and never deleted, the shape is checked, ends and members must be stored context nodes.

        Example: context edge e1 from c1 to c9 with only c1 stored -> unknown_endpoint "c9"; a workflow node n9 does not count; a context node without type -> schema_break "type".
        """
        # Given: one stored context node c1 (written twice) and one stored workflow node n9
        self.store.put("context_nodes", "c1", {"id": "c1", "data": {"type": "entity"}}, "anna")
        self.assertEqual(self.store.put("context_nodes", "c1", {"id": "c1", "data": {"type": "entity", "name": "x"}}, "anna"), {"version": 2})
        self.store.put("graph_nodes", "n9", {"id": "n9", "data": {"type": "data"}}, "anna")
        def header(kind, member):
            return {"id": "h1", "data": {"kind": kind, "context_graph_id": "c", "testbench_id": "", "description": "d",
                                         "nodes": [{"id": member, "version": 1}], "edges": []}}
        # When/Then: a bad shape, an end or member that is no stored context node, is refused naming the field or ID
        self.assertEqual(self.refusal_of("context_nodes", "c2", {"id": "c2", "data": {}}), ("schema_break", "type"))
        self.assertEqual(self.refusal_of("context_nodes", "c2", {"id": "c2"}), ("schema_break", "data"))
        self.assertEqual(self.refusal_of("context_edges", "e1", {"id": "e1", "from": "c1", "to": "c9", "data": {}}), ("unknown_endpoint", "c9"))
        self.assertEqual(self.refusal_of("context_edges", "e1", {"id": "e1", "from": "c1", "to": "n9", "data": {}}), ("unknown_endpoint", "n9"))
        self.assertEqual(self.refusal_of("graphs", "h1", header("context", "c9")), ("unknown_member", "c9"))
        self.assertEqual(self.refusal_of("graphs", "h1", header("workflow", "c1")), ("unknown_member", "c1"))
        # And: the twins are accepted and none of the two tables can be deleted
        self.assertEqual(self.store.put("context_edges", "e1", {"id": "e1", "from": "c1", "to": "c1", "data": {}}, "anna"), {"version": 1})
        self.assertEqual(self.store.put("graphs", "h1", header("context", "c1"), "anna"), {"version": 1})
        for table, record_id in (("context_nodes", "c1"), ("context_edges", "e1")):
            self.assertEqual(code_of(lambda: self.store.delete(table, record_id, "anna")), ("immutable", None))


class FileStorage(StorageBehaviour, unittest.TestCase):
    def new_backend(self, label):
        if not hasattr(self, "dir"):
            self.dir = tempfile.mkdtemp()
            self.addCleanup(shutil.rmtree, self.dir, True)
        self.main = FileBackend(os.path.join(self.dir, label))
        return self.main

    def reopen(self):
        return FileBackend(self.main.root)


    @mark.req("REQ-SLY-006")
    def test_a_raising_subscriber_does_not_stop_the_notice_to_the_other_instances(self):
        """Finding F2: put tells the shared channel even when a subscriber of this instance raises.
        Example: a backend with publish() and a raising subscriber; after put the channel got one notice of version 1."""
        # Given: a file backend with a channel, and a raising subscriber
        published = []
        backend = self.new_backend("channel")
        backend.publish = published.append
        store = Storage(backend)
        store.subscribe("tasks", lambda event: 1 / 0)
        # When: one write
        with self.assertLogs("storage", "ERROR"):
            store.put("tasks", "t", {"text": "a"}, "anna")
        # Then: the channel has the notice
        self.assertEqual([(e["id"], e["version"]) for e in published], [("t", 1)])

if __name__ == "__main__":
    unittest.main()
