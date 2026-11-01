# Verification report: node N-2.3 Workflow management, first Verify (2026-11-01)

**Verifier:** fresh session, branch `v1-n23-verify` from goal/v1 `d5e2268` (round 4 merged, A-64 to A-68 installed). I did not implement N-2.3. I changed no code, test, skill or suite; I ran no model and opened no holdout (CLAUDE.md). Mutants ran on a scratch copy in my scratchpad.
**Scope:** REQ-WFM-001 to -039 and IF-203. `goals/G-V1/goal.md` has no scope row for any of them, so all 39 are in G-V1. FB-01 will change REQ-WFM-031, -036, -038 and -039 (HLS iteration 1, Plan not done), so those four are verified as they stand today.

**Verdict proposal: Verified with accepted deviations, once the owner decides N1 to N3.** Every requirement that is a test, a code rule or an inspection has a passing test, and 9 of 12 mutants of the key rules were killed. But one requirement is neither built nor recorded (N1), four are model measurements that cannot be decided in G-V1 (N2), and 13 requirements and two deferrals are still unconfirmed (N3). If the owner does not accept them: **Not verified.**

## Automated results
| Check | Result |
|---|---|
| 50 Python files of the node in the image, from this worktree (`tools/run_in_image.sh`) | all OK, among them `test_workflow_library` 13, `test_review_stages` 26, `test_review_chat` 24, `test_review_score` 18, `test_verify_workflow` 4, `test_task_registry` 8, `test_task_monitor` 5, `test_review_run_mode` 10, `test_file_store` 7, `test_extension_loader` 8, `test_core_names_no_skill` 2, `test_number_gate` 45; contract suites IF-203 8, IF-302 14, IF-301 8, IF-104 10; protected `acceptance/test_workflow_library` 4. Skips: `test_seed_workflows` 3 (TD-06: `library/workflows` is missing) |
| JS tests (`node --test tests/js`) | 161 pass, 0 fail (includes `taskcard.test.mjs`) |
| Round-4 trial run on goal/v1 (earlier today) | 192 of 196 Python files OK; the 4 failures are not this node's |
| `trace_check.py` | no ERROR for N-2.3. WARN: 23 requirements have no `req` marker (REQ-WFM-001, -005 to -010, -016, -019 to -021, -027 to -037, -039). WARN: TD-03 and TD-04 are not listed in this node's report (listed below) |
| Protected material | IF-203 contract suite: only A-14 (real provider) since the plan commit; mock: unchanged; contract text: unchanged since the plan; `acceptance/test_workflow_library.py`: A-22/A-24 install. Commits on `tests/helpers/contract.py` since the baseline are all amendment installs except `7d6f3d6 added A-1 to A-3 files` (plan stage, before the baseline work) |
| Code against architecture | the storage check holds (`test_workflow_storage_imports`); the core names no skill (`test_core_names_no_skill`); `extensions/{lookup,search,review}` have a manifest and an entry |
| Static analysis, security scan, `test_doc_check` for this node | not run for this node (no checker configured; `test_doc_check` has about 2600 errors repo-wide, not counted per node) |

## Mutants (scratch copy, only the tests of the changed module)
Killed (9): a term proposed at 2 works instead of 3 (W1); the time cut-off not applied (W2); works not deduplicated (W4); a budget equal to the estimate counted as exceeded (W5); the cost of a session ignores `max_cycles` (W6); the hard cap factor of the run mode dropped (W7); a file over the limit stored (W8); the volume limit not enforced (W9); the "thin" threshold moved from 3 to 2 (W10).
**Survived (3):** W3, withdrawn works are kept (only retracted works are tested; REQ-WFM-021 names retracted works); W11, "good" coverage at 5 included works instead of 8 (the thresholds are start values: the log asks for more cases); W12, the cap of 10 domain experts raised to 99 (no test of the upper bound).
Not mutated by me: the verify workflow's order of code check and judge (tested by event positions), the task monitor, the model gate, pause and resume, the report record, the extension loader.

