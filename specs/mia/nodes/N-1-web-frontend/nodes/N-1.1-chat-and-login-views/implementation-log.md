# Implementation log: Chat and login views (N-1.1)

Status: **survey done, stopped before the first task** (2026-10-26). Reason: ten of the 21 requirements need events or REST calls that IF-101 v0 does not contain (see "Stop"). The other eleven are covered by the existing page or need only IF-101 v0.

## Survey: what the existing page and its tests already fulfil (owner rule: use existing code)

| Requirement | Existing code and tests | Gap |
|---|---|---|
| REQ-CLV-001 chat view with sender and streaming | `chat.js`, `chat-model.js` (`chat_start`, `chat_delta`, `chat_done`; tests: normalized messages, upsert, grouping) | the sender of a message is the account (IF-101 `sender`): today grouping is by role |
| REQ-CLV-002 stop and queue position | `chat_stop`, palette, `composer.js`; client-side queue | the position comes from the acknowledgement of `send` (IF-101 v0 has it) |
| REQ-CLV-003 shared history after reload | `chat_log.py`, history load in `app.js`, `chat_message` broadcast, upsert tests | none known; a browser test against the IF-101 mock is step 3 of N-1 |
| REQ-CLV-004 connection state and drafts | `socket.js`, `app.js` (connect, disconnect, connect_error), drafts in `composer.js` and `storage.js` (tests) | the 5 s cut test needs a browser (stage 2) |
| REQ-CLV-006 chat without the character | `character.js` disable path, now with tests (`character-bridge.test.mjs`) | none |
| REQ-CLV-007 character as stage | `layout.js` (tests: layout rules, `insetFor`), `caption.js` | the three viewports are a demonstration |
| REQ-CLV-016 accessibility and devices | `a11y.js`, `theme.js`, `ui/tools/chat_a11y.js`, `ui/CHECKLIST_CHAT_PHONE.md` (manual) | 320 and 2560 px are VN-4 |
| REQ-CLV-017 no request leaves the host | `tests/js/no-outside-requests.test.mjs`, CSP test in `test_chat_page.py` | none (done in N-1.3 T-04) |
| REQ-CLV-019 plain stack | `test_chat_page.py` (no inline code, local files, performance budget) | Godot version string is N-1.2 |
| REQ-CLV-020 delivered by the backend | `tests/test_frontend_delivery.py` | none (done in N-1.3 T-04) |
| REQ-CLV-021 use IF-101 only | the page uses Socket.IO events and `/api/...` of today | a static check of the endpoints against IF-101 |
| REQ-CLV-014 login views and password change | none: today there are no accounts | login is in IF-101 v0; **password change is not** |
| REQ-CLV-015 login page states that all is visible | none | text of CON-6 on the login page; needs the login view |
| REQ-CLV-018 password only over a secure channel | none | with the login view |
| REQ-CLV-005 regenerate and speak again | none | **no event or call in IF-101 v0** |
| REQ-CLV-008 status line and account of a task | status line: `mood.js`, `chat_status` | the account (step-by-step) needs the run log events (IF-401): **not in IF-101 v0** |
| REQ-CLV-009 editors for the persona | expression and gesture editors are in Godot (N-1.2) | persona editor and live update: **no call in IF-101 v0** |
| REQ-CLV-010 voting controls and score | none | **no vote or score call in IF-101 v0** |
| REQ-CLV-011 tasks, memos and memory views | none | **no list, edit, delete calls in IF-101 v0** |
| REQ-CLV-012 source trust edit | none | **no call in IF-101 v0** |
| REQ-CLV-013 variant label | none | **no variant in the events of IF-101 v0** (and N-1.2 T-03 is deferred) |

