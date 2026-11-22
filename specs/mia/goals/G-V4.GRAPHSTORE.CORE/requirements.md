# Requirements: G-V4.GRAPHSTORE.CORE (low level, new and changed items)

**Moved at the merge (2026-11-22, D-408):** the 22 requirements are now in `specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md` (REQ-GTB-029 to 032) and `specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md` (REQ-WFM-144 to 161), section "Iteration 4", with the status Verified. The node files are the source from now on (they win over this file for the same ID); this file stays as the record of the goal.

**Top-level spec:** `specs/mia/goals/G-V4.GRAPHSTORE/top-level-spec.md`   **High-level spec:** `specs/mia/goals/G-V4.GRAPHSTORE.CORE/high-level-spec.md`   **Status:** Approved by the owner (2026-11-21)   **Plan baseline:** plan-baseline

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
| 3 | CG | Context graphs: the same save path for the second kind of graph (FR-57), the kind of a graph | REQ-WFM-152, REQ-WFM-153, REQ-WFM-154, REQ-WFM-155, REQ-WFM-161, REQ-WFM-156, REQ-WFM-157 |
| 4 | RD | Reading, history and both places: versions, who and when, a version as it was saved, the same refusals on files and database (FR-57) | REQ-WFM-158, REQ-WFM-159, REQ-GTB-032 |

## Requirements

### REQ-GTB-029 – Scoped ID of a step or connection
- Level: low   Subject: Persistence
- Group: SC
- Text: If a step or connection record is written under a non-empty ID not of the form `<graph id>/<local id>`, then the Graph tables shall refuse the record and name the rule `unscoped_id`.
- Rationale: refines FR-60 and HR-001; makes a step belong to exactly one graph by construction (D-368); amends the plain IDs of A-92 / REQ-GTB-021
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-01 (accepted case AC-002): a step written under `chat` is refused naming `unscoped_id`, under `lookup/chat` it is accepted (exact)
- Binding: fixed
- Verified by: TC-GTB-033
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03); text changed to 'a non-empty ID' (D-409), approved by the owner 2026-11-21

### REQ-GTB-030 – Header names only its own members
- Level: low   Subject: Persistence
- Group: SC
- Text: If a graph header names a step or connection whose record ID begins with the ID of another graph, then the Graph tables shall refuse the header and name the rule `unscoped_id`.
- Rationale: refines FR-60 and HR-001; a header of graph g must not pin a member of graph h
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-02: a header `g` naming `h/step` is refused naming `unscoped_id`; naming `g/step` it is accepted (exact)
- Binding: fixed
- Verified by: TC-GTB-034
- Status: Approved
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
- Binding: fixed
- Verified by: TC-GTB-035
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-160 – No slash in a graph ID
- Level: low   Subject: TaskRuntime
- Group: SC
- Text: If a graph with at least one step is saved under an ID that contains a slash, then the Workflow management shall refuse the save and name the rule `unscoped_id`.
- Rationale: refines HR-001 and ASM-001; the record ID of its steps would name another graph; seen in the prototype: a graph `look/up` is refused naming `look/up/a`
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-21: a graph with steps saved under the ID `look/up` is refused naming `unscoped_id` and nothing is stored (exact); a graph without steps is not caught by this rule (D-410)
- Binding: fixed
- Verified by: TC-WFM-178
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03); narrowed to graphs with steps, the slash caught through the steps as in the prototype (owner's choice D-410, Plan step 4, 2026-11-21)

### REQ-WFM-144 – Local IDs on reading
- Level: low   Subject: TaskRuntime
- Group: SC
- Text: When a graph is read, the Workflow management shall return the IDs of its steps and connections without the graph ID.
- Rationale: refines FR-60; the caller sees `step.write`, the store holds `lookup/step.write`
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-04: a graph saved with local IDs is read back with the same local IDs, also for the ends of connections (exact)
- Binding: fixed
- Verified by: TC-WFM-162
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-163
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-164
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-165
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-166
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-167
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-168
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-169
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-170
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-171
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-172
- Status: Approved
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
- Verified by: TC-WFM-173
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

### REQ-WFM-161 – An empty context graph is stored
- Level: low   Subject: TaskRuntime
- Group: CG
- Text: When a context graph without steps and connections is saved, the Workflow management shall store it as one header version.
- Rationale: refines FR-57; a context graph is built up step by step, so an empty one is a valid start; the owner kept this case of TC-WFM-173 and asked for its requirement (review 2026-11-21)
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-22: an empty context graph is accepted and has exactly one header version and no member record (exact)
- Binding: open
- Verified by: TC-WFM-173
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 3, 2026-11-21, new (from the review of TC-WFM-173); approved by the owner in the group review of CG, 2026-11-21

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
- Verified by: TC-WFM-174
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-175
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-176
- Status: Approved
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
- Binding: fixed
- Verified by: TC-WFM-177
- Status: Approved
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
- Binding: fixed
- Verified by: TC-GTB-036
- Status: Approved
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03)

