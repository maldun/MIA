# Hand-over for the next G-V3 session (written 2026-11-12): PANEL implemented and not verified, CHAT T-01 to T-03 done

For the session that continues **G-V3**. Two lines of work now run in two worktrees of one repository. Start with `CLAUDE.md`, then this file, then the file of the line you work on. Nothing is pushed (the push and the merge are the owner's; `git push` is denied). The owner decides every approval and review item by questionnaire (`AskUserQuestion`, recommended option first); an agent never marks anything approved without an answer. Commit with `git add <paths>` and `git commit -m ... -- <paths>`; message ends with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; commits of a task carry `Task:` and `Requirements:` lines, CHAT commits also `Eval:` and `Model:`. Python for every test: `/home/maldun/prog/Python/venvs/mia312/bin/python`. Earlier hand-over (history of the Plan phase and the guards): `handover-2026-11-08-g-v3-implement-t01-done.md` and `handover-2026-11-08-g-v3-plan-review.md`.

## The two lines
| Line | Worktree | Branch | HEAD | State |
|---|---|---|---|---|
| **G-V3.PANEL** | `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3` | `goal/v3` | `ad454f6` (the verification report) | Implement T-01 to T-10 done; first Verify run: **Not verified**, fix round open |
| **G-V3.CHAT** | `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3-chat` | `goal/v3.chat` (made from `7556624` on 2026-11-11, so CHAT could go on while PANEL was verified) | `045369d` | Implement T-01 to T-03 done; T-04 to T-06 open; one protected-helper patch waits for the owner |

Both branches have the same parent `7556624`; master has moved on (STORE, MODEL, TD-11, CONVERT/TOOLBOX in other sessions) and **neither branch has merged master yet**. Collisions to expect at the merge are listed in `handover-2026-11-08-g-v3-plan-review.md` ("Collisions to expect") and in the "Open questions for Phase 4" of both implementation logs (`CHANGELOG.md` `[Unreleased]`, `architecture.sysml` generated block, `plausibility.yaml`). The two branches change different hunks of `tests/helpers/contract.py` (PANEL: the IF-101 adapter, CHAT: the IF-201 adapter).

## PANEL (branch `goal/v3`)
**Built (commits in order):** T-01 `39bf66b` table `skill_runs`; T-02 `4a895b8` `skill_runs.py` (`SkillRunRecorder`); T-06 `9d58901` `skill-run-model.js`; T-04 `ca255bb` `skill_run_observer.py`, `Task.phases`, review stages; T-05 `8890dc2` IF-101 v16 on the real backend (`chat_service.py`, `chat_ops_api.py`) and the helper patch `edf0534` (installed by the owner from `specs/mia/goals/G-V3/contract-change-3/`); T-07 `64df84d` the strip (`skill-run.js`); T-08 `19d8b43` Full run part, link, reload, shares (`skill-run-shares.js`); T-09 `9bcddec` layout; T-10 `8531be9` card removed, README, CHANGELOG. Log: `specs/mia/goals/G-V3.PANEL/implementation-log.md` (read "Unspecified behavior" and "Open questions for Phase 4").

**Verify, first run (2026-11-12): verdict Not verified.** Report: `specs/mia/goals/G-V3.PANEL/verification-report.md` (commit `ad454f6`); brief: `verify-brief.md` in the same folder. All automated checks are green (unit suite in a clean checkout: one error, the known `test_tailscale` timeout; contract suites, PostgreSQL contract run, 12 browser tests run three times without a flip, restart test, 163 JS tests; protected diff is only the owner's helper patch; `trace_check` 545 errors identical to the tag, none for a G-V3 id; 24 of 34 mutants killed). The verdict is held back by:

| Id | Sev | Finding | Destination |
|---|---|---|---|
| F-01 | medium | `skill_runs.py` does load, change, save with no lock: answers (HTTP thread) race with reports (skill thread); probe on the file backend kept 0 of 60 answers while a reporting thread ran (REQ-WFM-133) | Implement fix (lock per recorder, or a per-run lock; test first from the probe) |
| F-02 | medium | `chat_service._emit_status` lets a storage read error reach `monitor.update` and `monitor.finish` of the skill; the observer swallows the same error (REQ-WFM-136) | Implement fix |
| F-03 | low | a chat link with a broken `%` (`#run=%E0%A4%A`) makes `decodeURIComponent` throw in `skill-run.js` `start()`: the strip stays empty (REQ-CLV-037/038) | Implement fix |
| F-04 | medium | no protected test makes another account's run a 404 on `/api/skill-runs/<id>` (mutant M10 survives); the code is correct | Plan amendment (a check) |
| F-05 | low | TC-CLV-036 measures the summary of `details#srv-full` (18.8 px), not the floating `.srv-full-body` (257 px at 34 %, 189 px at 25 %: the limit holds) | Plan amendment |
| F-06 | low | test gaps shown by surviving mutants: observer phase filter (M11, M12), paused state (M20), reason sent for done (M21), the wire 204 (M22), reason stored for done (M04), tie order (M02) | Implement: unit tests |
| F-07 | medium | `architecture.sysml:232` still lists the removed `task-card.js`/`task-card-model.js`; `tools/check_sysml_model.py` now fails ("files not found"; it passed at the tag); `skill-run*.js`, `skill_runs.py`, the observer are not in the model; the part `skillRuns : SkillRunSource` describes CHAT's relay | Plan amendment (model) |
| F-08 | low | the history-delete notice carries the deleter, not the owner: deleting one history record deletes all run records of that author; REQ-WFM-135 is ambiguous | owner decision |
| F-09 | low | `extension_loader` does not type-check manifest `phases` (a string becomes a tuple of characters; None or 5 raise TypeError) | Implement fix |
| F-10 | low | nothing closes a run record left `running` after a crash; `shown` prefers running runs, so it is shown as running after every restart | owner decision / backlog |
| F-11 | low | REQ-FE-032 has no check of its own (`req_graph` G7, same at the tag) | Plan amendment |
| F-12 | low | the new test `TestReviewPhases` in `tests/test_review_chat.py` has no `Example:` line (`test_doc_check`, +1 error) | Implement fix |

Facts from the reviewer: `plausibility.yaml` already holds the PANEL ratings (the brief's note was out of date); REQ-RTB-001 is not "changed since review" because `review-log.md` has the owner's row for its new fingerprint.

**Next for PANEL, in order:**
1. Ask the owner (questionnaire) about F-08 and F-10 and about the plan amendments F-04, F-05, F-07, F-11 (draft them as `A-14x` notes under `specs/mia/amendments/`; protected test material and `architecture.sysml` model changes come as a payload with `install.py`; free ids: A-144 and on in G-V3's range A-140..A-149, D-332 and on, check `tail specs/mia/review-log.md` first).
2. A **T-11 fix task** on `goal/v3` (plan commit first, then test first from the reviewer's probes in `/tmp/claude-1000/-home-maldun-prog-Python-MIA/cad505ab-8fd6-492b-9090-0cb8ca6b10ce/scratchpad/vp/`): F-01, F-02, F-03, F-09, F-12 and the unit-test gaps of F-06. Earlier pattern in this project: each fix round introduced one regression found by the next Verify run, so start every fix from the exact failing probe and run the reviewer's property style of probe again.
3. Second Verify run with a new brief (`verify-brief-run2.md`, like the one of G-V2.MODEL); then the owner accepts or rejects the remaining low findings as deviations; verdict "Verified with accepted deviations" needs an approval row in `review-log.md`.
4. Commit phase (merge master into the branch, checks, merge request draft, the owner merges; status updates on a branch of their own, Status lines only, no History lines).

## CHAT (branch `goal/v3.chat`, worktree `goal-v3-chat`)
**Built:** T-01 `35241c0` `skill_digest.py` (`SkillDigestStep`: no tools, calls below 95 % of the 4096-token input limit, long results in consecutive pieces and rounds, result text only in the user role, `version` "1"); T-02 `b149f7e` `ChatService.skill_turn` (kinds question, phase, done, failed, stopped; link added by code, a link in the model text is cut off; repair of model-worded texts; speech through a shared `_voice` taken out of `speak_again`; plain fallback sentences when the step is missing or raises) and the patch `specs/mia/goals/G-V3/contract-change-4/`; T-03 `045369d` `ChatService.model_history` and the one call in `communicator.py` (`skill_history` provider, `_with_skill_messages`). Log: `specs/mia/goals/G-V3.CHAT/implementation-log.md` (Findings, Stop conditions, Unspecified behavior).
**Green:** all 21 tests of `tests/acceptance/test_chat_skill_turns.py`; unit tests `tests/test_skill_digest.py` (5), `test_skill_turn.py` (4), `test_skill_history.py` (5); full unit suite 2079 tests, one error (`test_tailscale`). Everything runs on the fake model: **no Ollama run and no eval run has happened**.
**Waits for the owner:** `python3 -I specs/mia/goals/G-V3/contract-change-4/install.py --do` in the CHAT worktree (the real adapter of IF-201 in the protected `tests/helpers/contract.py` gets the option `phases`, a digest step on a scripted model and `skill_turn`; without it the four real variants of TC-IF-201-09 to -12 fail; with it, in a sandbox copy, all 100 tests of `test_if_201_chat_turn` and `test_if_101_chat_api` pass). After the install: commit `tests/helpers/contract.py` (message like `edf0534`), set T-02 to "done" in the log.
**Next for CHAT:**
- **T-04** harness target and scorer of EV-skill_turns (spike, tests, code; `eval-target-note.md`, `tests/acceptance/test_digest_score.py` red; the owner sets the target line in the two `suite.json` and creates `eval/labels/` afterwards).
- **The cases of EV-skill_turns** (24 dev, 24 holdout, 7 categories, injection 6 per split) are still unlabelled: drafts in `specs/mia/eval-drafts/skill_turns.jsonl` (untracked `.bak` beside it can go), the owner labels truth, faithful and persona and moves them into `eval/suites/skill_turns` and `skill_turns.holdout`. Never read or run the holdout as the coding agent.
- **T-05** dev runs and prompt tuning on `gemma4:12b-it-qat` (MP-light; check the digest with `ollama list` before the first run; needs the cases and the baseline; one change at a time, bump `skill_digest.VERSION` with every change of prompt, log every run with versions and pin; measure `secondBudget = 20.0` s). Do not run the full compose stack or the 26B model (hardware note `crash-fatal-mce-cpu`: loading one 12B model unloads the other on 16 GB).
- **T-06** hook-up after both subgoals are merged: `web_app.py` gives the service `digest`, `declared_phases` and sets `comm.skill_history = chat_service.model_history`; the observer of PANEL calls `skill_turn` at question, phase, end; integration check of AC-39 (`tests/integration/G-V3/test_run_end_to_end.py`, red on purpose).

## Open for the owner
1. Install `contract-change-4` (above).
2. Decide F-08 and F-10; approve the amendments for F-04, F-05, F-07, F-11 once drafted.
3. `deferred.md` TD-01 still names the superseded REQ-CLV-023 (move to REQ-CLV-038 needs the `Relaxed:`/`Target:` lines on REQ-CLV-038: a requirement change).
4. VAL-012 and VAL-013 are not rows in the review log; the look of the character in the changed box and the 820 px question (decided: no switch) are Validate items (VAL-012).
5. G-V3.CHAT `goal_check` GL11 (29 requirements, no subgoals) is known; REQ-RTB-001 is re-verified by the next Verify run with TC-RTB-001.
6. The branches `goal/v3` (PANEL) and `goal/v3.chat` merge into one line later: decide the order and who resolves the generated `architecture.sysml` block.

## Checks and commands (both worktrees)
```
/home/maldun/prog/Python/venvs/mia312/bin/python -m unittest discover -s tests -p "test_*.py" -q      # about 8 minutes, foreground; known: test_tailscale times out
node --test "tests/js/*.test.mjs"                                                                      # PANEL worktree: 163 pass
/home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/test_skill_run_view_browser.py       # 12 browser tests, needs podman, localhost/mia, localhost/mia-browser
/home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/test_chat_skill_turns.py             # CHAT worktree: 21 tests
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests    # 545 errors, none for a G-V3 id
python3 -I tools/check_sysml_model.py . && bash tools/check_sysml.sh                                   # PANEL: fails on the removed card files until F-07 is fixed
```

## Pitfalls met in this stretch (keep)
- A bash command that copies a protected helper into a payload folder was refused by the permission classifier; the working way is a unified diff made in a sandbox copy (`diff -u --label a/... --label b/...`) stored as `contract.patch` with an `install.py` that uses `git apply` (`patch` is not installed on this host).
- A route added to `chat_ops_api.py` shadows the mock server's route of the same path: re-point the endpoint in `ui/tools/skill_run_stub_server.py` (`app.view_functions["chat_ops_api.<name>"]`), and keep the URL parameter name of the real blueprint.
- With accounts on, the page's `app.js` is refused (403 `bad_origin`) unless the container address is in `web_app.allowed_origins`; `ui/tools/real_backend_stub.py` adds it.
- `backdrop-filter` on an element makes it the containing block of its `position: fixed` children (the open Full run part had to float outside the strip's box).
- A test that sets a value must also check what it measures: TC-CLV-036 measures the summary, not the floating body (F-05).
- Podman bind mounts need `:z`/`:O` (SELinux); stop test containers with `podman rm -f -t 0 <name>` (none should be left: `podman ps -a | grep g-v3`).
- `specs/mia/eval-drafts/skill_turns.jsonl.bak` is an untracked backup in the PANEL worktree; delete or ignore it.

## Not touched
The voice path, TD-11, A-130, FR-43, the graph editor, everything of G-V2, master, the holdout suites, `eval/suites`, `eval/baselines`, `deferred.md`, `plausibility.yaml` (ratings of PANEL already applied by the owner).
