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
| FR-22 | out | owner 2026-11-01 (D-177): the Graph app N-5 moves to the next iteration and is redesigned with FB-02; its requirements REQ-GA-001 to -011 are out (below). What stays: the backend routes of IF-104 and the graph tables (N-2.1, N-3.2), the static page `graph_app/` and its `graph` container as they are |
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
| NFR-3 | partly | owner 2026-11-01 (D-180, TD-22): the red-team half of TC-MIA-006 (0 failures over all red-team cases) is deferred; the deterministic mitigations (tool door, sandbox, injection signal checks, PDF wall) stay in |
| NFR-4 | in | |
| NFR-5 | in | |
| NFR-6 | in | |
| NFR-7 | in | |
| NFR-8 | partly | owner 2026-11-01 (D-180, TD-21): the app keeps its state in the file backend; moving it to PostgreSQL (and CON-7) is deferred; the storage layer, the database service and backup and restore stay in |
| NFR-9 | in | the container of the Graph app (N-5) is the static page of the T-01 mockup, nothing more (D-177) |
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
| REQ-EVL-005 | partly | owner 2026-10-31 (D-164): recorded baselines for the tested and trusted workflows are out: next iteration's Plan with eval-spec.md; the baseline check stays in |
| REQ-EVL-009 | partly | owner 2026-10-31 (D-164): holdout cases for lookup and verify (labelled by the owner) are out: next iteration's Plan; the holdout guard stays in |
| REQ-EVL-003 | partly | owner 2026-10-31 (D-166): the calibrations act only once an eval target uses a judge: TD-07; the calibration code and its tests stay in |
| REQ-EVL-011 | partly | owner 2026-11-01 (D-172): the older suite kinds still run the in-process Core: TD-08 with FB-03; workflow targets run through IF-105 |
| REQ-CLV-002 | partly | owner 2026-11-01 (D-172, D-167): a late `chat_start` can shift the counted waiting places: FB-06; the waiting text and its count stay in |
| REQ-CHA-005 | partly | owner 2026-11-01 (D-173): deleting the history after a confirmation is out: TD-09; the bound on the history stays in |
| REQ-CHA-008 | partly | owner 2026-11-01 (D-173): AC-8 (the check dialogues) comes after the field test: TD-10; the persona mechanism and its tests stay in |
| REQ-WFM-022 | out | owner 2026-11-01 (D-173): optional and off by default (FR-13, AC-26); back in a later goal with the review pipeline it depends on |
| REQ-VOI-001 | partly | owner 2026-11-01 (D-173): the app speaks through SpeechStreamer; the chat audio through IF-204 and `audio_chunk` is TD-11; the sentence-by-sentence synthesis and the markup filter stay in |
| REQ-GA-001 | out | owner 2026-11-01 (D-177): the T-01 mockup stays as it is; TC-GA-001 (the owner's demonstration) is not part of G-V1; back with the redesign of the Graph app in the next iteration (FB-02) |
| REQ-GA-004 | out | owner 2026-11-01 (D-177): versions, history, diff and restore in the app (T-03); back with the redesign of the Graph app in the next iteration (FB-02) |
| REQ-GA-005 | out | owner 2026-11-01 (D-177): the app's calls through IF-104 and its login (T-04); back with the redesign of the Graph app in the next iteration (FB-02) |
| REQ-GA-006 | out | owner 2026-11-01 (D-177): context graphs edited in the app (T-03); back with the redesign of the Graph app in the next iteration (FB-02) |
| REQ-GA-007 | out | owner 2026-11-01 (D-177): the app's login page (T-04); back with the redesign of the Graph app in the next iteration (FB-02) |
| REQ-GA-008 | out | owner 2026-11-01 (D-177): library export and seed in the app (T-05); back with the redesign of the Graph app in the next iteration (FB-02) |
| REQ-GA-009 | out | owner 2026-11-01 (D-177): the node as a whole moves; the plain-stack files and their tests (`graph-app-files.test.mjs`) stay and keep passing; the library choice is part of the redesign |
| REQ-GA-010 | out | owner 2026-11-01 (D-177): as REQ-GA-009; the static no-outside-address test stays, the headless-browser test (TC-GA-010) is not built |
| REQ-GA-011 | out | owner 2026-11-01 (D-177): the `graph` service in `deploy/compose.yaml` stays (N-4.2); TC-GA-011 (stage 3) is not part of G-V1 |
| REQ-GA-002 | out | owner 2026-10-31 (D-135, D-177): N-5 T-02 (edit as JSON) waits for FB-02 (the graph form and the rules may change); back in the next iteration with the redesign |
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
| Plan | done | plan package approved, tags `plan-baseline-it1` and `decomp-baseline`; changes since then are amendments A-01 to A-86 (see `specs/mia/amendments/` and the review log; A-72 to A-85 installed on 2026-11-01) |
| Implement | in progress | node cycles of `decomposition.yaml`; open nodes and work in `handover-2026-10-31-late.md`. 2026-10-31: N-2.4.1 T-01 to T-05, T-07 done (T-06 out with REQ-RUN-007, T-08 deferred to the next iteration, D-128; fixes of three verification rounds, N-2.4.1 **Verified with findings** (re-verification 2, the D-128 scope rows written by D-130); N-2.4.2 **Verified with findings** (owner, D-134); N-2.4.3 and N-4.2 **Verified with accepted deviations** (owner, D-148); N-1.3 waits for the owner's checks by ear; N-2.1 Verify: not verified yet (D-147 A-52, findings V-0 to V-11)); N-2.4.2 T-01 to T-06 done (T-07 out with REQ-TLS-006); node Verifies of N-2.4.1 and N-2.4.2 started (reports in their node folders); only N-3 integrated (`tests/helpers/integration.py` READY) |
| Verify | done | `specs/mia/verification-report.md` (reviewer in a fresh context, commit e4dbbef): **Verified with accepted deviations**, approved by the owner Stefan Reiterer on 2026-11-01 (D-183) after his decisions D-180 to D-182 on the findings; the gate steps are in `goals/G-V1/merge-request.md` |
| Commit | done | goal/v1 merged into master by fast-forward on 2026-11-01, merge commit `67818fb`, tag `v0.1.0` (annotated, by the owner). Local merge gate on `67818fb`: stages 0 to 3 green (no CI, `--allow-local`), approved by the owner; `smoke` left the gate with A-88 (TD-25, D-182); verification report approved (D-183). Not pushed yet |
| Deploy | done | `goals/G-V1/deployment-record.md` (2026-11-02, owner's workstation): preflight and pins green, SMOKE-MIA-001, -003 and SMOKE-GATE-001/-002 green, recovery check and rollback to `mia:pre-v0.1.0` tested; **SMOKE-MIA-002 (Tailscale) not run** by the owner's decision (NFR-6, CON-5 evidence open); smoke eval only for the number gate; no voice lines in the image |
| Validate | closed, accepted as is, **not validated** | owner Stefan Reiterer, 2026-11-02 (D-185): v0.1.0 is accepted without the validation week because the skill rework (`specs/mia/skill_rework.md`) comes first. VAL-001 and VAL-003 to VAL-006 stay unrated and move to the exit criterion of the next goal; the check material is kept (`validation-plan.md`, `validation/VAL-003-check-sheet.md`); requirements stay `Verified`, none becomes `Validated`; FB-01 to FB-06 stay open; SMOKE-MIA-002 stays open (TD-26) |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
