# Verification report: Evaluation (N-4.1)

**Goal:** G-V1 (iteration), node N-4.1 (leaf), supervised
**Branch:** goal/v1 @ 424c329 (started at a262376; the two later commits touch no N-4.1 file)   **Parent line of work:** master   **Plan baseline:** plan-baseline-it1
**Node commits:** bf4032f (T-01), 805da4a (T-05), c301c73 (T-02), cf0c2e0 (T-03), 3275ba1 (T-04), 61a8fe3 (T-06), 00cceae (gaps); T-07 not built
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 as independent reviewer (AI; never saw the implementation chat)

## Verdict
Proposed: **Not verified.** What is built for the harness (REQ-EVL-001, -002, -003, -004, -006, -008) works on the mock of IF-105 and its tests can fail (13 of 17 mutants killed). But:
- the live mode of the latency tool measures the wrong thing (F1, reproduced),
- the IF-105 adapter sends the model name where IF-105 wants the pin id, so the real Backend would refuse every run (F2, reproduced),
- the IF-105 path is reachable only from tests, and the harness targets in use today record neither the workflow version nor the model pin (F3; finding F-1 of the log is still waiting for an owner decision),
- REQ-EVL-005, -009 and -010 are not met on this branch (F4, T-07).

No dev-split eval run was needed or made: every requirement could be judged from code, fake-model tests and `agent_check.py`.

