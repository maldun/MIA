# Hand-over for the Commit session (Phase 5) of TD-11, option B (written 2026-11-08): blocked by the owner's decision on the red stages

Read `CLAUDE.md` first. Skills: `dev-workflow`, `commit-phase` (`agent-app-commit` does not apply: no prompt, pipeline, eval suite or model pin changed). You are in Phase 5 for the change set of TD-11 option B (A-132, A-133, A-134, A-135, A-136). **Phase 5 is stopped by the owner** (section 2); do not tag, do not merge, do not supply an approval to `merge_gate.py`. This file says where things stand and what is left, so that the session that resumes does not repeat the work.

## 1. State at the end of this session
- Verify is done and approved. Report: `specs/mia/amendments/A-132-verification-report.md` (verdict Verified; approved by the owner 2026-11-08). Its fixes F1, F2, F3 and the amendments A-134 (parents), A-135 (wording of REQ-CHA-033 AC-1) and A-136 (REQ-VPB-006 3 s as an accepted risk) are all on master. Decisions D-283 to D-288 are in `specs/mia/review-log.md`; **D-289 is the next free id**.
- Master was at `1732666` when this was written (it includes the merge of `goal/v3`, resolved by keeping both sides; `goal/v3` is at the same commit). The TD-11 hand check TC-CHA-035 passed on the merged code (owner-reported, Firefox; audio device, exact commit and per-step table not given).
- TD-11 has no goal record (`goal.md`) and no goal branch: it is a change set on master (deferral TD-11, status dropped, replaced by TD-61, which stays open: trigger 2026-12-31 or the next voice iteration). So there is no merge request and no Phases table to update; Commit here means: the status update, the changelog and release notes, a tag decision.
- Branches and worktrees: `verify-a132`, `worktree-agent-a613bc8d70a369862`, `v3-merge-master` and the temporary check-outs are removed (merged or patch-equivalent on master, checked). **Kept:** worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/td11-release`, branch `td11-release` (from master `1732666`), with one prepared commit (section 4) and this file. Nothing is pushed, nothing of this branch is on master.

## 2. What the owner decided on 2026-11-08 and what stops Phase 5
| Question | Answer |
|---|---|
| Version tag | **No tag now.** Record TD-11 as Verified under `[Unreleased]`; the tag comes with iteration 2 (v0.2.0) after its own Verify. Reason: master also holds production changes since `v0.1.0` that this verification did not cover (section 5) |
| The red stages of the merge gate | **"Do not proceed"**: stop Phase 5 until the ladder is green. The option text said this blocks until the other goals' work is done (59 backlog errors of the plan, the G-V2.MODEL red tests). The owner did not choose to accept the three as deviations and did not choose to fix the tailscale test |

Resume only when the owner changes this decision, or when the ladder is green. Ask them (as a questionnaire, one question: accept as deviations, fix the tailscale test first, or wait) before doing anything beyond reading.

## 3. Evidence of the ladder on pristine master `1732666` (local run 2026-11-08 03:13 to 03:25, not CI)
`run_stages.py --stages stages.yaml --upto 3 --keep-going` with the venv first in `PATH`, in a clean detached check-out; the steps it skipped (`needs` a failed step) were run by hand.

| Step | Result | Note |
|---|---|---|
| model-ids, contract-js, js, quality, sysml-parse | pass | sysml-parse 63 s |
| decomposition | **fail**, 59 errors | the plan backlog (FR and REQ-WFM, REQ-GTB, REQ-RUN, REQ-FE); none names a TD-11 id (A-134 closed the eight of TD-11) |
| unit | **fail**, 2071 tests, 1 error | `test_tailscale.ScriptTest.test_without_tailscale_it_says_how_to_install`: `/usr/bin/tailscale` is installed on this host, so the test runs the real `tailscale up` and times out after 30 s; neither `ui/tools/remote.sh` nor the test changed in TD-11 |
| contract-mocks (by hand) | pass, 110 tests | |
| acceptance (by hand, one process per file) | **2 of 16 files fail** | `tests/acceptance/test_graph_model.py`, `test_graph_run.py`: the red tests of G-V2.MODEL (commit `e169361`), not implemented yet |
| contract-real, integration | pass | |
| container-alone (by hand) | pass, 2 tests | |
| contract-postgres | pass | |

TD-11's own checks are all green (details: verification report, sections 1, 7b). `merge_gate.py` has not been run; it needs a CI run on a clean tree (`ci: true`) or `--allow-local` (the precedent of `v0.1.0`: "the merge gate ran locally, no CI"), and a person's `--approved-by`.

## 4. Prepared, not committed to master
Branch `td11-release`, commit `b48d95b`: status `Approved` to `Verified` (and one History note "verified 2026-11-08 (A-132-verification-report.md, approved by the owner)") for REQ-CHA-030 to 036 in `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md` and REQ-VPB-006 in `specs/mia/nodes/N-1-web-frontend/nodes/N-1.3-voice-playback/requirements.md`; 8 requirements, 16 lines. After it, `trace_check.py` 545 errors (none TD-11), `req_graph.py` 28 errors and 46 warnings, the same as before. The commit message says "not for merge until Phase 5 is unblocked": the owner merges it, or asks for a new one, when Phase 5 resumes.

## 5. What is left when Phase 5 resumes (in this order)
1. Ask the owner the question of section 2. If the ladder is accepted with deviations: record the three reds (section 3) as accepted deviations in the release record, each with its owner or goal; if the tailscale test is to be fixed first: a Phase 3 task, test first (the lookup of `tailscale` has to ignore the host's `PATH`), then re-run `bash` ladder; if wait: stop.
2. Re-check master against the current commit (it may have moved): `git log --oneline -3 master`, re-run the ladder if code changed since `1732666`.
3. Merge the prepared status commit `b48d95b` (the owner merges). Add the review-log record `D-289`.
4. `CHANGELOG.md`: a new section `## [Unreleased]` above `[0.1.0]` with the entry of the appendix below; no tag. Release notes: the appendix is the draft (`commit-phase/assets/release-notes.md` format); write it to `specs/mia/amendments/A-132-release-notes.md` if the owner wants it as a file (the G-V1 notes are in `specs/mia/goals/G-V1/release-notes.md`).
5. Do not tag. The tag decision is deferred to iteration 2 (v0.2.0). A tag later is a human action on a Verify of the extras below.
6. Deploy (Phase 6) is probably empty for TD-11 with the reason "chat voice only, no new artifact; the owner runs master on the host"; Validate is the owner's use of the voice. The owner decides.

