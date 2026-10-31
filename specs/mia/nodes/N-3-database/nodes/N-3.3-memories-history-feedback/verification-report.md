# Verification report: Record tables (N-3.3)

**Goal:** G-V1 (iteration), supervised; node N-3.3 (leaf) verified as a black box with the mocks of its neighbours, and in the N-3 integration steps with its real siblings
**Branch:** goal/v1 @ 95052a0 (node files identical to 53c6766: no commit in `53c6766..HEAD` touches `record_tables.py`, its test, the IF-302 contract, mock or suite)   **Parent line of work:** master   **Plan baseline:** plan-baseline-it1, decomp-baseline
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context; it never saw the implementation chat)
**Commits reviewed (all on master before 53c6766):** 768ced8 (T-01 + T-02, one commit, logged), b8b637e (tables `cases`, `behaviours`, IF-302 v1, A-08), 6979e08 (memory `kind`/`status`, v2, A-10), fa7f630 (`workflow_meta`, v3, A-15), 9f4d311 (`reports`, v4/v5, A-23/A-24). Protected: df132a8, cfc3a13, 62914cd, c72c786, b00c099, ed2e0e3 (IF-302 v0..v5), fe819ca (suite, mock, N-3 steps), A-02 (real provider). Scope: REQ-RTB-001..006, IF-302 (provided). Shared findings of the siblings are referenced, not repeated: N-3.1 report F5, F11, F13 (D-158), N-3.2 report F8, F9.

## Verdict (proposal)
**Verified with findings.** All six requirements and IF-302 have tests that pass on the host and in the image; the IF-302 suite passes on the mock and the real module (6/6 each, no skip); N-3 steps 0 to 3 pass. Hand mutation: 10 of 13 mutants killed by the unit tests, 6 of 13 by the contract suite. No finding above Low: two test markers point at the wrong requirements since 9f4d311 (F1), REQ-RTB-001's text names tables that do not exist (F2), a float vote value `1.0` passes (F3), three surviving mutants show untested required-field and value cases (F4), and the mock and the real module answer differently for two inputs the suite does not cover (F5).

## Automated checks (local runs, not CI)
| Check | Result |
|---|---|
| Stage log (CI) | no CI run; all evidence below is local |
| Node tests, host python 3 | `tests/test_record_tables.py` 13 OK |
| Node tests in the image (`podman run --rm --init --network none --user 0 … localhost/mia:latest`, Python 3.12.15, one container) | `test_record_tables.py`, IF-302 suite, N-3 steps 0–3, `test_storage.py`, IF-102 suite: all OK; also via `tools/run_in_image.sh` |
| IF-302 contract suite | 12/12: `_mock` 6 and `_real` 6 (real side = `record_tables`, `tests/helpers/contract.py:795-797`, A-02); no skip |
| N-3 integration steps (A-02) | step_00 (mocks), step_01, step_02 (N-3.3 real), step_03: OK on host and in the image. PostgreSQL: not run; the node is pure Python and the PostgreSQL path calls the same `validate` (`storage.py:54-58`), covered by the N-3.1 report |
| Statistical checks | none: all checks exact and deterministic (test-spec) |
| Protected material | `contracts/IF-302-record-tables.md` equal to `amendments/A-24/IF-302-record-tables.md`; suite and mock equal to `specs/mia/contract-drafts/…` (the installed A-24 drafts); unchanged since ed2e0e3; `contract.py` IF-302 lines and `integration.py:18` (READY has N-3.3) equal to A-02; N-3 steps unchanged since decomp-baseline. No skip/xfail in the suite |
| Traceability (`trace_check.py`) | 93 errors / tree-wide; for this node: ERROR `test-spec.md` has 6 checks and no `## Scenarios` (F8); WARN REQ-RTB-006 "no marker" is a false positive of the script (it reads only the first argument of `mark.req`; `test_record_tables.py:18` names REQ-RTB-006 second) |
| `goal_check.py`, `check_sysml_model.py` | no findings; OK |
| `test_doc_check.py` | `test_record_tables.py` 19 errors (T1 ×3, T2 ×10, T3 ×6); suite 11 (protected) (F8) |
| Mutation testing (scratch copy, 13 hand mutants) | unit tests kill 10; survivors: `user` not required for votes, value `0` accepted, memory `status` accepting a kind (F4). Suite kills 6 (it checks fewer cases by design) |
| Architecture rules | `record_tables` imports nothing; consumers `storage.py:19-23,37,55` (IF-302, modelled) and `chat_service.py:44,52` (`CATEGORIES`, no interface, F6). No SysML part for the Record tables (N-3.1 F13) |
| Static / security / dependencies | no linter configured; stdlib only, no new dependency; no file, subprocess or network access; 44 lines |
| Usability with bad inputs | not applicable (no user-facing surface; errors reach the user through IF-101 votes, `chat_service.py:381-384` checks first) |

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-RTB-001 shared state held | Test | TC-RTB-001 `test_record_tables.py:19` (14 tables exact, all versioned, deletable exactly history/memory/tasks/memos), copy `:28`, free tables `:93`; TC-IF-302-01 both sides; AC-15 (written and read back) outside the node: `test_storage.py` one record per table, N-3 scenario | Pass; text mismatch F2 | yes |
| REQ-RTB-002 run results | Test | TC-RTB-002 `:42` (each of the four fields missing named), non-mapping `:86`; scenario step 2 stores and reads a run | Pass | yes |
| REQ-RTB-003 votes | Test | TC-RTB-003 `:51`, bool value `:62`; TC-IF-302-02 both sides; AC-18: N-3 scenario stores 100 votes and reads them back | Pass with F3, F4 | yes |
| REQ-RTB-004 memory records | Test | TC-RTB-004 `:68`, v2 fields `:115`; TC-IF-302-03/04; AC-24 (deleted record is gone): N-3 scenario on the real Storage | Pass | yes |
| REQ-RTB-005 tasks and memos exact | Test | TC-RTB-005 `:74` (newlines, tabs, quotes, non-ASCII, 20 000 chars; document compared before/after; mutant "validate writes a field" killed) | Pass | yes |
| REQ-RTB-006 source trust | Test | TC-RTB-006 `:25` (versioned, not deletable). AC-3 "an edited trust value survives a restart" has no evidence on the table: the app keeps trust edits in `source_trust.py`'s own file (implementation log, reuse check), nothing writes the table yet (F7) | Pass (definition); AC-3 open | yes |
| IF-302 | Test | suite 12/12, N-3 step_02; `ValueError` for a foreign table `:33`; golden examples 1–3 met | Pass; F5 (mock vs real), F9 | yes |