## Assumptions

### ASM-001 – A graph ID has no slash
- Text: The caller never gives a graph an ID with a slash; the first slash of a record ID ends the graph ID.
- Rationale: confirmed by the owner (D-402); a graph ID with a slash is refused (REQ-GTB-031), so the assumption is a rule, and validation only checks that no existing graph has such an ID (the 15 converted graphs have none).
- Status: Approved

### ASM-002 – Step versions of an interrupted save may stay
- Text: A save interrupted after some writes may leave step or connection versions that no graph header names; they are harmless and not cleaned up.
- Rationale: accepted by the owner (D-402); `step_history` ignores them and a repeated save pins them again when equal (REQ-WFM-145, REQ-WFM-151).
- Status: Approved

## Traceability
| Requirement | Level | Parent | Subject (part) | Functions | Interfaces | Verified by | Status |
|---|---|---|---|---|---|---|---|
| REQ-GTB-029 | low | FR-60 | Persistence | – | IF-301 v3 | TC-GTB-033 | Approved |
| REQ-GTB-030 | low | FR-60 | Persistence | – | IF-301 v3 | TC-GTB-034 | Approved |
| REQ-GTB-031 | low | FR-60 | Persistence | – | IF-301 v3 | TC-GTB-035 | Approved |
| REQ-WFM-160 | low | FR-60 | TaskRuntime | – | IF-301 v3 | TC-WFM-178 | Approved |
| REQ-WFM-144 | low | FR-60 | TaskRuntime | – | IF-301 v3 | TC-WFM-162 | Approved |
| REQ-WFM-145 | low | FR-60 | TaskRuntime | – | IF-301 v3 | TC-WFM-163 | Approved |
| REQ-WFM-146 | low | NFR-16 | TaskRuntime | – | IF-301 v3 | TC-WFM-164 | Approved |
| REQ-WFM-147 | low | NFR-16 | TaskRuntime | – | IF-301 v3 | TC-WFM-165 | Approved |
| REQ-WFM-148 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-166 | Approved |
| REQ-WFM-149 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-167 | Approved |
| REQ-WFM-150 | low | NFR-16 | TaskRuntime | – | IF-301 v3 | TC-WFM-168 | Approved |
| REQ-WFM-151 | low | NFR-16 | TaskRuntime | – | IF-301 v3 | TC-WFM-169 | Approved |
| REQ-WFM-152 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-170 | Approved |
| REQ-WFM-153 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-171 | Approved |
| REQ-WFM-154 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-172 | Approved |
| REQ-WFM-155 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-173 | Approved |
| REQ-WFM-161 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-173 | Approved |
| REQ-WFM-156 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-174 | Approved |
| REQ-WFM-157 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-175 | Approved |
| REQ-WFM-158 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-176 | Approved |
| REQ-WFM-159 | low | FR-57 | TaskRuntime | – | IF-301 v3 | TC-WFM-177 | Approved |
| REQ-GTB-032 | low | FR-57 | Persistence | – | IF-301 v3 | TC-GTB-036 | Approved |

## Won't (this time)
- A clean-up of unused step versions (owner, D-402).
- The rule set of a context graph beyond identity and ends (CONTEXT, FR-75).
- Moving, syncing and the same behaviour of files and database for whole stores (TRANSFER, FR-58, FR-59, FR-93).

## Approval
Reviewed item by item with the owner on 2026-11-21 (review log: `review-log.md`). The approval of the whole document is the owner's: tick the box (in Emacs `C-c C-c` on the line) or say so in the chat; the agent then sets the status to Approved and never before.

- [x] Approved by Stefan Reiterer (owner). Date: 2026-11-21 (said in the chat, "approved")
