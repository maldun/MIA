# Goal G-V4.VALIDATE – Validation of G-V2 and G-V3 after the G-V4 rework

Opened 2026-11-20 on the owner's request: G-V2 (v0.2.x) and G-V3 are in the Validate phase, and G-V4 starts a larger rework. Parts of the rework may change what the validation runs would see, so validating v0.2.1 now would be effort that may have to be repeated. The validation of both goals is therefore collected here and run **on the version after the rework**. G-V4 now has a goal record (`../G-V4/goal.md`, Proposed); this subgoal is its last one and a draft until the rework is planned.

- Kind: subgoal
- Parent: G-V4
- Statement: The owner has judged, in real use of the version after the G-V4 rework, whether the converted skills and snapshots (G-V2) and the Skill run view with the spoken-only chat and the report (G-V3) are the right thing, and every finding is triaged.
- Exit criterion: VAL-007, VAL-009, VAL-012, VAL-013 and VAL-006 (field items) rated pass, partial or fail with evidence; the Provisional strip height of REQ-CLV-041 settled; every finding triaged; decision on the next iteration recorded (validation report)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.validate
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given the finished rework, when the owner uses the version, then G-V2 and G-V3 are judged in real use and every finding is triaged | OC-5 of G-V4 (FR-6, FR-46) |
| OC-2 | Given the validation runs, when a graph turns out weak, then the owner improves it with the editor | OC-9 of G-V4 (FR-22) |

## Validation goals collected
| From | Criterion | What it settles | Source |
|---|---|---|---|
| G-V2 | VAL-007 | converted skills and snapshots as good as before (OC-1, OC-2 of CONVERT); V2-4 timing on both runners | `test-spec.md`, `goals/G-V2/goal.md`, `goals/G-V2/verification-report.md` |
| G-V2 | VAL-009 | skill record and refusals understood (MODEL OC-1 to OC-3) | `test-spec.md` |
| G-V3 | VAL-012 | the Skill run view followed without the chat; **Provisional** strip height of REQ-CLV-041 | `test-spec.md`, `goals/G-V3/goal.md` |
| G-V3 | VAL-013 | summaries and status messages faithful and in persona at production temperature (TR-CHAT-001) | `test-spec.md`, `G-V3.CHAT/holdout-decision.md` |
| G-V3.REPORT | FB-08 | closed: re-validated by the owner on 2026-11-20 (v0.2.1) | `feedback/FB-08.md` |
| both | VAL-006 | speed and weight in daily use (field items) | `test-spec.md` |
| both | open items | V2-4, V3-6, F-04 (D-344), V2-6 (THR-011 has no red-team case), TD-82 to TD-90 | verification reports, `deferred.md` |

The plan for sessions, tasks and analysis is `specs/mia/validation-plan-v0.2.1.md`. It is written against v0.2.1 and is the starting point: **re-base it on the post-rework version** (frozen version, pins, which skills run on which path, which VAL steps the rework made obsolete or changed).

## First task: review the validation goals after the rework
The subgoal starts with a review of every criterion in "Validation goals collected", **once the G-V4 rework is finished** (merged and deployed), before any session is prepared. The review updates the goals to what the reworked version is; the owner decides each one.

For each criterion (VAL-006, 007, 009, 012, 013) and each open item, take the finished rework's changes (its goal record, verification reports and amendments) and decide:
- **keep**: nothing the rework changed is observed by it;
- **change**: wording, session, evidence or tool names no longer fit (for example the converted-skill path, runner, Skill run view and layout, digest step, report, run-log events, model pins); the change goes through a test-spec amendment, not into the session notes only;
- **drop or replace**: the rework made it obsolete or answered it (with the reason);
- **add**: a new validation criterion for a rework change that users can judge.

Also: re-check the Provisional strip height of REQ-CLV-041 and every other `Provisional:` the rework touched (`grep -rn "Provisional:"`), the open items (V2-4, V3-6, F-04, V2-6, TD-82 to TD-90: still open, fixed, or moved), the assumptions (ASM-MU-001, model and VRAM) and the "not covered" contexts. A criterion that no rework change touches may be run on v0.2.1 earlier without waste; the owner may allow that.

Output: a short `validation-goals-review.md` in this folder (one row per criterion: keep / change / drop / add, reason, owner decision), the amendments it needs, and the re-based `validation-plan` for the frozen post-rework version. Only then do the sessions start.

## Open
- G-V4 is Proposed with its subgoals (D-360); the owner's Explore gate is open. Until the rework is planned, the line of work and the dependency "after the rework is deployed" stay placeholders. The editor-driven improvement of the workflow graphs (OC-9 of G-V4) is a stage of this subgoal; its place in the plan is open.
- Decide whether VAL-001, 003, 004 and 005 (G-V1 material, never run, D-185) join this round.
- Retention and deletion date for the run logs, and consent of any user besides the owner (validation plan).
- Whether the Validate rows of G-V2 and G-V3 (`goal.md`, Phases) should say "deferred to G-V4.VALIDATE". Not changed yet.
- Whether a version tag of the rework is the frozen version for this subgoal (needs a deployment record for it first).

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.VALIDATE | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | open | the review of the validation goals after the rework (First task), `validation-goals-review.md` |
| Plan | open | amend `test-spec.md` as the review decides; re-base `validation-plan-v0.2.1.md` on the post-rework version |
| Implement | empty | no code; only analysis tooling if `run_explain.py` lacks a query |
| Verify | empty | nothing built |
| Commit | empty | records only |
| Deploy | empty | uses the deployment of the G-V4 rework |
| Validate | open | the whole subgoal |
