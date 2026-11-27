# Requirements: Graph app (N-5, high level)

**Parent:** `specs/mia/requirements.md` (top level N-0)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

An independent add-on tool that shows and edits workflow and context graphs through the backend API IF-104 (no database access of its own). Integrated last. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-GA-001 – Graphs as nodes and edges
- Level: high   Subject: GraphApp
- Text: The Graph app shall show a workflow graph as nodes and edges.
- Rationale: refines FR-22
- Parent: FR-22
- Priority: Should
- Verification method: Demonstration
- Acceptance criterion: AC-16: a recorded library entry of the lookup is drawn with all its nodes and edges
- Verified by: TC-GA-001
- Status: Approved
- History: –

### REQ-GA-002 – Edit as JSON
- Level: high   Subject: GraphApp
- Text: When a logged-in user edits a node or an edge, the Graph app shall present it as a JSON dictionary of text data.
- Rationale: refines FR-22
- Parent: FR-22
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: a node edited as JSON is saved as the edited dictionary (exact)
- Verified by: TC-GA-002
- Status: Approved
- History: –

### REQ-GA-003 – Graph rules before saving
- Level: high   Subject: GraphApp
- Text: When a user saves, the Graph app shall check the identity of nodes, that no two data nodes are adjacent, that there is no cycle and that every session node has a stopping criterion, and name a broken rule.
- Rationale: refines FR-22, FR-7
- Parent: FR-22, FR-7
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-27: each violation is refused with the rule named, in the app and again by the backend
- Verified by: TC-GA-003
- Status: Approved
- History: –

### REQ-GA-004 – Versions, history and diff
- Level: high   Subject: GraphApp
- Text: The Graph app shall save every edit as a new version and show the version history, a diff and the restore of a former version.
- Rationale: refines FR-22
- Parent: FR-22
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: a former version is restored and saved as a new version
- Verified by: TC-GA-004
- Status: Approved
- History: –

### REQ-GA-005 – Work through the backend API
- Level: high   Subject: GraphApp
- Text: The Graph app shall read and write workflows and context graphs only through the workflow and graph API IF-104.
- Rationale: refines FR-22, CON-7
- Parent: FR-22, CON-7
- Priority: Should
- Verification method: Inspection, Test
- Acceptance criterion: AC-15: the Graph app imports no database driver (exact); every call goes to IF-104
- Verified by: TC-GA-005
- Status: Approved
- History: –

### REQ-GA-006 – Context graphs edited
- Level: high   Subject: GraphApp
- Text: The Graph app shall let a logged-in user adapt a context graph, every change a new version.
- Rationale: refines FR-30
- Parent: FR-30
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: a context graph edit appears as a new version
- Verified by: TC-GA-006
- Status: Approved
- History: –

### REQ-GA-007 – Login required
- Level: high   Subject: GraphApp
- Text: The Graph app shall require a login that the backend authenticates and use the backend session for every call.
- Rationale: refines FR-21, NFR-6
- Parent: FR-21, NFR-6
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-14: a request without a session shows the login only (exact); the Graph app holds no password check of its own
- Verified by: TC-GA-007
- Status: Approved
- History: –

### REQ-GA-008 – Library export and seed
- Level: high   Subject: GraphApp
- Text: The Graph app shall offer the export of the library to files and the seed from files.
- Rationale: refines FR-22
- Parent: FR-22
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-16: export then seed gives identical entries (exact)
- Verified by: TC-GA-008
- Status: Approved
- History: –

### REQ-GA-009 – Plain stack with a vendored library
- Level: high   Subject: GraphApp
- Text: The Graph app shall be plain HTML and JavaScript with a vendored graph library and no build step.
- Rationale: refines CON-3, FR-22
- Parent: CON-3, FR-22
- Priority: Should
- Verification method: Inspection
- Acceptance criterion: AC-20: no bundler files; the library is in the repository
- Verified by: TC-GA-009
- Status: Approved
- History: –

### REQ-GA-010 – No outside request
- Level: high   Subject: GraphApp
- Text: The Graph app shall load no resource from outside the host.
- Rationale: refines NFR-5
- Parent: NFR-5
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-5: a browser test finds 0 requests outside the host
- Verified by: TC-GA-010
- Status: Approved
- History: –

