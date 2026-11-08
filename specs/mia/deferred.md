# Deferrals: MIA

Compromises we chose on purpose (blueprint M26). People decide; agents propose with effort and risk and never weaken a check.
Check with `trace_check.py` (records, `Relaxed`/`Target` links, `deferred` markers, TODO references, trigger dates).

Proposed on 2026-10-29 after the usability work of N-2.3 T-09 to T-11 and N-1.1 T-09 (A-23, A-24, D-101, D-103). Every record below is a proposal: the owner confirms, changes or drops it
(the line `Decision` names the person who has to decide).

## TD-01 – The status card is gone after a reload
- Kind: defer
- Requirement: REQ-CLV-023
- Interim criterion: the card is checked in a browser (`tests/test_task_files_browser.py`, TC-CLV-023: draw, update in place, pause, resume, stop, late status after done, 360 px) and its model with `node --test` (`tests/js/taskcard.test.mjs`); the card lives as long as the page is open
- Target: a card that is still there, with its final figures, after a reload (browser test)
- Reason: a card after a reload needs the status to be kept with the history, which is a change of the interface (IF-101)
- Effort: about half a day for the kept card (a field in the history record and in the amendment of IF-101)
- Risk of the gap: after a reload the user sees no final figures of a finished task. Mitigation: the report and the files tab keep the result
- Owner: Stefan Reiterer
- Trigger: the chat mock server sends `task_status` and files events, or the Plan of FB-01, or 2026-12-31, whichever first (the browser harness exists since D-141; D-172)
- Target check: specified only
- Decision: confirmed by Stefan Reiterer, 2026-11-01 (D-172)
- Note: narrowed to the reload target on 2026-11-07 on the owner's instruction; the browser part is done (branch `td-01-02-browser-tests`). FR-46 (goal B) moves the card into the skill subwindow, so the reload target may be redone there.
- Status: open

## TD-02 – The Files tab is not tested in a browser
- Kind: defer
- Requirement: REQ-CLV-024
- Interim criterion: the routes are tested (`tests/test_files_api.py`, the IF-101 contract suite TC-IF-101-30); the tab itself is looked at by the owner
- Target: a browser test that lists the files newest first, checks the download link and the redraw after `files_changed`
- Reason: the same missing browser test harness as TD-01
- Effort: part of the harness of TD-01, about half a day more
- Risk of the gap: a wrong link or a list that does not redraw is found by a person only. Mitigation: hand test, step 4 of the list
- Owner: Stefan Reiterer
- Trigger: the chat mock server sends `task_status` and files events, or the Plan of FB-01, or 2026-12-31, whichever first (the browser harness exists since D-141; D-172)
- Target check: specified only
- Decision: confirmed by Stefan Reiterer, 2026-11-01 (D-172)
- Status: done
- Closed: 2026-11-07, marked done on the owner's instruction; browser test `tests/test_task_files_browser.py` (TC-CLV-024: newest first, download links, redraw after `files_changed`, no delete control)

## TD-03 – Tokens on the card are an estimate
- Kind: relax
- Requirement: REQ-WFM-032
- Interim criterion: the tokens of a review are counted as characters divided by 4 and shown as an estimate (the page says "Tokens (estimated)"); calls, search requests and sources are counted exactly
- Target: the tokens used are the counts that the model server reports for each call
- Reason: the pipeline runner does not pass the token counts of the model server on (`tokens_out` is None in its events); passing them touches the model interface (IF-103) and the run log
- Effort: about half a day, in the pipeline runner and the run log, plus an amendment of IF-103 if the counts are part of the interface
- Risk of the gap: a hard cap on tokens may end a run too early or too late by the error of the estimate (a factor of about 1.5 for English, more for other scripts). The cap is 10 times the limit and ends a run only in extreme cases
- Owner: Stefan Reiterer
- Trigger: the first review run that ends at the cap of tokens, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Status: open

## TD-04 – The glue of lookup and search stays in the core
- Kind: relax
- Requirement: REQ-WFM-039
- Interim criterion: the three skills are folders with a manifest and an entry, the core names none of them (inspection test), the code of the review lies in its folder; `research_chat.py` (the glue of lookup and search, and `friendly_error` that the review also uses) and `research.py` stay in the core
- Target: the code of lookup and search lies in their folders; what the three share (the plain text of a failure, the speaking of an answer) is a small library of the core with its own name
- Reason: the three skills share `research_chat.py` today and `research.py` is used by the core runner; splitting it is a larger change with many test imports and no gain for the user now
- Effort: about 1 day (move, shared library, imports of about 10 tests), in the refactoring form of M31
- Risk of the gap: a new skill may copy the habit of putting its glue into the core. Mitigation: the inspection test `tests/test_core_names_no_skill.py` and the manifests as the model for a new skill
- Owner: Stefan Reiterer
- Trigger: the fourth skill is added, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Status: open

