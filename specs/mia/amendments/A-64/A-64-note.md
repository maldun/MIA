# A-64: a stage-3 step for TC-API-013 (N-2.1 re-verification R-5; D-167, D-169)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
TC-API-013 (`tests/test_container_alone.py`, REQ-API-013, AC-29) is stage 3 in the node test-spec, but `stages.yaml` has no step for it: it runs only
inside the stage-1 step `unit` on a host with podman and skips in the image. The owner decided (D-167) that it gets its own stage-3 step, and (D-169)
that a skip of TC-API-013 in that step counts as a failure, like the step `contract-postgres` of A-59.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `stages.yaml` | made by the script from the installed file | stage-3 step `container-alone`: `bash tools/container_alone.sh`, `needs: [unit]`, inserted before the step `smoke` |

Not protected, committed with the draft: `tools/container_alone.sh` runs `tests/test_container_alone.py` and exits 1 when a test was skipped (as `tools/contract_postgres.sh`); `tests/test_container_alone_step.py` checks that with a fake python.

The script builds `stages.yaml` from the installed file at run time (A-59 added the step `contract-postgres` the same way), so it cannot bring back an
older copy; it refuses when the anchor (the step `smoke`) is not found exactly once, and a second run reports "unchanged".
No contract, mock, suite or test-spec row changes: the test-spec row of TC-API-013 already says stage 3.

## Conditions of the step
- Needs podman and the local image `localhost/mia:latest` (or `MIA_IMAGE`); the image is never pulled. The pod is published only on 127.0.0.1 and removed afterwards.
- Without podman, the image or the stand-in the test skips; the step then fails with "a test was skipped" (D-169).
- The test still runs inside the stage-1 step `unit` too (discover finds it); there it skips in the image.

Install (on goal/v1): `bash tools/apply_amendment_a64.sh` (look), then `bash tools/apply_amendment_a64.sh --do`; commit as "plan: A-64 installed".