### REQ-GA-011 – Own container
- Level: high   Subject: GraphApp
- Text: The Graph app shall start as its own container alone and by the compose stack.
- Rationale: refines NFR-9
- Parent: NFR-9
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-29: starts alone against the mock of IF-104 and in the stack
- Verified by: TC-GA-011
- Status: Approved
- History: –

## Iteration 4 (goal G-V4.VIEW, graph viewer and the IF-104 v2 backend; moved at the merge 2026-11-25)
Requirements of the subgoal G-V4.VIEW (goal record `specs/mia/goals/G-V4.VIEW/`: plan, test requirements TR-VIEW-001 to 021, verification report). Verified 2026-11-24 (both boxes ticked by the owner); Verify findings decided in D-501: V-1, V-2, V-4, V-5, V-8, V-9, V-10, V-13 fixed, V-15 closed by the owner's image build, V-3 handed to G-V4.GRAPHSTORE.TRANSFER, V-6, V-7, V-11, V-12, V-14 accepted; the specification points of the merge in D-502. The routes are offered through IF-104 v2 (`contracts/`, A-171, A-174), the record tables through IF-302 v15 (A-172).

Terms (store setting, owner, record of changes, entry, what cannot be drawn): see the section "Terms of G-V4.VIEW" in `specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md`.

## Groups of G-V4.VIEW
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 7 | FL | Frame and look: the owner's layout, the empty areas, the main app's tokens, light and dark, status bar, store shown (D-425, D-430, D-431, HR-009, NFR-14) | REQ-GA-012, REQ-GA-013, REQ-GA-014, REQ-GA-015, REQ-GA-016, REQ-GA-017, REQ-GA-018 |
| 8 | LS | List and opening: list, filter, open, not logged in, store down (FR-48, NFR-12, AC-009, AC-035) | REQ-GA-019, REQ-GA-020, REQ-GA-021, REQ-GA-022, REQ-GA-023, REQ-GA-045 |
| 9 | PI | The picture: every step and connection, what cannot be drawn, kinds, marks, other kinds of graph, text stays text (FR-49, FR-50, FR-54, D-426, AC-010 to AC-012) | REQ-GA-024, REQ-GA-025, REQ-GA-026, REQ-GA-027, REQ-GA-028, REQ-GA-029 |
| 10 | AS | Arrangement and settings: saved arrangement, fixed seed, moved step, layered reset, settings (FR-52, FR-53, HR-003, AC-014, AC-015) | REQ-GA-030, REQ-GA-031, REQ-GA-032, REQ-GA-033, REQ-GA-034, REQ-GA-035 |
| 11 | LC | Left column and history: selection, trust in words, history list, earlier versions (FR-51, FR-55, AC-013, AC-016) | REQ-GA-036, REQ-GA-044, REQ-GA-037, REQ-GA-038, REQ-GA-039, REQ-GA-040 |
| 12 | QA | Keyboard, nothing from outside, nothing written (NFR-13, NFR-14, HR-005) | REQ-GA-041, REQ-GA-042, REQ-GA-043 |

