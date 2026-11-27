# Handover: G-V4.GRAPHAPI.RUN Implement, T-04 done, T-05 next (2026-11-28)

Replaces `handover-2026-11-27-g-v4-run-t04-next.md` (kept as history).

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run`, branch `goal/v4.graphapi.run`, not pushed since `39dd1e1f` (the owner pushes: `git push -4`). Read `CLAUDE.md` and this file; load `dev-workflow`, `implement-phase`, `agent-app`, `agent-app-implement`. Ways of working as before: decisions as a questionnaire, full absolute paths, the owner signs and pushes.

## Done since the last handover
| Step | Result | Record |
|---|---|---|
| Merge of `goal/v4` (TRANSFER, `f6ccde75`) | no conflict; unit suite 2662 OK; acceptance scripts all OK except the known two (decide_guard, judge_calibration); the five TRANSFER scripts OK | `56c4894f` |
| T-04 store option | `tools/eval.py run ... --stored` (graph saved into a throw-away store, run through `Core` with `graph_store=`, header `stored_graph`); `tests/test_eval_cli_stored.py`; `ui/README.md` | `66a49249` |
| T-04 runs | REQ-WFM-110 to 114 PASS on the first run (0.950, 0.639, 0.940, 0.974, 0.667; stability 1.00); 0 of 196 cases differ from the old-runner baselines of `1fb0c35`; research_compound reported; SMOKE-RUN-001 green | `fcf37362`, `eval/runs/*__stored__*.jsonl`, implementation log "Eval runs" |

## Waiting for the owner
- F-8: `tests/test_delivery_on_stack.py` fails while Ollama runs because the pip layer of the merged `requirements.txt` is not in the podman cache; build the image once with network (as in F-2), then run it again.
- The plan's T-04 command names `--select req:<ID>`, which fits no case of these suites; decided by the criterion lines (`select=`). Open question for Verify in the log.
- From before: REQ-GTB-043 (Draft, A-189), the IF-301 consumers' agreement to A-189 (D-483), the three rows of "Unspecified behavior".

## Next: T-05 (F-7, D-486)
See `plan.md` T-05: a failing unit test first (the package `MIA` importable beside the plain modules makes a tool step of a converted run fail with `ToolMissing`), then `toolbox.py`'s thin code takes the same `common_operations` the run registers in; remove the pin in `tests/test_core_stored_graph.py`. No model run. After T-05: the regression set, the T-04 row's "(this commit)" set to `fcf37362`, Implement done in `goal.md`'s Phases, then Verify in a fresh session.

## State of the host
Ollama started for T-04 on the owner's word and stopped again afterwards; the sessions EDIT, CONTEXT and the G-V4 line session were told before and after.

## Next free numbers (RUN)
Decisions D-487; amendments A-191; checks TC-IF-301-40, TC-GTB-054, TC-WFM-188, TC-RUN-050; test requirements TR-RUN-013; findings F-9.

## Start prompt for the new session
> Continue G-V4.GRAPHAPI.RUN with T-05. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run` (branch `goal/v4.graphapi.run`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-28-g-v4-run-t05-next.md`, load `dev-workflow`, `implement-phase`, `agent-app`, `agent-app-implement`, then implement T-05 of `specs/mia/goals/G-V4.GRAPHAPI.RUN/plan.md`. Do not push; hand the owner `git push -4`.
