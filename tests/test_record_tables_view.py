"""The record tables of G-V4.VIEW T-01 (IF-302 v15, A-172): `arrangements` and `graph_changes`. Run with: python tests/test_record_tables_view.py"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from markers import mark                         # noqa: E402
from record_tables import definitions, validate  # noqa: E402

ARRANGEMENT = {"graph": "cp2.multi", "positions": {"var.in": {"x": 10, "y": -3}}}
CHANGES = {"graph": "cp2.multi", "version": 5, "from_version": 4, "kind": "derived", "entries": []}


class Arrangements(unittest.TestCase):
    @mark.req("REQ-RTB-010")
    def test_a_place_with_a_negative_and_a_zero_coordinate_is_valid(self):
        """Example: {"x": 0, "y": -3} -> None (whole pixels may be zero or negative)."""
        # Given an arrangement with a place at 0, -3
        doc = dict(ARRANGEMENT, positions={"a": {"x": 0, "y": -3}})
        # When it is validated
        # Then it is valid
        self.assertIsNone(validate("arrangements", doc))

    @mark.req("REQ-RTB-010")
    def test_a_place_with_an_extra_key_is_refused(self):
        """Example: {"x": 1, "y": 2, "z": 3} -> rule schema, detail positions (a place is exactly two integers)."""
        # Given a place with a third coordinate
        doc = dict(ARRANGEMENT, positions={"a": {"x": 1, "y": 2, "z": 3}})
        # When it is validated
        # Then the positions are named
        self.assertEqual(validate("arrangements", doc), {"rule": "schema", "detail": "positions"})

    @mark.req("REQ-RTB-010")
    def test_a_step_id_that_is_not_text_is_refused(self):
        """Example: positions {5: {"x": 1, "y": 2}} -> rule schema, detail positions (step IDs are texts)."""
        # Given a place keyed by a number
        doc = dict(ARRANGEMENT, positions={5: {"x": 1, "y": 2}})
        # When it is validated
        # Then the positions are named
        self.assertEqual(validate("arrangements", doc), {"rule": "schema", "detail": "positions"})


class GraphChanges(unittest.TestCase):
    @mark.req("REQ-RTB-011")
    def test_both_tables_are_versioned_and_kept(self):
        """Example: definitions()["graph_changes"] -> {"versioned": True, "deletable": False}."""
        # Given the definitions
        tables = definitions()
        # When the two new tables are looked up
        # Then both are versioned and never deleted by the application
        for table in ("arrangements", "graph_changes"):
            self.assertEqual(tables[table], {"versioned": True, "deletable": False}, table)

    @mark.req("REQ-RTB-011")
    def test_the_entries_are_kept_as_given(self):
        """Example: an entry of any form is not looked at (its form is IF-104 v2's) -> None."""
        # Given a record whose entry is a bare text
        doc = dict(CHANGES, entries=["anything"])
        # When it is validated
        # Then it is valid, and the document is not changed
        self.assertIsNone(validate("graph_changes", doc))
        self.assertEqual(doc["entries"], ["anything"])

    @mark.req("REQ-RTB-011")
    def test_from_version_may_be_above_version_for_a_restore(self):
        """Example: version 5 from_version 1 is valid for restore; the order of versions is the graph API's business."""
        # Given a restore record of version 5 from version 1
        doc = dict(CHANGES, kind="restore", from_version=1)
        # When it is validated
        # Then it is valid
        self.assertIsNone(validate("graph_changes", doc))


if __name__ == "__main__":
    unittest.main()
