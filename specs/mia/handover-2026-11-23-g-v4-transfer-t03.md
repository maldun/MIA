# Handover: G-V4.GRAPHSTORE.TRANSFER Implement, T-03 (2026-11-23)

For a new session in the worktree `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md`, this file, and load `dev-workflow`, `implement-phase`, `agent-app` (no eval path in TRANSFER: pure storage logic). Decisions: questionnaire, recommended option first; full absolute paths.

## State
- T-01 done (`bc2b100a`), T-02 done (`dc373458`, "feat: T-02 durable files, cut back"); details, regression set and decisions in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/implementation-log.md`.
- Built in T-02 for T-03: `FileBackend._replace` (fsync file, rename, fsync folder) under every file write; `cut(table, id, n)` on both backends (keeps 1..n; nothing written when nothing is above n; `n == 0` removes the record); `FileBackend.put_file(path, text)` with `path` relative to the root, durable. The format marker is **not** written yet (decided for T-05, logged).
- Red now (expected): `test_transfer_move.py` 1 (TC-SLY-021 sync half); `test_transfer_sync.py` 8 + 1 skipped (TC-SLY-030 until VIEW); `test_transfer_interrupt.py` 6; `test_transfer_sets.py` 6. Known reds of `goal/v4`: `test_decide_guard.py`, `test_judge_calibration.py`.
- No plan amendment, no stop condition, no owner item open.

## T-03: Lag, sync, aside, lock, commands (`plan.md`)
- Implements REQ-SLY-024 to 028, 038, 039. Turn green: TC-SLY-024 to 028 (`test_transfer_sync.py`), TC-SLY-038 (`test_transfer_interrupt.py`), TC-SLY-039 (`test_transfer_sets.py`, class Commands), TC-SLY-021 whole.
- Touches: `graph_store_transfer.py` (`lag`, `sync_store`: aside file through `put_file`, then cut back header first, then members, then the live versions members first; a graph only on the copy removed header first after its aside file; `copy_lock` with `fcntl.flock`); `migrate.py` (`lag`, `sync`); unit tests.
- Reuses the prototype `graph_store_sync.py` on `prototype/g-v4` (`lag`, `_set_aside`, `sync_store`), with the cut back of D-466 instead of `_remove_from`; the aside path in the answer is relative to the copy (REQ-SLY-027).
- Done when: listed tests green, regression set holds; the defects "removal before the aside file" (TC-SLY-026) and "header removed first" (TC-SLY-038) make their checks fail (logged, TR-TRANSFER-008).

## How to work here (lessons of T-01, T-02)
- `EnterWorktree` refuses this folder. Work with absolute paths; Edit needs a Read of the file in the session first. Git only as plain `git -C /home/maldun/prog/Python/MIA-goal-v4-transfer ...` commands (compound commands with git are refused), paths named. Do not push; the owner pushes.
- Venv `/home/maldun/prog/Python/venvs/mia312/bin/python`. Regression set as one background script, strictly sequential (example: `/home/maldun/.claude-work/jobs/85fdeba4/tmp/regress02.sh`: unit suite about 8 minutes, then `run_acceptance.sh` on the branch and on a `git archive HEAD` export). Do not edit files in the worktree while it runs (`test_checkout_untouched`). In the export `test_rules_rule_set.py` is red only because it asks git.
- Deliberate defects: a scratch runner in the job tmp folder patches the module in the test process (example `mutate_t02.py`).
- `trace_check.py`: 549 old ERROR lines; compare with the export line by line.
- Numbers: next D-471, next A-187 (VIEW keeps D-430 to D-459, A-171 to A-184).
- PostgreSQL in tests: throw-away `postgres:16` under podman only.

## Start prompt for the new session
> Continue Implement of G-V4.GRAPHSTORE.TRANSFER with T-03. Work in `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-23-g-v4-transfer-t03.md`, load `dev-workflow`, `implement-phase` and `agent-app`, and start T-03.