## Stop (needs a decision)
The ten views in the last rows are in the approved requirements but IF-101 v0 (spec, mock and protected suite) has only login, connect, send, stop, history and events. Building them needs the calls first (an IF-101 v1: amendment of the spec, the mock and the suite, owner-approved), and the Backend side (N-2.1, N-2.2) must offer the same. Options:
1. **Slice first (recommended for early human testing):** build what IF-101 v0 allows: the login view with the text of CON-6 and the secure-channel rule (CLV-014 login, -015, -018), the sender of messages (CLV-001), the queue position (CLV-002), the static endpoint check (CLV-021); plus a mock server for clicking (the IF-101 mock behind Socket.IO, started by `tools/start_testing.sh`). The remaining views wait for IF-101 v1.
2. **IF-101 v1 first:** I draft the amendment (vote, score, regenerate, speak again, tasks, memos, memory, source trust, persona, variant, password change, account of a task), mock and suite tests, you approve, then all of N-1.1 is built against it, and N-2.1 and N-2.2 get matching tasks.
3. Both, in this order.

## Plan amendments
None yet.

---

## Slice 1 (owner decision 2026-10-26: "slice first, v1 later")
Done on branch `impl/n-1-web-frontend`: the part of N-1.1 that IF-101 v0 allows, plus a mock server to click through it.

| Requirement | What was done | Tests (reported green) |
|---|---|---|
| REQ-CLV-001 sender | `senderName` and the group rule in `chat-model.js`, used by `chat.js`: another account is shown by name, my own as "You", MIA by her name; two users in a row are two groups; an old server without `sender` looks as before | `tests/js/multiuser.test.mjs` (2 tests); `tests/test_chat_mock_server.py` (the other user sees the sender) |
| REQ-CLV-002 queue position | `queueText`: "Waiting, place n" from the acknowledgement (`position`); "Waiting" for a server without a position; the acknowledgement of today's server (`ok`, `queued`) and of IF-101 (`id`, `position`) are both understood | 2 JS tests; mock server test (positions 1, 2, 3 and the refusal of a third message of one user) |
| REQ-CLV-014 login | new `login.js`: `submitLogin` (POST `/api/login`, JSON, same-origin cookie, one attempt), `loginErrorKey` (wrong, throttled, lost connection), the dialog `initLogin`; the page opens it when the history answers 401 or the socket is refused with `unauthenticated`; after success the page reloads with the cookie | 3 JS tests; mock server tests (401, cookie `HttpOnly` and `SameSite=Strict`, sixth wrong login 429 even with the right password) |
| REQ-CLV-015 all is visible | the login dialog says it, in English and German (`login.visible`) | JS test (both dictionaries and the markup) |
| REQ-CLV-018 password only over a secure channel | `secureChannel`: HTTPS, or localhost, 127.0.0.1, ::1 over HTTP; otherwise the form is switched off with a reason and nothing is sent | 2 JS tests |
| REQ-CLV-021 IF-101 only | a static check lists every `/api` address and socket event of the page against the interface and the character/voice events | 1 JS test |

Totals reported green: 76 JS tests (65 before + 11), `test_chat_page.py` 11 (dictionaries have equal keys, strict CSP, no inline code, performance budget), `test_chat_mock_server.py` 7.

### The mock server and the start script
`ui/tools/chat_mock_server.py` is the real page (served by `web_app.py`) with the chat handlers replaced by the IF-101 mock of the protected helper (login with throttling, `send` with positions, `stop`, `history`, events with the sender); answers are scripted and stream with a gap, and a message waits `ANSWER_DELAY` seconds (default 4) so that the positions can be seen. Stage `chat-with-login` of `tools/start_testing.sh` runs it as a container (port 8686): `bash tools/start_testing.sh start chat-with-login`, accounts `anna / pw-anna`, `ben / pw-ben`, `carl / pw-carl`. Tried in the container with real HTTP: page 200, history without session 401, login 200 with cookie, history 200. A browser click-through was not possible in this session (headless Chromium does not answer in the background session); the owner clicks.