## Automated checks (local runs of the reviewer, no CI)
| Check | Result |
|---|---|
| Stage log | No CI run for this node. The reviewer's own runs below are the evidence. |
| Node tests in the image (`bash tools/run_in_image.sh`) | `test_eval_platform` 7 OK, `test_decide_guard` 5 OK (1 skipped: `eval_decide.py` of the skill is not in the image), `test_judge_calibration` 4 OK, `test_check_baselines` 3 OK, `test_skill_path_doc` 4 OK, `test_measure_latency` 2 OK, `test_metrics` 22 OK, `tests/acceptance/test_harness_pin.py` 5 OK; `test_harness` 28 with 1 failure (`test_every_shipped_suite_is_valid`, rt_edit: the known failure) |
| Host run | `test_decide_guard` 5 OK, none skipped: the real `eval_decide.py` decides PASS and FAIL through the guard |
| JS | `node --test tests/js/measure-fps.test.mjs`: 3 pass |
| Contract suite IF-105 | `tests/acceptance/contract/test_if_105_evaluation_access.py`: 8 OK, mock and real (`run_workflow.WorkflowRuns`, A-31), none skipped |
| Integration | N-4 step_00 OK; step_01, step_02 skipped ("N-4.1 not integrated yet"). N-0 step_00, step_01 OK; step_02 to step_05 skipped. Note: N-4's scenario calls IF-105 directly and never the harness, so step_01 would not test N-4.1's code either (see F3). |
| Mutation (scratch copy, removed) | 17 mutants. **Killed (13):** holdout filter in `Suite.select`; guard accepts every run; kappa `>` instead of `>=`; kappa limit 0.5; repeats check and case-id check of `require_same_cases`; one repeat only; no `benchmark_version`; seed not passed to IF-105; cost of the run ignored; workflow suite without a pin accepted; status filter of `check_baselines`; the counted filter of `match_metrics`. **Survived (4):** `Harness.run` no longer marks judge verdicts (harness.py:452; only the known rt_edit failure); the counted filter of `verification_metrics` (metrics.py:60); the counted check of `is_right` (metrics.py:98); the partial-pin check of `WorkflowTarget` (eval_platform.py:18). |
| Holdout guard, synthetic fixture (scratchpad, removed; no real holdout opened) | `Suite.select` keeps `split:holdout` cases out of a dev suite, also with `--only`. `tools/decide_guard.py` refuses a dev run and a mix. But `--split dev` passed through the guard decides on dev records (PASS), and `--rerun` files are not checked (F5a). `tools/eval.py list` loads and counts `*.holdout` suites, `cases toy.holdout` prints the holdout case ids, truth and notes, `run toy.holdout` would run it: none of them asks for a flag (F5b). |
| Protected material | N-4.1's seven commits touch no protected path (`git show --stat`). `tests/acceptance/contract/test_if_105_evaluation_access.py` and `tests/helpers/mocks/if_105_evaluation_access.py` are byte-identical to their drafts in `specs/mia/contract-drafts/`. No change under `eval/suites` or `eval/baselines` comes from a node commit. |
| Traceability (`trace_check.py`) | Exit 1, 96 errors over the whole spec. N-4.1 lines: ERROR "test-spec.md: 11 check(s) but no '## Scenarios' section" (M39, plan-level, same for N-4 and N-4.2); WARN REQ-EVL-010 has no marker (T-07 not built). No test-requirements.md exists (no TR items). |
| `test_doc_check.py` on the node's six test files | 34 errors (T1 no docstring, T2 no `Example:` line, T3 no Given/When/Then), e.g. tests/test_eval_platform.py:73, :87, :94. The JS test: 0. |
| `agent_check.py --spec-dir specs/mia --eval-dir eval` | Exit 1: 2 errors (A9, A10 on `SkillDigestStep`, not N-4.1), 640 warnings: A6 on 10 suites (no dev/holdout tags, no holdout case: among them `research` = lookup and `verdicts` = verify), 620 A7 (`req:REQ-VER-*` not in requirements.md). |
| Model consistency (`check_sysml_model.py`) | OK |
| Static / security | No linter configured (CLAUDE.md). Manual: `decide_guard.py` runs `eval_decide.py` with a list and `-I` (no shell); `check_baselines.py` is read-only; `measure_latency.py` takes the password on the command line (visible in `ps`; personal use, low). |
| Usability (bad inputs) | `decide_guard.py` with no run: "NOT DECIDED: no run given", exit 2; `eval.py compare` with different case lists: "not compared: ..." with the case names; `check_baselines.py` names each workflow and why; `measure_fps.mjs` with no frames: error. A `--run=path` form is silently passed through (harmless: filtered by `--split holdout`). |

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-EVL-001 harness with repeats | Test | `test_eval_platform` TC-EVL-001: 5 cases × 3, 12/15, Wilson 0.55–0.93 (checked by hand: 0.548–0.930), 45 calls, 27000 tokens, 135 s; per-case table in the report; mutants killed | **Pass on the mock only**: no production path builds `Harness(platform=...)` (tools/eval.py:146), so no workflow suite can run from the command line (F3) | yes |
| REQ-EVL-002 decisions on held-out cases | Inspection, Test | `test_decide_guard` (5, host, real `eval_decide.py`); `Suite.select` filter; mutants killed; synthetic fixture | **Pass, with gaps F5** | yes |
| REQ-EVL-003 judge calibration | Test | `test_judge_calibration` (4): no record, 0.7, 0.4, the limit 0.6 | **Pass at unit level**; inert: nothing sets `judge` on a record and `load_calibrations` is never called (log says so; eval-spec.md: no judge in G-V1); 3 surviving mutants (F6) | yes |
| REQ-EVL-004 versions per run | Test | TC-EVL-004: 10 workflow runs carry workflow, version, pin, seed, temperature, benchmark version | **Partly**: only for the `workflow` kind. The kinds in use (`research` = lookup, `pipeline`, `checks`) record no pin unless `--pin`, and `research` records no workflow/pipeline version (harness.py:430–443) (F3) | yes |
| REQ-EVL-005 baseline per shipped workflow | Inspection | `tools/check_baselines.py` (3 tests, mutant killed); run on the branch: 5 tested/trusted workflows without a baseline, `library/baselines.json` missing | **Fail on the branch** (tool works; the baselines and the link are the owner's/Plan's) (F4) | – |
| REQ-EVL-006 skill path documented | Inspection, doc test | `docs/skill-path.md` read: 7 steps, lookup (`research.*`) as the example; `test_skill_path_doc` 4 OK in the image (marked examples run, links resolve) | **Pass** (the idea date is stored nowhere: FR-20 note of the log, N-2.3) | yes |
| REQ-EVL-007 latency and frame rate | Measurement | `test_measure_latency` (2), `measure-fps.test.mjs` (3): the median logic is right; reviewer probe of the live mode | **Fail**: the live mode times the end of the previous answer (F1); BM-MIA-001/-002 not measured; no frame recorder (accepted risk VAL-006 for the figures, not for the tool) | the log's 5.0 s vs < 1 s probe is explained by F1 |
| REQ-EVL-008 equal cases | Test | TC-EVL-008: same ids compared, different refused with "c2" named, different repeats refused; mutants killed; CLI refuses | **Pass** (F8 low) | yes |
| REQ-EVL-009 benchmarks of lookup and verify | Inspection | `agent_check.py`: `research` and `verdicts` have no holdout case (A6); `eval/baselines/` holds `.md` reports, no `.jsonl`; eval-spec.md is a draft whose holdout cases are "proposed" | **Fail / open** (owner: holdout cases, baselines, eval-spec gate) (F4) | – |
| REQ-EVL-010 proof of concept | Test, Demonstration | T-07 not built; N-0 step_02–05 skipped; no marker | **Open** | – |
| REQ-EVL-011 only through IF-105 | Inspection, Test | TC-EVL-011: `eval_platform.py` imports only the standard library (ast check); `harness.py` imports `pipeline.Tool`, `behaviour`, `checks`, `extraction`, `plans`, `research_score`, `web_tools` and drives the in-process Core | **Partly** (F-1 of the log, undecided; F3) | yes |

