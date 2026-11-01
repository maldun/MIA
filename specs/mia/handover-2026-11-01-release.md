# Hand-over for the next session (written 2026-11-01, late): G-V1 released as v0.1.0, Deploy is next

This is the newest hand-over. It replaces `handover-2026-11-01.md` (merge round 4, out of date).
Read `CLAUDE.md`, then `specs/mia/goals/G-V1/goal.md`, `specs/mia/goals/G-V1/deploy-plan.md`, and the last entries of `specs/mia/review-log.md` (**D-173 to D-183**).

Next free ids: **D-184, A-89, FB-07, TD-26**.

## State
- **Released:** G-V1 is on `master` as `e10f421`, pushed (the owner pushed; the remote was checked). Tag `v0.1.0` (annotated) is on the merge commit `67818fb`; three docs commits come after it (CHANGELOG `9296679`, requirement statuses `e10f421`, goal record `6c15057`). `origin/master` and the tag equal the local ones.
- **Phases of G-V1** (`goals/G-V1/goal.md`): Explore, Plan, Implement, Verify, **Commit: done**. Deploy and Validate: **open**.
- **Verification:** report approved by the owner on 2026-11-01 (D-183): *Verified with accepted deviations*, D-1 to D-9 accepted (`specs/mia/verification-report.md`).
- **Merge gate** (local run, no CI, `--allow-local`): on `67818fb` stages 0 to 3 green; the gate approval was the owner's (`merge_gate.py --approved-by`). The stage 3 step `smoke` left the ladder with A-88 (TD-25, D-182).
- **Requirement statuses:** 357 requirements are `Verified`; 69 stay `Approved` (the 12 top-level ones the verification matrix does not mark Met, the out and partly rows of goal.md, the `Relaxed` ones, N-5) and the 15 Drafts are unchanged.
- **Amendments:** A-01 to A-88 installed (A-88 by the owner, `60d48e2`). Deferrals: TD-01 to TD-04, TD-06 to TD-25 open (TD-05 is not used).

## Open, in this order
1. **Model digests on the host** (not done): `ollama show gemma4:12b-it-qat` against `sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3` (`tools/eval.py` PINS). There is no `ollama` on the agent's path. The tag is public: a mismatch is a release note, not a moved tag.
2. **Deploy (Phase 6)**, plan in `goals/G-V1/deploy-plan.md`, record in `goals/G-V1/deployment-record.md`. Run on the owner's workstation:
   - `python tests/smoke/smoke_fresh_install.py` (SMOKE-MIA-001), `python tests/smoke/smoke_stack.py` (SMOKE-MIA-003), `python tests/smoke/smoke_gate.py` (SMOKE-GATE-001, -002). They are protected and bring up the whole stack or call the real Ollama, so they are the owner's to run on a quiet machine (see Hardware).
   - TD-25 closes when they have run and the ladder has a smoke step that finds `smoke_*.py`.
   - `deploy/build.sh` does not exist; the image is built from `deploy/Containerfile`.
3. **Validate (Phase 7):** VAL-001 and VAL-003 to VAL-006 are field checks (`goals/G-V1/validation-plan.md`). The owner also reads the Draft Scenarios sections (N-1.1, N-4.1).
4. **Cleanup left for the owner's decision:**
   - the worktree `.claude/worktrees/v1-n12` and branch `v1-n12` (an uncommitted, stale note in `implementation-log.md`: "T-01 (D-137 (4)) stopped");
   - unmerged branches `mock-server-config`, `t11b-backup`, `v1-gate2` (nested in `goal-v1`), `v1-n24-gate5` (the number-gate experiment of D-159, "stays unmerged"), `worktree-chat-c5`;
   - the worktree `.claude/worktrees/goal-v1` and branch `goal/v1` stay while the owner's stack runs from them (`.venv-gate`, `.stages/log.jsonl` are there);
   - the container `n11-views-379765fe` (a test mock server of the stopped N-1.1 agent, running since the afternoon): `podman rm -f n11-views-379765fe`.
