# Handover: G-V4.GRAPHAPI.RUN Plan, step 3 reviewed, step 4 next (2026-11-24)

Replaces `handover-2026-11-24-g-v4-run-requirements-drafted.md`, which is kept as history (its section "The rest of G-V4" is still the state of the other goals).

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run`, branch `goal/v4.graphapi.run`, last commit `edba0449`. **Not pushed yet:** the owner runs `git push -4` there. Read `CLAUDE.md` and this file; load `dev-workflow`, `plan-phase`, `agent-app`, `agent-app-plan`, `local-coder` (test files are delegated by plan-phase step 4). Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; review by group (accept / waiver / discuss).

## Done in this session (2026-11-24)
| Step | Result | Record |
|---|---|---|
| 1b requirements | the four points decided: HR-007 corrected (extract_claims_rules needs no baseline file), graph ID `<pipeline name>@<pipeline version>`, rule split stored form / loaded graph, N-2.4.3 run log in Parts | D-477 |
| 1b requirements | all six groups reviewed; REQ-WFM-167 rewritten ("when several steps are ready, the lowest position first"; the pairwise rule could not be met by `lexicographical_topological_sort`), term *ready* added | D-478 |
| 3 test spec | `goals/G-V4.GRAPHAPI.RUN/test-spec.md` (23 checks with scenarios, edge inputs, five statistical rows, SMOKE-RUN-001) and `test-requirements.md` (TR-RUN-001 to 012) reviewed by group | D-479 |

## Waiting for the owner (state at the end of the session, 2026-11-24)
| Item | State | How the owner signs |
|---|---|---|
| `goal.md` Agreement "update of 2026-11-23" | box ticked in the working tree, **date empty, not committed** (the owner's edit) | `C-c r S`; then commit it with the owner's OK |
| `high-level-spec.md` approval line | `[ ]` open (HR-007 changed, D-477) | `C-c r S` |
| `requirements.md` | 0 Approved, 24 Draft | `C-c r s` per item, pick Approved (`C-c r S` signs only the document status line, boxes and labels, not the item Status lines) |
| `test-requirements.md` | 0 Approved, 12 Draft | `C-c r s` per item |
| `test-spec.md` | document status Draft | `C-c r S` |

All five are in the Emacs review queue. A batch command "approve all Draft items of this file with one confirmation" is planned for requirement-mode: handover `/home/maldun/prog/Lisp/requirement-mode/handover-2026-11-24-approve-drafts.md` (not committed there). Never set Approved yourself; check with `grep -c 'Status: Approved' specs/mia/goals/G-V4.GRAPHAPI.RUN/requirements.md` before step 4 depends on it.

After the signatures: `python tools/gen_node_requirements_model.py` (approved goal requirements enter the generated block), `python3 -I tools/check_sysml_model.py .`, `bash tools/check_sysml.sh`, `trace_check.py` (549 old ERROR lines are the baseline of `goal/v4`, none of them RUN's). Also open: the G-V4.GRAPHAPI.SWITCH agreement box (`G-V4.GRAPHAPI.SWITCH/goal.md`).

## Other open threads of this session
- **G-V4.BUILDER** waits (D-521 (1)): its Plan resumes only when the plans of RUN and CONTEXT are approved; CONTEXT's Plan has not started (it follows EDIT, which waits for VIEW's merge). Handover on `explore/builder-workflow`: `specs/mia/handover-2026-11-24-g-v4-builder-plan-waits.md`; that branch is not pushed either. The owner may mark samples A and B now (branch `spike/builder-samples`).

## Step 4: red tests (next)
In this order; each test file in the readable shape of the conventions (ID-first docstring with `Example:`, `# Given / # When / # Then`), `test_doc_check.py` green before the red commit.
1. **The oracle first (TR-RUN-002), before any code change.** One script (e.g. `tools/record_run_oracle.py`) run at a named commit of `goal/v4` records into a file under `tests/helpers/` (protected): the `rule_report` and `run_check` answers of IF-301 v4 on the 15 converted skill graphs, the 500 random graphs and golden 24 to 31; the orders of today's `order_of` for the converted and the acyclic random graphs; the model calls and answers of the six skills on the scripted replies of REQ-WFM-058 with an empty store. The header names the commit; the checks fail if it is not an ancestor or the file changed.
2. **The random graph generator (TR-RUN-003)** in `tests/helpers/`: `random.Random(7)`, 500 workflow graphs, 2 to 8 steps of the types data, transform, master, connections between any two steps incl. self loops and parallel ones; its acyclic count is stored with the oracle. The spike's generator was scratch code and is not in the repository.
3. **A-187's contract suite and mock:** `tests/acceptance/contract/test_if_301_v5_load.py` with TC-IF-301-35 to 38 (golden 32 to 35, real side and mock side), the IF-301 v5 mock in `tests/helpers/`, staged under `specs/mia/amendments/A-187/tests/` and copied by the owner's script `tools/apply_amendment_a187.sh` (pattern `tools/apply_amendment_a170.sh`). The agent cannot write protected paths directly.
4. **The red tests** of TC-GTB-048 to 052, TC-WFM-185 to 187, TC-RUN-041 to 047, TC-WFM-115 (stored path) as in `test-spec.md`; minimal stubs (`load` raising `NotImplementedError`) so they import and fail on an assertion. TC-WFM-110 to 114 are eval runs (stage 4), no test file; the run on the stored path needs a store option of `tools/eval.py`, planned as a task, not built in step 4.
5. Show TR-RUN-007's defects as a list in the red commit's message; recompute one expected value by hand (e.g. TC-WFM-186: `x`, `y`, `z` with `x` reading `z` gives `y`, `z`, `x`) and show it to the owner.
6. Commit `test: acceptance tests for G-V4.GRAPHAPI.RUN (red)`, tag `plan-baseline-run` after the owner's OK.

`networkx` is **not** installed yet: the red tests must not import it at module level (they fail on `NotImplementedError`, not `ImportError`). `networkx==3.7` goes into `requirements.txt` in the loader task (approved, D-473 (2)), then `/home/maldun/prog/Python/venvs/mia312/bin/pip install -r requirements.txt -r requirements-db.txt`.

## Then step 5: `plan.md`
Five tasks as proposed: (1) oracle and generator (already done in step 4, so the first task is the loader); loader and IF-301 v5 with `networkx`; order and rule set on the loaded graph; runner and the stored-graph path with the run record; equivalence runs on the stored path (store option of `tools/eval.py`, the six skills saved into a throw-away store, `eval_decide.py`; tell running sessions before the real runs, `ListAgents`). Each task names its tests, files, and for the eval task the budget (5 suites × cases × 3 repeats, one re-run at most).

## Joint amendment A-187
IF-301 v5 is frozen at G-V4: VIEW (session in Implement), EDIT and CONTEXT (not started) agree in `specs/mia/goals/G-V4/goal.md` Joint amendments; v5 only adds `load`.

## Next free numbers
- Decisions: D-480 (VIEW uses D-500 and up, BUILDER D-520 to D-539).
- Amendments: A-188 (check `specs/mia/amendments/` on every branch first).
- Checks: TC-IF-301-39, TC-GTB-053, TC-WFM-188, TC-RUN-048; test requirements TR-RUN-013.

## Start prompt for the new session
> Continue Plan of G-V4.GRAPHAPI.RUN with step 4. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run` (branch `goal/v4.graphapi.run`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-24-g-v4-run-step4-next.md`, load `dev-workflow`, `plan-phase`, `agent-app`, `agent-app-plan` and `local-coder`. First check the owner's signatures, then record the oracle at `goal/v4` before anything else.
