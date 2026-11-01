# A-83: the nine stage 4 checks of the root table are deferred (TD-12 to TD-20)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent). Decision: D-178 (owner, 2026-11-01: "start the goal Verify with the stage 4 rows deferred").

## Why
Nine checks of `specs/mia/test-spec.md` are stage 4 (eval, benchmark, statistical): TC-MIA-002, -003, -009, -011, -019, -022, -024, -025, -028. They are decided on the pinned model against criteria, suites, holdouts and baselines, none of which the plan has (no `eval-spec.md` for MIA; the holdouts are the owner's). The goal Verify can not decide them; each is recorded as a deferral so it stays visible and its target check stays alive (M26).

## What changes (built from the installed files)
| File | Change |
|---|---|
| `specs/mia/deferred.md` | TD-12 to TD-20 appended, one per check, each with interim criterion (the node tests of the row, listed in `tc-mia-status.md`), target (the check itself), reason, effort and risk (proposed), owner, trigger (the Plan of the next iteration, or 2026-12-31), target check "specified only", decision D-178 |
| `specs/mia/requirements.md` | 14 top-level requirements get `Relaxed: TD-nn`, `Target` and a History entry: TD-12 FR-9, FR-10; TD-13 FR-11, FR-12, NFR-4; TD-14 FR-20; TD-15 FR-29; TD-16 NFR-7; TD-17 NFR-2, FR-17, FR-18; TD-18 FR-14; TD-19 FR-15; TD-20 FR-33 |

Each edit is refused when its anchor is not found as expected; a second run says "nothing to do".

## One step is the owner's
`trace_check` demands a `Sign-off: <responsible person, date>` on a record whose text touches safety, security, legal, licence, privacy or confidentiality. **TD-15** (FR-29) does, because the text of FR-29 contains "safety". The agent does not sign. After the install, add the line yourself if you agree, for example:
`sed -i '/^## TD-15 /,/^## TD-16 /s/^- Decision: D-178/- Sign-off: Stefan Reiterer, 2026-11-01\n- Decision: D-178/' specs/mia/deferred.md`
Until then the trace check shows this one error (48 error lines instead of 47).

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of `v1-verify-prep`: trace_check 48 error lines (47 before; the new one is the TD-15 sign-off), warnings only for "open deferral not listed in the verification report" of the nodes (as for the older records; the goal report will list them); `check_sysml_model` OK; `goal_check` no findings; second run "nothing to do".

## What it does not do
It does not decide any of the nine checks and does not say they pass. The effort and risk lines are proposals for the owner to change.
