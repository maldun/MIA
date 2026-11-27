# Test requirements: G-V4.GRAPHSTORE.TRANSFER

**Test spec:** `test-spec.md`   **Status:** Approved by the owner by group (EX, BK, FI, EP, CR; 2026-11-22, review-log.md)

At the merge these go unchanged into the protected `specs/mia/test-requirements.md` (new section, prefix TR-TRANSFER-), as RULES' did.

<!-- Requirements on the checks, apart from the product requirements: under which conditions a measurement counts. Setup kind: the verdict depends on the setup; written out and reviewed in detail. Unit kind: exact expected values; grouped and signed off as a group. -->

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | EX | Exact values and fresh stores, signed off as a group | TR-TRANSFER-001, TR-TRANSFER-005 |
| 2 | BK | Backends and data: both backends, the sample store, throw-away databases only | TR-TRANSFER-002, TR-TRANSFER-003, TR-TRANSFER-007 |
| 3 | FI | Interruption: every write position, the injector shown to fire, the lock across processes | TR-TRANSFER-004, TR-TRANSFER-006 |
| 4 | EP | Entry points and stand-ins: the backend start and stop, the side tables of VIEW, the path search | TR-TRANSFER-009, TR-TRANSFER-010, TR-TRANSFER-011 |
| 5 | CR | Ability to fail | TR-TRANSFER-008 |

### TR-TRANSFER-001 – Exact values
- Applies to: TC-SLY-016, TC-SLY-017, TC-SLY-018, TC-SLY-019, TC-SLY-020, TC-SLY-021, TC-SLY-022, TC-SLY-023, TC-SLY-024, TC-SLY-025, TC-SLY-026, TC-SLY-027, TC-SLY-040, TC-SLY-030, TC-SLY-031, TC-SLY-032, TC-SLY-033, TC-SLY-034, TC-SLY-035, TC-SLY-039, TC-SLY-009, TC-API-060, TC-API-061, TC-API-062, TC-API-064, TC-API-065, TC-API-066, TC-API-067
- Requirement: REQ-SLY-016
- Group: EX
- Kind: unit
- Text: The expected values of these checks shall be written as exact values: record histories entry by entry, IDs, states, counts, call orders and refusals with rule and detail, with no tolerance and no check by "contains".
- Rationale: every outcome is a history, a name, a count or an equality (test spec, limit column); a move "without loss" is checked entry by entry, so a check by "contains" would hide a lost or changed version.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Sign-off: skimmed as a group
- Status: Approved

### TR-TRANSFER-002 – Both backends, skips visible
- Applies to: TC-SLY-016, TC-SLY-018, TC-SLY-022, TC-SLY-024, TC-SLY-025, TC-SLY-040, TC-SLY-029, TC-SLY-036, TC-SLY-038
- Requirement: REQ-SLY-022
- Group: BK
- Kind: setup
- Text: The check shall run on the files backend and on PostgreSQL 16 started as a throw-away container named by the test, with CORE's `tests/helpers/core_stores.py`, and shall report a half that cannot run as skipped, never as passed.
- Rationale: the same behaviour on both is FR-58 and HR-005; the copy is always files, the live side is both (TR-CORE-003, adopted unchanged in substance); a missing podman must not read as success.
- Credibility aspect: measurement conditions
- Verified by: inspection of the test report
- Status: Approved

### TR-TRANSFER-003 – The sample store from the fixtures
- Applies to: TC-SLY-016, TC-SLY-017, TC-SLY-018, TC-SLY-019, TC-SLY-020, TC-SLY-021, TC-SLY-024, TC-SLY-025, TC-SLY-026, TC-SLY-029, TC-SLY-033, TC-SLY-037, TC-SLY-009, SMOKE-TRANSFER-001
- Requirement: REQ-SLY-016
- Group: BK
- Kind: setup
- Text: The checks shall build the sample store from the 15 converted skill graphs, the graph `sample.code` and the context graph `context.cp13` under `tests/fixtures/graphs/`, unchanged, plus `cp2.multi` with four versions saved by four authors through the graph model.
- Rationale: the golden examples of CORE (TR-CORE-004) cover every kind of step including a loop-controlling one (D-374) and a context graph; `cp2.multi` gives the several versions and authors of AC-005 and AC-006.
- Credibility aspect: reference accuracy
- Verified by: inspection of the fixture list
- Status: Approved

### TR-TRANSFER-004 – Every write position is tried, and the injector fires
- Applies to: TC-SLY-026, TC-SLY-029, TC-SLY-036, TC-SLY-038
- Requirement: REQ-SLY-029
- Group: FI
- Kind: setup
- Text: The check shall interrupt the run after every single write of that run — each append, cut back and removal on the target, and the writing of the aside file — one run per write position, through CORE's `FailingBackend` on the target side, and shall show that it fired by comparing the counted writes with the writes of the same run without a stop.
- Rationale: HR-007 "at any one write": no sampling (TR-CORE-001, 002); an injector that never fires would let every position pass; the uninterrupted run gives the known number of writes. CORE's injector counts only appends; a sync also cuts back and removes on the copy and writes the aside file, and the positions between those writes are where the header-first defect sits (D-466), so `FailingBackend` is extended to count them (protected helper, installed with the red tests; CORE's counts stay, a save only appends; owner, review of group FI).
- Credibility aspect: power and false-alarm rate
- Verified by: mutation (header written first, or removed first in the sync, must fail the check)
- Status: Approved

