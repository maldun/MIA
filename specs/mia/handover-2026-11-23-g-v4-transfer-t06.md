# Handover: G-V4.GRAPHSTORE.TRANSFER Implement, T-06 (2026-11-23)

For a new session in the worktree `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md`, this file, and load `dev-workflow`, `implement-phase`, `agent-app` (no eval path in TRANSFER: pure storage logic and backend wiring). Decisions: questionnaire, recommended option first; full absolute paths.

## State
- T-01 `bc2b100a`, T-02 `dc373458`, T-03 `901d7763`, T-04 `355c8826`, T-05 `73a32730` ("feat: T-05 portable sets"); details, regression sets, deliberate-defect runs and decisions in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/implementation-log.md`.
- Every TRANSFER acceptance file is green on the branch: `test_transfer_move.py`, `test_transfer_sync.py` (1 skipped: TC-SLY-030), `test_transfer_interrupt.py`, `test_transfer_sets.py`. Known reds of `goal/v4`: `test_decide_guard.py`, `test_judge_calibration.py`. `test_skill_run_view_browser.py` failed once in the T-03 run and `test_sandbox.py` (leftover `mia-sandbox-*` folders in the shared `/tmp`) once in the T-05 run, each OK alone (logged as flakes for Verify; the second likely from the VIEW session's checks running at the same time).
- No plan amendment, no stop condition. Open for Phase 4 (logged): the sync refuses, rather than overwrites, a differing graph-group record that no graph names; the extra `sync` output line proposed for REQ-SLY-039's command texts.

## T-06 is blocked: VIEW first (D-469, D-470)
T-06 depends on T-04, T-05 (done) **and VIEW merged into `goal/v4`**. On 2026-11-23 VIEW (`goal/v4.view`, worktree `/home/maldun/prog/Python/MIA-goal-v4-view`) is in Implement at T-08 of 12; its Verify and Commit are open, and `goal/v4` does not contain it. TRANSFER holds `goal/v4` fully (nothing to bring in today). Order once VIEW is merged:

1. Bring `goal/v4` into this branch (`git -C /home/maldun/prog/Python/MIA-goal-v4-transfer merge goal/v4`, only with `git status` clean). Then:
   - TC-SLY-030 (`test_transfer_sync.py`, class SideRecords) is no longer skipped and must be green: the side records are carried through `_side_records` (T-04, only where `graph_changes` and `arrangements` are defined); if it fails, it is a finding of T-04, test first.
   - re-run the TRANSFER acceptance files and the regression set: VIEW's files stores now carry the format marker of T-05 (every write into a set without one adds `mia-store.json`); VIEW's checks that compare folders file by file are the place to look.
2. **Red tests of TC-API-060 to 064, before any code (D-469).** Written on the merged VIEW, staged in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/red-tests/` with an owner script `tools/apply_transfer_api_red_tests.sh` (pattern: `tools/apply_transfer_red_tests.sh`), installed and committed by the owner ("test: TRANSFER API acceptance tests (red)"); protected afterwards. Contents:
   - `tests/acceptance/test_transfer_backend.py`: TC-API-060 to 064 (scenarios in `test-spec.md`, lines 246 to 277; TR-TRANSFER-009, -010; the store cases from `tests/helpers/transfer_stores.py`, `ac006`). Each skipped with its reason while VIEW's `store` setting or `GET /api/v2/store` is missing (TR-TRANSFER-010).
   - `tests/helpers/web_app_probe.py`: TRANSFER's own copy of VIEW's `WebAppProbe` and `checkout_with` (D-470); TRANSFER's tests never import `tests/acceptance/test_view_backend.py` (protected, TR-VIEW-015).
   - TC-API-063's live store: a database address on a port where nothing listens (TR-TRANSFER-009), never the owner's server.
   - Every check fails by assertion against today's code, none by an import error (as at the first red commit).
   - Before writing them: the start steps and the orderly-stop list of `__main__.py` must be callable from a test (TR-TRANSFER-009). Splitting them out is part of T-06 (below); if a red test cannot be written without that split, name it in the owner script's note and do the split first as a `refactor(api)` commit with characterization checks (M31), not mixed into the task commit.
3. Implement T-06 (`plan.md`, "T-06: Copy setting, AutoSync, store answer, smoke").

