# A-158 (decided by the owner 2026-11-17, not yet applied; DRAFT text, 2026-11-17): the chat shows a skill run like a chatbot does: what to answer, what happens now, the summary

Source: owner answer of 2026-11-17 to the open point of A-156 ("where the status card shows phases"). Number: A-157 is the G-V3.REPORT renumbering on `origin/goal/v3.report`; check against the parent's range before applying.

## Owner's words (2026-11-17)
The card is superseded by the skill view. The chat tells what to answer, what currently happens, and the summary. The card may stay as a stub if that is easier. The chat should behave like common chatbot apps: the current state is shown last, not a card above the changes, and the result is shown.

## Finding
The task card (`task-card.js`) is already removed (G-V3.PANEL T-10); the Skill run strip and view replaced it. After A-156 the chat has no phase message at all, so while a run works the chat shows nothing between the user's command and the end message. This amendment fills that gap.

## Changes
1. **One live status line, last in the chat** (new, group ST, Must; supersedes the phase part of REQ-CHA-041): while a skill run works, the chat shows exactly one status message of the run, always the last message, with the current phase (and the run link). It is **updated in place** when the phase changes (not a new message per phase, so A-156's "noted once, no clutter" holds). Phases still come from the run status of REQ-CHA-041 (declared phases only; REQ-CHA-042 and 055 stay: no phase, no line).
2. **The line is replaced by the end message.** At done, failed or stopped the live line is removed (or becomes the end message) so the summary, failure reason or stop message is the last message (REQ-CHA-043, 044, 057 unchanged).
3. **A question comes after the line is moved down:** a question of the run (REQ-CHA-040) is a normal message; the live line stays last, below it (the question is the thing to answer, the line says that the run waits for the answer). While the run waits, the line reads that it waits.
4. **Not spoken, not in the model's history** (keeps A-156/REQ-CHA-067: the persona speaks once, at the end; REQ-CHA-045 gets the exception "the live status line is neither spoken nor part of the history for the chat model"; REQ-CHA-046/059 list it among the exclusions).
5. **No card.** The status card stays removed; Pause/Resume/Stop and the files stay in the Skill run view. The live line only links to it (REQ-CHA-056 style link).
6. **Code (after approval):** `skill_turn` sends a `status` message kind (not `phase`) and later updates it by id; a client-side rule keeps the line last (new messages are inserted above it). Needs a decision on the transport: update of a message by id (`chat_update` event) exists or is new (IF-1xx change, owner).

## Checks (red first, after approval)
- TC-CHA-041 changes again: a run with phases leaves one status message, updated per phase, last in the log; not spoken.
- New: after done/failed/stopped no live line remains and the end message is last; a question sits above the live line; the history for the model holds no live line.
- JS test of the chat model: the live line stays last when messages arrive.

## Decided by the owner (2026-11-17)
- A: the live line is **transient**: shown only while the run works, never stored in the chat log.
- B: a run without phases shows a **generic "working" line**; REQ-CHA-055 is relaxed accordingly.
- C: the wording is **fixed text from the manifest's phase names**, no model call.
- D: the interface change (update of a message by id, e.g. a `chat_update` event) is **approved**; it is planned as an IF change.

## Not done
Nothing is applied yet. Next: plan-phase (requirements, IF change, the six protected files, review-log line), then red tests, then code. Requirements, the six protected files, the plan and the review-log line come after the owner's decisions (plan-phase, then red tests, then code).

## Amended after the Verify run (2026-11-17, owner: "amend the requirements")
Source: `specs/mia/goals/G-V3.CHAT/verification-report-a158.md`, findings F-03, F-04, F-06.
- **New REQ-CHA-072** (TC-CHA-076): after a question ends by an answer or by a timeout the phase line comes again, or `working` for a run without a phase; after a stop no line is sent again (F-03, and the `answered` fallback of F-06).
- **REQ-CHA-069 clarified:** the clearing is sent whether or not a line was shown, so that a lost line cannot stay (F-06).
- **New REQ-CLV-055:** the two generic texts are shown in the language of the page (en, de), any other text of the line as it is (F-06).
- **F-04 (a reload during a run loses the line): "not now".** Decided with the transience of the line (2026-11-17, A-158 A): the line is not restored after a reload; the Skill run view shows the state (REQ-CLV-038). Recorded here as the accepted risk; to be confirmed by the owner in the review log. A later requirement could resend the line on connect.
- Protected: TC-CHA-076 is added to the `Applies to:` line of TR-CHAT-006 (patch `amendment-a158/protected-test-requirements-2.patch`, `apply-amend.sh`).

