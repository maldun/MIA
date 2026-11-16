# A-120: split tags and baselines for the conversion checks (G-V2.CONVERT)

Status: **proposed, not applied**. The five suites below are protected eval material; the owner labels and applies this, the coding agent does not touch them. Decided by the owner on 2026-11-07: "Tag cases split:dev".

## Why
REQ-WFM-110 to 114 are decided on the dev split (`split=dev`). `eval_decide.py` keeps a record for `split=dev` only if it carries the tag `split:dev` (its `keep()` function), and the harness copies the tags of a case into its run records. None of the active cases of the suites below carries a split tag (`agent_check.py` A6: "active cases without split:dev or split:holdout"). Checked on 2026-11-07 with a synthetic run of 20 cases that all passed: untagged, the decision selects 0 cases and reports FAIL; tagged `split:dev`, the same run is PASS. Every criterion would therefore fail whatever the converted skill does.

## Change 1 (owner, protected suites)
Tag every active case `split:dev` in the dev folders of these suites. No case moves between splits and no holdout case is added or opened.

| Suite | Cases | Criterion |
|---|---|---|
| EV-research | 20 | REQ-WFM-110 |
| EV-plans | 36 | REQ-WFM-111 |
| EV-verdicts | 50 | REQ-WFM-112 |
| EV-computable | 39 | REQ-WFM-113 |
| EV-extraction | 51 | REQ-WFM-114 and REQ-WFM-115 |

## Change 2 (record the baselines, Plan step 4)
The reference of each criterion is the run of the v0.1.0 skill with 3 repeats on the pin MP-light (TR-CONVERT-004). Today only `.md` summaries are committed in `eval/baselines/`; the run files are in the ignored `data/eval/` and mostly have one repeat. The harness records the five runs (roughly 35 minutes in total by the per-case times of the summaries: 20 x 3 x 4.5 s, 50 x 3 x 1.4 s, 39 x 3 x 8.4 s, 51 x 3 x 2.2 s, plans not stated; one model at a time), the owner places them in `eval/baselines/` as `<suite>__<variant>__baseline.jsonl`, and the minimum of each criterion is checked against the new rates **before** any converted skill runs. If a recorded rate differs from the reference in the criterion line by more than 0.02, the line is changed in Plan (an amendment after the gate), never after a converted run.

| Skill | Suite | Variant of the baseline | Reference now |
|---|---|---|---|
| research | EV-research | research.escalate@1 | 0.92 (3 repeats) |
| plan_question | EV-plans | plan.free@1 | 0.64 (3 repeats) |
| verify_claim | EV-verdicts | verify.single@1 | 0.93 (1 run) |
| verify_computable | EV-computable | verify.computable@2 | 0.92 (1 run) |
| extract_claims | EV-extraction | extract.llm@1 | 0.69 (1 run) |

## Not changed
Criteria, margin, repeats and rule of REQ-WFM-110 to 114; `eval/suites/` cases other than the tag; red-team cases; holdout folders.
