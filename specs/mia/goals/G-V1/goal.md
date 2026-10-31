# Goal G-V1 – First version of MIA

Back-filled on 2026-10-30, after the workflow skills introduced goals (M33–M37). The work before this date (Explore, Plan, decomposition, the nodes built so far) went straight to `master`; this record names it after the fact and does not change any decision. The line of work `goal/v1` starts at `53c6766`.

- Kind: iteration
- Parent: –
- Statement: MIA runs as the decomposed multi-user system of the approved HLS (2026-10-24): every node built and integrated, the lookup promoted by the skill path and the literature review added by the same path.
- Exit criterion: VAL-001 to VAL-006 (`specs/mia/test-spec.md`); VAL-002 is the HLS success criterion (second workflow within one month of the lookup's promotion)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner; goal agreed 2026-10-30)
- Line of work: goal/v1
- Subgoals: –
- Status: In progress

## Scope
<!-- Every FR-n / NFR-n of high-level-spec.md. The nodes of decomposition.yaml carry the refined requirements; a node is not a subgoal. -->
| Item | In/Out | Reason |
|---|---|---|
| FR-1 | in | |
| FR-2 | in | |
| FR-3 | in | |
| FR-4 | in | |
| FR-5 | in | |
| FR-6 | in | |
| FR-7 | in | |
| FR-8 | in | |
| FR-9 | in | |
| FR-10 | in | |
| FR-11 | in | |
| FR-12 | in | |
| FR-13 | in | off by default (HLS) |
| FR-14 | in | |
| FR-15 | in | |
| FR-16 | in | |
| FR-17 | in | |
| FR-18 | in | |
| FR-19 | in | |
| FR-20 | in | |
| FR-21 | in | |
| FR-22 | in | |
| FR-23 | in | |
| FR-24 | in | |
| FR-25 | in | |
| FR-26 | in | |
| FR-27 | in | |
| FR-28 | in | |
| FR-29 | in | |
| FR-30 | in | |
| FR-31 | in | |
| FR-32 | in | |
| FR-33 | in | |
| FR-34 | out | FB-01, HLS iteration 1, still waiting for the HLS gate; it becomes its own goal once the gate is approved |
| FR-35 | out | FB-01, as FR-34 |
| NFR-1 | in | |
| NFR-2 | in | |
| NFR-3 | in | |
| NFR-4 | in | |
| NFR-5 | in | |
| NFR-6 | in | |
| NFR-7 | in | |
| NFR-8 | in | |
| NFR-9 | in | |
| REQ-TLS-006 | out | owner 2026-10-31 (D-117): no eval criterion is fixed for it yet (suite, metric, repeats, pin, rule) and MIA has no eval-spec.md with pins; back in a later goal together with that criterion. Its parents REQ-WFX-016 (N-2.4) and REQ-BE-067 (N-2) stay in; they carry the same criterion. |
| REQ-RUN-011 | out | owner 2026-10-31 (D-118): its criterion is the IF-103 contract suite on the real side, but the suite cannot hand its scripted replies to a real provider; back in a later goal with an IF-103 provider and an amendment of the suite. Its parents stay in. |
| REQ-RUN-004 | out | owner 2026-10-31 (D-119): optional learning is not built (LearningLayer and FR-18 proposed); back with a goal that designs the learning layer. |
| REQ-RUN-006 | out | owner 2026-10-31 (D-119): a measurement without a fixed eval criterion and model pins, like REQ-TLS-006; back with the eval criterion and eval-spec.md. |
 | REQ-RUN-007 | out | owner 2026-10-31 (D-120): a measurement without an eval criterion and model pins |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | `high-level-spec.md` approved 2026-10-24 (`review-log.md`) |
| Plan | done | plan package approved, tags `plan-baseline-it1` and `decomp-baseline`; changes since then are amendments A-01 to A-35 (A-34 installed `cca40c8`, A-35 approved: N-2.4.1 T-08, D-125) |
| Implement | in progress | node cycles of `decomposition.yaml`; open nodes and work in `handover-2026-10-31-late.md`. 2026-10-31: N-2.4.1 T-01 to T-05, T-07 done (T-06 out with REQ-RUN-007, T-08 deferred to the next iteration, D-128; fixes of three verification rounds, re-verification 2: Verified with findings once the D-128 scope rows are in); N-2.4.2 T-01 to T-06 done (T-07 out with REQ-TLS-006); node Verifies of N-2.4.1 and N-2.4.2 started (reports in their node folders); only N-3 integrated (`tests/helpers/integration.py` READY) |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