### REQ-GA-012 – The whole frame
- Level: low   Subject: GraphApp
- Group: FL
- Text: The Graph app shall show the seven areas of the owner's layout: graph list, search band, other things, left column, picture, actions row, history and replay row, status bar.
- Rationale: the owner's layout (D-425, `../G-V4/layout.drawio`); VIEW builds the whole frame now
- Parent: FR-51
- Priority: Must
- Verification method: Test
- Acceptance criterion: in Firefox at 1280 × 800 each of the seven areas is present and visible by its label (exact)
- Verified by: TC-GA-033
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-013 – Areas of later subgoals
- Level: low   Subject: GraphApp
- Group: FL
- Text: The Graph app shall show each area that a later subgoal fills as an empty area with one line naming that subgoal and with no control in it.
- Rationale: D-430 (5): no dead buttons; the actions row (EDIT), the replay buttons and start-with-input (REPLAY, RUN), the search band (later slice, FR-96) and the chat
- Parent: FR-51
- Priority: Must
- Verification method: Test
- Acceptance criterion: the actions row, the replay part, the start-with-input part and the search band each hold one line naming its subgoal and no button, field or link (exact)
- Verified by: TC-GA-033
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-014 – The main app's design tokens
- Level: low   Subject: GraphApp
- Group: FL
- Text: The Graph app shall load a copy of the main app's design tokens file that is identical byte for byte to `templates/static/chat/tokens.css`.
- Rationale: HR-009, D-431: the main app's look; a copy so the graph container starts alone (REQ-GA-011)
- Parent: HR-009
- Priority: Must
- Verification method: Test
- Acceptance criterion: the copy and the main app's file have the same sha256 (exact)
- Verified by: TC-GA-031
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-015 – Styles only from the tokens
- Level: low   Subject: GraphApp
- Group: FL
- Text: The Graph app's own styles shall take every colour, font, spacing, radius and shadow from the variables of the design tokens.
- Rationale: HR-009: one look, no drift from the main app
- Parent: HR-009
- Priority: Must
- Verification method: Test
- Acceptance criterion: the page's own style sheets contain no colour literal, font name or pixel radius outside `var(--…)` uses (exact, by a scan of the files)
- Verified by: TC-GA-032
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-016 – Light and dark
- Level: low   Subject: GraphApp
- Group: FL
- Text: The Graph app shall show the theme chosen in the main app on the same device (dark, light, or auto, which follows the system's light or dark setting; no choice or an unknown value counts as auto) through the themes of the design tokens, the picture included, also when the choice changes while the page is open.
- Rationale: NFR-14 and HR-009; the picture's colours are read from the tokens (D-431); one theme choice for the whole app (D-503: on the owner's host the system is light, so a page that follows only the system never shows dark)
- Parent: NFR-14
- Priority: Must
- Verification method: Test
- Acceptance criterion: in Firefox without a saved choice, with the colour scheme light and then dark, the page background and the step label colour equal the token values of that theme (exact); with the saved choice dark or light they equal those of the chosen theme under either colour scheme, and with auto or an unknown value those of the colour scheme (exact); a choice saved in another page of the same origin re-colours the open page without a reload
- Verified by: TC-GA-034, TC-GA-040
- Status: Approved
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").; changed by A-176 (D-503, 2026-11-26): follows the main app's theme choice `mia.theme`, auto as before (the owner's look at Deploy); TC-GA-040 added; Approved confirmed in Emacs on 2026-11-27

### REQ-GA-017 – Graph status
- Level: low   Subject: GraphApp
- Group: FL
- Text: The Graph app shall show in the status bar the shown graph's ID, the shown version, who stored it and when, and that it is read-only.
- Rationale: D-425 layout: graph status; the rule report and unsaved changes come with EDIT
- Parent: FR-55
- Priority: Must
- Verification method: Test
- Acceptance criterion: opening cp2.multi shows `cp2.multi`, version 4, ben, its time and `read-only` in the status bar (exact)
- Verified by: TC-GA-021
- Status: Verified
- Detail: The version reads `version n` for the current one and `version n of m` for an earlier one.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour kept from the code written down (Verify V-14, accepted D-501) (item 9).

### REQ-GA-018 – Which store is shown
- Level: low   Subject: GraphApp
- Group: FL
- Text: The Graph app shall show under other things which store it reads and whether that store answers, read-only.
- Rationale: D-430 (6): the store is chosen by configuration and only shown; IF-104 v2 route 2
- Parent: FR-48
- Priority: Must
- Verification method: Test
- Acceptance criterion: with the store route answering `files` and reachable the entry reads files and reachable, and it offers no control (exact)
- Verified by: TC-GA-021
- Status: Verified
- Detail: The store part has no visible heading (D-459).
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour the owner kept at Verify written down (D-501).

