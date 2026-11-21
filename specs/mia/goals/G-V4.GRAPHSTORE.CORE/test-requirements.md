# Test requirements: G-V4.GRAPHSTORE.CORE

**Test spec:** `test-spec.md`   **Status:** Draft (for the owner's review, step 3 of the Plan of this subgoal)

<!-- Requirements on the checks, apart from the product requirements: under which conditions a measurement counts. Setup kind: the verdict depends on the setup; written out and reviewed in detail. Unit kind: exact expected values; grouped and signed off as a group. -->

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | FI | Fault injection: what makes the interruption checks credible | TR-CORE-001, TR-CORE-002 |
| 2 | BK | Backends and data: the stores and the graphs the checks run on | TR-CORE-003, TR-CORE-004, TR-CORE-009 |
| 3 | EX | Exact values: expected names, IDs and counts, signed off as a group | TR-CORE-005, TR-CORE-007, TR-CORE-008 |
| 4 | CR | Ability to fail: the checks are shown able to fail | TR-CORE-006 |

### TR-CORE-001 – Every write position is tried
- Applies to: TC-WFM-147, TC-WFM-151
- Requirement: REQ-WFM-147
- Group: FI
- Kind: setup
- Text: The check shall interrupt the save after every single write of that save, one run per write position, and shall fail when any one position fails.
- Rationale: HR-005 says "all k, no sampling": a save of a graph of five steps and four connections has ten writes, a context graph of three steps and two connections six, a changed save two to four; trying every position is cheap and the only way to show that no position leaves a half graph.
- Credibility aspect: power and false-alarm rate
- Verified by: mutation (the header written first must fail the check)
- Status: Approved

### TR-CORE-002 – The injector is shown to fire
- Applies to: TC-WFM-147, TC-WFM-151
- Requirement: REQ-WFM-147
- Group: FI
- Kind: setup
- Text: The failing store shall raise at the k-th write on the files backend and on the PostgreSQL connection alike, and the check shall show that it did raise by comparing the counted writes with the expected number of writes of that save.
- Rationale: a fault injector that never fires would let every position pass; the counted writes (ten, six, and the smaller numbers of a changed save) are the known answer that proves the injector fired at every k.
- Credibility aspect: stand-in fidelity
- Verified by: known answer (the write counts of the four saves)
- Status: Approved

### TR-CORE-003 – Both backends, skips visible
- Applies to: TC-GTB-032, TC-WFM-147, TC-WFM-151, TC-WFM-159, SMOKE-CORE-001
- Requirement: REQ-GTB-032
- Group: BK
- Kind: setup
- Text: The check shall run on the files backend and on PostgreSQL 16 started as a throw-away container named by the test, and shall report a half that cannot run as skipped, never as passed.
- Rationale: the same behaviour on both backends is the point of FR-57 and HR-003; the prototype ran on both (round 03); skipping must be visible so a missing podman is not read as success (CLAUDE.md: PostgreSQL tests skip, never weaken).
- Credibility aspect: measurement conditions
- Verified by: inspection of the test report
- Status: Approved

### TR-CORE-004 – Golden examples from the fixtures
- Applies to: TC-WFM-145, TC-WFM-148, TC-WFM-149, TC-WFM-158, TC-WFM-159
- Requirement: REQ-WFM-145
- Group: BK
- Kind: setup
- Text: The checks shall use the 15 converted skill graphs, the sample graph with a loop-controlling step and the context graph of the fixtures under `tests/fixtures/`, unchanged and with the content they have in the repository.
- Rationale: these graphs are the golden examples of HR-003 and HR-004: 13 of the 107 local step names are shared between graphs, 4 with different content, so the owner's case is the normal case.
- Credibility aspect: reference accuracy
- Verified by: inspection of the fixture list and the shared-name count
- Status: Approved

### TR-CORE-005 – Exact values
- Applies to: TC-GTB-029, TC-GTB-030, TC-GTB-031, TC-WFM-144, TC-WFM-146, TC-WFM-150, TC-WFM-152, TC-WFM-153, TC-WFM-154, TC-WFM-155, TC-WFM-156, TC-WFM-157, TC-WFM-160
- Requirement: REQ-GTB-029
- Group: EX
- Kind: unit
- Text: The expected values of these checks shall be written as exact values: rule names, field names, record IDs, kinds and counts, with no tolerance.
- Rationale: every outcome here is a name, an ID, a count or an equality (test-spec, limit column), so any tolerance would hide a defect.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Sign-off: skimmed as a group
- Status: Approved

### TR-CORE-006 – Each check is shown able to fail
- Applies to: TC-WFM-145, TC-WFM-146, TC-WFM-147, TC-WFM-148, TC-WFM-149, TC-WFM-150, TC-WFM-151
- Requirement: REQ-WFM-146
- Group: CR
- Kind: setup
- Text: Each of these checks shall be shown able to fail, by running it once against a deliberate defect of the unit it checks, before the check is trusted.
- Rationale: a test written against existing code tends to confirm it (the code of CORE is the kept prototype, reuse map R1); the defects: header written first, every member written at each save, no check before the first write, step history read from the record instead of the header.
- Credibility aspect: reviewer independence
- Verified by: mutation
- Status: Approved

### TR-CORE-007 – Fresh IDs and stores
- Applies to: TC-GTB-029, TC-GTB-030, TC-WFM-144, TC-WFM-145, TC-WFM-148, TC-WFM-149, TC-WFM-152, TC-WFM-160
- Requirement: REQ-GTB-029
- Group: EX
- Kind: unit
- Text: Each check shall use graph IDs of its own and a store that no other check has written to.
- Rationale: a check that finds records of an earlier check would pass or fail for the wrong reason; fresh stores are cheap on files and use a new database per run on PostgreSQL.
- Credibility aspect: measurement conditions
- Verified by: review
- Sign-off: skimmed as a group
- Status: Approved

### TR-CORE-008 – Times are not compared exactly
- Applies to: TC-WFM-158, TC-WFM-159
- Requirement: REQ-WFM-158
- Group: EX
- Kind: unit
- Text: The checks shall compare the time of a version only for being present and for not decreasing, never for an exact value.
- Rationale: the time is the clock of the store; exact values would make the checks flaky and say nothing about the requirement.
- Credibility aspect: measurement conditions
- Verified by: review
- Sign-off: skimmed as a group
- Status: Approved

### TR-CORE-009 – The smoke check never writes live data
- Applies to: SMOKE-CORE-001
- Requirement: REQ-WFM-158
- Group: BK
- Kind: setup
- Text: The smoke check shall write only throw-away graph IDs, to a new files directory and to a new database `mia_smoke` on the owner's running PostgreSQL server, drop both by name afterwards, and never write to MIA's own database or files store.
- Rationale: the check runs on the owner's host (Deploy) and proves that the running server works (owner's choice, review 2026-11-21); the live data of MIA is not a test fixture.
- Credibility aspect: measurement conditions
- Verified by: inspection
- Status: Approved