## Test requirements (M41)
`specs/mia/test-requirements.md` has no TR items (trace_check warning, tree-wide, as for the siblings). Applied as fixed in `test-spec.md`: exact unit checks at stage 1 (met, 0.001 s); IF-302 suite against mock and real (met, stages 1 and 2 locally).

## Goal acceptance (M34, M36)
| Item | Result |
|---|---|
| Requirements in scope verified | 6 of 6 plus IF-302 (REQ-RTB-006 AC-3 not evidenced, F7) |
| Frozen requirements unchanged | G-V1 has no frozen requirements (`goal_check.py`: no findings) |
| Protected checks identical to the baseline + installed amendments | yes |
| Nothing outside the node's parts touched | 768ced8 touches only the module, its test and the log; the later commits change `record_tables.py` as part of features of other nodes, each with its IF-302 amendment |
| Every stop condition logged | yes: the real provider of the suite left to the owner (A-02) |
| Exit criterion | node level only; G-V1 exit is checked in Validate |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-RTB-001 names "summaries" and "chat log" | no such tables; TC-RTB-001 and IF-302 list other ones (F2) | Phase 2 (text) |
| specified, not done | REQ-RTB-006 AC-3 (survives a restart) | the table is defined, not used (F7) | owner, with D-158/FB-04 |
| done, not specified | `validate` refuses a non-mapping for every table with detail `"a document must be a mapping"` (`record_tables.py:28-29`), and a boolean vote value (`:42`) | the mock does neither (F5); IF-302 says nothing | Phase 2 (IF-302 text) |
| done, not specified | tables without required fields (history, accounts, presets, gestures, source_trust) accept any mapping | logged decision; consistent with IF-302 (no required fields listed) | none |
| done, not specified | `chat_service.py` imports `CATEGORIES` from this module | intended by plan T-02 notes, not in IF-302 (F6) | owner |

Human review: specification side via `review-log.md`; code read in full by the reviewer (44 lines).

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | REQ-RTB-001..006, IF-302 | matrix | pass with findings | F2–F4, F7 |
| Performance efficiency | – | 13 tests in 1 ms | ok | not now: no budget for a pure check |
| Compatibility | IF-302 | suite on mock and real; N-3 steps | pass | F5 |
| Interaction capability | – | – | – | not now: no user surface |
| Reliability | REQ-RTB-005 | validation does not change a document (mutant killed) | pass | – |
| Security | TB-edit via Storage | documents are validated before storing; no I/O in the module | pass | – |
| Maintainability | – | 44 lines, no imports; mutation 10/13 | ok | F1, F4, F8 |
| Flexibility | – | new tables added by five amendments without structural change | ok | – |
| Safety | – | – | – | not applicable |

## Open deferrals (M26)
| TD | Requirement | Interim criterion verified? | Target check state | Trigger |
|---|---|---|---|---|
| none for this node | – | – | – | – |

