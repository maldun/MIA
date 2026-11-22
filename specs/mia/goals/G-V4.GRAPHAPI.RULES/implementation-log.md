# Implementation log: G-V4.GRAPHAPI.RULES

Goal: G-V4.GRAPHAPI.RULES   Line of work: goal/v4.graphapi.rules   Supervision: supervised (agent's own recommendations delegated by the owner, D-423)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 The rule set module | done | see `git log` ("feat: T-01 the rule set module") | TC-GTB-037 to 045, TC-GTB-047, TC-RUN-040, TC-IF-301-27 to 34 (mock and real), `tests/test_graph_rule_set.py` (9 unit tests) | TC-GTB-046 stays red until T-04 (needs T-02's `SaveResult.rules`) |
| T-02 The save path on the rule set | done | see `git log` ("feat: T-02 the save path on the rule set") | TC-WFM-179 to 184; TC-WFM-164, 168 and the three `check_graph(...) == []` tests kept; `tests/test_graph_model_rule_set.py` (8 unit tests) | `context_problems` removed (no caller left) |
| T-03 The runner asks the run check | done | see `git log` ("feat: T-03 the runner asks the run check") | TC-RUN-036 to 039; TC-RUN-016, 017, 033, 034 kept; `tests/test_graph_run_rule_set.py` (4 unit tests); `tests/test_graph_run_findings.py` (self-loop value changed) | TC-GTB-046: graph `second` conflicts with REQ-RUN-037 (finding, for T-04) |

## T-01: The rule set module

**What was done**
- `graph_rule_set.py` replaces the stub, adapted from the prototype `graph_rules_proto.py` (reuse map R3): `KINDS`, `TEXTS`, the eight rule functions, `rule_report` (was `check`), `run_check` (was `refusal` plus `missing_inputs`).
- Changes against the prototype: the names of IF-301 v4; `kinds()` returns a deep copy; every run-check item carries `rule` (`unsupplied_input` for an input item, with `step`, `input`, `parts` = [data step ID], `text`); `given` is counted by its keys (`set(given or ())`, so a value of None counts as given); malformed input as IF-301 v4 "Malformed input" says (D-418 (2)); the graph is read once into a view (existing steps, connections that are objects, connections between existing steps) that every rule uses, so no rule raises.
- No import of `graph_model`: `find_cycle`, `_limit` and the stop-limit check are copied (with a comment why), as the protected mock does.
- `specs/mia/architecture.sysml`: `graph_rule_set.py` added to the modules of `persistence.graphRecords`, "(planned)" dropped from its doc. `check_sysml_model.py` OK, `check_sysml.sh specs/mia/architecture.sysml` 0 errors, 0 warnings.
- Unit tests `tests/test_graph_rule_set.py`, written first and seen red against the stub (16 failures, 1 error): no import of graph_model/graph_run, deep copy of the registry, purity of the report, more malformed inputs (edges not a list, a connection that is a number, step data that is a list, a non-text connection ID, a list as step ID, `{}`), `run_check` on malformed graphs, the cycle not asked while rule 1 is broken, valid and invalid stop limits, `given` as mapping/list/set, a master's input and repeated inputs in connection order. `test_doc_check.py`: 0 findings.

**Tests green (my runs, feedback only):** `tests/acceptance/test_rules_rule_set.py` 9/9; `tests/acceptance/contract/test_if_301_v4_rule_set.py` 16/16 (mock and real); `tests/acceptance/test_rules_measures.py` TC-GTB-047 and TC-RUN-040 (TC-GTB-047 printed: refused only by the eight rules `{'duplicate_connection': 42, 'single_writer': 15}`, total 57); `tests/test_graph_rule_set.py` 9/9.

**Regression set (2026-11-22, sequential):** unit suite `discover -s tests` exit 0; 66 of 71 acceptance scripts (Python and `.mjs`) exit 0. Red: `test_decide_guard.py`, `test_judge_calibration.py` (known, G-V3.REPORT F-3); `test_rules_measures.py` (only TC-GTB-046, 10 sub-failures, all `SaveResult.rules` is None: T-02/T-04), `test_rules_save.py` (T-02), `test_rules_run.py` (T-03). No unexpected red.

**Deliberate-defect check (TR-RULES-008), on scratch copies under `/home/maldun/.claude-work/jobs/85fdeba4/tmp/defects/`:**

