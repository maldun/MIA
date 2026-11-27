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
2. (done) `goals/G-V4.VIEW/test-requirements.md`: TR-VIEW-001 to 021 approved by group (D-442). The fixtures are fixed by TR-VIEW-002 (`tests/fixtures/graph_view/`: R11 graphs plus `ctx.small`, `swarm.one`, `chat`, `chain.fifty`); the Firefox setup by TR-VIEW-008 to 013; the defects that show each check can fail go into `plan.md` (TR-VIEW-021).
3. (done) Red tests installed and committed (`82327296`, tag `plan-baseline-g-v4-view`, D-445): Playwright 1.64.1 and its Firefox 157 in `mia312`; page interface `goals/G-V4.VIEW/page-interface-note.md` (D-443); REQ-API-036's example now the extra field `colour` (D-444); page stubs `graph_app/viewer.js`, `api.js`, `drawing.js`. Known reds: `tests/acceptance/test_view_backend.py` (12), `test_graph_view_files.py` (2), `test_graph_view_browser.py` (7), `graph_view_page.test.mjs` (14), the real side of the IF-104 v2 suite (22) and of TC-IF-302-13, 14; TC-API-025 stays red until RULES is merged (TR-VIEW-014).
4. `plan.md`: Track A tasks first (record tables, store setting in web_app and the image, read routes, write routes, record of changes), then Track B (tokens and frame, list, picture, arrangement and settings, left column and history, the Firefox checks); per check the defect that shows it can fail (TR-VIEW-021); the binding map with AC-009 to AC-016 and AC-035; then the plan gate (protection of the new files is by the existing deny rules).

Next free numbers: D-446, A-175, TC-API-026, TR-VIEW-022, TC-GA-040, TC-OPR-012, SMOKE-VIEW-003. REQ-API: VIEW stays at or below 059 (TRANSFER holds 060 to 064, its D-465); otherwise REQ numbers as before.
