# Goal G-V4.GRAPHSTORE.TRANSFER – Files and database interchangeable, move and sync

Proposed 2026-11-20 by the owner (maldun), D-392: G-V4.GRAPHSTORE is cut into three smaller subgoals. Plan step 0 updated 2026-11-22 by the agent on its own recommendations (D-423), after the RULES merge and the read-only survey (D-460); the changes against the agreed text (OC-3 to OC-5, Depends on, Parts, Scope rows) wait for the owner's agreement below. The top-level requirements are those of the group's spec (`../G-V4.GRAPHSTORE/top-level-spec.md`), allocated below.

- Kind: subgoal
- Parent: G-V4.GRAPHSTORE
- Statement: Graphs behave the same in the live store and in a set of files, the whole store moves between them without loss, and the copy is kept in sync with the live store, which wins.
- Exit criterion: OC-1 to OC-5, decided by the checks the plan names for them (test spec of this subgoal)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphstore.transfer
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE.CORE (one stored truth, merged); G-V4.GRAPHAPI.RULES (the registry of kinds, IF-301 v4, for the unknown-kind refusal; merged `ae34260a`); G-V4.VIEW (the store setting and the fields of `GET /api/v2/store` in IF-104 v2, A-171; the side tables `arrangements` and `graph_changes`, A-172): TRANSFER makes VIEW's fixed store fields real and carries its side tables; the tests that need them skip until VIEW is merged into `goal/v4`
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given the same operations carried out in the live store and in a copy, when the answers are compared, then they are the same, including versions, authors and refusals | OC-5 of G-V4.GRAPHSTORE |
| OC-2 | Given a live store and a copy used for daily running, when the owner syncs them on command, at start and at an orderly stop, then the copy equals the live store and nothing that exists only on the copy is lost | OC-4 of G-V4.GRAPHSTORE |
| OC-3 | Given graphs with several versions each, when the owner moves the whole store from either place to the other and then again, then every graph arrives with all its versions, authors and times unchanged, the second move changes nothing, and a store with one damaged graph is refused with that graph named and nothing moved (proposed 2026-11-22) | OC-5 of G-V4.GRAPHSTORE |
| OC-4 | Given a set of files made on the owner's host, when MIA opens it in another folder or on another machine, then every graph is listed with the same versions and content; given a set made by an older MIA, then it is read completely or refused naming the conversion step (proposed 2026-11-22) | OC-5 of G-V4.GRAPHSTORE |
| OC-5 | Given a move or a sync that is interrupted halfway, when the owner lists and reads graphs afterwards, then every graph is entirely as before, entirely new or at an earlier complete version of the live store, and running the move or sync again finishes it (proposed 2026-11-22) | OC-4 and OC-5 of G-V4.GRAPHSTORE |

## Scope
Inside the scope of G-V4.GRAPHSTORE (`../G-V4.GRAPHSTORE/goal.md`). The group spec's items this part takes are FR-58, FR-59, FR-93, NFR-15 and the move and sync part of NFR-16; Plan step 1b writes their requirements into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| NFR-8 | in | files and database behave the same behind the storage interface (FR-58, FR-59, FR-93, NFR-15, NFR-16 of the group spec) |
| REQ-GA-008 | in | export and seed of the library moved here from the graph app (D-367); refined as a storage command under FR-59 (move of the whole store to and from a set of files), not as a page function (D-460, shown in the plan review) |
| FR-40, FR-30 | out | the stored truth itself is G-V4.GRAPHSTORE.CORE |
| FR-47, FR-36, FR-45 | out | snapshots, skills and migration are G-V4.GRAPHSTORE.MIGRATION; converting a set of the document form is MIGRATION's step, TRANSFER only refuses it by name |

Group-spec items and work outside the table (they are no items of the product spec): OC-1, OC-2, OC-3 come from the group's FR-58, FR-93, FR-59; OC-4 from NFR-15; OC-5 from the move and sync part of NFR-16 (saves are CORE's). Out: the keep in the editor and the recorded changes (FR-95 of EDIT, FR-81 of REPLAY): TRANSFER provides only the one-graph move after a keep that they call (signature agreed with VIEW in Plan). Out: the live store switch: moving the owner's data (volume `mia-data`) to the database and running MIA on "live database + files copy" is a separate later owner gate after `tools/backup.sh` (D-460 (1)); TRANSFER's Deploy runs a smoke on the throw-away database `mia_smoke` only.

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| cut again (the checker counts 26 to 42 requirements in scope) | keep together (proposed by the agent, the owner confirms in the plan review) | the number comes from the descendants of one or two top-level items, most of them verified in G-V1 and G-V2; the new work is a few requirements of the group spec; the cut into tasks follows in Plan step 5 | 2026-11-20 |
| cut again (the draft requirements: 27 new, 2 changed, above the hint of 25) | keep together (agent, by delegation D-423; the owner confirms in the plan review) | six groups of 2 to 8; the six tasks of the high-level spec stay; a cut would put the shared move check and record copy behind a new interface | 2026-11-22 |
| cut into "move" (FR-59, NFR-15) and "sync" (FR-93, AutoSync) | keep together (agent, by delegation D-423; the owner confirms in the plan review) | the sync reuses the move's integrity check and record copy; one interface (IF-102) and one module; expected 15 to 20 new requirements and six tasks | 2026-11-22 |

