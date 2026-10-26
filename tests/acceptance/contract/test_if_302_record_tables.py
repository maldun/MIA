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
        self.assertTrue({"history", "memory", "votes", "tasks", "memos", "accounts", "presets", "gestures", "runs", "source_trust"} <= set(defs))

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
        with self.assertRaises(ValueError):
            tables.validate("workflows", {})


if __name__ == "__main__":
    unittest.main()