### REQ-GA-019 – The list of graphs
- Level: low   Subject: GraphApp
- Group: LS
- Text: The Graph app shall list every graph that IF-104 v2 names, each with its ID, kind, version and numbers of steps and connections.
- Rationale: FR-48; the kind is named for every graph, also an unknown one
- Parent: FR-48
- Priority: Must
- Verification method: Test
- Acceptance criterion: on the JS mock with cp2.multi and sample.code both are listed with kind, version and counts (exact)
- Verified by: TC-GA-017 (witness of AC-009)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-020 – Filter by name or description
- Level: low   Subject: GraphApp
- Group: LS
- Text: When the owner types into the list filter, the Graph app shall show only the graphs whose ID or description contains every typed word, ignoring case.
- Rationale: FR-48 and AC-009 (name or description)
- Parent: FR-48
- Priority: Must
- Verification method: Test
- Acceptance criterion: typing `chat` keeps the graphs whose ID or description holds chat; typing `CODE step` keeps sample.code (exact)
- Verified by: TC-GA-018 (witness of AC-009)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-021 – Opening a graph
- Level: low   Subject: GraphApp
- Group: LS
- Text: When the owner chooses a graph in the list, the Graph app shall draw its current version.
- Rationale: FR-48
- Parent: FR-48
- Priority: Must
- Verification method: Test
- Acceptance criterion: choosing cp2.multi draws version 4 (exact)
- Verified by: TC-GA-017 (witness of AC-009)
- Status: Verified
- Relaxed: TD-94
- Target: the requirement as written, without the known gap (answers that arrive out of order when two graphs are opened quickly are not guarded (V-14 item 11); see TD-94)
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): Relaxed TD-94.

### REQ-GA-022 – Not logged in
- Level: low   Subject: GraphApp
- Group: LS
- Text: If IF-104 v2 answers that no one is logged in, then the Graph app shall show no graph and ask the person to log in through the main app.
- Rationale: NFR-12 and AC-035; one login is enough (the session cookie of the main app)
- Parent: NFR-12
- Priority: Must
- Verification method: Test
- Acceptance criterion: with the mock answering 401 the page shows no list and no picture and a link to the main app's login (exact)
- Verified by: TC-GA-019 (witness of AC-035)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-023 – The store does not answer
- Level: low   Subject: GraphApp
- Group: LS
- Text: If IF-104 v2 answers that the store cannot be reached, then the Graph app shall say so and keep what it already shows.
- Rationale: FR-95 (page side for reading); IF-104 v2 503 `store_unreachable`
- Parent: FR-48
- Priority: Must
- Verification method: Test
- Acceptance criterion: with the mock unreachable after opening cp2.multi the picture stays and a line says the store does not answer (exact)
- Verified by: TC-GA-020
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-045 – Another failure is said
- Level: low   Subject: GraphApp
- Group: LS
- Text: If IF-104 v2 answers with an error other than "not logged in" or "store does not answer", or does not answer at all, then the Graph app shall say in one line of the status band that the graph could not be loaded, with the reason, and keep what it already shows.
- Rationale: Verify V-11: a 404 between list and opening, a 500 or MIA down show nothing today; the owner wants a notice (D-502 (2)); not met yet, deferred (TD-91)
- Parent: FR-48
- Priority: Should
- Verification method: Test
- Acceptance criterion: with the mock answering 404 for a listed graph, 500, and no answer, the band says each time that the graph could not be loaded and names the reason; the picture shown before stays (exact)
- Verified by: deferred (TD-91)
- Status: Deferred
- Relaxed: TD-91
- Target: the requirement as written (see TD-91)
- History: D-502 (merge of G-V4.VIEW, 2026-11-25), new (Verify V-11); deferred to the Plan of G-V4.EDIT (TD-91)

### REQ-GA-024 – Every step and connection
- Level: low   Subject: GraphApp
- Group: PI
- Text: When a graph is opened, the Graph app shall draw every step and every connection of it, each connection with its direction.
- Rationale: FR-49
- Parent: FR-49
- Priority: Must
- Verification method: Test
- Acceptance criterion: sample.code is drawn with 7 steps and 6 arrows (exact)
- Verified by: TC-GA-022 (witness of AC-010)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-025 – What cannot be drawn
- Level: low   Subject: GraphApp
- Group: PI
- Text: When IF-104 v2 names a connection to a missing step, the Graph app shall draw that connection dashed to a marked missing step and name the problem beside the picture.
- Rationale: FR-49 ("nothing is dropped silently") and AC-010
- Parent: FR-49
- Priority: Must
- Verification method: Test
- Acceptance criterion: sample.broken shows e2 dashed to a step marked missing step `var.gone` and the problem named in the left column (exact)
- Verified by: TC-GA-023 (witness of AC-010)
- Status: Verified
- Detail: A step ID used twice is drawn once. The stored text shown for a missing step is `{id, missing: true}`.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour the owner kept at Verify written down (D-501); behaviour kept from the code written down (Verify V-14, accepted D-501) (item 2).

