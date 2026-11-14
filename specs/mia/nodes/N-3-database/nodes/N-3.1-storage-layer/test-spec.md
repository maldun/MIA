# Test specification: Storage layer (N-3.1)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/requirements.md   **Status:** Draft (Plan for node N-3.1, 2026-10-25)

Tests of this part alone against the mocks of its neighbours: the file backend runs in the commit stage, the PostgreSQL backend in a throwaway container in the acceptance stage. The interface IF-102 is tested by its contract suite against the mock and the real part and uses IF-301 and IF-302 (as mocks until their nodes are integrated). Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-SLY-001 | REQ-SLY-001, REQ-SLY-012 | Contract (real) | 3 | the contract suite test_if_102_storage.py with the real provider: the PostgreSQL backend in a throwaway container (`postgres:16`, data on tmpfs; stage-3 step `contract-postgres`, A-59) | every test of the suite passes; the step fails, never skips, where podman, the local image or psycopg is missing | exact |
| TC-SLY-002 | REQ-SLY-002 | Component | 1 | one record of each of the 10 record tables and of workflows and context_graphs, written and read back; file backend (stage 1) and PostgreSQL backend (stage 3) | every record reads back equal (deep equality) on both backends | exact |
| TC-SLY-003 | REQ-SLY-003 | Property | 1 | 500 random sequences (seeds 1 to 500) of put, get(version), history on both backends | versions run 1..n without gap; get(version=k) returns what put number k stored; no earlier version ever changes | 0 failures over 500 seeds |
| TC-SLY-004 | REQ-SLY-004 | Component | 1 | the Storage layer with the mocks of IF-301 and IF-302: a workflow with a cycle, an edge between two data nodes, a vote with category mood, a valid workflow | the three invalid documents are refused with the rule named and nothing is stored (ids and versions unchanged); the valid one is stored as version 1 | exact |
| TC-SLY-005 | REQ-SLY-005 | Component | 1 | create two accounts with the same password; dump the whole store; verify the right and a wrong password | the dump contains neither password; the two hashes differ (salt); the right password verifies, the wrong one does not; the hash function is scrypt or stronger from the standard library | exact |
| TC-SLY-006 | REQ-SLY-006 | Component | 3 | two subscribers on two connections (two threads on the file backend, two database connections on PostgreSQL); a write on the first | the second subscriber is notified once with table, id, version and author; the delay is at most 2 s; after unsubscribe nothing arrives | median of 20 writes <= 2 s, maximum <= 2 s |
| TC-SLY-007 | REQ-SLY-007 | Component | 3 | a data folder in the Storage layer's own record format (workflows with two versions, a memo with a slash in its id and non-ASCII text, an account) moved to the database and back with `python -m MIA.migrate files-to-db` and `db-to-files`; the legacy stores and their importers are out of G-V1 (D-158, FB-04) | the folder after the round trip is identical file by file (byte for byte after canonical JSON); each direction is one command | exact |
| TC-SLY-008 | REQ-SLY-008 | Component | 3 | a database with 50 records; the backup command; the database wiped; the restore command | the same 50 records with all versions; the backup also contains the other data of MIA (the data folder) | exact |
| TC-SLY-009 | REQ-SLY-009 | Component | 2 | the seed entries exported to files, then seeded into an empty library | the library holds identical entries (id, versions, documents) | exact |
| TC-SLY-010 | REQ-SLY-010 | System | 3 | the stack with the database; a connection attempt from the host LAN address and from a container outside the stack network | both are refused; a connection from a container of the stack succeeds | exact |
| TC-SLY-011 | REQ-SLY-011 | System | 3 | the container started alone with the configuration file, then by the compose stack with the same file | healthy in both cases; the same tables exist | exact |
| TC-SLY-012 | REQ-SLY-013 | Component | 1 | a document nested 200, 201, 600 and 990 levels, for `graph_nodes` and for another table | the 200-level one is stored as version 1; the others are refused as invalid and nothing is stored | exact |
| TC-SLY-013 | REQ-SLY-014 | Component | 1 | a list that contains itself, a dict that contains itself twice, as the value of a graph node and as a document of another table | each is refused as invalid within one second and nothing is stored | exact, 1 s |
| TC-SLY-014 | REQ-SLY-015 | Component | 1 | a task document {"text": "t", "numbers": [...]} with 99,997 and with 99,998 numbers (100,000 and 100,001 values: the document, the text and the list count 3), the same as the value of a graph node (99,995 and 99,996 numbers); a document that names the same child twice on 30 levels | the 100,000-value document is stored; the others are refused as invalid and nothing is stored, the last within one second | exact, 1 s |

Contract test cases of IF-102: TC-IF-102-01 to the last of the suite (listed in the root `test-spec.md`).

## Scenarios

### TC-SLY-001 – IF-102 on PostgreSQL
- Verifies: REQ-SLY-001, REQ-SLY-012
- Given: a throwaway `postgres:16` container with its data on tmpfs, and `MIA_TEST_DATABASE_URL` pointing at it
- When: the real side of the IF-102 contract suite runs (`tools/contract_postgres.sh`)
- Then: every test passes and none is skipped

