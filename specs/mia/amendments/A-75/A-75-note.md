# A-75: the Evaluation harness N-4.1 is integrated (N-4 step 1)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-4.1 is Verified with accepted deviations. `tests/integration/N-4/step_01` skips ("N-4.1 not integrated yet") because `tests/helpers/integration.py` does not list it in `READY`. N-4.1 provides no interface (it consumes IF-105, whose real provider `run_workflow.WorkflowRuns` is in `contract.py` since A-31), so only `READY` changes. Pattern: A-55.

## What changes (built from the installed file)
| File | Change |
|---|---|
| `tests/helpers/integration.py` | `READY` gets `N-4.1`; the comment names A-75 |

Refused when the `READY` line is not found exactly once; a second run says "nothing to do".

## What step 01 shows, and what it does not
- Step 01 runs (it skipped) with IF-105 as the mock. **The scenario of N-4 calls IF-105 directly and never the harness** (the N-4.1 verification says so), so the step adds no coverage of N-4.1's code, as with N-1.1 (D-176).
- The harness is evidenced by its own tests, all green on the scratch copy: IF-105 contract suite (mock and real) 8, `test_eval_platform` 17, `test_decide_guard` 11 (1 skip), `test_judge_calibration` 7, `test_check_baselines` 3, `test_eval_cli` 8.
- Not shown: the root proof-of-concept scenario TC-EVL-010 (task T-07), which waits for the N-0 steps.
- Step 02 (N-4.2) still skips.

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n4a`: N-4 step_00 and step_01 OK, step_02 skipped; the tests above; `run_integration_steps.py` 23 python and 4 javascript steps, 0 failed; `check_sysml_model` OK; trace_check 91 error lines, as without A-75; second run "nothing to do".
