# A-159 draft: split T-CV-05 (snapshots) out of G-V2.CONVERT; requirement for F-05; F-07 deferred

Status: **draft, not applied** (owner decisions of 2026-11-17: split; F-05 a requirement; F-07 later). The number A-159 is the next free one after A-158 at the time of writing: check before applying. Basis: `goals/G-V2.CONVERT/verification-report.md` (verdict "not verified as a whole": the conversion half is verifiable, snapshots are not built).

## 1. New subgoal G-V2.SNAPSHOT
- Kind: subgoal, parent G-V2, supervised, accepted by Stefan Reiterer (owner), line of work `goal/v2.snapshot`, status Proposed.
- Statement: the owner can take and restore a snapshot of the skill set (FR-47).
- Exit criterion: OC-2 of CONVERT (renumbered OC-1 here; it serves OC-4 of G-V2), checked by AC-40, TC-WFM-061 to 066 and VAL-007's snapshot part.
- Scope: REQ-WFM-061 to 066 (approved, `Approved` since 2026-11-17), task T-CV-05 (renamed T-SN-01, text unchanged), IF-203 v2, IF-302 v13, IF-102 v7 (A-121), the red tests TC-WFM-063 to 065 with `snapshot_lab.py` and `snapshot_store.py` moved to `set_current_version` (protected: owner's go).
- Depends on: A-121 installed (`A-121-contract-edits.patch`), IF-301 v2 (on master), CONVERT merged (it is).
- Ids: REQ-WFM-061 to 066 and TC-WFM-061 to 066 stay as they are (no renumbering); TR prefix `TR-SNAPSHOT-`; D-numbers and A-numbers from the parent's range.
- Split check row: "keep T-CV-05 inside CONVERT" reversed on 2026-11-17 because the contract text did not exist and the conversion half was ready to verify (owner).

## 2. Edits to G-V2.CONVERT (the goal file is its own session's: apply there)
| Where | Change |
|---|---|
| title and statement | "Conversion"; statement ends after "...for a written reason." (drop "and the owner can take and restore a snapshot") |
| exit criterion | OC-1 and OC-3 (OC-2 moves to G-V2.SNAPSHOT) |
| scope table | REQ-WFM-061 to 066 and IF-203 become `out` with reason "moved to G-V2.SNAPSHOT (A-159)"; group SN of the node moves with them |
| parts | `snapshotStore` row removed |
| plan.md | T-CV-05 and its row marked "moved to G-V2.SNAPSHOT as T-SN-01"; `test_skill_snapshots` is no longer a CONVERT check |
| verification report | verdict can be given for the conversion half: "verified with accepted deviations" once F-03, the baselines and F-05's requirement are settled |

## 3. Edit to G-V2 (parent only)
`goals/G-V2/goal.md`: Subgoals list gets G-V2.SNAPSHOT; OC-4 is now checked there. The exit criterion of G-V2 does not change (AC-34 with AC-31, 32, 38, 40).

## 4. F-05: requirement for budgets and stop on the converted path (proposal, id to confirm: next free REQ-WFM, today REQ-WFM-142)
- Level: low   Subject: TaskRuntime   Group: CV   Priority: Should   Method: Test
- Text: While a converted skill runs, the Workflow execution shall check the declared budgets (steps, seconds, calls, tokens) and the stop request before each step and end the run with status `budget` naming the exceeded key, or with status `stopped`, as the old runner does.
- Rationale: refines FR-45; verification finding F-05: today seconds and steps are checked only inside controllers, calls and tokens not at all, and a stop is read only at the start and in controllers.
- Acceptance criterion: AC-34: a straight-line converted pipeline with `budget: {seconds: 0.01}` and a slow scripted model ends with status `budget`, key `seconds`; a stop request raised during step 1 ends the run before step 2 (exact).
- Verified by: TC-WFM-142 (proposal; the next free TC id of the CONVERT range, to confirm), failing test already proposed in the report (F-05 row).
- Not in G-V2: the five skills declare only steps, seconds and tool budgets and are short, so no skill breaks today; the implementation belongs to the next sub goal (improve the skills), which already lists "`model_step` has no budget" (handover 2026-11-16, item 6).
- Open choice for the owner: this proposal asks for parity with the old runner. If parity is too much for now, the alternative is an accepted deviation in the verification report and no requirement.

## 5. F-07: deferred (owner: later)
Entry for `deferred.md`: "Converted runs read the app's real toolbox (trust and lifecycle live) instead of a fresh seeded one; proposed test: with `code.normalize_plan` set untrusted by the owner, `Core.run("plan_question")` refuses. Revisit in the sub goal that improves the skills. Source: Verify G-V2.CONVERT F-07, owner 2026-11-17." Until then the converted path runs only repo-shipped node code, so no untrusted code runs.

## 6. Order of application
1. Parent session installs A-121 (contracts, review-log row).
2. This amendment: goal files per sections 2 and 3, requirement of section 4 through the plan flow (review and plausibility are the owner's), `deferred.md` entry.
3. Owner's go for the protected test amendments of T-SN-01, then Implement in the new subgoal.
