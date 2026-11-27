# Test specification: API and accounts (N-2.1)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md   **Status:** Draft (Plan for node N-2.1, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-101 and IF-104 (provider), IF-201 and IF-203 (consumer), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-API-001 | REQ-API-001 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-1: with the fake model each scripted answer arrives as ordered sentences | as stated |
| TC-API-002 | REQ-API-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-15: a change by one user is visible on a second connection within 5 s with its author | as stated |
| TC-API-003 | REQ-API-003 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: correct credentials open a session; wrong ones do not | exact |
| TC-API-004 | REQ-API-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: the sixth failed attempt within a minute is refused even with the right password | exact |
| TC-API-005 | REQ-API-005 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: a search of the database and all logs after 10 logins finds no password | exact |
| TC-API-006 | REQ-API-006 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: a non-owner's create request is refused | exact |
| TC-API-007 | REQ-API-007 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: a request without a session is refused; a foreign origin is refused; the rate limit value is set in Plan | as stated |
| TC-API-008 | REQ-API-008 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: plain HTTP from a LAN address is refused | exact |
| TC-API-009 | REQ-API-009 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-15: 100 % of changes in a scripted session carry the account | as stated |
| TC-API-010 | REQ-API-010 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-20: a second user sees and changes a first user's workflow, preset and persona | as stated |
| TC-API-011 | REQ-API-011 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-20: the unit tests pass on 3.12 | exact |
| TC-API-012 | REQ-API-012 | Inspection | 1 | the code and the log files of the repository | AC-15: no database driver is imported outside the storage client | as stated |
| TC-API-013 | REQ-API-013 | System | 3 | the mia image as it is (never pulled) started alone in a pod published only on 127.0.0.1; its model server is the HTTP stand-in of IF-103 (`tests/helpers/mocks/if_103_model_server_http.py`, A-52, D-147), MIA waits at most 20 s for it; skipped, never passed, without podman, the image or the installed stand-in; the pod is removed afterwards | AC-29: the container starts alone against the mocks and serves the chat page: `/` answers within 180 s with the chat page (title MIA, the message list, the composer), and the stand-in saw the model list and the calibration chat | as stated |
| TC-API-014 | REQ-API-014 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-16: with the fake storage each of the six operations works; an invalid graph is refused with the rule named | exact |
| TC-API-015 | REQ-API-015 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1, AC-14: the contract suite test_if_101_chat_api.py passes against the API and accounts (stage 2) | as stated |
| TC-API-016 | REQ-API-016 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-16: the contract suite test_if_104_graph_api.py passes against the API and accounts (stage 2) | as stated |
| TC-API-017 | REQ-API-017 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: after the logout the same session is refused with 401 | exact |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).

## Test cases of G-V4.VIEW (moved at the merge 2026-11-25)
Unchanged from `specs/mia/goals/G-V4.VIEW/test-spec.md`; their test requirements TR-VIEW-001 to 021 are in `specs/mia/test-requirements.md`. All checks are exact. VAL-VIEW-01 stays in the goal record.

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|---|
| TC-API-018 | REQ-API-019 | component | 1 | a configuration without a store setting; graphs written to the data folder through CORE's GraphModel | the v2 list and read routes give those graphs; the store route says `files` | exact |
| TC-API-019 | REQ-API-020 | component | 1 | the store settings `postgress`, `""`, `5` | the start is refused, the message names `store` and the value | exact |
| TC-API-020 | REQ-API-030 | component | 1 | MIA's web application (`web_app`) with accounts on, a files store with cp2.multi | after a login through `/api/login` the routes `/api/v2/me` and `/api/v2/graphs` answer under the same session; the v1 route `/api/graphs` answers as before | exact |
| TC-API-021 | REQ-API-036 | component | 2 | cp2.multi at version 4 on files and on PostgreSQL; a save and a restore whose graph fails the store's record check (step.write with the extra field `colour`, every graph rule kept) | 422 `refused`, rule `schema_break`, detail `colour`; still 4 versions, no record of changes | exact |
| TC-API-022 | REQ-API-039 | component | 1 | cp2.multi at 4; a save to version 5; then a second write of the record `cp2.multi/5` attempted through the graph API's writer | the second write is not made (no new record version); the first record is unchanged | exact |
| TC-API-023 | REQ-API-040, REQ-API-042 | component | 1 | cp2.multi at 4; the table `graph_changes` made to fail on write | the save gives version 5 with `logged` false; the version is stored; the changes route lists version 5 as `before_the_record` | exact |
| TC-API-024 | REQ-API-047 | component | 1 | the real provider on files with allowed origin `http://localhost`; the owner's check, save, restore and arrangement save, each with `Origin: https://evil.example`; one save with that origin and no session | each is 403 `bad_origin`; still 4 versions, no arrangement, no record | exact |
| TC-API-025 | REQ-API-031, REQ-API-035, HR-008 | component | 2 | (after RULES is merged) a working copy of cp2.multi with two identical connections and a cycle; the check route, the save and the restore of a version that breaks a rule | check route, save refusal and restore refusal give the same items, in the same order, equal to IF-301 v4 `rule_report` of the same graph | 0 differences |