**Production changes on master since `v0.1.0` that the TD-11 verification did not cover** (a tag on master would release them; they need their own Verify): `deploy/preflight.sh` and `deploy/up.sh voice` (Kokoro files, commit `ae9cba2`, REQ-OPR-001), `tools/recovery_check.sh` (`1652ddd`), `tools/fetch_kokoro.sh`, `tools/fetch_benchmarks.py`, and the STUB modules `graph_model.py`, `graph_run.py`, `skill_record.py` of G-V2.MODEL (`e169361`, "STUB, written in Plan step 4 so the red tests import").

## 6. Known limitations for the release notes (from the report)
- F4: `/api/speak_again` has no rate limit and no cap on waiting repeats (accepted by the owner, trusted users; revisit with TD-61).
- TD-61 open: two voice paths (sound server and `SpeechService`); the sound server's handler ends only after the client closed its connection (`SpeechStreamer.wait` always closes, so today's route is not hit); one connection per sentence loses rendering ahead (D-280; the owner heard no choppy gaps in the hand check).
- A failed repeat logs two error lines in the app (the streamer's and the Chat agent's); REQ-CHA-033 AC-1 says "one error line of the Chat agent" (A-135).
- `stop()` returns true only when an answer was stopped; a spoken-again playback is ended anyway.
- Two guards for an answer that runs during a repeat (`not self._running`) are not pinned by a test; the status itself is (TC-CHA-037).
- Hand check TC-CHA-035: owner-reported; audio device, exact commit and per-step table not recorded (TR-VOICE-002 met with incomplete detail).
- REQ-VPB-006's 3 s is the constant `STOP_DROP_MS`, an accepted risk (A-136, follow-up VAL-006).
- The ladder on this host is red for other work (section 3).