## Source
Group spec FR-58, FR-59, FR-93, NFR-15, NFR-16 (D-389, D-406); decisions D-372 to D-374, D-460; accepted cases AC-004 to AC-008, and AC-027 (FR-95) and AC-033 (FR-81) for the mechanisms they share (`../G-V4/accepted-cases.md`); `../G-V4.GRAPHSTORE/spikes.md`; prototype rounds 02 and 03 on `prototype/g-v4` (no round 05, D-460: a deviation from D-401, recorded in the high-level spec).

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | real | both backends, the move, the lag, the sync, the aside folder, the format marker |
| N-3.2 Workflows and context graphs (graph tables, rules) | real | the tables that are moved; the registry of kinds (IF-301 v4) for the unknown-kind refusal |
| N-3.3 Record tables | real | VIEW's side tables `arrangements` and `graph_changes` (A-172), carried by the move and the sync |
| N-2.1 API and accounts (web server) | real | the copy setting, AutoSync at start and at an orderly stop, the real values of VIEW's `GET /api/v2/store` |
| N-2.3 Workflow management (library, graph model, snapshots, toolbox) | stand-in | not needed; operations are called directly |
| compose stack and web routing (Caddy) | stand-in | a second machine is simulated by a second folder; PostgreSQL in a throw-away container (`mia_smoke` only) |

## Notes for other records (stale text, corrected in TRANSFER's records)
- Group TLS "Prototype decisions" (FR-57 to FR-62 "not needed") is overtaken by prototype rounds 02 and 03; recorded in the high-level spec.
- G-V4 `goal.md` Frozen table, row IF-102 ("scoped record IDs, sync"): TRANSFER needs no IF-102 amendment (remove on the copy is a backend operation of N-3.1, D-460); the row is the parent's, changed only at the parent's gate.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHSTORE.TRANSFER | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.GRAPHSTORE.TRANSFER, update of 2026-11-22 (OC-3 to OC-5, Depends on, Parts, Scope rows) | Stefan Reiterer (owner): the box below | |

- [X] Agreed by maldun (owner): the update of 2026-11-22 (OC-3 to OC-5, Depends on, Parts, Scope rows). Date:

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | the group's research, spikes and top-level spec (approved 2026-11-20, D-389, D-390) |
| Plan | done | plan gate ticked by the owner (2026-11-23); high-level spec approved; requirements, checks and test requirements approved (D-466 to D-468); A-186 installed (`fbce1924`); red tests installed (`eb0030d9`, tag `plan-baseline-g-v4-transfer`); seam with VIEW agreed (D-470); the update of 2026-11-22 agreed by the owner (Agreement, ticked 2026-11-23) |
| Implement | done | `implementation-log.md`; T-01 to T-06 done (2026-11-23 to 27), SMOKE-TRANSFER-001 green on the branch, F-1 of VIEW's Deploy and V-3 fixed, A-195 installed and approved; image `localhost/mia:g-v4-transfer` (`2f6de35d4f4c`) built from a clean export; hand-over: `handover-2026-11-27-g-v4-transfer-verify-next.md` |
| Verify | done | `verification-report.md` (D-547; first Verify and the re-verify of the fix commits 7607cca9, D-548 to D-550); verified with accepted deviations (D-549's lock limit, R-1, R-2), both boxes ticked by the owner 2026-11-27 |
| Commit | done | merged into `goal/v4` by the owner at `f6ccde75` (2026-11-27, `--no-ff`); before it: `goal/v4` merged in (7eb2749b), the merge steps of plan.md (node files, model texts V-6, accepted cases, D-551), the 33 requirements set to Verified by the owner (268e54e2), TR-TRANSFER-001 to 011 installed by the owner script (c1e84d8e); merge request `merge-request.md` |
| Deploy | open | smoke on the throw-away database `mia_smoke` only (D-460 (1)); SMOKE-RULES-001 runs with it (D-462) |
| Validate | open | the first test run, G-V5 (parked, D-386) |
