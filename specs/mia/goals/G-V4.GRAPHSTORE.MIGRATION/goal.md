# Goal G-V4.GRAPHSTORE.MIGRATION – Migration of existing graphs and skills from stored graphs

Proposed 2026-11-20 by the owner (maldun), D-392: G-V4.GRAPHSTORE is cut into three smaller subgoals. Draft for Plan; the top-level requirements are those of the group's spec (`../G-V4.GRAPHSTORE/top-level-spec.md`), allocated below.

- Kind: subgoal
- Parent: G-V4.GRAPHSTORE
- Statement: The graphs that exist today are moved to the new stored form with a comparison report, pipelines are imported once into stored graphs, skills run from their stored graph, and snapshots restore graphs as they were.
- Exit criterion: OC-1 to OC-3 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphstore.migration
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE.CORE; G-V4.GRAPHSTORE.TRANSFER for the trial on a copy
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given the graphs stored today, when they are moved to the new form, then each reads back as before and the owner can compare old and new before anything old is removed | OC-2 of G-V4.GRAPHSTORE |
| OC-2 | Given a snapshot taken before and one after the change, when the owner restores either, then the graphs are as they were at that snapshot | OC-3 of G-V4.GRAPHSTORE |
| OC-3 | Given a skill with a stored graph, when the owner runs it, then the run follows that graph and says which graph and version it used; a skill without one runs as before until it is imported | OC-6 of G-V4.GRAPHSTORE |

## Scope
Inside the scope of G-V4.GRAPHSTORE (`../G-V4.GRAPHSTORE/goal.md`). The new requirements of the group's top-level spec that this part takes are named in "Source"; they are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-47 | in | snapshots over the new stored form (OC-10 of G-V4) |
| FR-36 | partly | a skill record points at its stored graph (FR-62 of the group spec) |
| FR-45 | partly | the converted pipelines become an import path (FR-61, FR-62); the old runner stays for a skill without a stored graph |
| FR-40, FR-30, NFR-8, REQ-GA-008 | out | the stored truth and the transfer are the other two parts |

## Source
Group spec FR-61, FR-62; decisions D-361, D-373, D-374.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHSTORE.MIGRATION | [ ] Stefan Reiterer (owner) | |

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
