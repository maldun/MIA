# A-79: the Chat agent N-2.2 is integrated (N-2 step 4)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-2.2 is Verified with accepted deviations; `tests/integration/N-2/step_04` skips ("N-2.2 not integrated yet"). Its real provider of IF-201 (`ChatService`) is in `tests/helpers/contract.py` since A-07, so only `READY` changes. Pattern: A-55, A-77, A-78.

**Step 03 (N-2.4) needs no amendment.** It needs N-2.5, N-2.3 and N-2.4; N-2.4 was listed by A-55, N-2.5 by A-77 and N-2.3 by A-78. It runs and passes on the installed goal/v1 (checked before this draft).

## What changes (built from the installed file; A-78 must be installed)
| File | Change |
|---|---|
| `tests/helpers/integration.py` | `READY` gets `N-2.2`; the comment names A-79 |

Refused when the `READY` line is not found exactly once; a second run says "nothing to do".

## What step 04 shows, and what it does not
- Step 04 runs (it skipped): the chat-turn part of the scenario (a message from anna reaches the stream with its sender, the history keeps the roles, an empty text is refused with `empty_text`) runs on the real `ChatService`, with speech, library, runner (IF-202, IF-105) and the log doors real from the earlier steps; the API and graph API (N-2.1) stay mocks.
- The events `audio_chunk` and `expression` of an answer are not built (TD-11, D-173): the IF-201 suite keeps 1 skip (15 pass of 16 with the mock).
- Not shown: the model-dependent behaviour of the chat agent (eval suites on the pinned model).
- Step 05 (N-2.1) still skips.

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n2c`: N-2 steps 00, 01, 03, 04 OK; the IF-201 suite OK (16 cases, 1 skip); the node's tests (`test_chat_backend`, `test_converse_behaviours`, `test_memory_records`) and the 16 other `tests/test_chat*.py` files OK in the image (`test_chat_views_browser` skips 1: no browser); `run_integration_steps.py` 23 python and 4 javascript steps, 0 failed; `check_sysml_model` OK; trace_check 91 error lines, as without A-79; second run "nothing to do".
