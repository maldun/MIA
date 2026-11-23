# Handover: G-V4.VIEW Verify found defects; back to Implement (2026-11-23)

Worktree `/home/maldun/prog/Python/MIA-goal-v4-view`, branch `goal/v4.view`. Report: `specs/mia/goals/G-V4.VIEW/verification-report.md` (independent reviewer; proposal: not yet verified). Owner's decisions: D-501 in `specs/mia/review-log.md`.

## For the Implement session (load `dev-workflow`, `implement-phase`)
For every item: a failing test first (log it as a finding), then the fix. Protected tests stay unchanged (D-501 (1)). One commit per reopened task, with the V-number in the message.

| Finding | Task | What to do | Reproduction |
|---|---|---|---|
| V-1 | T-08 | `graph_app/viewer.js:86`: `list.children.filter` throws in Firefox (`HTMLCollection`). Unit test with an `HTMLCollection`-like `children` (the fake DOM in `tests/js/fake-dom.mjs` returns an Array, which hid it), then `Array.from` | `verify-repro/repro_f1.py` |
| V-2 | T-10 | `graph_app/drawing.js:117`: the theme listener re-shows the last opened data, so dropped places are lost. Re-colour the shown nodes and edges instead | `verify-repro/repro_f3.py` |
| V-4 | T-06 | `graph_api_v2.py:172-183`: the `before` of an editor entry is kept as sent. Check it against the current version (refuse `changes_do_not_match`) | report V-4 |
| V-5 | T-04 | `graph_api_v2.py:240`: a step or connection that is not `{id: text, …}` crashes `derive` (500). Answer 422 `invalid` detail `graph` | report V-5 |
| V-8 | T-08 | `viewer.js:107-114`: a 401 while a graph is open must clear the problems, step list, left column and history, and stop Previous and Next | report V-8 |
| V-9 | T-10 | `graph_app/app.js:10`: read `localStorage` inside a try; the viewer works with its defaults | `verify-repro/repro_f2.py` |
| V-10 | T-07 | `viewer.js:204`: the store entry follows the answers (not reachable after a 503, reachable again after a success) | report V-10 |
| V-13 | T-12 | `specs/mia/architecture.sysml` `part def GraphApp`: statuses and modules of `pageFrame`, `graphList`, `graphView`, `detailsColumn`, `historyList`; then `bash tools/check_sysml.sh` and `check_sysml_model.py` | – |

Not in Implement: V-3 goes to TRANSFER (note it in TRANSFER's handover); V-6, V-7, V-11, V-12 and V-14 are accepted (V-7, V-11 and V-14 are written into the specification at Commit).

## The owner (V-15) – done 2026-11-24
The image was built and `tests/test_delivery_on_stack.py` is OK (5 tests). Keep the tag `mia-view-check` until the merge: removing it can drop the cached pip layer, and the offline build would fail again.

What was run: `podman build -f deploy/Containerfile -t mia-view-check .` in the worktree (with network), so that the offline build of `tests/test_delivery_on_stack.py` finds the new pip layer.

## Then Verify again (a fresh session)
Run the automated checks in full and the three reproductions in `specs/mia/goals/G-V4.VIEW/verify-repro/`. Review only the fix commits. Re-run `tests/test_delivery_on_stack.py`. Fill the verdict box.

Next free numbers: D-502 (VIEW's block D-500 to D-519), A-176.