| Defect in `graph_rule_set.py` | Check | Result |
|---|---|---|
| (a) `adjacency` and `single_writer` swapped in `KINDS` | TC-GTB-037 | fails (registry differs) |
| (b) only the first broken rule reported (`return report[:1]`) | TC-GTB-039 | fails (single_writer missing) |
| (c) the cycle asked while rule 3 is broken (`if view["identity"]:`) | TC-GTB-042 | fails (extra `cycle` with the missing end e9) |
| (c) as above | TC-IF-301-30 (golden 27, real side) | fails (extra `cycle`) |
| (d) inputs listed before rules in `run_check` | TC-GTB-043 | fails (order input, rule) |
| (e) a kind that cannot run also lists its rule items | TC-GTB-043 | fails (extra duplicate_connection) |

TC-GTB-043 passes under each of (a), (b) and (c): none of the three named defects reaches it, so (d) and (e) were added (see Findings).

**Deviations:** none from the plan's touch list. The defects (d) and (e) are additions to the three named in the task.

## T-02: The save path on the rule set

**What was done**
- `graph_model.py`: `save_graph` keeps CORE's order of checks: the kind first (an unknown kind or an explicit `"kind": None` stays `schema_break` / `kind`, REQ-WFM-154 changed, with no rule report), then `graph_rule_set.rule_report(graph)` for the graph's kind (REQ-WFM-162, REQ-WFM-155 changed), then the record checks of the Storage layer (unchanged). A refusal for broken rules is `SaveResult(False, None, named, None, None, rules)`: `rules` is the rule report (REQ-WFM-163, ASM-8), `named` the parts of every item in order, repeats kept (REQ-WFM-150 changed).
- `SaveResult` has the new last field `rules` (default None); every other result leaves it None.
- `check_graph(graph)` is the flat list of the parts of the rule report (REQ-WFM-164), one helper `_parts` shared with the save path. It asks the report of the graph's own kind (no kind means workflow), as the save does; every caller passes a workflow graph.
- Removed as dead code: `context_problems` (its only caller was `save_graph`; grep over the repo), the five-rule body of `check_graph`, `stop_is_valid`, `_limit`, `_node_type`, `NODE_TYPES`, `import math` (the copies in `graph_rule_set.py` are the ones in use). `find_cycle` and `order_of` stay (the runner and `tests/test_graph_run_findings.py` use them).
- Unit tests `tests/test_graph_model_rule_set.py` (8), written first and seen red (8 errors on the missing field, 1 failure): the report and `named` of a refusal with two broken rules; kind before rules (`swarm` and `None` with broken rules give only `kind`); rules before record checks (a rule and a record fault give the rule; a record fault alone gives the record rule, no report); a saved graph has `rules` None on the Storage layer and on the fake; the fake goes through the same report; a context graph with a cycle and a repeated step names only `step_identity`; `check_graph` is the flat parts; `check_graph` names a connection to a missing step instead of raising.

**Tests green (my runs, feedback only):** `tests/acceptance/test_rules_save.py` 6/6; `test_core_save.py` (TC-WFM-164, 168), `test_pipeline_graph.py`, `test_skill_binding.py`, `test_graph_order.py`, `test_graph_model.py`, the other CORE acceptance files; unit `test_graph_model_save.py`, `test_graph_model_context.py`, `test_graph_model_read.py`, `test_skill_record_storage.py`, `test_graph_run_findings.py`, `test_graph_model_rule_set.py`.

**Regression set:** (2026-11-22, sequential) unit suite `discover -s tests` exit 0 (2544 tests, OK, 5 skipped, 2 expected failures); 66 of 70 acceptance scripts (Python and `.mjs`) exit 0. Red: `test_decide_guard.py`, `test_judge_calibration.py` (known, G-V3.REPORT F-3); `test_rules_run.py` (T-03); `test_rules_measures.py` (only TC-GTB-046, 10 sub-failures, now all on the run's list, e.g. run `['d1', 't1', 'd1']` against the save's `['e4', 'd1', 'd1', 't1', 'd1']`: T-03). No unexpected red.

**Deliberate-defect check (TR-RULES-008), scratch copy `/home/maldun/.claude-work/jobs/85fdeba4/tmp/defects2/t02/`:**

