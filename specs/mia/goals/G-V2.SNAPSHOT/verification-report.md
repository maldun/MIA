# Verification report G-V2.SNAPSHOT (T-SN-01, REQ-WFM-061 to 066)

Reviewer: fresh Verify session (Sonnet 5.5), branch `verify/g-v2-snapshot` from `goal/v2.snapshot-prod` (b660b282, base ab8e8f4f). Date 2026-11-19.

## Verdict proposal: Verified with accepted deviations

All six requirements are covered by green tests that kill the relevant mutants. No high finding. Three medium/low gaps (F-01 to F-03) are cheap to close; none blocks the merge.

## 1. Protected files
`git diff $(merge-base master HEAD) HEAD` over `tests/acceptance`, `tests/helpers`, `tests/smoke`, `benchmarks`, `contracts`, `eval`: empty. Changed files are only `record_tables.py`, `workflow_library.py`, `tests/test_library_snapshots.py`, `tests/test_record_tables.py` and the log. No `.sysml` changed (model checks not needed). (`git diff master..HEAD` shows more only because master moved on with G-V3.CHAT.) The pre-existing patches of the protected suites came with the earlier merged commits and are not in this diff.

## 2. Re-run in the clean worktree (venv mia312)
| Check | Result |
|---|---|
| `test_skill_snapshots` (TC-WFM-061 to 066) | 8 of 8 |
| `test_if_203_v2_snapshots` (TC-IF-203-10 to 17, mock and real) | 16 of 16 |
| `test_if_302_record_tables` (TC-IF-302-11, 12) | 24 of 24 |
| `test_library_snapshots`, `test_snapshot_store`, `test_record_tables` | 6, 3, 18 green |
| `test_storage_postgres` (throwaway postgres:16) | 43 of 43 |
| full `unittest discover -s tests` | see section 2a |
| `trace_check.py` | no finding for REQ-WFM-061 to 066 (only unrelated TD and TR warnings) |

2a. Full suite: 2478 tests, 2 failures (both in `test_task_files_browser`), 4 skipped, 2 expected failures.
The two failures of `tests/test_task_files_browser.py` (files list drawn, files tab offers no delete) also fail on master ab8e8f4f (checked on a `git archive` copy): not caused by this branch.

## 3. Verification matrix
| Req | Test (acceptance, in-memory lab) | Test (real library, contract + own) | Code |
|---|---|---|---|
| 061 take | TC-WFM-061 | TC-IF-203-12 real; TC-IF-302-12 | `snapshot_store._items/_write`, `record_tables` snapshots |
| 062 list | TC-WFM-062 | TC-IF-203-13 real | `list_snapshots` |
| 063 keeps former state | TC-WFM-063 | TC-IF-203-14 real | `restore_snapshot` (kept name, suffix) |
| 064 version, trust, lifecycle | TC-WFM-064 | TC-IF-203-10/11/16 real, `test_library_pointer` | `set_current_version`, set_trust/set_lifecycle with evidence |
| 065 deletes nothing | TC-WFM-065 | TC-IF-203-10, 16 real | pointer move only; no delete path |
| 066 owner only | TC-WFM-066 | TC-IF-203-15 real, `test_library_snapshots` (no `is_owner` means forbidden) | `_owner_only` |
Rollback (IF-203 v2 text, not a REQ): TC-IF-203-17 real with the seam, `test_the_seam_fires_once...`.

## 4. Code against specification
Spec to code: all met. Error mapping Conflict to `conflict`, Refused to `forbidden`, NotFound to `not_found`, empty name to `invalid/schema`; missing version in `set_current_version` passes through as `WorkflowLibraryError`. Automatic name with suffix ` (2)`, ` (3)` correct (mutants on start and format die). Trust/lifecycle written back with evidence `restore of <name>` (mutants die). Table `snapshots` validated (name, items list, pins mapping; other fields kept; not deletable; required fields); mutants die.
`snapshots` is not in `KINDS`; `graph_api.answer` refuses any kind not in `KINDS` (`unknown_kind` 404), so it is unreachable from IF-104. `web_app.py` builds the library without `is_owner`: no endpoint calls the snapshot methods yet, and without `is_owner` all are `forbidden` (safe default; a later task must wire the owner).
Code to spec (behaviour no requirement states): `list_snapshots` is owner only (REQ-WFM-066 names take and restore only; IF-203 v2 and TC-IF-203-15 state it, so the contract covers it: info, F-06). The test seam `fail_set_current_version_at` lives in production code (contract needs it, TC-IF-203-17).
Documented race: `expected_version` is compared with the current version, then `put` runs without it; a concurrent writer in between is missed. Confirmed in code (`_put`); accepted in the log, single-user file backend.

