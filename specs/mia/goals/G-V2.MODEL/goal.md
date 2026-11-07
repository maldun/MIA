# Goal G-V2.MODEL – Skill record and graph model

Drafted 2026-11-07 when the owner asked to split G-V2 into four subgoals for review and build (cut: STORE, MODEL, TRUST, CONVERT).

- Kind: subgoal
- Parent: G-V2
- Statement: A skill is one versioned record that names its command, workflow graph and context graph, and its graph consists of data, transform and master nodes under fixed rules.
- Exit criterion: OC-1, OC-2, OC-3, with the checks of its requirements below
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v2.model
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a skill, when someone looks at what it is made of, then one description gives its command, its steps and the knowledge it uses | FR-36, FR-37, OC-2 |
| OC-2 | Given a description that breaks a rule of the graph (two writers of one piece of data, a loop, a second skill with the same command), when it is saved, then it is refused and the reason is given | FR-36, FR-37, OC-2 |
| OC-3 | Given a graph with steps in order, when it runs, then every step runs after the data it needs, and a step that needs a decision from the owner stops the run and says so | FR-37 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| networkx | real | graph rules (D-187) |
| jsonschema | real | description check (D-187) |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | 12 items in scope, one chain | 2026-11-07 |

## Scope
Top-level items it serves: FR-36, FR-37. Requirements by ID (inside G-V2's scope):

| Item | In/Out | Reason |
|---|---|---|
| REQ-WFM-040 | in | |
| REQ-WFM-041 | in | |
| REQ-WFM-042 | in | |
| REQ-WFM-043 | in | |
| REQ-WFM-044 | in | |
| REQ-WFM-045 | in | |
| REQ-WFM-046 | in | |
| REQ-WFM-047 | in | |
| REQ-WFM-048 | in | |
| REQ-WFM-049 | in | |
| REQ-RUN-016 | in | |
| REQ-RUN-018 | in | |
| IF-301 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |
| IF-203 | in | frozen at G-V2 (A-90, approved 2026-11-07); used through its mock until the provider is merged |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 workflow management (skill record, graph model) | real |  |
| N-2.4.1 pipeline runner | real | topological order, master node refusal |
| N-3.2 graph tables | stand-in | IF-301 v2 mock until G-V2.STORE is merged |

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