### Findings
| Finding | Covered by test |
|---|---|
| IF-101 v0 acknowledges `send` with `{id, position}` only. The page needs the stored message (with its server id and sender) in the acknowledgement, or the `client_id` echoed in the `chat_message` event; otherwise the local copy of my message and the server's copy are two rows. The mock server adds `message` to the acknowledgement. **Input for IF-101 v1 and for N-2.1** | mock server test (`ack["message"]`) |
| IF-101 v0 does not say how the session travels. Decision of this slice: a cookie `mia_session` (HttpOnly, SameSite=Strict, Secure on HTTPS) that the server sets at `/api/login`; the page keeps no token; a socket without the cookie is refused with the message `unauthenticated`. **To be written into IF-101 v1 and N-2.1** | mock server tests |
| Position 1 means "answered next"; the text "Waiting, place 1" shows until the answer starts. Whether place 1 should read differently is a wording decision | JS test |
| The page keeps working with today's server (no login, no sender, old acknowledgement): the old tests and the old-server cases pass | existing 65 JS tests, `test_chat_page.py` |

### Not done in the slice (waits for IF-101 v1)
Password change and the account of a kept session (REQ-CLV-014 rest), regenerate and speak again (-005), the account of a task (-008), editors for the persona (-009), voting (-010), tasks, memos and memory (-011), source trust (-012), variant label (-013).

### Reuse check
`chat.js`, `chat-model.js`, `socket.js`, `app.js` and the dialogs of the page were extended (a few lines each); `login.js` and the mock server are new because no login existed. The stub server of the old backend stays as stage `chat-on-stub`.

---

## Slice 2: the ten views against IF-101 v1 (owner: "go", 2026-10-26)
Branch `impl/n-1-1-views`. Built on the amended interface (A-03, spec draft `specs/mia/amendments/A-03/`); the mock server uses the draft mock until the installed mock is v1.

| Requirement | What was done | Tests (reported green) |
|---|---|---|
| REQ-CLV-005 regenerate and speak again | buttons under an answer (speak, plus, minus, how, regenerate); regenerate only on the last answer that is written and stored (`lastAnswerId`) | `panels.test.mjs`, `api.test.mjs`; browser click-through |
| REQ-CLV-008 account of an answer | button "how I got this" fetches `account` and lists the plain sentences, a second click hides them | browser click-through (2 steps listed, hidden again) |
| REQ-CLV-009 persona | tab Persona in the workspace: read, save; a change by another user redraws the open tab (not while typing) | browser click-through; mock server test (persona_changed to the other page) |
| REQ-CLV-010 votes and scores | plus and minus per answer (category answer_quality, one call each, marked pressed); the tab Score shows overall and four categories | `panels.test.mjs`, browser click-through (overall +1); mock server test |
| REQ-CLV-011 tasks, memos, memory | tabs with add, edit, delete; memory asks for a source; `item_changed` redraws | `panels.test.mjs` (draft check), browser click-through, mock server test |
| REQ-CLV-012 trust of sources | tab Sources: value 0 to 1 (comma accepted), saved with the source id | `panels.test.mjs` (`parseTrust`), browser click-through, mock server test |
| REQ-CLV-013 variant label | the `variant` event shows "Outfit: name" next to the mood line and goes to the character (`setVariant`, IF-111 `variant`); the Godot side is deferred (N-1.2) | `character-bridge.test.mjs`, `panels.test.mjs`; browser click-through (third answer) |
| REQ-CLV-014 rest | `whoami` and the dialog Account with the change of the own password (checked before it is sent, wrong old password told) | `panels.test.mjs`, `api.test.mjs`, browser click-through, mock server test |

New files: `api.js`, `panels-model.js`, `workspace.js`, `account.js`; changed: `chat.js`, `app.js`, `character.js`, `index.html`, styles, texts (English and German, 58 keys each). Reported green: 90 JS tests (76 before), 11 chat-page tests, 11 mock-server tests (7 before). **Real browser:** the click-through `ui/tools/chat_views_e2e.js` ran in headless Chromium against the mock server with `problems: []` (login, send, answer, five actions, vote mark, account steps, regenerate moves to the new last answer, variant label, six tabs, task and memory records, trust, persona, score, account dialog).