## 5. Mutations (on a copy; 32 mutants)
29 killed, 3 survivors. Killed among others: owner check dropped in snapshot, restore and list; suffix dropped or off by one; rollback skipped; error swallowed after rollback; evidence missing or wrong; trust or lifecycle write-back dropped; kept snapshot written after the restore or with another author; conflict, not_found checks; pins; list fields; every error mapping; default owner True; kind `snapshots` removed; seam not once; table validation of name, items, pins; table deletable; required fields; `expected_version` against newest instead of current.
Survivors:
- M1 `list_snapshots` sorted by name only instead of (time, name): no test takes a later-named snapshot first (F-03).
- M2 rollback in forward instead of reverse order: equivalent today (each item appears once), no finding.
- M3 `_restore_moves` not reset after a restore: the seam counter then keeps counting outside a restore; only matters with the seam set (F-05).

## 6. Findings
| Id | Sev | Finding and evidence | Proposed test |
|---|---|---|---|
| F-01 | medium | Two snapshots with the same name taken concurrently both pass the `list_ids` check in `_write`; the second `library.save("snapshots", ...)` becomes version 2 and the pointer moves to it, so a "written once" record is replaced (same shape of race as the documented one, but for snapshot names and for the kept name of a restore). Single-user, so accepted-deviation candidate. | A two-thread test with a barrier between check and put on a real Storage; expect one `conflict`. Or fix: `expected_version=0`-style check inside `_write`. |
| F-02 | low | Rollback does not restore everything of a transform meta: the restore writes `evidence="restore of <name>"`, `_put_back` calls `set_lifecycle` without evidence and `set_meta` copies the old dict, so the evidence and `changed_by` of an already changed transform stay after a failed restore. Trust, lifecycle and version are back (what the contract names). Code: `snapshot_store._put_back`. | After an injected failure assert `get_meta` equals the meta before the restore (except new versions). |
| F-03 | low | M1 above: oldest-first order is only tested with names in the time order. | list with "b" taken before "a": expect ["b", "a"]; also equal times. |
| F-04 | low | `_snapshot_call` maps every `ValueError` to `invalid/schema/name`, and a malformed stored snapshot (item without `trust`, KeyError) escapes unmapped after rollback; if a `_put_back` step itself fails during rollback the original error is replaced by the new one. The table checks `items` by type only. | Restore a hand-written snapshot with a transform item without `trust`: expect a defined error and unchanged state. |
| F-05 | low | Seam state `_restore_moves` is shared instance state (not thread safe, not reset in the survivor mutant); production code carries a test hook. | A test that moves the pointer after a restore with the seam set and expects no failure. |
| F-06 | info | `library.read/save/list_ids/history/set_current_version("snapshots", ...)` accept the internal kind for any caller holding the library, without an owner check (Toolbox uses only transforms; graph_api cannot reach it). A future caller must not pass user input as kind. | none |
| F-07 | info | `test_skill_snapshots` (TC-WFM-061 to 066) runs on the in-memory lab; the real library is covered by the real variants of the contract suite and `tests/test_library_snapshots.py`. Restore writes a new meta version for a transform even if trust and lifecycle are unchanged (noise only). | none |

## 7. Not done / for a human
- Quality characteristics, usability and static checks (ruff, bandit) were not run (no new tools configured; no UI or user input surface in this change).
- A human decides F-01 and F-04 (accept or fix) and signs the report; `merge_gate.py --approved-by` is theirs. The owner source (`is_owner`) for `web_app.py` and any endpoint for snapshots are future work.
