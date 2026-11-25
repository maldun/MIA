# A-175 – TC-GA-025 sees a graph of another kind drawn with the workflow shapes (G-V4.VIEW)

**Decided:** D-454, owner, 2026-11-23 (finding F-1 of T-09). **Installs:** `bash tools/apply_amendment_a175.sh --do` (the owner runs it, or says "approved"), then commit as "plan: A-175 installed".

**Why.** TC-GA-025 could not fail on its planned defect (TR-VIEW-021: "a graph of another kind drawn with workflow shapes"): `ctx.small` (types `concept`, `source`) and `swarm.one` (type `agent`) use no workflow step type, so the workflow shapes give the same boxes, and the backend sends no trust marks for a graph of another kind. Found in T-09 (implementation log, F-1).

**Changed (protected):**
- `tests/fixtures/graph_view/graphs.json`: `ctx.small` gets a third step `c.note` of type `data` (no connection). It saves through CORE's GraphModel (checked).
- `tests/acceptance/graph_view_page.test.mjs`: TC-GA-025 expects the types `concept`, `data`, `source` for `ctx.small` (every step still a box; `c.note` is a box, not an ellipse); its example and Given lines say so.
- `specs/mia/goals/G-V4.VIEW/test-requirements.md`: TR-VIEW-002 names the three types of `ctx.small`.

**Changed (not protected), with this amendment's commit:** the Given line of the TC-GA-025 scenario in `specs/mia/goals/G-V4.VIEW/test-spec.md`.

**Not changed:** REQ-GA-028 and its acceptance criterion; the other checks (no other check reads `ctx.small`'s steps or counts; the list shows it with 3 steps instead of 2, asserted nowhere).

**Expected after install:** `node --test tests/acceptance/graph_view_page.test.mjs`: TC-GA-025 green; with `isWorkflow` always true in `graph_app/step-marks.js` it fails (the defect of TR-VIEW-021).