### Findings
| Finding | Covered by test |
|---|---|
| Two drawings of a workspace tab at once (a save redraws, the event of the change redraws) listed every record twice | fixed: each drawing builds its own holder and only the latest is put on the page; checked in the browser run (`tasks` and `memory` listed once) |
| Without the client id echo (IF-101 v0 mock) a message of mine appeared twice; with the v1 mock it is merged | browser run with both mocks; contract test TC-IF-101-09 |
| `browser_check.py` hangs when an older headless Chromium still holds its debugging port; a driver that attaches to the running instance works (scratch tool, not committed) | – |
| The score is shown as sums per category and overall, not as a curve "over time" (REQ-CLV-010 says "over time"): the interface has no series. Proposal for IF-101 v2: `score` returns votes with times, or a series per day | – |
| The name of the REST addresses was open in the A-03 draft; fixed now in the spec (table) | `api.test.mjs`, mock server tests |

### Reuse check
The page kept its modules; `chat.js` got the answer actions (about 60 lines), the rest is new modules because no such views existed. The mock server is the same file as in slice 1, extended by the REST routes.

### Not done
Frame rate (field), the variant and model selection in Godot (deferred by the owner until after the first tests), the series of the score.
| REQ-CLV-022 logout (A-04) | button `account-logout` in the account dialog; `api.logout` (POST `/api/logout`); `initAccount` reports `onLoggedOut`, the page closes the socket and opens the login; a 401 (session already gone) counts as logged out; other failures keep the user logged in and say so; the mock server has the route (draft mock until A-04 is installed) | `tests/js/logout.test.mjs` (4), `test_chat_mock_server.py` logout test; the allowed-address list of TC-CLV-021 got `/api/logout` |

---

## Verify findings (report of 2026-10-31, owner's answers D-163)
Branch `v1-n11b` from `goal/v1` @ a262376 (A-52..A-58 installed). One commit per item, test-first.

