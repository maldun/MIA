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
- A-61 (2026-10-31, D-161 F3, F5, F8; installed in 849ac36): IF-302 v6, a non-mapping is rule `schema` in every table and a vote value is an integer; mock, TC-IF-302-07, root test-spec rows TC-IF-302-04..07, node `Verified by: TC-IF-302-01..07`. Drafts `specs/mia/amendments/A-61/IF-302-record-tables.md`, `specs/mia/contract-drafts/tests/{helpers/mocks,acceptance/contract}/…if_302…`; install `bash tools/apply_amendment_a61.sh --do` on goal/v1. Checked on a scratch copy: look-only changes nothing; the new suite is red on the old mock (TC-IF-302-07 `_mock`); after `--do` the suite is 14/14 (mock and real), the test-spec has 7 TC-IF-302 rows, a second look-only finds nothing to do.
- A-61, IF-101 part (D-162; installed in 849ac36): the IF-101 mock refuses a vote of 1.0 (`type(value) is not int`), IF-101 one version up (the vote value is the integer 1 or -1), TC-IF-101-32 and its test-spec row; all four BUILT FROM THE INSTALLED FILES. Checked on a scratch copy of goal/v1 @ e89ffa8 with A-54 and A-57 installed (IF-101 v13) plus the A-61 files and the F3 line of `chat_service.py`: look-only changes nothing; `--do` gives IF-101 v14 and the rows; IF-101 suite in the image 64 tests OK (3 skips, as before); with the old mock and goal/v1's `chat_service.py` the new case fails on both sides (2 failures), so the real side needs the merge of v1-n33b first; a second `--do` and A-57's look-only find nothing to do. Seen on the way: A-54's new case is also called TC-IF-101-30, like the existing files case (A-54's, not changed here).

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
| F6 `chat_service.py` gets the categories through IF-302 | replaced by D-162 | `df6ca82`, removed in `test(record_tables)` | `test_record_tables.py`, `test_chat_answers.py` OK, no skip | D-162: the categories go through IF-102 (`categories()`, A-59, N-3.1 branch), not IF-302; the two skip-guarded tests of `df6ca82` that expected `categories()` in IF-302 are removed; `chat_service.py`'s import is left to N-3.1 |
| F2 REQ-RTB-001 lists the 14 tables of IF-302 v5 | done | `docs(record_tables)` | `check_sysml.sh specs/mia/architecture.sysml` ok, `check_sysml_model.py` OK | requirements.md (text, intro, History "2026-10-31 D-161"), `architecture.sysml` REQ-RTB-001 doc; summaries and the chat log are records of `history`. Node test-spec: TC-RTB-001 lists the 14 tables; TC-RTB-003 widened to each required field and the wrong values 0, 1.0, -1.0, True (F4, Phase 2 part). The parent texts (N-3 REQ-DB-002, N-3.1, NFR-8) still name "summaries, chat log" as shared state, which stays true |
| A-61 draft (F3, F5, F8) | installed (849ac36) | `plan(record_tables)` | scratch copy: IF-302 suite 14 OK after `--do` (mock and real) | see Plan amendments |
| D-162 F6 rework | done | `test(record_tables)` | see the F6 row | the `df6ca82` tests removed |
| A-61 IF-101 part (D-162) | installed (849ac36) | `plan(record_tables)` | scratch goal/v1 + A-54 + A-57: IF-101 suite 64 OK, IF-302 suite 14 OK after `--do` | see Plan amendments |

## Stopped: F6 (the categories through IF-302), for the owner (answered by D-162: option (b), IF-102 in A-59)
`decomp_check.py` on a scratch copy with N-2.2 added to the consumers of IF-302 gives ERROR "IF-302: provider and consumers are not siblings: the parent decides interfaces between its children; route a deeper need through the boundary of the common ancestor" (N-2.2 is in N-2, N-3.3 in N-3; IF-302 is decided by N-3). So "chat_service gets the categories through IF-302" needs more than one small read operation: an interface across N-2/N-3 or an exception in `decomposition.yaml`. Not drafted in A-61. Options: (a) `categories()` in IF-302 and N-2.2 as consumer with a reasoned exception in `decomposition.yaml` (decided by N-0); (b) a read operation `categories()` in IF-102 (N-3.1's interface, the one N-2.2 already consumes) that hands on IF-302's list: amendment at N-3.1 (A-59 is in work there); (c) a shared constants module outside both nodes; (d) accept the import as an architecture exception in IF-302's text. The two skipped tests of `df6ca82` assume (a) or a `categories` name in `chat_service`; with (b) or (c) the consumer test changes.

## Re-verification fixes (D-170, 2026-10-31, branch v1-n33c)
| Finding | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| R3 log and plan text | done | `docs(record_tables)` | – | A-61 marked installed (849ac36); plan T-01 "Definitions of the 14 record tables" |
| R1, R2 amendment A-67 (draft, not installed) | drafted | `plan(record_tables)` | scratch copy of goal/v1 (d502c4e) + v1-n33c after `--do`: IF-302 suite 14 OK (mock and real), `test_record_tables.py` OK, N-3 step_02 OK; all `tests/test_*.py` in the image: 164 files, failing only the known `test_amendment_report` and `test_harness` (rt_edit) | IF-302 v7: deletable are exactly `history`, `memory`, `tasks`, `memos`; TC-IF-302-01 compares the whole set; `contract.py` IF-302 reason "unused: real_subject gives record_tables" (R1); test-spec row TC-IF-302-01; History of IF-302 in the node requirements. All five files built from the installed ones (A-62, A-65, A-66 may come before or after). Fail first: four mutants (mock and real: `history` not deletable, `source_trust` deletable) pass the old suite and fail the new one; a second `--do` finds nothing to do. Install: `bash tools/apply_amendment_a67.sh --do`. Note `specs/mia/amendments/A-67/A-67-note.md` |
