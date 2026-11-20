# Verify brief: G-V2 (iteration goal, parent Verify) for a fresh, independent context

You have not seen the implementation chats and must not have run the dev evals of this goal. Start from `CLAUDE.md`, `specs/mia/goals/G-V2/goal.md`, the five subgoal records (`G-V2.STORE`, `.MODEL`, `.TOOLBOX`, `.CONVERT`, `.SNAPSHOT`) and their verification reports, then `specs/mia/review-log.md` rows D-355 (decisions of this Verify) and D-354 (G-V3 Verify, for the shape of such a report). Load `dev-workflow`, `verify-phase`, `agent-app` and `agent-app-verify`. The reference for the form is `specs/mia/goals/G-V3/verification-report.md`. Write the report to `specs/mia/goals/G-V2/verification-report.md` in your own worktree (`git worktree add ../MIA-verify-g-v2 -b verify/g-v2 master`); do not change code, tests, suites or labels.

## Scope
Exit criterion: OC-1 to OC-5 of G-V2, checked by AC-34 (per-skill equivalence with v0.1.0), AC-31, AC-32, AC-38, AC-40; VAL-007 is a Validate item. All five subgoals are in master; there is no `goal/v2` branch. Subgoal Verify state: STORE, MODEL, TOOLBOX and SNAPSHOT verified with accepted deviations; CONVERT verified for its conversion half only (report of 2026-11-17, "not verified as a whole" before the split), its open items are yours to decide: F-03, F-05, F-07, F-09 and the five equivalence criteria.

## Owner decisions that bind you (D-355, 2026-11-20)
1. AC-34 is decided on the **dev split**, as the AC text says, with the pin MP-light (`gemma4:12b-it-qat`, digest `sha256:38044be4f923...`, seed 7, temperature 0), 3 repeats, against the old-runner baselines of 2026-11-15. The missing holdout is TD-88 (accepted).
2. F-05 (budgets and stop on the converted path) is TD-87 and F-07 (live trust and lifecycle) is TD-86: accepted deviations. Do not report them as new findings; check only that the interim criteria of the entries hold.
3. A criterion that fails and cannot be re-run with fresh seeds is **NOT DECIDED**, accepted by the owner; that skill stays on the old runner (record removed or not written). Do not change seeds, repeats or thresholds.
4. The baselines `eval/baselines/{research__escalate,plans__free,verdicts__single,computable__computable2,extraction__llm}__baseline.jsonl` were copied by the owner from the old-runner runs (`tools/install_baselines_g_v2.sh`; the suites differ from the runs only by the `split:dev` tags of A-120).

## Run (foreground, one after another; a background start makes `test_shutdown*` fail; never run browser checks while another run goes)
- In a clean worktree of master: `python -m unittest discover -s tests` in pieces (`test_[a-c]*`, `[d-m]`, `[n-r]`, `s[a-gi-z]`, `sh*`, `[t-z]`, each under 10 minutes), `node --test "tests/js/*.test.mjs"`, every `tests/acceptance/test_*.py` and `tests/acceptance/contract/test_*.py` as a script, PostgreSQL (`tests/test_storage_postgres.py`, `MIA_DB_PYTHON=... bash tools/contract_postgres.sh`), `check_sysml_model.py`, `check_sysml.sh`, `trace_check`, `goal_check`, `agent_check`.
- Expected and not ours: `test_decide_guard.py` and `test_judge_calibration.py` (`behaviour.FUNCTIONS`); in the main checkout `test_expression_llm.ApiTest` and `test_make_voice_lines` (leaked `setup_cfg.json`, folder named `MIA`): use a clean worktree.
- Equivalence: decide each of the five criteria with `eval_decide.py --baseline` on a run of the converted variant of the **final code**. The runs were made by the author session on 2026-11-20 (feedback, not your evidence), `tools/check_conversion.py <skill>` on master, the model server free, pin MP-light, 3 repeats, dev split; each step printed PASS and each rate equals the one of the acceptance run of 2026-11-16. Files (git-ignored, in `/home/maldun/prog/Python/MIA/data/eval/`):

  | Skill | Run file | Rate, minimum | Baseline |
  |---|---|---|---|
  | research | `research__converted__20261120-111026.jsonl` | 0.950, 0.85 | `eval/baselines/research__escalate__baseline.jsonl` |
  | plan_question | `plans__converted__20261120-111505.jsonl` | 0.639, 0.54 | `eval/baselines/plans__free__baseline.jsonl` |
  | verify_claim | `verdicts__converted__20261120-111801.jsonl` | 0.940, 0.83 | `eval/baselines/verdicts__single__baseline.jsonl` |
  | extract_claims | `extraction__converted__20261120-112131.jsonl` | 0.667, 0.59 | `eval/baselines/extraction__llm__baseline.jsonl` |
  | verify_computable | `computable__converted__20261120-112720.jsonl` | 0.974, 0.87 | `eval/baselines/computable__computable2__baseline.jsonl` |

  Use these files for the decision (a decision needs no model) or make your own run if the model server is free (`ListAgents` first). The five rates equal the earlier ones exactly: check that the runs went through the graph path (header `variant.converted`, the `commit` field, the call counts) and not a cached or old-runner route (point 10).
