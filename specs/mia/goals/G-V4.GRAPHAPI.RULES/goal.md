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
- Status: Proposed

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

## Source
Group spec FR-63, FR-64; decision D-375; the two existing rule sets (`../G-V4.GRAPHAPI/research.md`, F3).

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHAPI.RULES | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | the group's research, spikes and top-level spec (approved 2026-11-20, D-389, D-390) |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
