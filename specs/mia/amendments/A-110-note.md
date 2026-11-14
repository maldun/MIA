# A-110: IF-302, the table transform_meta (proposal, owner G-V2.TOOLBOX)

Status: **proposed** (Draft, 2026-11-11). `contracts/IF-302-record-tables.md`, `contracts/IF-102-storage-interface.md`, their mocks and suites are not changed; that is a separate step (suite red first, parent session or the owner's go), like A-141. Decision of the owner, 2026-11-08: trust and lifecycle of a transform live in a new IF-302 table, as `workflow_meta` does for workflows (D-89). Part of G-V2.TOOLBOX (REQ-WFM-050, 051, 054, 067, 091, 092).

## Why a table of its own
A transform is a versioned record of IF-203 v1 (ID, version, schemas, code text). Its trust and lifecycle must survive a new version of the code (REQ-WFM-092, D5), so they cannot be fields of the transform record. One meta record per transform ID, the record id is the transform id.

## Changes
| Item | Change |
|---|---|
| IF-302 `definitions()` | adds `transform_meta`: `versioned` true (every change of trust or lifecycle is a new version, so the history of who trusted what stays), `deletable` false |
| required fields | `transform_meta` {trust, lifecycle}: `trust` one of `untrusted`, `trusted`; `lifecycle` one of `draft`, `tested`, `retired`; any other value is rule `schema` with the field as detail |
| optional fields | `reason` (why untrusted, REQ-WFM-090), `evidence` (the check or run named when moving to `tested`, REQ-WFM-067), `baseline_allowed` (boolean, the owner's allowance for an untrusted retired transform, REQ-WFM-091), `shipped` (boolean, REQ-WFM-056), `changed_by` (account) |
| IF-302 deletable tables | unchanged (exactly `history`, `memory`, `tasks`, `memos`, and `skill_runs` once A-141 is installed) |
| IF-102 | the table list names `transform_meta`; no new operation |
| version number | the next free version of IF-302 at install time (A-141 takes v8 on `goal/v3`; v9 if it is installed first) |

## Requirement it needs
One requirement in N-3.3, REQ-RTB-008 (owner 2026-11-11): "The Record tables shall define the table transform_meta with the required fields trust and lifecycle, as versioned records that are not deletable." Check with a scenario like TC-RTB-007. REQ-RTB-001 (table count) changes with it; if A-141 is installed first it reads 16.

## What stays outside
- Whether an account may set a value (only the owner trusts; any account may untrust, REQ-WFM-054) is a rule of the Workflow management, not of the table.
- The event of REQ-WFM-093 is the toolbox's, through IF-401.
- The contract suite for the table and the IF-203 v1 `transforms` suite are Step 4 work (protected, the owner installs).

## Owner answers of 2026-11-11 (D-221)
1. Table name `transform_meta`. 2. The N-3.3 requirement is REQ-RTB-008 (not yet written); the IF-302 version is the next free one at install time (v8 or v9, A-141 or A-110 first), REQ-RTB-001's table count follows. 3. `shipped` is a field of the table.

## Open points (answered, kept for the record)
1. Table name `transform_meta` (proposal; parallel to `workflow_meta`).
2. Number of the N-3.3 requirement and the order of A-141 and A-110 (version numbers).
3. Is `shipped` a meta field (proposal) or derived from a folder? The proposal keeps it in the table so `look_up` needs one read.
