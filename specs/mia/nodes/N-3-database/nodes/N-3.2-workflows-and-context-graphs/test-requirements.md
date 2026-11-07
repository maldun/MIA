# Test requirements: Graph tables (N-3.2), iteration 2 (G-V2.STORE)

Requirements on the checks TC-GTB-006 to TC-GTB-016. The older checks TC-GTB-001 to TC-GTB-005 have none yet (they predate test requirements, G-V1 decision D-180, F-07); they are not part of G-V2.STORE.

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | Round trip | what is written is what is read, exact values and the stand-in that stores | TR-GTB-001, TR-GTB-002 |
| 2 | Types | schema check and the validator it uses | TR-GTB-003 |
| 3 | Generated graphs | seeds, count and the meaning of equal | TR-GTB-004 |
| 4 | Inspection | what the import check can and cannot see | TR-GTB-005 |
| 5 | Compatibility | the old suites stay the old suites | TR-GTB-006 |

### TR-GTB-001 – Exact values written by hand
- Applies to: TC-GTB-016, TC-GTB-006, TC-GTB-007, TC-GTB-008, TC-GTB-009, TC-GTB-010, TC-GTB-011, TC-GTB-013, TC-GTB-017, TC-GTB-018, TC-GTB-019, TC-GTB-020, TC-GTB-021
- Requirement: REQ-GTB-005
- Group: Round trip
- Kind: unit
- Text: The expected values of each check shall be written into the test by hand and not produced by the code under test.
- Rationale: A round trip that takes its expected value from the same code would pass for any bug that is symmetric in write and read.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Status: Draft

### TR-GTB-002 – The storage under the checks passes IF-102
- Applies to: TC-GTB-016, TC-GTB-006, TC-GTB-013, TC-GTB-014, TC-GTB-018, TC-GTB-019
- Requirement: REQ-GTB-005
- Group: Round trip
- Kind: setup
- Text: The storage used by these checks at stage 1 shall pass the contract suite of IF-102 before the checks run.
- Rationale: whether PostgreSQL keeps JSON and versions faithfully is the job of the database and of IF-102, whose suite already runs on the real postgres:16 at stage 3 (contract-postgres); this subgoal only needs the stand-in to be one that suite accepts. Shortened on the owner's remark, 2026-11-07 (the repeat of four checks on PostgreSQL was dropped).
- Credibility aspect: stand-in fidelity
- Verified by: contract suite
- Status: Draft

### TR-GTB-003 – Schema errors come from the pinned validator
- Applies to: TC-GTB-011, TC-GTB-010
- Requirement: REQ-GTB-011
- Group: Types
- Kind: setup
- Text: The schema check shall use jsonschema in the version of the host (4.23.0 at 2026-11-07), and the path in the message shall be the path of that validator's error.
- Rationale: The expected path in TC-GTB-011 depends on how the validator names it; another version can name it differently.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Status: Draft

### TR-GTB-004 – 1000 generated graphs, seeds 1 to 1000
- Applies to: TC-GTB-014
- Requirement: REQ-GTB-014
- Group: Generated graphs
- Kind: setup
- Text: The check shall run the seeds 1 to N, with N a parameter of the check and 1000 as its default, build graphs with 1 to 20 nodes of all three types and up to 40 edges, compare with the equality of node IDs, types, fields and edge ends, and count any difference as a failure.
- Rationale: the criterion is exact ('equal'), so one counterexample fails it and no rate is needed; the default follows TC-GTB-003. Fixed seeds let a failure be replayed; the owner can raise N (2026-11-07, review), for example when the generator changes. The size bounds and the stage 1 time are a starting guess, measured in Step 4 (D-187).
- Credibility aspect: repetitions and seeds
- Verified by: property test with a deliberately broken writer (mutation)
- Status: Draft

### TR-GTB-005 – The import check can fail
- Applies to: TC-GTB-012
- Requirement: REQ-GTB-012
- Group: Inspection
- Kind: setup
- Text: The inspection shall read the syntax tree of every module of the Graph tables and shall be shown to report a module that imports pickle, marshal or shelve, including inside a function.
- Rationale: An import check that cannot fail proves nothing, and imports inside functions are the common way to miss one. Dynamic imports by name (importlib, __import__) are not seen; this is accepted, the list of three modules is the owner's (2026-11-07).
- Credibility aspect: validity domain
- Verified by: mutation
- Status: Draft

### TR-GTB-006 – The old contract suites are the old ones
- Applies to: TC-GTB-015
- Requirement: REQ-GTB-015
- Group: Compatibility
- Kind: setup
- Text: The check shall run the contract suites of IF-301 v1 and IF-203 v0 from the files as they were before A-90, and shall fail if either file differs from that version.
- Rationale: The point is that the document form is unchanged; a suite edited to pass would hide a break.
- Credibility aspect: reference accuracy
- Verified by: contract suite
- Status: Draft
