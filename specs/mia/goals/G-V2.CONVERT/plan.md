# Plan: G-V2.CONVERT (conversion of the skills and snapshots)

**Requirements:** REQ-WFM-057 to 066, 069, 110 to 115 in `specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md`   **Test spec:** the same folder `test-spec.md` and `specs/mia/test-spec.md` (statistical checks)   **Eval spec:** `specs/mia/eval-spec.md`, section "G-V2.CONVERT"   **Status:** Draft (Plan step 5, 2026-11-07; not reviewed)

Written because two gaps of Plan step 3 cannot be closed in Plan: `stages.yaml` has no stage 4 step for TC-WFM-110 to 114, and the red tests do not exist. Both depend on things that appear later (the converted runner, the protected folders). They are tracked here as tasks and preconditions, not left open.

## Preconditions (nothing of Implement starts before all of them)
| # | Precondition | Owner | State |
|---|---|---|---|
| P1 | G-V2.STORE, MODEL and TOOLBOX are merged (parallel-work.md) | owner | met 2026-11-15: STORE, MODEL and TOOLBOX are in master |
| P2 | Step 4 done: red tests for the checks below in `tests/acceptance/`, helpers, fake model server with recorded replies; tag `plan-baseline-it2` | a dedicated test-writing session, reviewed by the owner | met: red tests committed (plan-baseline-it2-convert), amended 2026-11-15 after A-121 (D-242) |
| P3 | A-120 applied: tag `split:dev` on the cases of EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction (protected eval material) | owner | owner applies A-120 change 1 (owner agreed to apply it himself in the session of 2026-11-15); not yet confirmed |
| P4 | Baselines recorded as run files: dev split, 3 repeats, MP-light, per skill and variant of `eval-spec.md` (results only; `eval/baselines/` is protected) | owner or a harness run the owner starts | runs done 2026-11-15 (data/eval, 3 repeats, MP-light, A-122); the owner places the five files in eval/baselines/ |
| P5 | The ten proposed plausibility items rated; the margin 0.10 of REQ-WFM-110 to 114 judged against the recorded baselines (D-260 D probe) | owner | done 2026-11-15: ten items rated (D-245), margin kept, REQ-WFM-110 and 113 raised (A-122, D-244); written to plausibility.yaml |
| P6 | REQ-WFM-057 to 066, 069, 110 to 115 Approved in the review log with their final text | owner | done 2026-11-15: REQ-WFM-057 to 066, 069, 115 approved earlier; 110 to 114 approved with their final text |

## Task list
Task ids carry the prefix CV so that they do not collide with T-01 to T-11 of the N-2.3 plan. Riskiest first.

| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-CV-01 Recording of the old run (spike) | REQ-WFM-058 | TC-WFM-058 can be written against recordings: model replies and tool results of one old run replay deterministically | P1, P2 |
| T-CV-02 Settings record of the equivalence check | REQ-WFM-069 | TC-WFM-069 | P1, P2 |
| T-CV-03 Per-skill state, old runner until accepted, record of the check | REQ-WFM-057, REQ-WFM-059, REQ-WFM-060 | TC-WFM-057, TC-WFM-059, TC-WFM-060 | T-CV-02 |
| T-CV-03a The three-argument call of the graph runner (Stage) | REQ-RUN-030 to REQ-RUN-034 (A-124) | TC-RUN-030 to TC-RUN-034; TC-RUN-016 to 019 unchanged | T-CV-03 |
| T-CV-03b Common operations module and thin toolbox entries | REQ-WFM-058 (precondition), A-123 P1b | every shipped toolbox transform runs: `toolbox.run(id, args)` gives the result of its library node on recorded inputs; a view runs as a model step with its prompt and schema as data | T-CV-03 |
| T-CV-03c Order of independent steps | REQ-WFM-058 (precondition), A-123 P4 | the graph built from an ordered list of steps has `order_of` equal to that list; no edge joins two process nodes (R3) | T-CV-03b |
| T-CV-03d Pipeline to graph converter | REQ-WFM-058 (precondition), A-123 P2, P3 | a pipeline JSON becomes a graph that passes the graph rules: stages are transforms, a loop or a map over an unknown number of items is a master node with `stop` | T-CV-03c |
| T-CV-04 Same calls on scripted replies | REQ-WFM-058 | TC-WFM-058 for each skill converted in T-CV-06 to T-CV-08 | T-CV-03d |
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

