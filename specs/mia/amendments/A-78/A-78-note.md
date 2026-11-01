# A-78: the Workflow management N-2.3 is integrated (N-2 step 2)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-2.3 is Verified with accepted deviations. `tests/integration/N-2/step_02` skips ("N-2.3 not integrated yet") because `tests/helpers/integration.py` does not list it in `READY`. Its real provider of IF-203 (`WorkflowLibrary` on the real `Storage` in a fresh folder) is in `tests/helpers/contract.py` since A-14, so only `READY` changes. Pattern: A-55, A-77.

## What changes (built from the installed file; A-77 must be installed)
| File | Change |
|---|---|
| `tests/helpers/integration.py` | `READY` gets `N-2.3`; the comment names A-78 |

Refused when the `READY` line is not found exactly once; a second run says "nothing to do".

## What step 02 shows, and what it does not
- Step 02 runs (it skipped): the library part of the scenario (a workflow with a cycle is refused with the rule `cycle`; promotion to trusted needs a specification and a benchmark; then it succeeds) runs on the real `WorkflowLibrary`; speech is real from A-77; chat turn, run and API stay mocks.
- Not shown: the model-dependent criteria of N-2.3 (eval suites on the pinned model). Its holdouts (REQ-WFM-014/015/016/024) are the owner's: no `*.holdout` suite or `split:holdout` case was run or opened.
- Steps 03 to 05 of N-2 still skip.

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n2b`: N-2 step_00, 01, 02 OK; IF-203 contract suite OK (8, mock and real); the node's 15 test files OK in the image (test_pdf_text skips 13 cases whose tools the image lacks); `run_integration_steps.py` 23 python and 4 javascript steps, 0 failed; `check_sysml_model` OK; trace_check 91 error lines, as without A-78; second run "nothing to do".
