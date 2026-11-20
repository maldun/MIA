# Verification report G-V2 (iteration goal: Skill rework, foundation), 2026-11-20

Line: `master` at `740d7fa3` (STORE, MODEL, TOOLBOX, CONVERT and SNAPSHOT are all merged; there is no `goal/v2` branch). Clean checkout: worktree `/home/maldun/prog/Python/MIA-verify-g-v2` (branch `verify/g-v2`), venv `mia312`. Reviewer: one session that did not implement these goals and did not run their dev evals; it read the subgoal reports and the brief, not their chats, and re-ran the checks. Verdict (proposal): **Verified with accepted deviations**, conditions in "Findings" and "Verdict".

## 1. Automated results (clean worktree of master, foreground, in pieces)
| Check | Result |
|---|---|
| Unit suite `[a-c]` 678, `[d-m]` 513, `[n-r]` 596, `s[a-gi-z]` 427, `sh*` 20, `[t-z]` 269 (2503 in all) | all OK (4 skipped, 2 expected failures, as recorded) |
| JS `tests/js` | 186 of 186 |
| Acceptance scripts (40) and contract scripts | all OK except `test_decide_guard.py` and `test_judge_calibration.py` (`behaviour.FUNCTIONS`; known, not G-V2) |
| PostgreSQL `test_storage_postgres.py` | 43 OK |
| IF-102 contract on postgres:16 (`contract_postgres.sh`) | 12 OK |
| `check_sysml_model.py`, `check_sysml.sh` (4 models) | OK, 0 errors, 0 warnings |
| `trace_check` | 563 errors (handover: 559 before the TD-86 to TD-90 lines). New ones: `Relaxed: TD-86/87/88/89/90` missing on REQ-WFM-058 and 110 because the entries are still DRAFT (no sign-off). No error for a G-V2 requirement otherwise |
| `goal_check` | 8 errors: GL1 (G-V2 and G-V3 both open, Q-7), GL3 scope wording (CONVERT `REQ-WFM-143`, SNAPSHOT ids and interface versions, TOOLBOX `IF-302`), GL4 (G-V2.SNAPSHOT has no agreement row) |
| `agent_check` | 2 errors, both THR-011 (A8: `TB-exchange` not in the trust-boundary table, no RT case); known since 2026-11-08, see V2-6 |
| Smoke SMOKE-MIA-001 (AC-38: fresh clone, one config file, one command) | green, 5 services, first account, chat answered (49 s) |
| Plan documents after A-164 | TC-WFM-144 to 148 unique (no duplicate heading in test-requirements or test-spec), each in a table with a scenario and used by `test_pipeline_graph.py` and `test_skill_binding.py`; TC-WFM-143 and 149 do not exist |

Environment note: the main checkout is not a clean environment (leaked `setup_cfg.json`); all evidence is from this worktree.

## 2. Outcome criteria (verification matrix)
| OC | Method | Evidence | Result |
|---|---|---|---|
| OC-1 (same results as v0.1.0, or stays and says why) | Test (eval), AC-34 | Section 4: five criteria decided PASS on dev, MP-light, 3 repeats, against the old-runner baselines; `Core.run` routing checked (section 3) | Met on dev; no holdout (TD-88). `extract_claims_rules` and the skills without a suite stay on the old runner or have a stage-2 output check (TC-WFM-115) |
| OC-2 (one description gives command, steps, knowledge; a wrong one is refused with the reason) | Test | MODEL report (REQ-WFM-040 to 049, accepted deviations D-309), STORE report, acceptance `test_skill_record`, `test_graph_records`, `test_skill_conversion` green here | Met; context graph ID not read from the record (F-04, accepted D-309, goal C) |
| OC-3 (an outside step does not run, only the owner allows) | Test | TOOLBOX report and acceptance `test_toolbox.py` (untrusted refused with reason, marker side effect does not happen, runs after the owner marks it), `test_pipeline_graph`, TC-WFM-148 (untrusted entry stops the run before the model is asked) all green here; MODEL refusal REQ-RUN-017 | Met by tests; **no red-team case for THR-011** (V2-6) |
| OC-4 (snapshots: go back, state before is kept) | Test | SNAPSHOT report (signed 2026-11-19), `test_skill_snapshots.py`, IF-102 v7/IF-203 v2/IF-302 v13 and v14 contracts, PostgreSQL 43 and contract 12 here | Met |
| OC-5 (fresh copy, one config file, one command, everything still works) | Smoke test | SMOKE-MIA-001 green on this commit; unit and acceptance suites green | Met on the reference host; the stack was not run with a converted skill through the UI (Validate, VAL-007) |