### Contract suite IF-104 v2 (`tests/acceptance/contract/test_if_104_v2_graph_api.py` mock, files, postgres; `.test.mjs` JS mock)
| Test ID | Golden | Verifies | Expected result |
|---|---|---|---|
| TC-IF-104-17 | 1 | REQ-API-018, REQ-API-023, REQ-API-024, REQ-API-025, REQ-API-030 | list sorted by ID with kind, version, author, time, description, counts; version 2 of cp2.multi with current 4; versions oldest first |
| TC-IF-104-18 | 2 | REQ-API-026 | one `missing_step` problem for e2 to var.gone at `to`; nothing dropped |
| TC-IF-104-19 | 3 | REQ-API-027, REQ-API-028, REQ-API-029 | the hostile step `transform`, `untrusted`, no lifecycle, code, not changed; data steps carry only their kind; texts as stored |
| TC-IF-104-20 | 4 | REQ-API-032, REQ-API-033, REQ-API-037, REQ-API-042 | version 5 by anna with a `derived` record of one `change_step`; the same graph again is no version |
| TC-IF-104-21 | – | REQ-API-038, REQ-API-051 | a matching `add_step` kept as `editor`, reason trimmed; a list that does not give the graph is 422 `changes_do_not_match` |
| TC-IF-104-22 | 5 | REQ-API-034, REQ-API-035, REQ-API-046, REQ-API-048, REQ-API-049 | `not_owner`, `conflict` with current 4, `rules_broken` ending in `cycle`, `invalid` naming `graph`, `not_found`; still 4 versions |
| TC-IF-104-23 | – | REQ-API-031, REQ-API-046 | `rules: []` for the current graph; `cycle` last for the cyclic copy; ben `not_owner`; nothing stored |
| TC-IF-104-24 | 6 | REQ-API-041, REQ-API-049 | version 5 naming t1, versions 1 to 5, a `restore` record from 4; version 99 `not_found` |
| TC-IF-104-25 | 7 | REQ-API-043, REQ-API-044, REQ-API-046, REQ-API-048 | `positions` null, then var.in at 10, -3 by anna; `invalid` naming var.in; ben `not_owner`; still 4 versions |
| TC-IF-104-26 | 8 | REQ-API-021, REQ-API-022, REQ-API-050 | store, reachable, `shown` live, `live_reachable`, `lag` 0 / null; 503 `store_unreachable` while `me` answers ben |
| TC-IF-104-27 | – | REQ-API-045 | all eleven routes with a made-up session 401 `unauthenticated`; nothing changed; `me` names anna as owner |

