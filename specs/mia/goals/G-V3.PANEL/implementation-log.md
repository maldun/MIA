# Implementation log: G-V3.PANEL (the Skill run view)

Goal: G-V3.PANEL   Line of work: goal/v3 (the worktree's branch; the plan names goal/v3.panel, which was not created, owner's setup)   Supervision: supervised

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Table skill_runs in the Record tables and the storage | done | `39bf66b` (code and unit test); spec change `REQ-RTB-001` in its own commit | TC-RTB-007; TC-IF-302-01 and -08 and TC-IF-102-12 on the mock, the real file backend and the PostgreSQL contract run (`tools/contract_postgres.sh`, 12 tests); the old unit tests of record tables, storage, storage copy, migrate and database stack; the full unit suite: 2071 tests, one error, the known `test_tailscale` timeout (not touched by G-V3) | one entry in `record_tables.py` (TABLES, deletable set, REQUIRED); the storage layer and the backends needed no change |
| T-02 | done | (this commit) | TC-WFM-130..135, 137, 138 (8 tests) green; `test_task_monitor`, `test_chat_tasks`, `test_core_names_no_skill` green | `skill_runs.py` replaced the stub; `TaskMonitor.update` has the optional `elements` argument and `state()` the key `elements` (D-309) |
| T-03 | done | | | note approved |
| T-04 to T-10 | open | | | |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| The unit test of the table list (`tests/test_record_tables.py`, TC-RTB-001, TC-RTB-006) asserts exactly the 14 tables and the deletable set of four of the approved REQ-RTB-001 and fails with the 15th table | T-01 | the same test, now naming 15 tables and the deletable set of five |

## Plan amendments
None. The conflict of the finding was ruled by the owner (below); A-141 (approved 2026-11-08, D-302) already names the 15 tables.

## Stop conditions hit
| Date | Task | Condition | Escalated to | Outcome |
|---|---|---|---|---|
| 2026-11-08 | T-01 | a requirement and a test contradict the change the plan prescribes: REQ-RTB-001 (Verified) says 14 tables, A-141 says 15, the plan says "all other tests unchanged" | the owner (maldun) | change the requirement text (15 tables of IF-302 v8, status Approved again) and the unit test; done and marked approved in the review log |

## Unspecified behavior (decisions no requirement covers)
- T-02: on `end` with state `done` all phases of the record become `done`; with `failed` or `stopped` the phase states stay as they were. A phase name that is not declared at `start` changes the monitor's phase text only, not the phase list. A history delete is answered with one `skill_run_changed {id: null}` even if the account had no run record.

## Decisions
- REQ-RTB-001 now reads "the 15 tables of IF-302 v8 ... reports and skill_runs"; its status goes from Verified to Approved until the next verification; the check row TC-RTB-001 in the N-3.3 test-spec names the 15 tables and the deletable set of five; `architecture.sysml` (generated) follows.
- The contract text of IF-302 v8 and IF-102 v4 and their suites were already installed in the Plan phase; T-01 changed no protected file.

## Open questions for Phase 4
- IF-302 v9 (A-143) adds `elements` as an optional field of `skill_runs`: validation leaves optional fields free, so T-01 needed nothing for it; T-02 stores the field.
- `REQ-RTB-001` changed after its verification: Verify re-verifies it with TC-RTB-001.
