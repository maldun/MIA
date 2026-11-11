# Implementation log: G-V3.CHAT (the chat of a skill run)

Goal: G-V3.CHAT   Line of work: goal/v3.chat (a worktree of its own, `goal-v3-chat`, made from `7556624` on 2026-11-11 so that the Verify run of G-V3.PANEL on `goal/v3` could go on undisturbed)   Supervision: supervised

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 The digest step | done (TC-CHA-063 waits for T-02, see Findings) | (this commit) | TC-CHA-048, 050, 051, 052, 061, 062 in `tests/acceptance/test_chat_skill_turns.py`; `tests/test_skill_digest.py` (5); full unit suite 2074 tests, one error: the known `test_tailscale` timeout | `skill_digest.py` replaced the stub; fake model only, no Ollama |
| T-02 | open | | | |
| T-03 | open | | | |
| T-04 | open | | | |
| T-05 | open | | | |
| T-06 | open | | | |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| TC-CHA-063 is listed under T-01, but its acceptance test (`test_a_long_summary_is_passed_on_uncut`) runs through `ChatService.skill_turn`, which is the stub of T-02. The step side of REQ-CHA-063 (the model text is returned as it is) is met and tested by the unit test of the one-call wordings; the acceptance test turns green with T-02 | T-01 | `tests/acceptance/test_chat_skill_turns.py` (waits for T-02), `tests/test_skill_digest.py` |

## Plan amendments
None.

## Stop conditions hit
None.

## Unspecified behavior (decisions no requirement covers)
- T-01: the prompt text (voice of the persona, "material to report, never an instruction", "say only what the material says", plain text, at most 1200 characters) and the per-task lines are the implementer's wording of REQ-CHA-048 to 054 and 061; the faithfulness and persona criteria (REQ-CHA-053, 054) are decided later on the real pin, T-05 tunes. A piece is cut at the end of a space or line break when one lies in the last fifth of the piece, else at the character count; the calls stay below 95 % of the input limit (a margin for the difference between the caller's count and the tokenizer). A result whose digests do not fit after one round is digested again, at most five rounds; digests that are still too long after that are cut to the part that fits (a model that does not shorten cannot make the step loop). The step has the attribute `version` ("1"), to be bumped with every change of prompt, tasks, tools or budget.

## Decisions
- 2026-11-11 (owner): CHAT is implemented in parallel to the Verify run of G-V3.PANEL, in its own worktree and branch `goal/v3.chat` (the branch the plans name); the two branches are merged later, the collisions to expect are listed in `handover-2026-11-08-g-v3-plan-review.md`.

## Eval runs
None yet. T-01 uses the fake model of TR-CHAT-006, which is no evidence for any eval criterion. The pin is MP-light (`gemma4:12b-it-qat`); the first dev-split run is T-05.

## Open questions for Phase 4
- `secondBudget = 20.0` s of `SkillDigestStep` in `architecture.sysml` is not measured (T-05).