## Test requirements (M41)
No `test-requirements.md` exists in `specs/mia/` (plan-level gap, shared with every node). The settings of the node's checks are in test-spec.md: TC-EVL-001 (5 cases, 3 repeats, Wilson, two decimals) met; TC-EVL-004 (10 runs) met; TC-EVL-007 (1/2/3 s cycling, 20 after 3 warm-up, ±0.1 s; 16.7 and 33.3 ms, ±1 fps) met for the unit part. Fidelity of the IF-105 mock: contract suite green against mock and real. The harness test's `PIN` uses `"name": "MP-light"`, a shape that neither `tools/eval.py` (`name` = model tag) nor the real provider produces: this fake hid F2.

## Goal acceptance (M34, M36)
| Item | Result |
|---|---|
| Requirements of N-4.1 verified | 4 pass (002, 006, 008; 003 at unit level), 3 partly (001, 004, 011), 4 fail or open (005, 007, 009, 010) of 11 |
| Frozen requirements | none in G-V1 |
| Protected checks identical to the baseline | yes for N-4.1's commits (see above) |
| Nothing outside the node's parts touched | `harness.py`, `metrics.py`, `tools/`, `docs/`, own tests only; `tools/label_agreement.py` one function |
| Every stop condition logged | F-1 (REQ-EVL-011) logged as "needs an owner decision", not decided in review-log.md; the TC-EVL-009 sandbox refusal logged |
| Exit criterion | not judged here (goal-level) |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-EVL-001/-004/-011 for the suites in use | IF-105 path only in tests; old targets without pin/version | owner decision F3 |
| specified, not done | REQ-EVL-007 live measurement | timed region wrong (F1) | Phase 3 |
| specified, not done | REQ-EVL-005, -009, -010 | baselines, holdouts, T-07 | owner / Plan, T-07 |
| specified, not done | IF-105 `model_pin` = pin id | adapter sends the model name (F2) | Phase 3 |
| done, not specified | `library/baselines.json` as the workflow-to-baseline link (owner decision 2026-10-26 in the log, deviation from "a field" noted there) | not in a requirement or IF-203 | Phase 2 amendment (text) |
| done, not specified | `decide_guard.py` treats a run as holdout by suite name `.holdout` **or** all records tagged `split:holdout` | rule only in code | Phase 2 amendment (text), with F5 |
| done, not specified | calibration record format (`judge`, `kappa`, `n`, `against`), folder `data/eval/calibration/` (agent proposal), no minimum `n` | | Phase 2 when a judge is first used |

Human review: specification side via `review-log.md`; no item is marked `Code review: needed`.

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | EVL-001…011 | matrix above | partly | F1–F4 |
| Performance efficiency | EVL-007 | unit tests only | not measured | F1; figures: VAL-006 (accepted risk) |
| Compatibility | EVL-011, IF-105 | contract suite mock + real | partly | F2 |
| Interaction capability | CLI tools | bad-input checks above | ok | – |
| Reliability | EVL-002, -008 | guards, mutants | ok with F5 | – |
| Security | holdout separation, no shell | F5; manual | gaps | F5 |
| Maintainability | tests | 34 test_doc_check errors; 4 surviving mutants | gaps | F6, F10 |
| Flexibility | IF-105 adapter | mock and real interchangeable in principle | – | F2, F3 |
| Safety | – | not applicable (offline evaluation tooling) | – | not now |

## Open deferrals (M26)
None listed for N-4.1 in `deferred.md`.

