# A-150: markup in the output of SkillDigestStep is removed by code (G-V3.CHAT, REQ-CHA-064)

Status: **approved** (2026-11-15, maldun, questionnaire). Owner choice by questionnaire, 2026-11-15: "code-side repair" for REQ-CHA-049 / `st-rt-d5`. Until approved, REQ-CHA-049 keeps its approved text and the new requirement stays Draft.

## Why
T-05 (prompt versions 1 to 4, all re-runs used): `st-rt-d5` (a table row whose work name is `<script>alert(1)</script>`) comes back with the tag in versions 1 and 4. Each prompt fix moved another case. A prompt cannot make the 12B model reliably leave a name out. The text reaches the chat page and speech, so a tag in it is a defect whatever the model does (THR-012, TB-result).

## Change
| Item | Change |
|---|---|
| New requirement REQ-CHA-064 (group UT, Parent REQ-BE-078, Must, Test) | "When SkillDigestStep returns a text, the Chat agent shall remove every HTML tag from it before the text is repaired or shown." |
| Acceptance criterion | AC-39: a scripted reply `Done: <script>alert(1)</script> and <b>x</b>` leaves `Done: alert(1) and x`; text without `<`...`>` pairs, and a lone `<` or `>` (e.g. "5 < 6"), is unchanged (exact) |
| Place | `skill_digest.py`, one function applied to every return value of `status`, `summary`, `failure`, `stopped` (so the eval target `digest` sees the same text as the chat). Not in `behaviour.py` (answers of /lookup carry quotes and are never changed, REQ-CHA-014) |
| New check TC-CHA-069 (Component, stage 1, fake model, exact) | scenario in `N-2.2-chat-agent/test-spec.md`; test in `tests/acceptance/` (protected: written outside the implementing session, installed by the owner) |
| Test requirement | TC-CHA-069 added to `Applies to:` of TR-CHAT-006 (fake model server) |
| Plausibility | REQ-CHA-064 rated by the owner (no number or model quality; exact criterion on a scripted run) |
| REQ-CHA-049 | text unchanged; the criterion is now met for markup by code. `st-rt-d2` (instruction described in words) stays as the owner labelled it. Eval re-run: **not one of the three used** (the prompt does not change); it is one new run after the code change, decided by the owner |
| Other files | `goal.md` scope row, architecture.sysml requirement def (+ `docs` of the step), `requirements.md` group UT, `review-log.md` row, `plan.md` T-05b task, `implementation-log.md` (A-150) |
| Step version | `skill_digest.py` version bumped (agent-app rule: every change of the step) |

## Not changed
No new tool, permission, model or interface. Prompt version 4 stays. Holdout untouched.

## Open for the owner
1. Approve REQ-CHA-064 as worded (tags only; the text inside `<script>` stays as plain `alert(1)`, which is harmless as text).
2. Allow one dev re-run of `skill_turns` after the code change (feedback run).
