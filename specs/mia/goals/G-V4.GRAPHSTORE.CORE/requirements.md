# Requirements: G-V4.GRAPHSTORE.CORE (low level, new and changed items)

**Top-level spec:** `specs/mia/goals/G-V4.GRAPHSTORE/top-level-spec.md`   **High-level spec:** `specs/mia/goals/G-V4.GRAPHSTORE.CORE/high-level-spec.md`   **Status:** Draft   **Plan baseline:** plan-baseline

<!-- The requirements this subgoal adds. The 37 requirements already in force (graph tables REQ-GTB-001 to REQ-GTB-028 in
     `specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md`, the workflow rules REQ-WFM-043 to REQ-WFM-049, the storage layer
     REQ-SLY-001 to REQ-SLY-015) stay as they are, with one exception: every acceptance criterion that writes a step or connection under a plain ID is
     changed by the amendment A-nn of REQ-GTB-029 (the protected tests that fail with `unscoped_id` are listed in the high-level spec, section 5).
     Drafted from the validated prototype (round 02 and round 03); each item has a basis: seen in the prototype, with its accepted case or measure.
     Accepted cases (`specs/mia/goals/G-V4/accepted-cases.md`) witness the items: AC-001 (versions), AC-002 (a step belongs to one graph), AC-003 (no half graph). -->

## Groups
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | SC | Steps belong to one graph: what a record ID says and what a step's history lists (FR-60) | REQ-GTB-029, REQ-GTB-030, REQ-GTB-031, REQ-WFM-160, REQ-WFM-144, REQ-WFM-145 |
| 2 | SV | Saving a graph: order of writes, what is written, refused and interrupted saves (FR-57, NFR-16) | REQ-WFM-146, REQ-WFM-147, REQ-WFM-148, REQ-WFM-149, REQ-WFM-150, REQ-WFM-151 |
| 3 | CG | Context graphs: the same save path for the second kind of graph (FR-57), the kind of a graph | REQ-WFM-152, REQ-WFM-153, REQ-WFM-154, REQ-WFM-155, REQ-WFM-156, REQ-WFM-157 |
| 4 | RD | Reading, history and both places: versions, who and when, a version as it was saved, the same refusals on files and database (FR-57) | REQ-WFM-158, REQ-WFM-159, REQ-GTB-032 |

## Requirements

