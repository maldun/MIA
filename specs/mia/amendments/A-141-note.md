# A-141: IF-302 v8 and IF-102, the table skill_runs (proposal, owner G-V3.PANEL)

Status: **approved** (2026-11-08, maldun, D-302). `contracts/IF-302-record-tables.md`, `contracts/IF-102-storage-interface.md`, their mocks and suites are changed in a separate step (suite red first). Requirements named here stay Draft until that step is done and merged.

Earlier status line (kept for the record): Status: **proposed** (Draft). `contracts/IF-302-record-tables.md` (v7), `contracts/IF-102-storage-interface.md`, the mocks and REQ-RTB-001 (14 tables) are not changed. Part of A-131. Decision of the owner, 2026-11-08: a new table, not an extension of `reports`.

## Changes
| Item | Change |
|---|---|
| IF-302 `definitions()` | adds `skill_runs`: `versioned` true (every change of a run is a new version), `deletable` true (the chat history deletion of REQ-WFM-135) |
| required fields | `skill_runs` {run (id), skill, skill_version, account, started, state}; optional `ended`, `phases`, `budget`, `counts`, `reason`, `answers`, `result`, `material`, `files`; a record without a required field is rule `schema` |
| IF-302 deletable tables | exactly `history`, `memory`, `tasks`, `memos` and `skill_runs` (TC-IF-302-01 changes) |
| IF-102 | the table list names `skill_runs`; no new operation |
| `reports` | unchanged: the review report stays there (REQ-WFM-038), the run record names its files |

## Requirement it needs
REQ-RTB-007 (N-3.3, Draft, number given by the owner 2026-11-08): "The Record tables shall define the table skill_runs with the required fields run, skill, skill_version, account, started and state, as versioned records that are deletable." Check TC-RTB-007. REQ-RTB-001 (14 tables) carries the proposal for 15 next to its approved text. The deletion of all run records of an account needs no new IF-102 operation: `ids(table)` and `get` find them, `delete` removes them.

## Why not elsewhere
Owner chose it over extending `reports` (which would make a run without a report a 'report') and over a file store (not versioned, not backed up with the database).
