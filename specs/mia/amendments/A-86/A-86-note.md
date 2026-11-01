# A-86: deferral of NFR-8/CON-7 (TD-21) and of the red-team half of NFR-3 (TD-22)

Status: **proposed** (draft for the owner to read and install). Decision: D-180 (owner, 2026-11-01: "defer all" to the four findings of the goal Verify).

## Where it comes from
The goal Verify (`specs/mia/verification-report.md`, commit e4dbbef) found, besides the already decided deferrals:
- **F-01 / D-1:** NFR-8 and CON-7 are not met in the running product: `web_app.py` builds its stores on `FileBackend`, `deploy/compose.yaml` says nothing reads `MIA_DATABASE_URL` yet (D-139), the `mia` image has no psycopg. PostgreSQL runs and is backed up, but the app does not use it. The deviation existed at node level only.
- **F-02 / D-2:** the red-team half of TC-MIA-006 (NFR-3, "0 failures over all red-team cases") is not held: the seven `rt_*` dev suites have 2 cases each, target kind `pending`, and `tests/test_harness.py` fails on it.
- **F-07 / D-9** (no `test-requirements.md`) and **F-06** (36 `eval/suites` files added without an amendment) are process gaps, no requirement is relaxed by them: they are recorded as accepted for G-V1 in D-180 with their action for the Plan of the next iteration, not as TD records.

## What changes (built from the installed files; A-83 and A-85 must be installed)
| File | Change |
|---|---|
| `specs/mia/deferred.md` | TD-21 (NFR-8, CON-7) and TD-22 (NFR-3) appended: interim criterion, target (TC-MIA-015 and TC-MIA-006), reason, effort and risk (proposed), owner, trigger (the Plan of the next iteration or 2026-12-31), target check "specified only", decision D-180 |
| `specs/mia/requirements.md` | NFR-8 and CON-7 get `Relaxed: TD-21`, NFR-3 gets `Relaxed: TD-22`, each with `Target` and a History entry |

Refused when an anchor is not found as expected; a second run says "nothing to do". Outside the amendment (unprotected files of this branch): `goal.md` (NFR-3 and NFR-8 become *partly*, Phases: Verify *proposed*), `review-log.md` (D-180), `tc-mia-status.md`, and the corrected release drafts (PostgreSQL claim, counts, A-84/A-85 installed, TD-21/22 in the tables).

## One step is the owner's
TD-22 touches security, so `trace_check` demands a `Sign-off: <responsible person, date>`. The agent does not sign. If you agree, after the install:
`sed -i '/^## TD-22 /,$s/^- Decision: D-180/- Sign-off: Stefan Reiterer, 2026-11-01\n- Decision: D-180/' specs/mia/deferred.md`
Until then the trace check shows this one error.

## Checked on a scratch copy (not installed)
`--do` on a `git archive` of this branch: trace_check 48 error lines (the one above is the TD-22 sign-off), no other error about TD-21, TD-22, NFR-8, CON-7 or NFR-3; second run "nothing to do".
