# High-Level Specification: G-V4.GRAPHSTORE.CORE – one stored truth for graphs

**Status:** Draft (step 1 of the Plan of this subgoal; nothing here is approved until the owner has gone through it item by item)
**Top-level spec:** `../G-V4.GRAPHSTORE/top-level-spec.md` (items FR-57, FR-60, NFR-16 are this subgoal's; FR-40 and FR-30 of the product spec, partly)   **Owner:** Stefan Reiterer   **Date:** 2026-11-21
**Basis:** the validated prototype round 02 (`../G-V4/prototype/`, branch `prototype/g-v4`), the reuse map decision R1 `keep+tests` (D-400), the accepted cases AC-001 to AC-003 (`../G-V4/accepted-cases.md`).

## 1. Big parts and technology
CORE changes three existing parts and adds none. A graph is stored as one **header record** and one **record per step and per connection**; the header pins the version of every member it uses, so every edit is a new version and an old version stays readable. What is new is who a member belongs to: the ID of a step or connection starts with the ID of its graph (`<graph id>/<local id>`), so two graphs with a step of the same local name no longer share a history.

| Part (node) | Purpose | Technology | New / existing | Decided in |
|---|---|---|---|---|
| N-3.1 Storage layer | writes and reads records with versions, files and PostgreSQL | Python 3.12, one folder of JSON files or PostgreSQL 16 through psycopg 3 | existing, one rule added (a record of the change log is written once, used by REPLAY) | A-92, D-368 |
| N-3.2 Workflows and context graphs | the tables of graphs and the rules a record must keep | record tables `graph_nodes`, `graph_edges`, `context_nodes`, `context_edges`, `graphs`; check function per table | existing, the rule `unscoped_id` added | D-368, prototype R1 |
| N-2.3 Graph model | saves a whole graph, reads a version, lists versions and the history of one step | `GraphModel.save_graph`, `read_graph`, `graph_versions`, `step_history` | existing, saves scoped and writes only what changed | prototype R1 |

### Key decisions and alternatives
| Decision | Alternatives considered | Rationale | Record |
|---|---|---|---|
| Member IDs are scoped by the graph: `<graph id>/<local id>`, the first `/` separates, a graph ID has no `/` | members that are identical stay shared and different ones get their own ID; a separator other than `/` | the first option would change the history of a step when a second graph reuses its name (finding S1); scoped IDs make FR-60 true by construction, and storage already quotes IDs with a slash | D-368, ASM-1 of round 02 |
| A save writes the steps and connections first and the header last | header first; one transaction for all records | the header is what makes a graph visible, so a crash before it leaves unused step versions that no graph names (harmless), never a header that names a missing step; files have no transaction across records | prototype R1, NFR-16 |
| A step or connection is written as a new version only when its content differs; a graph is a new version only when a member changed | write every member at every save | an unchanged save is not an edit (FR-57: "every change a new version"), and the history of a step lists only real changes (FR-60) | ASM-2 of round 02 |
| Context graphs use the same save path with their own member tables | a separate model class | one stored truth for both kinds (FR-57) and one set of checks; the member tables already exist (A-98) | A-98, D-378 |
| A refused save writes nothing | refuse after the members are written | NFR-16: a refused save is not counted as a version; the checks run on the whole graph before the first write | prototype R1 |

## 2. Dependencies
| ID | Kind | What | Pin / version | Why we need it | If it fails or changes | Used by | Update policy | Contract tests (what we rely on) |
|---|---|---|---|---|---|---|---|---|
| DEP-1 | tool | Python | 3.12 (venv `/home/maldun/prog/Python/venvs/mia312`) | runs the storage and the model | the system Python is 3.14 and lacks psycopg 3; a move to 3.14 needs the driver first | HR-001 to HR-005 | compatible range 3.12 to < 3.15, exact version in the lockfile | the whole test suite on 3.12 |
| DEP-2 | library | psycopg (v3) | as `requirements-db.txt` | the PostgreSQL backend | the database tests skip, the files backend still works; no other driver is planned | HR-005 | compatible range 3.x | IF-102 contract suite on a throw-away database |
| DEP-3 | service | PostgreSQL | 16 (image `postgres:16`, never pulled by the tests) | the live store | none: files are the other backend | HR-005 | exact major version 16 | `tests/test_storage_postgres.py`, `tools/contract_postgres.sh` |
| DEP-4 | data | the 15 converted skill graphs and the sample graphs | commit of the prototype fixtures | the golden examples of the measures | the cases are re-made from the skills | HR-003, HR-004 | exact, changed only with its tests | `proto_checks/make_sample_store.py` becomes `tests/fixtures/` |

No new dependency is added.

## 3. High-level requirements
Hard bounds: **none**. Nothing the owner says depends on how fast a graph is saved; the speed of opening a graph is a viewer outcome (NFR-11 of VIEW). The prototype saved a graph of 54 steps in well under a second on the files backend; no bound is claimed.

### HR-001 – Scoped member IDs
- Kind: rule
- Parent: FR-60
- Text: The system shall refuse a step or connection record whose ID is not of the form `<graph id>/<local id>`, with the rule name `unscoped_id`, and shall refuse a graph header that names a member of another graph.
- Rationale: makes "every step belongs to exactly one graph" true by construction; the first `/` separates, a local ID may contain further slashes, a graph ID does not (ASM-1).
- Depends on: DEP-1
- Status: Draft

### HR-002 – Write order of a save
- Kind: rule
- Parent: NFR-16, FR-57
- Text: The system shall check the whole graph before the first write, write the steps and connections that changed, and write the header last, so that a graph appears only when all its members are stored.
- Rationale: a refused save writes nothing; an interrupted save leaves at most step versions no graph names.
- Depends on: DEP-1
- Status: Draft

### HR-003 – Measure: one stored truth, every change a version (FR-57)
- Kind: measure
- Parent: FR-57
- Text: A graph saved, changed twice, read and listed shall give the newest state, all three versions with account and time, and no version missing, for graphs with data, processing and loop-controlling steps, as workflow graph and as context graph.
- Method: the golden examples AC-001 and AC-003 on the 15 converted skill graphs, the sample graph with a loop-controlling step (`sample.code`) and one context graph (to be added in round 03), run on files and on PostgreSQL.
- Metric: for every example 3 of 3 versions listed with author and time, 0 versions lost, 0 differing bytes between what was saved and what is read; identical result on both backends.
- Rationale: FR-57 is an outcome of the owner, "nothing disappears"; counting versions and comparing what is read with what was saved decides it on real graphs, not on toy cases.
- Reference: Fedora host, Python 3.12, PostgreSQL 16 under podman.
- Detail in: the test requirements of this subgoal (to be written in step 3).
- Status: Draft

### HR-004 – Measure: a step belongs to one graph (FR-60)
- Kind: measure
- Parent: FR-60
- Text: Changing a step in one of two graphs that share its local name shall not add a version to any record of the other graph and shall list only changes of its own graph in the step's history.
- Method: AC-002 on the 15 converted graphs, which hold 13 shared local names (4 of different content).
- Rationale: the converted skills really share local names (13 of 107, 4 with different content), so the owner's case is the normal case, not a corner.
- Metric: 0 new record versions in the other graph; the history of the changed step has exactly the changes made in its graph.
- Reference: as HR-003.
- Detail in: the test requirements of this subgoal.
- Status: Draft

### HR-005 – Measure: no half-stored graph (NFR-16)
- Kind: measure
- Parent: NFR-16
- Text: A save that is refused, or interrupted after any number of writes, shall leave every graph entirely as before or entirely new, shall not count the refused save as a version, and a repeated save shall finish it.
- Method: fault injection at every write position of one save (the position k = 0 up to the last write), for a workflow graph and a context graph, on files and on PostgreSQL (the connection fails at write k); a refused save by a graph with a cycle, a broken rule or an unscoped ID.
- Rationale: an interruption can happen after any write; only trying every position shows that no position leaves a half graph, and the number of writes of one save is small enough to try them all.
- Metric: for every k and every case 0 graphs that are listed with a missing member, 0 counted versions for a refused save, 100 % of repeated saves reach the full graph. Pass only when all k pass; no sampling.
- Reference: as HR-003.
- Detail in: the test requirements of this subgoal.
- Status: Draft

## 4. Split proposal
### Nodes (decomposition)
The existing nodes N-3.1, N-3.2 and N-2.3 stay as they are; CORE adds no node. The interface that changes is **IF-301 v2** (the tables of graphs, with the scoped IDs and the rule `unscoped_id`; the amendment of A-92 / REQ-GTB-021, whose protected tests have to be rewritten) and, only for REPLAY, a write-once record in IF-302.

### Goals and subgoals
| Proposed goal / subgoal | Outcome it delivers | Top-level items | Why this cut | How it is checked |
|---|---|---|---|---|
| CORE (this) | one stored truth, graph-scoped steps, atomic saves, for both graph kinds | FR-57, FR-60, NFR-16 | first of the group, everything else stands on it; a few new requirements among many existing ones (the checker counts 37) | the three measures above, the contract suite IF-301 v2 |
Keep together: the 37 requirements come from the descendants of two or three items and most are verified in G-V1 and G-V2.

## 5. Integration with the existing system
- The prototype changed `graph_tables.py` (rule `unscoped_id`, scoped IDs: lines 159 to 224), `graph_model.py` (`save_graph` line 155, `read_graph` 195, `graph_versions` 208, `step_history` 212), and added two lines to `storage.py` and `record_tables.py` (about +93 lines in existing modules).
- Protected tests that use plain IDs fail with `unscoped_id`: `tests/test_graph_record_checks.py` (34), `tests/acceptance/contract/test_if_301_v2_graph_tables.py` (28), `tests/acceptance/test_graph_records.py` (14). They are rewritten by the amendment of A-92; `test_graph_model.py`, `test_graph_run.py` and `test_graph_tables.py` pass.
- Context graphs: the tables exist (A-98) and `graph_tables.py` checks them, but no model saves one yet; the prototype did not store a context graph.
- The converter and the 15 skill graphs already use the scoped form through `GraphModel` (prototype, round 02).

## 6. Risks and open questions
Decided by the owner in the HLS review of 2026-11-21 (D-402): the separator rule is confirmed, orphan step versions are accepted without a clean-up, a context graph is stored in prototype round 03, no hard bound.

| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| A context graph was never stored by the model | FR-57 for both kinds is untested | **decided:** prototype round 03 stores, reads, lists and changes a context graph with steps of every kind |
| An interrupted save leaves step versions no graph names; they accumulate | storage growth, unused rows | **decided:** accepted for now, no clean-up (`step_history` ignores them); revisited when the amount matters |
| The separator `/` is the first slash (ASM-1) | a graph ID with a slash is refused | **decided:** confirmed (HR-001) |
| The files backend cannot make several records atomic | the order is the only protection | the fault-injection measure (HR-005) proves it for both backends; if PostgreSQL could do better (one transaction), say so in the requirements |
| Rewriting the protected tests of A-92 | amendment effort | one amendment, joint with IF-301 v2 owners, listed in the plan |
| No hard performance bound | none claimed | **decided:** none (owner); a budget, if any, comes with the requirements |
