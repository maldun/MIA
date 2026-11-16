# A-152: model of the digest step, links of the model, the 1200 characters, the time budget (G-V3.CHAT, Verify run 1: F-06, F-07, F-10, F-11)

Status: **approved** (2026-11-15, maldun, questionnaire, four answers).

## Changes
| Finding | Decision | Change |
|---|---|---|
| F-06 | pin the step to the light profile | new REQ-CHA-065 (group BG, TC-CHA-070): every call of `SkillDigestStep` asks for the profile `light`; code: `LiveDigest` in `skill_digest.py`, wired in `web_app.py` |
| F-07 | reword REQ-WFM-036 | "... one summary of its result, worded by the digest step that is asked to keep it to at most 1200 characters ..."; REQ-CHA-052 and 063 unchanged |
| F-10 | cut in every turn text | new REQ-CHA-066 (group UT, TC-CHA-071): a link to a run is removed from every message the step words; REQ-CHA-056 (link added by code at the end messages) unchanged; code: `_turn_text` |
| F-11 | measure first | spike 2026-11-15 on MP-light (`gemma4:12b-it-qat` sha256:38044be4f923, seed 7, temperature 0, num_ctx 8192): a result of 82 183 characters (about 20 000 tokens) took 7 calls, 5.5 to 12.9 s per call, 59.5 s in all. `secondBudget = 20.0` s stays and is the time of one call (the slowest was 65 % of it); the whole summary of a long result is not bounded by it. Recorded in the rationale of REQ-CHA-065. Not an eval run |

## Protected part
`amendment-a152/protected.patch` (also holds the A-150 rating of REQ-CHA-064 and the claims of REQ-CHA-052, 056, WFM-036 from the plausibility questionnaire): `plausibility.yaml` (rows REQ-CHA-064, 065, 066, claims, two references) and `test-requirements.md` (TR-CHAT-006 applies to TC-CHA-070 and 071). Applied by the owner. The checks TC-CHA-070 and 071 are unit tests in `tests/test_chat_verify_fixes.py`.

## Not changed
Prompt, tools, schema, pin, interfaces, holdout. Step `VERSION` stays 7 (the output of the step is unchanged).
