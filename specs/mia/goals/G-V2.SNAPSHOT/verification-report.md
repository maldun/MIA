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

## Second round (2026-11-19, fresh reviewer, commits 11e5ef5b, 4fdcc896, 64e956f4, 693a5c48; branch rebased on `goal/v2.snapshot-prod`)

**Verdict for the whole branch: Verified with accepted deviations**, on the condition that F-08 (a failing existing test, one line to fix) is closed before merge. Without that fix the verdict is Not verified, because the full suite has a failure that master does not have.

### Evidence
1. Protected paths and contracts: `git diff --stat $(git merge-base master HEAD) HEAD -- tests/acceptance tests/helpers tests/smoke benchmarks eval contracts` is empty. (A plain diff against master shows `eval/labels/skill_turns.jsonl`, which is only master moving ahead.)
2. Mutations on a copy (tests: test_snapshot_store, test_library_snapshots, IF-203 v2 contract, test_skill_snapshots; baseline green):

| Mutant | Result |
|---|---|
| list sorted by name only | killed (test_snapshot_store) |
| every `ValueError` mapped to invalid/name | killed (test_library_snapshots) |
| up-front `_check_items` call dropped | killed (both) |
| item check never raises | killed |
| transform without trust/lifecycle not checked | killed |
| failing rollback step replaces the original error | killed (test_snapshot_store) |
| rollback skipped | killed (contract and TC-WFM tests) |
| no check of `id`/`version` type | **survived** |
| no check of `kind in KINDS` | **survived** |
| no check that `items` is a list | **survived** |

   F-03 and the original-error part of F-04 are really fixed. The F-04 claim "a malformed snapshot changes nothing and costs no automatic snapshot" is proved by code and test only for the missing-trust case; the three survivors are the other malformations (F-09).
3. Owner logic, checked with a script on a real file storage: a text config entry wins even for a name with no account (`ghost` only; Anna and anna are not owners); an entry that is empty, a number, a list, None or True falls back to the first account; the first account is by the time of its first version, ties to the smaller name (codepoint order, so " anna" < "Anna" < "anna"); a later account or a later `set_password` never takes over; with no account and no entry nobody is owner; account names that differ in case or by a space are different accounts and compared exactly (no case or space folding, so no impersonation); a non-string account (None, list, bytes, dict) is never owner and does not raise. The config is read at each call (`cfg.get`), so a runtime change of the dict counts. `first_account` reads the history of every account at each call (and each snapshot call checks the owner): 300 accounts took 6 ms, only a note. REQ-WFM-066 says "the account that creates accounts": accounts are only made by `tools/accounts_cli.py` and `first_account.py` (no API route creates one), so the first account is the same person in practice; the two differ only if the first account was a throwaway, and then `owner_account` is the override. Acceptable, see F-10.
4. Pins: `pins_from_config` returns `{"MP-light": version_light, "MP-full": version}`, the shape of the contract (`{pin id: model}`); missing, empty or non-text entries leave the pin out; no digest and no server call (read). `web_app.py`: `accounts` and `pins_from_config` are imported, `cfg` is defined at line 107 before use at about line 660, `pins=lambda: pins_from_config(cfg)` matches the constructor (a callable is accepted), `python -m py_compile web_app.py` passes. Not verifiable: the real import of `web_app.py` (it starts the service) and a real HTTP call; no route calls the snapshot operations yet. The two config keys exist in `setup_cfg.example.json` (`version`, `version_light`).
5. Re-run (venv mia312): test_owner_account 7, test_model_pins 5, test_library_snapshots 8, test_snapshot_store 7, test_accounts 6, test_accounts_api 30, test_first_account 9, test_record_tables 18, IF-203 v2 16, IF-203 workflow library 8, IF-302 24, test_skill_snapshots 8: all OK. `tests/test_storage_postgres.py`: 43 tests OK (throwaway postgres, no other podman test ran). Whole suite: 2496 tests, 3 failures: the 2 known of test_task_files_browser (also on master) and **a new one**, `test_config.Example.test_every_option_the_code_reads_is_in_the_example` (F-08).
6. Round 1: F-03 and F-04 closed (see 2). F-01, F-02, F-05, F-06, F-07 untouched by these commits and unchanged (F-01 accepted by the owner; F-02 and F-05 low, F-06 and F-07 info). The "owner source for `web_app.py`" open point of round 1 is closed by 4fdcc896/64e956f4; the pins open point by 693a5c48. Still open: no HTTP route calls the snapshot operations.

