# Hand-over for the Step 4 session of G-V2.MODEL (written 2026-11-07): write the red tests

Read `CLAUDE.md` first. Skills: `dev-workflow`, `plan-phase` (Step 4), `agent-app` (only to know it does not apply: no model step), `decomposition`; `local-coder` for typing the test files. Phase: Plan, Step 4 of subgoal **G-V2.MODEL**, line of work `goal/v2.model`, worktree `.claude/worktrees/goal-v2-model`. Work in that worktree, commit there, never `git add -A`, name the paths. The owner merges.

## What is done (all on `goal/v2.model`, last commit `436afef`)
- Requirements REQ-WFM-040..049 and REQ-RUN-016..019 (14) reviewed and approved in `review-log.md`. Plausibility records rated by the owner (14). Scenarios of TC-WFM-040..049 and TC-RUN-016..019 approved (at the end of the `test-spec.md` of N-2.3 and of N-2.4.1), test requirements `TR-MODEL-001..005` approved (`specs/mia/test-requirements.md`). VAL-009 written. `plan.md` (five tasks) is in this folder, Draft, not yet reviewed.
- Checks `goal_check`, `req_graph`, `req_lint`, `req_plausibility`, `quality_check` have no finding for these IDs; `trace_check` only warns "no `mark.req` marker" for them, which this step clears.

## Your job
1. Write the acceptance tests for the 14 checks, each mirroring its scenario step by step (`# Given / # When / # Then / # And`), with `ID-first docstring` and an `Example:` line (conventions §5 "Readable tests"); `test_doc_check.py` must pass.
2. Tests go in `tests/acceptance/` (one file for the graph rules and record, one for the runner, e.g. `test_graph_model.py`, `test_graph_run.py`; names are yours). Run as scripts like the existing ones (`python tests/acceptance/test_<name>.py`), markers from `tests/helpers/markers.py` (`mark.req("REQ-WFM-043")`, the `markers` import as in `tests/acceptance/test_workflow_library.py`). Stage 2 (step `acceptance` of the root `stages.yaml`, one process per file).
3. Helpers (fakes) go in `tests/helpers/`: the **minimal fake of the graph tables** (versions and fields, TR-MODEL-001: no wait for the STORE mock; it is run against the IF-301 v2 contract suite later, plan T-05), scripted transforms and a scripted master node with an ordered list of node IDs and a marker file in a fresh temporary folder (TR-MODEL-004). No model server.
4. Minimal stubs so the tests import (new modules proposed in `plan.md`: `graph_model.py`, `skill_record.py`, `graph_run.py`); the tests must fail for the right reason (an assertion, not an `ImportError`). Show the owner one hand-calculated expected value (suggestion: the cycle of TC-WFM-047, e.g. edges a->b, b->c, c->a gives `["a","b","c","a"]`).
5. Commit separately: `test: acceptance tests for G-V2.MODEL (red)`; the owner tags `plan-baseline-it2` (after the other subgoals, one tag for G-V2; ask).

## Rules that bite here
- **Test requirements first** (`test-requirements.md`): TR-MODEL-002 every refusal check has an accepted twin; TR-MODEL-003 TC-WFM-047 uses seeds 1 to 200, at least 60 graphs with and 60 without a cycle (cycles of 2 to 5 nodes), and the topological order is checked by "every edge points forward", not by calling the function under test; TR-MODEL-005 compare IDs and version numbers exactly, never the message wording.
- **A test that does not match its scenario is a finding**, not a thing to adapt. The scenarios are the approved text; do not change them. If a scenario looks wrong, stop and report.
- **Protected** (do not touch): `contracts/`, `tests/smoke/`, `benchmarks/`, existing tests in `tests/acceptance/` and `tests/helpers/` (add new files only), `eval/`. IF-301 and IF-203 are Frozen at G-V2 (A-90); use them through your own fake until STORE is merged.
- **Parallel work** (`goals/G-V2/parallel-work.md`): reserved IDs for MODEL: D-200..219, A-100..109, TD-30..39, SC-20..29, REQ-WFM-071..089, REQ-RUN-020..029 (019 taken), VAL-009. Shared files only as the rules say; `git merge master` first, and on a conflict in `architecture.sysml` take master's and regenerate (`python3 -I tools/gen_node_requirements_model.py .`, `bash tools/check_sysml.sh specs/mia/architecture.sysml`). `review-log.md` and `test-requirements.md` merge as union.
- **Stop and report** when: a protected test seems wrong, a new part, interface or dependency is needed, a file outside the task changes, the same test still fails after 3 serious attempts.

## Open points the owner has not answered (do not guess; write the tests so they do not depend on them)
1. The answer to the STORE session (`goal.md`, last section): field names of the node types (`data`: `value`, `parameters`; `transform`: `toolbox_id`; `master`: `stop`, `task`, maybe `toolbox_id`) are a proposal. In the tests build nodes through one small helper in `tests/helpers/`, so a change of a name is a change in one place.
2. Where the graph header, the membership of nodes in a graph version and the skill record are stored in the record form (five points, same section). The minimal fake takes the simplest shape (a dict per table keyed by ID, versions 1..n); tell the owner which shape you chose.
3. `plan.md` module names and whether STORE's write validation shares the rules of T-01.
4. `Quality:` lines for REQ-WFM-040 and REQ-RUN-017 (Q-5): not added; they would bring the approved requirements back into review.

## Commands
- A test file: `python tests/acceptance/test_<name>.py`; all acceptance files as stage 2 does: `rc=0; for f in tests/acceptance/test_*.py; do python "$f" || rc=1; done; exit $rc`.
- Checks: `python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests` (the 14 should lose their marker warning; the 517 errors are old and not yours), `goal_check.py`, `req_graph.py`, `python3 -I tools/check_sysml_model.py .`.
- Baseline of the old tests before you start: run `python -m unittest discover -s tests -q` once, note the result, so a red you did not cause is recognisable.
