# Handover: G-V4.GRAPHSTORE.TRANSFER Implement, T-04 (2026-11-23)

For a new session in the worktree `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md`, this file, and load `dev-workflow`, `implement-phase`, `agent-app` (no eval path in TRANSFER: pure storage logic). Decisions: questionnaire, recommended option first; full absolute paths.

## State
- T-01 `bc2b100a`, T-02 `dc373458`, T-03 `901d7763` ("feat: T-03 lag, sync, aside, lock, commands"); details, regression set and decisions in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/implementation-log.md`.
- Built in T-03, usable by T-04: `copy_lock(root)` (flock on `sync.lock`); `_graph_records(live, copy, graph_id)` (members named by any header version in either store, header last); `_state(live, copy, graph_id)` (current, behind, differs, copy_only, with per record (copy entries, live entries, shared count)); `_shared(have, wanted)`.
- Red now (expected): `test_transfer_interrupt.py` 2 (TC-SLY-029/036 at `run='one-graph move'`, files and postgres); `test_transfer_sync.py` 1 + 1 skipped (TC-SLY-031; TC-SLY-030 until VIEW); `test_transfer_sets.py` 3 (TC-SLY-032, 034, 035: T-05). Known reds of `goal/v4`: `test_decide_guard.py`, `test_judge_calibration.py`. `test_skill_run_view_browser.py` failed once in the T-03 full run and passed twice alone (logged as a flake for Verify).
- No plan amendment, no stop condition, no owner item open. Open for Phase 4 (logged): the sync refuses, rather than overwrites, a differing graph-group record no graph names; T-04 revisits this with the side records.

## T-04: Side records, one-graph move, interruptions (`plan.md`)
- Implements REQ-SLY-030, 031, 029, 036. Turn green: TC-SLY-031 (`test_transfer_sync.py`), TC-SLY-029 and TC-SLY-036 (`test_transfer_interrupt.py`, the one-graph move cases). TC-SLY-030 stays skipped until VIEW is merged and must be green before Verify.
- Touches: `graph_store_transfer.py` (`move_graph`: the lacking versions, members, `graph_changes`, `arrangements`, header last; `conflict` over the copy's own version, `detail={"graph": id}`, nothing written; the side tables by the explicit list `GRAPH_GROUP`, present only where defined; the sync's side records likewise); unit tests.
- Expected answer of TC-SLY-031: `{"graphs": 1, "records": 2}` (header version 5 and `var.in` version 2).
- Done when: listed tests green, regression set holds; the defect "one-graph move overwrites" makes TC-SLY-031 fail (logged, TR-TRANSFER-008).

## How to work here (lessons of T-01 to T-03)
- `EnterWorktree` refuses this folder. Work with absolute paths; Edit needs a Read of the file in the session first. Git only as plain `git -C /home/maldun/prog/Python/MIA-goal-v4-transfer ...` commands, paths named. Do not push; the owner pushes.
- Venv `/home/maldun/prog/Python/venvs/mia312/bin/python`. Regression set as one background script, strictly sequential (example `/home/maldun/.claude-work/jobs/85fdeba4/tmp/regress03.sh`: unit suite about 8 minutes, then `run_acceptance.sh` on the branch and on a `git archive` export of the previous commit). Do not edit files in the worktree while it runs (`test_checkout_untouched`). In the export `test_rules_rule_set.py` is red only because it asks git.
- Deliberate defects: a runner patches the module in the test process (example `/home/maldun/.claude-work/jobs/85fdeba4/tmp/mutate_t03.py`); make the mutation fail at the check's own assertion, not by an error of the mutation.
- `trace_check.py`: 549 old ERROR lines; compare with the export line by line.
- Numbers: next D-471, next A-187 (VIEW keeps D-430 to D-459, A-171 to A-184).
- PostgreSQL in tests: throw-away `postgres:16` under podman only.

## Start prompt for the new session
> Continue Implement of G-V4.GRAPHSTORE.TRANSFER with T-04. Work in `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-23-g-v4-transfer-t04.md`, load `dev-workflow`, `implement-phase` and `agent-app`, and start T-04.
