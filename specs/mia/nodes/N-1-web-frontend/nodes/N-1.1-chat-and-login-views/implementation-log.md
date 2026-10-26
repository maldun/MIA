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
