# Goal G-V2.TOOLBOX – Toolbox and trust

Drafted 2026-11-07 when the owner asked to split G-V2 into subgoals; renamed from TRUST and REQ-RUN-017 moved to MODEL when the owner asked for a cut with fewer dependencies (same day).

- Kind: subgoal
- Parent: G-V2
- Statement: Transforms are kept in a toolbox by ID with a trust status and a lifecycle; a step from outside is stored but never runs until the owner allows it.
- Exit criterion: OC-1, OC-2, OC-3, with the checks of its requirements below
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v2.toolbox
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a step that arrives from outside MIA, when someone looks it up, then it is shown as untrusted, with the reason, and cannot be marked trusted by anyone but the owner | FR-38, NFR-3, OC-3 |
| OC-2 | Given such a step, when the owner marks it trusted, then it is shown as trusted; when anyone else tries, it is refused and says why | FR-38, OC-3 |
| OC-3 | Given a step that is retired, when someone looks for a step to use, then it is not offered, but it can still serve as the reference of a comparison | FR-38, OC-1 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| jsonschema | real | exchange file check |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | 10 items in scope, one chain | 2026-11-07 |

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
| IF-203 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 toolbox | real |  |
| IF-203 v1 library (kind `transforms`) | stand-in | mock until the provider is merged; transforms are records of the library, the toolbox needs no graph |

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