### TC-SLY-002 – every table holds its records
- Verifies: REQ-SLY-002
- Given: an empty store on the file backend, and one on PostgreSQL
- When: one record of each table is written and read back
- Then: each record reads back equal, as version 1 with its author and id

### TC-SLY-003 – versions never change
- Verifies: REQ-SLY-003
- Given: 500 random sequences of put, get(version) and history (seeds 1 to 500) on each backend
- When: each sequence runs
- Then: versions run 1..n without a gap, get(version=k) returns what put number k stored, and no earlier version changes (0 failures)

### TC-SLY-004 – validation on write
- Verifies: REQ-SLY-004
- Given: a workflow with a cycle, a context graph with two adjacent data nodes, a vote of category `mood` and a valid workflow
- When: each is put
- Then: the three invalid ones are refused with their rule and nothing is stored; the valid one is version 1

### TC-SLY-005 – accounts keep no password
- Verifies: REQ-SLY-005
- Given: two accounts with the same password
- When: the whole store is dumped and both passwords are verified, the right one and a wrong one
- Then: the dump holds neither password, the hashes differ, the right password verifies and the wrong one does not

### TC-SLY-006 – change notices
- Verifies: REQ-SLY-006
- Given: a subscriber on a second thread (files) or a second database connection (PostgreSQL)
- When: 20 writes are made on the first
- Then: each is heard once with table, id, version and author, median and maximum delay at most 2 s; after unsubscribe nothing arrives

### TC-SLY-007 – reversible move from files
- Verifies: REQ-SLY-007
- Given: a data folder in the Storage layer's own record format (D-158: the legacy stores are out of G-V1)
- When: it is moved to the database with `migrate files-to-db` and back into an empty folder with `migrate db-to-files`
- Then: the two folders are identical file by file in canonical JSON

### TC-SLY-008 – backup and restore
- Verifies: REQ-SLY-008
- Given: a database with 50 records and extra versions, and a data folder
- When: `tools/backup.sh` runs, both are wiped and `tools/restore.sh` runs
- Then: the same rows and files come back, and the state before the restore is kept as a safety copy

### TC-SLY-009 – library export and seed
- Verifies: REQ-SLY-009
- Given: a library of workflows and context graphs with several versions
- When: it is exported to a folder and seeded into an empty library
- Then: ids, versions, authors, times and documents are identical

### TC-SLY-010 – reachable only in the stack
- Verifies: REQ-SLY-010
- Given: the stack with the database service
- When: a connection is tried from the host's LAN address, from a container outside the stack network and from a container of the stack
- Then: the first two are refused, the last one connects

### TC-SLY-011 – its own container
- Verifies: REQ-SLY-011
- Given: the database configuration file
- When: the container is started alone, then by the compose stack
- Then: it is healthy both times and has the same tables

### TC-SLY-012 – depth of a document
- Verifies: REQ-SLY-013
- Given: a document nested 200 levels (the document is level 1) and others nested 201, 600 and 990 levels, once as the value of a graph node and once as a document of a table that is not a graph table
- When: each is put
- Then: the 200-level document is stored as version 1; the others are refused as invalid
- And: the refusals store nothing; graph tables name `schema_break` and `data`, other tables `schema` and `nested too deep`; the same on the file backend and on PostgreSQL

### TC-SLY-013 – a document that contains itself
- Verifies: REQ-SLY-014
- Given: a list that contains itself and a dict that contains itself twice, once as the value of a graph node and once as a document of another table
- When: each is put, with a time limit of one second
- Then: each is refused as invalid within the limit
- And: nothing is stored; the same on the file backend and on PostgreSQL

### TC-SLY-014 – size of a document
- Verifies: REQ-SLY-015
- Given: a task document `{"text": "t", "numbers": [...]}` with 99,997 numbers and one with 99,998 numbers (100,000 and 100,001 values: the document, the text and the list count 3; documents of the tables other than graph tables are mappings), a data node whose value is a list of 99,995 and one of 99,996 numbers as records of a graph table, and a document that names the same child twice on 30 levels
- When: each is put, with a time limit of one second
- Then: the documents with 100,000 values are stored as version 1; the ones with 100,001 values are refused as invalid
- And: the 2**30-path document is refused within the limit; the refusals store nothing; graph tables name `schema_break` and `data`, other tables `schema` and `too large`; the same on the file backend and on PostgreSQL

## Assumptions (checked in validation)

- ASM-N3-001: podman is installed on the development host and can pull `postgres:16`; the PostgreSQL tests are skipped, never weakened, where it is not.
- ASM-N3-002: the standard library has `hashlib.scrypt`; no new dependency is needed for the password hash.
- ASM-N3-003: the PostgreSQL driver is `psycopg` 3, kept in `requirements-db.txt` and imported only when the storage is `postgres` (design of `deploy/REQUIREMENTS_DB.md`); approved by the owner on 2026-10-25 (D-54).
