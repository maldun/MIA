# A-112: IF-302, the table transforms (proposal, owner G-V2.TOOLBOX)

Status: **approved by the owner as drafted (2026-11-11)**, not yet installed. The four open points are settled as proposed (see the end). `contracts/IF-302-record-tables.md`, `contracts/IF-102-storage-interface.md`, their mocks and suites are not changed by this note; that is a separate step (suite red first, the owner's go for protected files), like A-110. Found in Implement (T-06, `implementation-log.md`): the real library of IF-203 v1 saves versioned transform records, and no storage table exists for them; A-110 gave only the meta record a table (`transform_meta`). Owner answers of 2026-11-11: a thin table, not a strict one; an empty code text is fine (a stub transform may stand beside a data node for formal reasons).

## Why a table
A transform is a versioned record of IF-203 v1: ID, version, input and output schemas, code text (A-111). The Storage keeps its immutable versions and the history with authors from the table's `versioned` flag (REQ-SLY-004), and cannot do that for a table it does not know (`unknown_table`). IF-301 holds the graph records (`skills` there is a graph record `{id, data}` and does not fit); trust and lifecycle are in `transform_meta` (A-110). So the code of a transform needs a table of its own.

## Why thin
The shape of the exchange file (ID, version, schemas, code) is checked once, by the toolbox on import (REQ-WFM-055, the exchange schema). A second, stricter copy in IF-302 would have to be kept in sync and could contradict it. The table checks only what the Storage must rely on, as `workflow_meta` does (free `specification` and `benchmark`).

## Changes
| Item | Change |
|---|---|
| IF-302 `definitions()` | adds `transforms`: `versioned` true (every saved version is kept, so the old code of a trusted transform stays readable), `deletable` false |
| required fields | `transforms` {id, version}: `id` a non-empty text, `version` an integer of at least 1 (a boolean or a float is not one, as for votes, D-161); else rule `schema` with the field as detail. The record id is the transform id; `id` inside the record equals it (the library writes both; the table does not compare them) |
| free fields | `inputs`, `outputs` (JSON schemas) and `code` (text) are free: not required, not typed, **an empty or missing `code` is valid** (a stub transform, and the shipped nodes, which have no code text, REQ-WFM-056) |
| `version` vs the Storage version | the field `version` is the version of the code, as the file states it; the Storage counter of the record is a separate number (a file may arrive as version 7 as the first one stored; REQ-WFM-050 compares the field) |
| IF-302 deletable tables | unchanged |
| IF-102 | the table list names `transforms`; no new operation |
| version number | the next free version of IF-302 at install time (v8 is A-110; v9 if A-141 is not installed first) |
| IF-203 (A-111) | the kind `transforms` is stored in this table, trust and lifecycle in `transform_meta`; `doc` may have an empty `code`; no other change |

## Requirement it needs
One requirement in N-3.3, REQ-RTB-009: "The Record tables shall define the table transforms with the required fields id and version, as versioned records that are not deletable." Check TC-RTB-009 (unit, exact): `definitions()["transforms"]`, `validate` for a complete record, for a record with empty code, for one lacking `id` and one lacking `version`, and for a version of 0, `true` and `1.5`; the first two are accepted, the others rule `schema` with the field as detail. REQ-RTB-001 changes with it (15 tables after A-110, 16 with this one, 17 when A-141 is installed too). Contract suite case TC-IF-302-10 (the number 08 is skill_runs of A-141, 09 is A-110; check at install time).

## Effect on the code (T-06, after installation)
`record_tables.py` gets the table and its check (about 8 lines, like `transform_meta`); `workflow_library.py` gets the kind `transforms` in `KINDS` and stores it in the table `transforms`; the mock of IF-203 v1 needs no change.

## What stays outside
- The check that a file has `inputs`, `outputs` and `code` is the toolbox's (exchange schema). A write that bypasses the toolbox through IF-102 is stored as long as `id` and `version` are right; the toolbox is the only writer by design (CON-6, A-89 for who may trust).
- A reader of the table treats `code` as untrusted text, as before; trust is in `transform_meta`.

## Alternatives not taken
- A strict table with `inputs`, `outputs` and `code` required: two places to change for one exchange form, and no stub transforms.
- One generic table `{id, version, data}` for all kinds (`transforms`, `skills`, `snapshots`): saves a definition per kind but hides each kind's rules and breaks the pattern of one table per kind.
- The transform record inside `transform_meta`: breaks REQ-WFM-092 (trust and lifecycle must survive a new version of the code).

## Open points for the owner
1. Name `transforms` (parallel to `transform_meta`).
2. `version` required and an integer of at least 1: yes (proposal), or free like the rest?
3. Whether the shipped nodes are written as stubs with `code: ""` (as `seed_shipped` does today) or with the field left out; both are valid under this proposal.
4. The numbers REQ-RTB-009, TC-RTB-009, TC-IF-302-10 and D-id (next free D-223 at the time of writing: check `tail specs/mia/review-log.md`).

## Owner decision, 2026-11-11 ("approve draft")
Approved as drafted, so the proposals of the four open points stand: 1. the name `transforms`; 2. `version` required, an integer of at least 1; 3. both forms of an empty code are valid, `seed_shipped` keeps writing `code: ""`; 4. the numbers REQ-RTB-009, TC-RTB-009, TC-IF-302-10, the D-id is taken at install time. Still to do by the owner or the Plan session: the requirement and check text, the contract and mock changes, the suite case (all protected), then the install.
