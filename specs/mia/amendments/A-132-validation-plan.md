# Validation plan: TD-11 option B, speak again (DRAFT of 2026-11-08, not run)

Phase 7 for a change set, not a goal: no `goal.md`, no Phases table. Prepared by the coding agent; people judge. Frozen version: master at `426da2b` or later as run on the host (deployment record: `A-132-deployment-record.md`, Phase 6 empty). No code change during the validation; a fix is a new change set.

## What is judged
Did "Speak again" become something the owner would use: heard when pressed, in order, stoppable, no surprises next to a running answer. Outcome of the change: a spoken-again message is heard (D-276).

## Validators and data
The owner on the host (Firefox; the audio device is written down this time, which the hand check lacked). Trusted users only if the owner invites them. No personal data beyond the chat itself; nothing is recorded; notes stay local.

## Criteria
`test-spec.md` has no VAL id for this change. **Name clash:** A-136 and `plausibility.yaml` call the 3 s follow-up "VAL-006", but VAL-006 in `test-spec.md` is the G-V1 criterion "fast and light enough in daily use". Proposal: keep the 3 s as an item of that VAL-006 session (it is a daily-use timing) and say so in the report; or give it a new id, the owner decides.

| ID | Criterion | Rating by |
|---|---|---|
| TD11-V1 | pressing the speaker button under old messages of different length is heard within a few seconds, every time | owner |
| TD11-V2 | a long answer spoken again has no choppy gaps and the sentences are in order | owner |
| TD11-V3 | Stop ends it at once; "speak again" right after a Stop is heard, not swallowed (the 3 s window, REQ-VPB-006: is 3 s too long or too short?) | owner |
| TD11-V4 | pressing it while an answer is being written: status and Stop button look right, the status returns afterwards | owner |
| TD11-V5 | exploratory: what feels wrong or missing around the voice | owner |

Provisional values in scope: the 3 s of REQ-VPB-006 (`STOP_DROP_MS`, accepted risk A-136). Settle it as confirmed, revised (a feedback item with the new value) or still open with a reason. Assumptions: none recorded for this change.

## Tasks (goals, not click instructions)
1. Use MIA for real chat for a few days; whenever you want to hear an older message again, use the speaker button.
2. Have it read a long answer again, and a very short one.
3. Stop a reading and start another one at once, a few times, also within 3 s.
4. Press the speaker button while MIA is still answering.
5. Exploratory: write down anything odd.

## Observation notes (to fill, one line each)
Date, browser, audio device, message length, what happened, what you expected. Use a table in the report; counts and quotes, no p-values.

## Open deferrals reviewed
- TD-61 (two voice paths): the interim criterion still serves; the validation shows whether divergence or rendering ahead matters in use. Decide at the trigger (next voice iteration or 2026-12-31): schedule or extend.
- TD-62: unrelated to use; trigger unchanged.
- Known limitation F4 (no rate limit on speak again): watch for runaway queues.

## Quality in use
Effectiveness (is it heard), efficiency (delay to first sound), satisfaction (owner's line), freedom from risk (no stuck status), context coverage: **not covered:** other browsers and the phone, other audio devices, several users at once.

## Triage
Every finding gets a type, priority and destination as in `validate-phase` step 4; files go to `specs/mia/feedback/` (next free id FB-07). A defect gets a failing test first. The report is `specs/mia/amendments/A-132-validation-report.md` (template `validate-phase/assets/validation-report.md`), written after the sessions.