### New findings
| ID | Severity | Finding | Proposed test |
|---|---|---|---|
| F-08 | medium | Regression: `owner_account` is read by the code (`accounts.py`) but is not in `setup_cfg.example.json` (the implementation log even notes it), so `tests/test_config.py::Example::test_every_option_the_code_reads_is_in_the_example` fails: `{'owner_account': ['accounts.py']}`. Not on master. The commits reported only selected tests green. Fix: add `owner_account` to `setup_cfg.example.json` (empty text means the first account) and describe it in README.md; the existing test is the regression test. | existing test_config test, must be green |
| F-09 | low | Mutants of `_check_items` survive: no test for a stored snapshot with a non-text id, a non-int or bool version, an unknown kind, or `items` that is not a list. Code is right (each raises `Malformed` before the first write), so only the test is thin. | one parametrised test over these four malformations: `Malformed`, state and snapshot names unchanged |
| F-10 | info | Owner is "first account" (one-second time resolution, ties by name, not by creation) while REQ-WFM-066 says "the account that creates accounts". Two accounts made in the same second (a script) can swap the default owner; `owner_account` removes the doubt. A human may want REQ-WFM-066 reworded to name the config entry and the default. | none |
| F-11 | info | `_check_items` does not look at whether an item's id and version exist; such a snapshot is refused only after the "before restore" snapshot was written (then rolled back, the kept snapshot stays as REQ-WFM-064 allows). | none |

### For a human
- Close F-08 (add the option to the example config and README), re-run the full suite, then sign; `merge_gate.py --approved-by` is theirs.
- Decide F-09 (test) and whether to reword REQ-WFM-066 (F-10).
- Later: an HTTP route for snapshots and a real start of `web_app.py` with the two new lines.

## Resolution after round 2 (2026-11-19, written by the implementing agent, NOT by a reviewer)

These fixes came after both review rounds. No reviewer has seen them. The status below is the implementer's claim; closing the findings in the signed report is the owner's decision (or a third review pass).

| Finding | Status | Commit on `goal/v2.snapshot-prod` | Evidence |
|---|---|---|---|
| F-01 | fixed | `eeef2346` | `_put` passes `expected_version=0` for the kind `snapshots`; a second write of the same name is `conflict`, also when two writers pass the name check together. Two tests in `tests/test_library_snapshots.py` (10 tests in the module). |
| F-08 | fixed | `32fc1873`, `42043f16` | `owner_account` in `setup_cfg.example.json` and `deploy/setup_cfg.compose.json` (the second one was found by `tests/test_deploy.py` after the first fix), described in `deploy/README.md`. |
| F-09 | fixed (tests) | `32fc1873` | Seven-shape test of malformed stored snapshots in `tests/test_snapshot_store.py` (8 tests in the module). |

Re-run by the implementer on `eeef2346`: `tests/test_storage_postgres.py` 43 of 43 OK; whole suite 2499 tests, only the 2 known `test_task_files_browser` failures (also on master).

Owner decisions (maldun, 2026-11-19): F-02, F-05, F-06, F-07, F-10, F-11 accepted; F-01, F-03, F-04, F-08, F-09 fixed. The condition of round 2 (close F-08) is met by the implementer's claim above; a reviewer has not confirmed it.
