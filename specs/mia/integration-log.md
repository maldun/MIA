# Integration log: MIA (N-0)

| Step | Node | Amendment | Result | Notes |
|---|---|---|---|---|
| 02 to 04 | N-1, N-4, N-2 real | A-81 (proposed) | steps 02, 03, 04 run and pass in the image; step 05 skips (N-5, FB-02) | One READY entry (`N-1`) wakes all three, because N-3, N-4 and N-2 were already listed. No finding. The TC-MIA tests (44 ids in no table) are still missing and are needed before the last step. Step 04 needs flask (image or venv). |

## TC-MIA checks (2026-11-01, branch v1-tcmia)
- The "44 missing TC-MIA tests" were a table format problem: the 29 rows had `(AC-n)` after the id, so `trace_check.py` did not read them. A-82 removes the suffix (trace errors 91 to 47).
- New: `tests/test_system_inspection.py` (TC-MIA-020: chat page without build step, login notice), 3 tests, 3 mutants killed. The licence, paid packages and web log of AC-20 were already held by `tools/check_free.py`; Python 3.12, Godot and the roles by TC-API-011, TC-CHV-013, TC-API-010.
- `specs/mia/tc-mia-status.md` and `tools/tc_mia_inventory.py`: which tests lie near each root check (inventory, not verification).
- Not done, by decision of the facts: the C rows (stage 4) need eval criteria and pins; the B rows need a root Verify. N-0 step 05 waits for N-5.

## N-5 (2026-11-01, D-177)
N-5 moves to the next iteration. N-0 step_05 stays a skip ("N-5 not integrated yet"): an accepted deviation of G-V1, to be recorded in the goal Verify. Steps 02 to 04 are the last root steps of this goal.
