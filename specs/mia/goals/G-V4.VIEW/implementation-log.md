# Implementation log: G-V4.VIEW

Goal: G-V4.VIEW   Line of work: goal/v4.view   Supervision: supervised (plan gate ticked by the owner, D-447)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Record tables | done | see `git log` ("feat: T-01 record tables arrangements and graph_changes") | TC-IF-302-13, 14 (mock and real); `tests/test_record_tables_view.py` (6 unit tests) | `tests/test_record_tables.py`: the expected table set gets the two new tables (A-172) |

## T-01: Record tables

**What was done**
- `record_tables.py`: tables `arrangements` and `graph_changes` (versioned, not deletable), their required fields, and the checks IF-302 v15 states: `graph` a text that is not empty; `positions` a mapping from a text step ID to exactly `{x, y}`, both integers (no bool, no float); `version` and `from_version` integers of at least 1; `kind` one of `editor`, `derived`, `restore`; `entries` a list, kept as given. Written once is the graph API's check (D-435, T-06), not the table's.
- `tests/test_record_tables_view.py` written first and seen red (6 errors): zero and negative places, a place with a third key, a step ID that is not text, both tables versioned and kept, entries kept as given, a restore from an older version.
- `tests/test_record_tables.py` (not protected): the exact set of tables in TC-RTB-001 gets `arrangements` and `graph_changes`, the change A-172 approved.
- No change to `architecture.sysml`: `record_tables.py` is already a module of `persistence.graphRecords` (D-439).

**Tests green (my runs, feedback only):** `tests/acceptance/contract/test_if_302_record_tables.py` 28/28; `tests/test_record_tables_view.py` 6/6; `tests/test_record_tables.py` OK.

**Regression set (2026-11-23, sequential):** unit suite `discover -s tests` exit 0 (2560 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 186 pass. Acceptance scripts: all OK except the VIEW checks of later tasks (`test_view_backend.py` 12, `test_graph_view_files.py` 2, `test_graph_view_browser.py` 7, `graph_view_page.test.mjs` 14, the real side of `test_if_104_v2_graph_api.py` 22) and the known reds `test_decide_guard.py`, `test_judge_calibration.py` (G-V3.REPORT F-3: `behaviour.FUNCTIONS` missing; also red on `goal/v4`).

**Deliberate defects (not required by TR-VIEW-021 for contract cases; run once, then restored):**

| Defect in `record_tables.py` | Check | Result |
|---|---|---|
| `before_the_record` accepted as a stored kind | TC-IF-302-14 | fails |
| a place's coordinates accepted as any number (float, bool) | TC-IF-302-13 | fails |

**Deviation:** `plan.md` T-01 names the defect "a second write of the same graph version replaces the record" against TC-IF-302-14. That case checks the table definition and validation only; written once is checked by the graph API before the write (D-435) and shown by TC-API-022 in T-06. So that defect belongs to T-06 (where the plan already lists "the record written twice"), and the kind defect above was run instead. No plan change needed; for Verify to note.

**Open questions for Verify:** none.
