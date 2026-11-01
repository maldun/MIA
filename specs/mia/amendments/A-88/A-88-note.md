# A-88: TD-25, the smoke tests leave the merge gate

Status: **proposed** (draft for the owner to read and install). Decision: D-182 (owner, 2026-11-01).

## Why
The merge gate run on `c4377aa` (stages 1 to 3, local) was green except the stage 3 step `smoke`. It ran `unittest discover -s tests/smoke -p "test_*.py"`; the files are named `smoke_*.py`, so nothing ran and Python 3.12 reports `NO TESTS RAN` as a failure. A corrected pattern would not help: the three files are run on the owner's workstation in Phase 6 (their own docstrings; `goals/G-V1/deploy-plan.md`). `smoke_fresh_install.py` and `smoke_stack.py` bring up the whole compose stack, which this machine cannot run (fatal CPU machine checks at shutdown under load); `smoke_gate.py` runs the number gate through the real Ollama, an eval-style run that does not belong in this Verify (D-178).

## What changes (built from the installed files; A-87 must be installed)
| File | Change |
|---|---|
| `specs/mia/deferred.md` | **TD-25** appended: the smoke tests are not part of the merge gate; target: they have run in Deploy and the ladder has a smoke step that finds them |
| `specs/mia/requirements.md` | NFR-9 gets `Relaxed: TD-25`, `Target`, History |
| `stages.yaml` | the step `smoke` is removed; a comment names where the smoke tests run |

`required_for_merge` stays `[1, 2, 3]`. Stage 3 keeps `container-alone` and `contract-postgres`.

Each edit is refused when its anchor is not found as expected; a second run says "nothing to do".

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of this branch: the three files changed, a second run "nothing to do", no trace error about TD-25, the dry run of the ladder lists no smoke step.

## One step is the owner's
TD-25 is not a security record, so it needs no `Sign-off` line. The owner decides when the Deploy phase runs the smoke tests (`deploy-plan.md`).