| Item | Finding | What was done | Tests (reported green; red first) | Commit |
|---|---|---|---|---|
| 1 | F1 (REQ-CLV-002): every `chat_start` cleared "Waiting, place n" of all waiting messages | `chat.js` `moveQueue`: a start moves each waiting message up one place (IF-101: place 1 is answered next); place 1 is cleared; a message without a place counts as place 1 | `tests/js/chat-page.test.mjs` (2, on the new fake DOM `tests/js/fake-dom.mjs`): three waiting, two starts -> places 1,2,3 -> -,1,2 -> -,-,1; a start for another user's message moves mine up, it does not clear it | see below |
| 2 | F3 (REQ-CLV-016): `.link-button.action { min-width: 32px }` outranked the 44 px touch size | `components.css`: under `pointer: coarse` the answer actions get `min-width: 44px` | new stage-2 browser test `tests/test_chat_views_browser.py` (TC-CLV-016: phone emulation 360 px with a coarse pointer, every visible control >= 44 x 44 px; 360/768/1440 px in dark and light without sideways scroll) with the driver `tests/browser/chat_views.py`; red before: speak, up, down, how, regenerate 32 x 44 px. The mock server runs in its own container (`n11-views-<random>`, `--network none`), Chromium of `localhost/mia-browser` in its network namespace; both removed afterwards | see below |
| 3 | F2 (REQ-CLV-011, REQ-CHA-019; D-163): an edit in the Tasks tab dropped `due` (IF-101 v6: a save without `due` clears it); the page never showed or set it | `api.saveItem(kind, id, text, source, due)` (no `due` key when there is none); Tasks tab: a `datetime-local` field per task and in the add form (texts `workspace.due`, en/de); a save keeps the stored `due` byte for byte while the field still shows it (seconds and the "said" mark stay), an emptied field clears it; helpers `dueToField`, `dueFromField` (`panels-model.js`) | `api.test.mjs` (1), `panels.test.mjs` (1), new `workspace-page.test.mjs` (3: edit keeps due, field shows and clears it, a new task gets a due time, memos have no field); red before (missing helpers, no due in the body) | see below |
| 4 | F6: the page wiring had no test that fails on a defect; the stage-2 browser checks did not exist | Unit tests on the fake DOM: `chat-page.test.mjs` (+4: sender name, streaming in one row, history `limit=50` in order plus a live message, account lines and hide), `workspace-page.test.mjs` (+4: Files links without delete, `files_changed`, `persona_changed` and not while typing, `item_changed` per kind), new `page-wiring.test.mjs` (6: task card in place, pause/resume/stop, done card; status line; variant label and character; logout closes the socket). To test them, three handlers moved out of `app.js` without a change of behaviour: `followStatus` and `followVariant` (`mood.js`), the `socket.disconnect()` of the logout (`account.js`, new parameter `socket`). One browser click-through (`tests/test_chat_views_browser.py`, scenarios `views`, `lan`, `offline` of `tests/browser/chat_views.py`): `ui/tools/chat_views_e2e.js` runs with `*/character/*` blocked (TC-CLV-006), the variant label comes and goes (TC-CLV-013), every request and websocket event is on the page's host and named in IF-101 (TC-CLV-021; the allow-list is read from `contracts/IF-101-chat-api.md` plus `PENDING_A62`, emptied by A-62), `http://mia-lan:8686` (mapped to loopback) sends no login (TC-CLV-018), a closed transport keeps the draft and comes back without a reload (TC-CLV-004). `chat_views_e2e.js` now expects 7 tabs (F9) | JS 157 pass; browser test 10 OK (39 s). **Mutants** (the 12 survivors of the report, re-made on a scratch copy of `templates/`, `tests/js/`, `graph_app/`, `ui/`, `contracts/`, `tools/`; the three of `app.js` at their new places after the move): before (goal/v1 a262376) 0 of 12 killed, after 12 of 12 killed: history limit 50 -> 20; sender name ignored; a new card per `task_status`; a delete button in Files; pause posts resume; `persona_changed` / `files_changed` not redrawn; `chat_delta` ignored; account lines not drawn; logout without `socket.disconnect()`; mood line not updated; variant not passed to the character | see below |
| 5a | F7 (REQ-CLV-018): the change of password was sent over plain HTTP from a LAN address | `account.js` checks `secureChannel` (of `login.js`) before it sends and shows `login.insecure` | `page-wiring.test.mjs` (+2: http://192.168.1.20 sends nothing and says why; https sends once); red before | see below |
| 5b | F8: `chat_mock_server.py` logout with a connected page gave 500 (`deliver()` asked the mock for the events of the ended session) | `deliver()` skips a session the mock no longer knows | `test_chat_mock_server.py` new test with a connected socket of the same session: 200, that socket closed, ben's stays; red before (500) | see below |
| 5c | F9 lows | `chat_views_e2e.js` expects 7 tabs (in item 4); `architecture.sysml` `chatPage` lists the page's modules (not `sound.js`, N-1.3, nor `character.js`, the IF-111 bridge); `## Scenarios` in this node's `test-spec.md` (24 blocks, **Draft**, for the owner's review); docstrings with `Example:` and Given/When/Then in `test_chat_mock_server.py`, `test_chat_page.py`, `test_files_api.py` (code lines unchanged) | `check_sysml.sh` OK, `check_sysml_model.py` OK; `trace_check` for N-1.1: the scenarios ERROR is gone, the "no marker" WARNs stay (JS tests, N6 of N-1.3); `test_doc_check`: 0 findings in the three files and the new browser test | see below |
| 6 | F4 (REQ-CLV-021; D-163): IF-101 did not name the whole wire; the allow-list of TC-CLV-021 was the test's own; duplicate id TC-IF-101-30 | **Draft amendment A-62** (not installed): `specs/mia/amendments/A-62/A-62-note.md`, `tools/apply_amendment_a62.sh` (IF-101 next version built at install time: REST addresses table, `history` on the wire, `commands`, `backgrounds`, events `chat_status`, `chat_pipeline`, `audio_owner`, `audio_reload`, page events `audio_claim`, `audio_ended`, `character_ready`; A-54's rate-limit case TC-IF-101-30 -> TC-IF-101-33 in the suite and `specs/mia/test-spec.md`; `PENDING_A62` emptied). On this branch TC-CLV-021 (`multiuser.test.mjs`) already reads its allow-list from the contract (`contractWire`, same rules as the browser test) plus `PENDING_A62` | JS 160 pass; scratch copies: A-62 alone -> IF-101 suite 62 OK (2 skipped), JS 160 pass, browser test 10 OK with the set empty, second run unchanged; A-61 then A-62 and A-62 then A-61 -> v15, both rows, TC-IF-101-32 and -33; only A-61's real TC-IF-101-32 fails (needs v1-n33b's code) | see below |

