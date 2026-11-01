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

# Re-verification (after v1-n33b, v1-n31b and the A-59/A-61 install)

**Goal:** G-V1 (iteration), supervised; node N-3.3 (leaf), black box with its neighbours' mocks, and in the N-3 integration steps with its real siblings
**Branch:** goal/v1 @ 81f0ffd (node code as of 0e8e767; `chat_service.py` and `storage.py` as of acf1320; later commits are docs only)   **Plan baseline:** plan-baseline-it1, decomp-baseline   **Date:** 2026-10-31
**Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context; it never saw the implementation chat)
**Commits reviewed:** v1-n33b (merged in 0e8e767): a626341 (F1), 5b602cb (F3, F5), 1aa6d4d (F4), df6ca82 and 73e5ef8 (F6, replaced by D-162), the `docs(record_tables)` and `plan(record_tables)` commits (F2, A-61 draft); v1-n31b: 2ae1fc5 (`categories()` in the storage), 6ba6322 (chat service asks IF-102); 849ac36 (A-59, A-60, A-61 installed by the owner). Inputs: D-161, D-162, IF-302 v6, IF-101 v14 (vote value), IF-102 v2 `categories()`, sibling re-verifications N-3.1 and N-3.2.

## Verdict (proposal)
**Verified with accepted deviations.** F1, F3, F4 and F5 are closed with tests that fail on a mutant that restores the old behaviour (table below), on the real module, the chat service, the IF-302 mock and the IF-101 mock; F6 is closed by D-162 (no module outside N-3.1 imports `record_tables`; three mutants of the chat service and the storage are caught); F2 is closed in `requirements.md`, `architecture.sysml` and TC-RTB-001; F7 is decided (REQ-RTB-006 partly, `goals/G-V1/goal.md:74`, `feedback/FB-04.md:14`). The installed IF-302, IF-101 and IF-102 files equal their A-59/A-61 drafts (look-only runs: all unchanged). Open: F8 (readability backlog) and the rest of F9 (R1). New findings are low: the IF-302 suite does not pin the deletable flags it does not name (R2), and log/plan residue (R3). None blocks the merge.

## Automated checks (local runs, not CI)
| Check | Result |
|---|---|
| Node tests, host | `tests/test_record_tables.py` 17 OK |
| IF-302 suite, host | 14/14 (`_mock` 7, `_real` 7, real = `record_tables` via `contract.py:841-843`), no skip |
| Consumers, host | `test_chat_answers.py` 12 OK, `test_chat_behaviour.py` 10 OK, `test_storage.py` 17 OK, IF-102 suite 20 OK. The IF-101 suite errors on the host's `_real` side (no flask on the host; expected) |
| In the image (`podman run --rm --init --network none --user 0 … localhost/mia:latest`, one container at a time) | `test_record_tables.py` 17, IF-302 suite 14, IF-101 suite 64 (2 skips: TC-IF-101-04, -17, unbuilt events, as before), IF-102 suite 20, `test_chat_answers.py` 12, `test_chat_ops_api.py` 4, N-3 steps 00–03: all OK |
| IF-101 vote cases | TC-IF-101-32 (`test_if_101_chat_api.py:576`) green on mock and real in the image; TC-IF-101 vote/score cases green |
| Protected material vs. A-59, A-61 | `contracts/IF-302-record-tables.md` = `amendments/A-61/…` (`cmp`); IF-302 mock and suite = `contract-drafts/…` (`cmp`). Look-only runs of `tools/apply_amendment_a61.sh` and `…a59.sh` (TMPDIR in the scratchpad): every file "unchanged (identical)", incl. IF-101 contract, mock and suite, IF-102 contract, mock, suite, `contract.py`, `stages.yaml`, `specs/mia/test-spec.md` and this node's `requirements.md`. Since the first report only a262376, 424c329 and 849ac36 (owner installs) touch `tests/acceptance`, `tests/helpers`, `tests/integration`, `contracts`, `stages.yaml`; no skip/xfail in the IF-302 suite |
| trace_check | exit 1 tree-wide (97 errors). This node: ERROR `test-spec.md` has no `## Scenarios` (F8); WARN REQ-RTB-006 "no marker" (false positive, as before: `test_record_tables.py:18` names it second); WARN TD-01..04, -06, -07 not listed here (listed below now) |
| test_doc_check | `test_record_tables.py` 19 errors (the 19 of F8; the four tests added in v1-n33b pass the rule); IF-302 suite 13 (11 of F8 + 2 of the protected TC-IF-302-07) |
| `goal_check.py --parent-ref master` | no findings |
| `check_sysml_model.py`, `check_sysml.sh specs/mia/architecture.sysml` | OK; 0 errors, 0 warnings |
| Architecture rules | `record_tables` imports nothing; its only importer outside the tests is `storage.py:24` (IF-302, modelled). `chat_service.py` has no `CATEGORIES` and no import of `record_tables`; it asks `self._votes.categories()` (`:384`, `:514`; IF-102 v2) |
| Static, security | no linter configured; fix commits read in full (one line in `record_tables.py:42`, one in `chat_service.py:386`); no new dependency, no I/O |

