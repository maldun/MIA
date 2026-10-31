# Hand-over for the next session (written 2026-10-31, night; updated late night): G-V1, verification queue, merge round 4 (superseded by `handover-2026-11-01.md`)

This is the newest hand-over. It continues `handover-2026-10-31-pm.md`, which has the owner's rules, the lessons and how to run things; read that first. Then read `CLAUDE.md`, `specs/mia/goals/G-V1/goal.md`, `specs/mia/review-log.md` (**D-137 to D-169**), and the logs and reports of the node you work on. The checks only the owner can do are in `specs/mia/owner-checklist-2026-10-31.md` (section A done; B and C open).

Next free ids: **D-170, A-67, FB-07, TD-08**.

## State of goal/v1 (after merge round 3, `bee8ead`)
- Merged: every branch up to round 3: `v1-a53`, `v1-n42-ops4`, `v1-n13c/d/e`, `v1-n21b`, `v1-n24-int`, `v1-n22`, `v1-n12c`, `v1-n31b`, `v1-n32b`, `v1-n33b`, `v1-n11b`, `v1-n41b`.
- Installed and committed: A-52 to A-63. Each is equal to its draft. A-54's IF-101 lines carry A-57's lines, and IF-101 is now at v15.
- Tests:
  - A full run after round 3 was in progress at the time of writing.
  - After round 2 the run was green apart from the known failures:
    - `test_amendment_report` (no git in the image);
    - `test_harness` (rt_edit has 2 cases and wants 30);
    - `tests/acceptance/test_benchmarks.py` (the gate-time baseline in `benchmarks/baseline.json` was never measured).
  - The IF-101 and IF-104 contract suites fail on the host because flask is missing there; they pass in the image.

## Merge round 4 (being prepared)
| Branch | Content | Amendment |
|---|---|---|
| `v1-fix167` | N-2.1: login throttle, `test_api_events` in a temp folder. N-1.2: missing presets added at start, deleted presets remembered (D-169), a second shocked face cancels the pending return, the load-timeout test, the RUNBOOK line. All web_app tests in a temp folder plus a guard test (D-169). | A-64 (stage-3 step for TC-API-013; a skip fails) |
| `v1-n31c` | N-3.1 re-verification: listener guard test, NaN/inf/non-string ids refused, REQ-SLY-006 text, Scenarios section | A-65 (IF-102 v3 Errors row, TC-IF-102-11) |
| `v1-n32c` | N-3.2 re-verification: the docstring fix | A-66 (JS mock refuses `2.0`, TC-IF-104-06 row, TD-06 lines) |

Trial-merge the three on a scratch copy of goal/v1, install A-64, A-65 and A-66, and run everything. Then give the owner the commands. Afterwards commit the installed files, new and deleted ones included (`git status` first).

## Node states
| Node | State |
|---|---|
| N-2.4.1, N-2.4.2 | Verified with findings |
| N-2.4.3, N-4.2 | Verified with accepted deviations |
| N-2.4 integration | done. verify_claim keeps v1; gate versus single moved to the next iteration's Plan (D-164) |
| N-2.1 | re-verified: Verified with accepted deviations (fixes of D-167 in round 4) |
| N-1.2 | re-verified: Verified with accepted deviations (fixes of D-167/D-169 in round 4; eye checks C0 to C5) |
| N-1.3 | re-verification 3: Verified with accepted deviations; R1 (3 s window) and R2 (serving folder) merged in round 3, **re-verify** |
| N-3.1 | re-verified: Verified with accepted deviations (D-168 fixes in round 4) |
| N-3.2 | re-verified: Verified with accepted deviations (D-169 fixes in round 4) |
| N-3.3 | **re-verification running** |
| N-1.1 | was Not verified; fixes merged in round 3 (queue places stay counted, FB-06): **re-verify** |
| N-4.1 | was Not verified; fixes merged in round 3 (latency, pin id, IF-105 wired, `--pin`, holdout guard, A-63): **re-verify** |
| N-2.2, N-2.3, N-2.5 | **first Verify** |
| N-5 | Verify after its files settle (T-02 waits for FB-02) |

Verification queue, one after the other (owner): N-3.3 (running), N-1.1, N-4.1, N-1.3, N-2.2, N-2.3, N-2.5.

## Scope changes of tonight (goal.md)
- "Partly" in G-V1:
  - REQ-SLY-007 and REQ-RTB-006 (FB-04);
  - REQ-GTB-004 (TD-06);
  - REQ-CLV-010 (FB-05);
  - REQ-EVL-005 and -009 (next iteration's Plan);
  - REQ-EVL-003 (TD-07).
- New feedback items: FB-04 (importers and trust edits into the record table), FB-05 (votes on reactions, series), FB-06 (queue places from the server).
- FB-02 gained the graph rule order and the unchecked cases.

## After the queue and round 4
1. Re-verify what round 4 changes, as far as the verifications above did not cover it.
2. Integration steps N-1, N-2, N-3, N-4, N-5, then N-0.
3. The `number_check` rule (D-132), the rest of the WorkflowRuns wiring, TD-01 to TD-05, and the owner's reading of the Draft Scenarios sections (N-1.1, N-4.1).
4. Goal-level Verify, Commit, Deploy, Validate (VAL-001, VAL-003 to VAL-006).

## Lessons of tonight
- A stage serves the checkout it was first started from. `start_testing.sh` now prints the real folder of a running container and warns when it differs.
- Commit only explicit paths while the owner installs in the same worktree (`git commit -- <path>`), and check for `MERGE_HEAD` first.
- An install commit must include the new and the deleted files as well as the modified ones. `git status --short` shows them, but `git add -u` misses the new ones.
- A test that walks the repository must skip hidden folders: git-ignored local-model drafts live in `.local-tasks/`.
- Log files and test files that several branches append to conflict at every merge. Resolve them on the branch by keeping both sides.
- Verifiers must keep temp files in their scratchpad, never in `/tmp` directly.