## T-06: Copy setting, AutoSync, store answer, smoke
- Implements REQ-API-060 to 064; HR-004 and HR-006 as a whole.
- Turn green: TC-API-060 to 064; `python tests/smoke/smoke_transfer.py` passes on the branch (SMOKE-TRANSFER-001).
- Touches: `graph_api_v2.py` (keyword-only `live=None` on `create_app(backend, accounts_store, store, allowed_origins, *, live=None)`, D-470; with `live=None` nothing changes, REQ-API-022; the real fields of `GET /api/v2/store`: `shown` `copy`, `live_reachable` as the live store answers now, `lag` `{"graphs": n not current, "since": time of the oldest live version the copy lacks or null}`), `web_app.py` and `__main__.py` (configuration keys `copy`, a folder, absent = no copy, and `autosync`, true/false, default false, D-467; the start steps and the stop list split into two functions `__main__` calls; AutoSync before the first answer and in the stop list before the database is closed, REQ-API-062); unit tests.
- Reuse: `graph_store_transfer.lag` and `sync_store` (the lock keeps one sync at a time, REQ-SLY-028); the prototype's `AutoSync` (`prototype/g-v4:graph_store_sync.py`): an unreachable live store is a report, never a failed start: one log line naming the live store and "sync not run", MIA goes on with the copy (REQ-API-063); a refused sync (`move_refused`, `older_format`, `conflict`, `locked`) is a log line as well, not a crash.
- The copy is a `FileBackend`; a copy of a newer format refuses to open (T-05, `StorageError("format")`): decide with the owner whether that stops the start or falls back to the live store (no requirement says it; questionnaire).
- Must not touch: protected material; the owner's live data; VIEW's requirements; IF-104 (no new route: lag and sync stay commands, D-467).
- Smoke (SMOKE-TRANSFER-001): on the owner's host, throw-away database `mia_smoke` on his running PostgreSQL server, **started only with his yes** (D-460 (1)); SMOKE-RULES-001 runs with it (D-462); `mia_smoke` and both folders dropped by name; MIA's own data never written. MIA itself keeps running on files: the live store switch is a later owner gate.
- Demonstrator: MIA on a copy with AutoSync on shows `shown: copy` and the lag in `GET /api/v2/store`.
- Done when: every TRANSFER check green (TC-SLY-030 included), the regression set holds with no known red of TRANSFER left; then Implement is recorded done in `goal.md` (Phases) and the hand-over to Verify (fresh context) follows.

## How to work here (lessons of T-01 to T-05)
- `EnterWorktree` refuses this folder. Work with absolute paths; Edit needs a Read of the file in the session first. Git only as plain `git -C /home/maldun/prog/Python/MIA-goal-v4-transfer ...` commands, paths named. Do not push; the owner pushes.
- Venv `/home/maldun/prog/Python/venvs/mia312/bin/python`. Regression set as one background script, strictly sequential (example `/home/maldun/.claude-work/jobs/85fdeba4/tmp/regress05.sh`: unit suite about 9 minutes, then `run_acceptance.sh` on the branch and on a `git archive` export of the previous commit). Do not edit files in the worktree while it runs (`test_checkout_untouched`). In the export `test_rules_rule_set.py` is red only because it asks git.
- Deliberate defects: a runner patches the module in the test process (examples `mutate_t03.py`, `mutate_t04.py` in the same folder); make the mutation fail at the check's own assertion, not by an error of the mutation. For T-06 the plan names no defect; an obvious one is "AutoSync only at start" against TC-API-062.
- Unit tests first and seen red (T-03's were written after the code; logged as a deviation).
- `trace_check.py`: 549 old ERROR lines; compare with the export line by line.
- Numbers: next D-473 (D-471, D-472 are EDIT's and REPLAY's plan points on `goal/v4`), next A-187 (VIEW keeps D-430 to D-459, A-171 to A-184).
- PostgreSQL in tests: throw-away `postgres:16` under podman only. Before a long run, look at `ListAgents`: VIEW's session may run browser or database checks at the same time.

## Start prompt for the new session
> Continue Implement of G-V4.GRAPHSTORE.TRANSFER with T-06. Work in `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-23-g-v4-transfer-t06.md`, load `dev-workflow`, `implement-phase` and `agent-app`. First check whether VIEW is merged into `goal/v4`; if not, stop and report. Otherwise follow the order in the handover, starting with the merge of `goal/v4` and the red tests of TC-API-060 to 064.
