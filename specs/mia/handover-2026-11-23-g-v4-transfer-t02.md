# Handover: G-V4.GRAPHSTORE.TRANSFER Implement, T-02 (2026-11-23)

For a new session in the worktree `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md`, this file, and load `dev-workflow`, `implement-phase`, `agent-app` (no eval path in TRANSFER: pure storage logic). Decisions: questionnaire, recommended option first; full absolute paths.

## State
- T-01 done (`bc2b100a`, "feat: T-01 move integrity and order"); details, regression set and open questions in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/implementation-log.md`. Goal Phases: Implement in progress.
- Red now (expected): `test_transfer_move.py` 1 (TC-SLY-021, sync half, T-03); `test_transfer_sync.py` 9 + 1 skipped (TC-SLY-030 until VIEW); `test_transfer_interrupt.py` 6 (the whole-store move cases of TC-SLY-029/036 are green since T-01; one-graph and sync cases wait for T-03/T-04); `test_transfer_sets.py` 6. Known reds of `goal/v4`: `test_decide_guard.py`, `test_judge_calibration.py` (G-V3.REPORT F-3).
- No plan amendment, no stop condition, no owner item open.

## T-02: Durable files, cut back, the same answers (`plan.md`)
- Implements REQ-SLY-022, REQ-SLY-023; `cut(table, id, version)` on both backends and `FileBackend.put_file(path, text)` (used later by REQ-SLY-026, 032, 038).
- Turn green: TC-SLY-023; keep TC-SLY-022 green (`tests/acceptance/test_transfer_sync.py`, class SameBehaviour).
- Touches: `storage_files.py` (write: fsync of the file, rename, fsync of the folder; `cut`; `put_file`), `storage_postgres.py` (`cut`: delete the versions above n in one statement); unit tests of both backends (`tests/test_storage_files*.py`, `tests/test_storage_postgres.py`).
- Must not touch: protected material; `storage.py` (no IF-102 operation); `graph_store_transfer.py` beyond calling the new operations.
- Interface fixed by the red tests: `cut` keeps versions 1 to n; `put_file` is durable (fsync, rename, fsync of the folder); `FileBackend.append` writes the format marker first into a set without one and flushes as REQ-SLY-023 says (marker `mia-store.json`, `{"format": 1}`; constants in `graph_store_transfer`: `FORMAT`, `MARKER`). TC-SLY-023 patches `os.fsync` and `os.replace`, appends one version to a `memos` record and asserts only the last three calls: `("fsync", "file"), ("replace",), ("fsync", "folder")`; a marker written first may add its own three calls before them. Whether the marker is written in T-02 or T-05 is open in the plan wording; read REQ-SLY-023 and REQ-SLY-032 and decide by them (log the choice). The marker's reading side (older and newer sets) is T-05.
- Demonstrator: a backend cut back to version 2 lists versions 1 and 2, on files and on the database.
- Done when: the listed tests green, the regression set holds; the defect "no flush" makes TC-SLY-023 fail (TR-TRANSFER-008, logged with the runner and result as for T-01).

## Lessons from T-01 (how to work here)
- `EnterWorktree` refuses this folder (it only takes worktrees under `.claude/worktrees/`). Work with absolute paths; Edit and Write reach the folder; long multi-step shell scripts with heredocs that write files may be refused by the isolation guard, so edit with Edit and keep shell calls plain. Commit with `git -C /home/maldun/prog/Python/MIA-goal-v4-transfer ...`, paths named. Do not push (agent-app rules); the owner pushes.
- Venv: `/home/maldun/prog/Python/venvs/mia312/bin/python`. The unit suite (`-m unittest discover -s tests`) takes about 8.5 minutes; run it in the background and **do not edit files in the worktree while it runs**: `test_checkout_untouched` reports every file changed during the run.
- Regression comparison: export HEAD with `git archive HEAD | tar -x -C <job tmp>/base` and run every `tests/acceptance/test_*.py` one by one in both trees (runner as in T-01: one line per file with the OK/FAILED summary). In the export `test_rules_rule_set.py` is red only because it asks git; ignore that difference. Run the trees one after the other (postgres containers).
- Deliberate defects: patch the module in the test process (a scratch runner in the job tmp folder imports the module, replaces the function, then runs the named test methods); the code on disk stays unchanged.
- `trace_check.py` has 549 old errors; compare the ERROR lines with the HEAD export, not the count alone.
- Numbers: this line uses D-460 and up (next D-471) and A-185 and up (next A-187); VIEW keeps D-430 to D-459, A-171 to A-184.
- PostgreSQL in tests: throw-away `postgres:16` under podman only; the owner's database only with his yes, never removed.

## After T-02
T-03 (lag, sync, aside, lock, commands; also turns TC-SLY-021 whole), then T-04, T-05. T-06 needs VIEW merged into `goal/v4` and its own red tests and owner script first (D-469, D-470).

## Start prompt for the new session
> Continue Implement of G-V4.GRAPHSTORE.TRANSFER with T-02. Work in `/home/maldun/prog/Python/MIA-goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-23-g-v4-transfer-t02.md`, load `dev-workflow`, `implement-phase` and `agent-app`, and start T-02.
