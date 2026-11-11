# Test specification: Record tables (N-3.3)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.3-memories-history-feedback/requirements.md   **Status:** Draft (Plan for node N-3.3, 2026-10-25)

Tests of this part alone against the mocks of its neighbours: unit tests with plain data, no database. The interface IF-302 is tested by its contract suite against the mock and the real part. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-RTB-001 | REQ-RTB-001 | Unit | 1 | definitions() of the Record tables | the 14 tables history, memory, votes, tasks, memos, accounts, presets, gestures, runs, source_trust, cases, behaviours, workflow_meta and reports (D-161); all versioned; deletable exactly history, memory, tasks, memos | exact |
| TC-RTB-002 | REQ-RTB-002 | Unit | 1 | validate(runs, doc) for a complete run result and for four documents each lacking one of workflow, workflow_version, model_pin, benchmark_version | None for the complete one; rule schema with the missing field named for each of the four | exact |
| TC-RTB-003 | REQ-RTB-003 | Unit | 1 | validate(votes, doc) for the four categories with value 1 and -1, for category mood, for the values 5, 0, 1.0, -1.0 and True, and for a document lacking each required field in turn | None for the eight valid combinations; rule category for mood; rule schema, detail value, for each wrong value; rule schema with the missing field named for each document lacking one (D-161) | exact |
| TC-RTB-004 | REQ-RTB-004 | Unit | 1 | validate(memory, doc) with and without source; definitions() | without source: rule schema, detail source; memory is deletable | exact |
| TC-RTB-005 | REQ-RTB-005 | Unit | 1 | validate(tasks, doc) and validate(memos, doc) for text with newlines, tabs, quotes, non-ASCII characters and 20,000 characters; the document compared before and after | None; the document is equal before and after (validation changes nothing); a document without text gives rule schema | exact |
| TC-RTB-006 | REQ-RTB-006 | Unit | 1 | definitions() entry source_trust | versioned, not deletable | exact |
| TC-RTB-007 | REQ-RTB-007 | Unit | 1 | definitions() entry skill_runs and validate(skill_runs, doc) for a complete run record and for six documents each lacking one required field | versioned and deletable; the complete one accepted; each incomplete one is rule schema with the missing field as detail | exact |
| TC-RTB-008 | REQ-RTB-008 | Unit | 1 | definitions() entry transform_meta and validate(transform_meta, doc) for a complete record, for two documents each lacking one required field and for documents with an unknown trust or lifecycle value | versioned and not deletable; the complete one accepted; each bad one is rule schema with the field as detail | exact |
| TC-RTB-009 | REQ-RTB-009 | Unit | 1 | definitions() entry transforms and validate(transforms, doc) for a complete record, for records with an empty, a null and a missing code, for two documents each lacking one required field and for documents with an id that is empty or not text and a version of 0, -1, true, 1.0, 1.5, "1" or null | versioned and not deletable; the complete one and the three code variants accepted; each bad one is rule schema with the field as detail | exact |

Contract test cases of IF-302: TC-IF-302-01 to the last of the suite (listed in the root `test-spec.md`).

## Assumptions (checked in validation)

- ASM-N3-005: the required fields of the record tables are the ones of `contracts/IF-302-record-tables.md`; other fields are kept as given.

## Scenarios (G-V3.PANEL, TC-RTB-007; the older checks of this file have none yet)

### TC-RTB-007 – Skill runs stored
- Verifies: REQ-RTB-007
- Given: the Record tables with the table skill_runs of IF-302 v8 (proposed) and a run record with run, skill, skill_version, account, started and state
- When: definitions() is read; the record is validated; then six copies, each lacking one of the six fields, are validated
- Then: skill_runs is versioned and deletable; the complete record is accepted; each incomplete copy is refused as rule schema naming its missing field

### TC-RTB-008 – Transform meta stored
- Verifies: REQ-RTB-008
- Given: the Record tables with the table transform_meta of IF-302 (A-110, proposed) and a record with trust `trusted` and lifecycle `tested`
- When: definitions() is read; the record is validated; then two copies, each lacking one of the two fields, and two copies with trust `maybe` and lifecycle `fine` are validated
- Then: transform_meta is versioned and not deletable; the complete record is accepted; each bad copy is refused as rule schema naming its field; the accepted values `untrusted` and `draft` are accepted as twins

### TC-RTB-009 – Transforms stored
- Verifies: REQ-RTB-009
- Given: the Record tables with the table transforms of IF-302 (A-112, proposed) and a record with id `t.one`, version 1, input and output schemas and a code text
- When: definitions() is read; the record is validated; then copies with an empty code, a null code and no code, two copies each lacking one of id and version, a copy with an empty id, and copies with version 0, -1, true, 1.0, 1.5, "1" and null are validated
- Then: transforms is versioned and not deletable; the complete record and the three code variants are accepted (a stub transform is valid); each bad copy is refused as rule schema naming its field; a version of 7 as the first record is accepted as a twin