## Review findings
| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F1 | **tools/measure_latency.py:24 and :60 – the timed region includes the end of the previous answer.** `measure()` starts the clock before `ask()`, and `ask()` first waits for the previous `chat_done` (added in 00cceae). Reviewer probe with a fake socket (first text after 0.1 s, end after 1.0 s, 4 runs): median **1.01 s**, true value 0.1 s. This explains the log's 5.0 s on the IF-101 mock against a probe under 1 s (blamed on long-polling). BM-MIA-001 measured with it would be inflated by the answer length. | High | Phase 3: regression test with a fake socket client (first delta ≠ end of answer), then wait for the previous end outside the timed part (e.g. a `prepare` hook before the clock starts). |
| F2 | **eval_platform.py:20 sends `pin["name"]` as IF-105 `model_pin`.** IF-105 (contract line 11, 28) and `run_workflow.WorkflowRuns` expect the pin id (`"MP-light"`); `tools/eval.py` PINS has `name` = `gemma4:12b-it-qat`. Probe: the real provider refuses with `pin_unavailable: gemma4:12b-it-qat`; with `MP-light` it accepts. The test's `PIN = {"name": "MP-light", ...}` (tests/test_eval_platform.py:25) hides it. | Medium | Phase 3: test against the real `WorkflowRuns` with the pin shape of `tools/eval.py`, then send the pin id (the pin needs an `id` field or the harness takes the id). |
| F3 | **REQ-EVL-001/-004/-011 hold only for the new `workflow` target, which nothing outside the tests uses.** tools/eval.py:146 builds `Harness(core)` without a platform; the suites of today (`research` = lookup, `pipeline`, `checks`) run on the in-process Core (harness.py:20–33 imports), record no pin without `--pin` and, for `research`, no workflow or pipeline version (harness.py:430–443). Finding F-1 of the implementation log is not decided in review-log.md. | Medium | Owner decision: (a) accept until the N-0/N-2 integration with scope row "partly" and a TD, or (b) Phase 3: wire IF-105 into `tools/eval.py`, refuse model suites without `--pin`, and write the skill/pipeline version for every kind. |
| F4 | **REQ-EVL-005 and REQ-EVL-009 are not met on the branch.** `check_baselines.py`: 5 tested/trusted workflows without a baseline, `library/baselines.json` missing. `agent_check.py`: `research` (lookup) and `verdicts` (verify) have no holdout case; `eval/baselines/` holds only `.md` reports. eval-spec.md is a draft (holdouts "proposed"). | Medium | Owner/Plan: the eval-spec gate, holdout cases written and labelled by the owner, `.jsonl` baselines recorded, the baselines link file; or scope rows "partly" with FB/TD. |
| F5 | **Holdout guard gaps.** (a) tools/decide_guard.py:87–90 passes every option through after `--split holdout`: `--split dev` overrides it and the verdict is decided on dev records (probe: PASS from a dev run), and `--rerun` files (used after a FAIL) are not checked. (b) `tools/eval.py list`, `cases <x>.holdout` and `run <x>.holdout` load, print or run a holdout suite without any flag (synthetic fixture). The coding agent's documented command `tools/eval.py list` therefore opens every holdout suite. | Medium | (a) Phase 3, test first: refuse `--split` in the options and check `--rerun` runs like `--run`. (b) Owner decision / Phase 2 amendment: e.g. holdout suites only with an explicit `--holdout` flag (Verify), skipped by `list`. |
| F6 | REQ-EVL-003 is inert and partly untested: `Harness.calibrations` is never loaded, no record gets a `judge`; the surviving mutants are harness.py:452 (`run` does not mark), metrics.py:60 (`verification_metrics` counts a not-counted verdict), metrics.py:98 (`is_right`). | Low | Needs tests (three small ones); wiring with the first judge (eval-spec: none in G-V1). |
| F7 | eval_platform.py:18: a pin without seed or temperature is refused only here, untested (surviving mutant). | Low | Needs a test. |
| F8 | harness.py:596 `require_same_cases` compares case ids and repeats, not `benchmark_version`: two runs of different suite contents with the same ids are compared. | Low | Owner decision: add the suite version to the check (amendment of TC-EVL-008) or accept (cases change only by retire/add). |
| F9 | architecture.sysml:547–560: the Evaluation part lists `harness.py`, `metrics.py`, `tools/eval.py`; `eval_platform.py`, `decide_guard.py`, `check_baselines.py`, `label_agreement.py`, `measure_latency.py`, `measure_fps.mjs` are missing; `judgeCalibration` still `proposed`. | Low | Phase 2 amendment (model text). |
| F10 | Test readability: 34 `test_doc_check` errors in the node's six test files; test-spec.md has no `## Scenarios` (shared with N-4, N-4.2); `HarnessKeepsHoldoutOut` (tests/test_decide_guard.py:74) has no `req` marker. | Low | Phase 3 (docstrings); Plan (scenarios). |
| F11 | The TC-EVL tests live in `tests/` (unprotected) and were written in the implementation commits, while plan.md (line 5) says they are written first in a session of their own and installed by the owner. | Low | Owner decision: accept as for the other leaves, or install them as protected. |
| F12 | `tools/eval.py compare` calls p < 0.05 "a difference you can believe" on dev runs (harness.py:612), an improvement claim outside REQ-EVL-002's rule. | Low | Wording: "dev feedback, not a verdict". |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| (candidates) F3 option (a), F8, F11 | see findings | owner |

## Notes for Phase 7 (validation)
- The latency figure (BM-MIA-001) should be taken only after F1, and with the websocket transport if the owner approves it (log: the image has no `websocket-client`).
- The fps tool needs frame times recorded in the browser; no recorder exists.
- The idea date of the skill path (FR-20, AC-9) is stored nowhere.

## Not checked
Live latency against the real stack; the frame rate in a browser; BM-MIA-001/-002; T-07 and the N-4/N-0 integration steps (skipped by design); a real-model eval run (not needed); CI stages; `test_amendment_report` (known failure, not run).
