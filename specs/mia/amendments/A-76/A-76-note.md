# A-76: the Operation layer N-4.2 and the node N-4 are integrated (N-4 step 2)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-4.2 is Verified with accepted deviations; `tests/integration/N-4/step_02` skips ("N-4.2 not integrated yet"). N-4.2 provides no interface (compose stack and configuration), so only `READY` changes. With step 02 both children of N-4 are done, so the node `N-4` is listed too (as A-55 did for N-2.4). Pattern: A-55, A-75.

## What changes (built from the installed file; A-75 must be installed)
| File | Change |
|---|---|
| `tests/helpers/integration.py` | `READY` gets `N-4.2` and `N-4`; the comment names A-76 |

Refused when the `READY` line is not found exactly once; a second run says "nothing to do". `N-4` wakes no N-0 step: they all need `N-1`, which is not in this list (it is added with the root steps).

## What step 02 shows, and what it does not
- Step 02 runs (it skipped) with IF-105 as the mock. The scenario never starts the compose stack (TC-N4-001 to -003 run in stage 3), so **the step adds no coverage of N-4.2**.
- N-4.2 is evidenced by its own stage 1 tests, green on the scratch copy in the image: test_backup (1 skip, podman), check_free, compose_stack, config, config_local, deploy, first_account, missing_options, requirements, runbook, shutdown, shutdown_database, up_backup. Not run, as the stack is off limits: test_compose_stack_system, test_up_fresh, test_first_account_up.
- Not shown: the stack starting on the host (stage 3, owner's checks).

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-int-n4b`: N-4 step_00, 01, 02 all OK, none skipped; the tests above; `run_integration_steps.py` 23 python and 4 javascript steps, 0 failed; `check_sysml_model` OK; trace_check 91 error lines, as without A-76; second run "nothing to do".
