# A-153: the paperwork findings F-12 and F-14 of the Verify of G-V3.CHAT (no requirement text changes)

Status: **F-12 and F-14 are to be fixed with these patches (owner's decision D-339, 2026-11-15)**; the owner installs them (protected files). The deviations that the owner accepts in D-339 are F-33, F-34 and F-35 (TD-85), not F-12 and F-14 (TC-CHA-008 decision by questionnaire: use the existing deferral TD-10).

## F-12: the protected contract tests lack `Example:` lines and Given/When/Then comments
`amendment-a153/f12-contract-comments.patch` changes only comments and docstrings of `tests/acceptance/contract/test_if_201_chat_turn.py` (TC-IF-201-01 to 12): the code of the tests is identical (compared as syntax trees with the docstrings removed); `test_doc_check.py` reports 0 errors and 0 warnings for the file with the patch.

## F-14: six checks in scope without scenario or test requirement
`amendment-a153/f14-scenarios-and-test-requirements.patch`:
| Check | Change |
|---|---|
| TC-CHA-008 | scenario of the **interim check of TD-10** (`tests/test_persona_prompt.py`); the statistical check of AC-8 stays deferred by TD-10 (REQ-CHA-008 is already `Relaxed: TD-10`, D-173); the persona of the status and end messages is decided by REQ-CHA-054 |
| TC-CHA-014 | scenario: the suite `behaviour` (67 texts, 32 clean) and the silent repair |
| TC-WFM-036 | scenario: the result of a task that asks is the newest message; a failed task leaves a message with the reason and the link |
| TC-IF-201-01 to 04 | new TR-CHAT-010 (setup kind, group Fakes (CHAT)): the contract cases run on the mock and on the real part |
| TC-CHA-008, 014, TC-WFM-036 | new TR-CHAT-011 (unit kind, new group Exact values (CHAT)), signed off as a group |
Effect on `trace_check` (checked on a copy of `specs/`): 538 errors become 528, none left for these checks. The two files `test-spec.md` of N-2.2 and N-2.3 are not protected; `test-requirements.md` is.

## Deferral (F-33 and F-35, not part of this amendment)
`amendment-a153/td85-deferred.patch` adds TD-85 to `deferred.md` (protected; with `Sign-off: maldun, 2026-11-15`): the fixes of F-33, F-34 and F-35 are not re-checked by a reviewer; the decision row D-339 is in `review-log.md`.

## Install
`git apply` of both patches, then `git add` of the four paths and one commit (the command is in the reply of the session).
