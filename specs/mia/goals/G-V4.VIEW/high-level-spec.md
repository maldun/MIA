# High-Level Specification: G-V4.VIEW – the graph app's frame and a read-only viewer

**Status:** Approved by the owner (2026-11-22, D-432); open points P-1 to P-3 decided (D-430), look and feel D-431
**Top-level spec:** `top-level-spec.md` of this folder (FR-48 to FR-55, NFR-10 to NFR-14)   **Owner:** Stefan Reiterer   **Date:** 2026-11-22
**Basis:** the design review `design-review.md` (D-425, D-426), the owner's layout `../G-V4/layout.drawio`, D-430 (goal update, split, IF-104 v1, browser checks, empty areas, store choice), prototype round 02 on `prototype/g-v4` (validated 2026-11-20) with the reuse map rows R5, R6, R7, R10, R11, the accepted cases AC-009 to AC-016 and AC-035 (`../G-V4/accepted-cases.md`), CORE as verified (D-414).

## 1. Big parts and technology
VIEW adds one interface version (IF-104 v2) with all its routes served by the real backend (D-430 (7)), a new page in the graph app's container that shows the whole frame of the owner's layout in the main app's look (D-431), and two record tables (the saved arrangement, the record of changes). The page offers no write action; the write routes are there for EDIT and REPLAY.

| Part (node) | Purpose | Technology | New / existing | Decided in |
|---|---|---|---|---|
| N-5 Graph app (page) | the frame (top band, left column, picture, actions, history and replay row, graph status) and the viewer inside it | plain HTML and JavaScript modules, vendored vis-network 10.1.2, no build step (REQ-GA-009); the 15 small page modules of the prototype kept with their node tests (R6), the shell written again (R7) | existing node, new page | D-425, R6, R7 |
| N-2.1 API and accounts | all routes of IF-104 v2 under the existing session: read, check, save, restore, arrangement, changes, status | a Flask blueprint in the MIA backend beside v1, adapted from `graph_proto_app.py` (R5), on CORE's `GraphModel`; the check route and the save path ask IF-301 v4 once RULES is merged | new module in an existing node | R5, D-430 (7), (8) |
| N-3.1 / N-3.2 store | the stored graphs and their versions, from files or from PostgreSQL | CORE's `GraphModel` on the file or the PostgreSQL backend of IF-102, chosen by a store setting; the release image gets `requirements-db.txt` (D-430 (9)) | existing | CORE, D-430 |
| N-3.1 record tables `arrangements`, `graph_changes` | the saved arrangement of a graph; the write-once record of changes per kept version | IF-302 (amendment): one arrangement record per graph, no version; change records written once, append-only, moving with the graph; carried by TRANSFER | new tables | D-425 B, D-430 (7), prototype round 02 |
| compose stack and Caddy | one origin and one session for page and API | `/graph/` to the graph container, the rest to MIA (`deploy/Caddyfile`, D-133) | existing, unchanged | D-133 |