## Verification matrix
| Requirement | Method | Evidence | Result |
|---|---|---|---|
| REQ-WFM-001 skills as tasks | Test | `test_skills_as_tasks`, `test_task_registry` | verified |
| REQ-WFM-002 to -004, -026 versioned library, no cycles, graph rules, API | Test | `test_workflow_library`, `test_graph_rules`, IF-203/IF-301/IF-104 contracts | verified |
| REQ-WFM-005 drafts, -006 specification before trust, -007 time record | Test | `test_workflow_library`, `test_record_tables` | verified (A-16 narrowed -006 to specification and benchmark, decided by the owner 2026-10-27) |
| REQ-WFM-008 context graphs | Test | `test_workflow_library`; the stored record is the design-time template (owner 2026-10-27) | verified; the content waits for the Graph app (D-108) |
| REQ-WFM-009 schedule and estimate | Test | `check_budget`, W5 and W6 killed | verified |
| REQ-WFM-010 variant per workflow | Test | `test_workflow_library` | verified |
| REQ-WFM-011 to -013 code checks first, unclear without evidence, failed check informs the judge | Test | `test_verify_workflow` 4 (order by event positions; ten number claims without evidence give "unclear" without a model call; the contradiction reaches the judge) | verified |
| REQ-WFM-014 verify beats single | Measurement | dev numbers of the implementer (gate 0 of 36 wrong claims passed against 2 for single; true claims not passed 9 against 10 of 52): feedback only | **not decided** (N2; D-164 moved gate versus single to the next iteration's Plan) |
| REQ-WFM-015 stable verdicts | Measurement | none on a holdout; limit 0.90 on dev suites | **not decided** (N2) |
| REQ-WFM-016 lookup with sources | Test, Measurement | no test names it; the extension is covered through `test_research_command` and `test_tool_calls_lookup` | **not decided** (N2) |
| REQ-WFM-017 search command | Test | `test_search_command` 3 (written after the fact), `test_research_command` | verified |
| REQ-WFM-018 review report | Test | `test_review_entry`, `test_review_chat` (`format_report`) | verified; the quality of a real report is the owner's reading |
| REQ-WFM-019 stages, run mode, slices | Test | `test_review_stages`, `test_review_run_mode`, `test_chat_review`, `test_review_request` | verified |
| REQ-WFM-020 stops by a code check | Test | `test_review_stages` (TC-WFM-020: a fake model that always says done) | verified |
| REQ-WFM-021 source records, cut-off | Test | `test_review_stages` (TC-WFM-021); W2 and W4 killed | verified; W3 survives (N5) |
| REQ-WFM-022 method transfer | Measurement | none: no code, no test, no library entry | **not built, not recorded** (N1) |
| REQ-WFM-023 confidence by code | Test | `test_gate_limits` 6 (the limits and the basis of the confidence come from code) | verified |
| REQ-WFM-024 no invented source | Measurement | the tool layer checks quotes (`test_web_tools`); no holdout of the lookup or review suites | **not decided** (N2) |
| REQ-WFM-025 storage only through IF-102 | Inspection, Test | `test_workflow_storage_imports` | verified |
| REQ-WFM-027 keyword extension with approval, -028 staged screening | Test | `test_review_stages` (a term below N never proposed, approval needed), `test_fulltext_*`, `test_review_skills`; W1 killed | verified (status Draft) |
| REQ-WFM-029 to -031 skill id, options, task monitor | Test | `test_task_registry`, `test_task_monitor`, `test_chat_tasks`, `taskcard.test.mjs`, IF-101 contract | verified (status Draft); the card in a browser is N-1.1's check |
| REQ-WFM-032 figures of the review | Test | `test_review_run_mode`; tokens are an estimate (characters / 4) | verified with TD-03 |
| REQ-WFM-033 pause and resume | Test | `test_task_monitor`, IF-101 contract | verified |
| REQ-WFM-034 run mode, hard caps | Test | `test_review_run_mode`; W7 killed | verified |
| REQ-WFM-035 class of the model | Test | `test_model_class`, `test_model_gate` | verified |
| REQ-WFM-036 result at the end of the chat, -037 files volume, -038 report record | Test | `test_chat_tasks`, `test_file_store`, `test_files_api`, `test_report_tex`, `test_record_tables`; W8, W9 killed | verified (FB-01 will change -036 and -038) |
| REQ-WFM-039 skills are self-contained extensions | Inspection, Test | `test_extension_loader`, `test_core_names_no_skill` | verified with TD-04 |
| IF-203 | Test | contract suite 8 OK against mock and the real library | verified |

## Agent checks
- **A. Protected eval material:** unchanged for this node since the baseline.
- **C. Suites:** none run. REQ-WFM-014, -015, -016, -024 and -022 are decided on suites; there is no holdout for the lookup and review suites (`eval-spec.md` gap, "Owner"), and an agent does not run a holdout.
- **D. Red team and trust boundaries:** read by test only: web and file text is untrusted data (`test_fulltext_source` lists injection-like phrases as signals, `test_web_tools`). The step list of the review (`@ModelStep`, budgets) was not re-read.
- **F2. Prompts against the specification:** not done for the review skills (v2 from two labelled cases, RVP-001 and RVP-002); that reading belongs with the owner's labels.
- **Plausibility:** the implementer's dev figures are reported as feedback; no result better than its method allows was seen.

## Open deferrals
TD-03 (REQ-WFM-032, tokens on the card are an estimate) and TD-04 (REQ-WFM-039, glue of lookup and search stays in the core): both "proposed 2026-10-29, to be confirmed", status open; interim criteria verified as above. TD-06 (library folder missing, REQ-GTB-004) shows as the 3 skips of `test_seed_workflows`.

## Findings
| ID | Severity | Finding | Destination |
|---|---|---|---|
| N1 | medium | REQ-WFM-022 (method transfer, optional, "where switched on", FR-13, AC-26) has no code, no test and no library entry, and neither a scope row in `goal.md` nor a deferral. It is Approved. | Plan: scope row "out" (or a TD) |
| N2 | medium | REQ-WFM-014, -015, -016 and -024 are model measurements decided on holdouts. No lookup or review suite has a holdout, so a decision in G-V1 is impossible; the dev numbers are feedback on tuned cases. REQ-WFM-016 has no test at all that names it. | Plan: scope rows "partly" with the eval-spec decisions of the next iteration (D-164 already moved gate versus single) |
| N3 | medium | REQ-WFM-027 to -039 (13 requirements) are still `Draft`, and TD-03 and TD-04 are "to be confirmed". FB-01 changes four of them. | Owner: approve or amend after the FB-01 Plan; confirm TD-03, TD-04 |
| N4 | low | 23 requirements have no `req` marker though tests exist (trace WARN). | Implement: markers |
| N5 | low | Three mutants survive: withdrawn works kept (REQ-WFM-021), coverage level "good" at 5 works, the cap of domain experts. | Implement: three small tests; W11 waits for the thresholds on more cases |
| N6 | low | The review's glue (lookup, search) imports `research_chat` from the core; the page parts of the card and the Files tab are tested in JS but not in a browser by this node (N-1.1 owns the browser test). | TD-04; N-1.1 |
| N7 | info | The tokens of a review are an estimate; hard caps and the run-mode factor 10 are the owner's start values. | TD-03; field test |

No blocker. Nothing goes back to Implement except N4 and N5.

## What I could not check
The whole chain with the real model through the page (the owner's hand test); a real full-text run on an open-access work (needs the host with the wall and network); the quality of review reports and of the review prompts; AC-26; the browser view of the card; static and security tools; the step list and budgets of the review against `architecture.sysml`.

## For the team
Decide N1 to N3 in one questionnaire. After the FB-01 Plan the four changed requirements (-031, -036, -038, -039) need a second look.
