# A-94: remove the doubles of the A-92 install (G-V2.STORE, F-04)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a94.sh` is not yet run with `--do` in the repository. Separate from A-93 (either order works, both ways tested).

## Finding
Verify finding F-04: `tools/apply_amendment_a92.sh --do` was run twice and the second run duplicated four places. The note said "running it twice changes nothing".

**Cause:** `once()` in the script tested the anchor first (`text.count(old) == 1`) and the "done" test second. Most `new` texts still contain `old`, so the anchor was still found once and the edit was applied again. Fixed in `tools/apply_amendment_a92.sh` by testing "done" first; A-93 and A-94 are written that way.

## What A-94 changes (no requirement, check or interface changes; only the doubles go)
| File | Change |
|---|---|
| N-3.2 `test-spec.md` | the second scenario TC-GTB-022 goes (`trace_check` error "scenario defined 2 times") |
| `goals/G-V2.STORE/goal.md` | the second scope row REQ-GTB-021 goes |
| `tests/acceptance/contract/test_if_301_v2_graph_tables.py` | the second `test_a_record_under_another_id_is_refused` goes (Python kept the second, 16 cases ran instead of 17) |
| `tests/helpers/mocks/if_301_graph_tables_v2.py` | the second `if record_id ...` block of `_check` goes |
| N-3.2 `requirements.md` | one addition beyond the doubles: REQ-GTB-021 is listed in the group HD (`req_lint` L0-GROUP warning: the table of groups forgot it). Drop this line of the script if you want A-94 to be only the doubles |

The script keeps the first copy, removes the later ones, refuses when a block is missing, and after `--do` runs the check F-04 asked for: an `ast` scan that no test method is defined twice in a class of the three amendment-touched test files, then `trace_check` and the checks of the cleaned files.

## Checked by the drafter (scratch copies; nothing installed in the repository)
- From the repository state: `--do` twice, second run changes nothing; `trace_check` 517 errors (was 518: the new "scenario defined 2 times" is gone, the 517 known stay); contract suite mock side, `test_graph_record_identity.py`, `test_graph_records.py` OK; the duplicate-method scan finds none.
- A-93 then A-94 and A-94 then A-93 give byte-identical files.
- The fixed `apply_amendment_a92.sh` run from the A-92 draft commit (`c2876b2`) twice: identical results, no GTB error in `trace_check`.
- Case count: the doubled method is a definition, not a case. Python already ran the 16 distinct cases (32 runs on mock and real); A-94 does not change that number, A-93 adds one case (34 runs). So A-94 changes no result of the suite, it only makes the file say what runs.

## Install
```
bash tools/apply_amendment_a94.sh --report     # look only
bash tools/apply_amendment_a94.sh --do         # then commit "plan: A-94 installed"
```
Review-log items that change: `goal.md` (G-V2.STORE) and REQ-GTB group list; test files are protected and only touched by this script.
