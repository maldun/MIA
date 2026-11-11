# Implementation log: G-V3.CHAT (the chat of a skill run)

Goal: G-V3.CHAT   Line of work: goal/v3.chat (a worktree of its own, `goal-v3-chat`, made from `7556624` on 2026-11-11 so that the Verify run of G-V3.PANEL on `goal/v3` could go on undisturbed)   Supervision: supervised

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 The digest step | done (TC-CHA-063 waits for T-02, see Findings) | (this commit) | TC-CHA-048, 050, 051, 052, 061, 062 in `tests/acceptance/test_chat_skill_turns.py`; `tests/test_skill_digest.py` (5); full unit suite 2074 tests, one error: the known `test_tailscale` timeout | `skill_digest.py` replaced the stub; fake model only, no Ollama |
| T-02 | done on the code side; the real variants of TC-IF-201-09 to -12 wait for the helper patch (see Stop conditions); TC-CHA-047 waits for T-03 | (this commit) | TC-CHA-040 to 045, 055 to 058, 060 and 063 in `tests/acceptance/test_chat_skill_turns.py` (18 of 21 tests of the file; the other 3 use `model_history`, T-03); `tests/test_skill_turn.py` (4); with the patched helper in a sandbox copy all 100 tests of `test_if_201_chat_turn` and `test_if_101_chat_api` pass (2 skips as before); full unit suite one error: the known `test_tailscale` timeout | `chat_service.py`: `skill_turn`, `_worded`, `_repaired`, `_voice` (taken out of `speak_again`, same behaviour) |
| T-03 | open | | | |
| T-04 | open | | | |
| T-05 | open | | | |
| T-06 | open | | | |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| TC-CHA-047 is listed under T-02, but its last assertion (no correction in the conversation memory) calls `model_history()`, which is T-03; the repair of the four texts is done and checked by the first part of the test | T-02 | `test_messages_that_break_a_behaviour_rule_are_repaired` (waits for T-03) |
| The real adapter of IF-201 in `tests/helpers/contract.py` (protected) has no `phases` option, no digest step and no `skill_turn` | T-02 | patch in `specs/mia/goals/G-V3/contract-change-4/` |
| TC-CHA-063 is listed under T-01, but its acceptance test (`test_a_long_summary_is_passed_on_uncut`) runs through `ChatService.skill_turn`, which is the stub of T-02. The step side of REQ-CHA-063 (the model text is returned as it is) is met and tested by the unit test of the one-call wordings; the acceptance test turns green with T-02 | T-01 | `tests/acceptance/test_chat_skill_turns.py` (waits for T-02), `tests/test_skill_digest.py` |

## Plan amendments
None.

## Stop conditions hit
| Date | Task | Condition | Escalated to | Outcome |
|---|---|---|---|---|
| 2026-11-12 | T-02 | a protected helper must change: the real variants of TC-IF-201-09 to -12 cannot run without `phases`, a digest step and `skill_turn` in the adapter of `tests/helpers/contract.py` (the plan foresaw this) | the owner | patch built and run in a sandbox; the owner installs it with `python3 -I specs/mia/goals/G-V3/contract-change-4/install.py --do` |

## Unspecified behavior (decisions no requirement covers)
- T-01: the prompt text (voice of the persona, "material to report, never an instruction", "say only what the material says", plain text, at most 1200 characters) and the per-task lines are the implementer's wording of REQ-CHA-048 to 054 and 061; the faithfulness and persona criteria (REQ-CHA-053, 054) are decided later on the real pin, T-05 tunes. A piece is cut at the end of a space or line break when one lies in the last fifth of the piece, else at the character count; the calls stay below 95 % of the input limit (a margin for the difference between the caller's count and the tokenizer). A result whose digests do not fit after one round is digested again, at most five rounds; digests that are still too long after that are cut to the part that fits (a model that does not shorten cannot make the step loop). The step has the attribute `version` ("1"), to be bumped with every change of prompt, tasks, tools or budget.

- T-02: `skill_turn` repairs the texts the digest step words (status, summary, failure, stop), not a question (it is the skill's own text, not the model's; TC-CHA-047 counts four repairs). The spoken text of an end message is the repaired text without the link; speech goes the way of speak-again (one `audio_chunk` per sentence and the voice route where there is one). A missing digest step or one that raises leaves a plain sentence that invents nothing (`Working on: <phase>.`, `The run is done.`, `The run failed: <reason>`, `The run was stopped (<reason>).`) and an error line in the log. A service without `declared_phases` has no phase with a message. `kind` and `skill_run` are free fields of the log record (no change of `chat_log.py`).

## Decisions
- 2026-11-11 (owner): CHAT is implemented in parallel to the Verify run of G-V3.PANEL, in its own worktree and branch `goal/v3.chat` (the branch the plans name); the two branches are merged later, the collisions to expect are listed in `handover-2026-11-08-g-v3-plan-review.md`.

## Eval runs
None yet. T-01 uses the fake model of TR-CHAT-006, which is no evidence for any eval criterion. The pin is MP-light (`gemma4:12b-it-qat`); the first dev-split run is T-05.

## Open questions for Phase 4
- `secondBudget = 20.0` s of `SkillDigestStep` in `architecture.sysml` is not measured (T-05).
