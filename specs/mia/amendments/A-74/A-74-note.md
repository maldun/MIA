# A-74: the Chat and login views N-1.1 are integrated (N-1 step 3)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent). Decision: D-176.

## Why
N-1.1 is Verified with accepted deviations; `tests/integration/N-1/step_03` skips ("N-1.1 not integrated yet"). The scenario replaces its stand-in page by the real page only through `p.page`, and the real page does not fit the scenario as written (see below). The owner chose (D-176) to leave the scenario alone.

## What changes (built from the installed file; A-72 and A-73 must be installed)
| File | Change |
|---|---|
| `tests/helpers/integration.mjs` | `READY` gets `N-1.1` |

Refused when the `READY` line is not found exactly once; a second run says "nothing to do". `N-1` itself is not added: only the root steps N-0/step_02 and later need it, and they come last.

## What step 03 shows, and what it does not
- Step 03 runs (it skipped) with the stand-in page and the mocks of IF-111 and IF-112, so it checks what steps 01 and 02 check. **No coverage is added by the step.**
- The real page is evidenced by its own tests (`tests/js`: chat-page, page-wiring, sound/voice-player with `initSound`, character, logout, no-outside-requests, 184 pass), and the stage 2 and 3 browser checks the scenario leaves to those stages.
- Why the real page is not in the scenario: (1) the scenario scripts `audio_chunk {id, url, index, sentence}`, but IF-101 v15 gives `audio_chunk` no `url`, and the page plays `audio_reload {url, serial}`; (2) `initSound` builds its own player, so the page cannot share the one voice port the scenario drives. A scenario amendment would fix both; it is not part of A-74.

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n1c`: the four N-1 steps run, 4 pass, none skip; `tests/js` and all JS contract suites 184 pass, 0 fail; `run_integration_steps.py` 23 python and 4 javascript steps, 0 failed; `check_sysml_model` OK; trace_check 91 error lines, as without A-74; second run "nothing to do".