### Mutation checks (scratch export of HEAD, removed)
| Mutation | Unit tests | Contract suite |
|---|---|---|
| `record_tables.py:42`: type check removed (float and bool pass) | killed | IF-302 killed |
| `:42`: only bool refused (old rule, float passes) | killed | IF-302 killed |
| `:28`: non-mapping refused only where fields are required | killed | IF-302 killed |
| `user` not required for votes (F4) | killed | IF-302 survives (by design: suite checks fewer cases) |
| value 0 accepted (F4) | killed | IF-302 survives |
| memory `status` accepts a kind (F4) | killed | IF-302 survives |
| `chat_service.py:386`: type check removed | `test_chat_answers` killed | IF-101 `_real` killed (in the image, 2 failures) |
| `:386`: only bool refused | `test_chat_answers` killed | – |
| `:384` / `:514`: the chat service keeps its own list of categories | `test_chat_answers` killed (both) | – |
| `storage.py:137`: categories reordered | `test_storage` killed | IF-102 killed |
| IF-302 mock: float allowed / non-mapping only with required fields | – | IF-302 `_mock` killed |
| IF-101 mock: only bool refused (old rule) | – | IF-101 `_mock` killed (in the image, 1 failure) |
| `history` not deletable / `source_trust` deletable | killed | IF-302 survives (R2) |

## Earlier findings
| # | Status | Evidence |
|---|---|---|
| F1 | closed | `test_record_tables.py:149` `mark.req("REQ-WFM-038", "IF-302")`, `:157` back on the `workflow_meta` test |
| F2 | closed | `requirements.md:11` (14 tables, summaries and chat log are `history` records, History D-161), `architecture.sysml:3398`, node `test-spec.md` TC-RTB-001 |
| F3 | closed | `record_tables.py:42`, `chat_service.py:386`; tests `test_record_tables.py:92`, `test_chat_answers.py:108`, TC-IF-302-07, TC-IF-101-32; mutants of the old rule caught on all four |
| F4 | closed | `test_record_tables.py:62` (each vote field), `:76` (value 0), `:179` (`status="fact"`); TC-RTB-003 text widened (node `test-spec.md`); 3 mutants caught |
| F5 | closed (A-61) | IF-302 v6 text and golden 4; mock `if_302_record_tables.py:27,40`; TC-IF-302-07; `test_record_tables.py:132` for all 14 tables; mock and real agree now |
| F6 | closed (D-162, A-59) | IF-102 `categories()` (`storage.py:135-137`, TC-IF-102-10, `test_storage.py:208`); `test_chat_answers.py:123` (a storage with one category decides; no `CATEGORIES` in `chat_service`), `:151` (runs on the IF-102 mock); the `df6ca82` tests removed |
| F7 | decided (D-161): REQ-RTB-006 partly | `goals/G-V1/goal.md:74`, `feedback/FB-04.md:14`; TC-RTB-006 (definition) green; AC-3 has no evidence in G-V1 (accepted deviation) |
| F8 | open, backlog | unchanged: no `## Scenarios`, 19 + 13 test_doc_check errors; the root `test-spec.md` rows TC-IF-302-04..07 and `requirements.md:93` `Verified by: TC-IF-302-01..07` are fixed (A-61) |
| F9 | partly closed | IF-302 header "draft v0" dropped (v6). Still open: R1 |
| F10 | info | the fixes this time were made before the amendment, and the amendment was installed after the merge, as the log says (the real side of TC-IF-101-32 needed v1-n33b) |