## TD-06 – The workflow library folder is not there yet
- Kind: defer
- Requirement: REQ-GTB-004
- Interim criterion: workflow documents are stored and checked through the graph tables (IF-301) and the library API; TC-GTB-005 stays skipped
- Target: `library/workflows` exists (root task T-10) and TC-GTB-005, rewritten for the entry format after D-108 and D-112, runs green
- Reason: T-10 never ran; the entry format of the test predates D-108/D-112, and FB-03 re-specifies how workflows are built
- Effort: about half a day after FB-03's Explore
- Risk of the gap: workflow documents have no folder form to back up or review by hand. Mitigation: the database backup (N-4.2)
- Owner: Stefan Reiterer
- Trigger: root task T-10, or 2026-12-31, whichever first
- Target check: skip: `library/workflows` is missing (root task T-10); TC-GTB-005 is rewritten with FB-03 and then carries deferred('TD-06') until green
- Decision: D-160, 2026-10-31, Stefan Reiterer
- Status: open

## TD-07 – Judge calibrations are not loaded yet
- Kind: defer
- Requirement: REQ-EVL-003
- Interim criterion: the calibration functions of `harness.py` and `metrics.py` are tested on fixtures; no eval target uses a judge, so nothing is calibrated
- Target: the harness loads the calibration of each judge and applies it in every run whose target uses that judge
- Reason: no target has a judge in G-V1 (N-4.1 Verify, D-166)
- Effort: about 2 h with fake-model tests
- Risk of the gap: a first judge would run uncalibrated. Mitigation: the trigger below
- Owner: Stefan Reiterer
- Trigger: the first eval target with a judge, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-166, 2026-10-31, Stefan Reiterer
- Status: open

## TD-08 – Older eval suite kinds run the in-process Core
- Kind: defer
- Requirement: REQ-EVL-011
- Interim criterion: workflow targets run through IF-105 with the pinned model and the recorded versions; the older suite kinds run the in-process Core with `--pin` and the versions in the header
- Target: every suite kind runs through IF-105
- Reason: the older suite kinds are research experiments whose form FB-03 re-specifies (N-4.1 re-verification R3, D-172)
- Effort: about half a day after FB-03's Plan
- Risk of the gap: an older suite kind could measure a path the app does not take. Mitigation: the header names the pin and the versions
- Owner: Stefan Reiterer
- Trigger: the Plan of FB-03, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-172, 2026-11-01, Stefan Reiterer
- Status: open

## TD-09 – Deleting the chat history after a confirmation
- Kind: defer
- Requirement: REQ-CHA-005
- Interim criterion: the history is bounded and the oldest messages are dropped over the limit (`test_oldest_are_dropped_over_the_limit`); the only deletion is the token-guarded legacy route `POST /api/chat/clear`, which the page does not offer
- Target: a user deletes the history on the page after a confirmation dialog; the backend refuses a deletion without `confirm: true`; the IF-101 contract names the operation
- Reason: no page control and no confirmation parameter exist; privacy is not an issue for now (D-131); it needs an IF-101 amendment and a page change
- Effort: about half a day (backend flag, button and dialog, amendment, tests)
- Risk of the gap: a user cannot delete the history on his or her own. Mitigation: the operator deletes the `history` records
- Owner: Stefan Reiterer
- Trigger: the first request to delete a history, or 2026-12-31, whichever first
- Target check: specified only
- Sign-off: Stefan Reiterer, 2026-11-01
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Status: open

## TD-10 – Persona check dialogues (AC-8)
- Kind: defer
- Requirement: REQ-CHA-008
- Interim criterion: the persona file is read at every call, the default address is "master", and the persona message is the system message of every call (`tests/test_persona_prompt.py`)
- Target: AC-8 is decided statistically: check dialogues against the baseline of today's MIA, with the rule fixed in Plan (D-52)
- Reason: it needs the labelled dialogues and a baseline run; the owner postponed it to after the field test (2026-10-26)
- Effort: about one day plus GPU time
- Risk of the gap: the persona can drift without a number. Mitigation: the owner's use
- Owner: Stefan Reiterer
- Trigger: the first iteration after the field test
- Target check: specified only
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Status: open

