# A-176 – The graph page shows the main app's theme choice (G-V4.VIEW, REQ-GA-016)

**Decided:** D-503, owner, 2026-11-26 (the owner's look at Deploy: "no dark mode"). **Installs:** `bash tools/apply_amendment_a176.sh --do` (the owner runs it), then commit as "plan: A-176 installed".

**Why.** On the owner's host the system's colour scheme is light (`prefer-light`), so the graph page, which follows only the system (REQ-GA-016), is always light. The main app has its own choice Auto, Dark, Light (menu "Theme", saved on the device as `mia.theme`, `templates/static/chat/theme.js`); the graph page on the same origin (`/graph/` behind Caddy) ignores it. The owner wants the graph page to follow that choice (questionnaire, recommended option); no switch of its own in the frame.

**Changed (protected):**
- `tests/acceptance/test_graph_view_browser.py`: new check TC-GA-040 (helpers `colours`, `choose`): system light with `mia.theme` dark, system dark with light, auto under both schemes and an unknown value (`purple`) show the expected theme, with the colours of a page of that scheme without a choice and equal to the tokens; a choice changed in another page of the same origin re-colours the open page without a reload. TC-GA-034 unchanged (no saved choice). The module docstring names TC-GA-040.

**Changed (not protected), with this amendment's commit:**
- REQ-GA-016 in `specs/mia/nodes/N-5-graph-app/requirements.md`: text, acceptance criterion, Verified by (TC-GA-034, TC-GA-040), History. The Status line is the owner's: Verified → Draft, review, approve again.
- `specs/mia/nodes/N-5-graph-app/test-spec.md`: TC-GA-040 row and scenario.
- `specs/mia/review-log.md`: D-503.

**Not changed:** the tokens, the frame and its layout (D-425), the main app; TR-VIEW-001 to 021 (TC-GA-040 runs under the same browser rules as TC-GA-033 to 039).

**Expected after install:** `<venv python> tests/acceptance/test_graph_view_browser.py`: TC-GA-033 to 039 ok, TC-GA-040 fails (the page reads no `mia.theme` yet) until the fix on `fix/g-v4-view-theme`. Defect that must make it fail after the fix: "the saved choice ignored" (`graph_app/theme.js` always `auto`).
