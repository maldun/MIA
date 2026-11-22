# Interface note: the graph viewer page for the node and browser checks (proposal for Plan step 4, G-V4.VIEW)

Status: **approved** by the owner (2026-11-22, D-443), with the fake DOM imported from `tests/js/fake-dom.mjs`. Drafted 2026-11-22. Inside the node N-5 (page code and test hooks); no contract in `contracts/`. It fixes the names the red tests TC-GA-017 to 039 use; a change after approval is a plan amendment. Pattern: `goals/G-V3.PANEL/skill-run-view-interface-note.md`.

## Why
The scenarios say what the page shows; the checks need to know which module a node test calls, how it hands the page a stand-in API and a stand-in drawing, and which elements a check reads. TR-VIEW-005: node checks read DOM text and the data handed to the drawing library, never pixels; TR-VIEW-010: the browser checks read places through a read-only hook.

## 1. Modules (`graph_app/`, plain ES modules, no build step, REQ-GA-009)
| Module | Export | What it does |
|---|---|---|
| `viewer.js` | `createViewer({document, root, api, storage, makeDrawing})` | builds the frame inside `root` and returns the controller below; `storage` is a `localStorage`-like object (may throw, REQ-GA-035); `makeDrawing(container)` returns a drawing (section 3) |
| `api.js` | `httpApi(fetchFn, base = '/api/v2')` | the page's reader of IF-104 v2: `me()`, `store()`, `listGraphs()`, `readGraph(id, version)`, `versions(id)`, `readArrangement(id)`; each a GET; a non-200 answer rejects with `{status, code, detail}` |
| `drawing.js` | `visDrawing(container, vis)` | the drawing on vendored vis-network (section 3) |
| `app.js` | – | the page entry: `createViewer({document, root: document.getElementById('app'), api: httpApi(fetch), storage: localStorage, makeDrawing: (c) => visDrawing(c, vis)})`, then `start()` |
| `tokens.css` | – | the copy of `templates/static/chat/tokens.css` (REQ-GA-014) |

The prototype's small modules (R6: `list-filter.js`, `step-marks.js`, `history.js`, `settings.js`, `arrangement.js`, `problems.js`, `panel.js`, `store-note.js`, `adapter.js`) come in as the viewer's helpers with their own unit tests in `tests/js/` (not protected); the acceptance checks call only the controller.

### Controller (returned by `createViewer`)
| Method | Effect |
|---|---|
| `start()` | asks `me`, `store` and `listGraphs`; renders the frame, the store entry and the list, or the login note on 401 |
| `filter(text)` | narrows the list (REQ-GA-020) |
| `open(id)` | reads the current version and the arrangement, draws them (REQ-GA-021) |
| `selectStep(id)`, `selectConnection(id)`, `selectNothing()` | fills or empties the left column (REQ-GA-036, 037, 044) |
| `openHistory()`, `showVersion(n)`, `previous()`, `next()` | the history row (REQ-GA-038 to 040) |
| `setSettings({edges, arrangement})` | `edges`: `rounded` or `straight`; `arrangement`: `on` or `off` (REQ-GA-034) |
| `layered()` | the layered reset (REQ-GA-033) |

All methods that read return a promise that settles when the page has drawn the result.

