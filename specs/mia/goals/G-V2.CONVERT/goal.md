# Goal G-V2.CONVERT – Conversion and snapshots

Drafted 2026-11-07 when the owner asked to split G-V2 into four subgoals for review and build (cut: STORE, MODEL, TRUST, CONVERT).

- Kind: subgoal
- Parent: G-V2
- Statement: Every existing skill runs from its record with the same outcomes on its suite, or stays on the old runner for a written reason, and the owner can take and restore a snapshot of the skill set.
- Exit criterion: OC-1, OC-2, OC-3, with the checks of its requirements below
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v2.convert
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given each skill MIA had in v0.1.0, when the owner uses it after conversion, then it gives the same results on its test cases as before, or it stays as it was and the reason is written down | FR-45, OC-1 |
| OC-2 | Given the skill set at a moment the owner has named, when the owner later changes things and goes back, then everything is as it was and the state before going back is kept too | FR-47, OC-4 |
| OC-3 | Given MIA is started from a fresh copy with one configuration file and one command, when it is up, then everything that worked before still works | NFR-9, OC-5 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| model server with the pins of eval-spec.md | real | equivalence runs on MP-light |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | 11 items in scope, one chain | 2026-11-07 |

## Scope
Top-level items it serves: FR-45, FR-47. Requirements by ID (inside G-V2's scope):

| Item | In/Out | Reason |
|---|---|---|
| REQ-WFM-057 | in | |
| REQ-WFM-058 | in | |
| REQ-WFM-059 | in | |
| REQ-WFM-060 | in | |
| REQ-WFM-061 | in | |
| REQ-WFM-062 | in | |
| REQ-WFM-063 | in | |
| REQ-WFM-064 | in | |
| REQ-WFM-065 | in | |
| REQ-WFM-066 | in | |
| REQ-WFM-069 | in | |
| IF-301 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |
| IF-203 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 converter, snapshotStore | real |  |
| N-2.4.1 pipeline runner | real | old runner side by side |
| G-V2.STORE, MODEL, TOOLBOX | real | merged before this subgoal starts |
| model server (Ollama) | real | equivalence on MP-light |

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
