# A-142: IF-201 v3, skill turns in the chat and in the history (proposal, owner G-V3.CHAT)

Status: **proposed** (Draft, Plan step 1b of G-V3.CHAT, 2026-11-08). `contracts/IF-201-chat-turn.md` (v2), its mock and its contract suite are not changed; they change together after approval (suite red first). Part of A-131 (approved, D-302). G-V3.PANEL provides IF-101 v16 (A-140); CHAT uses a mock of it.

## Changes (v3)
| Item | Change |
|---|---|
| `skill_turn(account, run, kind, payload)` (new) | the Workflow management hands one turn of a skill run to the chat agent; `run` is the run id; `kind` is `question` (payload: the question text), `phase` (payload: the phase name; only phases the manifest declares worth telling), `done` (payload: the full result), `failed` or `stopped` (payload: the reason); returns `{"id"}` of the message, or `{"id": null}` when the turn adds no message (an undeclared phase) |
| messages of a skill | `history` and the events carry `skill_run: <run>` and `kind`; the text of `done`, `failed` and `stopped` ends with ` [Open in the Skill run view](#run=<run>)`, added by code (REQ-CHA-043, 044, 037 of the view) |
| history the chat model sees | per run the questions, the users' answers, the end summary and the last status message; no other status message (REQ-CHA-046); the full result is never in it |
| speech | each message of `skill_turn` is sent to speech with the repair of REQ-CHA-014, like an answer (REQ-CHA-047) |
| errors | an unknown `kind` is `ServiceError("invalid_kind")`; nothing is added |

## Requirements it serves
REQ-BE-078, REQ-CHA-040 to 047; the digest step behind `done`, `failed` and `stopped`: REQ-CHA-048 to 054.

## Open
The mock of IF-201 and its contract suite (`tests/helpers/mocks`, `tests/acceptance/contract`) change only after approval. The link form `#run=<id>` is shared with A-140 and REQ-CLV-037 (the page opens the Full run part of that run).
