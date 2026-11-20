## G-V3.CHAT: a spoken-only chat for skill runs, with the digest step (no version: subgoal of G-V3)

**Goal:** G-V3.CHAT (subgoal of G-V3, with G-V3.PANEL which is in master; supervised)   **Branch:** `goal/v3.chat` → `master` (head `0b4e0de` plus this file)
**Accepted by:** not an unsupervised goal; the owner (maldun) merges
**TLS:** `specs/mia/high-level-spec.md` (FR-35, FR-46, AC-39)   **HLS:** `specs/mia/high-level-spec.md`
**Goal record:** `specs/mia/goals/G-V3.CHAT/goal.md`
**Plan:** `specs/mia/goals/G-V3.CHAT/plan.md` (T-01 to T-06)
**Verification reports:** `specs/mia/goals/G-V3.CHAT/verification-report.md` and `verification-report-run2.md` to `-run5.md` (five runs; verdict of the last run: **Not verified**, then F-12 and F-14 fixed, F-33 to F-35 fixed in code and accepted as deviations by the owner without a re-check, D-339 and TD-85; see "Known issues")
**Holdout decision:** `specs/mia/goals/G-V3.CHAT/holdout-decision.md` (all three evaluated criteria PASS, owner, 2026-11-16)
**Implementation log:** `specs/mia/goals/G-V3.CHAT/implementation-log.md`

### What changes
- During a skill run the chat holds only what a person would hear: the questions of the skill, one short status message per declared phase, and one summary at the end with a link to the run in the Skill run view. The full result stays in the run record and the Skill run view (G-V3.PANEL).
- New **digest step** (`skill_digest.py`, `SkillDigestStep`, step version 7, prompt version 4): words the status messages, the end summary, the failure and the stop message in MIA's persona; no tool; the result is only ever the user text (TB-result, THR-012); long results are read in pieces within half the context (4096 of 8192 tokens). In the app it runs on the model profile `light` (REQ-CHA-065), the pin of its evals.
- `ChatService.skill_turn` (IF-201 v3): kinds question, phase, done, failed, stopped; link added by code; repair, speech and history of every message; `model_history()` goes to the chat model through `comm.skill_history`.
- **Cleaning of the model text** (`clean_model_text`, `strip_markup`, `escape_markup`, `cut_run_links`, `neutralize_run_links`): no HTML tag, no script or style content, no link to a run from the model; the guarantees hold by construction at the end of each function (found over five Verify runs).
- Evaluation: harness target `digest`, scorer `digest_score.py`, suite EV-skill_turns (24 dev, 24 holdout, labels by the owner), tools to label and to rescore (`make_digest_label_form.py`, `apply_digest_labels.py`, `rescore_digest_run.py`), scripts for the holdout and for cleaning up (`tools/holdout_skill_turns.sh`, `holdout_all.sh`, `cleanup_panel.sh`).
- 70 files changed against the merge base (about 3900 lines added).

### Requirements implemented
REQ-BE-078, REQ-WFM-036 (reworded: the 1200 characters are a request), REQ-CHA-008 and 014 (rev B, the new texts), **REQ-CHA-040 to REQ-CHA-066**: 040 to 047 and 055 to 060 skill turns, history, repair; 048 to 052, 061 to 063 and 065 the step (no tool, budgets, pieces, user role, profile light); **049, 053, 054** evaluated; 064 and 066 the cleaning of the model text (A-150 to A-152); 056 link added by code. Interface IF-201 v3 (contract-change-4 and -6, installed by the owner). Test requirements TR-CHAT-001 to 011, checks TC-CHA-040 to 071, TC-MIA-030 renamed TC-CHA-068.

### Plan amendments
- A-131 (plan of G-V3.CHAT, D-302, D-303), A-142 (IF-201 v3).
- **A-150** REQ-CHA-064 (no HTML tag), **A-151** (script and style content), **A-152** (REQ-CHA-065 profile light, REQ-CHA-066 no run link from the model, REQ-WFM-036 reworded, the time budget stated per call: measured 12.9 s for the slowest call of 20 s, 59.5 s for a 20 000-token result), **A-153** (paperwork: F-12 and F-14, installed by the owner as `3f9ab31`).
- Owner decisions: D-302 and D-303, D-304 to D-309 (renamed D-332 to D-337 against master), **D-339** (F-33, F-34, F-35 accepted as deviations).
- No frozen requirement changed (`goal_check.py --parent-ref master`: no finding for this goal; GL1 and GL3 belong to G-V2 and G-V3).

### Agent changes
| Pin | Model | Digest | Change |
|---|---|---|---|
| MP-light | gemma4:12b-it-qat | sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 | unchanged; the app now runs the step on the `light` profile (A-152) |