### REQ-GA-026 – Kinds of step at a glance
- Level: low   Subject: GraphApp
- Group: PI
- Text: The Graph app shall draw data steps as ellipses, processing steps as boxes and loop-controlling steps as hexagons, each with its kind in words.
- Rationale: FR-50 ("without relying on colour alone") and AC-011; prototype round 02 (step-marks.js)
- Parent: FR-50
- Priority: Must
- Verification method: Test
- Acceptance criterion: in sample.code var.in is an ellipse labelled data, step.check a box labelled processing, loop.review a hexagon labelled loop-controlling (exact)
- Verified by: TC-GA-024 (witness of AC-011)
- Status: Verified
- Detail: The label has two lines: the step's ID, then its kind and marks, joined by a middle dot.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour the owner kept at Verify written down (D-501).

### REQ-GA-027 – A mark only where attention is needed
- Level: low   Subject: GraphApp
- Group: PI
- Text: The Graph app shall put a mark of at most one word on a processing or loop-controlling step that is untrusted, changed since trusted or holds code, and no mark on any other step.
- Rationale: D-426: minimal marks in the picture, trusted steps plain; FR-50, AC-011
- Parent: FR-50
- Priority: Must
- Verification method: Test
- Acceptance criterion: in sample.code the hostile step carries the marks untrusted and code; step.check and loop.review (trusted) carry none (exact)
- Verified by: TC-GA-024 (witness of AC-011)
- Status: Verified
- Relaxed: TD-92
- Target: the requirement as written, without the known gap (the dashed `--danger` border of an untrusted step looks like a missing step's dashes (V-14 item 1); see TD-92)
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): Relaxed TD-92.

### REQ-GA-028 – A graph of another kind
- Level: low   Subject: GraphApp
- Group: PI
- Text: When a graph is not a workflow graph, the Graph app shall draw its steps in one neutral shape with their type in words, without trust marks, read-only.
- Rationale: D-425 C/D: context graphs drawn generically, an unknown kind plain; FR-48, FR-50
- Parent: FR-50
- Priority: Must
- Verification method: Test
- Acceptance criterion: a context graph and a graph of kind `swarm` are drawn with boxes labelled by type, no marks, and their kind named in the status bar (exact)
- Verified by: TC-GA-025
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-029 – Stored text stays text
- Level: low   Subject: GraphApp
- Group: PI
- Text: The Graph app shall show every ID, name and value of a graph as plain text and never as markup, a link or code it runs.
- Rationale: FR-54, AC-012, THR-011; the page builds its elements with text only
- Parent: FR-54
- Priority: Must
- Verification method: Test
- Acceptance criterion: sample.code's step `<img src=x onerror=alert(1)> step "quoted" & more` appears as that text in the picture, the step list and the left column, no image element exists and no dialog opens (exact)
- Verified by: TC-GA-035 (witness of AC-012)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-030 – The saved arrangement
- Level: low   Subject: GraphApp
- Group: AS
- Text: When a graph with a saved arrangement is opened, the Graph app shall place its steps where the arrangement puts them.
- Rationale: FR-52 and HR-003
- Parent: FR-52
- Priority: Must
- Verification method: Test
- Acceptance criterion: cp2.multi with var.in saved at 10, -3 opens with var.in at 10, -3 (exact)
- Verified by: TC-GA-026 (witness of AC-014)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-031 – The same picture every time
- Level: low   Subject: GraphApp
- Group: AS
- Text: When a graph without a saved arrangement is opened, the Graph app shall arrange it with one fixed solver and one fixed seed.
- Rationale: HR-003 (D-436: replaces the "physics off" line of the old test); FR-52
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: opening sample.code twice gives the same place for every step (exact, rounded to whole pixels)
- Verified by: TC-GA-036
- Status: Verified
- Detail: Fixed layout numbers: Barnes-Hut with `avoidOverlap` 0.6, 400 stabilisation iterations, then `fit`.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour kept from the code written down (Verify V-14, accepted D-501) (item 6).

