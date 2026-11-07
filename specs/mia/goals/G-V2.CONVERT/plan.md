# Plan: G-V2.CONVERT (conversion of the skills and snapshots)

**Requirements:** REQ-WFM-057 to 066, 069, 110 to 115 in `specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md`   **Test spec:** the same folder `test-spec.md` and `specs/mia/test-spec.md` (statistical checks)   **Eval spec:** `specs/mia/eval-spec.md`, section "G-V2.CONVERT"   **Status:** Draft (Plan step 5, 2026-11-07; not reviewed)

Written because two gaps of Plan step 3 cannot be closed in Plan: `stages.yaml` has no stage 4 step for TC-WFM-110 to 114, and the red tests do not exist. Both depend on things that appear later (the converted runner, the protected folders). They are tracked here as tasks and preconditions, not left open.

## Preconditions (nothing of Implement starts before all of them)
| # | Precondition | Owner | State |
|---|---|---|---|
| P1 | G-V2.STORE, MODEL and TOOLBOX are merged (parallel-work.md) | owner | open |
| P2 | Step 4 done: red tests for the checks below in `tests/acceptance/`, helpers, fake model server with recorded replies; tag `plan-baseline-it2` | a dedicated test-writing session, reviewed by the owner | open |
| P3 | A-120 applied: tag `split:dev` on the cases of EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction (protected eval material) | owner | proposed |
| P4 | Baselines recorded as run files: dev split, 3 repeats, MP-light, per skill and variant of `eval-spec.md` (results only; `eval/baselines/` is protected) | owner or a harness run the owner starts | open; today only `.md` summaries exist |
| P5 | The ten proposed plausibility items rated; the margin 0.10 of REQ-WFM-110 to 114 judged against the recorded baselines (D-260 D probe) | owner | open |
| P6 | REQ-WFM-057 to 066, 069, 110 to 115 Approved in the review log with their final text | owner | 062, 063, 066 and 059 back in review |

## Task list
Task ids carry the prefix CV so that they do not collide with T-01 to T-11 of the N-2.3 plan. Riskiest first.

| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-CV-01 Recording of the old run (spike) | REQ-WFM-058 | TC-WFM-058 can be written against recordings: model replies and tool results of one old run replay deterministically | P1, P2 |
| T-CV-02 Settings record of the equivalence check | REQ-WFM-069 | TC-WFM-069 | P1, P2 |
| T-CV-03 Per-skill state, old runner until accepted, record of the check | REQ-WFM-057, REQ-WFM-059, REQ-WFM-060 | TC-WFM-057, TC-WFM-059, TC-WFM-060 | T-CV-02 |
| T-CV-04 Same calls on scripted replies | REQ-WFM-058 | TC-WFM-058 for each skill converted in T-CV-06 to T-CV-08 | T-CV-01, T-CV-03 |
| T-CV-05 Snapshots: take, list, restore, nothing deleted, owner only | REQ-WFM-061, REQ-WFM-062, REQ-WFM-063, REQ-WFM-064, REQ-WFM-065, REQ-WFM-066 | TC-WFM-061 to TC-WFM-066 | P1 (snapshotStore, IF-203 v1, IF-301 v2 through their mocks) |
| T-CV-06 Convert research and plan_question | REQ-WFM-110, REQ-WFM-111 | TC-WFM-110, TC-WFM-111 on the dev split | T-CV-04, P3, P4 |
| T-CV-07 Convert verify_claim and verify_computable | REQ-WFM-112, REQ-WFM-113 | TC-WFM-112, TC-WFM-113 on the dev split | T-CV-04, P3, P4 |
| T-CV-08 Convert extract_claims and extract_claims_rules | REQ-WFM-114, REQ-WFM-115 | TC-WFM-114 on the dev split, TC-WFM-115 equality of the 51 outputs | T-CV-04, P3, P4 |
| T-CV-09 Stage 4 steps and the per-suite check runner | TC-WFM-110 to TC-WFM-114 as steps | `bash` run of stage 4 with `--dry-run` lists five steps; one real step runs on a scripted run file | T-CV-06 |

## Tasks

### T-CV-01: Recording of the old run (spike)
- Implements: REQ-WFM-058 (D-260 C: model replies and tool results both scripted, replayed from a recording of the old run; a recording tool for tool results may be needed, a small task, no new part)
- Tests to turn green: the helper that records and replays (written in Step 4, protected); then TC-WFM-058 in T-CV-04
- Touches: `harness.py`, `pipeline.py` only to record and replay (no change of behaviour); a recording helper next to them
- Must not touch: protected material, `eval/`, `contracts/`
- Depends on: P1, P2
- Done when: one old run (skill `research`) is recorded once and replayed twice with the same list of calls (prompt, options, order); stop and report if recording needs a new part or a new dependency
- Notes: spike; decides whether T-CV-04 is a small task. Eval budget: none, no model run needed once recorded; the recording itself is one run of one case on MP-light (about 5 s)

### T-CV-02: Settings record of the equivalence check
- Implements: REQ-WFM-069 (D-187: starting values are configuration, versioned, one fixed version per run)
- Tests to turn green: TC-WFM-069
- Touches: the configuration record and its reader in N-2.3
- Must not touch: protected material, the numbers of the criteria (margin, repeats, rule are defaults of version 1: 0.10, 3, threshold)
- Depends on: P1, P2
- Done when: a changed margin creates version n+1; a new result names n+1, an earlier result still names n
- Notes: no eval run

