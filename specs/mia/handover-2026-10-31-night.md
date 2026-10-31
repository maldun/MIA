# Hand-over for the next session (written 2026-10-31, night): G-V1, the N-3 Verifies, big merge round

This is the newest hand-over. It continues `handover-2026-10-31-pm.md`, which has the owner's rules, the lessons and how to run things; read that first. Then read `CLAUDE.md`, `specs/mia/goals/G-V1/goal.md`, `specs/mia/review-log.md` (**D-137 to D-161**), and the logs and reports of the node you work on. The checks only the owner can do are in `specs/mia/owner-checklist-2026-10-31.md`.

Next free ids: **D-162, A-62, FB-05, TD-07**. A-52 to A-58 are drafted and wait for the big merge round. A-59, A-60 and A-61 are being drafted by the N-3 fix agents.

## Node states

| Node | State | Open |
|---|---|---|
| N-2.4.1 Pipeline runner | Verified with findings | low findings (see the pm hand-over) |
| N-2.4.2 Tools and sandbox | Verified with findings | the `number_check` rule (D-132 conflict) |
| N-2.4.3 | Verified with accepted deviations | – |
| N-2.4 integration | done on `v1-n24-int` (AC-2 reworded, check_run `skipped` event, A-55) | verify_claim keeps v1; gate versus single is decided on the holdout in the goal's Verify (D-159); branch `v1-n24-gate5` stays unmerged |
| N-4.2 Operation | Verified with accepted deviations (D-148) | owner checklist B1 to B6 |
| N-1.3 Voice playback | fixes on `v1-n13c` and `v1-n13d` (D-157: the page drops lines after Stop; `start_testing.sh` prints the folder and commit it serves) | owner repeats A3 (full app rebuilt from goal/v1) and A4 (stub started from the goal-v1 worktree) after the merge, then re-verify |
| N-1.2 Character view | fixes on `v1-n12c` (F1, F2 poll 1.5 s, F4, F5 = A-58, F7 to F10; D-159) | install A-58, re-verify; put the eye checks on the checklist |
| N-2.1 API and accounts | fixes on `v1-n21b` | re-verify after the merge |
| N-2.2 Chat agent | done on `v1-n22` (A-56, A-57) | Verify |
| N-3.1 Storage layer | **Verified with findings** (`ac06af9`), D-158; REQ-SLY-007 partly (FB-04) | fixes running on `v1-n31b` (F1, F2, F4, F5 migrate close, F7 delete notice, F8; A-59 = PostgreSQL stage step and IF-102 delete case) |
| N-3.2 Workflows and context graphs | **Verified with findings** (`95052a0`), D-160; REQ-GTB-004 partly (TD-06); rule order and unchecked cases go to FB-02 | fixes running on `v1-n32b` (F1, F2 limit is a positive integer, F4 part, F7; A-60 = IF-301 text and mock) |
| N-3.3 Record tables | **Verified with findings** (`123c1bc`), D-161; REQ-RTB-006 partly (FB-04) | fixes running on `v1-n33b` (F1, F3/F5 `schema`, F4, F6 categories through IF-302, F2 text; A-61) |
| Not verified yet | N-1.1, N-2.3, N-2.5, N-4.1, N-5 | – |

## Big merge round (in progress at the time of writing)
- Branches: `v1-a53`, `v1-n42-ops4`, `v1-n13c`, `v1-n21b`, `v1-n24-int`, `v1-n22`, `v1-n13d`, `v1-n12c`, merged in this order.
- `v1-n13d` conflicted with `v1-n13c` (the N-1.3 log) and with `v1-n22` (`tests/test_converse_behaviours.py`: both sides added tests). Both were resolved on `v1-n13d` (`cb12b57`, `9e8085f`), keeping every addition.
- The trial merge in the scratchpad (`trialmerge-big`) is clean. Its full test run was still going when this was written.
- After the owner merges, the amendments are installed in this order: **A-52, A-53, A-54, then A-57, A-55, A-56, A-58** (A-57 is built from the installed IF-101, which A-54 changes). Commit each installed file after comparing it with its draft.
- A later round merges `v1-n31b`, `v1-n32b` and `v1-n33b` and installs A-59, A-60 and A-61. All three can touch `tests/helpers/contract.py`, so each builds its lines at install time from the installed file.

## Owner checklist
- A1 and A2: ok.
- A3 and A4: not ok. Repeat them after the merge (see N-1.3 above).
- The `up()` helper gives `000` when the chat-on-stub stage is not running. This note is now in the checklist (`14b935c`).
- B1 to B6: open.

## After the merge round
1. Re-verify N-2.1, N-1.3 (after A3 and A4), N-1.2 and N-3.1 to N-3.3 (after their fixes). Verify N-2.2.
2. Verify N-1.1, N-2.3, N-2.5, N-4.1 and N-5.
3. Integration steps N-1, N-2, N-4, N-5 and N-0.
4. The `number_check` rule (D-132), the WorkflowRuns wiring, and TD-01 to TD-05 (TD-05 is still only a proposal in `handover-2026-10-30.md`).
5. Goal-level Verify (including the gate-versus-single decision on the holdout, D-159), then Commit, Deploy and Validate.

## Lessons of tonight
- A stage serves the checkout it is started from. Start owner checks from the goal-v1 worktree; `start_testing.sh` now prints which folder it serves.
- Log files conflict on every parallel branch of a node. Resolve them on the branch by keeping both sections in date order, never during the owner's merge.
- `tests/acceptance/test_benchmarks.py` fails on the gate-time baseline in `benchmarks/baseline.json`, which was never measured. The N-2.4 agent saw this; it is not a regression.