## Review findings
| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F1 | `tests/test_record_tables.py:98-106`: 9f4d311 inserted the `reports` test between the decorator `@mark.req("REQ-WFM-002", "REQ-WFM-006", "IF-302")` and the `workflow_meta` test. Now the `reports` test claims REQ-WFM-002/-006 (it verifies REQ-WFM-038, IF-302 v4/v5) and the `workflow_meta` test has no marker at all | Low (traceability wrong, behaviour tested) | Phase 3 (test file only): give `reports` `mark.req("REQ-WFM-038", "IF-302")` and put the old marker back on `test_workflow_meta_keeps_the_lifecycle_of_a_workflow` |
| F2 | `requirements.md:11` (and `architecture.sysml:3381`): REQ-RTB-001 says the Record tables define "history, summaries, chat log, votes, memory, tasks, memos, presets, gestures and run results"; there is no `summaries` or `chat log` table, while `accounts`, `source_trust`, `cases`, `behaviours`, `workflow_meta`, `reports` exist (TC-RTB-001 in `test-spec.md:11` lists ten others, the code 14). Where summaries and the chat log are held (in `history`?) is nowhere said | Low | Owner decision, then Phase 2 text amendment: proposal: "summaries and the chat log are records of `history`" and list the 14 tables of IF-302 v5 in REQ-RTB-001 and TC-RTB-001 |
| F3 | `record_tables.py:42`: `value not in (1, -1)` accepts `1.0` and `-1.0` (probe), so a JSON vote `{"value": 1.0}` through `POST` vote is stored as a float (`chat_service.py:383` has the same check). The boolean case was found and fixed; the float case was not | Low | Needs test: Phase 3, a failing case `value=1.0` → rule `schema` in `test_record_tables.py`, fix `type(value) is int`; the same in `chat_service.vote` with its own test |
| F4 | Surviving mutants: dropping `user` from the required vote fields; accepting value `0`; memory `status` accepting a kind. TC-RTB-003 checks only a missing `subject` and value `5` | Low | Needs test: Phase 3, loop over each required vote field (as TC-RTB-002 does for runs), value `0`, and `status="fact"`; Phase 2: widen TC-RTB-003's text to "each required field" |
| F5 | Mock and real differ outside the suite: a non-mapping document gives detail = first required field in the mock (`tests/helpers/mocks/if_302_record_tables.py:27-29`) but `"a document must be a mapping"` in the real one (`record_tables.py:28-29`), and `None` for tables without required fields in the mock, `schema` in the real one; a boolean vote value passes the mock (`:36`) and is refused by the real one. IF-302 defines neither case | Low | Owner decision, then amendment (IF-302 text, mock, one suite case): proposal: a non-mapping is rule `schema` for every table, detail free; a vote value is an integer, not a bool |
| F6 | `chat_service.py:44,52` imports `CATEGORIES` from `record_tables` (N-2.2 → N-3.3) without an interface; IF-302 names only N-3.1 as consumer. Intended by plan T-02 ("one place that names them") | Low | Owner: accept and add "the constant `CATEGORIES`" and N-2.2 as consumer to IF-302 (text), or move the list to a shared constants module |
| F7 | REQ-RTB-006 AC-3 ("an edited trust value survives a restart") is not evidenced by the table: trust edits live in `source_trust.py`'s user file; nothing writes `source_trust` to the Storage. Same root as N-3.1 F5 (legacy stores, D-158: FB-04, next iteration) | Low | Owner: name REQ-RTB-006 "partly" in the G-V1 scope row next to REQ-SLY-007 (D-158), or point `Verified by` to the legacy store's test (`test_source_trust.py:106`) |
| F8 | `test-spec.md` has no `## Scenarios` (trace_check ERROR); test_doc_check 19 errors in the node's test file; TC-IF-302-04..06 exist in the suite but not in the root `test-spec.md` (`:144-146` lists 01..03) and `requirements.md:93` says `Verified by: TC-IF-302-01..03` | Low | backlog as N-3.1 F11 / N-3.2 F8; Phase 2 text: add rows 04..06 and `Verified by: TC-IF-302-01..06` |
| F9 | `tests/helpers/contract.py:21` still lists IF-302 in `REAL_NOT_READY`; IF-302 v0 marked "draft" in its header; node `status: Draft` (`decomposition.yaml:246`) | Low | as N-3.2 F9 (one text amendment for both) |
| F10 | Process: b8b637e, fa7f630 and 9f4d311 changed `record_tables.py` 3 to 46 minutes before the matching IF-302 amendment was installed (A-08, A-15, A-24); 9f4d311 already followed v5 ("versioned") while only v4 ("not versioned") was installed. The final state matches the installed contract; T-01 and T-02 share one commit (logged) | Info | none; noted for the team |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| – (candidate: F7, if the owner marks REQ-RTB-006 partly for G-V1) | | |

## Notes for Phase 7 (validation)
- When the legacy stores move into the database (FB-04), check that a trust edit and a summary appear in the tables named here, and survive a restart.

## Reproduction
Mutation script and probes ran in a scratch copy (`/tmp/claude-1000/-home-maldun-prog-Python-MIA/1251f948-2f8f-400a-acca-407c0b962dbf/scratchpad/n33-mut`, removed afterwards). Probe: `validate("votes", {"user":"a","subject":"m","category":"service","value":1.0})` → `None`.
