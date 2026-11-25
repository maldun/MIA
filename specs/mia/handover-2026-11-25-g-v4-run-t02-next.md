# Handover: G-V4.GRAPHAPI.RUN Implement, T-01 done, T-02 next (2026-11-25)

Replaces `handover-2026-11-25-g-v4-run-gate-waits.md` (kept as history). The state of the other G-V4 goals is in `handover-2026-11-24-g-v4-run-step4-next.md`, section "The rest of G-V4".

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run`, branch `goal/v4.graphapi.run`, clean at `03a79c16` and not yet pushed by the owner after `1855ae2d` (`git push -4 origin goal/v4.graphapi.run`). Read `CLAUDE.md` and this file; load `dev-workflow`, `implement-phase`, `agent-app`, `agent-app-implement`. Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; the owner signs, the agent never sets Approved; only the owner pushes; protected material is changed only through an amendment script the owner runs (the agent writes drafts under `specs/mia/amendments/A-nnn/`, or gives the owner the commands when writing there is refused).

## Done since the gate (2026-11-25)
| Step | Result | Record |
|---|---|---|
| Plan gate | signed by the owner | `3f040f41` |
| A-188 | TC-GTB-050 also checks that of two steps `d1` the first is kept with its data and position 0 (finding F-1) | D-482, `b414cb4e` |
| T-01 | `load` in `graph_rule_set.py` (networkx imported at the top), `networkx==3.7` in `requirements.txt` and in the venv mia312, `tests/test_graph_loader.py` (5 unit tests), `graphRecords` doc in `architecture.sysml` | `2379dc0a` |
| F-2 | `localhost/mia:latest` had no networkx, six image-based tests went red; rebuilt as `9206eeb93719` (also tagged `pip-cache`), all six green | `03a79c16` |

Everything about T-01 (tests reported green, TR-RUN-007 defects and where they were caught, findings, the amendment) is in `specs/mia/goals/G-V4.GRAPHAPI.RUN/implementation-log.md`.

## State of the checks after T-01
- Unit suite (`discover -s tests`, about 10 minutes, 2535 tests): green.
- Acceptance scripts one by one (about 25 minutes for all 71): red only the known `test_decide_guard.py` and `test_judge_calibration.py` (G-V3.REPORT F-3) and the RUN checks of later tasks: TC-GTB-051 in `test_graph_loader.py` (T-02), "the run reads the loaded graph" in `test_run_graph_order.py` and the 15 failures of `test_stored_graph_run.py` (T-03).
- A script that runs all 71 one by one and prints one line each: `/tmp/claude-1000/-home-maldun-prog-Python-MIA/fcfa6e7f-99b4-4528-9e4b-3ef835547f2d/scratchpad/run_acc.sh` (scratchpad, may be gone; it is a loop over `find tests/acceptance -name 'test_*.py'` with the venv python, grepping `^(OK|FAILED)`).
- Never run the unit suite and acceptance scripts at the same time in this worktree (`mia.log`), and do not edit tracked or untracked files in the worktree while the unit suite runs: `test_checkout_untouched.py` reports them.

## Next: T-02, the order and the rule set on the loaded graph
From `plan.md`:
- Implements REQ-GTB-059, REQ-GTB-060, REQ-WFM-166, REQ-WFM-167.
- Turn green: TC-GTB-051 (`tests/acceptance/test_graph_loader.py`, a search: `graph_rule_set.py` must no longer contain `def _find_cycle`, and the rule set has no view of its own; the checklist of TR-RUN-008 is read by a person). Keep green: TC-GTB-052, TC-WFM-185, TC-WFM-186 (`tests/acceptance/test_run_graph_order.py`), the IF-301 v4 suite.
- Touches: `graph_rule_set.py` (adjacency, one writer, session setting and stop limit, cycle and unsupplied inputs read `load`; `_find_cycle` and the adjacency maps go; step identity, kind of step, connection ends and duplicate connections stay on the stored form, REQ-GTB-059); `graph_model.py` (`order_of` and `topological_order` walk the loaded graph first-ready-first; `find_cycle` goes once no production code uses it, checked with a search).
- Must not touch: protected material; `graph_run.py` (T-03); the answers of `rule_report` and `run_check` (the oracle `tests/helpers/run_oracle.json`).
- The walk is a queue over the loaded graph, not networkx `lexicographical_topological_sort` (D-480).
- Done when: the listed tests green with 0 differences against the oracle; the defects "one rule answering from its old view with one changed branch" and "ties by ID instead of first-ready" each make their check fail (plant, run, remove, log as for T-01).
- Demonstrator: the order of `research` from the loaded graph equals the recorded order, step by step.

## Still open
- The risk row of `high-level-spec.md` naming `lexicographical_topological_sort` is outdated (D-480); correct it with the next change of that document.
- `plan.md`, "Open points before the gate", still names SMOKE-RUN-001 as missing; it exists (`a3d1d800`). Strike it with the next change of `plan.md`.
- TR-RUN-006 "a marker per step": the red tests use the scripted model and tools as markers; ask the owner if a per-step marker is wanted.
- `localhost/mia:latest` is now a branch build and `deploy/compose.yaml` defaults to it: the deployed stack starts with `MIA_IMAGE=localhost/mia:v0.2.1` until v0.3 is deployed.
- Network: pip and GitHub time out often. Builds worked with `--network=host --env PIP_DEFAULT_TIMEOUT=120 --env PIP_RETRIES=10`; pushes with `git push -4`.

## Next free numbers
Decisions D-483 (VIEW D-500 and up, BUILDER D-520 to D-539); amendments A-189 (check `specs/mia/amendments/` on every branch first); checks TC-IF-301-39, TC-GTB-053, TC-WFM-188, TC-RUN-048; test requirements TR-RUN-013.

## Start prompt for the new session
> Continue G-V4.GRAPHAPI.RUN with T-02. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run` (branch `goal/v4.graphapi.run`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-25-g-v4-run-t02-next.md`, then implement T-02 of `specs/mia/goals/G-V4.GRAPHAPI.RUN/plan.md` test-first.
