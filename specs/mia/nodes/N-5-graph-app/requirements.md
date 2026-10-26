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