### REQ-GTB-029 – Scoped ID of a step or connection
- Level: low   Subject: Persistence
- Group: SC
- Text: If a step or connection record is written under an ID not of the form `<graph id>/<local id>`, then the Graph tables shall refuse the record and name the rule `unscoped_id`.
- Rationale: refines FR-60 and HR-001; makes a step belong to exactly one graph by construction (D-368); amends the plain IDs of A-92 / REQ-GTB-021
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-01 (accepted case AC-002): a step written under `chat` is refused naming `unscoped_id`, under `lookup/chat` it is accepted (exact)
- Verified by: TC-GTB-029
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-GTB-030 – Header names only its own members
- Level: low   Subject: Persistence
- Group: SC
- Text: If a graph header names a step or connection whose record ID begins with the ID of another graph, then the Graph tables shall refuse the header and name the rule `unscoped_id`.
- Rationale: refines FR-60 and HR-001; a header of graph g must not pin a member of graph h
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-02: a header `g` naming `h/step` is refused naming `unscoped_id`; naming `g/step` it is accepted (exact)
- Verified by: TC-GTB-030
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-GTB-031 – The first slash separates
- Level: low   Subject: Persistence
- Group: SC
- Text: The Graph tables shall take the text before the first slash of a record ID as the graph ID, and the rest as the local ID.
- Rationale: refines HR-001 and ASM-1 of round 02; confirmed by the owner (D-402); example: `lookup/a/b` is the local ID `a/b` of the graph `lookup`, so a local ID can hold slashes and a graph ID cannot
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-03: `lookup/a/b` is accepted as the local ID `a/b` of `lookup` and read back as `a/b` (exact)
- Verified by: TC-GTB-031
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-160 – No slash in a graph ID
- Level: low   Subject: TaskRuntime
- Group: SC
- Text: If the ID of a graph contains a slash, then the Workflow management shall refuse the save and name the rule `unscoped_id`.
- Rationale: refines HR-001 and ASM-001; the record ID of its steps would name another graph; seen in the prototype: a graph `look/up` is refused naming `look/up/a`
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-21: a graph saved under the ID `look/up` is refused naming `unscoped_id` and nothing is stored (exact)
- Verified by: TC-WFM-160
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-144 – Local IDs on reading
- Level: low   Subject: TaskRuntime
- Group: SC
- Text: When a graph is read, the Workflow management shall return the IDs of its steps and connections without the graph ID.
- Rationale: refines FR-60; the caller sees `step.write`, the store holds `lookup/step.write`
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-04: a graph saved with local IDs is read back with the same local IDs, also for the ends of connections (exact)
- Verified by: TC-WFM-144
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-145 – History of a step in its graph
- Level: low   Subject: TaskRuntime
- Group: SC
- Text: When the history of a step is asked, the Workflow management shall list the versions that the headers of that graph pin, oldest first, with account and time of each.
- Rationale: refines FR-60 and HR-004; two graphs with a step `step.write` of different content have separate histories (finding S1); versions left by an interrupted save are not listed
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-05 (accepted case AC-002): changing `step.write` in `lookup` adds one version to its history and none to the history of the other graph (exact)
- Verified by: TC-WFM-145
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-146 – Whole graph checked first
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: When a graph is saved, the Workflow management shall check all its steps, connections and header against the rules before it writes the first record.
- Rationale: refines NFR-16 and HR-002; a refusal found after the first write would leave unused versions
- Parent: NFR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-06: a graph with a broken connection at its last position leaves the record counts of every table as they were (exact)
- Verified by: TC-WFM-146
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-147 – Header written last
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: When a graph is saved, the Workflow management shall write the steps and connections before the header.
- Rationale: refines NFR-16 and HR-002; the header makes a graph visible, so a graph is listed only when all its members are stored
- Parent: NFR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-07 (accepted case AC-003): a save interrupted after each of its writes never lists a graph with a missing step or connection (every write position, files and database)
- Verified by: TC-WFM-147
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-148 – Changed members only
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: When a graph is saved, the Workflow management shall write a step or connection as a new version only if its content differs from its newest version.
- Rationale: refines FR-57, FR-60; ASM-2 of round 02; the history of a step lists real changes only
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-08 (accepted case AC-001): saving a graph with one changed step writes exactly one new step version and one new header version (exact)
- Verified by: TC-WFM-148
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-149 – Unchanged graph, no version
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: When a graph is saved whose steps, connections and header fields equal its newest version, the Workflow management shall write no record and answer with the newest version.
- Rationale: refines FR-57; an unchanged save is not an edit
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-09 (accepted case AC-001): the same graph saved twice has one version; the second answer names it and no table grew (exact)
- Verified by: TC-WFM-149
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-150 – Refused save writes nothing
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: If a save is refused, then the Workflow management shall write no record, count no version and name the broken rule or the IDs.
- Rationale: refines NFR-16 and HR-005; the refusals are those of the graph rules and the record checks
- Parent: NFR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-10 (accepted case AC-003): a graph with a cycle, two writers, an unknown kind of step or a context connection to a missing step is refused and no table grew (exact)
- Verified by: TC-WFM-150
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-151 – An interrupted save is finished by repeating it
- Level: low   Subject: TaskRuntime
- Group: SV
- Text: If a save is interrupted after any write, then the Workflow management shall complete the same graph when the same save is repeated, with exactly one new graph version.
- Rationale: refines NFR-16 and HR-005; unused step versions of the first attempt are pinned again when equal
- Parent: NFR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-11 (accepted case AC-003): for every write position the repeated save gives the full graph and one new header version (exact)
- Verified by: TC-WFM-151
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-152 – Kind of a graph selects the tables
- Level: low   Subject: TaskRuntime
- Group: CG
- Text: Where a graph has the kind `context`, the Workflow management shall store its steps and connections in the context tables and its header with the kind `context`.
- Rationale: refines FR-57 for both kinds and HR-003; the member tables exist since A-98
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-12: a context graph's members are in `context_nodes` and `context_edges` under `<graph>/<local>`, none in `graph_nodes` (exact)
- Verified by: TC-WFM-152
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-153 – No kind means workflow
- Level: low   Subject: TaskRuntime
- Group: CG
- Text: Where a graph has no kind, the Workflow management shall treat it as a workflow graph.
- Rationale: ASM-5 of round 03; all callers before the kind existed save workflow graphs
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-13: a graph saved without a kind is stored with the kind `workflow` (exact)
- Verified by: TC-WFM-153
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-154 – Unknown kind refused
- Level: low   Subject: TaskRuntime
- Group: CG
- Text: If the kind of a graph is neither `workflow` nor `context`, then the Workflow management shall refuse the save and name the field `kind`.
- Rationale: refines FR-57 and D-404; the registry of kinds is the list of accepted kinds, today two
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-14: kind `swarm` is refused naming `kind` and nothing is stored (exact)
- Verified by: TC-WFM-154
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-155 – Identity and ends of a context graph
- Level: low   Subject: TaskRuntime
- Group: CG
- Text: When a context graph is saved, the Workflow management shall refuse a repeated step ID, a repeated connection ID or a connection to a missing step, and name the IDs.
- Rationale: refines FR-57; the rule set of the context kind is CONTEXT's decision (FR-75, ASM-4); until then identity and ends only
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-15: each of the three faults is refused naming the ID and writes nothing (exact)
- Binding: open
- Verified by: TC-WFM-155
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-156 – No workflow rules for a context graph
- Level: low   Subject: TaskRuntime
- Group: CG
- Text: When a context graph is saved, the Workflow management shall not apply the order, alternation, writer and stop-limit rules of workflow graphs.
- Rationale: refines D-404: the rule set follows the kind of the graph; context steps are categories, not data and processing steps
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-16: a context graph with two connected steps of the same category and a cycle is accepted by this check (exact; CONTEXT may add rules)
- Binding: open
- Verified by: TC-WFM-156
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-157 – Kind on reading
- Level: low   Subject: TaskRuntime
- Group: CG
- Text: When a context graph is read, the Workflow management shall return it with the kind `context`.
- Rationale: refines FR-57 and FR-48 (a graph is listed with its kind)
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-17: a context graph read at any version carries the kind `context`; a workflow graph keeps the shape it had before (exact)
- Verified by: TC-WFM-157
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-158 – Versions with who and when
- Level: low   Subject: TaskRuntime
- Group: RD
- Text: When the versions of a graph are asked, the Workflow management shall list every version, oldest first, each with the account that stored it and the time.
- Rationale: refines FR-57 and HR-003
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-18 (accepted case AC-001): a graph saved by three accounts lists versions 1 to 3 with the three accounts and a time each (exact)
- Verified by: TC-WFM-158
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-159 – A version as it was saved
- Level: low   Subject: TaskRuntime
- Group: RD
- Text: When a graph is read at a given version, the Workflow management shall return the steps, connections and header fields exactly as they were saved at that version.
- Rationale: refines FR-57 and HR-003; no version is deleted (REQ-GTB-013)
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-19 (accepted case AC-001): each of three saved versions reads back equal to what was saved, for a workflow graph and a context graph (exact)
- Verified by: TC-WFM-159
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-GTB-032 – Same refusals in both places
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall refuse the same records with the same rule on the files backend and on the database backend.
- Rationale: refines FR-57 and HR-003; MIA runs on a copy of files and a live database (FR-58)
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-20: the cases of AC-CORE-01 to AC-CORE-02, AC-CORE-06, AC-CORE-21, AC-CORE-14 and AC-CORE-15 give the same refusal on both backends (exact)
- Verified by: TC-GTB-032
- Status: Draft
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

