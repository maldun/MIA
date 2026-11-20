# Prototype status: G-V4 (living prototype)

Single source for what the demonstrator can show (`dev-workflow/references/prototyping.md`). Updated with every checkpoint and at merges.

Demonstrator deployed at: not yet (worktree `../MIA-prototype-g-v4`, branch `prototype/g-v4`; round 01 ran from `serve.py files 8765`) · Last updated: 20574749 (CP7), 2026-11-20

| Part / feature | Requirement IDs | State (mock / working / real / not yet / retired) | Made real by task | Commit | Date | Notes |
|---|---|---|---|---|---|---|
| viewer page: login, list with name filter, drawing, problems named and marked (`graph_app_v2/`) | FR-48, FR-49 | working | – | 85efcc21 | 2026-11-20 | CP5: builds on round 01; left panel still shows the JSON of the selected item (CP6 makes it read-only fields); physics and rounded edges as in round 01; context graphs not in the slice; reuse decision: see reuse-map.md (not yet written) |
| viewer page: physics, rounded edges, left panel (round 01) | FR-52 | working | – | – | 2026-11-20 | from round 01 inside `graph_app_v2`; no saved arrangement yet (CP7) |
| graph routes for the stored form (round 01) | FR-48 | working | – | – | 2026-11-20 | two routes; to be replaced by the prototype of IF-104 v2 in CP5 |
| scoped record IDs `<graph>/<local>` and the storage refusal | FR-60 | working | – | 2f9312f8 | 2026-11-20 | CP1: `graph_tables.py` (rule `unscoped_id`), `graph_model.py`; 154 step records for 107 local names; files and PostgreSQL |
| save without half graphs, versions, authors, step history | FR-57, NFR-16 | working | – | 2f9312f8 | 2026-11-20 | CP1: everything checked before the first write; unchanged save = no version; interrupted save leaves nothing visible; `proto_checks/cp1_check.py` |
| same behaviour in files and database | FR-58 | working | – | 70e9c2cb | 2026-11-20 | CP2: one sequence of operations gives the same answers on both (9 fields incl. five refusals) |
| whole-store move files <-> database | FR-59 | working | – | 70e9c2cb | 2026-11-20 | CP2: `graph_store_move.py`; all or nothing, names the graph, repeatable, interrupted move can be run again; command line `python graph_store_move.py files:<dir> postgres:<url>` |
| sync live store to copy | FR-93, NFR-15 | not yet | – | – | – | CP3 |
| eight rules and the check route | FR-63, FR-64 | not yet | – | – | – | CP4 |
| graph backend with login, list, graph and versions (IF-104 v2 read side draft) | FR-48, NFR-12 | working | – | 85efcc21 | 2026-11-20 | CP5: `graph_proto_app.py`, existing accounts and session cookie; `GET /api/v2/graphs`, `/api/v2/graphs/<id>[?version=n]`, `/versions`; the history list in the page comes in CP7 |
| kinds by shape and words, trust and lifecycle marks, code mark, read-only fields with the full stored text, text-only display | FR-50, FR-51, FR-54 | working | – | 80bd08df | 2026-11-20 | CP6: `graph_app_v2/step-marks.js`, `panel.js`; trust and lifecycle from the toolbox (shipped entries seeded in memory); code mark = input connection with role `code`; **the mark "changed since trusted" is a mock**: nothing records the trusted content yet (FR-67, GRAPHAPI.CODE), the page shows it when the backend says so |
| settings menu remembered per browser, legend, step list for the keyboard, clearer status line | FR-53, NFR-14 | working | – | 80bd08df | 2026-11-20 | CP6: `settings.js`; light and dark by the system setting (round 01 CSS); phone layout out of scope (D-389) |
| shared arrangement (settled, saved by the owner for everyone, reset to layers), history list with previous and next, any version shown | FR-52, FR-55 | working | – | 20574749 | 2026-11-20 | CP7: table `arrangements` (a draft addition to IF-302), `GET/PUT /api/v2/graphs/<id>/arrangement` (PUT owner only = the account made first), `arrangement.js`, `history.js`; the save button is in the settings menu for now, the editor takes over in CP10 (FR-74) |
| editor: change, rule feedback, keep, restore, undo | FR-68, FR-69, FR-70, FR-71, FR-72, FR-73, FR-91, FR-92, FR-95, NFR-19 | not yet | – | – | – | CP8, CP9 |
| arrangement saving from the editor, copy a step | FR-74, FR-94 | not yet | – | – | – | CP10 (the save itself exists since CP7) |
| edit log | FR-76, FR-77, FR-80, FR-81 | not yet | – | – | – | CP11 |
| playback and comparison | FR-78, FR-79, NFR-20 | not yet | – | – | – | CP12 |

States: `mock` = looks right or stands in, behavior faked; `working` = functional prototype code built by the agent, not verified; `real` = made or adopted by a normal task (tests first, verified); `not yet` = nothing to show; `retired` = removed or archived at the MVP.