## Edge inputs of G-V4.VIEW
| Requirement | Edge | Test ID | Expected result |
|---|---|---|---|
| REQ-API-020 | an empty setting and a number | TC-API-019 | refused, naming `store` and the value |
| REQ-API-039 and REQ-API-033 | an unchanged save after a kept one | TC-IF-104-20, TC-API-022 | no version, no second record |
| REQ-API-040 and REQ-API-033 | the same graph saved again after a save with `logged` false | TC-API-023 | no new version; version 5 stays `before_the_record` |
| REQ-API-047 and REQ-API-045 | a foreign origin without a session | TC-API-024 | 403 `bad_origin` (the guard of `accounts_api.py` checks the origin before the session); nothing changed |

## Scenarios (G-V4.VIEW, approved by the owner 2026-11-22, D-441)

### TC-API-018 – Without a store setting the data folder is read
- Verifies: REQ-API-019
- Given: a configuration with no store setting; cp2.multi written with four versions through CORE's GraphModel into the data folder the backend uses today
- When: an account lists the graphs and reads cp2.multi through IF-104 v2
- Then: the list holds cp2.multi at version 4 and the read gives version 4
- And: the store route answers `store` `files`

### TC-API-019 – An unknown store setting stops the start
- Verifies: REQ-API-020
- Given: three configurations whose store setting is `postgress`, the empty text and the number 5
- When: the API and accounts is started with each
- Then: each start is refused before any route answers
- And: the message names the setting `store` and its value (`postgress`, the empty text, `5`)

### TC-API-020 – The v2 routes live in MIA's web application
- Verifies: REQ-API-030
- Given: MIA's web application with accounts on, `anna` the owner, a files store holding cp2.multi
- When: anna logs in through `/api/login` and calls `/api/v2/me`, `/api/v2/graphs` and the v1 route `/api/graphs` with that one session
- Then: `me` answers anna as owner and the list holds cp2.multi
- And: the v1 route answers as before (one login is enough, NFR-12)

