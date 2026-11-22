# Handover: G-V4.GRAPHAPI.RULES, merged into goal/v4; Deploy and Validate deferred; next TRANSFER (2026-11-22)

Read first: this file, `CLAUDE.md`, skills `dev-workflow`, `plan-phase` (or `implement-phase` once the gate is ticked), `agent-app`. The owner (Stefan Reiterer, maldun) decides every gate. Since D-423 the agent finishes RULES and TRANSFER on its own recommendations (recorded as taken by delegation) and asks the owner again at RUN, VIEW, EDIT and CONTEXT. No plausibility records (D-421). Older handovers: `handover-2026-11-22-g-v4-rules-round04-done.md`, `handover-2026-11-22-g-v4-rules-plan-next.md` (sections 5 and 7 still hold).

## 1. Where we are
| Item | State |
|---|---|
| Line of work | `goal/v4.graphapi.rules`, worktree `/home/maldun/prog/Python/MIA-goal-v4-rules`, not pushed |
| High-level spec | approved (`f1a0ab00`) |
| Requirements | 28 new (REQ-GTB-033 to 052, REQ-WFM-162 to 165, REQ-RUN-036 to 039) and 3 changed (REQ-WFM-150, 154, 155), **all approved by group** (`/home/maldun/prog/Python/MIA-goal-v4-rules/specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md`) |
| IF-301 v4 (A-170) | text approved in three parts (D-419); suite `test_if_301_v4_rule_set.py` (TC-IF-301-27 to 34) and mock `if_301_graph_tables_v4.py` staged in `specs/mia/amendments/A-170/tests/`; the mock passes the suite and every pure RULES check |
| Architecture | FR-63, FR-64 in the model; the 28 requirements generated with links to FR-63/64 (D-420); `check_sysml.sh` 0 errors, `check_sysml_model.py` OK |
| Test spec, test requirements | approved (D-422; TC-GTB-046, TC-GTB-047 and TR-RULES-003 corrected by delegation, D-424) |
| Red tests | staged in `specs/mia/goals/G-V4.GRAPHAPI.RULES/red-tests/` (4 acceptance files, helper `rules_graphs.py`, `smoke_rules.py`); stub `graph_rule_set.py` in the branch; on a scratch install every check fails by assertion, except those listed in `plan.md` "State at the red commit"; `test_doc_check.py` 0 findings |
| Plan | `plan.md` (T-01 rule set module, T-02 save path, T-03 runner, T-04 entry points and smoke) and `binding-map.md` (31 of 31 fixed), by delegation; the plan-gate box in `plan.md` and `Reviewed by` in `binding-map.md` are the owner's |

## 2. Next steps
1. Done 2026-11-22: A-170 installed (`fdbf2377`), red tests installed (`71523f7a`, tag `plan-baseline-g-v4-rules`), plan gate ticked by the owner (date field still empty, his). Plan phase done.
2. (Done, see 3.) Implement T-01 to T-04 in a fresh session (`implement-phase`), one commit per task; the defects of TR-RULES-008 logged per task.
3. Done 2026-11-22: Implement (T-01 to T-04) and Verify (verdict ticked by the owner, D-461; V-1 fixed `f478e040`, A-185 installed `fb3b72eb`).
4. Commit prepared 2026-11-22 (`goals/G-V4.GRAPHAPI.RULES/merge-request.md`): requirements and checks moved into N-3.2, N-2.3 and N-2.4.1 (`5cb4c87b`), the model regenerated, the witnesses of AC-017 and AC-018 filled, and TR-RULES-001 to 009 staged (`5ff3eb22`). The owner now runs `bash tools/apply_merge_g_v4_rules.sh --do`, commits "plan: RULES test requirements installed", then runs `git merge --no-ff goal/v4.graphapi.rules` on `goal/v4` in `/home/maldun/prog/Python/MIA-goal-v4`, and records the merge commit in `goal.md`. After that: Deploy (SMOKE-RULES-001 on the owner's host) and Validate (VAL-RULES-01, G-V5).
5. After RULES: TRANSFER on the agent's recommendations (D-423), in its own worktree; at RUN, VIEW, EDIT, CONTEXT ask the owner (VIEW/EDIT: design questions first; CONTEXT: purpose and use first).

## 3. Findings of this session (kept for Implement and Verify)
- The run check in front of the runner keeps every protected run test green when the inputs of a Stage with a prepare function count as given (D-418 (1)); the refusal must keep repeated IDs; the self-loop unit case of `tests/test_graph_run_findings.py` changes in T-03 (adds `adjacency`).
- `graph_tables.from_document` keeps a session as a transform: never use it to compare the old and new rules (D-424).
- HR ids repeat from goal to goal; the model generator resolves them (D-420).

## 4. Numbers
Next free (checked 2026-11-22): D-425, A-171, REQ-WFM-166, REQ-GTB-053, REQ-RUN-040, TC-WFM-185, TC-GTB-048, TC-RUN-041, TC-IF-301-35, AC-41, ASM-9.

## Start prompt for the next session
> Continue G-V4.GRAPHAPI.RULES. Read `CLAUDE.md` and `specs/mia/handover-2026-11-22-g-v4-rules-requirements-drafted.md`, work in `/home/maldun/prog/Python/MIA-goal-v4-rules`. If the red tests are installed and the plan gate is ticked, load `implement-phase` and start T-01.

## Closing state (2026-11-22)
RULES is merged into `goal/v4` (`ae34260a`): Plan, Implement, Verify (verdict ticked, V-1 fixed, V-2 by A-185, V-4 accepted, D-461) and Commit are done; Deploy and Validate are deferred (D-462: SMOKE-RULES-001 with the next deployable G-V4 build, VAL-RULES-01 with G-V5's first test run). The records committed on `goal/v4.graphapi.rules` after `ae34260a` (this section, the Commit row, the TRANSFER start handover) reach `goal/v4` with a second small merge by the owner. Next: TRANSFER, start handover `specs/mia/handover-2026-11-22-g-v4-transfer-start.md`.
