# Goal G-V5 – First test run (PARKED DRAFT)

Opened 2026-11-20 by the owner (maldun), D-385: the leftovers and the validation of G-V2 and G-V3 move out of G-V4, which now only builds, and are joined with the leftovers and the validation of G-V4 itself in one goal, the first test run of everything that was built since v0.2.1. **Parked by the owner on 2026-11-20 (D-386): the definition of G-V5 waits until G-V4 is closed, because G-V4 will change along the way.** Nothing here is decided beyond what the owner said on 2026-11-20; the outcome criteria and scope rows are a proposal for Explore.

- Kind: iteration
- Parent: –
- Statement: The version after G-V4 is put to its first test run: the leftovers of G-V2, G-V3 and G-V4 are settled, the owner judges in real use what G-V2, G-V3 and G-V4 built, and weak workflow graphs are improved with the graph editor.
- Exit criterion: OC-1 to OC-8 below (proposal), checked in Plan; the validation criteria are those collected in G-V5.VALIDATE
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v5
- Subgoals: G-V5.LEFTOVER, then G-V5.VALIDATE
- Status: Proposed (parked: the definition is deferred until G-V4 is closed, D-386)

## Outcome criteria (proposal, to confirm in Explore)
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a skill that runs on the graph path, when the owner changes its trust or lifecycle, or asks it to stop, or it reaches its budget, then the run follows the owner's current setting and ends as the old runner would | FR-6, FR-7, FR-34 (TD-86, TD-87) |
| OC-2 | Given the skills improved in the test run, when they are measured against their suites, then the decision rests on holdout cases labelled by the owner, not on the dev split alone | FR-6 (TD-88, TD-89, TD-90) |
| OC-3 | Given an imported skill step that would do harm, when it is offered to MIA, then it is refused and a red-team case shows that | NFR-3 (V2-6, THR-011) |
| OC-4 | Given the requirements, tests and records of G-V2, G-V3 and G-V4, when they are checked, then no draft, stale scope wording or missing table entry remains, and every open item has a decision | FR-6, FR-34, FR-35, FR-46 (V2-1 to V2-3, V2-8, TD-82 to TD-85) |
| OC-5 | Given the version after G-V4, when the owner uses it, then G-V2 and G-V3 are judged in real use with every finding triaged | FR-6, FR-34, FR-46, FR-47 (VAL-006, 007, 009, 012, 013) |
| OC-6 | Given the version after G-V4, when the owner uses the graph viewer, the editor, the edit log, the storage and its copy, and the context-graph builder in real use, then each is judged with evidence and every finding is triaged | FR-22, FR-30, FR-40, FR-41, FR-42, FR-47 (validation criteria to be written) |
| OC-7 | Given the validation runs, when a workflow graph turns out weak, then the owner improves it in the editor with a reason and sees the effect on the next run | FR-6, FR-22 |
| OC-8 | Given the open items that G-V4 leaves at its close (deferrals, drafts, findings), when the test run starts, then each is fixed, moved with a reason or dropped by the owner | FR-6, FR-22, FR-40 |

## Measure ideas for Plan step 1a (technology dependent second layer, not outcomes)
| Outcome | Measure idea |
|---|---|
| OC-1 | the converted skills run with a trust change, a stop and a budget end on the graph path; the run end and its record equal those of the old runner (the cases of TD-86, TD-87) |
| OC-2 | the holdout suites of the owner on the pinned model with `eval_decide.py`; agents never open them |
| OC-3 | a red-team case for THR-011 and an `agent_check` run with no errors |
| OC-4 | `goal_check.py`, `trace_check.py` and `agent_check.py` without errors for the three goals |
| OC-5, OC-6 | validation sessions with the owner over about a week with the observation protocol of `validation-plan`, rated pass, partial or fail with evidence |
| OC-7 | at least one workflow graph improved in a validation session, with its edit log shown to the owner |
| OC-8 | the lists of open items of G-V4's verification reports and `deferred.md` empty of undecided entries |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| G-V4 merged and deployed as a tagged version | real | the frozen version of the test run; needs a deployment record |
| model server and pins of `eval-spec.md` (MP-light `gemma4:12b-it-qat`) | real | a changed pin or quantization needs the owner |
| holdout suites for research, plans, verdicts, computable, extraction | to be written and labelled by the owner | TD-88; agents never label or run holdout |
| the owner's marked samples for the context-graph builder | to be marked by the owner | NFR-23 of G-V4.BUILDER |
| release v0.2.1 and the old-runner baselines of D-355 | real | the starting point of the comparison |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| leftovers and validation as two subgoals | split: G-V5.LEFTOVER first, then G-V5.VALIDATE | owner 2026-11-20 (D-385): validation runs on the settled version | 2026-11-20 |
| the editor-driven improvement of graphs | a stage of G-V5.VALIDATE | OC-7; it is driven by the validation runs | 2026-11-20 |

## Scope
| Item | In/Out | Reason |
|---|---|---|
| FR-6 | in | the converted skills run on the graph path with the owner's trust, lifecycle, budgets and stop (OC-1, TD-86, TD-87); validated in use (OC-5) |
| FR-7 | in | the graph path follows the owner's live settings (OC-1) |
| FR-22 | in | the graph app (viewer, editor, edit log) is validated in use (OC-6) and used to improve graphs (OC-7) |
| FR-30 | in | context graphs, their editing and their stored form are validated in use (OC-6) |
| FR-34 | in | open items of G-V3 and its validation (OC-4, OC-5) |
| FR-35 | in | open items of G-V3 and its validation (OC-4, OC-5) |
| FR-40 | in | storage, copy and sync of graphs are validated in use (OC-6) |
| FR-41 | in | the context-graph builder and the reading of confirmed items are validated in use (OC-6) |
| FR-42 | in | the context-graph builder is validated in use and its samples are marked (OC-6) |
| FR-46 | in | open items of G-V3 and its validation (OC-4, OC-5) |
| FR-47 | in | snapshots over the new stored form are validated in use (OC-5, OC-6) |
| NFR-3 | in | imported steps that would do harm are refused with a recorded case (OC-3) |
| FR-1, FR-2, FR-3, FR-4, FR-5, FR-8, FR-9, FR-10, FR-11, FR-12, FR-13, FR-14, FR-15, FR-16, FR-17, FR-18, FR-19, FR-20, FR-21, FR-23, FR-24, FR-25, FR-26, FR-27, FR-28, FR-29, FR-31, FR-32, FR-33, FR-36, FR-37, FR-38, FR-39, FR-43, FR-44, FR-45, NFR-1, NFR-2, NFR-4, NFR-5, NFR-6, NFR-7, NFR-8, NFR-9 | out | not changed by G-V2 to G-V4 and not a leftover; it is exercised in daily use but not judged here |

## Parts
To be written in Plan.

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|

None yet.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V5.LEFTOVER | [ ] Stefan Reiterer (owner) | |
| G-V5.VALIDATE | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | in progress | top-level specs of the two subgoals (moved from G-V4, D-385) |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | G-V5.VALIDATE |