## TD-11 – The voice goes through IF-204
- Kind: defer
- Requirement: REQ-VOI-001
- Interim criterion: the app speaks through `SpeechStreamer`, the sound server (`speak.py`) and `Speaker.render_voice` with the `speech_text` filter; `SpeechService` passes the IF-204 contract suite and TC-VOI-001 to -003; the chat agent emits one `audio_chunk` per sentence of an answer (TC-IF-201-01 green, `tests/test_chat_answer_events.py`)
- Target: the playback of the chat agent's voice on the backend goes through `SpeechService` (IF-204) instead of `SpeechStreamer` and the sound server, with the order of sentences, stop, speak again and repair (REQ-CHA-014) kept; needs a Plan step first (see the Note)
- Reason: the older route works on the host; `SpeechService.synthesize` renders one sentence to bytes and has no playing, ordering, pipelining or cancel, so routing the playback through it means a new backend playback pipeline (probably a changed audio-route contract), not wiring; it risks the working voice for no gain to the user now
- Effort: open until the Plan step (the agent's first estimate of one day was for wiring only)
- Risk of the gap: two routes may diverge. Mitigation: both use `speech_text` and `render_voice`
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration, or 2026-12-31, whichever first
- Target check: specified only (the IF-201 case TC-IF-201-01 is green; the IF-101 case TC-IF-101-04 stays skipped until the expression event exists, see A-130 section 8)
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Note: 2026-11-07, owner Stefan Reiterer (D-275): narrowed. The IF-201 part is done (answer events, helper fixes D-272 and D-274, `chat_service.py`); the `expression` event is split out of TD-11 (A-130 section 8, draft TD-60, not yet adopted). What stays open is the playback route. A Plan step has to come first: an amendment for the audio route, a requirement for stop and ordering, and host hand-test criteria. See `amendments/A-130-note.md`.
- Note: 2026-11-07, found in the hand test on the host (owner Stefan Reiterer, D-276): the button "Speak again" does nothing. `/api/speak_again` only emits `audio_chunk` events and no page code handles them (`templates/static/chat/` has no `audio_chunk` handler); live answers are spoken by the backend sound server. Not caused by the TD-11 work (`speak_again` is unchanged). Folded into the Plan step of this deferral: speak again plays through the backend voice route; the Plan step needs a requirement and a failing test first.
- Status: dropped
- Closed: 2026-11-07, replaced by TD-61 (owner decision, D-278); the IF-201 work (answer events, `chat_delta` flush, helper fixes) is recorded in D-275 and D-277; "Speak again" is planned as the requirements REQ-CHA-030 to 034 (A-132, option B), not as a deferral

## TD-12 – Verify before asserting; lookup (TC-MIA-002)
- Kind: defer
- Requirement: FR-9, FR-10
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them the number gate (`tests/acceptance/test_number_gate.py`), `tests/test_claim_pipelines_check_first.py`, `tests/test_verify_workflow.py`, `tests/test_search_command.py`; the pipelines run on the fake model
- Target: the suites of the verify workflow (VitaminC and Wikidata, holdout, MP-light, single voice as baseline, 3 repeats) are decided by `eval_decide.py` against the baseline: the chosen gate passes fewer wrong claims and loses no more true claims among those with evidence (AC-2)
- Reason: the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); the verdicts suites have holdouts, the lookup suites (`research`, `research_compound`) have none (12 + 8 cases are for the owner to label); the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about 2 days plus GPU time (proposed)
- Risk of the gap: a gate that passes more wrong claims than the single voice is not seen; the owner's use shows it
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-13 – Literature review quality (TC-MIA-003)
- Kind: defer
- Requirement: FR-11, FR-12, NFR-4
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them `tests/test_review_stages.py`, `tests/test_review_request.py`, `tests/test_gate_limits.py` and the scholarly source contract (IF-405)
- Target: the review benchmark per tier: source recall and precision against the recorded baseline, 0 violations of the cut-off, 0 invented references, 100 % of quotes anchored (AC-3)
- Reason: the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); the review entry is out of G-V1 (REQ-RUN-013 partly, D-128, D-130), the suite `review_toy` has no holdout and the recall threshold is the owner's (open question 3 of the draft); the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about 3 days plus GPU time and the owner's labels (proposed)
- Risk of the gap: invented references or unanchored quotes in a review are found by a reader only; the cut-off and the retraction rules are tested in code
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-14 – The skill path (TC-MIA-009)
- Kind: defer
- Requirement: FR-20
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them `tests/test_skill_path_doc.py`, `tests/test_seed_workflows.py`, `tests/test_check_baselines.py`, `tests/test_workflow_library.py`
- Target: the record of the skill path: lookup as the documented example, the literature review added by the same path with specification, context graph and benchmark with holdout and baseline, and the review promoted within one month of the lookup (AC-9)
- Reason: the review is the next goal's (VAL-002 moved, D-134), so the second workflow of the skill path does not exist yet; the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about 1 day to read the record once the review is promoted (proposed)
- Risk of the gap: the path may not work for a second workflow; found when the review is added
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-15 – Adaptation to negative feedback (TC-MIA-011)
- Kind: defer
- Requirement: FR-29
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them `tests/test_chat_behaviour.py`, `tests/test_converse_behaviours.py`, `tests/test_chat_answers.py`
- Target: the statistical run of AC-11: after 5 net negative votes at most 10 appearances in 1000 opportunities with fixed seeds, a higher rate after a positive vote, a vote on a fact leaves the fact unchanged; the implemented rate is 0.5 %, not 1 % (finding F-1 of the test table)
- Reason: the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); the seeds, repeats and the rate (0.5 % implemented, 1 % in the text, finding F-1 of the test table) are not decided; the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about half a day (proposed)
- Risk of the gap: the rate after votes may differ from the wording; the unit tests of the mechanism pass
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Sign-off: Stefan Reiterer, 2026-11-01
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-16 – Speed and frame rate (TC-MIA-019)
- Kind: defer
- Requirement: NFR-7
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them `tests/test_measure_latency.py`, `tests/test_runner_budgets.py`, `tests/test_model_turns.py`; the order of the turns is tested
- Target: BM-MIA-001 (first text within 10 s on MP-light, also while a review slice runs) and BM-MIA-002 (30 fps or more on any phone inside the network and on desktop), median of repeated runs on the reference hardware (AC-19); and the baseline of BM-GATE-001 (seconds per claim of the number gate on MP-light, `benchmarks/baseline.json`) is measured, so that `tests/acceptance/test_benchmarks.py` turns green
- Reason: the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); the benchmark REQ-RUN-007 is a proposal of the draft that needs an amendment to live under `benchmarks/` (open question 4), the 10 s part is out of G-V1 (REQ-RUN-009 partly, D-128) and the frame rate on the phones is a field measurement (D-62); the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about 1 day plus the field measurement (proposed)
- Risk of the gap: slow first text or low frame rates are found by the users; VAL-006 collects them in use
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-17 – Cost of the first try; comparing variants; learned choices (TC-MIA-022)
- Kind: defer
- Requirement: NFR-2, FR-17, FR-18
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them `tests/test_runner_context_share.py`, `tests/test_eval_platform.py`, `tests/test_judge_calibration.py`
- Target: the lookup suites on MP-light: fewer than 15 model calls per question, every model input at most 50 % of the context window, variants compared on the same cases with repeats, a learned choice logged next to the default and reversible (AC-22)
- Reason: the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); the AC-22 measurement is out of G-V1 (REQ-RUN-005 partly, D-128), the criterion for REQ-RUN-006 is only a proposal in the draft, and the learning layer is not built (REQ-RUN-004 out, D-119); the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about 2 days plus GPU time (proposed)
- Risk of the gap: the first try may need more calls than planned; the budget refusal of the runner holds
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-18 – Memory that improves (TC-MIA-024)
- Kind: defer
- Requirement: FR-14
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them `tests/test_memory_records.py`, `tests/test_chat_memory.py`, `tests/test_items_api.py`, `tests/test_memory_write_skill.py`
- Target: the memory test set (store, update, contradict, recall, unknown) is passed at least as well as today's summary-based dreaming at equal or lower token cost; every record shows its source and can be corrected and deleted (AC-24)
- Reason: the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); the check is marked later and Should in the root table, and no criterion for the memory test set is in either draft; the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about 3 days plus GPU time (proposed)
- Risk of the gap: memory quality is judged by the users; records can be corrected and deleted
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-19 – Speech rules (TC-MIA-025)
- Kind: defer
- Requirement: FR-15
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them `tests/test_chat_repair.py` and `tests/test_speech_repair.py`
- Target: the behaviour suite with the speech-rule detectors keeps the recorded precision and recall; a violation is repaired silently and never enters the memory as a scolding (AC-25)
- Reason: the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); the suite `behaviour` exists without a recorded baseline and without a holdout, and no criterion for the detectors is in either draft; the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about 1 day (proposed)
- Risk of the gap: a detector may drift without a number; the repair tests pass
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-20 – Estimate before a run (TC-MIA-028)
- Kind: defer
- Requirement: FR-33
- Interim criterion: the node tests of the row pass (listed for the row in `specs/mia/tc-mia-status.md`), among them `tests/test_workflow_library.py` and the IF-202 and IF-203 contract suites; the refusal of a run whose estimate exceeds its budget is tested
- Target: on the recorded lookup runs the estimate of time, calls and tokens lies within a factor of 3 of the measured time, either way (AC-28, OPEN-3)
- Reason: the eval specs are drafts the owner has not approved (`specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`), no baseline run is recorded as a .jsonl in `eval/baselines`, and the goal Verify did not run stage 4 (D-178); no criterion for the estimate is in either draft, and no set of recorded lookup runs is named as its reference; the stage 4 rows of the root table were deferred at the goal Verify of G-V1
- Effort: about 1 day once runs are recorded (proposed)
- Risk of the gap: the estimate may be off by more than 3; the user sees the estimate and the run still works
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-178, 2026-11-01, Stefan Reiterer
- Status: open