## 7. Commands for the resuming session
```bash
cd /home/maldun/prog/Python/MIA/.claude/worktrees/td11-release     # or a fresh worktree of master
git log --oneline -3 master
# ladder on a clean check-out (about 12 minutes; the unit suite is 8 of them)
PATH=/home/maldun/prog/Python/venvs/mia312/bin:$PATH /usr/bin/python ~/.claude/skills/dev-workflow/scripts/run_stages.py --stages stages.yaml --upto 3 --keep-going --log <a log outside the repo>
# steps that `needs` a failed step skips: contract-mocks, acceptance, container-alone, run them by hand with the commands of stages.yaml
python3 -I tools/check_sysml_model.py . ; bash tools/check_sysml.sh specs/mia/architecture.sysml
python ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests     # 545 errors, none of TD-11
```
The merge gate and the tag are human steps: `python ~/.claude/skills/dev-workflow/scripts/merge_gate.py --approved-by "<owner name>" --allow-local` only by the owner.

## 8. Processes stopped at the end of this session, and what continues in the next one
Checked on 2026-11-08 at the end of the session (`pgrep`, `ps`, `podman ps -a`): **no run, test or container of this session is active.**
- Stopped by me: the monitor of the stage ladder (a shell loop `until ! pgrep -f "stages_gate.sh"`; its pattern matched its own command line, so it could never see the ladder end; it had run 19 minutes). The ladder run itself had already finished (exit 0, 03:25), and the two other background runs (the first ladder in `td11-release`, killed on purpose because I edited spec files while it ran; the child unit run of that kill was not left over) are gone.
- Not mine, left running: one `python -m unittest discover -s tests` in `/tmp/v7/clean4` (parent session `2617`, started during this session); it belongs to another session. The podman list holds only old containers (16 months, `localhost/dpp`, `open-webui`), no `mia`, `n13-*` or pod of this work.
- For the next session: **a monitor must not use `pgrep -f "<script name>"` for a script whose name is also in its own command line** (it matches itself and never ends); wait on a process id (`while kill -0 <pid>`) or on a marker file the script writes at its end.

**What continues in the next session** (nothing runs by itself; everything below is to be started by the resuming session after the owner's answer in section 2):
1. The question to the owner of section 2 (accept the three reds as deviations, fix the tailscale test first, or wait).
2. Then, in order, section 5: the re-check of master, the ladder if master moved (about 12 minutes, started with a process id to wait on), the merge of the prepared status commit `b48d95b`, `D-289`, the `[Unreleased]` entry of the appendix, the release notes if wanted, and no tag.
3. The branch `td11-release` (commit `b48d95b` and this file) is the only thing kept on disk; merge it or branch from it, then remove it: `git worktree remove .claude/worktrees/td11-release && git branch -d td11-release` (from the main checkout).

## Appendix: draft `[Unreleased]` entry for `CHANGELOG.md`
```
## [Unreleased] – 2026-11-08, TD-11 option B: speak again through the voice route (verified, not released)

### Fixed
- The speaker button under a message ("Speak again") is heard: the chat agent hands the stored text sentence by sentence, in order and through the speech filter, to the voice route of live answers, one repeat at a time (REQ-CHA-030, REQ-CHA-031, REQ-CHA-034). Before, it only sent audio_chunk events that no page played (D-276).
- Stop ends a spoken-again playback, also when no answer is generated (REQ-CHA-032); the Stop button is shown while a message is spoken again, also over a running answer, and the status returns afterwards (REQ-CHA-035, REQ-CHA-036); a spoken-again line is heard within 3 s after a Stop (REQ-VPB-006).
- A voice route that is not reachable does not break the chat: one connection attempt, the rest of that repeat is dropped (REQ-CHA-033).

### Changed
- `stop()` returns true only when an answer was stopped (IF-101 and IF-201 unchanged).
- Specification: parents of REQ-CHA-030..036 and REQ-VPB-006 one level up (A-134); REQ-CHA-033 AC-1 reworded (A-135); the 3 s of REQ-VPB-006 recorded as an accepted risk (A-136).

### Known limitations
- see section 6 of this hand-over (F4, TD-61, two log lines, hand-check detail, the red stages on this host, and the changes on master that this verification did not cover).

### Release record
- Verified (verification report approved 2026-11-08, `specs/mia/amendments/A-132-verification-report.md`), on master since the merges of 2026-11-08; no tag (the owner, 2026-11-08: the tag comes with iteration 2).
```
