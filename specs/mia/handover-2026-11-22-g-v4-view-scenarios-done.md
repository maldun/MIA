# Handover: G-V4.VIEW Plan, architecture and scenarios approved; next the test requirements (2026-11-22)

Worktree `/home/maldun/prog/Python/MIA-goal-v4-view`, branch `goal/v4.view` (not pushed). Read this, `CLAUDE.md` and the previous handover `handover-2026-11-22-g-v4-view-requirements-done.md` (sections 4 and 5 still hold); load `dev-workflow` and `plan-phase`.

## Done in this session
| Item | State | Where |
|---|---|---|
| Architecture entries | approved (D-439) | `specs/mia/architecture.sysml`: 22 G-V4 items (FR-48 to 55, 70 to 74, 76, 77, 80, 81, 95, NFR-12 to 14, 19), IF-104 v2 port and link (`webApp.graphPort` to `graphApp.graphPort`), `webApp.graphApiV2`, GraphApp parts `pageFrame`, `graphList`, `graphView`, `detailsColumn`, `historyList`; generator takes RULES' HR-parent resolution. `check_sysml.sh` 0/0, `check_sysml_model.py` OK |
| REQ-GA-021, 024 | shifted attribute lines restored, re-approved | `goals/G-V4.VIEW/requirements.md` |
| Test spec with scenarios | approved by group (D-441) | `goals/G-V4.VIEW/test-spec.md`: TC-API-018 to 025, TC-OPR-011, TC-GA-017 to 039, TC-IF-104-17 to 27, TC-IF-302-13, 14, SMOKE-VIEW-001, 002, VAL-VIEW-01; Verified by filled in all 70 requirements (re-marked, D-440 (3)) |
| A-174 (IF-104 v2 cases renumbered 06..16 to 17..27) | **installed** (owner, commit de563198) | `specs/mia/amendments/A-174/`, `tools/apply_amendment_a174.sh` (the owner runs `--do` or says "approved") |
| Store setting | decided (D-440 (4)) | key `store` = `files` (default) or `database`, address from `MIA_DATABASE_URL`; answer sent to the TRANSFER session |

## Next
1. (done) A-174 installed.
2. `test-requirements.md` (TR-VIEW-001 on): setup kind with numbers (stores: files and throw-away postgres:16; JS and Python mock fidelity; Firefox build of the pinned Playwright, 1280 x 800, colour schemes; R11 fixtures plus `cp2.multi`, a context graph, a `swarm` graph, a `chat` graph, a ~50-step graph; for each check the step that shows it can fail). Review one check at a time.
3. Red tests staged under `specs/mia/amendments/A-175…/` (install Playwright first, see the previous handover step 4); the Firefox checks use the real provider on a seeded file store (D-440 (2)).
4. `plan.md` with the binding map, then the plan gate.

Next free numbers: D-442, A-175, TC-API-026, TC-GA-040, TC-OPR-012, SMOKE-VIEW-003, TR-VIEW-001 (REQ numbers as before).