### T-CV-03a: The three-argument call of the graph runner (Stage)
- Implements: REQ-RUN-030 to REQ-RUN-034 (A-124, D-248 C, D-249, D-250)
- Tests to turn green: new `tests/acceptance/test_graph_run_stages.py` written first (red, protected folder, the owner's go and placement): TC-RUN-030 to TC-RUN-034; the four old checks of `test_graph_run.py` stay green
- Touches: `graph_run.py` (class `Stage(function, prepare=None)`; the run reads edge fields `as` and `role` and the graph node `value`, builds inputs, outputs and the settings object, calls prepare once before the Stage, writes per output; plain callables unchanged)
- Must not touch: protected material, `contracts/`, the verified behaviour of REQ-RUN-016 to 019
- Depends on: T-CV-03
- Done when: the four new checks and the four old checks are green
- Notes: all configuration of a transform lives in the `value` of data nodes (A-124 R2); no change of IF-301

### T-CV-03b: Common operations module and thin toolbox entries
- Implements: precondition of REQ-WFM-058; A-123 (owner decisions 2026-11-15, P1 and P1b)
- Tests to turn green: new, written first (red) for the owner's go: `toolbox.run` of each shipped id on recorded inputs equals the library node's result (code, check, tool and rule nodes); a view runs as a model step whose prompt and schema come from data (scripted model)
- Touches: a Python module of common operations (the functions the library nodes name, `FUNCTIONS` registries of research.py and the others, moved there without change of behaviour), the code text of the shipped toolbox entries (thin: they call the module by name), `toolbox.py` only to run them
- Must not touch: protected material, prompts, the old pipelines and their results, any behaviour of a function; one-off functions (no second user) stay in their toolbox entry as code text, common ones live in the module (owner: no duplicates)
- Depends on: T-CV-03a
- Done when: every shipped transform runs from the toolbox and the old runner still gives its old results (TC-WFM-058 old side unchanged)
- Notes: about 50 code, check, tool and rule nodes and 21 views; the module is a move, not a rewrite; model-step views use the prompt and schema of the skill as data

### T-CV-03c: Order of independent steps
- Implements: precondition of REQ-WFM-058; A-123 P4 (owner: enforce the order with an artificial dependency)
- Tests to turn green: new, written first: a builder gives, for an ordered list of steps, a graph whose `order_of` is that list, by letting a later transform read the data node of an earlier step's output without using it; no edge joins two process nodes
- Touches: a graph builder next to `graph_model.py`/`graph_rules.py` (no change of the rules)
- Must not touch: protected material, `contracts/`, the graph rules
- Depends on: T-CV-03b
- Done when: the order of the recorded runs of the five skills is reproduced by the built graphs

### T-CV-03d: Pipeline to graph converter
- Implements: precondition of REQ-WFM-058; A-123 P2 and P3
- Tests to turn green: new, written first: `plan.free@1`, `verify.single@1`, `extract.llm@1` convert to graphs that pass the graph rules; `verify.computable@2` and `research.escalate@3` convert with master nodes for the loop and for a map over an unknown number of items (`stop` from the loop's maximum cycles or the map bound and the skill budget's seconds, `task` empty); a branch between fixed alternatives stays inside a transform
- Touches: the converter in N-2.3 (reads `library/pipelines`, writes graphs and a minimal context graph and the skill record through the existing stores)
- Must not touch: protected material, `contracts/`, `library/pipelines` (read only), prompts
- Depends on: T-CV-03c
- Done when: the five pipelines convert; nothing is run on a model
- Notes: a node of the pipeline that cannot be placed by the rule of A-123 P2 keeps its skill on the old runner with that reason (REQ-WFM-057)

### T-CV-04: Same calls on scripted replies
- Implements: REQ-WFM-058
- Tests to turn green: TC-WFM-058 for each converted skill
- Touches: the converted runner path of N-2.3: `run_converted` reads the skill record and its graph, merges `skill_changes` into the data node that holds the model options, runs the graph with the adapter of T-CV-03b (A-123); the comment of TC-WFM-058 changes accordingly (protected, amendment)
- Must not touch: protected material, prompts, schemas, tools, budgets of any skill
- Depends on: T-CV-01, T-CV-03d
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

### Order of the conversions (owner, A-123 P5, 2026-11-15)
The tasks T-CV-06 to T-CV-08 keep their groups, but the skills are converted in this order: plan_question, verify_claim, extract_claims_rules and extract_claims, then verify_computable, then research (the largest: 50 calls, 6 maps, 8 branches, 1 loop). Each skill has its own equivalence check; a failing skill stays on the old runner with the reason recorded.

### Wiring found before the conversions (checked 2026-11-15 against `library/pipelines`, after T-CV-03b)
- plan_question (plan.free@1), verify_claim (verify.single@1), extract_claims (extract.llm@1): use no placeholder function of `common_operations` and no tool; they can be converted as soon as T-CV-03c, T-CV-03d and T-CV-04 are done.
- verify_computable (verify.computable@2): uses `check.script` (function `script_check`, a placeholder until `common_operations.bind` is called by the app with the sandbox): a small task T-CV-07a binds it (sandbox wiring, trust of scripts the model wrote, no new permission) before this skill is converted; it needs the owner's look because it runs generated code in the sandbox.
- research (research.escalate@3): uses two tools (`tool.web_search`, `tool.fetch_page`) with the budget counting and the IF-402 door of the old runner (D-247 item 5: plain callables only so far) and 22 distinct nodes; a task T-CV-06a decides how a converted run counts budgets and labels trust of tool results before research is converted.
- all five: `model_step` has no budget, token estimate or run events (D-247 item 4); the converted runner path (T-CV-04) adds them or the check shows the difference.

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