- Baseline check: `python ~/.claude/skills/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval`.

## Look hard at
1. OC-1 to OC-5 across the five subgoals, one row each in the verification matrix, with the evidence and its source report; OC-3 (a step from outside does not run, only the owner allows) and OC-5 (fresh copy, one config file, one command) are checked across subgoals and have no single owner.
2. The **MODEL report's open items**, which nobody has re-checked: F-04, the re-approval of TC-WFM-047, TR-MODEL-001 and TR-MODEL-003.
3. `Core.run` routing: a skill with an acceptance record runs on the graph path, bound to the skill version, pipeline reference, resolved version and run file (`skill_converter.bound_checks`, F-02); a skill without a valid record stays on the old runner. Check with the five records of `data/conversion/` and with a record whose run file is moved.
4. Trust boundary and sandbox: `skill_converter.py` and `harness.py` diff for the sandbox script path; model-written code runs only in the sandbox; a tool step goes through the IF-402 door (F-08 was fixed: confirm); nothing is written outside the data folder.
5. Specification against code in both directions for REQ-WFM-057 to 060, 069, 110 to 115 and REQ-RUN-030 to 035: behavior in the code that no requirement states (`tool_call` and `budget_spent` events, status `budget`, the `conversion_dir` default) is a Plan finding.
6. The plan documents after the F-09 patch set (`specs/mia/amendments/A-164-f09-protected.patch`, the test-spec edits of `docs/f09-patches`): ids unique (TC-WFM-144 to 148 for the former CONVERT checks of 130 to 134), every check of the CONVERT range has a scenario. Open question, not decided: TC-WFM-128 and `tests/acceptance/test_pipeline_graph.py` load `research.escalate@3`, while the skill `research` (version 3) names `pipeline: research.escalate@1`: the converter check runs on a pipeline version that is not the one that runs. Report it; do not change it.
7. Protected material unchanged except named amendments: `git diff --stat plan-baseline-it2-model plan-baseline-it2-store plan-baseline-it2-toolbox plan-baseline-it2-convert -- tests/acceptance tests/helpers contracts eval/suites eval/baselines specs/mia/test-requirements.md` against the amendments A-120 to A-125, A-141, A-159, A-161 and the baselines of D-355; any other change is a finding. Skill and pipeline versions bumped with every change of prompt, graph or tools (`git diff -- skills library`).
8. Quality evidence per characteristic (`quality.md`), open deferrals (TD-81 to TD-88 and older) with their interim criteria, and `deferred.md` against `trace_check`.
9. By a person (the owner), not by you: a sample of transcripts of the converted runs that were wrong in every repeat (research `older-museum-or-builder`; verify_claim `num-eiffel-wrong`, `num-moon-wrong`, `num-sun-wrong`; verify_computable `bmi-right`; extract_claims, plan_question lists in the CONVERT log): list the cases for the owner.
10. Sanity of the results: a converted rate clearly above its baseline, zero variance over repeats, a run that is faster than the floor of a model call (a fake model left in, a cached answer): inspect before accepting.

## Not yours to decide
Whether a failing skill is switched back, whether to tag `v0.2.0`, any change to a prompt, suite, label, threshold or baseline. Everything outside the list above that looks wrong goes into the report as a finding with a proposed destination (Implement, Plan or Validate).

Verdict form: as in the G-V3 report, "Verified", "Verified with accepted deviations" (name each), or "Not verified" with the reasons; the owner approves.
