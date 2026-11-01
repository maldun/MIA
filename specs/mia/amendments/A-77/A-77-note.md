# A-77: the Voice synthesis N-2.5 is integrated (N-2 step 1)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-2.5 is Verified with accepted deviations. `tests/integration/N-2/step_01` skips ("N-2.5 not integrated yet") because `tests/helpers/integration.py` does not list it in `READY`. Its real provider of IF-204 (`SpeechService` behind a fake speaker that writes a short silent wav) is in `tests/helpers/contract.py` since A-13, so only `READY` changes. Pattern: A-55.

## What changes (built from the installed file; A-76 must be installed)
| File | Change |
|---|---|
| `tests/helpers/integration.py` | `READY` gets `N-2.5`; the comment names A-77 |

Refused when the `READY` line is not found exactly once; a second run says "nothing to do".

## What step 01 shows, and what it does not
- Step 01 runs (it skipped): the scenario's speech part (`synthesize` strips markup, a missing voice line gives `no_line`) now runs on the real `SpeechService`; the library, chat turn, run and API parts stay mocks.
- IF-204 is not wired into the chat (TD-11, D-173): the app speaks through `SpeechStreamer`. The step shows the provider, not the live path.
- Not shown: real TTS (the speaker is a fake), the `audio_chunk` event of an answer (not built, TD-11).
- Steps 02 to 05 of N-2 still skip.

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n2a`: N-2 step_00 and step_01 OK; the IF-204 contract suite OK (6, mock and real); N-2.5's tests in the image OK: test_speech_service, test_speech_text, test_speech_repair, test_speech_stop, test_voice_lines, test_make_voice_lines, test_voice_effects, test_workflow_voice; `run_integration_steps.py` 23 python and 4 javascript steps, 0 failed; `check_sysml_model` OK; trace_check 91 error lines, as without A-77; second run "nothing to do".
