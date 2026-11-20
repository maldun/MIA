# Goal G-V4.GRAPHAPI.CODE – Code in graphs through trusted tools

Proposed 2026-11-20 by the owner (maldun), D-392: G-V4.GRAPHAPI is cut into three smaller subgoals. Draft for Plan; the top-level requirements are those of the group's spec (`../G-V4.GRAPHAPI/top-level-spec.md`), allocated below.

- Kind: subgoal
- Parent: G-V4.GRAPHAPI
- Statement: A piece of code stored in a graph runs only through a tool and a step the owner has trusted; a step the owner changes keeps its trust and is marked, and an imported step starts untrusted.
- Exit criterion: OC-1 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphapi.code
- Subgoals: –
- Depends on: G-V4.GRAPHAPI.RUN; the threat entry THR-013 is written in its plan
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a graph with a code step, when the owner has not trusted the step, then the run is refused before any step runs and names the step; when trusted, it runs in the contained space of its tool | OC-5 of G-V4.GRAPHAPI |
| OC-2 | Given a trusted step that the owner changes, when the graph runs again, then it is still trusted, marked as changed since trusted, and the run record names the version that ran | OC-5 of G-V4.GRAPHAPI |

## Scope
Inside the scope of G-V4.GRAPHAPI (`../G-V4.GRAPHAPI/goal.md`). The new requirements of the group's top-level spec that this part takes are named in "Source"; they are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-38 | partly | code in a graph runs only through a trusted tool and step; trust stays on change with a mark (FR-66, FR-67); exchange of transforms is unchanged |
| NFR-3 | in | stored code and imported steps stay data until the toolbox runs them (THR-013) |
| FR-7, FR-37, FR-6 | out | the rules and the run are the other two parts |

## Source
Group spec FR-66, FR-67; decisions D-360, D-390; `../G-V4.GRAPHAPI/research.md` (proposed THR-013).

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHAPI.CODE | [ ] Stefan Reiterer (owner) | |

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
