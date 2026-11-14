# A-149: `elements` in the run record, IF-302 v9 and IF-101 v17 (owner G-V3.PANEL)

Status: **approved** (2026-11-08, maldun, D-334). `contracts/IF-302-record-tables.md`, `contracts/IF-101-chat-api.md`, the IF-101 mock and the suites of both are changed in `goals/G-V3/contract-change-2/` (suite red first; installed by the owner with its `install.py`).

## Why
REQ-WFM-138 says the elements a skill reports (label and text pairs) are passed on in `task_status` **and stored in the run record**. A-140 (IF-101 v16, run record) and A-141 (IF-302 v8, `skill_runs`) did not list `elements`, found when TC-WFM-138 was written. Owner decision 2026-11-08: close the gap in the contracts, not in the requirement.

## Changes
| Item | Change |
|---|---|
| IF-302 `skill_runs` | optional field `elements`: a list of `{label, text}` pairs, text only; validation unchanged (optional fields are free) |
| IF-101 run record (`shown_run`, `skill_run`) | adds `elements`: the same list, `[]` when the skill reports none |
| mock of IF-101 | the run record has `elements: []` (the scripted review reports none) |
| suites | TC-IF-101-35 names `elements` among the keys of the record (red on the old mock, green on the new); TC-IF-302-08 stores `elements` in the full record |

## Requirements it serves
REQ-WFM-138 (stored in the run record), REQ-CLV-044 (the view draws them). No requirement text changes.
