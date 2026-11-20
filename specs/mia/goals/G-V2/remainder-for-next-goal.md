# G-V2 closed (2026-11-20): what goes to the next goal

Owner decision 2026-11-20: G-V2 is closed with release v0.2.1 (Verified with accepted deviations, D-358). The items below are not part of G-V2 any more; a new goal takes them. Draft its scope from this list in Explore or Plan.

## Requirements and plan documents
- Requirements still Draft (owner approval open): REQ-RUN-030 to 035, REQ-WFM-057 to 060, 069, 110 to 115 (all other G-V2 requirements are Verified).
- V2-1: scope wording `REQ-WFM-143` (goal_check GL3); write the requirement when TD-87 is closed.
- V2-2: code behaviour without a requirement (`conversion_dir` and its default, `tool_call` and `budget_spent` events, status `budget` on the converted path).
- V2-8: TC-WFM-110 to 114 are in no table of the node test-spec.
- V2-6: red-team case and `TB-exchange` row for THR-011 (agent_check A8, 2 errors).
- goal_check: GL1 (G-V2 and G-V3 both open iteration goals, Q-7), GL3 (SNAPSHOT scope ids and interface versions, TOOLBOX `IF-302`).
- trace_check: 553 errors at the tag; WARN: TD triggers without a date, TDs not listed in the node verification reports.

## Code
- V2-3: stale "STUBS" docstring in `skill_converter.py` (Implement).
- `test_decide_guard.py` and `test_judge_calibration.py` fail on master (`behaviour.FUNCTIONS`).

## Open deferrals (all signed 2026-11-20)
TD-86 live trust and lifecycle on the converted path; TD-87 budgets and stop on the converted path; TD-88 AC-34 on dev only (holdout suites, labelled by the owner); TD-89 research.escalate@3 vs @1; TD-90 real half of the IF-103 contract suite (scripted proxy in front of Ollama). Triggers of TD-86 to TD-89: the start of the sub goal "improve the skills" (D-355, D-356). TD-81 to TD-85 as before.

## Validate items (not a goal of their own)
VAL-007 (a converted skill through the UI), V2-4 (speed difference of the converted and the old runner), the transcript sample of the Verify (report section 6), plausibility ratings are dropped (prototype tests instead).

## Baselines
The old-runner dev baselines of D-355 stay. New baselines wait for holdout suites (TD-88).
