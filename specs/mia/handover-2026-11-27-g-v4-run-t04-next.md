# Handover: G-V4.GRAPHAPI.RUN Implement, T-03 done, T-04 next (2026-11-27)

Replaces `handover-2026-11-25-g-v4-run-t03-next.md` (kept as history).

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run`, branch `goal/v4.graphapi.run` (pushed by the owner up to `39dd1e1f`; everything below is not pushed yet). Read `CLAUDE.md` and this file; load `dev-workflow`, `implement-phase`, `agent-app`, `agent-app-implement`. Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; the owner signs, the agent never sets Approved; only the owner pushes (`git push -4`). Amendments: drafts staged by a script outside the repo (the agent may run it), installed by the owner with `bash tools/apply_amendment_aNNN.sh --do`.

## Done since the last handover
| Step | Result | Record |
|---|---|---|
| Merge of `goal/v4` | conflict in `architecture.sysml` (graphRecords doc and the requirement blocks of RUN and VIEW): both sides kept; model checks OK | `9983b896` |
| A-190 | REQ-RUN-046 (the answer of a run from the stored graph is the value of the data step the pipeline names as its result) with TC-RUN-048; REQ-RUN-047 (`graph_run.py` and `graph_rule_set.py` import only the standard library, networkx and each other: the owner's "re-use = module boundary only") with TC-RUN-049 | D-485, proposed `93fbdd14`, installed `e12d5d94` |
| T-03 | the run reads the loaded graph; `Core(graph_store=)` runs the newest stored graph, refuses one the run check refuses, writes `graph`/`graph_version`; `run_explain show` names them; F-6 fixed (nested model calls take the stored `descriptor.model`); F-7 logged (test isolation, `toolbox.py` `IMPORT_OPS`) | `551c414b` |

Details (tests, the seven defects of TR-RUN-007, findings, unspecified behaviour, open questions) in `specs/mia/goals/G-V4.GRAPHAPI.RUN/implementation-log.md`.

## Waiting for the owner
- REQ-RUN-046, 047 (A-190): Draft, to approve in Emacs.
- REQ-GTB-060 (text changed twice, still Approved: to Draft and approve again), REQ-GTB-043 (Draft); A-189 as a joint amendment of IF-301 (VIEW, EDIT, CONTEXT agree).
- F-7: a small task to fix `IMPORT_OPS` in `toolbox.py` (outside RUN's Touches): the thin code takes the toolbox's own `common_operations` instead of importing one.
- The three rows of "Unspecified behavior" in the log (variant runs, silent fallback to the old runner, a stored graph without its result step).

## State of the checks after T-03 (feedback, not verification)
- Unit suite 2610 tests OK (skipped 5, expected failures 2), 2026-11-27.
- Acceptance scripts: 73 of 75 OK, red only `test_decide_guard.py`, `test_judge_calibration.py` (known, G-V3.REPORT F-3).
- `bash tools/regress.sh --out <dir> --python /home/maldun/prog/Python/venvs/mia312/bin/python --base <commit>` does both (about 35 minutes); never edit the worktree while it runs.

## Next: T-04, the equivalence runs on the stored-graph path
See `plan.md` T-04: a store option in `tools/eval.py`, the five dev suites (196 cases, 3 repeats on MP-light, 588 case runs), `eval_decide.py` against the baselines of `1fb0c35`, SMOKE-RUN-001. Before any model run: `ListAgents` and a message to every running session ("real run for about N hours, please hold model tests"); the TRANSFER fix session (`goal-v4-7b`, if still running) was told a message comes first. Compare the model digests with `eval-spec.md` (`ollama list`) before the first run; `ollama` was stopped on 2026-11-27.

## Next free numbers (RUN)
Decisions D-486; amendments A-191; checks TC-IF-301-40, TC-GTB-054, TC-WFM-188, TC-RUN-050; test requirements TR-RUN-013; findings F-8.

## Start prompt for the new session
> Continue G-V4.GRAPHAPI.RUN with T-04. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run` (branch `goal/v4.graphapi.run`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-27-g-v4-run-t04-next.md`, then implement T-04 of `specs/mia/goals/G-V4.GRAPHAPI.RUN/plan.md`.
