# A-158: change of IF-101 (chat API), for the owner to apply to `contracts/IF-101-chat-api.md` (and IF-201 if the turn carries it)

New server-to-client socket event `chat_run_status` (approved by the owner 2026-11-17 as the way to update the live line; a transient event instead of an update of a stored message, because the line is not in the log):

- Payload `{"run": <skill run id>, "text": <string>}`; `text` is the phase name of the manifest, `working`, or `waiting for your answer` (REQ-CHA-068, 070).
- Payload `{"run": <skill run id>, "text": null}` clears the line (REQ-CHA-069); it is sent before the end message.
- Not a chat message: no id, not in the log, not in the history, not spoken. A client that does not know the event ignores it (the chat then looks as after A-156).
- After a reload the line is not restored; the run strip of the Skill run view shows the state (REQ-CLV-038).

Mock: `tests/helpers/mocks/if_201_chat_turn.py` and the stub server emit the event for the scripted skill (protected files, to be changed with the red tests).