## Verification matrix (changes against the first report only)
| Requirement | Result now |
|---|---|
| REQ-RTB-001 | Pass; text matches the code (F2) |
| REQ-RTB-002, -004, -005 | Pass, unchanged |
| REQ-RTB-003 | Pass: each required field, 0, 1.0, -1.0, True, False refused in the module and the chat service; AC-18 through the N-3 scenario (step_03 green) |
| REQ-RTB-006 | Partly, accepted by the owner (D-161, FB-04): table defined, versioned, not deletable (TC-RTB-006); AC-3 next iteration |
| IF-302 v6 | Pass: 14/14 on mock and real, golden 1–4 met; mock and real agree on all probed inputs |

## Specification vs. code (M42), new items
| Direction | Item | Destination |
|---|---|---|
| done, not specified | `history` is deletable and `accounts`, `presets`, `gestures`, `source_trust` are not (`record_tables.py:9`, mock `:5-9`, TC-RTB-001); IF-302 names only `memory`, `tasks`, `memos` as deletable and `votes`, `runs` as not, and its suite pins only those five | R2 |

## Open deferrals (M26)
| TD | Requirement | Interim criterion verified? | Target check state | Trigger |
|---|---|---|---|---|
| none for this node | REQ-RTB-006 partly is a scope decision (D-161, FB-04), no relaxed check: TC-RTB-006 runs and passes | – | – | – |
| TD-01..04, TD-06, TD-07 | not of this node | – | – | listed for trace_check only |

## New findings
| # | Finding | Severity | Destination / proposal |
|---|---|---|---|
| R1 | Rest of F9: `tests/helpers/contract.py:20` still gives IF-302 the reason "N-3.3 Record tables not integrated yet" although `real_subject` returns `record_tables` since A-02 (`:841-843`); `decomposition.yaml:446` IF-302 `version: v0` (contract v6), `:246` node `status: Draft`. D-161 sent F9 to "the next amendments"; A-61 did not take it up | Low | amendment (text only), with the next one touching `contract.py`: the reason as A-60 wrote it for IF-301 (`"unused: real_subject gives record_tables"`); version and status in `decomposition.yaml` at the gate (one change with N-3.2 R3) |
| R2 | IF-302 does not say which tables other than `memory`, `tasks`, `memos`, `votes`, `runs` are deletable; the code and the mock make `history` deletable and the rest not. The suite pins only the five named, so a provider with `history` not deletable or `source_trust` deletable passes it (two mutants survive the suite; the node test kills them). REQ-RTB-006 "not deletable" is thus guarded only by the node test | Low | owner decision, then amendment: IF-302 note "deletable are exactly `history`, `memory`, `tasks`, `memos`" and one line in TC-IF-302-01 (`deletable` set equal), with the next IF-302 amendment |
| R3 | Residue: the implementation log still marks A-61 "drafted, not installed" (`implementation-log.md:18,35,40`) though 849ac36 installed it; plan T-01 is still "Definitions of the ten record tables" (`plan.md`) | Info | Phase 3 log line; plan text at the next node amendment |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| REQ-RTB-006 partly: AC-3 (a trust edit survives a restart through the table) not evidenced | D-161, FB-04 (legacy stores into the database next iteration) | owner |

## Not checked here
- CI: none; all results are local feedback runs.
- PostgreSQL path (N-3.1's stage-3 step, A-59); the node is pure Python and the storage calls the same `validate`.
- The whole test suite: only the node's file, its consumers named above, the IF-101/102/302 suites and the N-3 steps; the known failures (`test_amendment_report`, `test_harness` rt_edit, `tests/acceptance/test_benchmarks.py`) were not re-run.
- The log's claims that each fix test was red first (checked indirectly: every fix is caught by a mutant restoring the old code).

## Notes for Phase 7
- Unchanged: with FB-04, check that a trust edit and a summary land in `source_trust` and `history` and survive a restart.
