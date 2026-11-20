# Verification report G-V3 (iteration goal: Skill run view and spoken-only chat), 2026-11-20

Line: `master` at `71dc3a71` (G-V3.PANEL, .CHAT and .REPORT are all merged; `goal/v3` is an ancestor). Clean checkout: worktree `/home/maldun/prog/Python/MIA-verify-g-v3` (branch `verify/g-v3`), venv `mia312`. Reviewer: one session that did not implement these goals; it read the subgoal reports, not their chats, and re-ran the checks. Verdict (proposal): **Verified with accepted deviations**, conditions in "Findings".

## 1. Automated results (clean worktree of master, foreground, in pieces)
| Check | Result |
|---|---|
| Unit suite `[a-c]` (main checkout) 678, `[d-m]` 498, `[n-r]` 589, `s[a-gi-z]` 422, `sh*` 20, `[t-z]` 269 | all OK (expected failures only, as recorded) |
| JS `tests/js` | 186 of 186 |
| Acceptance scripts (40) | all OK except `test_decide_guard.py` and `test_judge_calibration.py` (`behaviour.FUNCTIONS` missing; known on master, not G-V3) |
| Contract suites IF-101 (2 skipped), IF-102, IF-201 | OK |
| Contract IF-302 | 1 error: `snapshots` table (A-161, G-V2.SNAPSHOT, branch not merged yet); not G-V3 |
| `check_sysml_model.py` | OK |
| `trace_check` | 592 errors (baseline 587 + the TD-85 lines now listed); none for a G-V3 requirement except the relaxed ones with signed deferrals (TD-82, 83, 85); 4 WARN markers (REQ-CHA-071, CLV-044, 049, 055) accepted before |
| `goal_check` | the known G-V2/G-V3 GL1 error; no G-V3 specific error |
| `check_d_numbers` | only old collisions (D-103, D-182) |

Note on the first run in the main checkout: `test_expression_llm.ApiTest` (3) and `test_make_voice_lines` (1) fail there and pass in the clean worktree (leaked `setup_cfg.json`, and the folder is named `MIA`). Environment, not code.

## 2. Outcome criteria
| OC | Evidence |
|---|---|
| OC-1, 2 (view shows the run, result, files, answers) | `G-V3.PANEL/verification-report-run4.md` (4 runs, last without open finding), acceptance `test_skill_runs`, `test_skill_run_view_browser`, browser file; re-run green here |
| OC-3 (reload, restart, delete history) | `skill_runs` table, IF-302 contract and `test_skill_runs` green; hand check item 14 |
| OC-4, 5 (spoken-only chat, failed or stopped run) | `test_chat_skill_turns`, `test_end_message` (A-160), A-156 and A-158 reports; CHAT run 5 left F-33 to F-35, fixed and accepted (D-339, TD-85) |
| OC-6 (layout) | browser checks, JS 186 |
| OC-7 (skill unaware of the view) | scripted skill on the stub (`tests/integration/G-V3`) green |
| OC-8 (hostile text is only text) | TC-CLV-043, TC-CLV-052 (hostile report scenario), TC-CHA-049 holdout; REPORT V-2 defang |
| FB-08 (report, links) | `G-V3.REPORT/verification-report.md` plus T-06 and T-07 fixes, all tests green here; **hand check by the owner open** |

## 3. Agent checks
- Holdout EV-skill_turns decided by the owner 2026-11-16 on digest step version 7: REQ-CHA-049, 053, 054 PASS (`G-V3.CHAT/holdout-decision.md`).
- Digest step is now version 8 (A-160, options with `num_predict` and shortening, prompt text unchanged). Dev runs of version 8 (2026-11-19): faithful and persona 72/72, resisted 18/18, labelled. **No holdout run for version 8**; agents never run the holdout.
- A-162 (eval target) verified separately: `G-V3.CHAT/verification-report-a162.md`.
- Protected eval material: the diff against the plan baselines is dominated by other goals; every G-V3 change maps to an installed amendment (A-154, 155, 156, 157, 158, 160, 162) with a named owner approval in `review-log.md` (D-340 to D-353). No self-approved amendment found.

## 4. Findings
| ID | Finding | Severity | Destination |
|---|---|---|---|
| V3-1 | Digest version 8 has no holdout decision; the decision of 2026-11-16 covers version 7 (prompt text unchanged, call options changed) | medium | owner decides: re-run the holdout (owner only) or accept as deviation |
| V3-2 | REQ-WFM-137, 139, 140, 141, REQ-CLV-043, 048 to 052 are still Draft; REQ-CLV-023 (retired) is Draft | low | Commit phase: set Verified once the owner gates; mark 023 as retired |
| V3-3 | `G-V3.REPORT/goal.md` Phases still say Verify open and Commit open; the report exists and the code is merged | low | Commit phase paperwork |
| V3-4 | T-06 and T-07 of REPORT (V-1 to V-4 fixes, `plain_modules`) were not re-checked by a second fresh reviewer; this run re-ran every test after them, all green, but did not read the diffs | low | owner: accept, or a small brief |
| V3-5 | FB-08 hand check (`/lookup`, Report part, links, download) not done | gate | owner (VAL-012 / FB-08), guide given in the session |
| V3-6 | Not measured: calls and seconds of the end message with the short result; F-04 (status line not restored after reload, accepted D-344) | info | Validate |
| V3-7 | Open from earlier: the 14 112-character `/review` end message is not yet a labelled eval case | info | owner labels |

## 5. Not covered
No fresh holdout, no transcript review by a person (check F), no mutation testing of the REPORT code, no current-state deployment check. Budgets were not re-measured.

## 6. Verdict (proposal)
All in-scope checks are green on a clean checkout. Verified with accepted deviations if the owner settles V3-1 and V3-4 and does the hand check (V3-5). Then Commit: statuses (V3-2, V3-3), CHANGELOG, tag v0.2.0 (the owner tags, together with G-V2).
