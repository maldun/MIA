# Handover: G-V4.VIEW plan drafted, RULES merged in; next the plan gate, then Implement T-01 (2026-11-23)

Worktree `/home/maldun/prog/Python/MIA-goal-v4-view`, branch `goal/v4.view` (not pushed). Read this, `CLAUDE.md`, `specs/mia/goals/G-V4.VIEW/plan.md`; sections 4 and 5 of `handover-2026-11-22-g-v4-view-requirements-done.md` still hold. Load `dev-workflow` and `implement-phase` (after the gate).

## Done in this session
| Item | State | Where |
|---|---|---|
| `plan.md` | drafted, owner's questionnaire answered (D-446), gate box open | `specs/mia/goals/G-V4.VIEW/plan.md`: T-01 to T-06 (Track A), T-07 to T-12 (Track B), defect per check (TR-VIEW-021), binding map AC-009 to AC-016, AC-035 |
| RULES into this branch | merged (D-446 (1)) | merge commit `b961c573`; `architecture.sysml` conflict resolved by keeping both sides; model regenerated unchanged; SysML checks 0/0, OK |
| Deny rules | added, for the owner's review (M20) | `.claude/settings.json`: `Edit(tests/fixtures/graph_view/**)`, `Edit(specs/mia/goals/*/test-requirements.md)` |
| Red state on the merged branch | same as the red commit | backend 12 failures, files 2, browser 7, node 14 (1 green), IF-104 v2 real side 22, IF-302-13, 14 errors; JS v2 suite 11 pass, 11 skipped; unit suite (`discover -s tests`, mia312) green, no known reds |

## Message from TRANSFER (2026-11-23, answered by the agent, for the owner to confirm)
TRANSFER (REQ-API-060 to 064, D-468) asked for `create_app(backend, accounts_store, store, allowed_origins, live=None)`, a keyword TRANSFER adds after VIEW's merge, plus whether its tests may import `WebAppProbe` and `checkout_with` from `tests/acceptance/test_view_backend.py`. The agent's answer: the keyword is fine if it is keyword-only and VIEW builds nothing for it; no import from the protected acceptance file: TRANSFER copies the two helpers into a helper of its own red-test install. TRANSFER took it over (its D-470 on `goal/v4.graphstore.transfer`: `*, live=None` in its T-06 after VIEW is merged, own `tests/helpers/web_app_probe.py`); nothing for VIEW to build. On the VIEW side not yet a decision record; the owner confirms or overrides it.

## Next
1. (done) Plan gate ticked (D-447). T-01 done (`3b7b8fb3`), T-02 done (`15ad28fc`), T-03 done (`55f2d122`), T-04 done (`b276b250`), T-05 done (`c66550fb`), T-06 done (`dfd1dd94`, Track A complete), T-07 done (`87e47482`), T-08 done (`e1c82471`), T-09 done (`edac887e`; A-175 staged `6ca6206f` for the owner to install), T-10 done (`d9e9aa1f`), T-11 done (`a5ee04e5`), T-12 done: Implement complete (F-2 and A-175 wait for the owner); log in `goals/G-V4.VIEW/implementation-log.md` (T-02 left TC-API-018, 020, TC-IF-104-27 for T-03, and three open questions).
2. Next: the owner looks at `/graph/` (demonstrator of T-12), installs A-175, decides F-2; then Verify (`verify-phase`) in a fresh, independent session, one session line on `goal/v4.view` (D-446 (3)). Each task: its defect per check run once and logged in `specs/mia/goals/G-V4.VIEW/implementation-log.md` (create it at T-01).

Next free numbers: D-460, A-176, TC-API-026, TR-VIEW-022, TC-GA-040, TC-OPR-012, SMOKE-VIEW-003. REQ-API for VIEW stays at or below 059.