Commits (in order of the items): 1 `7bb96db`, 2 `7e33b08`, 3 `b8d4360`, 4 `fb19571`, 5 `29d5cdd`, 6 `e434ee1`.
Runs at the end: `node --test "tests/js/*.test.mjs"` 160 pass, 0 fail; all 170 `tests/test_*.py` in the image (`tools/run_in_image.sh`, one container at a time): green except the two known failures (`test_amendment_report`, `test_harness` rt_edit); `tests/test_chat_views_browser.py` on the host 10 OK (own containers `n11-views-<random>`, removed).

### Open questions for Phase 4 and the owner
- REQ-CLV-011 does not mention the due time; D-163 decided the field, so the text (and AC-12) may need a plan amendment (behaviour now in code, M42).
- F1: the page counts places down at every `chat_start`. A task that sends `chat_start` only when its result is ready (IF-101 v8, the review) moves the shown places one step early while it runs; showing `chat_status.queue` would avoid that. Wording of "place 1" still the owner's (slice 1).
- The `## Scenarios` of `test-spec.md` are a Draft written in Phase 3: owner review.
- Three handlers moved from `app.js` to `mood.js` / `account.js` inside the F6 commit (needed to test them; no behaviour change), not as a separate `refactor` commit (M31).
- The browser check of TC-CLV-021 sees the socket events after the upgrade to the websocket only (the first events travel by polling); the mock server still has no `task_status`, `pause`, `files`, so TC-CLV-023/-024 stay unit-level (TD-01, TD-02).
- The mutation script (12 mutants, before/after) lived in the session's scratch folder; the mutants are listed in item 4 to be re-made.
- A-54's draft copy of the suite (`specs/mia/contract-drafts/...`) still numbers the rate-limit case 30; re-running A-54 needs A-62 again.

## After D-165 (2026-10-31)
- Merged goal/v1 (bc6df53 and earlier: A-59..A-61 installed, REQ-CLV-011 with the due time): no conflict. JS 160 pass.
- A-62 re-checked on a scratch copy of the merged branch: IF-101 v14 (A-61) -> **v15**, suite 64 OK (2 skipped), JS 160 pass, TC-IF-101-32 (A-61) and -33 (A-54's case) side by side.
- **Stop (F1 per D-165, not built):** IF-101 v14/v15 does not give the page what D-165 needs. (1) `chat_status.queue` is a count (`len(queue)` in `chat_service.py:185` and the mock), not the place of each waiting message; with a count alone the page cannot tell whose message is at which place (another user's message may wait behind mine), and sends and starts between two statuses cancel out. (2) `chat_start` is `{id, role}`: it does not name the message it answers, so the page cannot clear "only the answered message". Proposal for an IF-101 amendment (owner decides): `chat_status.queue` as the ordered list of waiting message ids (or `{id, position}` items), and `chat_start` with `reply_to` = the id of the message it answers (`null` for a regenerate or a task result); mock, real side and a contract case with it. Until then F1 stays as in 7bb96db.
