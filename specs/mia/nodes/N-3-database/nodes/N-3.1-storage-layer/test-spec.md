# Test specification: Storage layer (N-3.1)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/requirements.md   **Status:** Draft (Plan for node N-3.1, 2026-10-25)

Tests of this part alone against the mocks of its neighbours: the file backend runs in the commit stage, the PostgreSQL backend in a throwaway container in the acceptance stage. The interface IF-102 is tested by its contract suite against the mock and the real part and uses IF-301 and IF-302 (as mocks until their nodes are integrated). Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-SLY-001 | REQ-SLY-001, REQ-SLY-012 | Contract (real) | 3 | the contract suite test_if_102_storage.py with the real provider: the PostgreSQL backend in a throwaway container (`postgres:16`, data on tmpfs) | all 7 tests of the suite pass; skipped with the reason "podman not available" where podman is missing | exact |
| TC-SLY-002 | REQ-SLY-002 | Component | 1 | one record of each of the 10 record tables and of workflows and context_graphs, written and read back; file backend (stage 1) and PostgreSQL backend (stage 3) | every record reads back equal (deep equality) on both backends | exact |
| TC-SLY-003 | REQ-SLY-003 | Property | 1 | 500 random sequences (seeds 1 to 500) of put, get(version), history on both backends | versions run 1..n without gap; get(version=k) returns what put number k stored; no earlier version ever changes | 0 failures over 500 seeds |
| TC-SLY-004 | REQ-SLY-004 | Component | 1 | the Storage layer with the mocks of IF-301 and IF-302: a workflow with a cycle, an edge between two data nodes, a vote with category mood, a valid workflow | the three invalid documents are refused with the rule named and nothing is stored (ids and versions unchanged); the valid one is stored as version 1 | exact |
| TC-SLY-005 | REQ-SLY-005 | Component | 1 | create two accounts with the same password; dump the whole store; verify the right and a wrong password | the dump contains neither password; the two hashes differ (salt); the right password verifies, the wrong one does not; the hash function is scrypt or stronger from the standard library | exact |
| TC-SLY-006 | REQ-SLY-006 | Component | 3 | two subscribers on two connections (two threads on the file backend, two database connections on PostgreSQL); a write on the first | the second subscriber is notified once with table, id, version and author; the delay is at most 2 s; after unsubscribe nothing arrives | median of 20 writes <= 2 s, maximum <= 2 s |
| TC-SLY-007 | REQ-SLY-007 | Component | 3 | the recorded data folder of the repository (fixtures) moved to the database and back with `python -m MIA.migrate files-to-db` and `db-to-files` | the folder after the round trip is identical file by file (byte for byte after canonical JSON); each direction is one command | exact |
| TC-SLY-008 | REQ-SLY-008 | Component | 3 | a database with 50 records; the backup command; the database wiped; the restore command | the same 50 records with all versions; the backup also contains the other data of MIA (the data folder) | exact |
| TC-SLY-009 | REQ-SLY-009 | Component | 2 | the seed entries exported to files, then seeded into an empty library | the library holds identical entries (id, versions, documents) | exact |
| TC-SLY-010 | REQ-SLY-010 | System | 3 | the stack with the database; a connection attempt from the host LAN address and from a container outside the stack network | both are refused; a connection from a container of the stack succeeds | exact |
| TC-SLY-011 | REQ-SLY-011 | System | 3 | the container started alone with the configuration file, then by the compose stack with the same file | healthy in both cases; the same tables exist | exact |

Contract test cases of IF-102: TC-IF-102-01 to the last of the suite (listed in the root `test-spec.md`).

## Assumptions (checked in validation)

- ASM-N3-001: podman is installed on the development host and can pull `postgres:16`; the PostgreSQL tests are skipped, never weakened, where it is not.
- ASM-N3-002: the standard library has `hashlib.scrypt`; no new dependency is needed for the password hash.
- ASM-N3-003: the PostgreSQL driver is `psycopg` 3, kept in `requirements-db.txt` and imported only when the storage is `postgres` (design of `deploy/REQUIREMENTS_DB.md`); approved by the owner on 2026-10-25 (D-54).
