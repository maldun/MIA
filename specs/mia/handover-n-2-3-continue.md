# Hand-over for the next session (written 2026-10-27, late): N-2.5 done, N-2.3 in progress

Read this, then `CLAUDE.md`, `specs/mia/HANDOVER.md` (older, general), `specs/mia/review-log.md` (newest decisions D-87 to D-93) and `specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/implementation-log.md`. Everything below is **merged into master** (last code commit `d1442b6`); amendments A-13 to A-17 are installed. Start new work from a worktree: `git worktree add .claude/worktrees/<name> -b <branch> master` (create the worktree BEFORE writing files into it; a Write into a not yet existing worktree folder makes the later `git worktree add` fail).

## Done this session
- **N-2.5 Voice synthesis (T-01 to T-03, A-13).** `speech_service.py` (`SpeechService`, IF-204), `speech_text.py` removes html tags, `tools/make_voice_lines.py` + `library/voice_line_texts.json` (11 moods; the 11 clips `voice/expressions/<mood>_default.wav` are made and listed in `library/voice_lines.json`; the old `annoyed.wav` is no longer listed), acceptance tests TC-VOI-001..003. Open: nothing creates a `SpeechService` in `web_app.py` yet (waits for the N-2.2/N-2.5 integration).
- **N-2.3 Workflow management:** T-01 (`workflow_library.py`, IF-203 on the real Storage; A-14, A-15 = IF-302 v3 table `workflow_meta`), T-02 (skills as tasks and drafts confirmed by `tests/test_skills_as_tasks.py`; REQ-WFM-007 `promotion_record`; **A-16** reworded REQ-WFM-006 and REQ-BE-039: the gate checks specification and benchmark), T-03 (`check_budget`, `variant_of`, `step_view` with `budget_tokens` on a process node of the stored context graph = design-time template, may be optimised as new versions), T-04 (`tests/test_verify_workflow.py`, the verify workflow is the pipeline `verify.number_gate@4`), T-05 partly (below), T-06 partly (REQ-WFM-017 search command: `tests/test_search_command.py`).
- **A-17:** "limits" (REQ-WFM-023) = limits of the evidence plus the basis of the confidence figure, each `{code, text}` made by code; `verify.number_gate@5` (+ nodes `code.gate_record@2`, `code.gate_abstain@2`) returns them. `@4` and `@1` are unchanged; the skill `verify_claim` names no version, so nothing uses `@5` by default yet.
- Owner decisions today: promotion = the step to `tested` (trust is hard to measure); idea time = the first version; a context graph per workflow with the same id, optimised over time; REQ-WFM-006 reworded (narrow variant).

## Statistical evidence for REQ-WFM-014 and -015 (dev split, feedback only, not the Verify decision)
Runs of 2026-10-27 with the pin `MP-light` (gemma4:12b-it-qat, seed 7, temperature 0): the suite `verdicts_vitaminc`, tag `number`, a seeded sample of 100 dev cases (88 with a truth label: 36 false, 52 true; the holdout was never touched). Files: `data/eval/verdicts_vitaminc__t05-gate__20261027-214607.jsonl` (`verify.number_gate@4`, 3 repeats) and `data/eval/verdicts_vitaminc__t05-single__20261027-221911.jsonl` (`verify.single@1`, 1 repeat). `tools/eval.py compare` refuses unequal repeats, so the numbers come from a short script over the two files (case level, gate = majority of its repeats).

| | gate (`number_gate@4`) | single voice |
|---|---|---|
| wrong claims passed (of 36) | **0** (95 % interval 0 to 9.6 %) | 2 (1.5 to 18.1 %) |
| true claims not passed (of 52) | 9 (9.4 to 29.7 %) | 10 (10.8 to 31.9 %) |
| decided of 100 cases | 73 | 84 |
| seconds per run | 6.6 | 1.4 |