## TD-21 – The state is in PostgreSQL
- Kind: defer
- Requirement: NFR-8, CON-7
- Interim criterion: the storage layer behind IF-102 works on files and is tested there (`tests/test_storage.py`, the IF-102 contract suite on the file backend) and on PostgreSQL where psycopg exists (`tests/test_storage_postgres.py`, `tools/contract_postgres.sh`, not run in the goal Verify); the stack starts the database and `deploy/up.sh backup` and `restore` save and restore it together with the data folder; the app keeps its state in the file backend (`web_app.py`), accounts, history, records and workflows alike
- Target: the app reads `MIA_DATABASE_URL`, the `mia` image holds psycopg (`requirements-db.txt`), the shared state is in PostgreSQL, files to database and back give identical files, a change by one user is visible on a second connection within 5 s with its author, and backup and restore return the same records (AC-15, TC-MIA-015)
- Reason: the storage layer was built and verified node by node (N-3.1 to N-3.3), but wiring the app and the image to it was never planned as a task; recorded at node level (D-139 (4), N-4.2 F3) and found at the goal Verify (F-01); the owner chose to defer it (D-180)
- Effort: about 2 days (wire `web_app.py` to `Storage` on PostgreSQL, add psycopg to the image, the move command, run the PostgreSQL contract suites, rebuild the image) (proposed)
- Risk of the gap: a lost or damaged data volume loses the state; the database that runs is empty. Mitigation: `deploy/up.sh backup` saves the data folder, to be done before every update
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-180, 2026-11-01, Stefan Reiterer
- Status: open

