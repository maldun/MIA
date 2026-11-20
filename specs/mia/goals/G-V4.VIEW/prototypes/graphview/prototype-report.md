# Prototype report: graphview, round 01

Status: Prototype (reviewable draft, no product guarantees) · Location: `specs/mia/goals/G-V4.VIEW/prototypes/graphview/` on branch `prototype/graphview` · Date: 2026-11-20
Scope: G-V4.VIEW (item 3a of the owner) · Budget: one session

## Question
Can the graph app pull a real stored graph from the data source (files or PostgreSQL) through the backend and draw it, so that the data path is shown to work before requirements are written?

## Hard requirements (top-level only)
| ID | Outcome | Met? |
|---|---|---|
| OC-8 of G-V4 (FR-22), VIEW part | a stored graph opened in the web app is drawn as it is stored, from the live store or from a set of files | partly: data path and drawing data shown; the drawing on a canvas was not looked at (no browser in this session) |

## What was built
- `serve.py`: seeds the 15 converted skill graphs into the record form through `GraphModel` (files in a temp folder, or a throwaway postgres:16 under podman), serves two prototype routes (`/proto/graphs`, `/proto/graphs/<id>?version=`) that return the stored graph, and serves the graph app's own files plus the prototype page.
- `index.html`, `proto.js`, `adapter.js`: the page lists the graphs, fetches one and draws it with the existing `visData` and vis-network; `adapter.js` maps the record form's `data.type` to the `kind` the view reads.
- Owner's changes after the first look (2026-11-20): the detail panel moved to the left (the place of the later editor); vis-network physics with a choice of solver (`barnesHut`, `forceAtlas2Based`, `repulsion`, `hierarchicalRepulsion`) that settles and then freezes so a dragged node stays; rounded edges (bezier, arc, smooth, dynamic, straight); all view controls in one Settings menu (Escape or a click outside closes it). The layered layout stays as "Reset to layers".
- `check.mjs`: own check, for each stored graph over HTTP the drawing has all its nodes and edges, no problems, and a process node.
- To look at it: `/home/maldun/prog/Python/venvs/mia312/bin/python specs/mia/goals/G-V4.VIEW/prototypes/graphview/serve.py files 8765`, then open http://127.0.0.1:8765/ (or `postgres`).

## Findings
- 15 of 15 stored graphs are read over HTTP and give a complete drawing data set, from files and from PostgreSQL (`node check.mjs http://127.0.0.1:<port>`).
- The record form needs an adapter: the existing view reads `node.kind`, the record form keeps the type in `node.data.type` (and has `master` nodes the view does not know; none in the 15 graphs).
- The IF-104 routes serve the document form (`graph_api.py`); the prototype had to add its own routes for the record form. Plan decides the interface (amendment of IF-104).
- The static page and the API must share an origin (cookie): here one process serves both; the real setup has two containers (`deploy/compose.yaml:33-38`) and needs a routing check.
- The owner looked at it in a browser on 2026-11-20 and found the look good for a prototype; the left panel, the physics and the rounded edges were the owner's requests.
- Physics gives a more natural picture but is not reproducible: the same graph settles differently each time. That conflicts with the test of N-5 T-01 (stable places, physics off, REQ-GA-001) and is why saved positions (D-363, a side record per graph and account) matter: settle once, keep, reuse. The layered layout stays as the reset.
- The settings are not remembered between visits (a per-viewer convenience, left out).
- Not examined: login, a graph with a master node, context graphs, larger layouts (the largest graph has 54 nodes), the look of the drawing.

## Assumptions and choices the prototype made
| ID | Assumption or choice | Alternatives | Evidence |
|---|---|---|---|
| ASM-1 | the viewer reads the record form through a graph route that returns `{id, nodes, edges}` | document export with master nodes refused | the 15 graphs have no master node, so this is not tested |

## Prototype tests
| Question | Command | Result |
|---|---|---|
| every stored graph read over HTTP is drawn completely | `serve.py files 8765` and `node check.mjs http://127.0.0.1:8765` | pass, 15 of 15, 2026-11-20 |
| same on PostgreSQL 16 (podman, tmpfs) | `serve.py postgres 8766` and `node check.mjs http://127.0.0.1:8766` | pass, 15 of 15, 2026-11-20 |

## Carry-over (the developer decides)
| Item | Where | Decision: adopt / adapt / drop / stand-in | Reason |
|---|---|---|---|
| Proposed decisions are the agent's suggestions; the owner decides and ticks. | | | |
| graph routes for the record form | `serve.py` | [ ] adapt (proposed) | the real routes follow the interface amendment of Plan; the prototype's two routes show the shape |
| adapter record form to view | `adapter.js` | [ ] adapt (proposed) | the view should read the stored type directly once the form is settled |
| own check over HTTP | `check.mjs` | [ ] adopt as a contract idea (proposed) | every stored graph is drawn completely, from both backends |
| detail panel on the left | `index.html` | [ ] adopt (proposed) | the editor's place (OC-8) |
| physics with solver choice and freeze after settling | `proto.js` | [ ] adopt, with the positions as a side record (proposed) | natural look; replaces the "physics off" rule of REQ-GA-001, which needs an amendment |
| rounded edges, selectable style | `proto.js` | [ ] adopt the bezier as default (proposed) | the owner asked for it; the other styles for comparison only |
| settings menu | `index.html`, `proto.js` | [ ] adopt (proposed) | one place for view options as the editor grows |
| remembering the settings | – | [ ] decide | a small convenience, not built |

Decided by: [ ] Stefan Reiterer (owner), date: (empty, to be ticked)

## Effect on the TLS
The data path of G-V4.VIEW is plausible; the open work is the interface (record form or document export), master nodes and the two-container routing. No outcome changed.