## 2. Hooks in the page (attributes; the checks read only these and visible text)
- Areas: `[data-area=graph-list]`, `[data-area=search-band]`, `[data-area=other-things]`, `[data-area=left-column]`, `[data-area=picture]`, `[data-area=actions-row]`, `[data-area=history-row]`, `[data-area=status-bar]`; each carries a visible label (its `aria-label` and a heading or caption).
- Empty areas of later subgoals: `[data-later=EDIT]` (actions row), `[data-later=REPLAY]` (replay part), `[data-later=RUN]` (start-with-input part), `[data-later=SEARCH]` (search band); each holds one line of text naming the subgoal and no `button`, `input`, `select`, `textarea` or `a`.
- List: `#graph-filter` (input); one `[data-graph-id="<id>"]` per listed graph, its text holding ID, kind, `version <n>`, `<steps> steps`, `<connections> connections`.
- Store entry: `[data-store]` in other things, text `files` or `database` and `reachable` or `not reachable`.
- Status bar: `[data-area=status-bar]` text holding the graph ID, `version <n>`, the author, the time as answered, the kind, and `read-only`.
- Notices: `[data-login]` with a link `a[href="/"]` to the main app (401); `[data-notice=store_unreachable]` (503); `[data-problem]` per thing that cannot be drawn, its text naming the connection and the missing step.
- Left column: `[data-field="<name>"]` per field, its text `<label>: <value>` (names `kind`, `toolbox_id`, `trust`, `lifecycle`, `reason`, `changed_since_trusted`, `code`, `from`, `to`, `role`); `[data-stored-text]` (a `pre` with the stored JSON as text).
- History: one `[data-version="<n>"]` per version, newest first, text holding `version <n>`, the author, the time; `data-current="true"` on the current one; buttons `#history-previous` and `#history-next`, absent or `disabled` where no step is offered.
- Settings: `#settings-open` (button), `[data-setting=edges]` and `[data-setting=arrangement]` (selects).
- Test hook (browser only, read-only): `window.graphViewTest = {settled: <boolean>, positions(): {<id>: {x, y}}}`; `settled` is true once the drawing reported it stabilised or physics is off (TR-VIEW-010).

## 3. The drawing (what the page hands to the library; the node checks record it)
`makeDrawing(container)` returns an object with:
- `show({nodes, edges}, options)`: `nodes`: `{id, label, shape, kind, marks, missing, x?, y?, fixed?, level?}` (`shape` `ellipse`, `box` or `hexagon`; `kind` the words `data`, `processing`, `loop-controlling`, `missing step` or the stored type; `marks` a list of single words; `level` only in the layered arrangement); `edges`: `{id, from, to, arrows: 'to', dashes}`.
- `setOptions(options)`: `{edges: 'rounded' | 'straight', physics: true | false, seed, solver, layout: 'settle' | 'layered'}`; `seed` and `solver` are fixed constants of the page.
- `positions()`: `{<id>: {x, y}}`; `onDragEnd(fn)`, `onStabilized(fn)`.

The node checks pass a recording stand-in (`tests/helpers/graph_view_page.mjs`) and assert on the last `show` and `setOptions`; `visDrawing` is checked only in the browser.

## 4. Stand-ins and runners
- `tests/helpers/graph_view_page.mjs` (protected, new): `mockPageApi(mock, session)` (the JS mock of IF-104 v2 behind the `httpApi` method names, rejecting with `{status, code, detail}`), `recordingDrawing()`, `seededMock()` (the JS mock holding every version of `tests/fixtures/graph_view/graphs.json`), `pageWith({api, storage})` (a fake document from `tests/js/fake-dom.mjs`, a root, a viewer).
- Node checks: `tests/acceptance/graph_view_page.test.mjs` (TC-GA-017 to 030), run with `node --test tests/acceptance/graph_view_page.test.mjs`.
- Browser checks: `tests/acceptance/test_graph_view_browser.py` with the server helper `tests/helpers/graph_view_server.py` (TR-VIEW-009): Flask app of `graph_api_v2.create_app` plus `graph_app/` at `/graph/`, on a seeded throw-away file store; Firefox per TR-VIEW-008.
- File checks: `tests/acceptance/test_graph_view_files.py` (TC-GA-031, 032).

## Stub for step 4
`graph_app/viewer.js`, `api.js` and `drawing.js` are created with exports that throw `Error('not written')` (the old `app.js` and `graph-view.js` stay until Implement replaces them), so every node check fails at its first call (an assertion on the error), not at an import; the browser checks fail at their first hook lookup.

## Open questions (with my proposal)
1. Names of modules, controller methods and hooks as above? Proposal: yes; the page is written in Implement against them.
2. The node checks import the fake DOM from `tests/js/fake-dom.mjs` (not protected). Proposal: accept; a change there that breaks the checks shows as a red check, and copying it into `tests/helpers/` would fork it.
