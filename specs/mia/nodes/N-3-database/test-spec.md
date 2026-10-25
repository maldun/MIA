# Test specification: Database (N-3)

**Requirements:** specs/mia/nodes/N-3-database/requirements.md   **Status:** Draft (Plan for node N-3, 2026-10-25)

The tests of the inner node: the parts N-3.2, N-3.3 and N-3.1 put together, step by step (integration steps 1 to 3, step 0 is the skeleton with all three as mocks). They decide the requirements of the Database that no single part can show, such as "a record of every kind is written and read back" (the Whole-node requirements, decided by step 3). The tests of the parts are in their own test specifications; the interfaces are tested by the contract suites (`test-spec.md` of the root).

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-N3-001 | REQ-DB-001, REQ-DB-017 | Integration | 3 | N-3 complete (step 3): the container started alone and in the stack | the contract suites of IF-102, IF-301 and IF-302 pass against the real parts; the container is healthy | exact |
| TC-N3-002 | REQ-DB-002 | Integration | 3 | a record of each table kind written and read back through the real stack (IF-102 on top of the real IF-301 and IF-302) | every record reads back equal | exact |
| TC-N3-003 | REQ-DB-003 | Integration | 3 | an edit of a workflow, then of a context graph, then reading the former versions | each edit is a new version with author and time; the former versions are unchanged (AC-16) | exact |
| TC-N3-004 | REQ-DB-004 | Integration | 3 | a workflow with each broken rule written through the real stack (TB-edit) | refused with the rule named; the table and its versions are unchanged | exact |
| TC-N3-005 | REQ-DB-005 | Integration | 3 | two accounts with the same password in the real database; a text search of the dump | no plain password; two different hashes | exact |
| TC-N3-006 | REQ-DB-006 | Integration | 3 | a write on one connection watched on a second connection, 20 times | notified every time within 2 s | maximum <= 2 s |
| TC-N3-007 | REQ-DB-007, REQ-DB-008 | Integration | 3 | files to database and back; backup, wipe and restore of the database | identical files; the same records after the restore | exact |
| TC-N3-008 | REQ-DB-009, REQ-DB-018 | Integration | 3 | seed the five example workflows into the real database, export them, seed them again | five entries after the first seed; identical entries after the round trip (AC-9, AC-10) | exact |
| TC-N3-009 | REQ-DB-010 | Integration | 3 | ten run results stored through the real stack | each carries workflow version, model pin and benchmark version; a result without one is refused (AC-10) | exact |
| TC-N3-010 | REQ-DB-011 | Integration | 3 | a context graph for the workflow lookup and one for the chat, each edited twice | exactly one record per key; each edit is a new version (AC-10) | exact |
| TC-N3-011 | REQ-DB-012, REQ-DB-013, REQ-DB-014, REQ-DB-015 | Integration | 3 | 100 scripted votes in the four categories; a memory record stored and deleted; 50 tasks and memos with odd characters; an edited trust value and a restart of the container | all votes read back complete (user, time, subject, category, value); the deleted record is gone; 50 of 50 items identical; the trust value survives the restart | exact |
| TC-N3-012 | REQ-DB-016 | Integration | 3 | a connection attempt from the host LAN address | refused | exact |

## Assumptions (checked in validation)

- ASM-N3-001: podman is installed on the development host and can pull `postgres:16`; the PostgreSQL tests are skipped, never weakened, where it is not.
- ASM-N3-002: the standard library has `hashlib.scrypt`; no new dependency is needed for the password hash.
- ASM-N3-003: the PostgreSQL driver is `psycopg` 3, kept in `requirements-db.txt` and imported only when the storage is `postgres` (design of `deploy/REQUIREMENTS_DB.md`); approved by the owner on 2026-10-25 (D-54).
