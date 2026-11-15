# Interface note: the Skill run view for the browser and JS checks (proposal for Plan Step 4, G-V3.PANEL)

Status: **proposed** (the owner approves or changes it before any test of TC-CLV-030 to 047 is written). Drafted 2026-11-08. Inside the node N-1.1 (page code and test hooks); no contract in `contracts/`. It fixes the names the red tests use; a change after approval is a plan amendment.

## Why
TC-CLV-030 to 047 test what the page shows (strip, phases, meters, controls, reason, Full run part, link, layout, shares, text as text). No document names the elements the checks look at, the module the JS checks call, or how a browser check puts the page into a state (a run that fails, a second run that is shown, a deleted history). Without fixed names every test would guess.

## Proposal
### 1. JS model: `templates/static/chat/skill-run-model.js` (pure functions, `node --test`, like `task-card-model.js`)
| Export | Gives | Checks |
|---|---|---|
| `headerModel(run, t)` | `{skill, started, state}` for a run record or a `task_status`; `state` is one of running, paused, done, failed, stopped | TC-CLV-030 |
| `phaseModel(phases)` | list of `{name, state, current}` in order; at most one `current` (the running phase), none after the end; `[]` for a skill without phases | TC-CLV-031 |
| `meterModel(budget, counts, t)` | `{meters: [{key, text}], counts: [{key, text}]}`; Time and Searches first as `used/limit`, the counts after them; a status after `done` keeps its figure | TC-CLV-032 |
| `controlsModel(state)` | `{pause, resume, stop}` booleans: pause when running, resume when paused, stop when running or paused, none after the end | TC-CLV-033 |
| `shownModel(current, naming)` | the run the view draws after a naming of the backend (`null` for none) | TC-CLV-034, 039 |
| `elementsModel(elements)` | list of `{label, text}`, text only (no markup is interpreted), `[]` when none | TC-CLV-044 |
| `applyStatus(view, status)` | the view state after a `task_status`: the status itself, except that a status of the same run after `done` changes nothing (added 2026-11-08 while writing TC-CLV-032: "the figure after done changes nothing") | TC-CLV-032 |
| `controlAction(action, state, api)` | calls `api[action]()` once and returns true when `controlsModel(state)` allows the button, else calls nothing and returns false (added while writing TC-CLV-033: "exactly one request per press") | TC-CLV-033 |

`controlsModel(null)` (no run) gives no button (TC-CLV-039); `shownModel(current, naming)` returns the naming or `null`.

### 2. Hooks in the page (ids and data attributes; the browser checks read only these)
`#skill-run-view` (the strip), `#srv-header`, `#srv-state`, `.srv-phase[data-state][data-current]`, `.srv-meter[data-key]`, `.srv-count[data-key]`, buttons `#srv-pause`, `#srv-resume`, `#srv-stop`, `#srv-reason`, `#srv-elements`, `#srv-empty` (no run yet), the Full run part `details#srv-full` (open attribute) with `#srv-result`, `#srv-answers`, `#srv-material`, `#srv-files`, `#srv-counts`, the settings `#srv-share-strip` and `#srv-share-full` (inputs), the link in a chat message `a.run-link[href^="#run="]`. Layout checks read `getBoundingClientRect()` of `#character-box`, `#chat`, `#skill-run-view`.

### 3. Stand-in for the browser checks: `ui/tools/skill_run_stub_server.py` (not protected)
The page on the IF-101 mock of `tests/helpers/mocks` (as `chat_mock_server.py`) plus a control route `POST /stub/script` with a JSON list of steps: `{"emit": "task_status", ...}`, `{"emit": "skill_run_changed", "id": ...}`, `{"shown": <run record or null>}` (what `GET /api/skill-runs/shown` answers), `{"run": <record>}` (what `GET /api/skill-runs/<id>` answers), `{"history_deleted": true}`. The scripted skill of TR-PANEL-002 is such a list (questions, three phases, a long result, a failure, a stop); it sends only the events of IF-101 v15 and the v16 fields, never a word about the view. TC-CLV-038 (restart) uses the real backend process twice with file-backed storage instead (TR-PANEL-004).

### 4. Runners
- JS checks: `tests/js/skill-run-model.test.mjs` for TC-CLV-031, 033, 034, 039, 044 (and the model part of 030, 032).
- Browser checks: `tests/browser/skill_run_view.py` (selenium in `localhost/mia-browser`, scenarios by name) and `tests/test_skill_run_view_browser.py` (starts the stub server container and the browser container as `tests/test_task_files_browser.py` does; skipped, never passed, where podman or an image is missing) for TC-CLV-030, 032, 035, 036, 037, 040 to 043, 045 to 047; TC-CLV-038 with the real backend.

### 5. TR-PANEL-001 named (agreed for Step 4)
Harness of the layout checks: image `localhost/mia-browser`, **Chromium 156.0.8078.73** (Debian 13, package `chromium`), font **DejaVu Sans** (package `fonts-dejavu-core`, `fc-match sans-serif`), selenium 4.25.0 (read on 2026-11-08). Changing the text of TR-PANEL-001 sends it back into review.

## Stub for Step 4
`skill-run-model.js` is created with the eight functions that throw `Error('not written')`; the page and the stub server are not changed, so every browser scenario fails at its first lookup of a hook (an assertion on a missing element), not at an import.

## Open questions (with my proposal)
1. **Names of the hooks** as above (ids with the prefix `srv-`)? Proposal: yes; the page is written in Implement against them.
2. **Stub server as a new tool, not an extension of `chat_mock_server.py`?** Proposal: a new tool with the control route, so that the mock server of the contract and its uses stay as they are.
3. **Scope of this batch:** 18 checks in two runners. Proposal: write the JS checks first (TC-CLV-030 to 034, 039, 044: fast, no podman), the browser checks in a second payload.