### Key decisions and alternatives
| Decision | Alternatives considered | Rationale | Record |
|---|---|---|---|
| The page takes the main app's look: `templates/static/chat/tokens.css` copied unchanged into `graph_app/`, kept identical by a check; the page's own styles use only those tokens (glass panels, accent, themes dark, light, auto); the picture's colours are read from the tokens | link the main app's file across containers; an own design | the owner asked for the main app's look; a copy keeps the container able to start alone (REQ-GA-011), the check stops drift | D-431 |
| All IF-104 v2 routes are real in VIEW; the page writes nothing; write routes owner only (NFR-19) | read side real, rest on mocks | the owner's choice after the consequences were named | D-430 (7) |
| VIEW's plan writes all of IF-104 v2 as one amendment (A-171): read side plus check, save, restore, arrangement, changes; Python and JS mocks and a contract suite | only the read side now | the interface is shared by VIEW, EDIT, REPLAY and CONTEXT and frozen at G-V4 (D-368); writing it once avoids a second amendment round | D-425 A |
| v2 beside v1 under `/api/v2`; v1 routes, mocks and contract suite untouched, retired by the subgoal that replaces their last user | v2 replaces v1 now | no protected v1 test changes in VIEW | D-430 |
| Problems beside the picture are only what cannot be drawn (a connection to a missing step and the like); rule reports belong to EDIT's check route | show the RULES report in VIEW | FR-49 asks for what cannot be drawn; the rule check is the graph status of EDIT | D-425 A |
| Arrangement: a saved one is used; otherwise physics with a fixed seed and one fixed solver, so a graph settles the same way on every opening; the layered arrangement is the reset | physics off (REQ-GA-001 test today); a random seed | FR-52 "settles by itself" and "the same each time"; REQ-GA-001's "physics off" text is amended | D-425 B, D-377 |
| The look per kind of graph in a page-side table; an unknown kind drawn as plain steps and connections, read-only; context graphs drawn generically (type in words, one neutral shape, no trust marks) | an IF-104 route with the kinds now | EDIT needs field schemas later and brings the route then | D-425 C/D |
| A minimal mark in the picture only on steps that need attention (untrusted, changed since trusted, code); the full trust and lifecycle text in the left column; "changed since trusted" comes from the backend and is always no until CODE (R10); a code step is one with a connection of role `code` | marks on every step; marks only in the column | FR-50 "at a glance" and AC-011 | D-426 |
| The whole frame now; the areas of EDIT, REPLAY and RUN present, empty, each with one quiet line naming the subgoal that fills it, no dead controls; the history list (FR-55) fills its part of the row | hidden until filled; disabled controls | the owner sees the final layout now and nothing pretends to work | D-425, D-430 |
| The store (database or files) is chosen by configuration; the page shows which one it reads, read-only, under "other things" | a switch in the page | a switch is a write-side setting and fits EDIT or TRANSFER | D-430 |
| Page checks: node tests of the page modules against the JS mock of IF-104 v2, plus browser checks with Playwright for Python driving Firefox (keyboard reach, light and dark, the frame, no outside request) | no browser checks; Node Playwright; Chromium | the shell had no browser test in the prototype (R7); the repo's tests are Python unittest and it has no `package.json` | D-430 |
| No hard bound for opening; a measured smoke number for a graph of about fifty steps | a time bound | NFR-11 is "as experienced"; D-378: only about fifty steps promised | D-425 E-H |
| FR-96 (search by description) and the chat with MIA about the open graph are later slices; their band keeps its place | in VIEW | VIEW stays without a model step | D-425, D-430 |

## 2. Dependencies
| ID | Kind | What | Pin / version | Why we need it | If it fails or changes | Used by | Update policy | Contract tests (what we rely on) |
|---|---|---|---|---|---|---|---|---|
| DEP-1 | tool | Python | 3.12 (venv `/home/maldun/prog/Python/venvs/mia312`) | backend routes, tests | as CORE | HR-002, HR-004, HR-005 | compatible range 3.12 to < 3.15 | the test suite on 3.12 |
| DEP-2 | library | vis-network (vendored, `graph_app/vendor/`) | 10.1.2, sha256 `fc674cfa…41ad4` | draws the graph | the vendored file stays; a new version is the owner's decision (D-124) | HR-001, HR-003 | exact | the page tests on the vendored file |
| DEP-3 | library | Flask | 3.1.0 (`requirements.txt`) | the backend blueprint | as today | HR-002 | exact | the backend tests |
| DEP-4 | service, library | PostgreSQL and psycopg 3 | postgres:16 image (local, never pulled); `requirements-db.txt` | the database store | the file store still works; the DB checks skip | HR-004 | exact | IF-102 contract suite (`tools/contract_postgres.sh`) |
| DEP-5 | library (dev only) | Playwright for Python | pinned in a new `requirements-browser.txt` at install (a release at least two weeks old), not in the release image | browser checks of the page | the browser checks skip with a message; the node tests and the owner's demonstration stay | HR-006 | exact, updated only by the owner | a smoke browser check that opens the page |
| DEP-6 | tool (dev only) | Firefox build of Playwright | the one the pinned Playwright installs (`~/.cache/ms-playwright`) | the browser engine of DEP-5 | as DEP-5 | HR-006 | follows DEP-5 | as DEP-5 |
| DEP-7 | tool | Node.js (`node --test`) | as installed on the host today | the page module tests | as today | HR-001 | as today | `tests/js/*.test.mjs` |
| DEP-8 | data | the seeded sample store and the 15 converted skill graphs | prototype `proto_checks/make_sample_store.py` at `prototype/g-v4` (R11) | demo and check data, incl. `sample.broken`, `sample.code`, `cp2.multi`, a context graph | re-made from the skills | HR-002, HR-004 | exact, changed only with its tests | the fixtures under `tests/fixtures/` |
| DEP-9 | tool | Caddy (the https front) | as deployed in v0.2.1 | one origin for page and API | page and API on two origins: the session cookie fails | HR-005 | as the stack | the stack smoke check |