### T-CV-03: Per-skill state, old runner until accepted, record of the check
- Implements: REQ-WFM-057, REQ-WFM-059, REQ-WFM-060
- Tests to turn green: TC-WFM-057, TC-WFM-059 (scripted run files of `eval_decide.py`), TC-WFM-060 (inspection)
- Touches: the skill record state in N-2.3, the record of the check (suite, run, pins, verdict or reason); the reasons of the nine skills that stay on the old runner (chat, check_speech, memory_write, summarize, the five review skills) as in `eval-spec.md`
- Must not touch: protected material, skill files in `skills/` (no change of any prompt)
- Depends on: T-CV-02
- Done when: a skill whose criterion passes is accepted; one that fails or is not decided stays on the old runner; every skill record names its form and a verdict or a reason
- Notes: no model run; versions: records start at version 1, no skill file or pipeline changes, so no version bump

### T-CV-04: Same calls on scripted replies
- Implements: REQ-WFM-058
- Tests to turn green: TC-WFM-058 for each converted skill
- Touches: the converted runner path of N-2.3 (calls only, no prompt text)
- Must not touch: protected material, prompts, schemas, tools, budgets of any skill
- Depends on: T-CV-01, T-CV-03
- Done when: per skill the list of model calls of the old and the converted run on the recording is equal, a diff is shown otherwise
- Notes: the main guard of the conversion; the suite run is the second guard (miss 0.10 to 0.27 at a loss of 0.20 in `eval-spec.md`)

### T-CV-05: Snapshots
- Implements: REQ-WFM-061 to REQ-WFM-066
- Tests to turn green: TC-WFM-061 to TC-WFM-066
- Touches: the snapshot operations of N-2.3 through the provider mocks (IF-203 v1, IF-301 v2); the owner check as defined in REQ-WFM-066 (account that creates accounts)
- Must not touch: protected material, `contracts/`, the snapshot store of STORE (used through its interface)
- Depends on: P1
- Done when: the six checks pass with the mocks; the automatic snapshot is named "before restore of <name>" with the owner as author
- Notes: independent of the conversion tasks; can run in parallel with T-CV-01 to T-CV-04

### T-CV-06: Convert research and plan_question
- Implements: REQ-WFM-110, REQ-WFM-111
- Tests to turn green: TC-WFM-110 (EV-research dev), TC-WFM-111 (EV-plans dev), after TC-WFM-058 for both skills
- Touches: the skill records and workflow graphs of the two skills; skill and pipeline versions: records 1, the old skill files and pipelines unchanged (a change of any of them is a separate task with its own bump)
- Must not touch: protected material, `eval/suites/`, `eval/baselines/`, prompts
- Depends on: T-CV-04, P3, P4
- Done when: both criteria PASS on the dev split (`python tools/eval.py run <suite> --pin MP-light --repeats 3`, `eval_decide.py` against the baseline run file); a FAIL is re-run once with fresh seeds, never more; a failing skill stays unconverted with the reason recorded
- Notes: eval budget on MP-light from the baselines: EV-research 20 cases x 3 x about 5 s = about 5 min; EV-plans 36 x 3 x about 2 s (an estimate: one model call per plan, not measured) = about 4 min. Run outside the implementation loop, one model loaded

### T-CV-07: Convert verify_claim and verify_computable
- Implements: REQ-WFM-112, REQ-WFM-113
- Tests to turn green: TC-WFM-112 (EV-verdicts dev), TC-WFM-113 (EV-computable dev), after TC-WFM-058
- Touches / Must not touch: as T-CV-06
- Depends on: T-CV-04, P3, P4
- Done when: both criteria PASS on the dev split, same re-run rule
- Notes: eval budget: EV-verdicts 50 x 3 x about 1.4 s = about 3.5 min; EV-computable 39 x 3 x about 8.4 s = about 16 min. The baselines of both come from 1 run, so P4 must record 3 repeats first; if they differ from the summaries by more than the margin, stop and report

### T-CV-08: Convert extract_claims and extract_claims_rules
- Implements: REQ-WFM-114, REQ-WFM-115
- Tests to turn green: TC-WFM-114 (EV-extraction dev, model), TC-WFM-115 (51 outputs equal, no model)
- Touches / Must not touch: as T-CV-06
- Depends on: T-CV-04, P3, P4
- Done when: TC-WFM-115 equal on all 51 cases; REQ-WFM-114 PASS on the dev split
- Notes: eval budget: 51 x 3 x about 2.2 s = about 6 min for the model skill; none for the rule-based one

### T-CV-09: Stage 4 steps and the per-suite check runner
- Implements: TC-WFM-110 to TC-WFM-114 as steps of `stages.yaml` (closes the gap noted in Plan step 3)
- Tests to turn green: `run_stages.py --stages stages.yaml --upto 4 --dry-run` lists one step per suite; a unit test of the runner on a scripted run file (PASS and FAIL)
- Touches: `stages.yaml`, a small runner in `tools/` that calls `tools/eval.py run` and `eval_decide.py` with the criterion line of the requirement
- Must not touch: protected material, `tools/eval.py` behaviour, repeats, seeds, margin or rule (they come from the settings record of T-CV-02)
- Depends on: T-CV-06
- Done when: the five steps are in stage 4 with `needs: [acceptance]`; `required_for_merge` stays 1 to 3 unless the owner decides otherwise
- Notes: stage 4 is long (about 35 min for all five on MP-light); a new tool inside an existing node, no new part; stop and report if it needs a dependency

## Not in this plan
- OC-3 (fresh start with one configuration file and one command) has no requirement in the scope of this subgoal; it is the check of the parent goal G-V2 at integration.
- Packaging and deployment: part of G-V2, not of this subgoal.
- Review skills and the four unconverted skills: their own later subgoal (owner, 2026-11-07).
