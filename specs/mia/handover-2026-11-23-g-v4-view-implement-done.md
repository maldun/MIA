# Handover: G-V4.VIEW Implement done; next Verify (2026-11-23)

Worktree `/home/maldun/prog/Python/MIA-goal-v4-view`, branch `goal/v4.view` (not pushed). Start Verify in a **fresh, independent session** that has not seen the implementation chat: read `CLAUDE.md`, this file, `specs/mia/goals/G-V4.VIEW/goal.md`, `plan.md`, then load `dev-workflow` and `verify-phase`. The plan baseline is the tag `plan-baseline-g-v4-view` (red tests `82327296`).

## State
| Item | State | Where |
|---|---|---|
| Tasks | T-01 to T-12 done, one commit each (T-12 has a follow-up commit for the owner's layout, D-459) | `git log plan-baseline-g-v4-view..goal/v4.view`; `specs/mia/goals/G-V4.VIEW/implementation-log.md` |
| Amendments | A-175 installed by the owner (`fe03ab23`, D-454): TC-GA-025 now sees its defect | `specs/mia/amendments/A-175/` |
| Findings | F-1 closed (A-175); F-2 kept by the owner (D-500): `graph_app/graph-view.js` stays for the protected smoke check | implementation log |
| Owner's decisions during Implement | D-448 to D-459, D-500 | `specs/mia/review-log.md` |
| Phases table | Implement done | `goal.md` |

## Checks reported green (my runs: feedback, not verification)
- Track A: IF-104 v2 suite 33/33 (mock, files, postgres), `test_view_backend.py` 9/9, IF-302 record tables 28/28.
- Track B: `graph_view_page.test.mjs` 15/15, `test_graph_view_files.py` 2/2, `test_graph_view_browser.py` 7/7 (three runs in a row, Firefox of Playwright, headless).
- Regression after T-12: unit suite 2588 OK (5 skipped, 2 expected failures), `tests/js` 225 pass, every acceptance script OK except the known reds `test_decide_guard.py` and `test_judge_calibration.py` (G-V3.REPORT F-3, red on `goal/v4` too); traceability: the same 549 ERROR lines as at the plan gate, none new; model check OK. After the layout change (D-459) the page, file and browser checks were run again, not the whole unit suite (the change touched `graph_app/` and one JS unit test only).
- Every check of TR-VIEW-021 was run once against its planned defect; each failed as planned (tables per task in the log).

## For the reviewer (Verify)
1. **Plan deviations** (logged per task): checks the plan put into a task that needed a route of a later task waited for it (TC-API-018, 020, TC-IF-104-27 → T-03; TC-IF-104-20 → T-06; TC-API-021 → T-05; TC-GA-017 → T-11); `api.js` written in T-07 (plan: T-08); `app.js` replaced in T-07; unit tests written after the code in T-02 and T-03 (the code had been drafted before), test-first from T-04 on.
2. **Behaviour only in the code (P25)**: every task's log lists its open questions; the owner kept all of them for Verify and the merge (D-448 to D-457). Notable: `onSelect` added to the drawing interface (section 3 of the page interface note); the view settings moved to the picture's header (D-458); the store part has no visible heading, so REQ-GA-012's "visible by its label" holds for it only for screen readers (D-459); a `remove_step` entry carries `connections` (not in IF-104 v2's entry fields).
3. **F-2**: the plan's T-12 removal of `graph-view.js` was not done (D-500).
4. **Shared Ollama**: VIEW's checks call no model; still look at `ListAgents` before long runs (CLAUDE.md).
5. **Demonstrator**: the owner looked at `/graph/` in Firefox on the seeded test store (the browser checks' server helper, `tests/helpers/graph_view_server.py`), not yet with `store: database`; that and SMOKE-VIEW-001, 002 belong to Deploy.

## Next
1. Verify (`verify-phase`) in a fresh session: verification matrix, re-run of every check in a clean environment, protected material unchanged except A-171 to A-175, the code against `architecture.sysml` (`webApp.graphApiV2` built; the page node N-5), batched human review with a close look at the page (the owner's rule: close look where users feel it).
2. Then Commit (merge into `goal/v4`), Deploy, Validate as the goal record says.

Next free numbers: D-501 (VIEW's block D-500 to D-519, D-500), A-176, TC-API-026, TR-VIEW-022, TC-GA-040, TC-OPR-012, SMOKE-VIEW-003. REQ-API for VIEW stays at or below 059.
