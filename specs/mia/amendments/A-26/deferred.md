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
- Trigger: a browser test harness exists for N-1, or 2026-12-31, whichever first
- Target check: specified only
- Decision: proposed 2026-10-29, to be confirmed by Stefan Reiterer
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
- Trigger: a browser test harness exists for N-1, or 2026-12-31, whichever first
- Target check: specified only
- Decision: proposed 2026-10-29, to be confirmed by Stefan Reiterer
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
- Decision: proposed 2026-10-29, to be confirmed by Stefan Reiterer
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
- Decision: proposed 2026-10-29, to be confirmed by Stefan Reiterer
- Status: open
