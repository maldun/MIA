# Verification report: G-V4.GRAPHAPI.RULES (one rule set for graphs)

**Goal:** G-V4.GRAPHAPI.RULES (subgoal of G-V4.GRAPHAPI), supervised, accepted by Stefan Reiterer (owner); agent decisions by delegation (D-423)
**Branch:** `goal/v4.graphapi.rules` @ f6854766 (Implement started at b5f494ce, plan gate)   **Plan baseline:** `plan-baseline-g-v4-rules` (71523f7a)
**Date:** 2026-11-22   **Reviewer:** an independent AI reviewer (Opus 5.5, fresh context, never saw the implementation chat); no person has read this report yet

## Verdict
**Proposal: verified with accepted deviations**, if the owner decides V-1 (medium). Each of the 31 requirements in scope (28 new, 3 changed) has a green check. Each check ran under its test requirements. The measures HR-004 to HR-006 are met. Protected material differs from the baseline only by A-170b (D-428), and the installed files match the staged copies byte for byte. Every TR-RULES-008 defect I put in on a scratch copy made its check fail. Nothing agentic was touched: no skill, prompt, pipeline, eval suite or model pin.

V-1 is a real gap. `rule_report`, `run_check`, `check_graph`, the save and the run raise `TypeError` when a connection's `from`, `to`, `id`, `role` or `as` is a list or an object. REQ-GTB-040 says a check never raises, and its own definition of malformed includes "a non-text ID or end". goal/v4 raised in the same way, so this is not a regression, but RULES promised to fix it. The other findings are a contract sentence the code contradicts (V-2), unspecified behaviour (V-3, V-4) and record nits (V-5 to V-7).

- [ ] Verified by Stefan Reiterer (owner). Date:

