# A-177 – TC-GA-040 tightened and traced (G-V4.VIEW, REQ-GA-016)

**Decided:** D-504, owner, 2026-11-26 (findings F-3 and F-4 of the independent Verify of `fix/g-v4-view-theme`). **Installs:** `bash tools/apply_amendment_a177.sh --do` (the owner runs it), then commit as "plan: A-177 installed".

**Why.** F-3: TC-GA-040 tried an unknown value of `mia.theme` only under the light scheme, so a page that maps every unknown value to light would pass; the acceptance criterion says an unknown value gives the colours of the scheme. F-4: `trace_check.py` reports `TC-GA-040 | no test requirement applies to this check (M41)`.

**Changed (protected):**
- `tests/acceptance/test_graph_view_browser.py`: TC-GA-040 also tries `purple` under the dark scheme (expected dark).
- `specs/mia/test-requirements.md`: TC-GA-040 added to the "Applies to" lines of TR-VIEW-002 (fixture graphs), 003 (fresh stores and accounts), 008 (Firefox), 009 (one origin), 013 (colours against the token values) and 021 (each new check shown able to fail), the test requirements that apply to TC-GA-034.

**Not changed:** REQ-GA-016 (A-176); the goal's copy `specs/mia/goals/G-V4.VIEW/test-requirements.md` (history; the root file is the source since the merge).

**Expected after install:** `<venv python> tests/acceptance/test_graph_view_browser.py` 8/8 on the fixed branch; `trace_check.py` without the TC-GA-040 line. Defect that must make the new case fail: unknown values mapped to light.
