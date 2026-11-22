# Merge request: G-V4.GRAPHAPI.RULES, one rule set for graphs

**Goal:** G-V4.GRAPHAPI.RULES (subgoal of G-V4.GRAPHAPI, supervised; agent decisions by delegation, D-423)   **Branch:** `goal/v4.graphapi.rules` → `goal/v4` (no version, no tag: a subgoal merge)
**Accepted by:** Stefan Reiterer (owner)   **Merged by:** the owner (agents hold no integration rights)
**TLS:** `specs/mia/goals/G-V4.GRAPHAPI/top-level-spec.md` (FR-63, FR-64)   **HLS:** `specs/mia/goals/G-V4.GRAPHAPI.RULES/high-level-spec.md` (HR-001 to HR-006)
**Goal record:** `specs/mia/goals/G-V4.GRAPHAPI.RULES/goal.md`   **Plan:** `specs/mia/goals/G-V4.GRAPHAPI.RULES/plan.md`
**Verification report:** `specs/mia/goals/G-V4.GRAPHAPI.RULES/verification-report.md` (verified with accepted deviations, verdict ticked by the owner `f4cc31ae`)
**Implementation log:** `specs/mia/goals/G-V4.GRAPHAPI.RULES/implementation-log.md`
**Interface:** IF-301 v4 (`contracts/IF-301-graph-tables.md`; A-170, A-185)
**Drafted:** 2026-11-22 by the agent (Commit phase); Merge: [ ] the owner

## What RULES delivers
- **OC-1:** one set of rules per kind of graph (`graph_rule_set.py`, N-3.2): eight rules for a workflow graph and three for a context graph, in one fixed order, in one registry. The rule report, the save, the check route (stand-in) and the run all name the same broken rules in the same order, each with its steps or connections (TC-GTB-046: 2 graphs × 4 entry points × 5 repeats, 0 differences; TC-WFM-180).
- **OC-2:** a run is checked before its first step (`graph_run.py`, N-2.4.1). A cycle, two writers, a missing or duplicate connection, an unsupplied step input, a context graph or an unknown kind is refused, no step runs, and every broken part is named (TC-RUN-036, TC-RUN-037, TC-GTB-044, SMOKE-RULES-001 on the branch). Trust is checked after the run check (TC-RUN-038).
- The save path of the Workflow management (`graph_model.py`, N-2.3) asks the rule report of the graph's kind. A refusal carries the report (`SaveResult.rules`), and `check_graph` remains the flat list. CORE's V-2 (`"kind": null`) and V-3 (`not_found` for a graph that was never stored) are now stated as requirements.
- The document form (IF-301 `validate`) keeps its five rules until MIGRATION (REQ-GTB-052, TC-GTB-045).

## Commits per task
| Task / item | Commit(s) | Requirements |
|---|---|---|
| A-170 (IF-301 v4 contract, suite, mock, helper) | `fdbf2377` | IF-301 v4 |
| Red tests, tag `plan-baseline-g-v4-rules` | `71523f7a` | – |
| T-01 The rule set module | `5722f4d7`, follow-up `ae7eea41` (malformed `given`) | REQ-GTB-033 to 052 |
| T-02 The save path on the rule set | `5a238e9f` | REQ-WFM-162 to 165; REQ-WFM-150, 154, 155 (changed) |
| T-03 The runner asks the run check | `811d7850` | REQ-RUN-036 to 039 |
| A-170b (TC-GTB-046 test data, D-428) | `a1f8c49a` (staged), `d99fc6e9` (installed) | – |
| T-04 Every entry point, and the smoke check | `f6854766` | HR-004, HR-006 |
| V-1 fix (a check never raises on list- or object-valued connection fields) | `f478e040` | REQ-GTB-040 |
| A-185 (IF-301 v4: the save asks the rule report before the record checks; V-2) | staged in `f478e040`, installed `fb3b72eb` | IF-301 v4 |
| Commit phase: generator fix (HR parents of moved requirements, D-420) | `cc3da934` | – |
| Commit phase: requirements and checks moved into the node files | `5cb4c87b` | all 31 |
| Commit phase: test requirements staged, owner script | `5ff3eb22` | TR-RULES-001 to 009 |