New against `goal/v4`: DEP-5 and DEP-6 (approved by the owner, D-430).

## 3. High-level requirements
Hard bounds: **none** (D-425 E-H). The parents of HR-007 (NFR-19) and HR-008 (FR-70) are items of `../G-V4.EDIT/top-level-spec.md`, whose backend side VIEW takes over (D-430 (7)); `spec_check.py` (HS1) reads one top-level spec only and reports them. The opening time of a graph of about fifty steps is measured as a smoke number in the low-level spec.

### HR-001 – Plain page, vendored library
- Kind: technology
- Parent: FR-49
- Text: The Graph app page shall be plain HTML and JavaScript modules that draw with the vendored vis-network 10.1.2 and need no build step.
- Rationale: REQ-GA-009 and NFR-13; the prototype page met it.
- Depends on: DEP-2, DEP-7
- Status: Approved

### HR-002 – Only through IF-104 v2
- Kind: constraint
- Parent: FR-48
- Text: The Graph app page shall read graphs, versions, arrangements and the store status only through IF-104 v2, which amendment A-171 defines with a Python mock, a JavaScript mock and a contract suite.
- Rationale: REQ-GA-005; IF-104 v2 is frozen at G-V4 and shared with EDIT, REPLAY and CONTEXT (D-368, D-425 A).
- Depends on: DEP-1, DEP-3
- Status: Approved

### HR-003 – The same picture on every opening
- Kind: constraint
- Parent: FR-52
- Text: When a graph without a saved arrangement is opened, the Graph app shall arrange it with one fixed solver and one fixed seed, and when a saved arrangement exists it shall use it.
- Rationale: FR-52; physics alone is not reproducible (D-363); the saved arrangement is one record per graph in IF-302 (amendment), carried by TRANSFER.
- Depends on: DEP-2
- Status: Approved

### HR-004 – Store chosen by configuration
- Kind: constraint
- Parent: FR-48
- Text: The backend shall read the graphs from the file store or from the PostgreSQL store as its configuration names, and IF-104 v2 shall report which one it reads.
- Rationale: FR-48 "the same list and picture" from either place; D-430 store choice; today no code reads a database setting (CORE deployment finding).
- Depends on: DEP-4
- Status: Approved

### HR-005 – The page writes nothing
- Kind: constraint
- Parent: NFR-12
- Text: The Graph app page of VIEW shall offer no action that changes a stored graph, an arrangement or a version.
- Rationale: NFR-12 (look, not change) and D-425 E-H; the write routes of IF-104 v2 are real in the backend (D-430 (7)) and used by the page from EDIT on.
- Depends on: –
- Status: Approved

### HR-006 – Browser checks
- Kind: dependency
- Parent: NFR-14
- Text: The checks of the page frame, keyboard reach, light and dark reading and the absence of outside requests shall run in Firefox driven by Playwright for Python, outside the release image.
- Rationale: D-430; the shell had no browser test (R7); NFR-13 and NFR-14 get automated parts beside the owner's validation.
- Depends on: DEP-5, DEP-6
- Status: Approved

