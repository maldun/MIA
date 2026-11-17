# Plan: G-V2.SNAPSHOT

**Requirements:** REQ-WFM-061 to 066 (N-2.3 `requirements.md`)   **Checks:** TC-WFM-061 to 066 (`tests/acceptance/test_skill_snapshots.py`), TC-IF-203-10 to 17 (`tests/acceptance/contract/test_if_203_v2_snapshots.py`), TC-IF-302-11

## Tasks
| Task | Implements | Checks | Depends on |
|---|---|---|---|
| T-SN-01 Snapshots: take, list, restore, nothing deleted, owner only (was T-CV-05): the snapshot store, the real IF-203 v2 provider, the table `current_versions` in the record tables and the storage backends | REQ-WFM-061 to 066 | TC-WFM-061 to 066 on the mocks; the real variants of TC-IF-203-10 to 17 and TC-IF-302-11 | contracts installed (A-121) |

### T-SN-01
- Done when: the six checks pass with the mocks, the real variants of the IF-203 v2 and IF-302 checks pass, the automatic snapshot is named "before restore of <name>" with the owner as author, the existing IF-203, IF-302 and IF-102 suites stay green.
- Must not touch: protected material, `contracts/`.
- Owner decision 2026-11-18: the real provider is part of this task (A-159).
