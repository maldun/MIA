# G-V2: rules for parallel sessions (written 2026-11-07)

Four subgoal sessions plan in parallel, each in its own git worktree and branch (`goal/v2.store` work is on master; `goal/v2.model`, `goal/v2.toolbox`, `goal/v2.convert`). They share a few files; these rules keep their changes from colliding. The parent goal and master are written by one session only (the "parent session").

## Merge order and routine
1. STORE (already on master). 2. MODEL. 3. TOOLBOX. 4. CONVERT (its Implement waits for 1 to 3).
Tags: the single tag `plan-baseline-it2` is set by the owner on master after every subgoal has its red tests installed. Until then each subgoal tags its own commit `plan-baseline-it2-<name>` (`-store`, `-model`, `-toolbox`, `-convert`), local, never pushed by an agent. The tag marks the state at that commit: red tests that are only staged (not yet installed under `tests/`) are not protected by it.
Before a merge, in the subgoal's worktree: `git rebase master` (or `git merge master`), fix conflicts as below, then run `goal_check.py`, `trace_check.py`, `req_graph.py`, `req_lint.py` and `bash tools/check_sysml.sh`. The owner merges. After each merge the next session rebases again.

## Reserved IDs (do not take numbers outside your range; if you already did, renumber in your branch before the merge)
| Kind | STORE | MODEL | TOOLBOX | CONVERT | Parent / master |
|---|---|---|---|---|---|
| D- (review-log) | D-189 to D-199 | D-200 to D-219 | D-220 to D-239 | D-240 to D-259 | D-260 and up |
| A- (amendments) | A-91 to A-99 | A-100 to A-109 | A-110 to A-119 | A-120 to A-129 | A-130 and up |
| TD- | TD-27 to TD-29 | TD-30 to TD-39 | TD-40 to TD-49 | TD-50 to TD-59 | TD-60 and up |
| SC- | SC-10 to SC-19 | SC-20 to SC-29 | SC-30 to SC-39 | SC-40 to SC-49 | SC-50 and up |
| REQ-WFM- (new) | – | 071 to 089 | 090 to 109 | 110 to 129 | – |
| REQ-RUN- (new) | – | 019 (taken) to 029 | – | 030 to 039 | – |
| REQ-GTB- (new) | 016 to 029 | – | – | – | – |
| TR- prefix | TR-GTB- | TR-MODEL- | TR-TOOLBOX- | TR-CONVERT- | – |
| VAL- | VAL-008 | VAL-009 | VAL-010 | VAL-007 and VAL-011 | VAL-012 and up |
| FB- | – | – | – | – | FB-07 and up |
Test check IDs follow their requirement (TC-WFM-nnn for REQ-WFM-nnn); a check with no requirement of its own takes the next free number of the requirement range of its subgoal.

## Shared files and how each is handled
| File | Rule |
|---|---|
| `review-log.md` | append-only; `.gitattributes` merges it with `merge=union` (both sides' rows are kept). Never edit an existing row. |
| `test-requirements.md` (root, one file; STORE keeps its own in the N-3.2 node folder) | blocks only appended, under the subgoal's own heading and prefix; `merge=union`. |
| `plausibility.yaml` | insert the entries of a requirement right after the entry of its neighbour of the same area (GTB after REQ-GTB-004, WFM after the last WFM entry, RUN after the last RUN entry), so different sessions touch different places. Resolve any conflict by keeping both sides' entries; run `req_plausibility.py`. |
| `test-spec.md` of a node | rows and scenarios of own check IDs only; where MODEL, TOOLBOX and CONVERT share N-2.3, add rows after the last row of your own ID range. |
| `architecture.sysml` | the requirement block is generated: on a conflict take master's version and run `python3 -I tools/gen_node_requirements_model.py .`, then `bash tools/check_sysml.sh`. Hand-written parts are changed by the parent session only. |
| `requirements.md` (root), `goals/G-V2/goal.md`, `high-level-spec.md`, `contracts/`, `tests/acceptance/` | parent session only. A subgoal reports what it needs changed to the owner. |
| the subgoal's own `goals/G-V2.<NAME>/goal.md` and its requirements | its own session only. |

Requirement text of a requirement that is already approved never merges with `union`; a conflict there is settled by the owner.
