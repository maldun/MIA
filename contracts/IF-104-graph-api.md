# IF-104 – Workflow and graph API (REST with the backend's session), v2

Owner (provider): N-2 Backend (child N-2.1, workflow logic in N-2.3)   Consumers: N-5 Graph app   Decided by: N-0 (frozen at G-V4, D-368)   Mock complexity: 2 (fake REST server on the storage mock; for the JavaScript consumer a fake `fetch` on the routes)   Suites: v1 `tests/acceptance/contract/test_if_104_graph_api.py` and `test_if_104_graph_api.test.mjs` (unchanged); v2 `tests/acceptance/contract/test_if_104_v2_graph_api.py` (the routes on the real backend, files and PostgreSQL) and `test_if_104_v2_graph_api.test.mjs` (the same cases on the JS mock)   Mocks: v1 `tests/helpers/mocks/if_104_graph_api.py`, `.mjs` (unchanged); v2 `tests/helpers/mocks/if_104_v2_graph_api.py`, `.mjs`

Added by amendment 7 (D-47): the graph app has no database access and no login of its own. **v2** (A-171, G-V4.VIEW, D-425 A, D-430) adds the routes of the **stored form** (CORE: one header per graph, steps and connections as their own records, local IDs) under `/api/v2`, written from the prototype's routes (round 02, reuse map R5). **v1 stays as it is** beside v2 (D-430 (3)): its routes, mocks and suite are unchanged and are retired by the subgoal that replaces their last user. Everything below the heading "v1" is the text of v1, unchanged.

# v2 (stored form)

## v2 Wire (HTTP)
The session is the cookie `mia_session` of the existing accounts (IF-101: `POST /api/login`, `POST /api/logout`, `GET /api/whoami`); the page keeps no token and sends the cookie with every call (`credentials: 'same-origin'`). Every v2 route needs a session. A route that changes something also needs the `Origin` of the page (the existing guard) and an account that is the **owner** (the first account, or `owner_account` of the configuration; NFR-19). Bodies and answers are JSON. The graph ID in the path is URL-encoded; a graph ID has no slash (REQ-GTB-029), so `/api/v2/graphs/<id>/versions` is never ambiguous.

A **graph** in v2 is the stored form with local IDs, as CORE's `read_graph` gives it (REQ-WFM-144, 157): `{"id", "kind"?, "description", "context_graph_id", "testbench_id", "nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]}`. `kind` is present only for a kind other than `workflow` (a workflow graph keeps its earlier shape); `data.type` of a node is its kind of step (`data`, `transform`, `master` for a workflow graph; a category for a context graph).

