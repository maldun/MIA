# A-140: IF-101 v16, the run of a skill for the Skill run view (proposal, owner G-V3.PANEL)

Status: **approved** (2026-11-08, maldun, D-302). `contracts/IF-101-chat-api.md`, its mock and its contract suite are changed in a separate step (suite red first). Requirements named here stay Draft until that step is done and merged.

Earlier status line (kept for the record): Status: **proposed** (Draft). `contracts/IF-101-chat-api.md` (v15), its mock and its contract suite are not changed; they change together after approval (suite red first). Part of A-131. G-V3.CHAT works against a mock of this amendment (D-273).

## Changes (v16)
| Item | Change |
|---|---|
| `task_status` | adds `skill` (id and version), `started` (UTC time), `phases` (list of `{name, state}` with state `waiting`, `running`, `done`, `failed` or `stopped`, empty for a skill without phases), `state` (`running`, `paused`, `done`, `failed` or `stopped`) and `reason` (text, only for `failed` and `stopped`); `elements` (list of `{label, text}` pairs a skill reports for itself, text only, empty when none: owner 2026-11-08, REQ-WFM-138); the other fields stay; one view per run `id`, replaced in place, at most twice per second (REQ-WFM-031) |
| route `GET /api/skill-runs/shown` | the run that is shown (REQ-WFM-134) as a run record: `id, skill, version, started, ended, state, phases, budget, counts, reason, answers [{text, time}], result, material, files [name]`; `204` when none |
| route `GET /api/skill-runs/<id>` | the same record for one run named by a link; `404 not_found` for a run that does not exist or is deleted |
| event `skill_run_changed` | `{id}` after an answer, the result, a file or the end changed the record; the page asks for the record again |
| `chat_start` / `chat_done` | the message of a skill carries `skill_run: <id>`, the marker the page turns into the link to the view; `chat_done` of a run summary carries no table, card or full result (REQ-WFM-036) |
| `chat_done` text | **[owner 2026-11-08]** the `Files: [name](/api/files/name), ...` suffix of v10 is dropped; `text` is the summary with the link to the view; `files` (names) stays; a failing task gives a message with the reason and the link, not `/<id> could not finish: <reason>` |
| `history` / `chat_start` | messages of a skill carry `skill_run: <id>` in the history too, so the link survives a reload |
| `task_status` fields `paused`, `done` | **[owner 2026-11-08]** stay as in v15; `state` is added and must agree with them (the mock and the suite check it) |
| history deleted | no new operation (owner 2026-11-08): when history records of an account are deleted in the storage (IF-102 `subscribe`, delete is told with `version: None`), the run records of the account are deleted, the event `skill_run_changed` goes out with `id: null`, and `shown` answers `204` |
| all routes | the session cookie is required: `401 unauthenticated` without it, as everywhere in IF-101 |
| `files_changed` | unchanged; the page redraws the list in the Full run part (REQ-CLV-024) |
| `pause`, `resume`, `stop` | unchanged; the state is reported by `task_status` |

## Requirements it serves
REQ-CLV-030 to 039, REQ-CLV-044, REQ-WFM-130 to 138 (the page reads the shown run again on `skill_run_changed`, REQ-CLV-038). Realised by REQ-API-015 (no new API requirement: the routes are part of "realise IF-101"); the contract suite gets one group `TC-IF-101-28` onward, defined in Step 3.

## Open
Nothing open on the wording; the protected mock `tests/helpers/mocks/if_101_chat_api.py` and the suite change only after approval.