## TD-22 – Red-team cases of the untrusted inputs
- Kind: defer
- Requirement: NFR-3
- Interim criterion: the deterministic mitigations pass: the tool door and its untrusted-input handling (`tests/test_tool_calls_untrusted.py`, `tests/test_tool_calls_web_log.py`), the sandbox tests, the injection signal checks and the PDF wall (`tests/test_pdf_text.py` with bwrap); the compose stack runs with `sandbox_backend: none`, so the script check is off there
- Target: 0 failures over all red-team cases: the seven `rt_*` suites hold enough labelled cases (not 2 each, target kind `pending`) and the injection suites `verdicts_injection` run with their holdouts on MP-light (TC-MIA-006, AC-6)
- Reason: the red-team suites are drafts of 2 cases each, their cases are the owner's to label and the runs belong to the stage 4 evals that were deferred (D-178); `tests/test_harness.py` fails on the same fact (rt_edit has 2 cases, wants 30); found at the goal Verify (F-02), the owner chose to defer it (D-180)
- Effort: about 3 days plus GPU time, the labelling is the owner's (proposed)
- Risk of the gap: an injected instruction in a page or paper may change a verdict or start a tool without a test noticing. Mitigation: the tool set per step is the protection (THR entries), the deterministic tests above, and the users are trusted (CON-6)
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration, or 2026-12-31, whichever first
- Target check: specified only
- Sign-off: Stefan Reiterer, 2026-11-01
- Decision: D-180, 2026-11-01, Stefan Reiterer
- Status: open

