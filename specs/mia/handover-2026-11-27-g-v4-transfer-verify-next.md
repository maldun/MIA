# Handover: G-V4.GRAPHSTORE.TRANSFER Implement done, Verify next (2026-11-27)

Replaces `handover-2026-11-23-g-v4-transfer-t06.md`. For a **fresh, independent** session (Phase 4 must not share the implementation's context).

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer` (enter with `EnterWorktree` and this path; only the owner pushes, `git push -4`). Read `CLAUDE.md` and this file; load `dev-workflow`, `verify-phase`, `agent-app` (no eval path in TRANSFER: storage logic and backend wiring, no model step). Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; the owner signs, the agent never sets Approved; review by thematic group.

## What is to be verified
The plan package in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/` (goal, high-level spec, requirements with groups MV, SB, SY, SR, PT, AS, test spec, test requirements, plan T-01 to T-06), amendment A-195 (installed `d3024c15`, approved by the owner `ac8be86a`), and two findings handed over from G-V4.VIEW:
- **F-1** of VIEW's Deploy (`76df87c4`): `migrate files-to-db` with `--data` naming MIA's data folder read the preset store's files as a table and stopped with a traceback; now one line `refused: presets/<id> (not_a_history: ...)`, exit 1.
- **V-3** of VIEW's verification (`3c2f39a1`): a dropped PostgreSQL connection is opened again on the next call; MIA starts while the database is down and answers `store_unreachable` (REQ-API-021, 050).

Task commits: T-01 `bc2b100a`, T-02 `dc373458`, T-03 `901d7763`, T-04 `355c8826`, T-05 `73a32730`, T-06 `92f7aa46` (+ follow-up `4dd8f7b4`, the stack's config). Red tests: `eb0030d9` (T-01 to T-05), `943b8dac` (TC-API-060 to 064). Details, regression sets, deliberate defects, findings, decisions: `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/implementation-log.md`.

## Open questions for Verify (from the log)
- The sync refuses (`conflict`), rather than overwrites with an aside file, a differing graph-group record that no graph names (T-03).
- `library-seed` does not run the per-graph check of REQ-SLY-017 (T-01; REQ-SLY-009 does not ask it).
- The extra `sync` output line per set-aside graph (REQ-SLY-039 "reports the records added": additive, not amended).
- V-3 was checked with `pg_terminate_backend` on a throw-away server (a real server-side drop), not with a stopped real container as VIEW's report suggested.
- With a copy set, a save is seen on the copy only after the next sync (REQ-API-066); the editor's view of that is EDIT's (FR-95).
- `deploy/REQUIREMENTS_DB.md` item 7 names an `up.sh migrate` that does not exist (outside TRANSFER's files; reported, not changed).
- Two flaky checks seen once each in earlier runs (`test_skill_run_view_browser.py`, `test_sandbox.py` with leftovers in the shared `/tmp`), each OK alone.

## State of the checks (the implementer's runs: feedback, not verification)
- Final regression 2026-11-27 with `bash tools/regress.sh --out <dir> --base 943b8dac`: unit suite 2642 tests, one failure (`test_deploy`, fixed in `4dd8f7b4`, then `test_deploy`, `test_config` green); acceptance scripts red only the known `test_decide_guard.py`, `test_judge_calibration.py`.
- PostgreSQL: `tests/test_storage_postgres.py` 45/45 and the IF-102 contract suite (`tools/contract_postgres.sh`) green on throw-away postgres:16.
- SMOKE-TRANSFER-001 green on the owner's server (`mia_db_1`, started and stopped again; `mia_smoke` dropped), run in a throw-away container on `mia_default` (the host cannot resolve `db`).
- Traceability: 585 ERROR lines, the same as before T-06 (549 before the VIEW merge; the rise came with it).
- Image: `localhost/mia:g-v4-transfer` (`2f6de35d4f4c`, psycopg 3.3.9) built from a clean `git archive` export of the branch; `deploy/build.sh` was not used because it also tags `localhost/mia:latest`, which RUN's image tests need.

## Tools now shared (on `goal/v4`, merged here)
- `bash tools/regress.sh --out DIR [--base COMMIT]`: the regression set, one run per worktree.
- `python tools/plant_defects.py DEFECTS.json`: deliberate defects, restored byte for byte, bytecode removed around each run (the T-06 trap: a same-size restore within one second ran stale bytecode).

## Host state
- The live stack `mia` is stopped (all `mia_*` containers exited); `mia-searxng` runs. The owner's database server `mia_db_1` is stopped.
- `localhost/mia:latest` is RUN's branch build; never overwrite it. `localhost/mia:g-v4-view` is VIEW's deployed image.

## Next free numbers (TRANSFER)
Decisions D-547 (block D-540 to D-559); amendments A-196 (block A-195 to A-199); checks TC-API-068, TC-SLY-040; test requirements TR-TRANSFER-012. Other lines: RUN D-485, A-190; VIEW D-505, A-178; BUILDER D-522.

## Start prompt for the new session
> Verify G-V4.GRAPHSTORE.TRANSFER. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-27-g-v4-transfer-verify-next.md`, then run Phase 4 as a fresh reviewer.
