# A-158: change of IF-101 (chat API), for the owner to apply to `contracts/IF-101-chat-api.md` (and IF-201 if the turn carries it)

New server-to-client socket event `chat_run_status` (approved by the owner 2026-11-17 as the way to update the live line; a transient event instead of an update of a stored message, because the line is not in the log):

- Payload `{"run": <skill run id>, "text": <string>}`; `text` is the phase name of the manifest, `working`, or `waiting for your answer` (REQ-CHA-068, 070).
- Payload `{"run": <skill run id>, "text": null}` clears the line (REQ-CHA-069); it is sent before the end message.
- Not a chat message: no id, not in the log, not in the history, not spoken. A client that does not know the event ignores it (the chat then looks as after A-156).
- After a reload the line is not restored; the run strip of the Skill run view shows the state (REQ-CLV-038).

Mock: `tests/helpers/mocks/if_201_chat_turn.py` and the stub server emit the event for the scripted skill (protected files, to be changed with the red tests).

## IF-201 v4 (same amendment): two new turn kinds of `skill_turn`
- `start` (payload ignored): the run begins; for a run **without declared phases** the chat agent sends the line `working`, for a run with phases it sends nothing yet (the first declared phase gives the first line).
- `answered` (payload: the answer text): the answer of a question reached the run; the chat agent sends the line of the current phase again, or `working` if the run has none.
- `question` additionally sends the line `waiting for your answer` after the question message; `done`, `failed` and `stopped` send the clearing line (`text: null`) before the end message; `phase` of a declared, changed phase sends the line with the phase name and still returns `{"id": null}`.
- The mock `tests/helpers/mocks/if_201_chat_turn.py` and the contract suite get TC-IF-201-13 to -15 with the contract change (owner applies, protected).

## Open until the code exists
- Browser/JS check TC-CLV-053 (REQ-CLV-053, 054) has no test yet: it needs the page wiring of the event (a pure function of the chat model for the line, or the stub server scripted to emit it). Decide with the code design in the first task.
