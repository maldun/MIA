## G-V3: Skill run view and spoken-only chat (iteration goal, FR-34, FR-35, FR-46; no version yet)

**Goal:** G-V3 (iteration goal, supervised)   **Branch:** `goal/v3` and its subgoals, all already in `master` (head of this record: see the commit)
**Accepted by:** the owner (maldun) merged each subgoal; he tags
**Goal record:** `specs/mia/goals/G-V3/goal.md`   **Verification report:** `specs/mia/goals/G-V3/verification-report.md` (verified with accepted deviations, D-354)
**Subgoals:** G-V3.PANEL (merged `772abc2`, 2026-11-14), G-V3.CHAT (`8b8bd2a`, with follow-ups A-156, A-158, A-160, A-162 on master), G-V3.REPORT (`2db7f8d5`); each has its own `merge-request.md` or log.

### What changes for the user
- One **Skill run view** (strip across the page, details in the Full run) shows the running skill or the last run: status, phases, meters, pause, resume, stop, answers, result, files; it survives reload and restart.
- The chat holds only spoken text: questions, one status message per declared phase, a short end summary in MIA's persona with a link to the view; the status card is gone. A live status line shows the run in the chat.
- Every skill run ends with a **report** (Markdown file, first line the state) shown in the Report part, sources as links (http and https only), with a download (FB-08).

### Requirements
All of G-V3.PANEL, CHAT and REPORT are Verified. Set Verified in this commit: REQ-WFM-137, 139, 140, 141, REQ-CLV-043, 048 to 052. REQ-CLV-023 (status card) is superseded by REQ-CLV-030 to 039 and keeps the status Draft (no status "retired" exists; nothing to verify).

### Checks (2026-11-20, clean worktree of master)
Unit suite in six pieces green; JS 186 of 186; acceptance scripts green except `test_decide_guard.py` and `test_judge_calibration.py` (as on master); IF-101, IF-102, IF-201 contract suites green; `check_sysml_model.py` OK. The IF-302 contract fails on the `snapshots` table of G-V2.SNAPSHOT (not merged yet, not G-V3). `trace_check`: 592 errors, none new from this goal (TD-82, 83, 85 are signed deferrals).

### Agent changes
| Item | Before | After | Note |
|---|---|---|---|
| EV-skill_turns holdout (REQ-CHA-049, 053, 054) | – | PASS, digest step version 7 (owner, 2026-11-16, `G-V3.CHAT/holdout-decision.md`) | version 8 has dev runs only (deviation V3-1) |
| digest step | – | version 8 (A-160: `num_predict` 1024, shortening, stop text) | prompt text unchanged |
| skills `lookup`, `review`, `search` | 1 | 2 (need `run_report`) | G-V3.REPORT |
| model pin MP-light | `gemma4:12b-it-qat` | unchanged; `num_ctx` 8192 added to the pin record of `tools/eval.py` (A-162) | no change of the model |
| red-team cases | – | no case regressed in the subgoal verifications | no new run in this Verify |
| budgets | – | no change measured | not re-measured |
No baselines are written: the quick eval subset was not re-run (no eval path changed since the verified runs except A-160 and A-162, both covered by their own reports); baselines are recorded with the release run.

### Known limitations and open items
V3-1 and V3-4 (accepted deviations). F-04 (status line not restored after a reload, D-344). Not measured: calls and seconds of the end message. Open deferrals TD-82 to TD-85 (signed).

### Next
Tag v0.2.0 together with G-V2 (owner decision 2026-11-08: the tag comes with iteration 2); join the two `[Unreleased]` blocks of the CHANGELOG then.
