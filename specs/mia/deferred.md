# Deferrals: MIA

Compromises we chose on purpose (blueprint M26). People decide; agents propose with effort and risk and never weaken a check.
Check with `trace_check.py` (records, `Relaxed`/`Target` links, `deferred` markers, TODO references, trigger dates).

Proposed on 2026-10-29 after the usability work of N-2.3 T-09 to T-11 and N-1.1 T-09 (A-23, A-24, D-101, D-103). Every record below is a proposal: the owner confirms, changes or drops it
(the line `Decision` names the person who has to decide).

## TD-01 – The status card is not tested in a browser and is gone after a reload
- Kind: defer
- Requirement: REQ-CLV-023
- Interim criterion: the model of the card (figures, state, a late status after done) is tested with `node --test` (`tests/js/taskcard.test.mjs`); the drawing, the buttons and the placement in the chat are looked at by the owner (hand test); the card lives as long as the page is open
- Target: a browser test that draws the card from a `task_status` of the mock, updates it in place, presses pause, resume and stop, and a card that is still there, with its final figures, after a reload
- Reason: the repository has no browser test harness for the page yet (no DOM library in `tests/js`); a card after a reload needs the status to be kept with the history, which is a change of the interface (IF-101)
- Effort: about 1 day for the harness, half a day for the kept card (a field in the history record and in the amendment of IF-101)
- Risk of the gap: a broken layout or a dead button is found only by a person; on a phone the card may be too wide. Mitigation: the hand test list in `handover-review-workflow.md` and the owner's look before the release
- Owner: Stefan Reiterer
- Trigger: the chat mock server sends `task_status` and files events, or the Plan of FB-01, or 2026-12-31, whichever first (the browser harness exists since D-141; D-172)
- Target check: specified only
- Decision: confirmed by Stefan Reiterer, 2026-11-01 (D-172)
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
- Status: open

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
- Trigger: the first eval target with a judge
- Target check: TC-EVL-003
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
- Target check: TC-EVL-011
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
- Interim criterion: the app speaks through `SpeechStreamer` and `Speaker.render_voice` with the `speech_text` filter; `SpeechService` passes the IF-204 contract suite and TC-VOI-001 to -003
- Target: the chat agent's audio goes through `SpeechService`, the `audio_chunk` event of an answer is built, and the skipped cases of IF-201 and IF-101 and the integration step 1 of N-2 run green
- Reason: the older route works on the host; changing it risks the working voice for no gain to the user now
- Effort: about one day
- Risk of the gap: two routes may diverge. Mitigation: both use `speech_text` and `render_voice`
- Owner: Stefan Reiterer
- Trigger: the Plan of the next iteration, or 2026-12-31, whichever first
- Target check: skip: the IF-204 side of the chat is not wired (TD-11); the skipped cases carry deferred('TD-11') until green
- Decision: D-173, 2026-11-01, Stefan Reiterer
- Status: open
