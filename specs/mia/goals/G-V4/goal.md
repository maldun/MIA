# Goal G-V4 – Rework of what G-V2 and G-V3 left over (DRAFT)

Opened 2026-11-20 on the owner's request: "G-V4 starts a bigger rework". The owner chose (questionnaire 2026-11-20) to **take the leftovers of G-V2 and G-V3 as the scope**. The sources are `G-V2/remainder-for-next-goal.md`, the open items of `G-V3/verification-report.md` and `deferred.md` (TD-82 to TD-90). **Nothing here is decided by the owner beyond that choice**: statement, outcome criteria and scope rows are a proposal for the Explore phase; the rework may be bigger than this list.

- Kind: iteration
- Parent: –
- Statement: The converted skills run with the live trust, lifecycle, budgets and stop of the owner, the skills improved by the rework are measured on holdout suites, the draft requirements and deferrals of G-V2 and G-V3 are settled, and the validation of G-V2 and G-V3 is done on this version.
- Exit criterion: OC-1 to OC-5 below (proposal), checked in Plan; the validation criteria are those collected in G-V4.VALIDATE
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4
- Subgoals: G-V4.VALIDATE (further subgoals, for example "improve the skills" named by D-355 and D-356, are not agreed yet)
- Status: Proposed

## Outcome criteria (proposal, to confirm in Explore)
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a skill that runs on the graph path, when the owner changes its trust or lifecycle, or asks it to stop, or it reaches its budget, then the run follows the owner's current setting and ends as the old runner would | FR-6, FR-7, FR-34 (TD-86, TD-87) |
| OC-2 | Given the skills of the rework, when they are measured against their suites, then the decision rests on holdout cases labelled by the owner, not on the dev split alone | FR-6 (TD-88, TD-89, TD-90) |
| OC-3 | Given an imported skill step that would do harm, when it is offered to MIA, then it is refused and a red-team case shows that | NFR-3 (V2-6, THR-011) |
| OC-4 | Given the requirements, tests and records of G-V2 and G-V3, when they are checked, then no draft, stale scope wording or missing table entry from the lists of both goals remains | (V2-1 to V2-3, V2-8, TD-82 to TD-85) |
| OC-5 | Given the finished rework, when the owner uses the version, then G-V2 and G-V3 are validated on it (G-V4.VALIDATE) | VAL-006, 007, 009, 012, 013 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| model server and pins of `eval-spec.md` (MP-light `gemma4:12b-it-qat`) | real | a changed pin or quantization needs the owner |
| holdout suites for research, plans, verdicts, computable, extraction | to be written and labelled by the owner | TD-88; agents never label or run holdout |
| release v0.2.1 and the old-runner baselines of D-355 | real | the starting point |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| validation of G-V2 and G-V3 as its own subgoal | split: G-V4.VALIDATE | owner 2026-11-20: validate after the rework, since its changes may affect the validation runs | 2026-11-20 |
| improving the skills (TD-86 to TD-89 name it as the trigger) | open | scope not set; decide in Explore | |
| paperwork (V2-1, V2-2, V2-3, V2-8, goal_check GL1 and GL3, TD signatures) | open | small; may be a task list, not a subgoal | |

## Scope
To be written in Explore. Every FR and NFR of the top-level spec needs a row (in or out, with a reason) before Plan. Proposed from the leftovers:

| Item | In/Out | Reason |
|---|---|---|
| FR-6, FR-7 (graph path: trust, lifecycle, budgets, stop) | proposed in | TD-86, TD-87 |
| FR-34, FR-35, FR-46 (Skill run view, chat) | proposed in, partly | open items V3-6, F-04, TD-82 to TD-85 |
| NFR-3 (trust boundaries) | proposed in | V2-6, THR-011, `TB-exchange` |
| everything else | open | decide in Explore |

## Parts
To be written in Plan.

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | none yet |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.VALIDATE | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | open | scope of the rework (owner), `top-level-spec.md` update |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | G-V4.VALIDATE |
