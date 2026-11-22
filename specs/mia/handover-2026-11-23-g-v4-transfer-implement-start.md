# Handover: start of G-V4.GRAPHSTORE.TRANSFER Implement (2026-11-23)

For a new session in the worktree `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md`, this file, and load `dev-workflow`, `implement-phase`, `agent-app` (no eval path in TRANSFER: pure storage logic). Decisions: questionnaire, recommended option first; full absolute paths.

## State
- Plan done: plan gate ticked by the owner; `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/plan.md` holds the six tasks and the interface the red tests fix. Requirements, checks and test requirements approved (D-466 to D-468), red tests and stubs D-469, seam with VIEW D-470 (all in `specs/mia/review-log.md`).
- A-186 installed (`fbce1924`, IF-102 v9, text only). Red tests installed (`eb0030d9`, tag `plan-baseline-g-v4-transfer`): `tests/acceptance/test_transfer_{move,sync,interrupt,sets}.py`, helpers `tests/helpers/transfer_stores.py` and the extended `core_stores.py`, smoke `tests/smoke/smoke_transfer.py`.
- Red as expected: move 7 failures, sync 9 failures + 1 skipped (TC-SLY-030, until VIEW), interrupt 8, sets 6; TC-SLY-022 green from the start; CORE's save checks green.
- Open owner item: the Agreement row "update of 2026-11-22" in `goal.md` (line 65) is not ticked yet.

## Next
1. T-01 Move integrity and order (`plan.md`), test first, one commit, `implementation-log.md` (new file in the goal folder).
2. Then T-02 to T-05 in order. T-06 needs VIEW merged into `goal/v4`: its red tests (TC-API-060 to 064, helper `tests/helpers/web_app_probe.py`, keyword-only `live=None` on `graph_api_v2.create_app`) are written then, with their own owner script (D-469, D-470).
3. Numbers: this line uses D-460 and up (next D-471) and A-185 and up (next A-187); VIEW keeps D-430 to D-459, A-171 to A-184.
4. PostgreSQL in tests: throw-away `postgres:16` under podman only; the owner's database only with his yes, never removed (CORE Deploy lessons).

## Start prompt for the new session
> Start Implement of G-V4.GRAPHSTORE.TRANSFER. Work in `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-23-g-v4-transfer-implement-start.md`, load `dev-workflow`, `implement-phase` and `agent-app`, and start T-01.
