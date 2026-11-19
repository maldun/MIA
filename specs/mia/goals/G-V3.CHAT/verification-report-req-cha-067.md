# Verification report REQ-CHA-067 (a run is spoken once, by the persona; A-156) — 2026-11-19

Reviewer read the requirement, the code and the tests, not the chat. Scratch worktree from `master` `ab8e8f4f`.

## Result: Verified, with two test gaps found and closed
- Code: `workflow_voice.speaker_for(..., end_messages=True)` gives no voice whatever the settings say; `ChatService.has_end_messages()` is true only with recorder and digest step; `web_app.py` passes it to the tasks (`services.speaker`), and `lookup` and `review` ask it at run time (`extensions/*/entry.py`), so the lazy wiring holds.
- Checks: TC-CHA-072 (`tests/acceptance/test_chat_skill_turns.py`, `OneVoice`) pass; `tests/test_chat_verify_fixes.py` `RunSpeaksOnce` (service flag; a run through the chat is spoken once, "All done." only) and `tests/test_workflow_voice.py` pass.

## Mutations
| Mutation | Caught by |
|---|---|
| M1 `speaker_for` ignores the flag | TC-CHA-072 and unit tests |
| M2 `has_end_messages` always False | unit tests |
| M5 flag ignored when the task has its own setting | TC-CHA-072 |
| M3 `has_end_messages` needs the recorder only | **survived** (F-01) |
| M4 `web_app.py` drops `end_messages=` | **survived** (F-02; known gap in the implementation log) |

## Findings (both low, fixed by tests in `tests/test_chat_verify_fixes.py`, no protected file touched)
- F-01: nothing checked that a recorder without a digest step leaves the voice to the skill (otherwise the run would be silent). New test `test_a_recorder_without_a_digest_step_leaves_the_voice_to_the_skill`; fails under M3.
- F-02: the wiring in `web_app.py` had no test. New source test `test_the_voice_rule_of_the_tasks_asks_the_service_for_end_messages` (AST, as the existing wiring test); fails under M4.
- Not covered: spoken output of a real run with the voice server (hand check by the owner on 2026-11-18 heard the run once).
