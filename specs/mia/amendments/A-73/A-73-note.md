# A-73: the Character view N-1.2 is integrated (N-1 step 2)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent). Decision: D-175.

## Why
N-1.2 is Verified with accepted deviations. `tests/integration/N-1/step_02` skips ("N-1.2 not integrated yet"). The real Character view is the Godot bridge (`host_bridge.gd`); D-155 made `ui/godot/tools/test_bridge.gd` its real side. It cannot run inside the synchronous node scenario, and an adapter that drives a headless Godot would be a new part. The owner chose (D-175) to keep `test_bridge.gd` as the real side.

## What changes (all built from the installed files; A-72 must be installed)
| File | Change |
|---|---|
| `tests/helpers/integration.mjs` | `READY` gets `N-1.2`; `realSubject('IF-111')` returns the `CharacterMock`, with a comment that the Godot bridge is checked by `test_bridge.gd` |
| `tests/helpers/contract.mjs` | the IF-111 skip reason names `ui/godot/tools/test_bridge.gd` instead of "not integrated yet" |
| `specs/mia/test-spec.md` | TC-IF-111-01 to -06: stage column "1 (mock); real: `ui/godot/tools/test_bridge.gd` (Godot, D-155; the JS real side skips)" |

Each edit is refused when its anchor is not found exactly once; a second run says "nothing to do".

## What step 02 shows, and what it does not
- Step 02 now runs (it skipped). With the mock as IF-111 it checks the same as step 01: **no JS coverage is added**. This is stated, not hidden.
- The evidence for the real character is `test_bridge.gd`: `bash ui/tools/run_godot_tests.sh bridge` gave `RESULT ALL PASSED` on a scratch copy of this branch (Godot 4.6.1 flatpak, `mia.vrm` copied in, project imported first).
- The six JS real cases of IF-111 stay skipped, with the reason above.
- Not shown: the page side of the iframe (`character.js`, tested by `tests/js/character*.test.mjs`) and the frame rate (REQ-CHV-010, field measurement).

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n1b`: IF-111 suite 6 pass, 6 skip (named reason); step_01 and step_02 run, step_03 skips; `tests/js` and all JS contract suites 184 pass, 0 fail; `run_integration_steps.py` 23 python and 4 javascript steps, 0 failed; `check_sysml_model` OK; trace_check 91 error lines, as without A-73; second run "nothing to do".
