# Goal G-V1 – First version of MIA

Back-filled on 2026-10-30, after the workflow skills introduced goals (M33–M37). The work before this date (Explore, Plan, decomposition, the nodes built so far) went straight to `master`; this record names it after the fact and does not change any decision. The line of work `goal/v1` starts at `53c6766`.

- Kind: iteration
- Parent: –
- Statement: MIA runs as the decomposed multi-user system of the approved HLS (2026-10-24): every node built and integrated, the lookup promoted by the skill path and the literature review added by the same path.
- Exit criterion: VAL-001 and VAL-003 to VAL-006 (`specs/mia/test-spec.md`); VAL-002, the HLS success criterion (second workflow within one month of the lookup's promotion), moved to the next goal with the review (owner 2026-10-31, D-134)
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
| REQ-RUN-013 | partly | owner 2026-10-31 (D-128, D-130): the review entry of AC-9 is out: T-08 deferred to the next iteration with FB-02, FB-03; lookup and verify run on the runner |
| REQ-RUN-005 | partly | owner 2026-10-31 (D-128, D-130): the measurement of AC-22 is out: server token counts over the lookup suites come back with eval-spec.md; the refusal by estimate stays in |
| REQ-RUN-009 | partly | owner 2026-10-31 (D-128, D-130): the 10 s part of AC-19 is out: with REQ-RUN-007; the order of the turns stays in |
| REQ-TLS-002 | partly | owner 2026-10-31 (D-152): the measurement part (an eval run with a criterion and pins) is out: back with eval-spec.md and FB-03; the passages with their source references stay in |
| REQ-SLY-007 | partly | owner 2026-10-31 (D-158): the importers of outside data are out: next iteration with FB-04; storage, versions and the change notices stay in |
| REQ-GTB-004 | partly | owner 2026-10-31 (D-160): the workflow library folder (root task T-10) is out: TD-06; TC-GTB-005 is rewritten with FB-03; the graph rules and tables stay in |
| REQ-RTB-006 | partly | owner 2026-10-31 (D-161): AC-3 (an edited trust value survives a restart through the record table) is out: next iteration with FB-04; the table and its rules stay in |
| REQ-CLV-010 | partly | owner 2026-10-31 (D-163): votes on reactions and behaviours and the drawn series of the votes are out: next iteration with FB-05; votes on answers stay in |
| REQ-GA-002 | out | owner 2026-10-31 (D-135): N-5 T-02 (edit as JSON) waits for FB-02 (the graph form and the rules may change); back in the next iteration |
| REQ-GA-003 | out | owner 2026-10-31 (D-135): the graph rules in the page wait for FB-02; the backend still checks the rules on save |
| REQ-CHV-007 | out | owner 2026-10-31 (D-137): model selection after the first human tests; next iteration |
| REQ-CHV-008 | out | owner 2026-10-31 (D-137): the outfit switch in Godot comes with the model selection; the variant label in the chat stays |

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
| Implement | in progress | node cycles of `decomposition.yaml`; open nodes and work in `handover-2026-10-31-late.md`. 2026-10-31: N-2.4.1 T-01 to T-05, T-07 done (T-06 out with REQ-RUN-007, T-08 deferred to the next iteration, D-128; fixes of three verification rounds, N-2.4.1 **Verified with findings** (re-verification 2, the D-128 scope rows written by D-130); N-2.4.2 **Verified with findings** (owner, D-134); N-2.4.3 and N-4.2 **Verified with accepted deviations** (owner, D-148); N-1.3 waits for the owner's checks by ear; N-2.1 Verify: not verified yet (D-147 A-52, findings V-0 to V-11)); N-2.4.2 T-01 to T-06 done (T-07 out with REQ-TLS-006); node Verifies of N-2.4.1 and N-2.4.2 started (reports in their node folders); only N-3 integrated (`tests/helpers/integration.py` READY) |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