## Assumptions

### ASM-001 – A graph ID has no slash
- Text: The caller never gives a graph an ID with a slash; the first slash of a record ID ends the graph ID.
- Rationale: confirmed by the owner (D-402); a graph ID with a slash is refused (REQ-GTB-031), so the assumption is a rule, and validation only checks that no existing graph has such an ID (the 15 converted graphs have none).
- Status: Draft

### ASM-002 – Step versions of an interrupted save may stay
- Text: A save interrupted after some writes may leave step or connection versions that no graph header names; they are harmless and not cleaned up.
- Rationale: accepted by the owner (D-402); `step_history` ignores them and a repeated save pins them again when equal (REQ-WFM-145, REQ-WFM-151).
- Status: Draft

## Traceability
| Requirement | Level | Parent | Subject (part) | Functions | Interfaces | Verified by | Status |
|---|---|---|---|---|---|---|---|
| REQ-GTB-029 | low | FR-60 | Persistence | – | IF-301 v2 | TC-GTB-029 | Draft |
| REQ-GTB-030 | low | FR-60 | Persistence | – | IF-301 v2 | TC-GTB-030 | Draft |
| REQ-GTB-031 | low | FR-60 | Persistence | – | IF-301 v2 | TC-GTB-031 | Draft |
| REQ-WFM-160 | low | FR-60 | TaskRuntime | – | IF-301 v2 | TC-WFM-160 | Draft |
| REQ-WFM-144 | low | FR-60 | TaskRuntime | – | IF-301 v2 | TC-WFM-144 | Draft |
| REQ-WFM-145 | low | FR-60 | TaskRuntime | – | IF-301 v2 | TC-WFM-145 | Draft |
| REQ-WFM-146 | low | NFR-16 | TaskRuntime | – | IF-301 v2 | TC-WFM-146 | Draft |
| REQ-WFM-147 | low | NFR-16 | TaskRuntime | – | IF-301 v2 | TC-WFM-147 | Draft |
| REQ-WFM-148 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-148 | Draft |
| REQ-WFM-149 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-149 | Draft |
| REQ-WFM-150 | low | NFR-16 | TaskRuntime | – | IF-301 v2 | TC-WFM-150 | Draft |
| REQ-WFM-151 | low | NFR-16 | TaskRuntime | – | IF-301 v2 | TC-WFM-151 | Draft |
| REQ-WFM-152 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-152 | Draft |
| REQ-WFM-153 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-153 | Draft |
| REQ-WFM-154 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-154 | Draft |
| REQ-WFM-155 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-155 | Draft |
| REQ-WFM-156 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-156 | Draft |
| REQ-WFM-157 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-157 | Draft |
| REQ-WFM-158 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-158 | Draft |
| REQ-WFM-159 | low | FR-57 | TaskRuntime | – | IF-301 v2 | TC-WFM-159 | Draft |
| REQ-GTB-032 | low | FR-57 | Persistence | – | IF-301 v2 | TC-GTB-032 | Draft |

## Won't (this time)
- A clean-up of unused step versions (owner, D-402).
- The rule set of a context graph beyond identity and ends (CONTEXT, FR-75).
- Moving, syncing and the same behaviour of files and database for whole stores (TRANSFER, FR-58, FR-59, FR-93).