AC-31, AC-32, AC-38, AC-40: green as above (AC-31 `test_graph_records`, AC-32 `test_toolbox`, AC-38 smoke, AC-40 `test_skill_snapshots`).

## 3. Agent checks
**A. Protected material.** Per-commit audit since `plan-baseline-it1` is not possible against one tag (the tags sit on different lines). Against the baselines of the four goals the modified files are all contract and mock files (IF-101, IF-102, IF-201, IF-203, IF-301, IF-302, amendments A-90 to A-161), `test-requirements.md`, `test_skill_snapshots.py` and `snapshot_lab.py` (commit `973e2167`, A-121, D-242) and the five suites. The suites differ from `plan-baseline-it2-convert` only by the `split:dev` tag (compared case by case with the tags removed: 39, 51, 36, 20, 50 cases identical, all tagged dev, none holdout; A-120). Baselines: installed by the owner (D-355, `8d952a04`). No self-approved or unnamed amendment found in what I read; I did not read each of the 99 test and helper commits of the iteration.
**Versions.** `git log` of the five skills and their pipelines (`research.escalate`, `plan.free`, `verify.single`, `verify.computable`, extraction): last change 2026-10-20, before the baselines; versions unchanged since. Skills added in the iteration carry versions.
**A2/B. Runs against their test requirements.** All five runs: pin MP-light, digest `sha256:38044be4f923...` equal to the baseline pin, 3 repeats, dev split, variant `converted`, `skill_version` in the header. Their header commits (`74c81500`, `bf28a0de`, `1735cf1b`, `4d6f0a08`) differ from master `740d7fa3`, but **no `.py`, skill or library file changed between any of them and master** (`git diff --stat`), so they are runs of the final code. Not met by me: I did not make my own run (the decision used the author's files, as the brief allows) and I did not re-check `ollama show` digests.
**C. Decisions** (`tools/check_conversion.py <skill> --run <file>`, which calls `eval_decide.py` with the criterion line of the requirement; run files in `/home/maldun/prog/Python/MIA/data/eval/`):

| Skill | Run file | Criterion (dev, n, 3 repeats) | Point | Result |
|---|---|---|---|---|
| research | `research__converted__20261120-111026.jsonl` | right >= 0.85, n=20 | 0.950 | PASS |
| plan_question | `plans__converted__20261120-111505.jsonl` | right >= 0.54, n=36 | 0.639 | PASS |
| verify_claim | `verdicts__converted__20261120-111801.jsonl` | right >= 0.83, n=50 | 0.940 | PASS |
| extract_claims | `extraction__converted__20261120-112131.jsonl` | right >= 0.59, n=51 | 0.667 | PASS |
| verify_computable | `computable__converted__20261120-112720.jsonl` | right >= 0.87, n=39 | 0.974 | PASS |

No re-run was needed. Holdout: none exists (TD-88, accepted by the owner, D-355); the dev run is feedback by the plan's own words, so these PASS carry the weakness of TD-88.
**E2. Sanity of the results.** Zero differing repeats per case in all five runs (expected at seed 7, temperature 0). Call counts equal the baseline per case and repeat (research 60/60, plans 108/108, verdicts 150/150, extraction 153/153; computable 108/117), so the graph path does the same work as the old runner (research: 42 cases 1 call, up to 11). Outputs are not a copy: identical to the baseline text in 59/60 (research), 90/108, 144/153, and 0/150 and 0/117 (verdicts, computable: other output format). The converted runs are 2 to 10 times faster per case than the baselines (median seconds research 2.7 vs 13.6, plans 1.6 vs 12.6, verdicts 1.3 vs 12.4, extraction 2.0 vs 12.2, computable 7.1 vs 12.9). That is not explained by the code (same calls); it points to a loaded or cold model server during the baseline runs. Judged plausible, not proven: V2-4.
**`Core.run` routing (F-02).** With the five records of `data/conversion/`, `bound_checks` returns all five. On a copy of the records: run file of `research` moved -> research drops out; `skill_version` 99 in `plan_question` -> drops out; `pipeline` changed in `verify_claim` -> drops out; the other records stay bound. `Core.run` takes the graph path only for a name in `bound_checks` (`core.py:100`), else the old runner; `conversion_dir` None means old runner for all. `extract_claims` and `verify_claim` records have no `pipeline_resolved` (checked on the reference alone, as documented).
**D. Trust boundary and sandbox.** Model-written code runs only through `self.sandbox.run` (`pipeline.py:469 to 483`; no sandbox configured raises `NodeError`); `skill_converter.py` uses `subprocess` only for `eval_decide.py`; tool steps go through the IF-402 door (`_call_door`, `door_tools`, refusals that count nothing give the reserved call back); `run_converted` writes no run record and no file. F-08 confirmed fixed. Live trust and lifecycle on the converted path: TD-86 (accepted), budgets and stop: TD-87 (accepted); their interim criteria were not re-checked beyond the tests listed in section 1.
**MODEL open items.** The handover says nobody re-checked them: that is out of date. D-309 (2026-11-08) accepts F-04 as a deviation and records the owner's approval of TC-WFM-047, TR-MODEL-001 and TR-MODEL-003 (review-log rows of 2026-11-08); `req_review.py status` does not list them as changed. Closed.
**F2. Specification against code.** Requirement side: REQ-WFM-057 to 060, 069, 110 to 115 and REQ-RUN-030 to 035 have tests that pass (no `trace_check` error) except the relaxations below. Code side, behaviour no requirement states: `tool_call` and `budget_spent` events and the `budget` status on the converted path (the event types exist in IF-401; the converted-path use has no requirement, TD-87), the `conversion_dir` setting and its default `data/conversion` (`constants.py:40`, `web_app.py:636`), and `REQ-WFM-143` named in the CONVERT scope but not in `requirements.md` (V2-1, V2-2).
**D-356 / TD-89.** `skills/research.md` names `research.escalate@1`; `test_pipeline_graph.py` (TC-WFM-128) loads `research.escalate@3`. Reported, not changed; the converted research run and its record use `@1`.

## 4. Findings
| ID | Finding | Severity | Destination |
|---|---|---|---|
| V2-1 | The CONVERT scope names `REQ-WFM-143`, which does not exist (GL3); budgets and stop on the converted path have no requirement (TD-87, accepted) | low | Plan: reword the scope or write the requirement when TD-87 is closed |
| V2-2 | Code behaviour without a requirement: `conversion_dir` setting and default, `tool_call`/`budget_spent` events and status `budget` on the converted path | low | Plan amendment (or remove) |
| V2-3 | `skill_converter.py` line 1 still says "STUBS ... until the tasks T-CV-03 to T-CV-08" although everything is implemented | low | Implement (docstring) |
| V2-4 | Converted runs are 2 to 10 times faster than the baseline runs with identical call counts; cause not proven (probably load or a cold model during the baseline runs) | low | Validate: a person may time one skill on both runners; no action for the verdict |
| V2-5 | TD-86 to TD-90 are DRAFT, so REQ-WFM-058 and 110 do not carry `Relaxed:` and `trace_check` shows 4 more errors; TD-88 (no holdout) means AC-34 is decided on dev only | medium (paperwork) | Owner: sign the TD entries (D-355 accepts the content); then trace_check should drop them |
| V2-6 | THR-011 (imported transform that does harm when run) has no red-team case and `TB-exchange` is not in the trust-boundary table (`agent_check` A8, known since 2026-11-08). OC-3 is covered by `test_toolbox.py`, not by a red-team case | medium | Plan amendment (RT case and table row); owner decides whether it is a deviation of G-V2 |
| V2-7 | GL4: G-V2.SNAPSHOT has no row in the Agreement table of `goal.md`; the Verify and Commit rows of G-V2.CONVERT still say "in progress" | low | Commit paperwork |
| V2-8 | `TC-WFM-110` to `114` have scenarios but are in no table of the node test-spec (trace WARN) | low | Plan |
| V2-9 | The equivalence runs are feedback runs of the author session: I decided them but did not repeat them with the model; AC-34 per criterion holds for these files | info | owner accepts, or asks for a repeat run of one skill |
| V2-10 | Not re-checked: `ollama show` digests, budgets and VRAM (V2-9), replay of recorded runs, mutation tests, the 99 test and helper commits one by one | info | see section 5 |

## 5. Not covered
No holdout (TD-88), no fresh model run of my own, no transcript review by a person (check F), no budget or VRAM measurement, no replay with `run_explain.py reproduce`, no current-state deployment check, no hand check of the stack with a converted skill through the UI (VAL-007 is a Validate item), PostgreSQL ran on postgres:16 under podman only.

## 6. Cases for the owner's transcript sample (check F)
Cases wrong in every repeat of the converted runs: research `older-museum-or-builder` (11 calls, fail 3 of 3; the only failing case of that run); for verify_claim (`num-eiffel-wrong`, `num-moon-wrong`, `num-sun-wrong`), verify_computable (`bmi-right`), extract_claims and plan_question use the lists in `specs/mia/goals/G-V2.CONVERT/implementation-log.md`; the `status` field of the run files is not the metric of those suites, so I did not derive a list from it. In addition, about 10 random cases per suite and at least one case where the converted output differs from the baseline in format (verdicts, computable).

## 7. Quality evidence per characteristic
| Characteristic | Evidence | Gap |
|---|---|---|
| Functional suitability | OC table, five decided criteria, 2503 unit tests, 40 acceptance scripts | no holdout (TD-88) |
| Performance efficiency | calls equal to the old runner, converted runs not slower (V2-4) | budgets and VRAM not re-measured: not now (Validate) |
| Compatibility | five suites on both runners with the same pin; IF-203/IF-301/IF-302 contract suites, PostgreSQL | the file backend stays for the transition |
| Interaction capability | not changed by this goal (goal B) | not now |
| Reliability | restore keeps the state before (OC-4), fresh-install smoke, bound records fall back to the old runner | stop and budgets on the converted path: TD-87 |
| Security | untrusted transforms never run (OC-3), sandbox only path for model code, IF-402 door | live trust on converted runs TD-86; THR-011 has no RT case (V2-6) |
| Maintainability | one module per part; stale docstring (V2-3) | `check_sysml_model.py` and `check_sysml.sh` OK |
| Flexibility | records and graphs as data, pipeline version bound per record | research@1 against @3 (TD-89) |
| Safety | not applicable to this goal | none |

## 8. Open deferrals
TD-81 (running state after a crash), TD-82 to TD-84 (G-V3, DRAFT), TD-85 (accepted), TD-86 (live trust, DRAFT), TD-87 (budgets and stop, DRAFT), TD-88 (no holdout, DRAFT), TD-89 (research@3 vs @1, DRAFT), TD-90 (IF-103 real half skipped by design, DRAFT, D-357 accepted in spirit). For TD-86 to TD-90 the entries wait for the owner's sign-off. Interim criteria: the converter and binding tests (TC-WFM-144 to 148, TC-WFM-128) and the dev decisions above hold.

## 9. Verdict (proposal)
**Verified with accepted deviations.** In scope all checks are green on a clean checkout, the five criteria of AC-34 are decided PASS on dev, and OC-1 to OC-5 have evidence. Deviations to accept: TD-86, TD-87, TD-88 (dev only), TD-89, TD-90, the open MODEL items already accepted (D-309), V2-6 (no red-team case for THR-011) if the owner does not want it fixed first, and V2-9. Findings V2-1 to V2-3, V2-7, V2-8 go to Plan, Implement or Commit paperwork. The tag `v0.2.0` is the owner's.

## 10. Decisions of the owner, 2026-11-20 (questionnaire)
Verdict: **Verified with accepted deviations**. V2-6 (no red-team case for THR-011) accepted as deviation, amendment later. V2-9 and V2-4 accepted: the author's run files decide AC-34, the speed difference goes to Validate. The owner still signs TD-86 to TD-90, sets the statuses and tags `v0.2.0`; recorded as D-358 in `review-log.md`.
