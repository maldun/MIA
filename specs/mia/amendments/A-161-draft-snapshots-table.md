# A-161 draft: the table `snapshots` (IF-302 v14, IF-102 v8, IF-203 v3), and what follows for G-V2.SNAPSHOT

Status: **draft, not applied**; owner decisions in the session of 2026-11-18 (answers to the T-SN-01 questionnaire): a new table `snapshots` with a contract bump; the suite documents valid for both providers; `is_owner` and `pins` injected into the real library. The number A-161 is the next free one after A-160 at the time of writing: check before applying.

Why: the real Storage answers `unknown_table` for the snapshot records of IF-203 v2; IF-302 v13 and IF-301 v2 define no such table (T-SN-01, `specs/mia/goals/G-V2.SNAPSHOT/implementation-log.md`).

## 1. Contract text: `A-161-contract-edits.patch` (checked with `git apply --check` against master `2c4b0915`)
- IF-302 v14: table `snapshots`, versioned, not deletable; required `name` (non-empty text), `time`, `author`, `items` (list), `pins` (mapping); other fields kept, never refused (`format`, `note` known); record id = the snapshot name; written once, `conflict` for an existing name is the library's check.
- IF-102 v8: the table list names `snapshots`; no new operation.
- IF-203 v3: names the place of the snapshot record; no operation, error or example changes.

## 2. Review-log row (append after applying; D-number to take at that moment, D-348 if still free)
| D-348 | **A-161 installed, G-V2.SNAPSHOT, <date>.** `contracts/IF-302-record-tables.md` v14 has the table `snapshots` (REQ-WFM-061), `contracts/IF-102-storage-interface.md` v8 names it, `contracts/IF-203-workflow-library.md` v3 names the place of the snapshot record. Owner decision 2026-11-18 (questionnaire of T-SN-01). Not part of this step: the IF-302 mock and the TC-IF-302 checks for the table, the suite documents and the adapter of IF-203 v2 (protected), the production code. |

## 3. What follows, in this order
1. Apply 1 and 2 (parent session, one commit apart from other work; stage by path).
2. Protected patch (owner applies): the IF-302 mock and a TC-IF-302-12 for `snapshots`; the documents of `tests/acceptance/contract/test_if_203_v2_snapshots.py` made valid for the real graph and record rules and the mock alike; the adapter in `tests/helpers/contract.py` passes `is_owner` (the accounts check) and `pins` (`eval-spec.md`) to the real library and exposes the failure seam of TC-IF-203-17.
3. Production (fork): `record_tables.py` (table `snapshots`), the real library of IF-203 v2 takes `is_owner` and `pins` as constructor arguments and writes `snapshots`; the real variants of TC-IF-203-10 to 17 and TC-IF-302-12 go green.
4. Known risk to log: the library checks `expected_version` against the current version first and then puts without it; a concurrent writer between the two steps is missed (T-SN-01 log).