| Defect in `graph_model.py` | Check | Result |
|---|---|---|
| (a) the save path left on CORE's `check_graph` / `context_problems` (the file of the T-01 commit, only `SaveResult.rules` added so the checks reach their assertions) | TC-WFM-179, TC-WFM-180 | both fail (`rules` None; 179 also no `duplicate_connection`); TC-WFM-181 and 184 fail too |
| (b) the new `check_graph`, but the save path asks it and returns `SaveResult(False, None, named)` without the report | TC-WFM-179, TC-WFM-180 | both fail (`rules` None); TC-WFM-184 fails too |

**Deviations:** none from the touch list (`graph_model.py`, one new unit test file).

**Findings:** none.

## T-03: The runner asks the run check

**What was done**
- `graph_run.py`: `GraphRunner.run` first asks `graph_rule_set.run_check(graph, given)` (REQ-RUN-036); when it answers refused the run returns `RunResult("refused", <parts of every item in the check's order, repeats kept>, None, <the data values of the run's inputs, as before>)` before any step and before the trust callback is asked (REQ-RUN-037, REQ-RUN-038). The old unknown-end and cycle check is gone, and with it the import of `find_cycle` (it stays in `graph_model.py` for `tests/test_graph_run_findings.py`). The trust check (REQ-RUN-017) and the wiring check (REQ-RUN-033) follow unchanged, only for a ready graph.
- `given` = the keys of the run's `inputs` plus every data step with a connection into a step whose function in `nodes` is a `Stage` with a prepare function (`_given`, REQ-RUN-039, D-418 (1)).
- The step types are read leniently (`_kinds`) before the check, so a malformed graph is refused by the run check instead of raising a `KeyError`.
- `tests/test_graph_run_findings.py`: only the self-loop case changed, the expected `named` is now `["T1>T1", "T1", "T1"]` (a transform connected to itself also breaks `adjacency`, REQ-GTB-045), with a comment saying why. Nothing else in that file.
- Unit tests `tests/test_graph_run_rule_set.py` (4), written first and seen red against the old runner (1 failure, 2 errors): a Stage without a prepare function does not make its inputs given; a run input given as None counts as given; a refused run asks no trust and answers the given data values; a malformed graph (a step without data, `nodes` not a list) is refused, not raised.

**Tests green (my runs, feedback only):** `tests/acceptance/test_rules_run.py` 4/4; `test_graph_run.py` (TC-RUN-016, 017), `test_graph_run_stages.py` (TC-RUN-033, 034); `tests/test_graph_run_findings.py` 10/10; `tests/test_graph_run_rule_set.py` 4/4. The skill and conversion tests: see the regression set.

**Regression set:** (2026-11-22, sequential) unit suite `discover -s tests` exit 0 (2548 tests, OK, 5 skipped, 2 expected failures); 67 of 70 acceptance scripts (Python and `.mjs`) exit 0, among them `test_rules_run.py`, `test_graph_run.py`, `test_graph_run_stages.py`, `test_skill_binding.py`, `test_pipeline_graph.py` and the conversion files. Red: `test_decide_guard.py`, `test_judge_calibration.py` (known, G-V3.REPORT F-3); `test_rules_measures.py` (only TC-GTB-046 graph `second`, 5 sub-failures, see Findings). No unexpected red.

**Deliberate-defect check (TR-RULES-008), scratch copies `/home/maldun/.claude-work/jobs/85fdeba4/tmp/defects2/t03a`, `t03b`, `t03c` (script `../defects_t03.py`):**

