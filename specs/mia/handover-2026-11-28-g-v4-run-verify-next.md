# Handover: G-V4.GRAPHAPI.RUN Implement done, Verify next (2026-11-28)

Replaces `handover-2026-11-28-g-v4-run-t05-next.md` (kept as history).

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run`, branch `goal/v4.graphapi.run`, pushed by the owner up to `0d913533`; `259a64b8` and the log commit after it are not pushed (`git push -4`). Ways of working as before: decisions as a questionnaire, full absolute paths, the owner signs and pushes.

## Done since the last handover
| Step | Result | Record |
|---|---|---|
| T-05 (F-7, D-486) | `Toolbox._code_namespace` hands its own `common_operations` to the thin code, which is `ops = common_operations` (no import); the pin in `tests/test_core_stored_graph.py` gone; new `tests/test_toolbox_one_module.py` (red before the fix) | `259a64b8` |
| Regression set after T-05 | unit suite 2669 tests OK (skipped 5, expected failures 2); acceptance scripts all OK except the known two (decide_guard, judge_calibration) | implementation log, T-05 row |
| Implement | all five tasks done; Phases table of `goal.md` updated (Plan done by the plan gate of 2026-11-25, Implement done) | `goal.md` |

A first T-05 version kept the import as a fallback; TC-WFM-118 (thin entries at most 12 lines) went red in the regression set, so the fallback went. Logged in the T-05 row.

## Waiting for the owner
- F-8: build the image once with network (the pip layer of the merged `requirements.txt` is not cached), then `tests/test_delivery_on_stack.py` while Ollama runs.
- REQ-GTB-043 (Draft, A-189) and the IF-301 consumers' agreement to A-189 (D-483).
- The open questions of the log (the plan's `--select req:<ID>`, the old baselines without `split:dev` tags, the three rows of "Unspecified behavior", `tests/plain_modules.py` after F-7).

## Next: Verify (fresh, independent session)
Load `dev-workflow`, `verify-phase`, `agent-app`, `agent-app-verify`. Inputs: `specs/mia/goals/G-V4.GRAPHAPI.RUN/` (goal, plan, requirements, test spec, test requirements, implementation log), the commits `2379dc0a` to `259a64b8`, the dev runs `eval/runs/*__stored__*.jsonl`. The eval criteria REQ-WFM-110 to 114 are decided in Verify on the pinned model (the holdout stays relaxed by TD-88); before any model run `ListAgents` and a message to every session; Ollama is stopped and is started only on the owner's word. Verify must not reuse this session's context.

## Next free numbers (RUN)
Decisions D-487; amendments A-191; checks TC-IF-301-40, TC-GTB-054, TC-WFM-188, TC-RUN-050; test requirements TR-RUN-013; findings F-9.

## Start prompt for the new session
> Verify G-V4.GRAPHAPI.RUN. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run` (branch `goal/v4.graphapi.run`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-28-g-v4-run-verify-next.md`; load `dev-workflow`, `verify-phase`, `agent-app`, `agent-app-verify`. You are an independent reviewer: start from the plan package and the branch, not from the implementation chat. Ask the owner before starting Ollama; message every running session before a model run. Do not push; hand the owner `git push -4`.
