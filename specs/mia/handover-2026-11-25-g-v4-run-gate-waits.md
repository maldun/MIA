# Handover: G-V4.GRAPHAPI.RUN Plan, all red material installed, the gate waits for the owner (2026-11-25)

Replaces `handover-2026-11-25-g-v4-run-plan-gate.md` (kept as history; its tables "Done", "Open points" and "Next free numbers" are still valid where not changed below, and `handover-2026-11-24-g-v4-run-step4-next.md`, section "The rest of G-V4", is still the state of the other goals).

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run`, branch `goal/v4.graphapi.run`, clean at `a3d1d800`. Read `CLAUDE.md` and this file; load `dev-workflow`, `implement-phase`, `agent-app`, `agent-app-implement`. Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; review by group (accept / waiver / discuss); the owner signs, the agent never sets Approved; only the owner pushes.

## Done in this session (2026-11-25)
| Step | Result | Record |
|---|---|---|
| SMOKE-RUN-001 | `tests/smoke/smoke_run.py`: the converted verify_claim graph saved into a throw-away files store (`run_store.ThrowAwayStore`), Core with `graph_store=` runs `true-pacific` of EV-verdicts dev once on MP-light (pin name, seed, temperature, num_ctx forced on every call; exit 2 when the server lacks the pin's digest). Green when the graph is read once from the store, the run ends `done` and the record names `verify.single@1`, version 1; the answer is printed, not judged. Not run yet (red until T-03) | draft `41120c32` |
| A-187 extended | `tools/apply_amendment_a187.sh` copies the smoke script (it does not run it); installed by the owner with `--do` | `a3d1d800` |
| `test-requirements.md` | was already committed with 12 of 12 Approved (`f2377a9c`); a stale Emacs autosave `#test-requirements.md#` deleted | – |

State of the checks after the install: red as expected: `test_graph_loader.py` (failures 1, errors 42), `test_stored_graph_run.py` (failures 15), `contract/test_if_301_v5_load.py` (errors 24, networkx missing); green: IF-301 v1, v2, v4 suites. `test_run_graph_order.py` printed only its timing line ("order of 174 graphs in 0.118 s"); look at its full output at the start of T-02.

## Waiting for the owner (the gate)
| Item | How |
|---|---|
| REQ-WFM-167 and REQ-GTB-057: text changed after approval (D-480, D-481), the file still says Approved (the status tool failed with `integer-or-marker-p, nil`) | set to Draft by hand in Emacs, review, approve again |
| IF-301 v5 text (`specs/mia/amendments/A-187/IF-301-graph-tables.md`, installed in `contracts/`) | approve the text |
| `high-level-spec.md`, `test-spec.md`: document status Draft | `C-c r S` |
| `goal.md` Agreement "update of 2026-11-23": box ticked, date cell empty | fill the date |
| Plan gate in `plan.md` | tick, with date |
| Tag `plan-baseline-run` | after the gate |

The "Open points before the gate" in `plan.md` still names SMOKE-RUN-001 as missing; that point is done (strike it when `plan.md` changes next). After the signatures: `python tools/gen_node_requirements_model.py`, `python3 -I tools/check_sysml_model.py .`, `bash tools/check_sysml.sh`, `trace_check.py` (549 old ERROR lines are the baseline of `goal/v4`, none of them RUN's). Also open: the G-V4.GRAPHAPI.SWITCH agreement box (`G-V4.GRAPHAPI.SWITCH/goal.md`).

## Next: Implement, after the gate
T-01 loader and IF-301 v5 (first: `networkx==3.7` into `requirements.txt`, then `/home/maldun/prog/Python/venvs/mia312/bin/pip install -r requirements.txt -r requirements-db.txt`), T-02 order and rule set on the loaded graph, T-03 runner and stored-graph path, T-04 equivalence runs plus `python tests/smoke/smoke_run.py` (tell running sessions first: `ListAgents`, "real run for about N hours, please hold model tests"). Mutations of TR-RUN-007 are in the message of `0f15df9f` and the Done-when lines of the tasks.

## Still open from the Plan
- The risk row of `high-level-spec.md` naming `lexicographical_topological_sort` is outdated (D-480); correct it with the next change of that document.
- TR-RUN-006 "a marker per step": the red tests use the scripted model and tools as markers; ask the owner if a per-step marker is wanted.

## Next free numbers
Decisions D-482 (VIEW D-500 and up, BUILDER D-520 to D-539); amendments A-188; checks TC-IF-301-39, TC-GTB-053, TC-WFM-188, TC-RUN-048; test requirements TR-RUN-013.

## Start prompt for the new session
> Continue G-V4.GRAPHAPI.RUN. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run` (branch `goal/v4.graphapi.run`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-25-g-v4-run-gate-waits.md`. Check the plan gate in `plan.md` and the tag `plan-baseline-run`; if the gate is still open, list what the owner has left and stop; otherwise start T-01.
