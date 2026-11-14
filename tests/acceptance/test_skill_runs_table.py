"""
Acceptance test of the Record tables for the Skill run view (N-3.3, G-V3.PANEL): TC-RTB-007 (REQ-RTB-007) against the real record_tables module.
Run with: python tests/acceptance/test_skill_runs_table.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark          # noqa: E402
import record_tables              # noqa: E402

RUN = {"run": "r1", "skill": "review", "skill_version": "2", "account": "anna", "started": "2026-11-08T10:00:00Z", "state": "running"}


class SkillRunsTable(unittest.TestCase):
    @mark.req("REQ-RTB-007")
    def test_a_skill_run_is_a_versioned_deletable_record_with_six_required_fields(self):
        """TC-RTB-007: skill_runs is versioned and deletable, a complete run record is accepted, and each of the six required fields that is missing is rule schema naming that field.
        Example: validate("skill_runs", RUN without "state") -> {"rule": "schema", "detail": "state"}."""
        # Given: the Record tables with the table skill_runs of IF-302 v8 and a record with the six required fields
        definitions = record_tables.definitions()
        # When: definitions() is read and the record is validated, then six copies, each lacking one field, are validated
        refused = {field: record_tables.validate("skill_runs", {k: v for k, v in RUN.items() if k != field}) for field in RUN}
        # Then: the table is versioned and deletable
        self.assertEqual(definitions["skill_runs"], {"versioned": True, "deletable": True})
        # And: the complete record is accepted
        self.assertIsNone(record_tables.validate("skill_runs", RUN))
        # And: each incomplete copy is refused as rule schema naming its missing field
        self.assertEqual(refused, {field: {"rule": "schema", "detail": field} for field in RUN})


if __name__ == "__main__":
    unittest.main()