| # | Operation | Route | Who | Request body | Answer (200) |
|---|---|---|---|---|---|
| 1 | `me` | `GET /api/v2/me` | session | | `{"user": <account>, "owner": bool}` |
| 2 | `store` | `GET /api/v2/store` | session | | `{"store": "files" or "database", "reachable": bool, "shown": "live" or "copy", "live_reachable": bool, "lag": {"graphs": n, "since": time or null}}`: which store the backend reads (its configuration, D-430 (6)) and whether it answers now; the fields of the live store and its copy (D-460) are below |
| 3 | `list_graphs` | `GET /api/v2/graphs` | session | | a list sorted by ID of `{"id", "kind", "version", "author", "time", "description", "steps", "connections"}`; `kind` is always named here (`workflow`, `context`, or the stored text of another kind); `steps` and `connections` are counts |
| 4 | `read_graph` | `GET /api/v2/graphs/<id>` or `?version=n` | session | | `{"graph", "version", "current", "author", "time", "problems", "steps"}`: the graph of that version (default the current one); `version` the one shown, `current` the newest; `author` and `time` of the shown version; `problems` and `steps` below |
| 5 | `versions` | `GET /api/v2/graphs/<id>/versions` | session | | `[{"version", "author", "time"}]`, oldest first (REQ-WFM-158) |
| 6 | `read_arrangement` | `GET /api/v2/graphs/<id>/arrangement` | session | | `{"positions": null}` when none is saved; else `{"positions": {<step ID>: {"x", "y"}}, "version", "author", "time"}` (whole numbers) |
| 7 | `changes` | `GET /api/v2/graphs/<id>/changes` | session | | one item per graph version, oldest first: `{"version", "kind", "from_version", "author", "time", "entries"}`; `kind` is `editor`, `derived`, `restore`, or `before_the_record` (a version kept without a record: `from_version` absent, `entries` empty) |
| 8 | `check` | `POST /api/v2/graphs/<id>/check` | owner | `{"graph": {"description"?, "nodes", "edges"}}` | `{"rules": [{"rule", "parts", "text"}]}`: the rule report of IF-301 v4 `rule_report` for the stored graph's kind with the sent steps and connections; `[]` when every rule holds. Nothing is stored |
| 9 | `save` | `PUT /api/v2/graphs/<id>` | owner | `{"graph": {"description"?, "nodes", "edges"}, "expected_version"?, "changes"?}` | `{"version", "changed", "logged", "entries"}`: a new version authored by the account when something changed (`changed: true`), else the current version (`changed: false`, nothing written); `logged` whether the record of changes was written (`null` when nothing changed); `entries` the number of entries |
| 10 | `restore` | `POST /api/v2/graphs/<id>/restore` | owner | `{"version", "reason"?}` | `{"version", "restored", "changed"}`: the content of `version` saved as a new version; nothing is deleted (FR-73) |
| 11 | `save_arrangement` | `PUT /api/v2/graphs/<id>/arrangement` | owner | `{"positions": {<step ID>: {"x", "y"}}}` | `{"version", "saved"}`: one record per graph, the same for every account, not part of a graph version (FR-74, D-363); `saved` the number of places kept |

### v2 Fields
- **`problems`** (route 4): what cannot be drawn, never a rule report (D-425 A): `{"problem": "missing_step", "connection", "step", "end": "from" or "to"}` for a connection to a step the graph does not have, `{"problem": "duplicate_step", "step"}` for a step ID used twice; `[]` when everything can be drawn. The rules of a graph are route 8.
- **`steps`** (route 4): per step ID `{"kind"}` (its `data.type`, `unknown` when missing); for a step of kind `transform` or `master` also `{"trust", "lifecycle", "reason", "code", "changed_since_trusted"}`: `trust` and `lifecycle` of its toolbox entry (`untrusted`, `null`, reason "it is not in the toolbox" when the entry does not exist), `code` true when a connection into the step has `data.role` = `code` (D-426), `changed_since_trusted` always `false` until G-V4.GRAPHAPI.CODE records the trusted content (reuse map R10, D-426). A context graph's steps carry `kind` only.
- **Live and copy** (route 2, D-460): `shown` names whether the graphs shown come from the live store or from its copy, `live_reachable` whether the live store answers, `lag` how many graphs the copy is behind on and since when (the time of the oldest version the copy does not have yet). **Until G-V4.GRAPHSTORE.TRANSFER brings the copy, the values are fixed:** `shown` = `live`, `live_reachable` = `reachable`, `lag` = `{"graphs": 0, "since": null}`; TRANSFER makes them real without a new version of the interface.
- **Save body** (route 9): the stored graph's `id`, `kind`, `context_graph_id` and `testbench_id` are kept; `description` is taken when sent. `changes` is the editor's list of entries (below); when it is sent, playing it back on the current version must give the sent graph exactly, else nothing is written (`changes_do_not_match`); when it is not sent, the backend derives the entries from the two graphs and the record's `kind` is `derived`.
- **Entries** (routes 7, 9): `{"n", "op", "target", "before", "after", "reason"}`, `n` from 1; `op` is `add_step`, `remove_step`, `change_step` (target a step ID, before and after its `data`), `add_connection`, `remove_connection`, `change_connection` (target a connection ID, before and after `{"from", "to", "data"}`), or `restore` (target the restored version, one entry). A record of changes is written once, after its version, and never changed (FR-80; IF-302 `graph_changes`, A-172).
- **Arrangement body** (route 11): a place for a step the graph does not have is ignored; `x` and `y` are finite numbers, stored rounded to whole numbers.

