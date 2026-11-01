# A-87: TD-23, TD-24, the strict expected failure, and the quality step of the stage ladder

Status: **proposed** (draft for the owner to read and install). Decision: D-181 (owner, 2026-11-01).

## Why
After the goal Verify (`specs/mia/verification-report.md`) and D-180, the merge gate (`merge_gate.py`) was still blocked by more than the missing CI: two known red tests, a failing `quality` step, and deviations without a record.

## What changes (built from the installed files; A-83 and A-86 must be installed)
| File | Change |
|---|---|
| `specs/mia/deferred.md` | **TD-23** (IF-404, IF-405, IF-103: the real sides of the contract suites; the IF-104 JS skip reason) and **TD-24** (REQ-TLS-005: `sandbox_backend: none` in the stack) appended; the Target of **TD-16** also names the baseline of BM-GATE-001 |
| the requirements of IF-103 (N-2), IF-404, IF-405, REQ-TLS-005 (N-2.4.2) | `Relaxed`, `Target`, History |
| `tests/helpers/markers.py` | `mark.deferred(TD)`: a unittest expected failure that names its record. When the check starts to pass it fails (an unexpected success): the deferral must then be closed (M26, strict xfail) |
| `tests/acceptance/test_benchmarks.py` | the test carries `mark.deferred("TD-16")`; its text and its failure condition are unchanged |
| `tests/helpers/contract.mjs` | the skip reason of the IF-104 real cases names `tests/test_graph_api.py` (A-60, A-66) and TD-23 instead of "N-2 Backend does not serve the routes of IF-104 yet" |
| `stages.yaml` | the step `quality` passes the requirement files of all nodes (F-08); the runner uses a shell, so the globs work; the step has 0 errors |

Outside the amendment, on this branch: `tests/test_harness.py` (unprotected) keeps the size check for the normal suites and moves the check for the red-team suites (`rt_*` and `verdicts_injection`, 2 to 12 cases, wants 30) into its own test marked `deferred("TD-22")`; `tools/run_merge_gate.sh` (below); `.gitignore` (`.venv-gate/`, `.stages/`).

Each edit is refused when its anchor is not found as expected; a second run says "nothing to do".

## Two steps are the owner's
TD-22 (A-86) and TD-24 touch security: `trace_check` wants a `Sign-off: <person, date>` on each. The agent does not sign. If you agree, after the install:
`sed -i -e '/^## TD-22 /,/^## TD-23 /s/^- Decision: D-180/- Sign-off: Stefan Reiterer, 2026-11-01\n- Decision: D-180/' -e '/^## TD-24 /,$s/^- Decision: D-181/- Sign-off: Stefan Reiterer, 2026-11-01\n- Decision: D-181/' specs/mia/deferred.md`

## The merge gate
`merge_gate.py` blocks every required step of stages 1 to 3 with "no CI result for this commit" and wants one approval by a person; there is no CI. `tools/run_merge_gate.sh` is the local replacement: it makes a Python 3.12 venv from `requirements.txt` and `requirements-db.txt`, runs the stage ladder up to stage 2 (stage 3 only with `MIA_GATE_UPTO=3`, it starts podman containers), writes `.stages/log.jsonl` and prints the gate verdict with `--allow-local` and **no approval**. Whether a local run is enough evidence for the merge is the owner's decision; the approval is typed by the owner. The helper refuses on a dirty tracked tree.

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of this branch: all six files changed, a second run "nothing to do"; no trace error about TD-23, TD-24; `test_benchmarks` "OK (expected failures=1)"; `test_harness` "OK (expected failures=1)", and with the size condition removed it fails with "unexpected successes=1"; the `quality` command exits 0 through a shell; JS contract and page tests 184 pass; the IF-101 suite, `test_graph_api`, `test_preflight`, `test_system_inspection` pass in the image; trace_check 48 error lines = the 46 baseline + the two sign-offs above.