- REQ-WFM-014: the direction is as required (fewer wrong claims passed, no more true claims lost: 3 only the gate lost, 4 only the single voice lost), **but the difference is not statistically established**: the exact sign test gives p = 0.5 for the false passes (2 against 0 discordant cases) and p = 1.0 for the lost true claims. The gate abstains more (27 percentage points of coverage lost to 16 abstentions on labelled cases) and costs 4.7 times the time. For a decision the Verify session needs the holdout (never open it here) and more near-miss cases; an earlier 50-claim run (`eval/baselines/verdicts-styles.md`) found the same pattern, resting on three claims.
- REQ-WFM-015: all 100 cases gave the same status in all 3 repeats (100 of 100, lower bound of the 95 % interval **96.3 %**, limit 0.90). **Read with care:** the pin fixes the seed and temperature 0, so this shows the determinism of the server, not the variety of the model. A check without the pin (temperature as in production) would say more; it needs an owner decision because the pin is fixed in the eval spec.
- REQ-WFM-024 (no invented source) and the lookup half of REQ-WFM-015: not measurable until the lookup workflow exists.

## Next steps (suggested order)
1. **REQ-WFM-025** (state only through IF-102): an inspection test like `tests/test_chat_storage_imports.py` for `workflow_library.py` and the code that uses it.
2. **REQ-WFM-019, -020, -021** (review in time slices, stop by a code check, source records and cut-off): "Test" requirements; check first what the research pipeline already does.
3. **T-06 REQ-WFM-016 (lookup), T-07 REQ-WFM-018 (review report), T-08 REQ-WFM-022 (method transfer):** measurements on the pinned model, with the rest of REQ-WFM-015 and -024. Run them one at a time (one 12B model in 16 GB; never the compose stack or the 26B model).
4. TC-WFM-002/003/004/026 acceptance tests as a small amendment (like A-13's TC-VOI): their criteria are covered by `tests/test_workflow_library.py`, but no file carries the TC markers.
5. N-1 page details (about 3 hours, estimate): the counters tab (REQ-CHA-017/018, IF-101 v5; no requirement line in N-1.1 yet, add one by amendment or record it in the log) and the `due` input for tasks (A-09). Needs a look in the browser by the owner (`bash tools/start_testing.sh`, `ui/CHECKLIST_CHAT_PHONE.md`).
6. Then N-2.4 Workflow execution as a node cycle (the largest missing node; the code of the runner, sandbox and run log exists, the node requirements and tests do not), N-2.2 T-01 check, N-2.1 rest (REST codes, IF-104), N-4.2, N-5, the example workflows (root T-10) and the root integration (T-12). Order: `specs/mia/decomposition.yaml`.

## Open questions for the owner
- `verify.number_gate@4` has the status `draft` in its file (an explicit `@4` runs anyway). Promotion needs its specification and benchmark (root T-10).
- Whether `verify.number_gate@5` should become the version of the skill `verify_claim` (it adds `limits`; verdicts are unchanged: tested on the scripted model, not on the real one).
- The stability check without the pin (see above).
- `promotion_record` is not an operation of IF-203; if N-2.1 should report it, the interface needs an amendment.
- Postponed to field test (only the owner applies the label): AC-8, AC-25, T-04 items D-3 to D-5 and AC-24 (b); see `handover-n-2-5-start.md`.

## How to work (unchanged, short)
Tests: `bash tools/run_in_image.sh tests/test_x.py` (the host python is 3.14, the project 3.12; stdlib-only tests also run with `python3`); the eval harness runs with the venv from the MIA folder: `source ~/prog/Python/venvs/mia312/bin/activate; python tools/eval.py ...`. Amendments: draft under `specs/mia/amendments/A-NN/` and `specs/mia/contract-drafts/`, test on a scratch worktree, `tools/apply_amendment_aNN.sh` with `tools/amendment_lib.sh`, a decision in `review-log.md`. A shell command that mixes `cp`, `git`, variables and heredocs is often refused: use Write/Edit and small scripts in the scratchpad. Delegation to the local coder model (`local-coder`) failed twice today on a test with a temp folder and JSON round trip; short pure tests with a pasted fixture still work. End every branch job with exact merge commands, and commit every file first.