## Automated checks (all run by me; Python 3.12 venv `mia312`)
| Check | Result |
|---|---|
| Clean state | `git status` clean at f6854766 (only ignored caches, `mia.log`, `data/`). Unit suite in a fresh `git archive HEAD` copy under `/home/maldun/.claude-work/jobs/85fdeba4/tmp/verify/clean/`; acceptance scripts in the worktree, one by one, not in parallel with anything else |
| Unit suite `unittest discover -s tests` (fresh copy) | Ran 2548 in 484 s: **OK** (skipped 5, expected failures 2) |
| RULES acceptance files | `test_rules_rule_set.py` 9 OK (TC-GTB-037 to 045; TC-GTB-045 ran the 8 document-form suites and `git diff --quiet goal/v4` on each); `test_rules_save.py` 6 OK (TC-WFM-179 to 184); `test_rules_run.py` 4 OK (TC-RUN-036 to 039); `test_rules_measures.py` 3 OK (TC-GTB-046 both graphs × 5 repeats, TC-GTB-047, TC-RUN-040). No `skip`/`xfail` in any RULES acceptance file, helper or smoke script |
| IF-301 v4 contract suite `contract/test_if_301_v4_rule_set.py` | 16 OK: golden 24 to 31 (TC-IF-301-27 to 34), each on the real side and on the mock side |
| New and changed unit tests | `test_graph_rule_set.py` 10 OK, `test_graph_model_rule_set.py` 8 OK, `test_graph_run_rule_set.py` 4 OK, `test_graph_run_findings.py` 10 OK |
| SMOKE-RULES-001 `tests/smoke/smoke_rules.py` (on the branch) | **pass**: 15 skills ready; `sample.broken` refused naming `['e2']`, no step run. The run on the owner's host belongs to Deploy |
| TC-GTB-047 record | 57 graphs newly refused (42 `duplicate_connection`, 15 `single_writer`), the same counts as prototype round 04. The only "lost" graph is the named `max_seconds: 1.0` exception |
| Regression: every acceptance script one by one | 70 scripts (Python and `.mjs`, `tests/acceptance/` and `contract/`), sequential, 127 s in all: **68 exit 0**. The 2 red ones are the known reds outside RULES, `test_decide_guard.py` and `test_judge_calibration.py`, both failing on import (G-V3.REPORT F-3), as on goal/v4. Among the green: the IF-301 v1 to v3 suites, `test_graph_run.py` (TC-RUN-016, 017), `test_graph_run_stages.py` (TC-RUN-033, 034), `test_core_save.py` (TC-WFM-164, 168), `test_pipeline_graph.py`, `test_skill_binding.py`, `test_graph_order.py` |
| My TR-RULES-008 defects (scratch copies, below) | 8 defects: every one caught |
| Protected material vs. `plan-baseline-g-v4-rules` | only `tests/acceptance/test_rules_measures.py`, identical (`diff`) to `specs/mia/amendments/A-170b/tests/acceptance/test_rules_measures.py` (A-170b, D-428). `tests/helpers`, `tests/smoke`, `tests/integration`, `contracts`, `benchmarks`, `stages.yaml`, `specs/mia/test-requirements.md`: no change since the tag |
| Protected material vs. `goal/v4` | `contracts/IF-301-graph-tables.md` matches the A-170 staging text. The suite `contract/test_if_301_v4_rule_set.py` and the mock `helpers/mocks/if_301_graph_tables_v4.py` match their A-170 staging copies. `helpers/rules_graphs.py`, `smoke/smoke_rules.py` and the four `test_rules_*.py` match `red-tests/` (the red commit 71523f7a; measures as amended by A-170b). Nothing else changed |
| `trace_check.py` (temporary folder with the RULES `*.md` files and `specs/mia/architecture.sysml`) | 30 errors, 659 warnings. No error names a RULES item. 8 RULES warnings, "no marker": REQ-GTB-036, 038, 042 to 046, 050. Each of these IDs **has** a marker, but not as its first argument, and `trace_check.py` reads only the first argument of `mark.req(...)` (line 179). So this is a limit of the tool (V-7), not missing evidence |
| `goal_check.py --parent-ref goal/v4` | RULES: GL11 (size) only, decided in the split check (D-418 (3)) |
| `tools/check_sysml_model.py .`, `tools/check_sysml.sh specs/mia/architecture.sysml` | OK (40 acceptance criteria); 0 errors, 0 warnings |
| `test_doc_check.py --tests-dir tests` | no finding in a RULES file (the findings it lists are in older contract suites) |
| `refactor_check.py --base plan-baseline-g-v4-rules`, `agent_config_diff.py --base goal/v4` | 0 refactoring commits; no configuration change |
| Static, security, dependencies | No linter or SAST is configured (CLAUDE.md). No new dependency or import (`graph_rule_set.py` imports only `copy`, `math`). No `eval`, `exec`, `subprocess`, `open` or `pickle` in the three product files. I read all three product files in full |

