# Handover: G-V4.GRAPHAPI.RUN Implement, T-02 done, T-03 next (2026-11-25)

Replaces `handover-2026-11-25-g-v4-run-t02-next.md` (kept as history). The state of the other G-V4 goals is in `handover-2026-11-24-g-v4-run-step4-next.md`, section "The rest of G-V4".

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run`, branch `goal/v4.graphapi.run`, pushed by the owner at `4f8a9c56` (this handover's commit comes on top). Read `CLAUDE.md` and this file; load `dev-workflow`, `implement-phase`, `agent-app`, `agent-app-implement`. Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; the owner signs, the agent never sets Approved; only the owner pushes (`git push -4`).

**Protected material and amendments:** the auto-mode permission check refuses the agent's own writes under `specs/mia/amendments/` with Bash and refuses running a staging script; editing an existing draft there with the Edit tool worked. What works: the agent writes a staging script (drafts, note, `tools/apply_amendment_aNNN.sh`) outside the repo and gives the owner a short one-line command (long paths break when copied: use a glob such as `/tmp/claude-1000/*/*/scratchpad/stage_aNNN.sh`); the owner stages, then installs with `cd /home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run && bash tools/apply_amendment_aNNN.sh --do`; the agent checks with the script's look-only mode that every file is `unchanged`, then commits "plan: A-NNN installed".

## Done since the last handover (2026-11-25)
| Step | Result | Record |
|---|---|---|
| A-189 | rule 3 also names a connection without a non-empty text ID (`load` leaves it out; the save raised `KeyError` once the rules read the loaded graph); REQ-GTB-043 changed, REQ-GTB-060 narrowed; TC-GTB-053, TC-IF-301-39 (golden 36); joint amendment of IF-301 | D-483, `adfae0f3` |
| A-189 corrected | REQ-GTB-060 narrowed again to connections with existing ends: `stop_limit` on the loaded graph no longer counts settings connections into missing steps (shown to the owner in the G-V4.VIEW viewer) | D-484, `362180c7` |
| T-02 | rules 1 to 4 on the stored form; adjacency, one writer, `stop_limit`, cycle (`networkx.find_cycle`) and unsupplied inputs on `load(graph)`, connections sorted by `position`; `order_of` a queue over the loaded graph; `graph_model.find_cycle` and the copied cycle finder gone (their unit tests ask the cycle rule) | `4f8a9c56` |

Details (tests reported green, TR-RUN-007 defects, findings F-3 to F-5, stop conditions) in `specs/mia/goals/G-V4.GRAPHAPI.RUN/implementation-log.md`.

## Waiting for the owner (not blocking T-03)
- REQ-GTB-060: text changed twice after approval (A-189, D-483, D-484), Status line still Approved: set to Draft in Emacs, review, approve again.
- REQ-GTB-043 (changed), new block in the goal's `requirements.md`: Draft, to approve.
- A-189 is a joint amendment of IF-301 (frozen at G-V4): the consumers VIEW, EDIT, CONTEXT agree (their sessions or the owner for them).

## State of the checks after T-02
- Unit suite (`discover -s tests`, about 8 minutes, 2563 tests): OK.
- Acceptance scripts one by one (about 25 minutes, 71): red only `test_decide_guard.py`, `test_judge_calibration.py` (known, G-V3.REPORT F-3) and T-03's: "the run reads the loaded graph" (TC-RUN-043) in `test_run_graph_order.py`, 15 failures in `test_stored_graph_run.py`.
- One background command for both: `L=$(mktemp -d /tmp/claude-1000/regression-XXXX)`, the unit suite into `$L/unit.log`, then `for f in $(find tests/acceptance -name 'test_*.py' | sort); do ... done > $L/acceptance.log`, printing the non-OK lines.
- Never run the two at the same time in this worktree (`mia.log`), and do not edit files in the worktree while the unit suite runs (`test_checkout_untouched.py`).
- `localhost/mia:latest` is a branch build with networkx (`9206eeb93719`); six image-based tests need it.

## Next: T-03, the runner and the stored-graph path
From `plan.md`:
- Implements REQ-RUN-016 (changed), REQ-RUN-040 to 045, REQ-WFM-168, and the check of REQ-WFM-115.
- Turn green: TC-RUN-043 (`tests/acceptance/test_run_graph_order.py`), TC-RUN-044, 046, 047, TC-WFM-187, TC-WFM-115 (`tests/acceptance/test_stored_graph_run.py`). Keep green: TC-RUN-041, 042, 045, TC-RUN-016 to 019 and 030 to 039.
- Touches: `graph_run.py` (types, roles and names from the loaded graph; `_kinds`, the `reads` map and `_given` go; no list `graph["nodes"]` or `graph["edges"]` is scanned); `core.py` (`graph_store=`: look up `<pipeline>@<version>`, read it once with `read_graph(graph_id)` and its version from `graph_versions(graph_id)`, run it, write `graph` and `graph_version` into the run record, refuse a stored graph the run check refuses with `error` naming the rule, the graph ID and `version <n>`, before any model or tool call); `skill_converter.py` (`run_converted` takes the loaded graph instead of converting in memory when one is given); `run_log.py` only if the record needs the two fields in its shape; unit tests.
- Must not touch: protected material; the old runner `pipeline.py` and the skills, pipelines and library nodes (a skill without a stored graph runs as before, REQ-RUN-043).
- Helpers of the red tests: `tests/helpers/run_store.py` (`ThrowAwayStore` with counted reads and `plant()`, `stored_run`, `old_run`, `run_record`), the oracle `tests/helpers/run_oracle.json`.
- Done when: the listed tests green, the regression set holds; each defect makes its check fail (plant, run, remove, log as in T-01 and T-02): "two steps run in a thread pool", "the stored graph ignored (the in-memory converted graph runs)", "version 1 run instead of the newest", "the run record without `graph_version`", "one prompt changed in the stored graph".
- Demonstrator: `Core(..., graph_store=store).run("verify_claim", ...)` on scripted replies, then `python tools/run_explain.py show <run>` names `verify.single@1` and its version.
- `graph_order.py` (G-V2) says the runner uses an order-only edge for the order only (REQ-RUN-035); keep that when `graph_run.py` reads roles from the loaded graph.

## Then T-04 (model runs)
The five dev suites with 3 repeats on MP-light through the stored-graph path, plus `python tests/smoke/smoke_run.py`. Before: `ListAgents` and a message to running sessions ("real run for about N hours, please hold model tests"); the Ollama server has no queue.

## Still open
- The risk row of `high-level-spec.md` naming `lexicographical_topological_sort` is outdated (D-480).
- TR-RUN-006 "a marker per step": the red tests use the scripted model and tools as markers; ask the owner if a per-step marker is wanted.
- The sentence of rule 3 ("a connection leads to or from a step that does not exist") now also covers a connection without an ID; a better sentence would change the oracle for golden 27 and 31.
- `deploy/compose.yaml` defaults to `localhost/mia:latest`, now a branch build: the deployed stack starts with `MIA_IMAGE=localhost/mia:v0.2.1` until v0.3 is deployed.
- Network: pip and GitHub often time out; builds worked with `--network=host --env PIP_DEFAULT_TIMEOUT=120 --env PIP_RETRIES=10`, pushes with `-4`.

## Next free numbers
Decisions D-485 (VIEW D-500 and up, BUILDER D-520 to D-539); amendments A-190 (check `specs/mia/amendments/` on every branch first); checks TC-IF-301-40, TC-GTB-054, TC-WFM-188, TC-RUN-048; test requirements TR-RUN-013; findings F-6.

## Start prompt for the new session
> Continue G-V4.GRAPHAPI.RUN with T-03. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run` (branch `goal/v4.graphapi.run`). Read `CLAUDE.md` and `specs/mia/handover-2026-11-25-g-v4-run-t03-next.md`, then implement T-03 of `specs/mia/goals/G-V4.GRAPHAPI.RUN/plan.md` test-first.
