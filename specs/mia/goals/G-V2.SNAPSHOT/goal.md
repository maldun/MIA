# Goal G-V2.SNAPSHOT – Snapshots of the skill set

Split out of G-V2.CONVERT on 2026-11-18 (A-159) after the Verify of CONVERT: the conversion half was ready, the snapshots waited for the contract text of A-121 (installed 2026-11-18: IF-203 v2, IF-302 v13, IF-102 v7).

- Kind: subgoal
- Parent: G-V2
- Statement: The owner can take and restore a snapshot of the skill set.
- Exit criterion: OC-1 below (it serves OC-4 of G-V2), checked by AC-40, TC-WFM-061 to 066, TC-IF-203-10 to 17 and TC-IF-302-11
- Supervision: supervised
- Accepted by: pending (the owner records the agreement in the table below)
- Line of work: goal/v2.snapshot
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given the skill set at a moment the owner has named, when the owner later changes things and goes back, then everything is as it was and the state before going back is kept too | FR-47, OC-4 of G-V2 (was OC-2 of G-V2.CONVERT) |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| PostgreSQL (TD-21) | real | the table `current_versions` is one more generic versioned table (IF-102 v7) |
| G-V2.STORE, MODEL, TOOLBOX, CONVERT | real | merged |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| keep T-CV-05 inside CONVERT | reversed: split | the contract text did not exist; the conversion half was ready to verify | 2026-11-18 |

## Scope
Top-level items it serves: FR-47. Requirements by ID (all approved in the review log of 2026-11-07; status lines corrected 2026-11-17):

| Item | In/Out | Reason |
|---|---|---|
| REQ-WFM-061 to 066 | in | moved from G-V2.CONVERT; ids and checks TC-WFM-061 to 066 unchanged |
| IF-203 v2 | in | installed 2026-11-18 (A-121, D-347 draft row) |
| IF-302 v13, IF-102 v7 | in | installed 2026-11-18 (A-121); the table `current_versions` |

Protected tests: the IF-203 v2 mock and suite and the IF-302 check were added on 2026-11-18 (`c939cc51`); TC-WFM-063 to 065 follow `set_current_version` (`973e2167`).

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 snapshot store and the real library of IF-203 v2 | real | T-SN-01 (was T-CV-05) |
| N-3.3 record tables, N-3.1 storage | real | the table `current_versions` |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | see parent G-V2 |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V2.SNAPSHOT | (owner to fill in) | |