## Verification matrix
| Requirement | Method | Evidence (run by me) | TR | Result |
|---|---|---|---|---|
| REQ-GTB-033 one registry | Test | TC-GTB-037, TC-IF-301-27 (real, mock) | 001, 007, 008 | Pass |
| REQ-GTB-034 eight rules in order | Test | TC-GTB-037, TC-IF-301-27, TC-GTB-047; my swap defect caught by TC-GTB-037 and golden 24 | 001, 003, 008 | Pass |
| REQ-GTB-035 context rules | Test | TC-GTB-037, TC-GTB-038, TC-IF-301-31 | 001, 002, 007 | Pass |
| REQ-GTB-036 run flags | Test | TC-GTB-037, TC-IF-301-27 | 001, 007 | Pass |
| REQ-GTB-037 rule report | Test | TC-GTB-039, TC-IF-301-29; "first rule only" defect caught by TC-GTB-039 and TC-GTB-046 | 001, 002, 008 | Pass |
| REQ-GTB-038 no kind = workflow | Test | TC-GTB-039, TC-IF-301-28 | 001, 002 | Pass |
| REQ-GTB-039 unknown kind | Test | TC-GTB-040, TC-IF-301-32 | 001, 002 | Pass |
| REQ-GTB-040 never raises | Test | TC-GTB-041, TC-IF-301-34 green (the five named cases and a list as graph) | 001, 002 | **Pass as tested; fails for list/object IDs, ends, role or name (V-1)** |
| REQ-GTB-041 to 048 the eight rules | Test | TC-GTB-042 (broken graph and twin per rule, plus edge pairs); "cycle while rule 3 broken" defect caught | 001, 002, 008 | Pass |
| REQ-GTB-049 kind first and alone | Test | TC-GTB-043, TC-IF-301-32 | 001, 002, 004 | Pass |
| REQ-GTB-050 rules, then inputs | Test | TC-GTB-043, TC-IF-301-33 | 001, 002, 004 | Pass |
| REQ-GTB-051 unsupplied input | Test | TC-GTB-044, TC-IF-301-33 | 001, 004 | Pass |
| REQ-GTB-052 document form unchanged | Test | TC-GTB-045 (8 suites green, byte-identical to goal/v4) | 009 | Pass |
| REQ-WFM-162 save with rule set | Test | TC-WFM-179; "report left out" defect caught | 001, 002, 008 | Pass |
| REQ-WFM-163 refusal carries report | Test | TC-WFM-180, TC-GTB-046; defect caught | 001, 002, 008 | Pass |
| REQ-WFM-164 flat list | Test | TC-WFM-181; `test_pipeline_graph.py`, `test_skill_binding.py`, `test_graph_order.py` green | 001, 002 | Pass |
| REQ-WFM-165 never stored → not_found | Test | TC-WFM-182 | 001 | Pass |
| REQ-WFM-150 (changed) refused save writes nothing | Test | TC-WFM-168 (CORE, green), TC-WFM-180 | 001, 002 | Pass |
| REQ-WFM-154 (changed) `kind: null` refused | Test | TC-WFM-172 (CORE), TC-WFM-183 | 001, 002 | Pass |
| REQ-WFM-155 (changed) context rules on save | Test | TC-WFM-173 (CORE), TC-WFM-184 | 001, 002 | Pass |
| REQ-RUN-036 run check before first step | Test | TC-RUN-036 (7 reasons, markers 0 calls, twin calls its marker); my "first step before the check" defect caught | 002, 005, 008 | Pass |
| REQ-RUN-037 every part, repeats kept | Test | TC-RUN-037; "repeats removed" defect caught (TC-RUN-037, 038, TC-GTB-046) | 001, 002, 004, 008 | Pass |
| REQ-RUN-038 trust after | Test | TC-RUN-038; "trust first" defect caught | 001, 002, 008 | Pass |
| REQ-RUN-039 prepare inputs given | Test | TC-RUN-039, TC-RUN-034 (protected, green); implementer's defect (c) logged; see V-4 | 001, 002, 005, 008 | Pass |
| HR-004 same list everywhere | Test (measure) | TC-GTB-046: 2 graphs × 4 entry points × 5 repeats, 0 differences (check route = IF-104 v2 stand-in, wiring only, TR-RULES-007) | 006, 007 | Pass (check route: wiring only until IF-104 v2 is real) |
| HR-005 no old refusal lost | Test (measure) | TC-GTB-047: TC-GTB-002 cases and seeds 1 to 1000; 0 lost except the named `max_seconds: 1.0` | 003 | Pass |
| HR-006 refused before any step, skills ready | Test (measure) | TC-RUN-036, TC-RUN-040 (15 of 15), SMOKE-RULES-001 | 004, 005 | Pass (smoke on the owner's host: Deploy) |

31 of 31 requirements and the 3 measures have a green check; REQ-GTB-040 is met only for the tested inputs (V-1). The results are plausible: the scripts take 0.01 to 3 s (TC-GTB-047 with 1000 seeds included), the pure checks need no store, and every check I mutated failed for the reason it is for.

## Test requirements (M41)
| Test requirement | Source | Applies to | How I verified | Met? |
|---|---|---|---|---|
| TR-RULES-001 exact values | product | 25 checks | read: `assertEqual` on whole items, lists and tuples; no `assertIn` on results | yes |
| TR-RULES-002 small graphs with sound twins | product | 16 checks | read TC-GTB-039 to 044, TC-RUN-036 to 039: graphs written out, at most 8 steps, each broken graph has a sound twin. Some twins differ in more than one place (TC-GTB-042 `stop_limit`, `adjacency`, `single_writer`), but each still shows the item comes from the broken part | yes (Info: "one place" is loose for 3 twins) |
| TR-RULES-003 corpus of old refusals | product | TC-GTB-047 | read: `SEEDS = range(1, 1001)`, the prototype mapping, the one exception named and asserted exactly, counts printed and not asserted | yes |
| TR-RULES-004 converted skills | product | 7 checks | `converted_skills()` builds them at test time, `SKILL_COUNT = 15` guard; the smoke listed 15 | yes |
| TR-RULES-005 markers that can fire | product | TC-RUN-036, 039, SMOKE | read: twin calls its marker; mutation: my "first step before the check" defect makes TC-RUN-036 fail in all 7 reasons. The implementer did not log this mutation; it is closed here | yes |
| TR-RULES-006 every entry point, five times | product | TC-GTB-046 | read: `REPEATS = 5`, a fresh files store per save, item-by-item comparison; the run compared by parts (D-424); the second graph runs with `{"d1": "x"}` (A-170b) | yes |
| TR-RULES-007 stand-ins | product | TC-GTB-046, TC-IF-301-27 to 34 | contract suite green on both sides; the check route counted as wiring only | yes |
| TR-RULES-008 shown able to fail | product | 11 checks | implementer's log covers TC-GTB-037, 039, 042, 043, TC-WFM-179, 180, TC-RUN-037, 038, 039. TC-RUN-036 and TC-GTB-046 were not logged; I covered them (table below). My own runs repeat 037, 039, 042, 179, 180, 037, 038 | yes (with my runs) |
| TR-RULES-009 older suites untouched | product | TC-GTB-045 | the check runs `git diff --quiet goal/v4` per suite file; green in the worktree | yes |

### My deliberate defects (TR-RULES-008), scratch copies `/home/maldun/.claude-work/jobs/85fdeba4/tmp/verify/m1` to `m7` (from `git archive HEAD`, script `mutate.py`)
| Defect | Check | Result |
|---|---|---|
| `adjacency` and `single_writer` swapped in `KINDS` | TC-GTB-037; golden 24 (real side) | both fail; TC-GTB-046 stays green (no graph there breaks both rules) |
| first broken rule only (`report[:1]`) | TC-GTB-039; TC-GTB-042; TC-GTB-046 | all fail |
| cycle asked while rule 3 is broken | TC-GTB-042 | fails (extra `cycle`) |
| repeats removed from a refused run | TC-RUN-037; TC-RUN-038; TC-GTB-046 | all fail |
| trust checked before the run check | TC-RUN-038 | fails (`['T2'], 'untrusted'`) |
| refused save without the rule report | TC-WFM-179, 180, 184 | all fail (`rules` None) |
| first plain step called before the run check | TC-RUN-036 | fails for all 7 refusal reasons (`['t1'] != []`) |

TC-GTB-045 fails in every scratch copy because a `git archive` copy has no `.git`. That is the copy, not the defect, and I did not count it.

## Goal acceptance (supervised goal: for information)
| Item | Result |
|---|---|
| Requirements in scope verified | 31 / 31 (V-1 open on REQ-GTB-040) |
| Frozen requirements unchanged | IF-301 v4 is the shared item; installed by A-170 before the tag, unchanged since |
| Protected checks identical to the baseline | yes, except A-170b (identical to its staging copy; owner's decision D-428) |
| Nothing outside the goal's parts touched | product code: `graph_rule_set.py` (N-3.2), `graph_model.py` (N-2.3), `graph_run.py` (N-2.4.1), all within the plan's touch lists. Also: unprotected tests (three new unit files and the one value in `test_graph_run_findings.py` that the plan names), `tools/gen_node_requirements_model.py` (D-420), the owner's apply scripts, `architecture.sysml`, and the VIEW handover documents (D-427) |
| Stop conditions logged | yes: the TC-GTB-046 conflict was stopped and settled by the owner (A-170b, D-428), not worked around |
| Exit criterion OC-1, OC-2 | OC-1: TC-GTB-046 (save, check route, run, five times), TC-WFM-180; OC-2: TC-RUN-036, 037, TC-GTB-044, smoke |

## Code against the architecture
- `graph_rule_set.py` is listed in `persistence.graphRecords` (`architecture.sysml` line 666), `graph_model.py` in `taskRuntime.workflowGraph`, `graph_run.py` in `taskRuntime.pipelineRunner` (D-420). One module per part, named as in the model.
- `graph_rule_set.py` does not import `graph_model` or `graph_run`. A unit test asserts this, and I confirmed it by reading the imports. `find_cycle` and the stop limit are copies, with a comment saying why.
- New code dependency: `graph_run.py` (pipelineRunner) → `graph_rule_set` (graphRecords). `graph_model.py` → `graph_tables` was there before. The model has no flow or connection between `taskRuntime` and `persistence.graphRecords` for either. The only link is the allocation of IF-301 to `persistence.database` and of FR-63/FR-64 to both parts. As in CORE, the dependency is described by IF-301 (consumers named in its header) but not drawn as a flow (V-6, Info).
- IF-301 v4 as specified: operation names, item fields (`rule`, `parts`, `text`; `kind`, `step`, `input` on run-check items), the sentences in `TEXTS`, parts once except `cycle`, malformed input as the paragraph says. There is one contradiction with the contract text (V-2) and the gap V-1.

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-GTB-040 | raises on unhashable IDs, ends, role or `as` (V-1) | Phase 3 (regression test first) |
| done, contradicts contract text | save order | IF-301 v4 says the Workflow management asks `rule_report` "after the record checks"; the code (and a unit test) asks it **before** them, as CORE did (V-2) | Phase 2: correct the sentence (contract amendment) |
| done, not specified | REQ-RUN-039 scope | a data step read by a preparing Stage counts as given for the whole run, so a plain step reading the same data step is not refused for it (implementer's log; V-4) | owner: state it or narrow REQ-RUN-039 |
| done, not specified | `check_graph` of a non-workflow graph | asks the report of the graph's own kind (context rules; `["swarm"]` for an unknown kind); REQ-WFM-164 speaks of a workflow graph; every caller passes one (log) | accept (info) |
| done, not specified | missing `nodes` / `edges` keys | treated as empty lists, so `{}` gives `[]` (no rule broken); the contract names only "not a list". The record checks refuse a graph without an ID on save | V-3, accept or state |
| done, not specified | `"kind": None` | `unknown_kind` naming `"None"` in check and run; the mock does the same (log) | accept (info) |
| done, not specified | `run_check` with a malformed `given` | counts as nothing given (T-01 finding, D-423), tested | accept (settled by delegation) |
| done, not specified | rule 7 third pass | counts settings connections over all connection objects, so it may name a missing step as target (e.g. `z`); rule 3 names those connections too | accept (info) |

No item is marked `Code review: needed`. I read `graph_rule_set.py`, the diffs of `graph_model.py` and `graph_run.py`, and the changed unit value in full.

## Quality evidence per characteristic (M32)
Touched: functional suitability (matrix); reliability (no raising on malformed graphs: met for the tested inputs, V-1); compatibility (the document-form suites unchanged, TC-GTB-045; 15 skills still ready, TC-RUN-040); security, in a narrow sense: a graph that breaks a rule never runs a step and the run check comes before trust (TC-RUN-036, 038); no evaluation of graph content. Not touched: performance (no bound, D-416 (4)), interaction capability (no user surface), maintainability (one rule set instead of three is the gain), flexibility, safety. `quality_check.py` was not run (no goal-level `quality.md`).

## Open deferrals (M26)
None in the goal's scope.

## Review findings
Severity: High / Medium / Low / Info. The probes are in `/home/maldun/.claude-work/jobs/85fdeba4/tmp/verify/probe/` and are deleted with this job, so each reproduction is given here in full.

| ID | Severity | Where | Finding | Reproduce | Destination |
|---|---|---|---|---|---|
| V-1 | Medium | `graph_rule_set._duplicate_connection` (set of keys and IDs), `_stop_limit` (`settings_in` keyed by `to`); `graph_run._given` (`e.get("to") in preparing`) | `rule_report`, `run_check`, `check_graph`, `GraphModel.save_graph` and `GraphRunner.run` raise `TypeError: unhashable type` when a connection's `from`, `to` or `id` is a list or an object, or when its `data.role` or `data.as` is one. REQ-GTB-040's own definition of malformed includes "a missing or non-text ID or end", and IF-301 v4 says such a connection is rule 3. The five tested cases pass. The save asks the rules before the record checks, so the save raises too. goal/v4 raised the same way, so this is not a regression, but the new requirement is not met | `rule_report({"nodes": [{"id": "a", "data": {"type": "data"}}, {"id": "t", "data": {"type": "transform"}}], "edges": [{"id": "e1", "from": ["a"], "to": "t"}]})` → TypeError; likewise `"id": ["x"]`, `"data": {"role": {"x": 1}}`, `"data": {"as": ["n"]}`, a settings connection with `"to": ["t"]` | Phase 3: a failing unit test first (the five probe graphs, each through the five entry points), then compare only hashable or text values (non-text ends are already rule 3). The fix is in `graph_rule_set.py` and `graph_run._given` |
| V-2 | Low | `contracts/IF-301-graph-tables.md` (v4, "who asks what") vs `graph_model.save_graph` | The contract says the Workflow management asks `rule_report` "after the record checks". The code asks it before them, keeping CORE's order (whole graph first, REQ-WFM-146), and `test_graph_model_rule_set.py` asserts that order. No requirement fixes the order between the two | read both | Phase 2: correct the contract sentence to "before the record checks" (owner-run amendment, no code change); or state the order in REQ-WFM-162 |
| V-3 | Info | `graph_rule_set._view` | A graph without `nodes` or `edges` keys is treated as empty and breaks no rule (`rule_report({}) == []`); the contract covers only "not a list" | `rule_report({})` → `[]` | accept, or state it with the next IF-301 amendment |
| V-4 | Low | `graph_run._given` (REQ-RUN-039) | Implementer's open item, confirmed by reading: an input of a Stage with a prepare function makes its data step given for the whole run, so a plain step reading the same data step is not refused for it (it gets no value). This follows from "given" being counted per data step (IF-301 v4). No test fixes it | log T-03 "Unspecified" | owner: accept as stated (narrowing of FR-64 already accepted in D-418 (1)), or narrow REQ-RUN-039 |
| V-5 | Info | `requirements.md`, `plan.md`, `binding-map.md`, `goal.md` | The records say "27 new, 3 changed" and "30 of 30", but `requirements.md` has 31 items: 28 new (REQ-GTB-033 to 052 = 20, REQ-WFM-162 to 165 = 4, REQ-RUN-036 to 039 = 4) and 3 changed. The binding-map table has 31 rows | `grep -c '^### REQ-' requirements.md` → 31 | fix the counts at the merge (Commit moves the requirements) |
| V-6 | Info | `architecture.sysml` | the code dependencies taskRuntime (`graph_model.py`, `graph_run.py`) → persistence.graphRecords (`graph_rule_set.py`, `graph_tables.py`) have no flow or connection in the model; IF-301's header names the consumers | grep for `graphRecords` | backlog: draw the IF-301 consumer flows with the next model change |
| V-7 | Info | `trace_check.py` (skill tool) | reads only the first ID of `mark.req(...)`, so 8 RULES requirements look unmarked; their markers exist | line 179 of the script | tool backlog, outside the product |

## Accepted-deviation candidates
V-1 (only if the owner chooses not to fix it now; then REQ-GTB-040 needs its definition narrowed to text-valued fields), V-3, V-4, V-5, V-6, V-7. V-2 needs only a sentence corrected.

## Notes for Commit and Validate
- Commit: the merge steps of `plan.md` (move the requirements into N-3.2, N-2.3, N-2.4.1 with the corrected count, V-5; TR-RULES-001 to 009 into `specs/mia/test-requirements.md` by an owner-run script; regenerate the model; fill the Witness columns of AC-017 and AC-018).
- Deploy: SMOKE-RULES-001 on the owner's host.
- Validate (G-V5): whether the sentences of the rule report read well in the editor (EDIT), and whether the 57 newly refused old graphs (duplicate connections, second writers) appear in real stores.
- TC-GTB-046's check-route half is a wiring check until IF-104 v2 is real (TR-RULES-007); the real route is verified in VIEW/EDIT.
