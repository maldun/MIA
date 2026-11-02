# Hand-over for the next session (written 2026-11-02): G-V1 is deployed, Validate is next

Newest hand-over; it replaces `handover-2026-11-01-release.md`. Read `CLAUDE.md`, then `specs/mia/goals/G-V1/goal.md`, `deployment-record.md`, `validation-plan.md` and the last entries of `specs/mia/review-log.md` (D-183, **D-184**).

Next free ids: **D-185, A-89, FB-07, TD-27**.

## State
- **G-V1:** Explore, Plan, Implement, Verify, Commit, **Deploy: done** (2026-11-02, owner's workstation, record complete). Validate: open.
- **Deployed:** tag `v0.1.0`, image `localhost/mia:latest` = `localhost/mia:v0.1.0`, id `8217ecd0ccf8...`, stack in `~/tmp/mia-v0.1.0` (login off, bound to 127.0.0.1, host Ollama through `OLLAMA_URL`). Previous image `localhost/mia:pre-v0.1.0` (`e37a87782beb`) kept for rollback; backup `~/tmp/mia-v0.1.0/mia-backup-20261102-2303.tar.gz`. Pins verified: both model digests equal the pins (before and after the rollback).
- **Checks on the target, green:** preflight; SMOKE-MIA-001, SMOKE-MIA-003, SMOKE-GATE-001/-002; recovery check (`tools/recovery_check.sh`); rollback to `pre-v0.1.0` and forward again.
- **Not done:** SMOKE-MIA-002 (Tailscale phone check) deferred by the owner: **TD-26, D-184**. It is a precondition of VAL-004; the validation plan says so.
- **Frozen during validation:** no pulls, no skill or prompt edits on the target; a fix is a patch version.

## Commits after the tag (master, not pushed; the owner pushes)
`ae9cba2` Kokoro preflight, `tools/fetch_kokoro.sh`, `deploy/up.sh voice` · `1652ddd` `tools/recovery_check.sh` · `c0f1f27` rollback recipe in the RUNBOOK · `5366eff`, `49f486c`, `b053df8`, `8ac7e17` deployment record, Deploy done, TD-25 progress · and the commit of this hand-over and TD-26/D-184. The deployed tree is `v0.1.0` **without** these; they are tools and docs. If a patch version is cut, they go in.

## Open, in this order
1. **Before Validate starts (owner):**
   - SMOKE-MIA-002 / TD-26 (needed for VAL-004): `ui/tools/remote.sh up` after the Tailscale install; steps are in this session's answer and `README.md` ("From outside the home network").
   - Switch the login on before other people use it (`deploy/up.sh login on`, `deploy/up.sh owner NAME`, RUNBOOK "The login"); with it off every tailnet member can change trust classes (D-131). `tools/recovery_check.sh` needs the login off.
   - Informed consent of the users (validation plan, "Validators and data").
2. **Validate (Phase 7):** VAL-001 and VAL-003 to VAL-006 (`goals/G-V1/validation-plan.md`); the owner also reads the Draft Scenarios sections (N-1.1, N-4.1). Skills: `validate-phase`, `agent-app-validate`. Run logs stay local.
3. **Smaller items from Deploy:**
   - TD-25 stays open: a smoke step in `stages.yaml` that finds `smoke_*.py` (a gate change, next iteration).
   - Only the number gate has `smoke` cases; the other suites need 2 tagged cases each for a smoke eval (`tools/tag_smoke_cases.py`).
   - No voice lines in the image (`python tools/make_voice_lines.py`, then a rebuild); MIA is silent on mood lines.
   - `mia_ollama_1` (the stack's own Ollama) runs idle with no models; `podman rm -f mia_ollama_1` frees it.
   - No `deploy/build.sh`; the image is built on the target.
4. **Cleanup for the owner's decision** (unchanged from the last hand-over): worktree `.claude/worktrees/v1-n12` and branch `v1-n12`; unmerged branches `mock-server-config`, `t11b-backup`, `v1-gate2`, `v1-n24-gate5`, `worktree-chat-c5`; worktree `goal-v1` and branch `goal/v1`; the test container `n11-views-379765fe` if it still runs.
5. **Next iteration (its own Explore and Plan):** FB-01 to FB-06, TD-21, TD-22, TD-23, TD-24, TD-12 to TD-20, `eval-spec.md` criteria and holdouts, N-5.

## Lessons of this session
- **podman-compose does not recreate a running container** when only `MIA_IMAGE` changes. Rollback = retag the old image as `latest`, `podman rm -f mia_mia_1 mia_graph_1`, `deploy/up.sh db up -d --no-build` (RUNBOOK, "Rollback to the previous image"). The containers hold no data.
- **A fresh clone lacks git-ignored files** (Kokoro, character page, voice lines): `bash tools/fetch_kokoro.sh`, `deploy/up.sh voice`, `MIA_KOKORO_DIR` / `MIA_CHARACTER_DIR` in `deploy/.env`; the preflight now checks the Kokoro files.
- **Host vs container Ollama address:** `host.containers.internal` resolves only inside containers; run the preflight on the host with `OLLAMA_URL=http://127.0.0.1:11434`.
- **Hardware:** no crash during this Deploy (stack up, smoke tests, hard kill, rollback). The open machine-check risk at shutdown stays (memory note `crash-fatal-mce-cpu`); back up before stopping the stack.
- Commits name their files (never `git add -A`); `git push` is the owner's; the owner approves, the agent drafts and records.

## Files that matter
`specs/mia/goals/G-V1/goal.md`, `deployment-record.md`, `validation-plan.md`, `release-notes.md`; `specs/mia/deferred.md` (TD-25, TD-26), `review-log.md`; `deploy/RUNBOOK.md`; `tools/recovery_check.sh`, `tools/fetch_kokoro.sh`; `CHANGELOG.md`.
