# A-156 (approved by the owner 2026-11-16): a skill run speaks once, in character, and keeps its status in the skill window

Source: FB-09, owner decision 2026-11-16 (persona summary stays; phase messages are not spoken) and addition of the same day (a status is noted once, never repeated; phase messages stay in the Skill run view and are not chat messages; only messages that need interaction are in the chat). The number is a proposal: the owner checks it against A-155 and the parent's range.

## Changes
1. **Phase messages leave the chat** (REQ-CHA-042, 055 and the phase part of REQ-CHA-040/041, to be named exactly by `trace_check`): the Chat agent shall not add a message of kind `phase`; the phases of a run are shown in the Skill run view and the status card only. Because no phase message is added, REQ-CHA-045 (every added message is spoken) needs no exception: phases are not spoken either. Rationale: phase texts are not in the persona's voice and clutter the chat (owner 2026-11-16).
1a. **A status is noted once** (new, group ST): the same status text of a run is shown once in a row; an unchanged phase is not noted again (also not in the Skill run view's list). Rationale: the owner heard and saw the same feedback repeatedly.
1b. **Only what needs interaction is in the chat:** questions of a run (REQ-CHA-040) and the end message of the persona (the summary that is spoken, decision 1 of FB-09) with its link to the run. See the open point below.
2. **New REQ-CHA-067** (group ST, Must): "While a skill run has a spoken `done`, `failed` or `stopped` message of the Chat agent, the skill itself shall not speak its own result." Rationale: the answer was heard twice, once from the skill (`run_research`, `speak=services.speaker(task)`) and once as the persona summary (FB-09).
3. **Code** (after approval): the chat service does not hand `phase` turns to `_voice`; for a task whose run has turns (`turns` in `_do_chat`) the skill gets no `speak` route (`services.speaker(task)` returns None), so the summary is the only voice. A task without turns (no digest step) keeps its own voice.

## Checks (red first, after approval)
- Phase checks (TC-CHA-042 and neighbours) change: a run with phases adds no `phase` message to the chat log, the Skill run view still lists the phases; a repeated identical phase is listed once. TC-CHA-045: question, done, failed, stopped are still spoken once.
- New TC-CHA-067: a `/lookup` run with a scripted model and a recording voice route: the recorded sentences are those of the summary only, none of the answer text. Setup requirement for the recording voice (fake fidelity) in `test-requirements.md`.
- Existing tests that expect a spoken phase turn change with it (to be listed by `trace_check`).

## Decided by the owner (2026-11-16)
- The end message of a run (done, failed, stopped, with its link to the run) stays in the chat and is the one spoken text of the run.
- The run report file is only in the Skill run view (D-340, A-154); the owner saw it there only.

## Still open (assumed)
- Where the status card shows phases: assumed unchanged.
- Is a `/review` question spoken? Assumed yes: a question is addressed to the person, in the persona's voice.

## Applied (2026-11-16, agent) and still to do by the owner
- Applied in `nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md`, status Draft: REQ-CHA-041 changed (phase noted in the run status, no chat message), new REQ-CHA-067, group ST lists it. REQ-CHA-042, 045, 055 stay as they are (no phase message, so nothing to exempt).
- Owner (protected or review): TC-CHA-041 changed and TC-CHA-067 new in `test-spec.md` with scenarios; test requirement for the recording voice route in `test-requirements.md`; `plausibility.yaml` record for REQ-CHA-067; protected acceptance tests `tests/acceptance/test_chat_skill_turns.py` (TC-CHA-041) and a new one for TC-CHA-067; a review-log line with a D-number from the parent's range.
- Code only after those exist (red first).
