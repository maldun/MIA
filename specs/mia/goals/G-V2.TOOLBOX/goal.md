# Goal G-V2.TOOLBOX – Toolbox and trust

Drafted 2026-11-07 when the owner asked to split G-V2 into subgoals; renamed from TRUST and REQ-RUN-017 moved to MODEL when the owner asked for a cut with fewer dependencies (same day).

Amended 2026-11-08 after the toolbox prototype (`prototype/toolbox`, owner decisions D1 to D5 and the answers on the open points): TOOLBOX adds the `transforms` part of IF-203 v1 itself; six new requirements (REQ-WFM-090..095) and a changed REQ-WFM-054; a new table in IF-302 (A-110, proposed). The draft plan is `specs/mia/prototypes/toolbox/plan.md` on that branch.

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
| IF-203 v1, kind `transforms` | real | TOOLBOX adds it (kind, `set_trust`, `set_lifecycle`) in its own block of `workflow_library.py`; MODEL and CONVERT add their own parts; merge order STORE, MODEL, TOOLBOX, CONVERT |
| IF-302, table of transform meta | real | new table for trust, lifecycle, evidence and baseline allowance (A-110, proposed, owner 2026-11-08); needs its contract suite in Plan Step 4 |
| IF-401 run events | stand-in | the event of REQ-WFM-093 goes through a stand-in in the tests |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | 10 items in scope, one chain | 2026-11-07 |
| further cut, after the amendment of 2026-11-08 | keep together | 17 requirement and interface items in scope (16 requirements, IF-203) plus the IF-302 table, still one chain, six tasks in the draft plan; owner decision D-220 | 2026-11-11 (first date 2026-11-08) |

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
| REQ-WFM-090 | in | new, proposed 2026-11-08: the reason an untrusted transform is untrusted is shown on look-up |
| REQ-WFM-091 | in | new, proposed 2026-11-08: the owner's allowance for an untrusted retired transform to run as baseline |
| REQ-WFM-092 | in | new, proposed 2026-11-08: a newer version replaces the code and keeps trust and lifecycle; an equal or lower version is refused |
| REQ-WFM-093 | in | new, proposed 2026-11-08: replacing a trusted transform's code records an event |
| REQ-WFM-094 | in | new, proposed 2026-11-08: a shipped transform is not exported |
| REQ-WFM-095 | in | new, proposed 2026-11-08: only the owner allows the baseline of an untrusted retired transform |
| IF-203 | in | frozen at G-V2 (A-90, approved 2026-11-07); TOOLBOX provides the `transforms` part itself (owner 2026-11-08) |
| IF-302 | in | one new table for transform meta (A-110, proposed); no other change |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 toolbox | real |  |
| IF-203 v1 library (kind `transforms`) | real | built by this goal (owner 2026-11-08); until it is merged the toolbox runs against a mock of it in the tests; transforms are records of the library, the toolbox needs no graph |
| IF-302 table of transform meta | real | new, A-110 (proposed) |

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
| Plan | in progress | requirements, checks and test requirements reviewed and approved 2026-11-11 (maldun, D-220, D-221), goal reviewed; `plan.md` is a draft; A-110 drafted (script `tools/apply_amendment_a110.sh`, not installed); open: Step 4 (red tests, `handover-step4.md`), the parent session's files |
| Implement | in progress | T-01 to T-06 done on `goal/v2.toolbox` (commits `3e68ba6` to `6477dbf`, `implementation-log.md`); hand-over waits for the owner's approval of A-111 (the `transforms` part of IF-203 v1, not installed); A-110 and A-112 are installed |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
