# Hand-over after Plan step 3 of G-V2.TOOLBOX (written 2026-11-08): what is done, what is open

Read `CLAUDE.md` first. Line of work `goal/v2.toolbox`, worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox` (branched from master `66fc76a`, STORE merged). Commit there, never `git add -A`, name the paths. The owner merges. Skills for the next session: `dev-workflow`, `plan-phase` (`agent-app` only to know it does not apply: no model step, prompt or eval).

## State
- Explore: done for FR-38 (HLS of iteration 2, D-186). A prototype answered the open questions: branch `prototype/toolbox`, worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/prototype-toolbox`, folder `specs/mia/prototypes/toolbox/` (never merged, Status: Prototype). Files: `toolbox.py`, `check_toolbox.py` (11 checks, green), `explore_toolbox.py` (guided tour), `prototype-report.md` (carry-over table filled in by the owner), `proposed-spec-changes.md` (older than step 3, superseded by `requirements.md`), `plan.md` (draft of Step 5, commit `175f97b`).
- Plan step 0: `goals/G-V2.TOOLBOX/goal.md` amended (commit `4768d5d`, later extended in `308c67f`): TOOLBOX adds the `transforms` part of IF-203 v1 itself, IF-302 gets one new table (A-110, proposed), scope now has REQ-WFM-090..095, Split check row is `open`.
- Plan step 3 (commit `308c67f`, everything Draft): in the N-2.3 files REQ-WFM-090..095 (new), changed criteria of 050, 054, 068 and text of 056, 16 checks TC-WFM-050..056, 067, 068, 070, 090..095 with scenarios in `test-spec.md`, TR-TOOLBOX-001..006 in `specs/mia/test-requirements.md`, proposals (not ratings) for 090..095 in `plausibility-proposal.yaml`, regenerated requirement block of `architecture.sysml`.
- Not started: Step 4 (red tests), Step 5 (`goals/G-V2.TOOLBOX/plan.md`), review in batches, Implement.

## Checks as of `308c67f`
- `req_lint` (N-2.3 requirements): no error on the toolbox IDs, INFO only (singular? on 092, 093).
- `bash tools/check_sysml.sh`: 0 errors. `check_sysml_model.py`: OK.
- `goal_check`: 2 errors. GL3 "IF-302 is in scope here but not in the scope of G-V2" (parent session must fix); GL1 two open iteration goals (G-V2, G-V3), not from this work, not checked whether older.
- `trace_check`: 536 errors, the six of REQ-WFM-090..095 (not in the model) are gone; the rest was there before. `req_graph`: 18 errors, none on the toolbox.
- `req_plausibility`: 6 errors, REQ-WFM-090..095 have no rating. A person rates them; do not write `rated_by` yourself.

## Owner decisions of 2026-11-08 (do not re-ask)
D1 one entry per ID, latest version / D2 shipped nodes in the same toolbox, flagged shipped, not exported / D3 a retired untrusted transform runs as a baseline only with the owner's allowance given when retiring, never in a graph / D4 SC-09 stays, stated as a risk / D5 trust and lifecycle carry over to a newer version, the change of a trusted one is logged (REQ-WFM-093) / TOOLBOX itself builds the `transforms` part of IF-203 v1 (option A) / a new table in IF-302 for transform meta / any logged-in account may untrust, only trusting is owner-only / `workflow_library.py` is shared with MODEL and CONVERT: own block, own methods, merge order STORE, MODEL, TOOLBOX, CONVERT / IDs from the TOOLBOX block of `goals/G-V2/parallel-work.md` (REQ-WFM-090..109, A-110..119, D-220..239, TD-40..49, SC-30..39, TR-TOOLBOX-).

## Decisions still needed
1. **Owner:** rate REQ-WFM-090..095 (plausibility).
2. **Owner:** split REQ-WFM-092 and 093 or keep (several "and" in the lint, INFO).
3. **Owner:** split the goal or keep it together (16 requirements, IF-203, IF-302 table, six tasks); the Split check row says `open`.
4. **Owner:** is the History line of REQ-WFM-054 ("A-89 not yet approved") stale because A-90 superseded it? Not checked.
5. **Owner:** approve amendment A-110 (IF-302 table for transform meta).
6. **Owner:** start the batched review (`req_review.py`), group TB first.
7. **Parent session** (parent-only files, `parallel-work.md`): `goals/G-V2/goal.md` (IF-302 in scope; line 115 "all three extend it" now has an owner), `high-level-spec.md` (FR-38 text with lifecycle, AC-32 split into AC-32a..c, wording in the prototype's `proposed-spec-changes.md`), root `requirements.md`.

## Next steps, in order
1. Owner answers 1 to 6 (questionnaire in the style of `decisions-as-questionnaire`, one item per question).
2. Step 5: write `goals/G-V2.TOOLBOX/plan.md` from the prototype's draft `plan.md` (same branch folder `specs/mia/prototypes/toolbox/plan.md`); tasks T-01 to T-06, T-06 waits for STORE and A-110.
3. Step 4 in a separate session: IF-203 v1 contract suite for `transforms`, A-110 with the IF-302 contract suite, red tests TC-WFM-050..056, 067, 068, 070, 090..095 in `tests/acceptance/`, helpers (mock of the library part, fixed copy of three shipped nodes, marker folder, account lookup, event stand-in). The owner installs them; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `contracts/`.
4. `git rebase master` before the merge, then `goal_check`, `trace_check`, `req_graph`, `req_lint`, `bash tools/check_sysml.sh`; tag `plan-baseline-it2-toolbox` (local, never pushed by an agent).

## Rules that bite
- Requirements that are approved never merge with `union`; these are all Draft, so edits are allowed in this branch, but the owner settles conflicts with MODEL or CONVERT.
- Do not take IDs outside the TOOLBOX block. Do not touch `goals/G-V2/goal.md`, `high-level-spec.md`, root `requirements.md`, `contracts/` or `tests/acceptance/`.
- Keep `tools/gen_node_requirements_model.py .` and `bash tools/check_sysml.sh` after every change of a requirement; on a conflict in `architecture.sysml` take master's version and regenerate.
- The prototype is evidence, not code to copy: the code is rewritten test-first in Implement. Its findings: shipped IDs have several versions in `library/nodes` (89 files, 73 IDs), shipped nodes have no code text, a retired untrusted transform needs the owner's allowance to be a baseline.
- Known risks (accepted): D5 new code runs without a new decision; SC-09 / TD-24 trusted code runs unsandboxed in the MIA process.