5. **Next iteration (its own Explore and Plan):** FB-01 to FB-06, TD-21 (state in PostgreSQL), TD-22 (red-team cases), TD-23 (real sides of IF-103, IF-404, IF-405), TD-24 (sandbox backend in the stack), the nine stage 4 checks (TD-12 to TD-20), `eval-spec.md` with criteria and holdouts, `test-requirements.md`, the `number_check` rule (D-132), N-5 (D-177).

## Lessons of this session (how to run things)
- **The merge gate** is `MIA_GATE_UPTO=3 bash tools/run_merge_gate.sh` from the `goal-v1` worktree (about 7 minutes: the `unit` step alone is 343 s). It always runs the whole ladder from stage 0. The gate reads the exact commit and **counts a tree as dirty when anything is untracked**, so a dirty run is ignored. Untracked now ignored: `voice/expressions/*.wav` and editor files (`#*#`, `.#*`) in `.gitignore`, and `.claude/worktrees/` in `.git/info/exclude` (local, shared by the worktrees).
- **Stage 1 `unit` is one `unittest discover` process.** Tests that change the shared `MIA.web_app` break the later ones. Fixed with `tests/checkout_copy.py`: `load_isolated` (the chat mock server gets its own web_app) and `swap_in`/`swap_back` (a fresh MIA package for one test class); a guard is `tests/test_mock_server_isolation.py`. A new test that imports MIA must not leave routes, hooks or config patches behind.
- **Stage 2 `acceptance` runs one process per file** (`stages.yaml`): the protected `test_stability.py` puts `tests/` on `sys.path`, and `test_workflow_library.py` and `test_number_gate.py` exist in both `tests/` and `tests/acceptance/`.
- **Flaky tests are real races:** `test_author_in_records` let the chat worker thread outlive the test (56 of 300 stress runs red); the fixture now runs the worker in the test's own thread (`spawn=lambda target: target()`).
- **In the image** only `test_amendment_report` still fails (no git there; it passes on the host).
- **Hardware:** the 26B model and the full compose stack are not run on this machine (fatal CPU machine checks at shutdown under load); stage 3 started only after a copy of `data/` and the local config. A backup of the owner's data was made at `/tmp/claude-1000/-home-maldun-prog-Python-MIA/fb4d2d91-1d2f-423e-a95f-870a6081dab0/scratchpad/goal-v1-data-backup.tgz` (a session scratch folder, may be gone).
- **Master is checked out in the main checkout**, so `git checkout master` fails in a worktree: merge there (`git merge --ff-only`). The merge of master into `goal/v1` (`d4e4a13`) was needed because master had an early N-1.3 re-verification with committed conflict markers.
- **Git for agents:** `git push` is denied to the agent here; the owner pushes. Never `git add specs/mia` (the owner has untracked work files there: `Viewer_db.drawio`, `graph_structure.drawio`, `skill_rework.md`, a Kate swap file); name the files. The shell resets its directory after each command in some cases: use absolute paths. Do not stop a background wait with a `pgrep -f` or `pkill -f` pattern that also matches its own command line.
- **The owner approves, the agent drafts:** amendments are drafted with a note and an `apply_amendment_aNN.sh` script, tried on a `git archive` copy, and installed by the owner; approvals (`merge_gate.py --approved-by`, the verification report, sign-offs) are the owner's words, recorded afterwards with the date.

## Files that matter
- `/home/maldun/prog/Python/MIA/specs/mia/goals/G-V1/goal.md`, `merge-request.md`, `release-notes.md`, `deploy-plan.md`, `deployment-record.md`, `validation-plan.md`
- `/home/maldun/prog/Python/MIA/specs/mia/verification-report.md`, `deferred.md`, `review-log.md`, `/home/maldun/prog/Python/MIA/CHANGELOG.md`
- `/home/maldun/prog/Python/MIA/stages.yaml`, `/home/maldun/prog/Python/MIA/tools/run_merge_gate.sh`