### REQ-GA-032 – A moved step stays
- Level: low   Subject: GraphApp
- Group: AS
- Text: When the owner drags a step, the Graph app shall keep it where it was dropped while the graph is open.
- Rationale: FR-52; nothing is saved (saving the arrangement is EDIT's page side)
- Parent: FR-52
- Priority: Must
- Verification method: Test
- Acceptance criterion: after dragging step.check by 100 px it stays there and nothing is sent to IF-104 v2 (exact)
- Verified by: TC-GA-037 (witness of AC-014)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-033 – The layered reset
- Level: low   Subject: GraphApp
- Group: AS
- Text: When the owner asks for the layered arrangement, the Graph app shall place the steps in layers so that every connection points forward.
- Rationale: FR-52 (the reproducible reset) and AC-014
- Parent: FR-52
- Priority: Must
- Verification method: Test
- Acceptance criterion: after the reset every connection of sample.code goes from a lower to a higher layer (exact)
- Verified by: TC-GA-027 (witness of AC-014)
- Status: Verified
- Detail: Layers are 220 px apart. The reset is offered inside the settings popover.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour kept from the code written down (Verify V-14, accepted D-501) (items 6, 7).

### REQ-GA-034 – Settings in one place
- Level: low   Subject: GraphApp
- Group: AS
- Text: When the owner changes the connection style (rounded or straight) or the automatic arrangement (on or off) in the one settings place, the Graph app shall redraw the picture at once.
- Rationale: FR-53 and AC-015
- Parent: FR-53
- Priority: Must
- Verification method: Test
- Acceptance criterion: switching to straight and arrangement off changes the drawn connections and stops the movement without reloading; moved steps stay (exact)
- Verified by: TC-GA-028, TC-GA-037 (witness of AC-015)
- Status: Verified
- Detail: The view settings sit in the picture's header (D-458). With "arrangement on" the picture settles once, then physics is switched off.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour the owner kept at Verify written down (D-501); behaviour kept from the code written down (Verify V-14, accepted D-501) (item 5).

### REQ-GA-035 – Settings remembered
- Level: low   Subject: GraphApp
- Group: AS
- Text: The Graph app shall remember the settings on the device for the next visit and work with its defaults when they cannot be kept.
- Rationale: FR-53 and AC-015; defaults rounded connections and arrangement on (prototype)
- Parent: FR-53
- Priority: Must
- Verification method: Test
- Acceptance criterion: after a reload the settings are still straight and off; with the storage blocked the page opens with rounded and on (exact)
- Verified by: TC-GA-028 (witness of AC-015)
- Status: Verified
- Detail: The settings are kept under the key `mia-graph-viewer-settings`; a stored value that is not valid is dropped silently and its default used.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour kept from the code written down (Verify V-14, accepted D-501) (item 3).

### REQ-GA-036 – Content of the selection
- Level: low   Subject: GraphApp
- Group: LC
- Text: When the owner selects a step or a connection, the Graph app shall show in the left column its known values as labelled read-only fields and its full stored text.
- Rationale: FR-51 and AC-013
- Parent: FR-51
- Priority: Must
- Verification method: Test
- Acceptance criterion: selecting step.check shows its kind and toolbox ID as fields and its stored text; clicking empty space empties the column (exact)
- Verified by: TC-GA-029 (witness of AC-013)
- Status: Verified
- Detail: The drawing interface reports a selection through `onSelect`.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour the owner kept at Verify written down (D-501).

### REQ-GA-044 – Nothing selected
- Level: low   Subject: GraphApp
- Group: LC
- Text: When the owner selects nothing, the Graph app shall leave the left column empty.
- Rationale: FR-51 ("selecting nothing clears it") and AC-013; split from REQ-GA-036
- Parent: FR-51
- Priority: Must
- Verification method: Test
- Acceptance criterion: after selecting step.check, a click on empty space empties the left column (exact)
- Verified by: TC-GA-029 (witness of AC-013)
- Status: Verified
- Detail: The left column then reads "Nothing selected."
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour kept from the code written down (Verify V-14, accepted D-501) (item 9).

### REQ-GA-037 – Trust and lifecycle in words
- Level: low   Subject: GraphApp
- Group: LC
- Text: When the owner selects a processing or loop-controlling step, the Graph app shall show its trust, lifecycle, reason and whether it changed since trusted or holds code in the left column.
- Rationale: D-426: the full trust and lifecycle text is in the left column; FR-50
- Parent: FR-50
- Priority: Must
- Verification method: Test
- Acceptance criterion: selecting the hostile step of sample.code shows untrusted, no lifecycle, "it is not in the toolbox", not changed, holds code (exact)
- Verified by: TC-GA-029
- Status: Verified
- Relaxed: TD-93
- Target: the requirement as written, without the known gap (a transform step without trust is marked untrusted, but its trust fields are hidden in the left column (V-14 item 10); see TD-93)
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): Relaxed TD-93.

