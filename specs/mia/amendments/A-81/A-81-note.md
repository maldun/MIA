# A-81: the Web Frontend N-1 is listed; N-0 steps 02 to 04 run

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The root steps are Python and read `READY` of `tests/helpers/integration.py`; the children of N-1 were integrated in the JavaScript `READY` (A-72, A-73, A-74), so `N-1` itself is not listed in the Python one. N-3 (A-02), N-4 (A-76) and N-2 (A-80) are listed. N-0 step_02 needs N-3 and N-1, step_03 needs N-3, N-1, N-4, step_04 needs N-3, N-1, N-4, N-2. **One entry, `N-1`, therefore wakes all three steps at once**; a separate amendment per step is not possible. Step_05 still needs N-5. Pattern: A-55, A-76, A-80.

## What changes (built from the installed file; A-80 must be installed)
| File | Change |
|---|---|
| `tests/helpers/integration.py` | `READY` gets `N-1`; the comment names A-81 |

Refused when the `READY` line is not found exactly once; a second run says "nothing to do".

## What the steps show, and what they do not
- Step_02 (N-1 real), step_03 (N-4 real) and step_04 (N-2 real, all the Python interfaces real: IF-101, 102, 104, 105, 201, 202, 203, 204, 301, 302, 401, 402) run the root scenario (the lookup workflow from chat to the stored record) and **pass**. No finding.
- N-1 itself is JavaScript and has no Python interface in this scenario; the scenario's chat goes through the IF-101 provider. So steps 02 and 03 repeat what step 01 and the real N-3 (and N-4 harness) already show; step_04 is the real end-to-end of the Python side.
- Step_05 (N-5) skips: N-5 waits for FB-02.
- The requirements the steps decide (FR-1, FR-9, FR-16, FR-21) are verified by `TC-MIA-nnn` ids that are in no test table yet (44 known, the traceability errors stay): **they must be written before the last N-0 step**. Nothing was invented here.
- Step_04 needs flask (the real IF-101): on a python without it the runner reports it failed (like N-2 step_05); in the image and the stage venv it passes.

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n0a`: N-0 step_00 to 04 OK, step_05 skipped; all 23 Python steps OK in the image; `check_sysml_model` OK; trace_check 91 error lines, as without A-81; second run "nothing to do".
