# Handover: G-V4, CORE plan package complete (2026-11-21, evening)

Written for the next session. Read this first, then `CLAUDE.md` of the repository and the skills `dev-workflow`, `plan-phase` (or `implement-phase` for CORE's tasks) and `agent-app`. The owner is Stefan Reiterer (maldun). He decides every gate; never treat an agent report or silence as approval. The previous handover is `handover-2026-11-21-g-v4-plan-core.md`.

## 1. Where we are
Goal **G-V4** (graph rework) is in **Plan**, subgoal by subgoal (D-401): CORE, RULES, TRANSFER, RUN, VIEW, EDIT, REPLAY, CODE, MIGRATION, CONTEXT, BUILDER.

| CORE item | State |
|---|---|
| High-level spec, requirements (22 + 2 assumptions) | approved; REQ-WFM-161 added, REQ-GTB-029 ("non-empty ID") and REQ-WFM-160 (narrowed to graphs with steps) changed with the owner's approval |
| Checks (22) and test requirements (9) | approved; all 55 items reviewed (`req_review.py ... status`: 0 pending) |
| Architecture (Plan step 2) | done: FR-57, FR-60, NFR-16 in the hand-written model, the 22 requirements in the generated block (D-408); `check_sysml.sh` 0 errors, `check_sysml_model.py` OK |
| Amendment A-167 (IF-301 v3, scoped IDs) | **installed** by the owner (be9a0c61) |
| Fixtures (TR-CORE-004) | `tests/fixtures/graphs/` (c783f0a2), made by `tools/make_core_fixtures.py` |
| Red tests (Plan step 4) | **installed** by the owner (3e43ff1c), tag `plan-baseline-g-v4-core` |
| `plan.md` (Plan step 5) | **approved** (7e7d6727): T-01 to T-05 |
| Binding map (iteration 0) | **decided and ticked** (D-411): 19 fixed, 3 open |
| Round 03 sign-off | still open: `Validated by:` in `rounds/03/validation.md`, `Decided by:` in `rounds/03/prototype-report.md` (prototype worktree) |

So the CORE plan gate is complete except the round 03 signatures. **Next: Implement CORE T-01** in a fresh session (`implement-phase`), or **Plan RULES** (the next subgoal), as the owner chooses.

## 2. Where everything is
- Worktree `/home/maldun/prog/Python/MIA-goal-v4`, branch `goal/v4` (not pushed; no upstream). CORE folder: `specs/mia/goals/G-V4.GRAPHSTORE.CORE/` with `goal.md`, `high-level-spec.md`, `requirements.md`, `test-spec.md`, `test-requirements.md`, `plan.md`, `binding-map.md`, `review-log.md`, `red-tests/` (the staged originals of the installed red tests).
- Prototype worktree `/home/maldun/prog/Python/MIA-prototype-g-v4`, branch `prototype/g-v4` (493aff3e): the reference code of reuse map R1 (`graph_tables.py` lines 159 to 224, `graph_model.py` `GraphModel`). Merge `goal/v4` into it before round 04.
- Main checkout `/home/maldun/prog/Python/MIA`: unrelated untracked files; do not touch.
- `specs/mia/amendments/A-167/A-167.diff` is an untracked view file (the A-167 change for Emacs); delete it or leave it, never commit it.

## 3. Decisions of this session (full text in `specs/mia/review-log.md`)
- **D-407** plan reviews by thematic group: per group accept, waiver (approved with a note starting `WAIVER:`) or discuss; close look where users feel it (GUI), backend conventions little.
- **D-408** a goal keeps its new requirements in `goals/<CODE>/requirements.md` until the merge moves them into the node files; `tools/gen_node_requirements_model.py` reads approved goal items too; `tools/check_sysml_model.py` accepts FR/NFR of `goals/*/top-level-spec.md` (Outcome line = acceptance criterion).
- **D-409** CORE checks renumbered (six IDs were taken): TC-GTB-033..036, TC-WFM-162..178; an empty record ID stays `record_identity` (`id`); IF-301 is v3.
- **D-410** a graph ID with a slash is caught only through its steps (REQ-WFM-160 narrowed); five test details written into the scenarios; TC-WFM-164 is green from the start.
- **D-411** binding: 19 fixed, REQ-WFM-155/156/161 open (CONTEXT's rule set); REQ-WFM-145's clause "only pinned versions" open; REQ-GTB-031 and REQ-WFM-160 fixed with TC-GTB-036 as witness.

## 4. For Implement of CORE (T-01 first)
- State at the red commit: every CORE check fails by assertion on `goal/v4`, except TC-WFM-164 (green, must stay green) and two injected `Interrupted` errors in TC-WFM-169 (today's code rewrites every member: the REQ-WFM-148 defect). `GraphModel.graph_versions` and `step_history` are stubs returning `[]` (T-03 replaces them).
- T-01 turns green TC-GTB-033..035 and the real side of TC-IF-301-25/-26 (`graph_tables.py` only). The tests: `tests/acceptance/test_core_scoped_ids.py`, `test_core_save.py`, `test_core_context_and_history.py`, `test_core_both_stores.py`, `tests/smoke/smoke_core_graphs.py`, helper `tests/helpers/core_stores.py` (fresh files store or database per check, `FailingBackend`).
- PostgreSQL halves start their own `postgres:16` container per process (named `mia-core-test-<pid>`, never pulled). **Never** remove other containers: the owner's `mia_*`, `ollama`, `mia-searxng` run on this host.
- Fixed requirements change only by plan amendment (A-nn); open ones freely with a line in the change log.
- At the merge: move the 22 requirements into N-3.2 and N-2.3 (D-408), regenerate the model, fill the Witnesses of AC-001..003.

## 5. Tools and checks used here
- `trace_check.py` and `binding_check.py` do not see a subgoal's parent records: run them on a temporary folder with symlinks (CORE files + `architecture.sysml`, or + `G-V4/prototype`, `accepted-cases.md`, `top-level-spec.md`). On the CORE folder this way: trace 0 errors; binding no errors, BD3 share warning 86 % (accepted).
- Protected files (`tests/acceptance`, `tests/helpers`, `tests/smoke`, `contracts`) are changed only by the owner's scripts: `tools/apply_amendment_aNNN.sh`, `tools/apply_core_red_tests.sh` (look, `--report`, `--do`). Write a staging copy and a script; try `--do` on a scratch copy first.
- Next free numbers (check master and the other branches first): D-412, A-168, TC-GTB-037, TC-WFM-179, REQ-WFM-162, REQ-GTB-033, AC-CORE-23, TC-IF-301-27.

## 6. Working rules (the owner's preferences)
- Decisions as a questionnaire (AskUserQuestion), recommended option first; reviews by thematic group (D-407).
- Never sign for the owner: `[ ]` boxes, `Validated by`, `Decided by`, `Reviewed by` stay empty until he ticks or says so; record how he said it.
- Test venv `/home/maldun/prog/Python/venvs/mia312/bin/python`; name files by full path; privacy is no concern (personal use), untrusted web text still is.
- Commits end with the Co-Authored-By line of the session; name paths in every `git add`; never commit another session's changes.
- Leave files alone while the owner may have them open in Emacs.
