# Goal G-V2.STORE – Graph records (storage)

Drafted 2026-11-07 when the owner asked to split G-V2 into four subgoals for review and build (cut: STORE, MODEL, TRUST, CONVERT).

- Kind: subgoal
- Parent: G-V2
- Statement: Graphs are kept as separate node and edge records with a fixed type, rebuilt from their type, and the document form stays readable during the transition.
- Exit criterion: OC-1, OC-2, OC-3, with the checks of its requirements below
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v2.store
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a skill's graph kept as separate pieces, when the owner or MIA asks for it back, then the same graph returns, unchanged | FR-40, OC-2 |
| OC-2 | Given a graph with an unknown kind of piece or a description that does not fit its kind, when it is stored or checked, then it is refused and the reason names the piece | FR-40, OC-2 |
| OC-3 | Given a graph kept in today's single-document form, when MIA reads it after the rework, then it reads as before | FR-40, OC-1 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| PostgreSQL (TD-21) | real | node and edge tables |
| jsonschema | real | types as schemas (D-187) |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | 12 items in scope, one chain | 2026-11-07 |

## Scope
Top-level items it serves: FR-40. Requirements by ID (inside G-V2's scope):

| Item | In/Out | Reason |
|---|---|---|
| REQ-GTB-005 | in | |
| REQ-GTB-006 | in | |
| REQ-GTB-007 | in | |
| REQ-GTB-008 | in | |
| REQ-GTB-009 | in | |
| REQ-GTB-010 | in | |
| REQ-GTB-011 | in | |
| REQ-GTB-012 | in | |
| REQ-GTB-013 | in | |
| REQ-GTB-014 | in | |
| REQ-GTB-015 | in | |
| IF-301 | in | |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-3.2 graph tables, typeRegistry | real | provider of IF-301 v2 |
| N-2 library and runner | stand-in | unchanged; consumers use the IF-301 v2 mock until this subgoal is merged |

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
