# Implementation log: G-V4.GRAPHAPI.RULES

Goal: G-V4.GRAPHAPI.RULES   Line of work: goal/v4.graphapi.rules   Supervision: supervised (agent's own recommendations delegated by the owner, D-423)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 The rule set module | done | see `git log` ("feat: T-01 the rule set module") | TC-GTB-037 to 045, TC-GTB-047, TC-RUN-040, TC-IF-301-27 to 34 (mock and real), `tests/test_graph_rule_set.py` (9 unit tests) | TC-GTB-046 stays red until T-04 (needs T-02's `SaveResult.rules`) |
| T-02 The save path on the rule set | done | see `git log` ("feat: T-02 the save path on the rule set") | TC-WFM-179 to 184; TC-WFM-164, 168 and the three `check_graph(...) == []` tests kept; `tests/test_graph_model_rule_set.py` (8 unit tests) | `context_problems` removed (no caller left) |

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

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| TR-RULES-008 lists TC-GTB-043 among the checks to be shown able to fail, but none of its three rule-set defects (swap, first only, cycle with rule 3 broken) makes TC-GTB-043 fail; two run-check defects (inputs before rules, kind not alone) do. Proposal for Verify: name a run-check defect for TC-GTB-043 in TR-RULES-008 (a text change of a protected file, so the owner's decision). | T-01 | TC-GTB-043 with defects (d), (e); settled 2026-11-22 by delegation (D-423): `plan.md` T-01 names (d) and (e) for TC-GTB-043; TR-RULES-008's text (protected) needs no change, it lists the defects without mapping them to checks |
| `run_check` raised `TypeError` on a `given` that is not a list of IDs, against IF-301 v4 "never raises". Settled 2026-11-22 by delegation (D-423): a malformed `given`, or an item that is not text, counts as nothing given (`_given_ids`) | T-01 follow-up | `tests/test_graph_rule_set.py` `test_a_malformed_given_counts_as_no_values_and_never_raises` (red first: TypeError on 5, object(), [["q"]], 2.5; then green) |

## Plan amendments
None.

## Stop conditions hit
None.

## Unspecified behavior (decisions no requirement covers)
| Decision | Where in code | Proposed requirement or amendment |
|---|---|---|
| Interpretations the protected mock fixes where IF-301 v4 is short are followed: rule 2 asks only existing, first-occurring steps; a non-text connection ID is named by `str()`; rule 7 in three passes; the cycle is the first one a depth-first walk finds in listed order; an explicit `"kind": None` is `unknown_kind` naming `"None"` | `graph_rule_set.py` `_steps`, `_step_kind`, `_stop_limit`, `_find_cycle`, `_graph_kind` | none needed: stated in the mock header, which the contract suite holds to |
| `given` that is not a list of IDs counts as nothing given (was: `TypeError`) | `run_check`, `_given_ids` | settled by delegation (D-423), see Findings |

## Open questions for Phase 4
- None open from T-01 (both settled 2026-11-22, see Findings).
