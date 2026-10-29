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
        """TC-IF-302-01 golden 3: memory, tasks and memos are deletable, votes and runs are not; every table is versioned."""
        defs = tables.definitions()
        for table in ("memory", "tasks", "memos"):
            self.assertTrue(defs[table]["deletable"], table)
        for table in ("votes", "runs"):
            self.assertFalse(defs[table]["deletable"], table)
        self.assertTrue(all(d["versioned"] for d in defs.values()))
        self.assertTrue({"history", "memory", "votes", "tasks", "memos", "accounts", "presets", "gestures", "runs", "source_trust", "cases", "behaviours", "workflow_meta", "reports"} <= set(defs))
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


if __name__ == "__main__":
    unittest.main()