### REQ-GA-038 – The history list
- Level: low   Subject: GraphApp
- Group: LC
- Text: When the owner opens the history of a graph, the Graph app shall list its versions newest first with who stored each and when, the current one marked.
- Rationale: FR-55 and AC-016
- Parent: FR-55
- Priority: Must
- Verification method: Test
- Acceptance criterion: cp2.multi lists 4, 3, 2, 1 with ben, anna, ben, anna, version 4 marked current (exact)
- Verified by: TC-GA-030 (witness of AC-016)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-039 – An earlier version
- Level: low   Subject: GraphApp
- Group: LC
- Text: When the owner chooses an entry of the history, the Graph app shall draw that version read-only and name it with its time in the status bar.
- Rationale: FR-55 and AC-016
- Parent: FR-55
- Priority: Must
- Verification method: Test
- Acceptance criterion: choosing version 2 draws the step naming t2 and the status bar reads version 2 with its time (exact)
- Verified by: TC-GA-030 (witness of AC-016)
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-040 – Previous and next
- Level: low   Subject: GraphApp
- Group: LC
- Text: The Graph app shall let the owner step from the shown version to the next older and the next newer one, and offer no step beyond the oldest or the newest.
- Rationale: FR-55 and AC-016
- Parent: FR-55
- Priority: Must
- Verification method: Test
- Acceptance criterion: from version 2, previous shows 1 and next shows 3; at version 1 previous is not offered (exact)
- Verified by: TC-GA-030 (witness of AC-016)
- Status: Verified
- Detail: Previous and next are offered only after the history is opened.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour kept from the code written down (Verify V-14, accepted D-501) (item 8).

### REQ-GA-041 – By keyboard
- Level: low   Subject: GraphApp
- Group: QA
- Text: The Graph app shall let the owner pick a graph, move from step to step, select a step and open the settings with the keyboard alone.
- Rationale: NFR-14; a step list beside the picture serves the keyboard (prototype round 02)
- Parent: NFR-14
- Priority: Must
- Verification method: Test
- Acceptance criterion: in Firefox with key presses only the owner opens sample.code, reaches step.check, selects it (its fields appear) and opens the settings (exact)
- Verified by: TC-GA-038
- Status: Verified
- Detail: The arrow keys also move through the graph list.
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge"); D-502 (merge of G-V4.VIEW, 2026-11-25): behaviour kept from the code written down (Verify V-14, accepted D-501) (item 4).

### REQ-GA-042 – Nothing from outside
- Level: low   Subject: GraphApp
- Group: QA
- Text: The Graph app shall request nothing from an address other than its own origin.
- Rationale: NFR-13 and REQ-GA-010; the vendored library and the copied tokens are served by the graph container
- Parent: NFR-13
- Priority: Must
- Verification method: Test
- Acceptance criterion: in Firefox, opening sample.code, selecting steps, opening the history and the settings makes no request to another origin (exact)
- Verified by: TC-GA-039
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GA-043 – The page writes nothing
- Level: low   Subject: GraphApp
- Group: QA
- Text: The Graph app shall send no request that changes a graph, an arrangement or a version.
- Rationale: HR-005 and NFR-12; the write routes of IF-104 v2 are used from EDIT on
- Parent: HR-005
- Priority: Must
- Verification method: Test
- Acceptance criterion: during a session of opening, dragging, settings and history the page sends only GET requests to IF-104 v2 (exact)
- Verified by: TC-GA-039
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track B; basis: prototype round 02 R6, R7, the owner's layout D-425, D-426, D-430, D-431, D-436); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").