### HR-007 – Write routes for the owner only
- Kind: constraint
- Parent: NFR-19
- Text: The backend shall refuse every IF-104 v2 route that changes a graph, an arrangement or a record of changes for an account that is not the owner, and shall change nothing then.
- Rationale: NFR-19 of EDIT; the routes are real from VIEW on (D-430 (7)).
- Depends on: DEP-3
- Status: Approved

### HR-008 – One rule set on the save path and the check route
- Kind: constraint
- Parent: FR-70
- Text: The save and check routes of IF-104 v2 shall take the rules of a graph from IF-301 v4 once G-V4.GRAPHAPI.RULES is merged into the line of work.
- Rationale: FR-63 of RULES (one rule set everywhere); RULES is still in Implement, so the tasks of these two routes depend on its merge.
- Depends on: G-V4.GRAPHAPI.RULES
- Status: Approved

### HR-009 – The main app's look
- Kind: constraint
- Parent: NFR-14
- Text: The Graph app page shall use the main app's design tokens unchanged, and its own styles shall take fonts, colours, spacing, radii and themes only from them.
- Rationale: D-431; NFR-14 light and dark come with the tokens' themes.
- Depends on: –
- Status: Approved

## 4. Nodes, interfaces and amendments
No new node. Changed: N-5 (page), N-2.1 (all routes of IF-104 v2), N-3.1 (tables `arrangements` and `graph_changes`).

| Amendment | What | Protected material it touches |
|---|---|---|
| A-171 | IF-104 v2: text from the prototype's `/api/v2` routes (read side, check, save, restore, arrangement, changes), the field "changed since trusted", the role `code`; Python and JS mocks; contract suite | `contracts/IF-104-graph-api.md` (a v2 section, v1 unchanged), `tests/helpers/mocks/` (new v2 mocks), `tests/acceptance/contract/` (new v2 suite) |
| A-172 | IF-302: the record tables `arrangements` (one record per graph, no version) and `graph_changes` (written once, append-only, moves with the graph) | `contracts/IF-302-record-tables.md`, its contract suite |
| A-173 | REQ-GA-001: "physics off" replaced by the fixed solver and seed (HR-003) | none: `tests/js/graph-view.test.mjs:69` (`physics == false`) is not deny-protected; it changes with the requirement in the same task |

## 5. Open points (questionnaire)
Decided 2026-11-22 (D-430): P-1 all IF-104 v2 routes real in VIEW; P-2 a blueprint in the MIA backend; P-3 `requirements-db.txt` in the release image with a store setting. Look and feel: D-431. No point open.

## 6. Split proposal
Kept as one goal with two tracks (D-430 (2)): first the interface and backend track (A-171, A-172, mocks, contract suite, all routes, store setting, image), then the page track (frame in the main app's look, viewer, browser checks). The page tasks run against the JS mock and need the backend track only for the end-to-end check; the save and check routes wait for RULES' merge (HR-008).

**Effort split within the goal (owner, D-432):** VIEW stays one goal (one set of phases, one verification, one merge), and its work is cut into two tracks, each with its own requirement groups, scenarios, review sittings and block of tasks in `plan.md`:
- **Track A – interface and backend:** IF-104 v2 (A-171) with both mocks and the contract suite, the IF-302 tables (A-172), all routes as a blueprint in the MIA backend, the store setting, `requirements-db.txt` in the image. Checked by the contract suite on the file and the PostgreSQL backend. The save and check route tasks wait for RULES' merge (HR-008).
- **Track B – page:** the frame in the main app's look, the viewer (list, picture, marks, left column, history, settings, arrangement), the browser checks. Built against the JS mock of IF-104 v2, so it can start as soon as A-171's text and mock are approved; checked end to end against Track A at the end.
Order: A-171 text and mocks first (both tracks need them), then the tracks side by side.
