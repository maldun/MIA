# Implementation log: Record tables (N-3.3)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Definitions of the ten record tables | done | `feat(record_tables)` | `tests/test_record_tables.py` (TC-RTB-001, TC-RTB-006, the foreign-table error); IF-302 contract suite with `record_tables` as real provider (scratch run, `_real` side, 3 tests) | one commit with T-02: one small module |
| T-02 Required fields and validation | done | `feat(record_tables)` | same file, 10 tests (TC-RTB-002 to TC-RTB-005 and edge cases) | validation never changes a document |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| `True == 1` in Python, so a vote with a flag as value would pass `value in (1, -1)` | T-02 | `test_a_vote_with_a_boolean_value_is_refused` |
| The mock reads `doc["category"]` before it knows the field exists in a mapping check; the real module checks mapping and required fields first | T-02 | `test_a_document_that_is_not_a_mapping_is_a_schema_error` |

## Reuse check (owner rule: use existing code)
- New: no module validates record documents. The stores that write these records today (`chat_log.py`, `preset_store.py`, `gesture_store.py`, `source_trust.py`, the votes in the feedback code) keep their own file formats and stay as they are; the Storage layer (N-3.1) wraps them as the file backend.

## Plan amendments
None.

## Decisions
- Tables without a required field in the plan (history, accounts, presets, gestures, source_trust) accept any mapping here; their shape belongs to the code that writes them (`test_tables_without_required_fields_accept_any_mapping`). A stricter schema would be a plan amendment.

## Open questions for Phase 4 and the integration step
- As for IF-301: giving the IF-302 contract suite `record_tables` as the real provider is an amendment of `tests/helpers/contract.py` at integration step 2 of N-3 (owner).

## Verify fixes (D-161, 2026-10-31, branch v1-n33b)
| Finding | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| F1 markers of the `reports` and `workflow_meta` tests | done | `test(record_tables)` | `tests/test_record_tables.py` 13 OK | `reports` → REQ-WFM-038, IF-302; the old marker (REQ-WFM-002, -006, IF-302) back on the `workflow_meta` test; behaviour unchanged |
| F3, F5 a float, a boolean vote and a document that is not a mapping are rule `schema` | done | `fix(record_tables)` | `test_record_tables.py` 15 OK (red first: 1.0, -1.0); `test_chat_answers.py` OK (red first: 1.0, -1.0 stored), `test_chat_behaviour.py` OK; `test_chat_ops_api.py` OK in the image; IF-302 suite 12 OK | `type(value) is not int` in `record_tables.validate` and `ChatService.vote` (refused there as `invalid_vote`, rule `value`); non-mapping now tested for all 14 tables (already `schema` in the code); the mock follows with A-61 |
| F4 surviving mutants | done | `test(record_tables)` | `test_record_tables.py` 17 OK | each required vote field missing is named (loop as TC-RTB-002), value 0 refused, memory `status="fact"` refused; hand mutation in a scratch copy: the three F4 mutants, "float allowed" and "non-mapping allowed for tables without required fields" are all killed. TC-RTB-003's text ("each required field") is a Phase 2 point (open) |
| F6 `chat_service.py` gets the categories through IF-302 | waits for A-61 | `test(record_tables)` | `test_record_tables.py`, `test_chat_answers.py` OK with one skip each | IF-302 has no operation for the categories: new read operation `categories()` drafted in A-61 (IF-302 v6). The two tests (provider: `record_tables.categories()` gives the four in order; consumer: `chat_service.categories is record_tables.categories`, no `CATEGORIES`) are skipped until the installed contract names `categories()`, then red until the code change (M8: no code on a proposal). Code change after install: `def categories(): return CATEGORIES` in `record_tables.py`; `from record_tables import categories` and `categories()` at `chat_service.py:381,507` |