| Skill / pipeline | Old version | New version | What changed |
|---|---|---|---|
| digest step (`SkillDigestStep`) | – (new) | step 7, prompt 4 | six prompt versions measured (the three approved re-runs of T-05 are used), then output processing (steps 5 to 7: markup, links, fail-closed ends) |

| Suite | Requirement | Metric | Holdout, release (rate, 95 % interval, cases × repeats) | Previous baseline | Paired sign test | Wording |
|---|---|---|---|---|---|---|
| EV-skill_turns | REQ-CHA-049 | pass (quoted instruction reported, not followed) | 1.000 (0.610 to 1.000), 6 × 3 | none | – | threshold met (min 1.0) |
| EV-skill_turns | REQ-CHA-053 | faithful (people's label plus hard checks) | 0.958, 23 of 24 (0.798 to 0.993), 24 × 3 | none (the baseline file has no cases) | 0 shared cases, p = 1.000 (vacuous) | threshold met (min 0.85, low 0.70); **no claim of "not worse" or "better"** |
| EV-skill_turns | REQ-CHA-054 | persona (people's label) | 1.000, 24 of 24 (0.862 to 1.000), 24 × 3 | none | 0 shared cases, p = 1.000 (vacuous) | threshold met (min 0.80, low 0.70); same caution |

- **Red-team:** 6 of 6 injection cases resisted on the holdout in every repeat (RT-014, THR-012); on dev the same after the code repair of A-150 and A-151.
- **Budgets:** time of the step per call 2.5 to 12.9 s (`secondBudget` 20 s per call, unchanged); about 60 s for a 20 000-token result (7 calls); `tokenBudget` 4096 unchanged; a phase message delays the skill by one call (2 to 3 s). Measured by a spike on the pin, not by an eval run.
- **Baselines:** none new (a subgoal; `eval/baselines/skill_turns__nodigest__baseline.jsonl` stays as it is, without cases).
- **For deployment:** the model is pulled by digest (`ollama pull gemma4:12b-it-qat` and check `sha256:38044be4f923`); no new service; the app needs the profile `light` configured, otherwise the step falls back to the current model without a message (`pipeline_model.resolve`): check it before Deploy.

### Frozen requirements unchanged (goal_check.py --parent-ref master)
No finding for G-V3.CHAT (only GL1, GL3 and the warning GL11, known and not caused by this goal).

### Resolved feedback items
FB-01 (the chat shows the whole result of a skill) is the origin of G-V3; its re-validation criterion is VAL-012 and VAL-013 (Validate, real summaries in use).

### Known issues / accepted deviations
- **Verdict of the last Verify run: Not verified** (run 5: F-33 an exception on a character reference with more than 4300 digits, F-34 the link swallowed by an open code block, F-35 `<?` left as markup). All three are fixed in the code with tests that failed first; **the owner accepted them as deviations without a sixth run (D-339, TD-85)**. Nobody has re-checked the fixes independently. The page's DOMPurify has not been run on these cases (no DOM library in the repository).
- **TD-10** (REQ-CHA-008, the statistical persona check of ordinary dialogues) stays deferred: the interim check is `tests/test_persona_prompt.py`; the persona of status and end messages is decided by REQ-CHA-054.
- The **baseline of EV-skill_turns is empty**, so "not worse than the baseline" cannot be shown for REQ-CHA-053 and 054; the criteria are met on their thresholds.
- One holdout case is labelled unfaithful (23 of 24): read its transcript in Validate (VAL-013).
- The wiring of `web_app.py` (digest step, profile light, `comm.skill_history`) is covered by source tests and a fake-model integration check, **not by a run of the app against a real model**.
- The voice may read `&lt;` or `&amp;` aloud when a cleaning net fires (rare, F-38).
- `trace_check`: 530 errors (master: 538); none for the scope of this goal except the two TD-85 lines (`Relaxed:` and `Target:`), to be linked together with TD-81 to TD-84 in one amendment.
- The holdout of `skill_turns` is spent; three more holdout runs of the same suite exist (repeats at the same seed, not re-runs with fresh seeds, they decided nothing).

### Conflict resolutions
- Merge `0b4e0de` (master `a17ede7`, `split:dev` tags in five other suites): no conflict.
- Merge `b560ae1` (TOOLBOX, master `1fb0c35`): no conflict; checked after the merge: SysML model and parser, `check_d_numbers.py` (the two D-182 collisions exist in master), `trace_check` against master, the full suite.
- Earlier: the renaming of D-numbers against master (D-304 to D-309 are D-332 to D-337, A-143 is A-149), done by `fa41063` and `e67244d`.

### Checks on this branch (merged with master `a17ede7`)
- **Full unit suite:** 2327 tests, 2326 pass (4 skipped, 2 expected failures), 501 s. One test failed, `test_checkout_untouched`, because the implementing session wrote and committed this very file while the suite was running (the test reports that file as changed in the checkout). Run **alone and untouched** it passes (1 test, OK, 87.5 s, no file changed). Run the full suite once more on the merge commit before merging.
- Integration check of AC-39, acceptance tests, IF-201 contract suites (mock and real), `check_sysml_model.py`, `check_sysml.sh`, doc check of the goal's tests, plausibility (parses; the one error REQ-RTB-009 belongs to TOOLBOX): green as listed in `verification-report-run5.md`, re-run after the fix rounds.
- `check_d_numbers.py`: the two D-182 collisions that master has too. `trace_check.py`: 530 errors (master 538). `goal_check.py --parent-ref master`: no frozen requirement changed; `agent_check.py`: no error for this goal.

### History
Not rewritten: the branch is pushed. It has the task commits (T-01 to T-06), the amendment commits (A-150 to A-153), the fix commits naming the finding of each Verify run, the owner's installs and label commits, and docs. Merge with a merge commit to keep the audit trail; a squash would lose the finding-by-finding history that the verification reports refer to (the owner decides).

### To merge (the owner types it; no `git add -A`)
```
cd /home/maldun/prog/Python/MIA && git switch master && git merge --no-ff goal/v3.chat -m "Merge goal/v3.chat: G-V3.CHAT spoken-only chat with the digest step (REQ-BE-078, REQ-CHA-040 to 066, A-150 to A-153, D-339)"
```
Then the status update on a branch of its own (Status lines only, no History lines): REQ-BE-078, REQ-WFM-036, REQ-CHA-008, 014, 040 to 066 from Draft or Approved to Verified, except where the owner says otherwise (see "Known issues"), the Phases row Commit of G-V3.CHAT, and the TD-85 status line.

---

## Follow-up after the merge `8b8bd2a`: A-156, A-158, A-160 (built on `master`, no branch, no new merge)
`goal/v3.chat` is stale (one handover file that `master` lacks); the three amendments were planned, built and verified on `master` and pushed. The status of the 14 requirements below is Verified (`e18acf9d`). No version (subgoal of G-V3).

| Amendment | What changes for the user | Requirements | Verification |
|---|---|---|---|
| A-156 (FB-09, owner 2026-11-16) | a skill run speaks once: no chat message per phase (phases stay in the run status), the skill has no voice of its own where the run has an end message | REQ-CHA-041 (changed), REQ-CHA-067 (new) | REQ-CHA-041 in `verification-report-a158.md`; REQ-CHA-067 in `verification-report-req-cha-067.md` (two test gaps found and closed) |
| A-158 (owner 2026-11-17) | live status line of a run, last element of the chat, transient, restored after a question | REQ-CHA-068, 069, 070, 071, 072; REQ-CLV-053, 054, 055 | `verification-report-a158.md` (pass with findings, fixed) |
| A-160 (owner 2026-11-18) | the end message is bounded (1024 tokens per digest call, shortened once if over 1200 characters), Stop ends it with a plain sentence, the line stays until the text is ready, the review returns a short result | REQ-CHA-069 (clarified), 073, 074, 075; REQ-WFM-142 | `verification-report-a160.md` with the verification matrix (no findings) |
| A-162 (owner 2026-11-19) | the eval target `digest` runs the step as the app does: step options, pin seed, temperature and `num_ctx`, input text by checked reference | REQ-EVL-012, 013, 014, 015 | `verification-report-a162.md` (no findings, mutations repeated) |

**Contracts:** IF-101 v19 and IF-201 v4 installed (A-158, `d962ed27`). Known gap: IF-201 `done` and the IF-101 field `result` still say "the full result" while the review sends a short one (owner: no rewording).
**Checks (2026-11-19, clean worktree of `master`):** protected `test_end_message.py` 5 of 5; JS 186 of 186; full unit suite 2468 run, 2 failures, both `test_task_files_browser` (known); `check_sysml_model.py` OK; `trace_check.py`: no error for these requirements, two warnings (REQ-CHA-071, REQ-CLV-055: no marker, F-08 of the A-158 report).
**Agent changes:** digest step version 7 to 8 (A-160: `options` with `num_predict` 1024, task `shorten`, `DigestStopped`); prompt text unchanged; pin MP-light `gemma4:12b-it-qat` unchanged. **No eval run exists for version 8** (see open items); holdout decisions of the table above stand for the prompt, not for version 8. No new baseline (subgoal).
**Known issues:** F-04 of the A-158 report (the status line is not restored after a page reload, accepted as not now, D-344); not measured: calls and seconds of the end message with the short result; the transcript review by a person of the A-160 verification is open.
**Open before the iteration goal:** (1) dev run of EV-skill_turns for version 8 as feedback (`python tools/eval.py run skill_turns --pin <MP-id> --repeats 3`, never the holdout; tell a running session first); (2) the 14 112-character end message of the first real `/review` (run `01794952818010348-121f`, local only) is proposed as an eval case and labelled by a person.

