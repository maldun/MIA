# Test specification: Record tables (N-3.3)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.3-memories-history-feedback/requirements.md   **Status:** Draft (Plan for node N-3.3, 2026-10-25)

Tests of this part alone against the mocks of its neighbours: unit tests with plain data, no database. The interface IF-302 is tested by its contract suite against the mock and the real part. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-RTB-001 | REQ-RTB-001 | Unit | 1 | definitions() of the Record tables | the ten tables history, memory, votes, tasks, memos, accounts, presets, gestures, runs and source_trust; all versioned; deletable exactly history, memory, tasks, memos | exact |
| TC-RTB-002 | REQ-RTB-002 | Unit | 1 | validate(runs, doc) for a complete run result and for four documents each lacking one of workflow, workflow_version, model_pin, benchmark_version | None for the complete one; rule schema with the missing field named for each of the four | exact |
| TC-RTB-003 | REQ-RTB-003 | Unit | 1 | validate(votes, doc) for the four categories with value 1 and -1, for category mood, for value 5, and for a document without subject | None for the eight valid combinations; rule category for mood; rule schema for value 5 and for the missing subject | exact |
| TC-RTB-004 | REQ-RTB-004 | Unit | 1 | validate(memory, doc) with and without source; definitions() | without source: rule schema, detail source; memory is deletable | exact |
| TC-RTB-005 | REQ-RTB-005 | Unit | 1 | validate(tasks, doc) and validate(memos, doc) for text with newlines, tabs, quotes, non-ASCII characters and 20,000 characters; the document compared before and after | None; the document is equal before and after (validation changes nothing); a document without text gives rule schema | exact |
| TC-RTB-006 | REQ-RTB-006 | Unit | 1 | definitions() entry source_trust | versioned, not deletable | exact |

Contract test cases of IF-302: TC-IF-302-01 to the last of the suite (listed in the root `test-spec.md`).

## Assumptions (checked in validation)

- ASM-N3-005: the required fields of the record tables are the ones of `contracts/IF-302-record-tables.md`; other fields are kept as given.