| Defect in `graph_run.py` | Check | Result |
|---|---|---|
| (a) repeats removed from `named` (`dict.fromkeys`) | TC-RUN-037 | fails (`wf-cycle` loses the closing D1); TC-RUN-038 fails too |
| (b) the trust check before the run check | TC-RUN-038 | fails (`["T2"], "untrusted"` instead of the cycle) |
| (c) prepare inputs not counted as given (`given` = the run's inputs only) | TC-RUN-039, TC-RUN-034 | both fail (`refused` instead of `done`; TC-RUN-034 in two cases) |

**Deviations:** none from the touch list (`graph_run.py`, the one value in `tests/test_graph_run_findings.py`, one new unit test file).

**Findings:**
- TC-GTB-046 (T-04's check, protected, `tests/acceptance/test_rules_measures.py`) stays red after T-03, now only for its graph `second` (5 sub-failures; graph `first` is green): the run names `['e9', 'e3', 'd1', 'd1']`, the check expects `['e9', 'e3', 'd1']`, the parts of the rule report alone. The extra `d1` is the unsupplied-input item: `d1` (with `session: true`, no `value`) is read by `t1`, has no writer and the test runs with `{}`. IF-301 v4 `run_check` lists every rule item and then every unsupplied input, and REQ-RUN-037 makes the runner name the parts of every item, so the runner cannot give the expected list without breaking REQ-RUN-037 or the contract. Proposal for the owner (before T-04): either give `d1` a value in the graph `second` of TC-GTB-046 (or run it with `{"d1": ...}`), or compare the run with the parts of the rule items of `run_check` only; a change of a protected test, so a plan amendment. Not chased in T-03 (task bounds).
- Unspecified (REQ-RUN-039 as written): a data step read by a preparing Stage counts as given for the whole run, so another, plain step reading the same data step is not refused for it either (it gets no value). The run check counts `given` per data step (IF-301 v4), so this follows from the text; no test fixes it.

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| TR-RULES-008 lists TC-GTB-043 among the checks to be shown able to fail, but none of its three rule-set defects (swap, first only, cycle with rule 3 broken) makes TC-GTB-043 fail; two run-check defects (inputs before rules, kind not alone) do. Proposal for Verify: name a run-check defect for TC-GTB-043 in TR-RULES-008 (a text change of a protected file, so the owner's decision). | T-01 | TC-GTB-043 with defects (d), (e); settled 2026-11-22 by delegation (D-423): `plan.md` T-01 names (d) and (e) for TC-GTB-043; TR-RULES-008's text (protected) needs no change, it lists the defects without mapping them to checks |
| `run_check` raised `TypeError` on a `given` that is not a list of IDs, against IF-301 v4 "never raises". Settled 2026-11-22 by delegation (D-423): a malformed `given`, or an item that is not text, counts as nothing given (`_given_ids`) | T-01 follow-up | `tests/test_graph_rule_set.py` `test_a_malformed_given_counts_as_no_values_and_never_raises` (red first: TypeError on 5, object(), [["q"]], 2.5; then green) |
| TC-GTB-046 graph `second` expects the run to name only the rule-report parts, but its `d1` is also an unsupplied input, which IF-301 v4 `run_check` lists and REQ-RUN-037 makes the runner name; open, owner's decision (protected test or requirement), before T-04 | T-03 | TC-GTB-046 (red, 5 sub-failures, graph `second`) |

## Plan amendments
None.

## Stop conditions hit
None.

## Unspecified behavior (decisions no requirement covers)
| Decision | Where in code | Proposed requirement or amendment |
|---|---|---|
| Interpretations the protected mock fixes where IF-301 v4 is short are followed: rule 2 asks only existing, first-occurring steps; a non-text connection ID is named by `str()`; rule 7 in three passes; the cycle is the first one a depth-first walk finds in listed order; an explicit `"kind": None` is `unknown_kind` naming `"None"` | `graph_rule_set.py` `_steps`, `_step_kind`, `_stop_limit`, `_find_cycle`, `_graph_kind` | none needed: stated in the mock header, which the contract suite holds to |
| `given` that is not a list of IDs counts as nothing given (was: `TypeError`) | `run_check`, `_given_ids` | settled by delegation (D-423), see Findings |
| A data step read by a Stage with a prepare function counts as given for the whole run, so a plain step reading the same data step is not refused for it (it reads no value) | `graph_run.py` `_given` | follows from REQ-RUN-039 and `given` per data step (IF-301 v4); propose stating it, or narrowing REQ-RUN-039 to that step's inputs, if the owner wants it otherwise |
| `check_graph` asks the rule report of the graph's own kind (no kind means workflow), as the save does; REQ-WFM-164 speaks of a workflow graph, and every caller passes one | `graph_model.py` `check_graph` | none needed unless a caller passes a context graph |

## Open questions for Phase 4
- None open from T-01 (both settled 2026-11-22, see Findings).
- T-03: TC-GTB-046 graph `second` against REQ-RUN-037 / IF-301 v4 `run_check` (see Findings); the owner decides before T-04.

## Plan amendment A-170b (2026-11-22, D-428)
TC-GTB-046, second graph: run with `{"d1": "x"}` (the owner's choice) because `d1` has no value and no writer and the run check rightly reports it as an unsupplied input (REQ-GTB-051, REQ-RUN-037). Staged in `specs/mia/amendments/A-170b/`; on a scratch install `test_rules_measures.py` is OK (TC-GTB-046 both graphs, TC-GTB-047, TC-RUN-040). Installed by the owner with `tools/apply_amendment_a170b.sh --do`.