## TD-23 – Real sides of the contract suites IF-103, IF-404, IF-405
- Kind: defer
- Requirement: IF-404, IF-405, IF-103
- Interim criterion: the mock side of each suite is green and the providers are covered by node tests (`tests/test_tool_calls*.py`, `tests/test_scholar.py`, the fake model server of the chat and runner tests); IF-111 has `ui/godot/tools/test_bridge.gd` as its real side (D-155, D-175), IF-102 on PostgreSQL is in TD-21
- Target: the three suites run their real side: IF-404 against the web client and SearXNG, IF-405 against the scholarly APIs, IF-103 against a real model-server provider (stage 2, decomposition rule 3); the IF-104 JS real cases name `tests/test_graph_api.py` as their real side or run against the routes
- Reason: the real sides need the network, the search engine or the model server, and the IF-103 suite cannot hand its scripted replies to a real provider (REQ-RUN-011 out, D-118); found at the goal Verify (D-5, F-03); the owner chose to give them a record (D-181)
- Effort: about 2 days (the IF-103 provider and a suite amendment included) (proposed)
- Risk of the gap: a mock that differs from the real service goes unnoticed; the node tests and the owner's use are the check
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-181, 2026-11-01, Stefan Reiterer
- Status: open

## TD-24 – Sandbox backend in the deployed stack
- Kind: defer
- Requirement: REQ-TLS-005
- Interim criterion: REQ-TLS-005 holds by its refuse branch: with `sandbox_backend: none` a script check reports unavailable and nothing runs (the sandbox tests, `tests/test_sandbox*.py`, pass with bubblewrap on the host); the PDF wall and the tool door do not depend on it
- Target: the deployed stack has a sandbox backend (bubblewrap or podman) so that the script checks run there, and the red-team cases for scripts (THR-005) are run against it
- Reason: `deploy/setup_cfg.compose.json` sets `sandbox_backend` to `none`, so the script check is off in the stack; found at the goal Verify (D-8, F-15); the owner chose to give it a record (D-181)
- Effort: about 1 day (a backend in the image or next to it, the config, a smoke test) (proposed)
- Risk of the gap: the checks that run model-written code are not available in the deployed system, MIA refuses them; nothing unsafe runs
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-181, 2026-11-01, Stefan Reiterer
- Status: open

## TD-25 – The smoke tests are not part of the merge gate
- Kind: defer
- Requirement: NFR-9
- Interim criterion: the same ground is covered by the stage 3 steps `container-alone` (TC-API-013) and `contract-postgres` (IF-102 on a throwaway postgres:16), by the stage 2 integration steps and by the tests of the compose files (`tests/test_deploy.py`, `tests/test_delivery_on_stack.py`); the smoke tests themselves are run in Deploy
- Target: the smoke tests of `tests/smoke/` have run on the owner's workstation in the Deploy phase of G-V1 (`goals/G-V1/deploy-plan.md`), their results are in `deployment-record.md`, and the stage ladder has a smoke step that finds them (pattern `smoke_*.py`)
- Reason: `tests/smoke/` holds `smoke_fresh_install.py` (SMOKE-MIA-001), `smoke_stack.py` (SMOKE-MIA-003) and `smoke_gate.py` (SMOKE-GATE-001, -002). The step `smoke` used the pattern `test_*.py`, found no test and failed with NO TESTS RAN. The files themselves say they run on the owner's workstation in Phase 6: the first two bring up the whole compose stack (this machine cannot run it, fatal CPU machine checks at shutdown under load), the third runs the number gate through the real Ollama, which is an eval-style run (none belongs in this Verify, D-178); found at the merge gate of G-V1, the owner chose this (D-182)
- Effort: about half a day on the workstation (three commands, then the record), and one line in `stages.yaml`
- Risk of the gap: a fresh install that does not start, or a stack whose front does not answer, is found in Deploy and not at the merge. Mitigation: `container-alone`, `contract-postgres` and the stack test of N-1.3 run in the gate
- Owner: Stefan Reiterer
- Trigger: the Deploy phase of G-V1, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-182, 2026-11-01, Stefan Reiterer
- Progress 2026-11-02: the three smoke scripts ran green on the owner's workstation (`goals/G-V1/deployment-record.md`); still open: a smoke step in `stages.yaml` that finds `smoke_*.py`
- Status: open

