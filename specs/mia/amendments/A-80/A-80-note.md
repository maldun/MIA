# A-80: the API and accounts N-2.1 and the node N-2 are integrated (N-2 step 5)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-2.1 is Verified with accepted deviations; `tests/integration/N-2/step_05` skips ("N-2.1 not integrated yet"). Its real providers of IF-101 (login, session, logout, the routes and the chat service) and IF-104 (the routes of `graph_api.py` behind the guard of `accounts_api`) are in `tests/helpers/contract.py` since A-05, A-07 and A-51, so only `READY` changes. With step 05 all five children of N-2 are done, so the node `N-2` is listed too (as A-55 did for N-2.4, A-76 for N-4). Pattern: A-55, A-79.

## What changes (built from the installed file; A-79 must be installed)
| File | Change |
|---|---|
| `tests/helpers/integration.py` | `READY` gets `N-2.1` and `N-2`; the comment names A-80 |

Refused when the `READY` line is not found exactly once; a second run says "nothing to do". `N-2` wakes no N-0 step: they all need `N-1`, which is not in this list (it is added with the root steps).

## What step 05 shows, and what it does not
- Step 05 runs (it skipped) with every part of the N-2 scenario real: the API (no session gives 401, a wrong password 401, the same session works for chat and graph API with the 422 `cycle` refusal), the chat turn, the library, the runner and the speech.
- The unbuilt events of an answer skip in the IF-101 suite (2 skips: `audio_chunk`/`expression` of TD-11, D-173, and REQ-CHV-008, out of G-V1).
- **Needs flask.** The real IF-101 adapter imports flask, so step 05 fails on a python without it: `python3 -I tools/run_integration_steps.py` on this host (no flask) reports 1 failed (`ModuleNotFoundError: flask`), as the IF-101 and IF-104 real suites do. In the image, and in the venv of `requirements.txt` that the stage `integration` needs, it passes. The script of A-80 therefore runs the N-2 steps with `tools/run_in_image.sh`. No change to `stages.yaml` or the runner.
- Not shown: the stack on the host (stage 3).

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n2d`: N-2 steps 00, 01, 03, 04, 05 OK in the image; every other Python integration step in the image OK (9 OK, 4 with the skips of the later N-0 and N-1/N-2 cases, none failed); IF-101 suite 64 tests (2 skips), IF-104 suite 10, both with the real side, OK; the node's 14 test files OK in the image (`test_container_alone*` need podman and the stack and were not run); `check_sysml_model` OK; trace_check 91 error lines, as without A-80; second run "nothing to do".
