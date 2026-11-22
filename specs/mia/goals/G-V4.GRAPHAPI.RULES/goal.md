# Goal G-V4.GRAPHAPI.RULES – One rule set for graphs

Proposed 2026-11-20 by the owner (maldun), D-392: G-V4.GRAPHAPI is cut into three smaller subgoals. Draft for Plan; the top-level requirements are those of the group's spec (`../G-V4.GRAPHAPI/top-level-spec.md`), allocated below.

- Kind: subgoal
- Parent: G-V4.GRAPHAPI
- Statement: One set of eight graph rules applies wherever a graph is checked, in one fixed order, and a graph that breaks a rule or has a step input nobody supplies is refused before any step runs.
- Exit criterion: OC-1 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphapi.rules
- Subgoals: –
- Depends on: –; pure checks, they need no stored graph
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a graph that breaks several rules, when it is checked while saving, while editing and before a run, then the same broken rules are listed in the same order every time, each with its steps or connections | OC-4 of G-V4.GRAPHAPI |
| OC-2 | Given a graph with a cycle, two writers of one piece of data, a missing or duplicate connection or an unsupplied step input, when the owner runs it, then no step runs and each broken part is named | OC-4 of G-V4.GRAPHAPI |

## Scope
Inside the scope of G-V4.GRAPHAPI (`../G-V4.GRAPHAPI/goal.md`). The new requirements of the group's top-level spec that this part takes are named in "Source"; they are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-7 | in | one set of eight rules in one fixed order, all broken rules named (FR-63, FR-64 of the group spec) |
| REQ-GA-003 | out | graph rules before saving are refined in G-V4.EDIT, which asks the check route of the interface |
| FR-37, FR-6, FR-38, NFR-3 | out | the run and code in graphs are G-V4.GRAPHAPI.RUN and G-V4.GRAPHAPI.CODE |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| cut again (the checker counts 26 to 42 requirements in scope) | keep together (proposed by the agent, the owner confirms in the plan review) | the number comes from the descendants of one or two top-level items, most of them verified in G-V1 and G-V2; the new work is a few requirements of the group spec; the cut into tasks follows in Plan step 5 | 2026-11-20 |
| cut again (the draft requirements: 27 new, 3 changed, above the hint of 25) | keep together (owner, D-418 (3)) | eight of them are one-line rule definitions reviewed as one group; four tasks as in the high-level spec (rule set module, save path, runner, check route against the mock) | 2026-11-22 |

## Source
Group spec FR-63, FR-64; decision D-375; the two existing rule sets (`../G-V4.GRAPHAPI/research.md`, F3).

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-3.2 Workflows and context graphs (graph tables, rules) | real | the rules module and its table checks |
| N-2.4.1 Pipeline runner (graph run, converter) | real | the check before a run |
| N-5 Graph app (page, vendored vis-network) | stand-in | the check route is tested against the mock |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHAPI.RULES | [x] Stefan Reiterer (owner) | 2026-11-20 |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | the group's research, spikes and top-level spec (approved 2026-11-20, D-389, D-390) |
| Plan | open | plan package complete (2026-11-22): HLS, 30 requirements, test spec, test requirements approved (D-422, D-424); red tests and A-170 staged, `plan.md`, `binding-map.md` by delegation (D-423); waits for the owner's install scripts and plan-gate box |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