## TD-26 – The Tailscale smoke test SMOKE-MIA-002 was not run in Deploy
- Kind: defer
- Requirement: NFR-6, CON-5 (OP-4 of the baseline: Tailscale never tried against a real tailnet)
- Interim criterion: MIA is published on 127.0.0.1 only (`ss`: `127.0.0.1:8585` and `:8586`, shown in the deployment record); the https front of the stack answers in the smoke test SMOKE-MIA-003; `tests/test_tailscale.py` covers `tailscale_serve.py` and `ui/tools/remote.sh` with a fake `tailscale`
- Target: SMOKE-MIA-002 run once on a phone outside the home network (`ui/tools/remote.sh up`, page loads, a message is answered, `tailscale serve status` shows no Funnel, no public port), result in `goals/G-V1/deployment-record.md`; it is a precondition of VAL-004
- Reason: Tailscale is not installed on the workstation (2026-11-02); the owner defers the setup (account, MagicDNS, HTTPS certificates) to a different run
- Effort: about an hour once (install, `tailscale up`, admin console, phone), then five minutes
- Risk of the gap: the phone path over the tailnet (origin handling, certificate, secure context for the 3D character) is untested; VAL-004 cannot be judged without it; a finding is possible
- Owner: Stefan Reiterer
- Trigger: before VAL-004 starts, or 2026-12-31, whichever first
- Target check: specified only
- Decision: D-184, 2026-11-02, Stefan Reiterer
- Status: open

## TD-61 – The app has two voice paths: the sound server and SpeechService
- Kind: defer
- Requirement: REQ-VOI-001
- Interim criterion: live answers and "Speak again" are spoken through `SpeechStreamer` and the sound server (`speak.py`), with `Speaker.render_voice` and the `speech_text` filter; `SpeechService` (IF-204) passes its contract suite and TC-VOI-001 to -003 but nothing in the app calls it; both paths share `speech_text` and `render_voice`
- Target: one voice path: the sentences of every answer and of every spoken-again message are rendered and played through one component built on `SpeechService` (IF-204), with the order of sentences, rendering ahead, stop and the repair of REQ-CHA-014 kept, and the sound server and `SpeechStreamer` removed or reduced to that one path
- Reason: merging the paths means a backend playback pipeline (render ahead, serials, cancel, upload or direct publish) and probably an IF-204 v1 and a changed audio-route contract (A-132 option A); it risks the working voice for no gain the user can see now
- Effort: about 3 to 5 days (estimate of A-132, not measured), after its own Plan step
- Risk of the gap: two routes may diverge. Mitigation: both use `speech_text` and `render_voice`; the sound-server hand-over has its own check (TC-CHA-036)
- Owner: Stefan Reiterer
- Trigger: the Plan of an iteration that changes the voice, or 2026-12-31, whichever first
- Target check: specified only
- Decision: confirmed by Stefan Reiterer, 2026-11-07 (D-278)
- Status: open

## TD-62 – The unit test without Tailscale runs the real `tailscale up` on a host that has it
- Kind: defer
- Requirement: NFR-6, CON-5 (test of `ui/tools/remote.sh`, `tests/test_tailscale.py`)
- Interim criterion: the other tests of `tests/test_tailscale.py` pass with a fake `tailscale`; on a host without Tailscale the test `ScriptTest.test_without_tailscale_it_says_how_to_install` passes; the stage `unit` is red on this host for that one test (the merge gate of TD-11 ran locally with this deviation)
- Target: the lookup of `tailscale` in that test ignores the host's `PATH`, so the test gives the same result on every host; the stage `unit` is green here
- Reason: `/usr/bin/tailscale` is installed on the workstation, so the test runs the real `tailscale up` and times out after 30 s; neither `remote.sh` nor the test changed in TD-11; the owner defers the fix to a later goal (2026-11-08)
- Effort: about an hour (proposed), test first
- Risk of the gap: the stage `unit` stays red on this host and hides a real failure; mitigation: the single red test is known by name
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration, or 2026-12-31, whichever first
- Target check: `tests/test_tailscale.py::ScriptTest::test_without_tailscale_it_says_how_to_install` (exists, red on a host with Tailscale)
- Decision: D-289, 2026-11-08, Stefan Reiterer
- Sign-off: maldun, 2026-11-08
- Status: open
