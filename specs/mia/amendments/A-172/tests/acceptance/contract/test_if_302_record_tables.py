"""IF-302 record table definitions and validation (Storage layer to Record tables): the contract suite runs against the mock (stage 1) and the real
Record tables (stage 2, skipped until N-3.3 is integrated). Protected after the Plan gate.
Run with: python tests/acceptance/contract/test_if_302_record_tables.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402  (from tests/helpers, shared with the other acceptance tests)

IF = "IF-302"


@contract
class RecordTablesContract(unittest.TestCase):
    @mark.req("IF-302", "REQ-DB-013")
    @each_provider(IF)
    def test_what_may_be_deleted(self, tables):
        """TC-IF-302-01 golden 3: deletable are exactly history, memory, tasks, memos and skill_runs (v7, A-67; v8, A-141), so votes, runs and source_trust are not; every table is versioned."""
        defs = tables.definitions()
        for table in ("memory", "tasks", "memos"):
            self.assertTrue(defs[table]["deletable"], table)
        for table in ("votes", "runs"):
            self.assertFalse(defs[table]["deletable"], table)
        self.assertTrue(all(d["versioned"] for d in defs.values()))
        self.assertEqual({t for t, d in defs.items() if d["deletable"]}, {"history", "memory", "tasks", "memos", "skill_runs"})      # v7 (A-67) and v8 (A-141): the whole set
        self.assertTrue({"history", "memory", "votes", "tasks", "memos", "accounts", "presets", "gestures", "runs", "source_trust", "cases", "behaviours", "workflow_meta", "reports", "skill_runs"} <= set(defs))
        for table in ("cases", "behaviours", "workflow_meta", "reports"):                                   # v1 (A-08): proposed benchmark cases and the adaptation counters keep every version
            self.assertEqual(defs[table], {"versioned": True, "deletable": False}, table)

    @mark.req("IF-302", "REQ-DB-012")
    @each_provider(IF)
    def test_votes_have_four_categories_and_a_value(self, tables):
        """TC-IF-302-02 golden 1 and 2: the four categories are valid; another category is rule category; a value other than 1 or -1 is rule schema."""
        for category in ("answer_quality", "reactions", "character_behaviour", "service"):
            self.assertIsNone(tables.validate("votes", {"user": "anna", "subject": "m1", "category": category, "value": -1}))
        self.assertEqual(tables.validate("votes", {"user": "anna", "subject": "m1", "category": "mood", "value": 1})["rule"], "category")
        self.assertEqual(tables.validate("votes", {"user": "anna", "subject": "m1", "category": "service", "value": 5})["rule"], "schema")

    @mark.req("IF-302", "REQ-DB-013", "REQ-DB-014")
    @each_provider(IF)
    def test_required_fields_and_exact_text(self, tables):
        """TC-IF-302-03: a memory record needs a source (rule schema, detail source); text with newlines, quotes and non-ASCII characters is valid; a foreign table is a ValueError."""
        self.assertEqual(tables.validate("memory", {"text": "likes tea"}), {"rule": "schema", "detail": "source"})
        self.assertIsNone(tables.validate("memos", {"text": "Call Zoë at 9:00 – bring \"the\" notes\n\tdone ✓"}))
        self.assertEqual(tables.validate("runs", {"workflow": "lookup"})["rule"], "schema")
        self.assertEqual(tables.validate("cases", {"question": "q", "status": "proposed"}), {"rule": "schema", "detail": "answer"})
        self.assertIsNone(tables.validate("cases", {"question": "q", "answer": "a", "status": "proposed"}))
        self.assertIsNone(tables.validate("behaviours", {"name": "wave", "net": -5, "votes": 5}))
        with self.assertRaises(ValueError):
            tables.validate("workflows", {})


    @mark.req("IF-302", "REQ-CHA-011")
    @each_provider(IF)
    def test_a_memory_record_may_carry_kind_and_status(self, tables):
        """TC-IF-302-04 (v2): kind (fact, preference, commitment) and status (active, replaced) are checked when present, subject and updated are free; a record of v1 stays valid; the source stays required."""
        old = {"text": "likes tea", "source": "chat"}
        self.assertIsNone(tables.validate("memory", old))
        self.assertIsNone(tables.validate("memory", dict(old, kind="commitment", status="replaced", subject="anna", updated="2026-10-27T10:00:00Z")))
        self.assertEqual(tables.validate("memory", dict(old, kind="opinion")), {"rule": "schema", "detail": "kind"})
        self.assertEqual(tables.validate("memory", dict(old, status="deleted")), {"rule": "schema", "detail": "status"})
        self.assertEqual(tables.validate("memory", {"text": "x", "kind": "fact"}), {"rule": "schema", "detail": "source"})

    @mark.req("IF-302", "REQ-WFM-002")
    @each_provider(IF)
    def test_workflow_meta_keeps_the_lifecycle(self, tables):
        """TC-IF-302-05 (v3): status is required and one of draft, tested, trusted, retired; specification and benchmark are free."""
        self.assertIsNone(tables.validate("workflow_meta", {"status": "draft"}))
        self.assertIsNone(tables.validate("workflow_meta", {"status": "tested", "specification": {"inputs": "q"}, "benchmark": {"suite": "verdicts"}}))
        self.assertEqual(tables.validate("workflow_meta", {"specification": {}}), {"rule": "schema", "detail": "status"})
        self.assertEqual(tables.validate("workflow_meta", {"status": "wild"}), {"rule": "schema", "detail": "status"})


    @mark.req("IF-302", "REQ-WFM-038")
    @each_provider(IF)
    def test_a_finished_report_is_a_record_with_its_origin(self, tables):
        """TC-IF-302-06 (v4, v5): a `reports` record needs task, skill, skill_version, question, account, model_pin and report; a missing field is rule schema with that field as detail; the table is versioned and not deletable."""
        doc = {"task": "review", "skill": "review", "skill_version": "1", "question": "q", "account": "anna", "model_pin": "m", "report": {"works": []}}
        self.assertIsNone(tables.validate("reports", doc))
        for field in doc:
            self.assertEqual(tables.validate("reports", {k: v for k, v in doc.items() if k != field}), {"rule": "schema", "detail": field})
        self.assertEqual(tables.definitions()["reports"], {"versioned": True, "deletable": False})

    @mark.req("IF-302", "REQ-DB-012")
    @each_provider(IF)
    def test_a_document_that_is_not_a_mapping_and_a_vote_value_that_is_no_integer_are_schema(self, tables):
        """TC-IF-302-07 (v6, A-61) golden 4: a document that is not a mapping is rule schema in every table; a vote value 1.0, -1.0, True or False is rule schema, detail value."""
        for table in tables.definitions():
            for bad in (None, [], "text"):
                self.assertEqual(tables.validate(table, bad)["rule"], "schema", (table, bad))
        vote = {"user": "anna", "subject": "m1", "category": "service", "value": 1}
        for value in (1.0, -1.0, True, False):
            self.assertEqual(tables.validate("votes", dict(vote, value=value)), {"rule": "schema", "detail": "value"}, value)

    @mark.req("IF-302", "REQ-RTB-008")
    @each_provider(IF)
    def test_transform_meta_keeps_trust_and_lifecycle(self, tables):
        """TC-IF-302-09 (v10, A-110; TC-RTB-008): transform_meta is versioned and not deletable; trust (untrusted or trusted) and lifecycle (draft, tested or retired) are required and exact; the optional fields are free.
        (08 is taken by skill_runs of G-V3, A-141: check the number when both are installed.)"""
        self.assertEqual(tables.definitions()["transform_meta"], {"versioned": True, "deletable": False})
        self.assertIsNone(tables.validate("transform_meta", {"trust": "trusted", "lifecycle": "tested"}))
        self.assertIsNone(tables.validate("transform_meta", {"trust": "untrusted", "lifecycle": "draft", "reason": "not reviewed", "evidence": "run-17", "baseline_allowed": False, "shipped": True}))
        for field in ("trust", "lifecycle"):
            incomplete = {"trust": "trusted", "lifecycle": "tested"}
            del incomplete[field]
            self.assertEqual(tables.validate("transform_meta", incomplete), {"rule": "schema", "detail": field})
        self.assertEqual(tables.validate("transform_meta", {"trust": "maybe", "lifecycle": "tested"}), {"rule": "schema", "detail": "trust"})
        self.assertEqual(tables.validate("transform_meta", {"trust": "trusted", "lifecycle": "fine"}), {"rule": "schema", "detail": "lifecycle"})

    @mark.req("IF-302", "REQ-RTB-009")
    @each_provider(IF)
    def test_transforms_keeps_the_versions_of_the_code(self, tables):
        """TC-IF-302-10 (v11, A-112; TC-RTB-009): transforms is versioned and not deletable; id (text, not empty) and version (an integer of at least 1) are required and exact;
        inputs, outputs and code are free, a missing, empty or null code is valid."""
        self.assertEqual(tables.definitions()["transforms"], {"versioned": True, "deletable": False})
        full = {"id": "t.one", "version": 1, "inputs": {"type": "object"}, "outputs": {"type": "number"}, "code": "def run(args):\n    return 1\n"}
        self.assertIsNone(tables.validate("transforms", full))
        for free in ({"code": ""}, {"code": None}, {"inputs": 5}):
            self.assertIsNone(tables.validate("transforms", dict(full, **free)), free)
        self.assertIsNone(tables.validate("transforms", {"id": "t.two", "version": 7}))
        stub = dict(full)
        del stub["code"]
        self.assertIsNone(tables.validate("transforms", stub))
        for field in ("id", "version"):
            incomplete = dict(full)
            del incomplete[field]
            self.assertEqual(tables.validate("transforms", incomplete), {"rule": "schema", "detail": field})
        self.assertEqual(tables.validate("transforms", dict(full, id="")), {"rule": "schema", "detail": "id"})
        self.assertEqual(tables.validate("transforms", dict(full, id=5)), {"rule": "schema", "detail": "id"})
        for version in (0, -1, True, 1.0, 1.5, "1", None):
            self.assertEqual(tables.validate("transforms", dict(full, version=version)), {"rule": "schema", "detail": "version"}, version)

    @mark.req("IF-302", "REQ-RTB-007")
    @each_provider(IF)
    def test_a_skill_run_is_a_versioned_deletable_record(self, tables):
        """TC-IF-302-08 (v8, A-141): `skill_runs` is versioned and deletable; a record needs run, skill, skill_version, account, started and state (a missing field is rule schema with that field as detail); the optional fields ended, phases, budget, counts, reason, answers, result, material, files and (v9) elements are free; `reports` stays as it is.
        Example: validate("skill_runs", {"run": "r1", "skill": "review", "skill_version": "2", "account": "anna", "started": "2026-11-08T10:00:00Z", "state": "running"}) -> None."""
        doc = {"run": "r1", "skill": "review", "skill_version": "2", "account": "anna", "started": "2026-11-08T10:00:00Z", "state": "running"}
        self.assertEqual(tables.definitions()["skill_runs"], {"versioned": True, "deletable": True})
        self.assertIsNone(tables.validate("skill_runs", doc))
        for field in doc:
            self.assertEqual(tables.validate("skill_runs", {k: v for k, v in doc.items() if k != field}), {"rule": "schema", "detail": field})
        full = dict(doc, ended="2026-11-08T10:05:00Z", phases=[{"name": "screening", "state": "done"}], budget={"seconds": 600}, counts={"searches": 3},
                    reason="stopped by the user", answers=[{"text": "yes", "time": "2026-11-08T10:01:00Z"}], result="text", material=[], files=["report.md"],
                    elements=[{"label": "Works read", "text": "12"}], report="report.md")
        self.assertIsNone(tables.validate("skill_runs", full))
        self.assertEqual(tables.definitions()["reports"], {"versioned": True, "deletable": False})


    @mark.req("IF-302", "REQ-WFM-064")
    @each_provider(IF)
    def test_the_current_version_pointer_is_a_versioned_record_that_is_not_deletable(self, tables):
        """TC-IF-302-11 (v13, A-121): `current_versions` is versioned and not deletable; a record needs `version`, an integer of at least 1 (a boolean, a float, a text, 0 or a missing field is rule schema with detail version); every other field is kept and never refused (`reason`, `format`, and one nobody knows yet); the deletable set stays as in v8.
        Example: validate("current_versions", {"version": 2}) -> None; validate("current_versions", {"version": 1.0}) -> {"rule": "schema", "detail": "version"}."""
        self.assertEqual(tables.definitions()["current_versions"], {"versioned": True, "deletable": False})
        self.assertIsNone(tables.validate("current_versions", {"version": 2}))
        self.assertIsNone(tables.validate("current_versions", {"version": 2, "reason": "snapshot restore of a", "format": 1, "note": "later"}))
        for bad in (0, -1, True, 1.0, "1", None):
            self.assertEqual(tables.validate("current_versions", {"version": bad}), {"rule": "schema", "detail": "version"}, bad)
        self.assertEqual(tables.validate("current_versions", {"reason": "save"}), {"rule": "schema", "detail": "version"})
        self.assertEqual({t for t, d in tables.definitions().items() if d["deletable"]}, {"history", "memory", "tasks", "memos", "skill_runs"})


    @mark.req("IF-302", "REQ-WFM-061")
    @each_provider(IF)
    def test_a_snapshot_is_a_versioned_record_that_is_not_deletable(self, tables):
        """TC-IF-302-12 (v14, A-161): `snapshots` is versioned and not deletable; a record needs name (a text that is not empty), time, author, items (a list) and pins (a mapping), else rule schema with that field as detail; every other field is kept and never refused; the deletable set stays as in v8.
        Example: validate("snapshots", {"name": "a", "time": 1, "author": "anna", "items": [], "pins": {}}) -> None; with name "" -> {"rule": "schema", "detail": "name"}."""
        doc = {"name": "a", "time": 1, "author": "anna", "items": [{"kind": "skills", "id": "research", "version": 1}], "pins": {"MP-light": "gemma4:12b-it-qat"}}
        self.assertEqual(tables.definitions()["snapshots"], {"versioned": True, "deletable": False})
        self.assertIsNone(tables.validate("snapshots", doc))
        self.assertIsNone(tables.validate("snapshots", dict(doc, format=1, note="before the rework", unknown_field=[1])))
        for field in doc:
            self.assertEqual(tables.validate("snapshots", {k: v for k, v in doc.items() if k != field}), {"rule": "schema", "detail": field}, field)
        for field, bad in (("name", ""), ("name", 5), ("items", "x"), ("items", None), ("pins", []), ("pins", "MP-light")):
            self.assertEqual(tables.validate("snapshots", dict(doc, **{field: bad})), {"rule": "schema", "detail": field}, (field, bad))
        self.assertEqual({t for t, d in tables.definitions().items() if d["deletable"]}, {"history", "memory", "tasks", "memos", "skill_runs"})


    @mark.req("IF-302")
    @each_provider(IF)
    def test_an_arrangement_is_a_versioned_record_of_whole_places(self, tables):
        """TC-IF-302-13 (v15, A-172): `arrangements` is versioned and not deletable; a record needs graph (a text that is not empty) and positions (a mapping of step ID to two integers x and y), else rule schema with that field as detail; other fields are kept; the deletable set stays as in v8.
        Example: {"graph": "cp2.multi", "positions": {"var.in": {"x": 10, "y": -3}}} -> None; a place {"x": 10.5, "y": 0} -> {"rule": "schema", "detail": "positions"}."""
        # Given a valid arrangement record
        doc = {"graph": "cp2.multi", "positions": {"var.in": {"x": 10, "y": -3}, "step.write": {"x": 0, "y": 0}}}
        # When it is defined and validated, also with an empty mapping and an extra field
        # Then it is versioned, not deletable, and valid
        self.assertEqual(tables.definitions()["arrangements"], {"versioned": True, "deletable": False})
        self.assertIsNone(tables.validate("arrangements", doc))
        self.assertIsNone(tables.validate("arrangements", dict(doc, positions={}, note="kept")))
        # And a missing field or a bad value is rule schema naming the field
        for field in doc:
            self.assertEqual(tables.validate("arrangements", {k: v for k, v in doc.items() if k != field}), {"rule": "schema", "detail": field}, field)
        for field, bad in (("graph", ""), ("graph", 5), ("positions", []), ("positions", {"a": {"x": 10.5, "y": 0}}), ("positions", {"a": {"x": True, "y": 0}}),
                           ("positions", {"a": {"x": 1}}), ("positions", {"a": [1, 2]})):
            self.assertEqual(tables.validate("arrangements", dict(doc, **{field: bad})), {"rule": "schema", "detail": field}, (field, bad))
        self.assertEqual({t for t, d in tables.definitions().items() if d["deletable"]}, {"history", "memory", "tasks", "memos", "skill_runs"})

    @mark.req("IF-302")
    @each_provider(IF)
    def test_a_record_of_changes_names_its_version_and_kind(self, tables):
        """TC-IF-302-14 (v15, A-172): `graph_changes` is versioned and not deletable; a record needs graph (text, not empty), version and from_version (integers of at least 1), kind (editor, derived or restore) and entries (a list), else rule schema with that field as detail; entries and other fields are kept as given.
        Example: {"graph": "cp2.multi", "version": 5, "from_version": 4, "kind": "derived", "entries": []} -> None; kind "before_the_record" -> {"rule": "schema", "detail": "kind"}."""
        # Given a valid record of changes
        doc = {"graph": "cp2.multi", "version": 5, "from_version": 4, "kind": "derived",
               "entries": [{"n": 1, "op": "change_step", "target": "step.write", "before": {"toolbox_id": "t4"}, "after": {"toolbox_id": "t9"}, "reason": None}]}
        # When it is defined and validated, for each kind and with an extra field
        # Then it is versioned, not deletable, and valid
        self.assertEqual(tables.definitions()["graph_changes"], {"versioned": True, "deletable": False})
        for kind in ("editor", "derived", "restore"):
            self.assertIsNone(tables.validate("graph_changes", dict(doc, kind=kind)), kind)
        self.assertIsNone(tables.validate("graph_changes", dict(doc, entries=[], note="kept")))
        # And a missing field or a bad value is rule schema naming the field
        for field in doc:
            self.assertEqual(tables.validate("graph_changes", {k: v for k, v in doc.items() if k != field}), {"rule": "schema", "detail": field}, field)
        for field, bad in (("graph", ""), ("graph", None), ("version", 0), ("version", 5.0), ("version", True), ("version", "5"), ("from_version", 0),
                           ("from_version", None), ("kind", "before_the_record"), ("kind", "Editor"), ("entries", {}), ("entries", None)):
            self.assertEqual(tables.validate("graph_changes", dict(doc, **{field: bad})), {"rule": "schema", "detail": field}, (field, bad))
        self.assertEqual({t for t, d in tables.definitions().items() if d["deletable"]}, {"history", "memory", "tasks", "memos", "skill_runs"})


if __name__ == "__main__":
    unittest.main()