### TR-TRANSFER-005 – Times copied are compared exactly, times made are not
- Applies to: TC-SLY-016, TC-SLY-020, TC-SLY-022, TC-SLY-025, TC-SLY-040, TC-SLY-026, TC-API-064
- Requirement: REQ-SLY-016
- Group: EX
- Kind: unit
- Text: A check shall compare the time of a version exactly where the time was copied by a move or sync, and shall set a fixed clock where it compares times made by two saves.
- Rationale: FR-59 "times unchanged" is an exact claim about copied values; a time made by a save is the clock of the store (TR-CORE-008), so TC-SLY-022 fixes the clock instead of loosening the comparison.
- Credibility aspect: measurement conditions
- Verified by: review
- Sign-off: skimmed as a group
- Status: Approved

### TR-TRANSFER-006 – The lock is tried across real processes
- Applies to: TC-SLY-028, TC-SLY-039
- Requirement: REQ-SLY-028
- Group: FI
- Kind: setup
- Text: The check shall hold the copy's lock in a separate operating-system process and kill that process with SIGKILL before the second attempt, never with threads in one process.
- Rationale: the lock is an operating-system lock released when its process ends; a lock tried by threads of one process may pass for the wrong reason, and only a killed process shows that a crashed sync leaves no stale lock.
- Credibility aspect: stand-in fidelity
- Verified by: inspection
- Status: Approved

### TR-TRANSFER-007 – Only throw-away databases and folders
- Applies to: TC-SLY-016, TC-SLY-018, TC-SLY-022, TC-SLY-024, TC-SLY-025, TC-SLY-040, TC-SLY-029, TC-SLY-036, TC-SLY-038, TC-API-063, TC-API-065, TC-API-066, TC-API-067, SMOKE-TRANSFER-001
- Requirement: REQ-SLY-016
- Group: BK
- Kind: setup
- Text: The checks shall write only to folders under a new temporary folder and to databases they create; the smoke check shall write only to a new database `mia_smoke` and new folders, refuse any other database name, and drop them by name afterwards.
- Rationale: TR-CORE-009 and CORE's Deploy lessons: the owner's data (volume `mia-data`, his database) is never a fixture; the live store switch is a later owner gate (D-460 (1)).
- Credibility aspect: measurement conditions
- Verified by: inspection
- Status: Approved

### TR-TRANSFER-008 – Each check is shown able to fail
- Applies to: TC-SLY-017, TC-SLY-018, TC-SLY-019, TC-SLY-023, TC-SLY-026, TC-SLY-029, TC-SLY-038, TC-SLY-031
- Requirement: REQ-SLY-019
- Group: CR
- Kind: setup
- Text: Each of these checks shall be shown able to fail by running it once against a deliberate defect before it is trusted: the per-record check of today, the headers written first, no flush, the removal before the aside file, the header removed first in the sync, a one-graph move that overwrites.
- Rationale: the two defects of today (survey) and the prototype's header-first removal (D-466) are the faults these checks exist for; a check that cannot catch them proves nothing.
- Credibility aspect: reviewer independence
- Verified by: mutation
- Status: Approved

### TR-TRANSFER-009 – The backend is started and stopped for real
- Applies to: TC-API-060, TC-API-061, TC-API-062, TC-API-063, TC-API-064, TC-API-065, TC-API-066, TC-API-067
- Requirement: REQ-API-062
- Group: EP
- Kind: setup
- Text: The checks shall start the backend through the same start function and stop it through the same orderly-stop list as `python -m MIA` does, with a configuration naming `store`, `copy` and `autosync`, and an unreachable live store shall be a database address on a port where nothing listens.
- Rationale: AutoSync hangs on the start and the stop hook (survey: `__main__.py`); a check that calls the sync directly would not show that the hook runs, nor that the stop sync runs before the database is closed. Today `__main__.py` does the start steps and `socketio.run` in one function: Implement splits the start steps and the stop list into two functions that `__main__` calls and the checks call with Flask's test client (a structural change inside N-2.1, no new part or interface; owner, review of group EP).
- Credibility aspect: stand-in fidelity
- Verified by: inspection
- Status: Approved

### TR-TRANSFER-010 – VIEW's parts, skipped until they exist
- Applies to: TC-SLY-030, TC-API-060, TC-API-061, TC-API-062, TC-API-063, TC-API-064
- Requirement: REQ-SLY-030
- Group: EP
- Kind: setup
- Text: TC-SLY-030 shall write the side records through the table definitions of IF-302 v15 (VIEW, A-172), and TC-API-060 to 064 shall configure the backend through VIEW's `store` setting and ask VIEW's `GET /api/v2/store`; each shall be skipped, with the reason, while that part of VIEW is missing, and shall be green before TRANSFER's Verify.
- Rationale: D-460: the side tables are carried by an explicit list, tested once VIEW is merged into `goal/v4`; the copy setting lies on top of VIEW's store setting (D-465); a skip keeps the gap visible, a stand-in table or route would test TRANSFER against itself. Extended to the API checks by the agent on the owner's delegation (2026-11-22, D-468).
- Credibility aspect: validity domain
- Verified by: inspection of the test report
- Status: Approved

### TR-TRANSFER-011 – The path search
- Applies to: TC-SLY-037
- Requirement: REQ-SLY-037
- Group: EP
- Kind: setup
- Text: The check shall place the source under a folder whose name holds a random 16-character token and shall search every file of the resulting folders, as bytes, for that token, for the absolute path of every folder the check made, and for the home folder's path.
- Rationale: AC-008 "no file holds a path of where it was made"; a random token cannot appear by chance, and a byte search also finds a path inside JSON strings. The folders the check made lie under the system's temporary folder, outside home and without the token: a file that held the copy's own path was missed (V-4 of Verify, A-197).
- Credibility aspect: power and false-alarm rate
- Verified by: mutation (an aside file that holds the copy's absolute folder must fail the check: defect D1 of `verify-repro/defects.json`)
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan, 2026-11-22, new; Verify, 2026-11-27, changed by A-197 (D-548: every folder the check made)
