# A-72: the Voice playback N-1.3 is integrated (N-1 step 1)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-1.3 is Verified with accepted deviations. `tests/integration/N-1/step_01` skips ("N-1.3 not integrated yet") and the real side of the IF-112 contract suite (5 tests) skips, because `tests/helpers/integration.mjs` has an empty `READY`, has no real adapter, and `contract.mjs` still holds the skip reason. Pattern: A-02, A-55.

## What changes
| Protected file | How | Change |
|---|---|---|
| `tests/helpers/real/if_112_voice_player.mjs` (new) | copied from `specs/mia/contract-drafts/tests/helpers/real/` | `RealVoicePlayer`: the `VoicePlayer` of `templates/static/chat/sound.js` on an audio element that answers at once, plus the test adapter of the mock (`tick()` ends the playing line, `played`, `blocked`). It plays no sound. |
| `tests/helpers/integration.mjs` | built from the installed file | `READY` gets `N-1.3`; `realSubject('IF-112')` returns `RealVoicePlayer`; the later N-1 steps add their own lines |
| `tests/helpers/contract.mjs` | built from the installed file | the `IF-112` skip reason goes |
| `tests/acceptance/contract/test_if_112_voice_player.test.mjs` | built from the installed file | `make('real')` returns `RealVoicePlayer` instead of `null` |

Every edit is refused when its anchor is not found exactly once; a second run says "nothing to do".

## What the step then shows, and what it does not
- Contract suite IF-112: 10 of 10 (5 mock, 5 real).
- Step 01: the scenario runs with the real player and the character as mock; the page is the stand-in page of the scenario.
- A mutant (`tick()` does nothing) makes step 01 fail, so the step looks at the real player.
- Not shown here (stage 2/3, as the scenario says): a real `<audio>` element, autoplay policy of a browser, the `audio_reload` / `audio_ended` socket events (`initSound`, tested by `tests/js/voice-player.test.mjs`). The events `audio_chunk` and `expression` of an answer are not built (TD-11, D-173): the scenario scripts them.

## Checked on a scratch copy (not installed)
`git archive` of `v1-int-n1` with `bash tools/apply_amendment_a72.sh --do`: IF-112 suite 10/10, step_01 ok (steps 02, 03 still skip), `node --test tests/js` and all JS contract suites 184 pass, 0 fail; `tools/run_integration_steps.py` 23 python and 4 javascript steps, 0 failed; `check_sysml_model` OK; trace_check 91 error lines, the same as without A-72 (baseline unchanged).
