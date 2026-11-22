# Handover: G-V4.GRAPHAPI.RULES, requirements drafted, IF-301 v4 text staged; next the review by group (2026-11-22)

Read first: this file, `CLAUDE.md`, the previous handovers `handover-2026-11-22-g-v4-rules-round04-done.md` and `handover-2026-11-22-g-v4-rules-plan-next.md` (sections 5 and 7 still hold), skills `dev-workflow`, `plan-phase`, `agent-app`. The owner (Stefan Reiterer, maldun) decides every gate.

## 1. Where we are
| Item | State |
|---|---|
| Line of work | `goal/v4.graphapi.rules`, worktree `/home/maldun/prog/Python/MIA-goal-v4-rules`, not pushed |
| High-level spec | approved (ticked, `f1a0ab00`) |
| Requirements | **drafted**: `/home/maldun/prog/Python/MIA-goal-v4-rules/specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md`, 27 new (REQ-GTB-033 to 052, REQ-WFM-162 to 165, REQ-RUN-036 to 039) and 3 changed (REQ-WFM-150, 154 with V-2, 155), six groups RS, RD, RF, SV, RR, DF; lint 0 errors, 0 warnings; **all 31 approved by the owner group by group** (2026-11-22, `goals/G-V4.GRAPHAPI.RULES/review-log.md`) |
| IF-301 v4 (A-170) | staging text `/home/maldun/prog/Python/MIA-goal-v4-rules/specs/mia/amendments/A-170/IF-301-graph-tables.md` (v3 plus `kinds()`, `rule_report(graph)`, `run_check(graph, given)`, rules in detail, golden 24 to 31, decision 18); suite, mock and the owner's apply script still to write |
| Decisions | D-418 (questionnaire, all as recommended): (1) inputs of a Stage with a prepare function count as given (REQ-RUN-039), REQ-RUN-034 unchanged; (2) malformed input reported by the eight rules as staged; (3) RULES kept together |

## 2. Findings of this session (evidence for the test spec)
- Scratch run (copy of the worktree in the job folder, prototype rule set put in front of `GraphRunner.run`): protected TC-RUN-016, 017, 033, 034 (with REQ-RUN-039), `test_graph_order.py`, `test_skill_binding.py`, `test_run_converted.py` pass unchanged. Two lessons, both now requirements: the refused run must keep repeated IDs (REQ-RUN-037; the prototype's `run_guarded` removed them), and a transform connected to itself now also names `adjacency` (REQ-GTB-045): the unit check `tests/test_graph_run_findings.py` (self-loop) changes in Implement.
- Four files fail the same way with and without the run check (`test_convert_verify_fixes.py`, `test_conversion_record.py`, `test_harness_converted.py`, `test_skill_conversion.py` on the scratch copy): likely the copy's layout, not RULES; check them in the real worktree before the red commit.
- Goldens 26 to 29 of A-170 were checked against the prototype module and match; golden 31 (malformed input) is new behaviour (D-418 (2)).
- HLS section 5 names REQ-RUN-016 for the refusal change; the refusal is the new group RR instead, REQ-RUN-016 keeps its text (noted in the requirements file).

## 3. Next steps
1. Done: requirements reviewed and approved **by group** (memory: accept / waiver / discuss per group), order RS, RD, RF, SV, RR, DF: `python ~/.claude-work/skills/plan-phase/scripts/req_review.py --spec-dir specs/mia/goals/G-V4.GRAPHAPI.RULES --tests-dir tests next --group RS`, then `mark ... --by "Stefan Reiterer"` with how he said it.
2. Done: A-170 text approved in three parts (D-419).
3. Done: architecture entries (D-420; FR-63, FR-64 in the model, the 27 requirements generated with their links; `check_sysml.sh` 0 errors, `check_sysml_model.py` OK). Next: test spec with scenarios (TC-GTB-037 to 045, TC-WFM-179 to 184, TC-RUN-036 to 039, TC-IF-301-27 on), test requirements (HR-004 to HR-006 in detail), red tests, the A-170 suite and mock, `plan.md`, binding map, witnesses for AC-017 and AC-018.

## 4. Numbers
Next free (checked on all four branches 2026-11-22): D-422, A-171, REQ-WFM-166, REQ-GTB-053, REQ-RUN-040, TC-WFM-185, TC-GTB-046, TC-RUN-040, TC-IF-301-27, AC-41, ASM-9.

## Start prompt for the next session
> Continue G-V4.GRAPHAPI.RULES. Read `CLAUDE.md` and `specs/mia/handover-2026-11-22-g-v4-rules-requirements-drafted.md`, load `dev-workflow`, `plan-phase` and `agent-app`, work in `/home/maldun/prog/Python/MIA-goal-v4-rules`. The requirements and the A-170 text are approved; the architecture entries are in (D-420); continue with the test spec (Plan step 3). No plausibility records (D-421).