Other commits on the branch, not RULES work: VIEW handovers and design decisions (`967fd8c4`, `e93ead7c`, `ca01eed7`, D-425 to D-427) and `d2318ef9` (D-429, D-460). They change only documents, and were made in this worktree by delegation. The history is kept as it is: no squash, no rebase (owner's rule for this merge).

## Requirements implemented
28 new and 3 changed (31 items, Verify V-5). From this merge on, the node files are the source:
- `specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md`: REQ-GTB-033 to 052 (groups RS, RD, RF, DF)
- `specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md`: REQ-WFM-162 to 165 (group SV); REQ-WFM-150, 154, 155 with the approved new texts, in place in CORE's section
- `specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/requirements.md`: REQ-RUN-036 to 039 (group RR)

All are Verified (verdict 2026-11-22). The checks, the contract cases TC-IF-301-27 to 34, SMOKE-RULES-001 and the scenarios are in the node test specs of the same nodes. The witnesses of AC-017 and AC-018 are filled in `specs/mia/goals/G-V4/accepted-cases.md`. VAL-RULES-01 stays in the goal's `test-spec.md`, as VAL-CORE-01 did.

## Plan amendments
A-170 (IF-301 v4), A-170b (TC-GTB-046 test data, D-428), A-185 (V-2: contract sentence corrected, D-461). No frozen requirement was changed by a joint amendment.

## Frozen requirements unchanged
`goal_check.py --spec-dir specs/mia --parent-ref goal/v4`: no frozen requirement changed against `goal/v4`. The RULES entry is GL11 only (size, decided in the split check, D-418 (3)). The GL5 errors on IF-203 and IF-301 (`Frozen: G-V2`) were already there and are not about RULES.

## Verification result and deviations (D-461)
- 31 of 31 requirements and the measures HR-004 to HR-006 have a green check. Each check ran under its test requirements, and each TR-RULES-008 defect was caught.
- V-1 (medium, REQ-GTB-040): fixed, test first (`f478e040`).
- V-2 (low): the contract sentence is corrected by A-185. No code or test change.
- V-4 (low, an input a prepare function may give counts as given for the whole run): accepted as stated (recorded in the History of REQ-RUN-039).
- V-5 (counts): corrected to 28 new and 3 changed.
- V-3, V-6, V-7 (info): noted. V-6: the IF-301 consumer flows are not drawn in the model. V-7: `trace_check.py` reads only the first ID of a `mark.req`, so it warns that 8 RULES requirements have no marker, although they have one.
- The check-route half of TC-GTB-046 is a wiring check until IF-104 v2 is real (TR-RULES-007).

## Checks on the branch after the merge preparation (2026-11-22, venv `mia312`)
| Check | Result |
|---|---|
| Update with the target | `goal/v4` (`e7847ba5`) is the merge base: no commit to bring in, nothing merged |
| RULES acceptance files | `test_rules_rule_set.py` 9 OK, `test_rules_save.py` 6 OK, `test_rules_run.py` 4 OK, `test_rules_measures.py` 3 OK |
| IF-301 v4 suite | `contract/test_if_301_v4_rule_set.py` 16 OK |
| Unit tests | `test_graph_rule_set.py` 11 OK, `test_graph_model_rule_set.py` 9 OK, `test_graph_run_rule_set.py` 5 OK, `test_graph_run_findings.py` 10 OK, `test_gen_node_requirements_model.py` 3 OK (new) |
| Smoke | `tests/smoke/smoke_rules.py`: SMOKE-RULES-001 pass (15 skills ready, `sample.broken` refused naming `e2`, no step run) |
| Full regression | not re-run: nothing was merged in, and the product code is unchanged since the clean regression after the V-1 fix (`762ec356`) |
| Model | `gen_node_requirements_model.py`: 597 node requirements, the same dependency set as before the move; `check_sysml_model.py` OK (40 acceptance criteria); `check_sysml.sh specs/mia/architecture.sysml` 0 errors, 0 warnings |
| Traceability | `specs/mia` now: 580 errors (549 + the 31 RULES checks whose test requirements wait for the owner's script). Scratch copy with the staged `test-requirements.md`: **549**, the same set as before the merge preparation, none about RULES |

## What the owner runs
In this worktree (`/home/maldun/prog/Python/MIA-goal-v4-rules`, branch `goal/v4.graphapi.rules`):
1. `bash tools/apply_merge_g_v4_rules.sh` to look at the diff (add `--report` for the readable form), then `bash tools/apply_merge_g_v4_rules.sh --do`. It prints the number of trace errors about RULES, which should be 0.
2. `git add specs/mia/test-requirements.md && git commit -m "plan: RULES test requirements installed"`
3. `specs/mia/goals/G-V4.GRAPHAPI.RULES/plan.md` (open in your Emacs) has an uncommitted change of yours (one blank line after T-01). The agent did not touch or stage it. Commit or drop it before the merge so that `git status` is clean. Its "At the merge" section still says "27 new requirements"; the correct count is 28 (V-5, D-461).

In the parent's worktree (`/home/maldun/prog/Python/MIA-goal-v4`, branch `goal/v4`):

4. `git status` (clean), then `git merge --no-ff goal/v4.graphapi.rules`
5. Record the merge commit in the RULES `goal.md` Phases row Commit (`done`, merge commit).

## Checks after the merge (on `goal/v4`)
- `python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests`: 549 errors, none about RULES
- `python3 -I tools/check_sysml_model.py .` and `bash tools/check_sysml.sh specs/mia/architecture.sysml`
- the four `tests/acceptance/test_rules_*.py`, `tests/acceptance/contract/test_if_301_v4_rule_set.py`, `tests/smoke/smoke_rules.py`
- if VIEW was merged first: the unit suite (`-m unittest discover -s tests`, about 8 minutes) and every acceptance script one by one (known reds: `test_decide_guard.py`, `test_judge_calibration.py`)

## Notes for other subgoals
From `requirements.md`, section "Notes for other subgoals":
- **EDIT** and the check route (IF-104 v2, G-V4 level): every entry point checks a working copy with the kind stored for the graph (the prototype's page lost it, finding 9). RULES tested the check route only against a mock that returns the rule report (D-416 (2)).
- **CODE:** the known-tool check (Q-2). **TRANSFER or MIGRATION:** the read-only listing of a graph of an unknown kind (Q-7). **MIGRATION:** retires the document form and REQ-GTB-052 with it (Q-6).
- REQ-RUN-016 (order), REQ-RUN-033 and REQ-RUN-034 keep their texts. The run check stands in front of them, and TC-RUN-016, 033 and 034 pass unchanged.
- The model generator now resolves the HR parent of a requirement in a node file through the goal its History names (`cc3da934`). Later goals keep the History form `G-… Plan step …` when they move requirements.

VIEW (`goal/v4.view`) runs in parallel and merges separately. `git merge-tree` of `goal/v4.view` (`54e498c4`) and this branch shows no conflict today. If both add rows at the end of `specs/mia/review-log.md`, the only expected conflict is the row order there: keep both rows, ordered by decision number. TRANSFER (`goal/v4.graphstore.transfer`) also merges after RULES and updates with `goal/v4` first.

## Known issues / accepted deviations
V-3, V-4, V-6, V-7 (above). The smoke test on the owner's host belongs to Deploy, and VAL-RULES-01 belongs to Validate (G-V5, parked, D-386).

## Conflict resolutions
None: nothing was merged into the branch.
