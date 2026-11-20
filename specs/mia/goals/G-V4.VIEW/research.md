# Research: the graph app and its data path today (G-V4.VIEW, EDIT, REPLAY; Explore)

Read-only, 2026-11-20, `goal/v4`. Shared by the three viewer subgoals. Not examined: `graph_app/graph.css`, the Caddy routing between the static page and the backend, the JS tests in detail, N-5 requirements REQ-GA-004 to -011 beyond their titles.

## Facts
| # | Fact | Evidence |
|---|---|---|
| F1 | The page (170 lines) opens a **JSON file** picked by the user and draws it with the vendored vis-network; it reads nothing from the backend and saves nothing. T-02 to T-05 were never started | `graph_app/app.js:1-25`, N-5 `implementation-log.md` |
| F2 | The backend side exists: IF-104 routes `list`, `read` (with version), `save` (with `expected_version`), `history`, `diff`, `restore`, under the session cookie; the author of a version is the account | `graph_api.py:33-76`, `contracts/IF-104-graph-api.md` |
| F3 | These routes go through the **workflow library** and so serve the **document form** (`workflows`, `context_graphs`, plus `skills`, `transforms` kinds); the record form is not reachable from the app. A graph with a master node cannot be shown as a document (`not_representable`) | `graph_api.py:1-8`, `graph_tables.py:347-364` (see GRAPHSTORE F3, F8) |
| F4 | The page runs in its own container serving static files with `python -m http.server`; the backend session cookie and the API are on the other container | `deploy/compose.yaml:33-38` |
| F5 | The rules run in the backend on save (422 `invalid` with `rule`); none in the page. The open question Q-2 of N-5 (a JavaScript copy, check on save only, or a check route) is still open | N-5 log, Q-2 |
| F6 | `history`, `diff` (nodes and edges added, removed, changed) and `restore` (a new version with the former content) exist on the document form: a state-to-state record of changes | `contracts/IF-104-graph-api.md` |
| F7 | `ChangeLog` records requests (time, account, action, target such as `POST /api/vote`), not edits of a graph | `web_app.py:720`, `data/changes.jsonl` |
| F8 | Dragged positions are not kept (Q-6); context graphs of a run are not in the form the page opens (Q-5) | N-5 log |
| F9 | A protected JavaScript mock of IF-104 (A-36 drafts) is not installed; JS tests of editing need it | `specs/mia/amendments/A-36/` |

## What it means
1. **VIEW depends on GRAPHSTORE.** Once the stored truth is the record form, IF-104 must serve it (or its document export, with master nodes handled). That is an interface decision for Plan; the contract changes by amendment.
2. **The edit log is new.** Versions and `diff` tell what a save changed, not the steps within a session (moves, deletions, undone changes) and not who changed what between two saves of one session. F7 is no log of edits.
3. **Positions** are layout, not graph content; keeping them changes the stored form (GRAPHSTORE) or needs a side record.
