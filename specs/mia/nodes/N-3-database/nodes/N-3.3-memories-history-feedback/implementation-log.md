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
