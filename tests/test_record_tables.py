"""The record tables (N-3.3 T-01, T-02): TC-RTB-001 to TC-RTB-006 and the foreign-table error of IF-302. Run with: python tests/test_record_tables.py"""
import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from markers import mark                         # noqa: E402
from record_tables import definitions, validate  # noqa: E402

CATEGORIES = ("answer_quality", "reactions", "character_behaviour", "service")
RUN = {"workflow": "lookup", "workflow_version": 1, "model_pin": "MP-light", "benchmark_version": "B1"}


class Definitions(unittest.TestCase):
    @mark.req("REQ-RTB-001", "REQ-RTB-006", "IF-302")
    def test_all_tables_versioned_and_deletable_exactly_where_planned(self):
        """TC-RTB-001, TC-RTB-006."""
        tables = definitions()
        self.assertEqual(set(tables), {"history", "memory", "votes", "tasks", "memos", "accounts", "presets", "gestures", "runs", "source_trust", "cases", "behaviours"})
        self.assertTrue(all(t["versioned"] for t in tables.values()))
        self.assertEqual({k for k, t in tables.items() if t["deletable"]}, {"history", "memory", "tasks", "memos"})
        self.assertEqual(tables["source_trust"], {"versioned": True, "deletable": False})

    @mark.req("REQ-RTB-001")
    def test_the_definitions_are_a_copy(self):
        definitions()["votes"]["deletable"] = True
        self.assertFalse(definitions()["votes"]["deletable"])

    @mark.req("IF-302")
    def test_a_table_that_is_not_a_record_table_is_a_value_error(self):
        """IF-302: the caller asks IF-301 instead."""
        for table in ("workflows", "context_graphs", "nope", None):
            with self.subTest(table=table), self.assertRaises(ValueError):
                validate(table, {})


class Validation(unittest.TestCase):
    @mark.req("REQ-RTB-002")
    def test_a_run_result_names_its_versions(self):
        """TC-RTB-002: complete is valid; each of the four fields missing gives schema with its name."""
        self.assertIsNone(validate("runs", RUN))
        for field in RUN:
            with self.subTest(field=field):
                broken = {k: v for k, v in RUN.items() if k != field}
                self.assertEqual(validate("runs", broken), {"rule": "schema", "detail": field})

    @mark.req("REQ-RTB-003")
    def test_votes_have_four_categories_and_a_value_of_one_or_minus_one(self):
        """TC-RTB-003."""
        vote = {"user": "anna", "subject": "m1", "category": "answer_quality", "value": 1}
        for category in CATEGORIES:
            for value in (1, -1):
                self.assertIsNone(validate("votes", dict(vote, category=category, value=value)), (category, value))
        self.assertEqual(validate("votes", dict(vote, category="mood"))["rule"], "category")
        self.assertEqual(validate("votes", dict(vote, value=5))["rule"], "schema")
        self.assertEqual(validate("votes", {k: v for k, v in vote.items() if k != "subject"}), {"rule": "schema", "detail": "subject"})

    @mark.req("REQ-RTB-003")
    def test_a_vote_with_a_boolean_value_is_refused(self):
        """True == 1 in Python; a vote is a number, so a flag is a schema error."""
        vote = {"user": "anna", "subject": "m1", "category": "service", "value": True}
        self.assertEqual(validate("votes", vote)["rule"], "schema")

    @mark.req("REQ-RTB-004")
    def test_a_memory_record_needs_text_and_source(self):
        """TC-RTB-004: without source the rule is schema, detail source."""
        self.assertIsNone(validate("memory", {"text": "likes tea", "source": "chat"}))
        self.assertEqual(validate("memory", {"text": "likes tea"}), {"rule": "schema", "detail": "source"})

    @mark.req("REQ-RTB-005")
    def test_tasks_and_memos_keep_any_text_unchanged(self):
        """TC-RTB-005: newlines, tabs, quotes, non-ASCII and 20,000 characters are valid and the document is not changed."""
        for table in ("tasks", "memos"):
            for text in ("a\nb\tc", 'say "hi" \'there\'', "Zoë – ✓ 日本語", "x" * 20000):
                with self.subTest(table=table, size=len(text)):
                    doc = {"text": text}
                    before = copy.deepcopy(doc)
                    self.assertIsNone(validate(table, doc))
                    self.assertEqual(doc, before)
            self.assertEqual(validate(table, {"note": "no text"}), {"rule": "schema", "detail": "text"})

    @mark.req("REQ-RTB-002")
    def test_a_document_that_is_not_a_mapping_is_a_schema_error(self):
        for table in ("runs", "votes", "memory", "tasks"):
            for bad in (None, [], "text"):
                with self.subTest(table=table, bad=bad):
                    self.assertEqual(validate(table, bad)["rule"], "schema")

    @mark.req("REQ-RTB-001")
    def test_tables_without_required_fields_accept_any_mapping(self):
        """history, accounts, presets, gestures and source_trust have no required field here: their shape belongs to the code that writes them."""
        for table in ("history", "accounts", "presets", "gestures", "source_trust"):
            self.assertIsNone(validate(table, {"anything": 1}))


if __name__ == "__main__":
    unittest.main()
