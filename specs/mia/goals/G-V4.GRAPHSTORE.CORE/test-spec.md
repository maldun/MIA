# Test specification: G-V4.GRAPHSTORE.CORE

**Requirements:** `requirements.md` (REQ-GTB-029 to REQ-GTB-032, REQ-WFM-144 to REQ-WFM-160)   **Status:** Draft (scenarios for the owner's review, step 3 of the Plan of this subgoal)

All checks are exact: every expected value is a name, an ID, a count or an equality, so no statistical check and no benchmark is needed (the high-level spec has no hard bound). The accepted cases AC-001 to AC-003 (`specs/mia/goals/G-V4/accepted-cases.md`) are witnessed by TC-WFM-148, TC-WFM-149, TC-WFM-158 and TC-WFM-159 (AC-001), TC-GTB-029, TC-GTB-030 and TC-WFM-145 (AC-002), TC-WFM-147, TC-WFM-150 and TC-WFM-151 (AC-003).

## Test cases
| Test ID | Verifies | Level | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|
| TC-GTB-029 | REQ-GTB-029 | component | a step record and a connection record, each written under `chat`, `lookup/chat`, `/chat`, `lookup/` and an empty ID | `chat`, `/chat`, `lookup/` and the empty ID refused naming `unscoped_id`; `lookup/chat` accepted | exact rule name and field |
| TC-GTB-030 | REQ-GTB-030 | component | headers `g` that pin `g/step`, `h/step`, `g/conn` and `h/conn`; all members exist | headers with `h/step` or `h/conn` refused naming `unscoped_id`; with `g/step` or `g/conn` accepted | exact |
| TC-GTB-031 | REQ-GTB-031 | unit | the record IDs `lookup/a/b`, `lookup/a`, `g//`, `lookup/` | graph `lookup` and local ID `a/b`; `lookup`, `a`; `g`, `/`; no local ID (not scoped) | exact |
| TC-GTB-032 | REQ-GTB-032 | contract | the refusal cases of TC-GTB-029, TC-GTB-030, TC-WFM-146, TC-WFM-154, TC-WFM-155, TC-WFM-160 on the files backend and on PostgreSQL 16 | the same refusal rule and detail on both | exact; the PostgreSQL half skips (never weakened) where podman, the image or psycopg 3 is missing |
| TC-WFM-144 | REQ-WFM-144 | component | a graph with steps `a`, `a/b`, connection `e1` from `a` to `a/b` | read back with the same local IDs for steps, connections and their ends | exact |
| TC-WFM-145 | REQ-WFM-145 | component | two graphs with a step `step.write` of different content; `step.write` changed once in the first | its history has the versions of its own graph, oldest first, with account and time; the other graph's step history is unchanged; versions left by an interrupted save are not listed | exact version numbers |
| TC-WFM-146 | REQ-WFM-146 | component | a graph whose last connection leads to a missing step, a graph with a cycle, a graph with a broken step content | the save is refused; the number of versions of every record of every graph table is as before | exact counts |
| TC-WFM-147 | REQ-WFM-147 | component (fault injection) | a first save and a changed save of a workflow graph and of a context graph, interrupted after each write k = 1..n | after each interruption the graph is not listed or is entirely as before; never listed with a missing member | every k; no sampling; files and PostgreSQL |
| TC-WFM-148 | REQ-WFM-148 | component | a graph of five steps saved, one step changed, saved again; then one connection changed, saved again | each save: exactly one new version of the changed step or connection and one new header version; the other records unchanged | exact counts |
| TC-WFM-149 | REQ-WFM-149 | component | the same graph saved twice, then saved after a change of its description only | the second save writes no record and answers with the newest version; the changed description is a new header version | exact counts |
| TC-WFM-150 | REQ-WFM-150 | component | a workflow graph with a cycle, one with two writers, one with an unknown kind of step, a context graph with a connection to a missing step | each refused naming the rule or IDs; no table grew; the version count of the stored graph is as before | exact counts |
| TC-WFM-151 | REQ-WFM-151 | component (fault injection) | as TC-WFM-147, then the same save repeated | the repeated save gives the full graph and exactly one new header version, for every k | every k; no sampling; files and PostgreSQL |
| TC-WFM-152 | REQ-WFM-152 | component | a context graph of three steps and two connections | members in `context_nodes` and `context_edges` under `<graph>/<local>`, none in `graph_nodes` or `graph_edges`; header kind `context` | exact IDs |
| TC-WFM-153 | REQ-WFM-153 | component | a graph saved without a kind and the same graph with the kind `workflow` | both stored with the kind `workflow`; members in the workflow tables | exact |
| TC-WFM-154 | REQ-WFM-154 | component | kinds `swarm`, the empty text and a number | each refused naming `kind`; nothing stored | exact |
| TC-WFM-155 | REQ-WFM-155, REQ-WFM-161 | component | a context graph with a repeated step ID, one with a repeated connection ID, one with a connection to a missing step | each refused naming the ID; nothing written; an empty context graph accepted as one header version | exact |
| TC-WFM-156 | REQ-WFM-156 | component | a context graph of two connected steps of the same category and a cycle | accepted (no order, alternation, writer or stop-limit rule applied) | exact |
| TC-WFM-157 | REQ-WFM-157 | component | a context graph and a workflow graph, each read at every version | the context graph carries the kind `context`; the workflow graph has the shape it had before the kind existed | exact |
| TC-WFM-158 | REQ-WFM-158 | component | a graph saved by three accounts | versions 1 to 3, oldest first, with the three accounts and a time each | exact |
| TC-WFM-159 | REQ-WFM-159 | component | three saved versions of a workflow graph (with a loop-controlling step) and of a context graph | each version reads back equal to what was saved at that version | exact equality |
| TC-WFM-160 | REQ-WFM-160 | unit | graph IDs `look/up`, `lookup`, `/lookup`, the empty ID | `look/up`, `/lookup` and the empty ID refused naming `unscoped_id` and nothing stored; `lookup` accepted | exact |

## Edge inputs (per rule: zero, empty, missing, at and past the limit; per pair of rules acting on the same data)
| Rule (REQ) | Edge or pair | Test ID | Expected result |
|---|---|---|---|
| REQ-GTB-029 | empty local ID (`lookup/`) | TC-GTB-029 | refused naming `unscoped_id` |
| REQ-GTB-029 | empty graph part (`/chat`) | TC-GTB-029 | refused naming `unscoped_id` |
| REQ-GTB-031 | a local ID of only a slash (`g//`) | TC-GTB-031 | graph `g`, local ID `/` (the first slash separates) |
| REQ-WFM-160 and REQ-GTB-029 | a graph ID that is the prefix of another (`look` and `lookup`) | TC-WFM-145 | the two graphs' steps do not mix; `look/x` is never a member of `lookup` |
| REQ-WFM-148 and REQ-WFM-149 | a step whose content is changed and changed back | TC-WFM-148 | two new step versions (the content is compared with the newest version only) |
| REQ-WFM-147 and REQ-WFM-151 | an interruption after the last write (the header) | TC-WFM-147 | the graph is entirely new; the repeated save writes nothing |
| REQ-WFM-152 and REQ-WFM-161 | a context graph with no steps and no connections | TC-WFM-155 | accepted; one header version |
| REQ-WFM-154 and REQ-WFM-153 | the kind given as `workflow` explicitly and as missing | TC-WFM-153 | the same stored result |

## Statistical checks (M19)
None: no result of this subgoal is random or noisy.

## Benchmarks and baselines
None: the high-level spec has no hard bound (owner, D-402); a budget, if wanted later, comes with a reference.

## Smoke tests (run in Phase 6, target environment)
| Test ID | Verifies | Target | Conditions | Expected result |
|---|---|---|---|---|
| SMOKE-CORE-001 | REQ-WFM-158, REQ-WFM-159, REQ-WFM-152 | the owner's host, a new files directory and a new database `mia_smoke` on the owner's running PostgreSQL server, both made for the test | one workflow graph and one context graph under throw-away IDs, saved, changed twice and read | three versions each with account and time, each read as saved, on both stores |

## Validation criteria (checked in Phase 7)
| ID | Criterion | How we check | Who | Agreement (if numeric): margin, mean or single values, method |
|---|---|---|---|---|
| VAL-CORE-01 | FR-57, FR-60 and NFR-16 hold for the deployed version as they held in the prototype (round 03) | the owner re-runs the commands of the round 03 sheet against the deployed code, or looks at the same cases through the viewer | Stefan Reiterer (owner) | single values: every line passes on files and on PostgreSQL |

## Scenarios
<!-- one block per check of the tables above, in plain language, approved before the check is built -->

### TC-GTB-029 – A step or connection without a graph in its ID is refused
- Verifies: REQ-GTB-029
- Given: a step record and a connection record, each offered under four IDs: `chat`, `/chat`, `lookup/` and the empty ID, and once under `lookup/chat`
- When: each of the ten records is written
- Then: the four unscoped IDs of each table are refused, each naming the rule `unscoped_id`
- And: the records under `lookup/chat` are accepted and stored
- And: witnesses AC-002

### TC-GTB-030 – A header names only its own members
- Verifies: REQ-GTB-030
- Given: four headers for the graph `g`: one pins the step `h/step`, one the step `g/step`, one the connection `h/conn`, one the connection `g/conn`; all four members exist
- When: each header is written
- Then: the headers with `h/step` and with `h/conn` are refused, each naming `unscoped_id`; the headers with `g/step` and with `g/conn` are accepted
- And: witnesses AC-002

### TC-GTB-031 – The first slash separates graph and local ID
- Verifies: REQ-GTB-031
- Given: the record IDs `lookup/a/b`, `lookup/a`, `g//` and `lookup/`
- When: each is split into graph ID and local ID
- Then: `lookup/a/b` gives graph `lookup` and local ID `a/b`; `lookup/a` gives `lookup` and `a`; `g//` gives `g` and `/`; `lookup/` gives no local ID, so it is not scoped

### TC-GTB-032 – Both stores refuse the same way
- Verifies: REQ-GTB-032
- Given: one files store and one PostgreSQL 16 store (throw-away container), both empty
- When: the refusal cases of TC-GTB-029, TC-GTB-030, TC-WFM-146, TC-WFM-154, TC-WFM-155 and TC-WFM-160 are run on both
- Then: each case gives the same refusal rule and the same named detail on both stores
- And: where podman, the image or psycopg 3 is missing the PostgreSQL half is skipped and reported as skipped, never as passed

### TC-WFM-144 – A graph is read with local IDs
- Verifies: REQ-WFM-144
- Given: a workflow graph `g` with steps `a` and `a/b`, and a connection `e1` from `a` to `a/b`
- When: it is saved and read back
- Then: the step IDs are `a` and `a/b`, the connection ID is `e1`, and its ends are `a` and `a/b`; no ID carries the graph ID

### TC-WFM-145 – A step's history lists its own graph's changes
- Verifies: REQ-WFM-145
- Given: two graphs `lookup` and `search`, each with a step `step.write` of different content; `look` also exists with a step `x`
- When: `step.write` of `lookup` is changed and saved
- Then: its history lists two versions with account and time, oldest first; the history of `step.write` in `search` lists one; versions left by an interrupted earlier save are not listed
- And: the step `x` of `look` is never a member of `lookup`
- And: witnesses AC-002

### TC-WFM-146 – The whole graph is checked before the first write
- Verifies: REQ-WFM-146
- Given: a stored graph, and three new graphs: one whose last connection leads to a missing step, one with a cycle, one with a broken step content
- When: each of the three is saved
- Then: each is refused; the number of versions of every record in every graph table is as before

### TC-WFM-147 – The header is written last: no half-stored graph at any write
- Verifies: REQ-WFM-147
- Given: a workflow graph of five steps and four connections (ten writes for a first save) and a context graph (six writes), for a first save and a changed save of each; a store that fails at the k-th write
- When: the save is run once for every k from 1 to the number of writes of that save
- Then: after each interruption the graph is not listed, or is entirely as before; it is never listed with a step or connection that is missing
- And: the check runs for every k, on the files store and on the PostgreSQL store, and fails when one k fails
- And: witnesses AC-003

### TC-WFM-148 – Only changed members get a new version
- Verifies: REQ-WFM-148
- Given: a workflow graph of five steps saved as version 1
- When: one step is changed and the graph is saved again
- Then: exactly one new version of that step and one new header version exist; the other four steps and all connections have no new version
- And: when then one connection is changed and the graph saved, exactly one new version of that connection and one new header version exist; no step has a new version
- And: a step changed and changed back gives two new step versions
- And: witnesses AC-001

### TC-WFM-149 – An unchanged graph gets no new version
- Verifies: REQ-WFM-149
- Given: a graph saved as version 1
- When: the same graph is saved again; then only its description is changed and it is saved
- Then: the second save writes no record and answers with version 1; the third save writes one header version and no step version
- And: witnesses AC-001

### TC-WFM-150 – A refused save writes nothing
- Verifies: REQ-WFM-150
- Given: a stored graph at version 2 and four new graphs: a cycle, two writers of one data step, an unknown kind of step, a context graph with a connection to a missing step
- When: each is saved
- Then: each is refused naming the rule or the IDs; no table grew; the stored graph is still at version 2
- And: witnesses AC-003

### TC-WFM-151 – An interrupted save is finished by repeating it
- Verifies: REQ-WFM-151
- Given: the interrupted saves of TC-WFM-147, one for every k
- When: the same save is repeated after each interruption
- Then: the graph is complete and equals the saved one; it has exactly one new header version; no step is stored twice for equal content
- And: witnesses AC-003

### TC-WFM-152 – A context graph is stored in the context tables
- Verifies: REQ-WFM-152
- Given: a context graph `c` of three steps and two connections
- When: it is saved
- Then: the members are records `c/<local>` in `context_nodes` and `context_edges` and none in `graph_nodes` or `graph_edges`; the header has the kind `context`

### TC-WFM-153 – No kind means workflow
- Verifies: REQ-WFM-153
- Given: a graph given without a kind, and the same graph with the kind `workflow` written out
- When: each is saved under its own ID
- Then: both are stored with the kind `workflow` and members in the workflow tables, with the same content

### TC-WFM-154 – An unknown kind is refused
- Verifies: REQ-WFM-154
- Given: graphs with the kind `swarm`, the empty text and the number 3
- When: each is saved
- Then: each is refused naming the field `kind`; nothing is stored

### TC-WFM-155 – A context graph keeps identity and ends
- Verifies: REQ-WFM-155, REQ-WFM-161
- Given: three context graphs: one with a repeated step ID, one with a repeated connection ID, one with a connection to a missing step
- When: each is saved
- Then: each is refused naming the repeated or missing ID; nothing is written
- And: an empty context graph is accepted as one header version

### TC-WFM-156 – Workflow rules do not apply to a context graph
- Verifies: REQ-WFM-156
- Given: a context graph of two connected steps of the same category and a connection back, so that it has a cycle
- When: it is saved
- Then: it is accepted: no order, alternation, writer or stop-limit rule of workflow graphs is applied

### TC-WFM-157 – A context graph is read with its kind
- Verifies: REQ-WFM-157
- Given: a context graph and a workflow graph, each saved twice
- When: each is read at every version
- Then: the context graph is returned with the kind `context` at every version; the workflow graph has exactly the fields it had before the kind existed

### TC-WFM-158 – Versions are listed with who and when
- Verifies: REQ-WFM-158
- Given: a graph saved by the accounts `ann`, `bob` and `cy`, one version each
- When: the versions are asked
- Then: versions 1 to 3 are listed oldest first with `ann`, `bob`, `cy` and a time each
- And: witnesses AC-001

### TC-WFM-159 – Every version reads back as saved
- Verifies: REQ-WFM-159
- Given: a workflow graph (with a loop-controlling step) and a context graph (with category steps), each saved in three different versions
- When: each version is read at its number
- Then: each equals what was saved at that version, step by step and connection by connection
- And: witnesses AC-001

### TC-WFM-160 – A graph ID with a slash is refused
- Verifies: REQ-WFM-160
- Given: the graph IDs `look/up`, `/lookup`, the empty ID and `lookup`
- When: a graph is saved under each
- Then: the first three are refused naming `unscoped_id` and nothing is stored; `lookup` is accepted

### SMOKE-CORE-001 – Both graph kinds work on the owner's two stores
- Verifies: REQ-WFM-158, REQ-WFM-159, REQ-WFM-152
- Given: the owner's host; a new files directory and a new database `mia_smoke` on the owner's running PostgreSQL server, both made for the smoke test; a workflow graph and a context graph under throw-away IDs
- When: each is saved, changed twice and read, on both stores
- Then: each shows three versions with account and time and reads back as saved on both stores
- And: afterwards the files directory is removed and the database `mia_smoke` is dropped by name; MIA's own database and files store are not written
