# Interface note: the digest step and the skill turns of the Chat agent (proposal for Plan Step 4, G-V3.CHAT)

Status: **proposed** (the owner approves or changes it before any test of TC-CHA-040 to 063 is written). Drafted 2026-11-08. Inside the node N-2.2 (no other node calls it), except `skill_turn`, which is the operation of IF-201 v3 (contract installed). It fixes the names the red tests use; a change after approval is a plan amendment.

## Why
TC-CHA-040 to 063 test behaviour of a step (`SkillDigestStep`, REQ-CHA-048 to 054, 061 to 063) and of the chat service around it (REQ-CHA-040 to 047, 055 to 060). The step has no code; `ChatService` has no `skill_turn`, no declared phases and no filtered history for the chat model (that history lives in `communicator.py`, outside the service).

## Proposal
### 1. `skill_digest.py`: `SkillDigestStep(model, persona="", input_tokens=4096, count_tokens=None)`
- `model(messages) -> str`: one call of the pinned model; `messages` is a list of `{"role": "system" | "user", "content": str}`. In the checks it is the fake model of TR-CHAT-006.
- `count_tokens(text) -> int`: default `max(1, len(text) // 4)`; the checks use the same function for their own count.
- Attributes: `tools` (a tuple, empty: REQ-CHA-048, TC-CHA-048) and `prompt` (the system prompt text; it names `1200 characters`: REQ-CHA-052, TC-CHA-052; it never contains text of a result: REQ-CHA-061).
- `status(phase) -> str`, `failure(reason) -> str`, `stopped(reason) -> str`: one model call each; the reason or phase goes in the `user` role; the text the model returns is returned unchanged.
- `summary(full_result) -> str`: a result that fits `input_tokens` (the whole call, prompt included) is one call; a longer one is cut into consecutive pieces in order, each piece digested by one call (`user` role), then one last call gets only the digests (REQ-CHA-050, 051, 061, 062); the text of the last call is returned uncut, whatever its length (REQ-CHA-063).

### 2. `ChatService` gets three additions
| Addition | Does | Requirement |
|---|---|---|
| constructor arguments `digest=None`, `declared_phases=None` | `digest` is a `SkillDigestStep` (or anything with its four methods); `declared_phases(run) -> tuple of phase names` | REQ-CHA-041, 042, 055 |
| `skill_turn(account, run, kind, payload)` | exactly the operation of IF-201 v3: kinds `question`, `phase`, `done`, `failed`, `stopped`; wording by `digest`; the link ` [Open in the Skill run view](#run=<run>)` added by code at the end of `done`, `failed`, `stopped` (a link in the model text is not taken as the link, it is cut off); the existing `repair` is applied to every text before it is shown, spoken and stored; every message is spoken through the existing `speak` once; returns `{"id"}` or `{"id": None}` | REQ-CHA-040 to 045, 047, 055 to 060, 063 |
| `model_history()` | the list of messages the next chat turn sends to the chat model, `[{"role": "user" | "assistant", "text": str}]`, in order; for a skill run: its questions, the users' answers, the end summary and the last status message, no other status message, never the full result | REQ-CHA-046, 059 |

Violations of the behaviour rules in a skill text are recorded as signals through the existing mechanism of `repair` (the check counts the calls of a recording `repair` that returns the repaired text and a list of four violations in the scripted cases).

### 3. Fake model: `tests/helpers/fake_model.py` (protected, TR-CHAT-006)
`FakeModel(replies)` is the `model` callable: `replies` is a list (next reply per call), a dict `{role-of-the-last-user-text-substring: reply}` or a function `messages -> str`; it records every call (`.calls`, each the list of messages, with the size from `count_tokens`) and is no evidence for any eval criterion (TR-CHAT-006).

## Open questions (with my proposal)
1. **`model_history()` as a new method of `ChatService`** or as a function in `communicator.py` (where the conversation memory is built today)? Proposal: the method on the service, which the Communicator will call in Implement; `communicator.py` stays out of Step 4.
2. **Signals:** a recording `repair` is enough for TC-CHA-047 and TC-CHA-060 (four violations counted, text repaired once). The run-log line per violation stays the job of `behaviour.record_signals`, checked by its own tests. Proposal: keep it that way, no new constructor argument.
3. **`declared_phases` as a callable per run** (from the manifest of the skill, REQ-WFM-039) is enough for TC-CHA-041, 042, 055; the manifest itself is not read by the chat agent in these checks.

## Stub for Step 4
`skill_digest.py` is created with the class but without the attributes `tools` and `prompt` (so that TC-CHA-048 and 052 are red); the four methods raise `NotImplementedError`. `ChatService.skill_turn` and `model_history` are added as stubs raising `NotImplementedError` (a new method on an existing class, no other change); the two constructor arguments are accepted and kept.
