# G-V1: first version of MIA, merge request (DRAFT, v0.1.0 proposed)

**Draft of 2026-11-01. Do not merge before the verification report is approved.** Written by the coding agent from the repository; the human reads, completes the marked blanks (`<<...>>`) and merges.

**Goal:** G-V1 (iteration, supervised)   **Branch:** goal/v1 → master (the project's main branch)
**Accepted by:** Stefan Reiterer (owner; supervised goal, a person merges and tags)
**HLS:** specs/mia/high-level-spec.md
**Goal record:** specs/mia/goals/G-V1/goal.md
**Plan:** specs/mia/plan.md and the node plans below specs/mia/nodes/
**Verification report:** specs/mia/verification-report.md (verdict proposal: **Verified with accepted deviations, conditional on the owner's decisions D-1 to D-9 of the report**; reviewer in a fresh context, commit e4dbbef; the owner's decisions on the findings are D-180, the report is not yet approved)
**Implementation logs:** specs/mia/nodes/*/implementation-log.md, specs/mia/integration-log.md and the integration logs of N-1, N-2, N-4

### What changes
MIA as the decomposed multi-user system of the approved HLS (2026-10-24): one tree: the root N-0, 5 high-level nodes (N-1 to N-5) and 13 low-level nodes, one of them (N-2.4) cut again into N-2.4.1 to N-2.4.3.
- **N-1 Web Frontend:** chat and login views (N-1.1), the character view with the Godot bridge (N-1.2), voice playback (N-1.3).
- **N-2 Backend:** API and accounts (N-2.1), chat agent (N-2.2), workflow management (N-2.3), workflow execution with the pipeline runner, tools and sandbox, and the run log (N-2.4.1 to N-2.4.3), voice synthesis (N-2.5).
- **N-3 Database:** storage layer (N-3.1, files and PostgreSQL), graph tables (N-3.2), record tables (N-3.3). **The app keeps its state in the file backend**; wiring it to PostgreSQL is deferred (TD-21).
- **N-4 Evaluation and operation:** the evaluation harness behind IF-105 (N-4.1), the compose stack, backup, shutdown and configuration (N-4.2).
- **N-5 Graph app:** not part of this release (D-177); the static T-01 mockup page and its `graph` container stay as they are.
- **Integration:** N-1 (A-72 to A-74), N-2 (A-77 to A-80, with A-55 for N-2.4), N-3 (A-02), N-4 (A-75, A-76); the root scenario runs with every Python node real (N-0 steps 02 to 04, A-81). N-0 step 05 stays a skip (N-5).
- **Scope of this request:** goal/v1 is ahead of master by `git rev-list --count master..goal/v1` commits (47 on 2026-11-01). Master took the earlier merge rounds of the goal (`git rev-list --count 53c6766..master` = 400); the whole goal is the history since 53c6766, `git diff --stat master...goal/v1` is the open delta (87 files on 2026-11-01: A-72 to A-86, the verification report and deferral records, D-137 to D-180).

### Requirements implemented
Nodes and their verification state (the reports are in each node folder; N-2.1, N-2.2, N-2.3, N-2.5 proposed their verdict "once the owner decides", the owner's answers are D-173):

| Node | Verdict | Report |
|---|---|---|
| N-1.1 Chat and login views | Verified with accepted deviations | nodes/N-1-web-frontend/nodes/N-1.1-chat-and-login-views/verification-report.md |
| N-1.2 Character view | Verified with accepted deviations, provided the owner decided R1 (D-155, D-172) | .../N-1.2-character-view/ |
| N-1.3 Voice playback | Verified with accepted deviations (re-verification 4) | .../N-1.3-voice-playback/ |
| N-2.1 API and accounts | Verified with accepted deviations (D-173) | nodes/N-2-backend/nodes/N-2.1-api-and-accounts/ |
| N-2.2 Chat agent | Verified with accepted deviations (D-173) | .../N-2.2-chat-agent/ |
| N-2.3 Workflow management | Verified with accepted deviations (D-173) | .../N-2.3-workflow-management/ |
| N-2.4.1 Pipeline runner | Verified with findings | .../N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/ |
| N-2.4.2 Tools and sandbox | Verified with findings | .../N-2.4.2-tools-and-sandbox/ |
| N-2.4.3 Run log | Verified with accepted deviations | .../N-2.4.3-run-log/ |
| N-2.5 Voice synthesis | Verified with accepted deviations (D-173) | .../N-2.5-voice-synthesis/ |
| N-3.1, N-3.2, N-3.3 | Verified with accepted deviations | nodes/N-3-database/nodes/ |
| N-4.1 Evaluation, N-4.2 Operation | Verified with accepted deviations | nodes/N-4-evaluation-operation/nodes/ |
| N-5 Graph app | out of G-V1 (D-177) | – |

The "with findings" verdicts of N-2.4.1 and N-2.4.2 are deviation D-7 of the verification report: the owner accepts them with the report. The status of the root checks is in specs/mia/tc-mia-status.md (A-82).

### Plan amendments
A-01 to A-86 (`specs/mia/amendments/`, decisions in `specs/mia/review-log.md`). Installed by the owner: all up to A-85; A-86 (TD-21, TD-22) is drafted. No joint amendment of a frozen requirement (the goal has no subgoals).

### Frozen requirements unchanged (goal_check.py --parent-ref)
The goal has no parent and no frozen requirements (`goal_check.py --spec-dir specs/mia`: 0 errors, 0 warnings on 2026-11-01).

### Resolved feedback items
None resolved in this release. FB-01 to FB-06 are *Triaged* and go to the next iteration: FB-01 skills panel, FB-02 graph objects and the graph app redesign, FB-03 re-specify the workflow pipelines, FB-04 importers for outside data, FB-05 votes on reactions and the series, FB-06 queue places from the server.

### Known issues / accepted deviations
- **Failing test files, known:** `tests/test_amendment_report.py` (no git in the image), `tests/test_harness.py` (rt_edit has 2 cases, wants 30), `tests/acceptance/test_benchmarks.py` (the gate-time baseline was never measured); `tests/test_author_in_records.py` failed once in a full run and passes alone.
- **Skips by design:** N-0 step 05 (N-5); IF-201 keeps 1 and IF-101 2 skipped cases (`audio_chunk` and `expression` events of an answer not built, TD-11, D-173; REQ-CHV-008 out); the JS real cases of IF-111 (the real side is `ui/godot/tools/test_bridge.gd`, D-155, D-175); N-1.1, N-4.1, N-4.2 integration steps add no coverage over their own tests (D-176).
- **Trace check:** 46 to 48 error lines depending on the open sign-off of TD-22 (known: missing `## Scenarios` sections in about 20 test-specs and others), ~290 warnings.
- **Environment:** the IF-101 and IF-104 real suites and N-2 step 05 / N-0 step 04 need flask (the image or the requirements venv).
- **Not met or not held:** NFR-8 and CON-7 (state in PostgreSQL, TD-21); the red-team half of TC-MIA-006 (TD-22); no `test-requirements.md`; 36 `eval/suites` files added by `271176c` without an amendment (owner confirms the labels, D-180); the contract suites of IF-103, IF-404, IF-405 have no real side (F-03).
- **Not decided here:** nine stage 4 checks (TC-MIA-002, -003, -009, -011, -019, -022, -024, -025, -028) are deferred (TD-12 to TD-20, D-178); VAL-001 and VAL-003 to VAL-006 are field validation.

Open deferrals:

| Record | Subject | Requirement | Trigger |
|---|---|---|---|
| TD-01 | The status card is not tested in a browser and is gone after a reload | REQ-CLV-023 | the chat mock server sends `task_status` and files events, or the Plan of FB-01, or 2026-12-31, whichever first (the browser harness exists since D-141; D-172) |
| TD-02 | The Files tab is not tested in a browser | REQ-CLV-024 | the chat mock server sends `task_status` and files events, or the Plan of FB-01, or 2026-12-31, whichever first (the browser harness exists since D-141; D-172) |
| TD-03 | Tokens on the card are an estimate | REQ-WFM-032 | the first review run that ends at the cap of tokens, or 2026-12-31, whichever first |
| TD-04 | The glue of lookup and search stays in the core | REQ-WFM-039 | the fourth skill is added, or 2026-12-31, whichever first |
| TD-06 | The workflow library folder is not there yet | REQ-GTB-004 | root task T-10, or 2026-12-31, whichever first |
| TD-07 | Judge calibrations are not loaded yet | REQ-EVL-003 | the first eval target with a judge, or 2026-12-31, whichever first |
| TD-08 | Older eval suite kinds run the in-process Core | REQ-EVL-011 | the Plan of FB-03, or 2026-12-31, whichever first |
| TD-09 | Deleting the chat history after a confirmation | REQ-CHA-005 | the first request to delete a history, or 2026-12-31, whichever first |
| TD-10 | Persona check dialogues (AC-8) | REQ-CHA-008 | the first iteration after the field test |
| TD-11 | The voice goes through IF-204 | REQ-VOI-001 | the Plan of the next iteration, or 2026-12-31, whichever first |
| TD-12 | Verify before asserting; lookup (TC-MIA-002) | FR-9, FR-10 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-13 | Literature review quality (TC-MIA-003) | FR-11, FR-12, NFR-4 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-14 | The skill path (TC-MIA-009) | FR-20 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-15 | Adaptation to negative feedback (TC-MIA-011) | FR-29 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-16 | Speed and frame rate (TC-MIA-019) | NFR-7 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-17 | Cost of the first try; comparing variants; learned choices (TC-MIA-022) | NFR-2, FR-17, FR-18 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-18 | Memory that improves (TC-MIA-024) | FR-14 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-19 | Speech rules (TC-MIA-025) | FR-15 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-20 | Estimate before a run (TC-MIA-028) | FR-33 | the Plan of the next iteration (eval-spec.md with criteria, suites and pins), or 2026-12-31, whichever first |
| TD-21 | The state is in PostgreSQL | NFR-8, CON-7 | the Plan of the next iteration, or 2026-12-31, whichever first |
| TD-22 | Red-team cases of the untrusted inputs | NFR-3 | the Plan of the next iteration, or 2026-12-31, whichever first |

Out of scope or partly in scope (from goal.md):

| Item | In/Out | Reason |
|---|---|---|
| FR-22 | out | owner 2026-11-01 (D-177): the Graph app N-5 moves to the next iteration and is redesigned with FB-02; its requirements REQ-GA-001 to -011 are out (below). What stays: the backend routes of IF-104 and the graph tables (N-2.1, N-3.2), the static page `graph_app/` and its `graph` container as they are |
| FR-34 | out | FB-01, HLS iteration 1, still waiting for the HLS gate; it becomes its own goal once the gate is approved |
| FR-35 | out | FB-01, as FR-34 |
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

### Conflict resolutions after rebase
master is 3 commits ahead of goal/v1 (merges and the report of the N-1.3 re-verification 4, one file). A trial merge (`git merge-tree`) of master into goal/v1 on 2026-11-01 is clean. <<Redo after the last change; note any resolution here.>>

### Agent changes
(from `agent-app-commit/assets/release-notes-agent.md`; no eval decided for this release)

**Models.** MP-light = `gemma4:12b-it-qat`, digest `sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3` (`tools/eval.py` PINS, seed 7, temperature 0), unchanged; MP-full = `gemma4:26b` (`sha256:001e5dafc3c7...`, not used for criteria in G-V1); both pins are in the drafts `specs/mia/eval-spec.md` and `specs/number-gate/eval-spec.md` (not approved), `tools/eval.py` PINS holds MP-light only; `num_ctx` 8192 is configuration (CLAUDE.md). <<Check the digests on the reference host before the tag: `ollama show`.>>

**Skills and pipelines (since plan-baseline-it1).**

| Skill / pipeline | Old | New | What changed |
|---|---|---|---|
| skill chat | 1 | 2 | the conversation runs on the pipeline runner |
| skill memory_write | new | 7 | the memory-writing skill |
| skills review_abstract, review_section, review_summary | new | 1 | literature-review steps |
| skills review_full, review_keywords | new | 2 | literature-review steps |
| pipeline memory.write | new | 5 | |
| pipelines review.abstract, review.section, review.summary | new | 1 | |
| pipelines review.full, review.keywords | new | 2 | |
| pipeline verify.number_gate | new | 5 | the number gate |

The review entry itself is out of G-V1 (REQ-RUN-013 partly, D-128, D-130). Versions come from the front matter and the file names; the reviewer checks that every change of a prompt, schema, tool, budget or graph has its bump (agent-app-verify A).

**Eval results (holdout).** None: the stage 4 checks are deferred (D-178). Release notes must not say "better" for any agent behaviour.

**Red-team and budgets.** Not run (the stage 4 evals and the red-team half of TC-MIA-006 are deferred, TD-12 to TD-22); the verification report records what was and was not measured.

**Baselines.** No new baseline files; `eval/baselines/` is unchanged. After the merge the deciding runs would be copied there (agent-app-commit step 4): there are none to copy.

**For deployment.** Pull models by digest; services: SearXNG, the sandbox, the compose stack of `deploy/compose.yaml`; smoke eval: none defined yet.

### Steps for the human
1. Approve the verification report; run `merge_gate.py --approved-by "<name>"` (only a person supplies the name).
2. Update goal/v1 with master (`git merge master`), re-run stages 1 to 3 in CI, redo the trial merge line above.
3. Merge into master, check CI on master (red: revert first).
4. Tag the version you choose (proposal `v0.1.0`: first version, not yet validated; the exit criteria VAL-001, VAL-003 to VAL-006 are field checks) and let CI build the artifact from the tag. **`deploy/build.sh` does not exist** (Deploy finding): the image is built from `deploy/Containerfile`.
5. Copy `release-notes.md` and `CHANGELOG.md` entries (drafts in this folder and the repository root), set the requirement statuses (Implemented → Verified) and the goal record (Commit: done, merge commit).
