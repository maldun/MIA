# Goal G-V2.TRUST – Toolbox and trust

Drafted 2026-11-07 when the owner asked to split G-V2 into four subgoals for review and build (cut: STORE, MODEL, TRUST, CONVERT).

- Kind: subgoal
- Parent: G-V2
- Statement: Transforms are kept in a toolbox by ID with a trust status and a lifecycle; a step from outside is stored but never runs until the owner allows it.
- Exit criterion: OC-1, OC-2, OC-3, with the checks of its requirements below
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v2.trust
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a step that arrives from outside MIA, when someone tries to use it, then it does not run and says why | FR-38, NFR-3, OC-3 |
| OC-2 | Given such a step, when only the owner allows it, then it runs; nobody else can allow it | FR-38, OC-3 |
| OC-3 | Given a step that is retired, when someone looks for a step to use, then it is not offered, but it can still serve as the reference of a comparison | FR-38, OC-1 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| jsonschema | real | exchange file check |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | 11 items in scope, one chain | 2026-11-07 |

## Scope
Top-level items it serves: FR-38. Requirements by ID (inside G-V2's scope):

| Item | In/Out | Reason |
|---|---|---|
| REQ-WFM-050 | in | |
| REQ-WFM-051 | in | |
| REQ-WFM-052 | in | |
| REQ-WFM-053 | in | |
| REQ-WFM-054 | in | |
| REQ-WFM-055 | in | |
| REQ-WFM-056 | in | |
| REQ-WFM-067 | in | |
| REQ-WFM-068 | in | |
| REQ-WFM-070 | in | |
| REQ-RUN-017 | in | |
| IF-301 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |
| IF-203 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 toolbox | real |  |
| N-2.4.1 pipeline runner (refusal) | real | REQ-RUN-017 |
| graph model, skill record | stand-in | G-V2.MODEL contract, used through IF-203 v1 mock until merged |
| N-3.2 graph tables | stand-in | IF-301 v2 mock |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | see parent G-V2 |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| – | – | no subgoals |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | HLS of iteration 2 approved 2026-11-05 (D-186) |
| Plan | in progress | requirements drafted in G-V2 Plan step 1; checks in Step 3 |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