### TC-API-021 – A refused record check writes nothing
- Verifies: REQ-API-036
- Given: cp2.multi at version 4, on the file store and on PostgreSQL; a working copy whose step.write carries the extra field `colour` (it keeps every graph rule, so only the store's record check can refuse it; D-444)
- When: the owner saves the copy; then a version 5 with the same content is written around the checks as raw records (as sample.broken is), a clean version 6 is kept on top, and the owner restores version 5
- Then: each answer is 422 `refused` with the rule `schema_break` and the detail `colour`
- And: cp2.multi still has 4 versions and no record of changes was written

### TC-API-022 – A record of changes is written once
- Verifies: REQ-API-039
- Given: cp2.multi at version 4; the owner saved version 5, so the record `cp2.multi/5` exists
- When: the graph API's writer of records is asked to write `cp2.multi/5` again with other entries
- Then: no write is made: the record keeps one version
- And: its entries are those of the first write

### TC-API-023 – A version without its record
- Verifies: REQ-API-040, REQ-API-042
- Given: cp2.multi at version 4; the table `graph_changes` made to fail on every write (a stand-in backend that raises for that table only)
- When: the owner saves a changed graph
- Then: the answer is version 5 with `changed` true and `logged` false, and version 5 is stored
- And: the changes route lists five items, the last one version 5 marked `before_the_record`

### TC-API-024 – A foreign origin changes nothing (real side)
- Verifies: REQ-API-047
- Given: the real provider on the file store with the allowed origin `http://localhost`; cp2.multi at version 4; anna logged in
- When: anna sends the check, a save, a restore of version 1 and an arrangement save, each once with `Origin: https://evil.example`; then one save with that origin and no session
- Then: each is 403 `bad_origin`, also the one without a session (the origin is checked first, as `accounts_api.py` does)
- And: cp2.multi still has 4 versions, no arrangement and no record of changes (the JS mock side is the installed case TC-IF-104-22)

### TC-API-025 – One rule report on the check route, the save and the restore
- Verifies: REQ-API-031, REQ-API-035, HR-008
- Given: RULES merged (IF-301 v4 in the code); cp2.multi at version 4; a working copy with a second identical connection e3 from var.in to step.write (`duplicate_connection`) and e9 var.out → step.write (`cycle`); a version 5 stored around the checks with the same faults and a clean version 6 kept on top
- When: the owner sends the copy to the check route, saves it, and restores version 5
- Then: the check route gives `duplicate_connection` and then `cycle` with their parts
- And: the save and the restore are 422 `rules_broken` with the same items in the same order, equal to `rule_report` of IF-301 v4 for the same graph (0 differences)
- And: nothing was written

### TC-IF-104-17 – List, one version, versions (golden 1)
- Verifies: REQ-API-018, REQ-API-023, REQ-API-024, REQ-API-025, REQ-API-030
- Given: cp2.multi with versions 1 to 4 by anna, ben, anna, ben; sample.code with one version; the mock, the real provider on files and on PostgreSQL
- When: ben lists the graphs, reads cp2.multi and its version 2, and asks for its versions
- Then: the list is cp2.multi, sample.code, with kind `workflow`, version 4 by ben, description, 3 / 2 and 7 / 6
- And: the current read is version 4 by ben with current 4 (t4); version 2 is by ben with current 4 (t2); no problems
- And: the versions are 1 to 4 by anna, ben, anna, ben; the three providers give the same answers

### TC-IF-104-18 – What cannot be drawn is named (golden 2)
- Verifies: REQ-API-026
- Given: sample.broken (e2 from step.a to the missing var.gone), stored around the checks
- When: it is read
- Then: problems is exactly one `missing_step` for connection e2, step var.gone, end `to`
- And: both steps and both connections are in the answer

### TC-IF-104-19 – Marks and text as stored (golden 3)
- Verifies: REQ-API-027, REQ-API-028, REQ-API-029
- Given: sample.code with the hostile step (toolbox ID import.demo, not in the toolbox, a code connection e2)
- When: it is read
- Then: the hostile step is `transform`, `untrusted`, lifecycle null, `code` true, `changed_since_trusted` false, with a reason text
- And: loop.review is `master`, no code, not changed; step.check carries trust, lifecycle and reason; var.in carries only `{"kind": "data"}`
- And: the hostile ID and var.in's value come back exactly as stored

### TC-IF-104-20 – A change is a new version with its record (golden 4)
- Verifies: REQ-API-032, REQ-API-033, REQ-API-037, REQ-API-042
- Given: cp2.multi at version 4
- When: anna saves it with step.write changed to t9 and expected version 4, then saves the same graph again
- Then: the first answer is version 5, changed, logged, 1 entry, by anna
- And: the changes route lists four `before_the_record` items and one `derived` from 4 with the entry `change_step` of step.write, t4 to t9
- And: the second answer is version 5, not changed, `logged` null, and there are still 5 versions

### TC-IF-104-21 – Editor entries kept only when they give the graph
- Verifies: REQ-API-038, REQ-API-051
- Given: cp2.multi at version 4
- When: anna saves it with a new data step var.note and the entry `add_step` var.note with reason " a note "; then a graph naming t8 with the entry `change_step` naming t7
- Then: the first is version 5, logged, with an `editor` record whose reason is "a note"
- And: the second is 422 `changes_do_not_match` and there are still 5 versions

### TC-IF-104-22 – Refusals change nothing (golden 5)
- Verifies: REQ-API-034, REQ-API-035, REQ-API-046, REQ-API-048, REQ-API-049
- Given: cp2.multi at version 4; anna the owner, ben another account
- When: ben saves; anna saves with expected version 3; anna saves a graph with e9 var.out → step.write; anna saves `{"nodes": "x"}`; anna saves `nope`; ben reads version 9
- Then: 403 `not_owner`; 409 `conflict` with current 4; 422 `rules_broken` whose last item is `cycle` naming step.write and var.out; 422 `invalid` detail `graph`; 404 `not_found`; 404 `not_found` detail `version`
- And: cp2.multi still has 4 versions
- And: (JS suite) a save with `Origin: https://evil.example` is 403 `bad_origin` on the JS mock

### TC-IF-104-23 – The check route reports and stores nothing
- Verifies: REQ-API-031, REQ-API-046
- Given: cp2.multi at version 4
- When: anna checks the current graph and the copy with e9 var.out → step.write; ben checks the copy
- Then: the current graph gives `rules: []`; the copy's last item is `cycle`, every item with a text
- And: ben is 403 `not_owner`; still 4 versions

### TC-IF-104-24 – Restore as a new version (golden 6)
- Verifies: REQ-API-041, REQ-API-049
- Given: cp2.multi at version 4
- When: anna restores version 1 with the reason "back to the start", and restores version 99
- Then: the answer is version 5, restored 1, changed; version 5 names t1; versions 1 to 5 are listed
- And: the last record is `restore` from 4 with the one entry restore 1 and its reason
- And: version 99 is 404 `not_found`

### TC-IF-104-25 – The arrangement (golden 7)
- Verifies: REQ-API-043, REQ-API-044, REQ-API-046, REQ-API-048
- Given: cp2.multi never arranged
- When: ben reads the arrangement; anna saves var.in at 10.4, -3 and `nope` at 0, 0; anna saves var.in at x "far"; ben saves a place; ben reads again
- Then: first `positions` null; `saved` 1; then var.in at 10, -3 by anna
- And: 422 `invalid` detail var.in; 403 `not_owner`; still 4 graph versions

### TC-IF-104-26 – The store route and an unreachable store (golden 8)
- Verifies: REQ-API-021, REQ-API-022, REQ-API-050
- Given: cp2.multi in a store that answers; ben logged in
- When: ben asks for the store, the store stops answering, ben asks for the store, lists and reads
- Then: first `store` files or database, reachable, `shown` live, `live_reachable` true, `lag` 0 graphs since null
- And: then reachable and live_reachable false; listing and reading 503 `store_unreachable`; `me` still answers ben, not owner

### TC-IF-104-27 – No session, no access
- Verifies: REQ-API-045
- Given: cp2.multi at version 4; the made-up session `made-up`
- When: each of the eleven v2 routes is called with it
- Then: each is 401 `unauthenticated`
- And: cp2.multi still has 4 versions; anna's real login works and `me` names her owner; a wrong password is 401

## Test cases of G-V4.GRAPHSTORE.TRANSFER (moved at the merge 2026-11-27)
Unchanged from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/test-spec.md` (TC-SLY-040 by A-196, the path search of TC-SLY-037 by A-197); their test requirements TR-TRANSFER-001 to 011 are in `specs/mia/test-requirements.md`. All checks are exact and run in stage 2 (`tests/acceptance/test_transfer_*.py`); the PostgreSQL half needs podman, the local `postgres:16` image and psycopg 3. The storage checks, the smoke row and the witnesses of the accepted cases are in `specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/test-spec.md`.

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|---|
| TC-API-060 | REQ-API-060 | component | 2 | the backend app with `store` files (live) and `copy` set to a folder holding a different version of `cp2.multi` | `GET` of `cp2.multi` through IF-104 v2 answers the copy's version | exact |
| TC-API-061 | REQ-API-061 | component | 2 | `copy` set, no `autosync`; the live store has a newer version; start and orderly stop of the backend | the copy is unchanged after start and after stop | exact |
| TC-API-062 | REQ-API-062 | component | 2 | `copy` set, `autosync` true; the live store has a newer version; a version written to the live store while running; orderly stop | the newer version is on the copy before the first answer; the version written while running is on the copy after the stop | exact |
| TC-API-063 | REQ-API-063 | component | 2 | `copy` set, `autosync` true, `store` database with an address on a closed port | the backend starts and answers graphs from the copy; the log holds one line naming the live store and `sync not run` | exact |
| TC-API-064 | REQ-API-064 | component | 2 | AC-006 with `copy` set; `GET /api/v2/store` before and after a sync | before: `shown` `copy`, `live_reachable` true, `lag` `{"graphs": 1, "since": <time of live version 5 of cp2.multi>}`; after: `lag` `{"graphs": 0, "since": null}` | exact |
| TC-API-065 | REQ-API-065 | component | 2 | the live store with cp2.multi at 4; `copy` set to a folder whose marker names format 2 | the read answers version 4; `shown` live, lag no graphs; one log line naming the copy and `format 2` | exact |
| TC-API-066 | REQ-API-066 | component | 2 | AC-006 with `copy` set, no `autosync`; the owner saves cp2.multi on version 6 | version 7 in the live store (7 versions); the copy's graph group unchanged | exact |
| TC-API-067 | REQ-API-064 | component | 2 | `copy` set, no `autosync`, `store` database with an address on a closed port; `GET /api/v2/store` | `shown` copy, `reachable` true, `live_reachable` false, `lag` `{"graphs": 0, "since": null}` | exact |

## Edge inputs of G-V4.GRAPHSTORE.TRANSFER (per operation: empty, missing, at and past the limit)
| Operation | Edge | Check |
|---|---|---|
| AutoSync | off; on with live reachable; on with live unreachable | TC-API-061 to 063 |

## Scenarios (G-V4.GRAPHSTORE.TRANSFER, approved 2026-11-22, D-468)

### TC-API-060 – MIA reads graphs from the copy
- Verifies: REQ-API-060
- Given: the backend with the live store on files and `copy` set to a folder holding a different version of `cp2.multi`
- When: `cp2.multi` is read through the graph interface
- Then: the answer is the copy's version

### TC-API-061 – Without AutoSync nothing is synced
- Verifies: REQ-API-061
- Given: `copy` set, no `autosync`; the live store has a newer version of `cp2.multi`
- When: the backend starts and stops in an orderly way
- Then: the copy is unchanged after the start and after the stop

### TC-API-062 – AutoSync at start and at an orderly stop
- Verifies: REQ-API-062
- Given: `copy` set, `autosync` true; the live store has a newer version of `cp2.multi`
- When: the backend starts, a new version is written to the live store while it runs, and the backend stops in an orderly way
- Then: the newer version is on the copy before the first answer
- And: the version written while running is on the copy after the stop

### TC-API-063 – An unreachable live store is reported, not fatal
- Verifies: REQ-API-063
- Given: `copy` set, `autosync` true, `store` database with an address on a port where nothing listens
- When: the backend starts
- Then: it starts and answers graphs from the copy
- And: its log holds one line naming the live store and "sync not run"

### TC-API-064 – The store answer tells how far the copy lags
- Verifies: REQ-API-064
- Given: the case of AC-006 with `copy` set
- When: `GET /api/v2/store` is asked before and after a sync
- Then: before: `shown` is `copy`, `live_reachable` true, `lag` `{"graphs": 1, "since": <time of live version 5 of cp2.multi>}`
- And: after: `lag` is `{"graphs": 0, "since": null}`

### TC-API-065 – A copy of a newer format is not read
- Verifies: REQ-API-065
- Given: the live store on files with the sample store (cp2.multi at version 4); `copy` set to a folder whose marker names format 2
- When: the backend starts, and cp2.multi and the store are read through the graph interface
- Then: the read answers version 4 (the live store's), the store answer has `shown` live and a lag of no graphs
- And: `mia.log` holds one line naming the copy folder and "format 2"

### TC-API-066 – While a copy is set, a save goes to the live store
- Verifies: REQ-API-066
- Given: AC-006 with `copy` set, no `autosync`
- When: the owner saves cp2.multi on version 6 with one value changed
- Then: the answer is version 7 and the live store holds 7 versions
- And: the copy's graph group is unchanged, entry by entry

### TC-API-067 – The store answer while the live store does not answer
- Verifies: REQ-API-064
- Given: `copy` set (the sample store), no `autosync`, `store` database with an address on a port where nothing listens
- When: `GET /api/v2/store` is asked
- Then: `shown` copy, `reachable` true, `live_reachable` false, `lag` `{"graphs": 0, "since": null}`
