# A-122: baselines recorded, two criterion lines raised (G-V2.CONVERT, proposal for the owner's review)

Status: **proposed, not applied**. Basis: A-120 change 2 ("if a recorded rate differs from the reference in the criterion line by more than 0.02, the line is changed in Plan, never after a converted run"), the five baseline runs the owner started on 2026-11-15, owner decision 2026-11-15 "raise both floors" (margin 0.10 kept).

## The runs (MP-light gemma4:12b-it-qat, seed 7, temperature 0, 3 repeats, all cases, commit 1fb0c35; files in `data/eval/`, not yet in `eval/baselines/`)
| Skill / suite | Run file | Right case-repeats | Case majority | Reference in the line | Diff |
|---|---|---|---|---|---|
| research / EV-research | research__escalate__20261115-173301.jsonl | 57/60 = 0.950 | 19/20 | 0.92 | +0.030 |
| plan_question / EV-plans | plans__free__20261115-173323.jsonl | 69/108 = 0.639 | 23/36 | 0.64 | -0.001 |
| verify_claim / EV-verdicts | verdicts__single__20261115-173350.jsonl | 141/150 = 0.940 | 47/50 | 0.93 | +0.010 |
| verify_computable / EV-computable | computable__computable2__20261115-173501.jsonl | 114/117 = 0.974 | 38/39 | 0.92 | +0.054 |
| extract_claims / EV-extraction | extraction__llm__20261115-173516.jsonl | 104/153 = 0.680 | 34/51 | 0.69 | -0.010 |

`right` is the metric of `eval_decide.py` (`is_right`: status equals the truth label, `inconclusive` where expected). Counting `pass` as right would give 0.08 for EV-verdicts (a claim whose truth is false is right when the status is `fail`); it is the wrong reading.

## Change (REQ-WFM-110 and REQ-WFM-113 only; the three others are within 0.02 and stay)
| Requirement | Line now | Line proposed | False alarm | Miss at loss 0.25 / 0.15 |
|---|---|---|---|---|
| REQ-WFM-110 research | min=0.82 (17 of 20), reference 0.92 | min=0.85 (17 of 20), reference 0.95 | 0.0003 | 0.2027 / 0.6536 |
| REQ-WFM-113 computable | min=0.82 (32 of 39), reference 0.92 | min=0.87 (34 of 39), reference 0.974 | 0.0000 | 0.0469 / 0.5020 |
Computed with `false_alarm.py --n --min-rate --good --bad --rerun`. Texts in `requirements.md` ("at least 82 %") become 85 % and 87 %; `Eval criterion:` lines, rationale lines (baseline 0.95 resp. 0.974, source = the run files), `eval-spec.md` tables (baselines and error rates), plausibility claims `floor` (REF-CONVERT-1 and -4) and the test numbers follow.

## What follows from it (all protected or the owner's; nothing done)
1. **TC-WFM-059** copies the line of REQ-WFM-110 (min 0.82, 17 of 20 passes, 16 of 20 fails). With 0.85 the threshold k stays 17 of 20, so the numbers of the test hold; the copied line and its comment change (assumption 7 of the Step 4 hand-over). Check, do not assume.
2. The miss for a loss of 0.15 is higher than before (research 0.50 to 0.65, computable 0.51 to 0.50: about the same), i.e. the dev suites still cannot see small losses; REQ-WFM-058 (same model calls as the old runner) remains the real guard.
3. All repeats of a case gave the same result (temperature 0, seed 7): case majority equals the repeat share in four of five suites. Three repeats add no information here; the effective n is the number of cases.
4. The header of the extraction run names the target skill `extract_claims_rules` (the suite's `target.skill`) while the variant runs `extract.llm@1`; the run is the llm pipeline on the extraction suite, as the baseline md says. Worth a look when the owner places the file.
5. `split:dev` tags (A-120 change 1) were not yet applied when the runs were made; the runs contain all cases. After the tags, `eval_decide` with `split=dev` keeps all of them (no case moves).
