# Handover: G-V4.VIEW fixes after Verify done; next Re-verify (2026-11-24)

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-view`, branch `goal/v4.view` (tracks `origin/goal/v4.view`; the owner pushes). Start in a **fresh, independent session** that did not write the fixes: read `CLAUDE.md`, this file, `specs/mia/goals/G-V4.VIEW/verification-report.md` (findings V-1 to V-15, D-501), the section "Fixes after Verify" of `specs/mia/goals/G-V4.VIEW/implementation-log.md`, `goal.md` and `plan.md`. Then load `dev-workflow` and `verify-phase` (VIEW has no model step; the agent additions do not apply). This file supersedes `handover-2026-11-24-g-v4-view-fixes-next.md`.

## State
| Item | State | Where |
|---|---|---|
| Implement | T-01 to T-12 done; fixes after Verify done (D-501), one commit per reopened task | `implementation-log.md`, Phases row in `goal.md` |
| Verify | report drafted (proposal: not yet verified), verdict box empty; re-verify of the fix commits open | `verification-report.md` |
| V-15 | closed; keep the image tag `mia-view-check` until the merge | report, D-501 (4) |
| V-3 | handed to G-V4.GRAPHSTORE.TRANSFER; the line in TRANSFER's record is written by the session that works on TRANSFER | D-501 (2) |
| V-6, V-7, V-11, V-12, V-14 | accepted; V-7, V-11 and V-14 go into the specification at Commit | D-501 (3) |

## The fix commits to review (only these)
| Finding | Task | Commit | Test added (not protected) |
|---|---|---|---|
| V-1, V-8 | T-08 | `80c43641` | `tests/js/graph-viewer-fixes.test.mjs` (V-1, V-8) |
| V-10 | T-07 | `4fccc9c8` | same file (V-10) |
| V-2, V-9 | T-10 | `af76fb51` | `tests/js/graph-drawing-scheme.test.mjs`; `tests/js/graph-settings.test.mjs` (V-9) |
| V-5 | T-04 | `7b945c1e` | `tests/test_graph_api_v2.py` `test_a_connection_id_of_the_wrong_form_is_invalid_on_save_and_check` |
| V-4 | T-06 | `e86ce702` | `tests/test_graph_api_v2.py` `test_an_entry_whose_before_is_not_the_stored_value_is_refused` |
| V-13 | T-12 | `976348e4` | – (`check_sysml.sh`, model check) |
| log | – | `cd906b88`, `d8df65cf` | – |

Range: `git diff f02c8f00..d8df65cf`. No protected file was changed; the protected diff since `b961c573` must still show only A-175.

## Points for the reviewer
1. **V-5 is narrower than the old handover's table.** Only a connection object whose `id` is missing or not text gave the 500; it is now 422 `invalid`, detail `graph`. Every other wrong form (a step that is text, a step id that is an object, a connection without `from`, a connection that is text) was and stays 422 `rules_broken` with the rule report, as T-04's test `test_a_broken_rule_is_refused_with_the_report` decides. Open question for the owner in the log, to settle at Commit together with V-7. Judge whether REQ-API-048 is met as it stands.
2. **`repro_f2.py` cannot show V-9 as written.** It blocks every cookie, so the login cookie is not sent and `GET /graph/` answers 401 before any script runs (0 areas with and without the fix). The implementer's variant kept cookies and made only the `localStorage` getter throw `SecurityError` (`page.add_init_script`): old `app.js` 0 areas and "The operation is insecure.", fixed 8 areas, 6 entries, no error. Re-create such a variant yourself rather than trusting this line.
3. **V-10 behaviour:** a 503 of any route sets the store entry to "not reachable"; the next route that answers sets it back to "reachable". Without a 503 the entry stays as the store route said at start (an existing test expects "not reachable" from the store route even when the list answers).
4. **V-2:** the scheme listener in `drawing.js` updates node colours (`nodes.update` of `font`, `color`, and `ctxRenderer` for hexagons) and the edge options in place; no `show()`, no solver restart. The unit test uses a recording vis stand-in; `repro_f3.py` is the real-browser evidence.
5. **V-13:** `graph-view.js` is no longer named in the model (the page does not load it; the file stays for the protected smoke check, D-500).

## Re-verify (D-501)
- The automated checks in full, sequentially (not in parallel: `mia.log`):
  - `tests/acceptance/test_view_backend.py`, `tests/acceptance/test_graph_view_files.py`
  - `tests/acceptance/contract/test_if_104_v2_graph_api.py` (33, PostgreSQL under podman)
  - `node --test tests/acceptance/graph_view_page.test.mjs`
  - `tests/acceptance/test_graph_view_browser.py`, three runs in a row
  - `node --test "tests/js/*.test.mjs"`
  - `<venv python> -m unittest discover -s tests`
  - every acceptance script one by one; known reds outside VIEW: `test_decide_guard.py`, `test_judge_calibration.py` (G-V3.REPORT F-3)
  - `bash tools/check_sysml.sh`, `python3 -I tools/check_sysml_model.py .`, the traceability check (549 ERROR lines expected, none new) and `goal_check.py` (82 errors expected)
- The protected diff since `b961c573` (only A-175).
- The three reproduction scripts in `specs/mia/goals/G-V4.VIEW/verify-repro/` (`<venv python> <script> <checkout root>`), plus your own storage-only variant for V-9 (point 2).
- A review of the fix commits only (table above).
- Append a short section "Re-verify" to `verification-report.md`: per finding closed or not, new findings if any, the proposal. The owner ticks the verdict box; then the close look at the page by the list in the report's notes.

The implementer's runs (2026-11-24, feedback only): JS 230 pass; unit suite exit 0, 2590 tests, 5 skipped (`test_delivery_on_stack` skipped: no model server answered then), 2 expected failures; browser checks 7/7 three times; contract suite 33 OK; all acceptance scripts OK but the two known reds; model checks 0/0; 549 / 82 unchanged.

Shared Ollama: VIEW's checks call no model. `test_delivery_on_stack` asks the model server only whether it answers; start Ollama if that test should run instead of skip.

## Then
Commit (merge into `goal/v4`; requirements, checks and TR-VIEW into the node files; Witnesses of AC-009 to AC-016 and AC-035; V-7, V-11, V-14 and the V-5 question into the specification), Deploy (SMOKE-VIEW-001 and 002; the owner's look with `store: database`), Validate as the goal record says.

Next free numbers: D-502 (VIEW's block D-500 to D-519), A-176, TC-API-026, TR-VIEW-022, TC-GA-040, TC-OPR-012, SMOKE-VIEW-003. REQ-API for VIEW stays at or below 059.