## v2 Errors
Every error answers its status with `{"error": code}` and the fields named here. A refused request changes nothing.

| Condition | Signal | Routes |
|---|---|---|
| no or unknown session | 401 `unauthenticated` | all |
| a change from a foreign `Origin` | 403 `bad_origin` | 8 to 11 |
| the account is not the owner | 403 `not_owner` | 8 to 11 |
| unknown graph, or unknown version | 404 `not_found` (`"detail": "version"` for a version) | 4 to 11 |
| a body that is not the shape above (no `graph` object, `nodes` or `edges` not lists, `positions` not an object, a place that is not two finite numbers) | 422 `invalid` with `detail` (`graph`, `positions`, or the step ID) | 8, 9, 11 |
| `expected_version` is not the current version | 409 `conflict` with `current` | 9 |
| a rule of the graph's kind is broken | 422 `rules_broken` with `rules` (the rule report of route 8) | 9, 10 |
| a record check of the store refuses the graph (IF-301 `check_record`) | 422 `refused` with `rule` and `detail` | 9, 10 |
| the sent `changes` do not give the sent graph | 422 `changes_do_not_match` | 9 |
| the store cannot be reached | 503 `store_unreachable` | all except 1; route 2 answers `reachable: false` instead |

## v2 Bounds
None (D-425 E-H: no hard bound for opening; the opening time of a graph of about fifty steps is measured as a smoke number in VIEW's low-level spec). The v1 proposals below stay v1's.

## v2 Golden examples
On the seeded sample store (the prototype's `make_sample_store.py --broken --code`, R11) plus `cp2.multi`, a small workflow with four stored versions (the fixture of VIEW's plan, as the prototype's `cp8_check.py` builds it); owner `owner`, a second account `guest`:
1. Typical: `guest` lists the graphs and gets each with its kind, version, author, time, description and counts; reads `cp2.multi` and gets version 4 of 4 with `problems: []`; `versions` gives four entries oldest first; `?version=2` gives version 2 with its own author and time and `current: 4`.
2. Drawable problem: `read_graph("sample.broken")` gives the graph with `problems == [{"problem": "missing_step", "connection": "e2", "step": "var.gone", "end": "to"}]`; the steps `var.in`, `step.a` and the connections `e1`, `e2` are all in `graph`.
3. Marks: in `read_graph("sample.code")` the step `<img src=x onerror=alert(1)> step "quoted" & more` (toolbox ID `import.demo`, not in the toolbox) has `trust: "untrusted"` and `code: true` (its connection `e2` has the role `code`); `loop.review` has `kind: "master"`; every step of kind `transform` or `master` has `changed_since_trusted: false`; the names come back exactly as stored.
4. Save: `owner` saves `cp2.multi` with one changed step and `expected_version: 4`: version 5, `changed: true`, `logged: true`, `entries: 1`; `changes` lists version 5 as `derived` from version 4 with one `change_step` entry; saving the same graph again gives `changed: false` and no version 6.
5. Refusals: `guest` saving anything gets 403 `not_owner`; `owner` saving with `expected_version: 3` gets 409 `conflict` with `current: 5`; saving a graph with a cycle gets 422 `rules_broken` whose last item is `cycle`; none of them writes a version.
6. Restore: `owner` restores version 1 of `cp2.multi`: a new version equal in content to version 1, `restored: 1`; `changes` lists it as `restore` with one entry.
7. Arrangement: `read_arrangement` of a graph never arranged gives `positions: null`; `owner` saves `{"a": {"x": 10.4, "y": -3}, "nope": {"x": 0, "y": 0}}` and gets `saved: 1`; reading gives `{"a": {"x": 10, "y": -3}}`; a place `{"x": "far"}` gives 422 `invalid` with `detail: "a"`.
8. Store: `store` gives `{"store": "files", "reachable": true, "shown": "live", "live_reachable": true, "lag": {"graphs": 0, "since": null}}` on the file store and `"store": "database"` on PostgreSQL; with the database stopped every route but `me` and `store` answers 503 `store_unreachable`.

## Not in v2
Routes of the prototype that later subgoals add as a new version when they need them: the tool list of the editor (`toolbox`, G-V4.EDIT, FR-92), copying a step into another graph (`copy-step`, G-V4.EDIT, FR-94), the run (`run`, G-V4.GRAPHAPI.RUN), the sync of the copy (`sync`, G-V4.GRAPHSTORE.TRANSFER, FR-93; the fields of route 2 are already in v2, D-460).

# v1 (document form, unchanged)

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `login(user, password)` | account, password | session token | the same accounts and throttle as IF-101 |
| `list_ids(session, kind)` | | sorted ids | |
| `read(session, kind, id, version=None)` | | `{"id","version","author","time","doc"}` | |
| `save(session, kind, id, doc, expected_version=None)` | document | `{"version": n}` | a new immutable version, author = the session's account |
| `history(session, kind, id)` | | list of `{"version","author","time"}` | |
| `diff(session, kind, id, a, b)` | two versions | `{"nodes_added","nodes_removed","nodes_changed","edges_added","edges_removed"}` | edges as `from->to` |
| `restore(session, kind, id, version)` | | `{"version": n}` | saves the former content as a new version; the former version stays |

## Wire (HTTP) **[v1]**
The session is the cookie `mia_session` that `POST /api/login` sets, as in IF-101 v1; the page keeps no token and sends the cookie with every call (`credentials: 'same-origin'`). Bodies are JSON.

| Operation | Route | Request body | Answer (200) |
|---|---|---|---|
| `login` | `POST /api/login` | `{"user", "password"}` | `{"ok": true}` and the cookie |
| `list_ids` | `GET /api/{kind}` | | the sorted ids (a list) |
| `read` | `GET /api/{kind}/{id}` or `?version=n` | | `{"id","version","author","time","doc"}` |
| `save` | `PUT /api/{kind}/{id}` | `{"doc"}` or `{"doc", "expected_version"}` | `{"version": n}` |
| `history` | `GET /api/{kind}/{id}/history` | | list of `{"version","author","time"}` |
| `diff` | `GET /api/{kind}/{id}/diff?a=&b=` | | the diff of the operations table |
| `restore` | `POST /api/{kind}/{id}/restore` | `{"version"}` | `{"version": n}` |

An error answers its status with `{"error": code}`, plus `"rule"` for 422 and `"detail"` where the table below names one (`{"current": n}` for 409, the broken node, edge or cycle for 422). The id in the path is URL-encoded.

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| no or unknown session | 401 `unauthenticated` | nothing changed |
| wrong credentials | 401 `bad_credentials` | no session |
| unknown id, version or kind | 404 `not_found` / `unknown_kind` | nothing changed |
| `expected_version` differs from the current version | 409 `conflict` with `detail.current` | nothing changed |
| a graph rule is broken | 422 `invalid` with `rule` (`node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`, `cycle`) | no version consumed |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| read of one graph | at most 200 ms for a graph of 200 nodes | proposal, set in Plan |
| graph size | at most 500 nodes | proposal, set in Plan |

## Golden examples
1. Typical: anna logs in, saves the lookup workflow (version 1), edits one node (version 2), `diff(…,1,2)` lists the changed node, `restore(…,1)` gives version 3 equal to version 1.
2. Failure: saving a graph with a cycle `a->b->a` gives 422 `cycle`; `list_ids` shows no new id.
3. Edge: a request with a made-up session token is 401; saving with `expected_version=1` when the record is at version 2 is 409.


## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | 7 |
| v1 | 2026-10-31 | the wire of the routes (bodies, cookie, error body), a JavaScript mock of the routes for the Graph app and the same contract cases on them (N-5 Q-3, D-122); the operations are unchanged | A-36 |
| v2 | 2026-11-22 | the routes of the stored form under `/api/v2` (read, versions, arrangement, changes, check, save, restore, me, store), the fields `problems` and `steps` (with `changed_since_trusted` and `code`), owner-only changes, the record of changes; Python and JS mocks and suites of their own; v1 unchanged | A-171 |
