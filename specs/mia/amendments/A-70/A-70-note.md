# A-70: form of the deferrals TD-07 and TD-08 and of REQ-EVL-011 (N-4.1 re-verification 2, S3 and S4)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The second re-verification of N-4.1 found that the decisions D-166 (TD-07, judge calibrations) and D-172 (TD-08, older suite kinds through IF-105) were recorded, but not in the form the trace check needs: REQ-EVL-011 carries no `Relaxed: TD-08` and no `Target` (S3), and TD-07 and TD-08 name a test as their target check although no test can carry a deferral marker while the target is not built (S4). TD-07's trigger has no date. No decision changes; this repairs the form.

## What changes
| Installed file | Change |
|---|---|
| `specs/mia/deferred.md` | TD-07: `Trigger: the first eval target with a judge, or 2026-12-31, whichever first`; TD-07 and TD-08: `Target check: specified only` (was TC-EVL-003 and TC-EVL-011; the tests stay, they check the interim criterion) |
| node `N-4.1-evaluation/requirements.md` | REQ-EVL-011: `Relaxed: TD-08`, `Target: every suite kind runs through IF-105`, History line A-70 |

Both files are built from the installed ones at install time; each edit refuses when its anchor is not found exactly once, and a second run reports "unchanged".

## Checked on a scratch copy of goal/v1 (not installed)
Install with `--do`: two files updated; `trace_check.py` reports no error for TD-07, TD-08 or REQ-EVL-011 (the errors of the whole spec went from 94 to 90, the four being these); a second run says "nothing to do".

Install (on goal/v1): `bash tools/apply_amendment_a70.sh` (look), then `bash tools/apply_amendment_a70.sh --do`, commit as "plan: A-70 installed".
