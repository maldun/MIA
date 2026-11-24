# Handover: G-V4.GRAPHAPI.RUN Plan, step 5 written, the gate is the owner's (2026-11-25)

Replaces `handover-2026-11-24-g-v4-run-step4-next.md` (kept as history; its section "The rest of G-V4" is still the state of the other goals).

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run`, branch `goal/v4.graphapi.run`. Read `CLAUDE.md` and this file; load `dev-workflow`, `plan-phase` (to finish the gate) or `implement-phase`, `agent-app`, `agent-app-plan` / `agent-app-implement` (T-04). Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; review by group (accept / waiver / discuss); the owner signs, the agent never sets Approved.

## Done in this session (2026-11-24 and 2026-11-25)
| Step | Result | Record |
|---|---|---|
| 4.1, 4.2 oracle and generator | oracle recorded at `goal/v4` `f3e6243c` by `tools/record_run_oracle.py`: 15 converted skills, 500 random graphs (159 acyclic), 16 golden cases, the six skills on scripted replies; deterministic (two runs byte-equal) | `64ecbcab` |
| 4.3 A-187 contract suite | `test_if_301_v5_load.py` (TC-IF-301-35 to 38), mock `if_301_graph_tables_v5.py`, stub `load` in `graph_rule_set.py`, `tools/apply_amendment_a187.sh` | `59cb7a61`, `b7807d08` |
| REQ-WFM-167 | **contradicted itself**: "lowest position among the ready" differs from today's order for 62 of 159 random graphs and for research and verify_computable. Decided: keep today's order, tie rule first-ready-first (a queue); entry of the stored path = `Core(graph_store=)` | D-480, `473b9888` |
| 4.4 red tests | three acceptance files and the helper `run_store.py`; `Core` takes `graph_store=` and ignores it | `0f15df9f`, `9bf55ea5` |
| REQ-GTB-057 | a connection with `data` `[]` is well-formed and kept, with empty `data` (requirement, A-187 text and tests corrected) | D-481, `e74567aa` |
| 5 plan.md | four tasks T-01 to T-04, interface fixed by the red tests, budget of the equivalence runs | `d02f56a0` |

Also done outside this repo: `requirement-mode` had no lifecycle for the ID prefix `TR`, so test requirements could not be approved. One line added (uncommitted) in `/home/maldun/prog/Lisp/requirement-mode/requirement-status.el` and in its worktree `.claude/worktrees/approve-drafts/requirement-status.el`; the session `requirement-mode-6f` was told. In Emacs load the **worktree** file (the main one has the older two-argument `requirement-status--put` and breaks the batch approve).

## Waiting for the owner
| Item | State | How |
|---|---|---|
| REQ-WFM-167 and REQ-GTB-057 | text changed after approval (D-480, D-481); the file still says Approved, the status tool failed (`integer-or-marker-p, nil`) | set to Draft by hand in Emacs, review, approve again |
| IF-301 v5 text (`specs/mia/amendments/A-187/IF-301-graph-tables.md`, installed in `contracts/`) | changed by D-481 | approve the text |
| `high-level-spec.md`, `test-spec.md` | document status Draft / approval line open | `C-c r S` |
| `goal.md` Agreement "update of 2026-11-23" | box ticked, date cell empty | fill the date |
| `test-requirements.md` | 12 of 12 Approved in the working tree, **not committed** | commit it (see the commands the agent gave) |
| Plan gate in `plan.md` | open | tick when the above is done |
| Tag `plan-baseline-run` | not set | after the owner's OK |

After the signatures: `python tools/gen_node_requirements_model.py`, `python3 -I tools/check_sysml_model.py .`, `bash tools/check_sysml.sh`, `trace_check.py` (549 old ERROR lines are the baseline of `goal/v4`, none of them RUN's). Also open: the G-V4.GRAPHAPI.SWITCH agreement box (`G-V4.GRAPHAPI.SWITCH/goal.md`).

## Open points of the Plan
- **SMOKE-RUN-001 has no script.** `tests/smoke/smoke_run.py` is protected material: write it, stage it with A-187 (extend `tools/apply_amendment_a187.sh`), and have the owner install it before the gate. Content: verify_claim saved into a throw-away files store, run once on MP-light with one claim of EV-verdicts dev; the run ends `done` and its record names `verify.single@1` and its version.
- The risk row of `high-level-spec.md` that names `lexicographical_topological_sort` is outdated (D-480); correct it with the next change of that document.
- TR-RUN-006 says "a marker per step"; the red tests use the scripted model and tools as the markers (every step of verify_claim with an effect goes through one of them). Tell the owner if a per-step marker is wanted.
- In TC-WFM-115 the planted difference is in the comparison of the outputs, not in a changed stored graph.
- The mock side of the v5 contract suite needs networkx: it errors until T-01 installs it (`networkx==3.7` into `requirements.txt`, then `/home/maldun/prog/Python/venvs/mia312/bin/pip install -r requirements.txt -r requirements-db.txt`).

## State of the checks (scratch install, 2026-11-25)
Red: TC-GTB-048 to 051, TC-IF-301-35 to 38 (real side), TC-RUN-043, 044, 046, 047, TC-WFM-187, TC-WFM-115. Green and to be kept green: TC-GTB-052, TC-WFM-185, 186, TC-RUN-041, 042, 045. The older IF-301 v1, v2, v4 suites are green.

## Next: Implement, after the gate
T-01 loader and IF-301 v5, T-02 order and rule set on the loaded graph, T-03 runner and stored-graph path, T-04 equivalence runs (tell the running sessions first: `ListAgents`, "real run for about N hours, please hold model tests"). Mutations of TR-RUN-007 are listed in the message of commit `0f15df9f` and in the Done-when lines of the tasks. Stop and report on the conditions in `CLAUDE.md` and at the end of T-04 in `plan.md`.

## Next free numbers
- Decisions: D-482 (VIEW uses D-500 and up, BUILDER D-520 to D-539).
- Amendments: A-188 (check `specs/mia/amendments/` on every branch first).
- Checks: TC-IF-301-39, TC-GTB-053, TC-WFM-188, TC-RUN-048; test requirements TR-RUN-013.

## Other open threads
- **G-V4.BUILDER** waits (D-521 (1)) until the plans of RUN and CONTEXT are approved; CONTEXT's Plan has not started (it follows EDIT, which waits for VIEW's merge). Handover on `explore/builder-workflow`: `specs/mia/handover-2026-11-24-g-v4-builder-plan-waits.md`.
- The batch "approve all Draft items" command of requirement-mode lives in the worktree `approve-drafts` (branch `feat/approve-drafts`), not yet merged.

## Start prompt for the new session
> Continue G-V4.GRAPHAPI.RUN. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run` (branch `goal/v4.graphapi.run`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-25-g-v4-run-plan-gate.md`. First check the owner's signatures (`grep -c 'Status: Approved'` of `requirements.md` and `test-requirements.md`, the plan gate in `plan.md`); if the gate is open, write `tests/smoke/smoke_run.py` (staged), otherwise start T-01.
