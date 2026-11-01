# A-82: the 29 root checks TC-MIA-001 to -029 become readable for the trace check

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The handover said 44 TC-MIA tests were missing from the test tables and "needed before the final N-0 step". The cause is a format one. The 29 rows of `specs/mia/test-spec.md` read `| TC-MIA-001 (AC-1) | ...`; `trace_check.py` reads a test-spec row only when its first cell is the id alone, so these 29 checks were unknown and 44 requirement lines (FR/NFR "Verified by TC-MIA-nnn") reported "in no test-spec table or scenario, test or eval suite". The checks, their requirements, stages and expected results were all in the table.

## What changes (built from the installed file)
| File | Change |
|---|---|
| `specs/mia/test-spec.md` | `| TC-MIA-nnn (AC-n) |` becomes `| TC-MIA-nnn |` in 29 rows; nothing else. The acceptance criterion stays in `requirements.md` ("Acceptance criterion: AC-n") and in `specs/mia/tc-mia-status.md`. |

Refused when the number of rows with the suffix is neither 29 nor 0; a second run says "nothing to do".

## Effect on the trace check (scratch copy)
Error lines 91 to 47: the 44 "Verified by TC-MIA" lines go. The line "test-spec.md: 128 check(s) but no '## Scenarios'" becomes 154 checks (the same one line: the root table has no scenario section, a known gap of the plan, 19 test-specs). Nothing else changes; `check_sysml_model` OK.

## What is not claimed
The rows being readable does not mean the checks are done. `specs/mia/tc-mia-status.md` is the inventory: 1 row has a root-level test of its own now (TC-MIA-020, `tests/test_system_inspection.py`, new, unprotected), 17 are held by node and integration tests with no single system test, 9 are stage 4 (eval, benchmark, statistical; they need `eval-spec.md` criteria and pins), 2 are out of G-V1 or after the field test (TC-MIA-026, -008). Whether the B rows are met is for the root Verify.
