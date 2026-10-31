# Verification report: Chat and login views (N-1.1)

**Goal:** G-V1 (iteration), supervised; node N-1.1 (leaf) verified as a black box against the IF-101 mock (and the IF-111 / IF-112 mocks where used)
**Branch:** goal/v1 @ 49f191b (review start; HEAD moved to 3620732 during the review by merges of other nodes: none of them touches an N-1.1 file, `git diff --stat 49f191b 3620732 -- templates tests/js ui/tools contracts tests/helpers` = `sound.js` and `voice-player.test.mjs` only)   **Parent line of work:** master   **Plan baseline:** plan-baseline-it1
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context; it never saw the implementation chat)
**Commits reviewed (N-1.1 files):** on master before 53c6766: def2175 (slice 1), a883c27 (slice 2), af54bb4, 22d61b5 (logout, A-04), 562fade, 16393fa (T-09: status card, Files tab), 344484c (login behind a trusted proxy); on goal/v1: 9bceaa5, 95d293a (confirmation of /light! /full!, REQ-RUN-002, not an N-1.1 requirement; in bounds of `app.js`/`chat-model.js`), 9d0bc1f (one line of `app.js` for N-1.3, judged there).
**Not judged:** the branches v1-n12c and v1-n13d (not merged at the start; v1-n13d was merged as 3620732 during the review) change `index.html`, `character.js` and `sound.js`; those changes belong to N-1.2 / N-1.3.

## Verdict (proposal)
**Not verified.** Two Must requirements have defects that a browser shows: the queue position of a waiting message disappears as soon as any answer starts (REQ-CLV-002, F1), and the answer actions are 32 px wide on a touch screen (REQ-CLV-016, F3). Most stage-2 browser checks of `test-spec.md` were replaced by unit or static tests, and the page wiring (`chat.js`, `workspace.js`, `task-card.js`, `app.js`) has no test that fails on a defect (F6). After F1 and F3 are fixed test-first and the owner decides F2, F4, F5 and F6, the expected status is *verified with accepted deviations* (REQ-CLV-007 and the phone part of -016 by checklist; REQ-CLV-023/-024 under TD-01/TD-02).

## Automated checks (local runs, no CI)
| Check | Result |
|---|---|
| Stage log | no CI run exists for this node; all results are the reviewer's local runs |
| JS unit tests `node --test "tests/js/*.test.mjs"` | 132 pass, 0 fail at 49f191b; 134 pass, 0 fail at 3620732 |
| JS contracts + N-1 integration `node --test tests/acceptance/contract/*.mjs tests/integration/N-1/*.mjs` | 33: 17 pass, 16 skipped (`[real]` sides and later N-1 steps), 0 fail |
| IF-101 contract suite (Python, MIA image, `--network none`) | `test_if_101_chat_api.py`: 60 tests OK, 3 skipped on the real side (TC-IF-101-17 variant: REQ-CHV-008 out; TC-IF-101-04 expression/audio_chunk: N-2.5; TC-IF-101-06 stop before start: N-2.2 T-01) |
| Node's Python tests (MIA image `localhost/mia:latest` 6033e7b5, `--network none`, one container at a time) | `test_chat_mock_server.py` 13 OK; `test_chat_page.py` 11 OK; `test_files_api.py` 4 OK |
| Browser runs of the reviewer (headless Chromium 156 of `localhost/mia-browser` ea481da5, own mock container `n11verify-mock-*` with `--network none`, the browser in its network namespace: loopback only; a fresh mock per run, removed afterwards) | (a) `ui/tools/chat_views_e2e.js` after a login as anna: one problem, "six tabs" (the page has seven since T-09, F9); everything else as expected (five actions, vote marked, account 2 steps and hidden again, regenerate moves to the new answer, variant label "Outfit: summer", tasks, memory needs a source, delete, trust 0.2 kept, persona kept, score overall +1 and four categories, account dialog with the three password errors). (b) Queue: two quick messages show "Waiting, place 1" and "place 2"; at the first `chat_start` both texts go blank although the second still waits (F1). (c) Connection cut (engine closed, reconnect delay 5 s): state `offline` with banner, Send disabled, draft "my unsent draft" kept, `online` again after 5 s without a reload (REQ-CLV-004 behaviour met; no committed test). (d) Viewports 360, 768, 1440 in dark and light: no horizontal scroll; with a fine pointer the answer actions are 32x17 and Copy 38x17; with mobile emulation (360 px, touch, `pointer: coarse` true) the answer actions are **32x44** (F3). (e) Logout on the mock stage: "Logging out failed." although the session ended (mock server 500, F8); after a reload the login is shown. (f) 482 requests of all sessions: 0 outside `127.0.0.1:8686` (REQ-CLV-017). Containers: the mock and the browser ran at the same time (the check needs both), never more than these two |
| Delivery / no outside request on the stack | not re-run: TC-VPB-004 (`test_page_requests.py`) and TC-VPB-005 (`test_delivery_on_stack.py`) ran green in the N-1.3 re-verification 2 at f4da817 on the same chat page; `git diff --stat f4da817 49f191b -- templates deploy web_app.py` is empty |
| Protected material vs. baseline | `contracts/IF-101-chat-api.md`, `IF-111`, `IF-112`, `tests/helpers/mocks/if_101_chat_api.py`, `tests/acceptance/contract/test_if_101_chat_api.py`, `tests/helpers/contract.py`, `contract.mjs`, `tests/integration/N-1/`: every change since plan-baseline-it1 is an "A-nn installed" commit (A-03..A-09, A-20..A-27, A-32, A-36, A-48, A-49, A-51); goal/v1 vs master differs only by A-49 (IF-101 v11), A-48 (IF-111 v2), A-36/A-51/A-52 helper lines. None of the seven N-1.1 implementation commits touches a protected file |
| Traceability (`trace_check.py --spec-dir specs/mia --tests-dir tests`) | for N-1.1: ERROR `test-spec.md` 24 checks but no `## Scenarios` (M39); WARN "no mark.req marker" for REQ-CLV-003, -004, -006, -008, -009, -010, -012, -013, -016, -017, -018, -020, -021, -023, -024 (JS tests carry the TC id in the name only; the tool reads the first id of a Python marker only, N6 of N-1.3); WARN TD-01, TD-02 "not listed in a verification report" (listed below) |
| `test_doc_check.py --tests-dir tests` | `test_chat_mock_server.py` 19 errors, `test_chat_page.py` 20, `test_files_api.py` 6 (no docstrings, no `Example:`, no Given/When/Then); the JS files are not read by the tool (F13) |
| Model | `python3 -I tools/check_sysml_model.py .`: OK. `architecture.sysml:206-207` names only `index.html`, `app.js`, `chat.js`, `mood.js` as modules of `chatPage` (F10) |
| Refactoring commits / agent configuration | no `refactor:` commit of this node; no agent configuration touched |
| Static / security | no linter configured (CLAUDE.md). Answers go through `renderMarkdown` (marked + DOMPurify, `markdown.js`); user text is built with text nodes and `linkify` (links `rel=noopener noreferrer`); workspace, account, task card and the account of an answer use `textContent`; file links use `encodeURIComponent`; the page makes requests only through `api.js`, `login.js`, `chat.js` history and the socket; strict CSP tested by `test_chat_page.py`. No shell, no `eval`. Privacy findings rank low (D-131) |
| Usability with bad inputs (by code and the e2e run) | empty login fields, wrong password, throttling, wrong channel, foreign address: each named; empty record, memory without source, trust "50%" or 1.5, empty persona, short/different/same password: refused with a reason before sending; offline actions say "offline". Gaps: F7 (change of password over plain HTTP is sent), F2 (a task edit drops its due time) |
| Deployable artifact | the page is part of the MIA image (N-1.3 evidence above) |

## Mutation checks (scratch copy of `templates/` and `tests/js/`, removed afterwards)
Run against `multiuser`, `panels`, `logout`, `api`, `chat`, `taskcard`, `confirm`, `no-outside-requests`, `character-bridge`, `settings` (70 tests, all green unmutated).

| Killed (pure helpers) | Survived (page wiring) |
|---|---|
| `secureChannel` always true (2 fail); `submitLogin` without channel check (1); `queueText` without position (1); `senderName` always "You" (1); `latest` ignores done (1); logout does not report (2); an address outside IF-101 in `api.js` (2); vote category changed (1); regenerate never offered (1); trust without upper bound (1); login text gone from `index.html` (1) | `app.js` logout without `socket.disconnect()`; history `limit` 50 -> 20; `chat.js` ignores the sender name; a new task card per `task_status` (no update in place); a delete button in the Files list; `pause` posts `/api/resume`; mood line not updated; `persona_changed` / `files_changed` not redrawn; variant not passed to the character; `chat_delta` ignored (no streaming); account lines not drawn |

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-CLV-001 sender, streaming | Test | `multiuser.test.mjs` TC-CLV-001 (2, `senderName`, `continuesGroup`; mutant killed); contract TC-IF-101 mock+real; e2e (a): scripted answers arrive | **Met** in the browser; the drawing in `chat.js` (sender in the row, deltas) has no test (mutants survive, F6) | yes |
| REQ-CLV-002 stop, queue position | Test | TC-CLV-002 (`queueText` 2 tests); mock server positions 1..3; stop: text match in `voice-player.test.mjs:364` | **Not met**: `chat.js:378` clears the "Waiting, place n" of every waiting message at the first `chat_start`; positions never move up (F1, browser run b) | the green tests check the text helper only |
| REQ-CLV-003 shared history | Test | none named TC-CLV-003; `chat.test.mjs` upsert/order tests; `chat.js:300` limit 50 (mutant survives) | **Met by inspection** (history on load and on every reconnect, live `chat_message`); no test of AC-1 (F6) | – |
| REQ-CLV-004 connection state, draft | Test | none named TC-CLV-004; reviewer's browser run (c) | **Met** in the reviewer's run; no committed test (F6) | yes |
| REQ-CLV-005 regenerate, speak again | Test | `panels.test.mjs` TC-CLV-005 (`lastAnswerId`), `api.test.mjs` addresses; contract TC-IF-101 regenerate/speak; e2e (a) | **Met** | yes |
| REQ-CLV-006 chat without character | Test (stage 2 browser) | every reviewer run with `?character=0` and `/character/` answering 404: send and answer work; `character-bridge.test.mjs` | **Met**; the specified stage-2 test does not exist (F6) | yes |
| REQ-CLV-007 character as stage | Demonstration | `ui/CHECKLIST_CHAT_PHONE.md`; reviewer: panel `fixed`, no horizontal scroll at 360/768/1440 | **Open: owner's checklist** (collapsed view with caption not checked) | – |
| REQ-CLV-008 status line, account of an answer | Test, Demonstration | contract TC-IF-101 account (mock+real, v11); mock server test; e2e (a) 2 steps, hidden again | **Met** in the browser; the drawing (mood update, account lines) has no test (mutants survive) | yes |
| REQ-CLV-009 persona live | Test | contract TC-IF-101 persona; mock server test (`persona_changed` reaches the other page); e2e persona kept | **Met by inspection** (`workspace.js:203` redraws the open tab, not while typing); the page side has no test (mutant survives) | – |
| REQ-CLV-010 votes and score | Test, Demonstration | `panels.test.mjs` (`voteArgs`, `scoreLines`), contract; e2e score +1 | **Partly**: plus/minus only on answers (`answer_quality`); no vote on reactions or behaviours; totals only, `series` (IF-101 v4, A-06 "over time") not drawn (F5) | – |
| REQ-CLV-011 tasks, memos, memory | Test | `panels.test.mjs` (`itemDraftError`), contract, mock server, e2e | **Met** for list, add, edit, delete; but a task edit drops `due` and `due` is never shown or set (F2) | – |
| REQ-CLV-012 source trust | Test | `panels.test.mjs` (`parseTrust`), contract (`trust_changed {source, old, new}`), e2e 0.2 kept | **Met** (the page sends source and new value; old/new are in the server's event, IF-101) | yes |
| REQ-CLV-013 variant label | Test (stage 2 browser) | `panels.test.mjs` (`variantLabel`), `character-bridge.test.mjs`; e2e "Outfit: summer" | **Met** for the label and the pass to IF-111; the outfit change itself is out (REQ-CHV-008, D-137); no stage-2 test (F6) | yes |
| REQ-CLV-014 login, password, account | Test | `multiuser.test.mjs` (4), `panels.test.mjs` (`passwordProblem`), `api.test.mjs`, contract, mock server, e2e | **Met** | yes |
| REQ-CLV-015 visible to all | Inspection | `index.html:191`, `en.json:104`, `de.json`; test TC-CLV-015 (mutant killed); browser (a) text shown | **Met** | yes |
| REQ-CLV-016 accessibility, devices | Test, Demonstration | `ui/tools/chat_a11y.js` (manual tool), `a11y.js`; reviewer run (d) | **Not met**: on a touch screen the answer actions are 32x44 px (`components.css:439` beats `messages.css:278`, F3); the specified stage-2 test does not exist; keyboard/screen reader and Safari/Firefox by the owner's checklist | – |
| REQ-CLV-017 no outside request | Test (stage 2 browser) | TC-VPB-004 browser test (N-1.3, green); `no-outside-requests.test.mjs`; reviewer run (f): 0 of 482 | **Met** | yes |
| REQ-CLV-018 password only over HTTPS/localhost | Test (stage 2 browser) | `multiuser.test.mjs` TC-CLV-018 (2, unit; mutants killed) | **Met for the login**; the change of password has no channel check (F7); the browser test was not run (no LAN address available here) | yes |
| REQ-CLV-019 plain stack | Inspection | no bundler files (only `templates/static/package.json` `{"type": "module"}`), ES modules, vendored libraries; Godot: `project.godot` features "4.6", 4.6.1 in `ui/README.md` (N-1.2 part) | **Met** | – |
| REQ-CLV-020 delivered by the backend | Test (stage 3) | TC-VPB-005 on the compose stack (N-1.3 re-verification 2, 5/5 OK), no frontend service | **Met** (evidence reused, unchanged files) | yes |
| REQ-CLV-021 IF-101 only | Test (stage 2 browser) | `multiuser.test.mjs` TC-CLV-021 static scan (mutant killed); browser (f) | **Partly**: the page also uses `chat_pipeline`, `audio_claim/owner/reload/ended`, `character_ready`, `/api/chat/commands`, `/character-backgrounds.json` and the history shape `{messages, older}` with `before`, none of them in IF-101; the test's allow-list is wider than the interface (F4) | – |
| REQ-CLV-022 logout | Test | `logout.test.mjs` (4, mutants killed); mock server and contract logout tests | **Met** on the account dialog; the page's `socket.disconnect()` has no test (mutant survives); on the mock stage the logout fails (F8) | yes |
| REQ-CLV-023 status card (Draft, TD-01) | Test + checklist | `taskcard.test.mjs` (4, named TC-WFM-031/-033; mutant on `latest` killed) | **Interim criterion met** (the model of the card); update in place, pause/resume and the card in the chat untested (mutants survive); the mock server has no `task_status`, so no browser check was possible | – |
| REQ-CLV-024 files list (Draft, TD-02) | Test | `test_files_api.py` 4 OK, contract TC-IF-101-30; inspection of `workspace.js:131-145` (link `/api/files/<name>`, no delete, redraw on `files_changed`) | **Interim criterion met**; no page test (mutants "delete button", "no redraw" survive); the order is the server's (IF-101 "newest first") | – |

## Test requirements (M41)
| Test requirement | Source | Kind | Applies to | Credibility aspect | Verified by | Met? |
|---|---|---|---|---|---|---|
| – | – | – | – | – | – | `test-requirements.md` has no TR items (global WARN of trace_check). The credibility gap of this node: the IF-101 mock server (`ui/tools/chat_mock_server.py`) is the only page-level stand-in, and it has no `task_status`, `pause`, `files` and fails on logout with a connected page (F8) |

## Goal acceptance (node part)
| Item | Result |
|---|---|
| Requirements of N-1.1 verified | 24 in scope: 14 met (001, 004*, 005, 006, 008, 012, 013, 014, 015, 017, 019, 020, 022, 003 by inspection; *by the reviewer's run only), 5 partly (009 by inspection, 010, 011, 018, 021), 2 not met (002, 016), 1 open demonstration (007), 2 Draft under deferral (023, 024) |
| Frozen requirements unchanged | G-V1 has no frozen requirements |
| Protected checks identical to the parent's baseline | yes, except installed amendments (table above) |
| Nothing outside the node's parts touched | 344484c also changes `accounts_api.py`, `deploy/`, `web_app.py`, `setup_cfg*.json` (N-2.1 / N-4.2 side of the same fix); 22d61b5 committed `mia.log` (removed later, `.gitignore:36`) (F12) |
| Every stop condition logged | yes for the IF-101 v0 gap (log "Stop", owner's decision "slice first"); T-09 is not in this node's log (logged in N-2.3's, F12) |
| Exit criterion | checked in Validate (VAL-001, VAL-003..006) |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-CLV-002 position while waiting | F1 | Phase 3 |
| specified, not done | REQ-CLV-016 touch targets 44 px | F3 | Phase 3 |
| specified, not done | REQ-CLV-010 votes on reactions and behaviours, score over time | F5 | owner: build, or amend REQ-CLV-010 |
| specified, not done | REQ-CLV-018 for the change of password | F7 | Phase 3 |
| specified, not done | stage-2 browser checks TC-CLV-006, -013, -016, -017 (as CLV), -018, -021 and component tests TC-CLV-003, -004 | F6 | Phase 3 tests, or a test-spec amendment |
| done, not specified | the page's wire beyond IF-101 (F4) | IF-101 amendment | Phase 2 |
| done, not specified | a task edit clears `due` (IF-101 says so); the page has no `due` field | F2 | owner decision |

Human review: the specification side via `review-log.md`; code read in full by the reviewer for `app.js`, `api.js`, `chat.js`, `chat-model.js`, `login.js`, `account.js`, `workspace.js`, `panels-model.js`, `task-card.js`, `task-card-model.js`.

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | CLV-001..014, -022..-024 | JS unit tests, contract suite, e2e click-through, reviewer's browser runs | partly | F1, F2, F5 |
| Performance efficiency | – | `test_chat_page.py` performance budget of the page | met | no N-1.1 budget beyond that |
| Compatibility | CLV-016 (browsers), CLV-021 | Chromium 156 only | partly | Firefox, Safari iOS by the owner; F4 |
| Interaction capability | CLV-016, CLV-023 (360 px) | reviewer run (d), mobile emulation | not met | F3; the card at 360 px not checked (no `task_status` in the mock) |
| Reliability | CLV-004 | reviewer run (c) | met (no committed test) | F6 |
| Security | CLV-017, -018, -015 | CSP test, TC-VPB-004, unit tests, code reading | partly | F7 (Low, D-131) |
| Maintainability | CLV-019 | inspection; test_doc_check | partly | F6, F10, F13 |
| Flexibility | – | – | not now | no requirement for this node |
| Safety | – | – | not now | no requirement for this node |

## Open deferrals (M26)
| TD | Requirement | Interim criterion verified? | Target check state | Trigger |
|---|---|---|---|---|
| TD-01 status card not in a browser, gone after a reload | REQ-CLV-023 | yes: `taskcard.test.mjs` 4 green; the drawing only by the owner's hand test | specified only | a browser harness for N-1 or 2026-12-31; **Decision line still "proposed, to be confirmed by Stefan Reiterer"** |
| TD-02 Files tab not in a browser | REQ-CLV-024 | yes: `test_files_api.py` 4 OK, TC-IF-101-30 green | specified only | as TD-01; **still proposed** |

A browser harness now exists (`localhost/mia-browser`, D-141, used by `test_page_requests.py`), which is one of the two triggers of TD-01 and TD-02.

## Review findings
| # | Finding | Severity | Needs | Proposal |
|---|---|---|---|---|
| F1 | `templates/static/chat/chat.js:378`: on every `chat_start` the page clears `local: 'queued'` of **all** waiting messages, so "Waiting, place n" disappears while a message still waits; positions never move up (2 -> 1). Browser run (b): `q one=Waiting, place 1 \| q two=Waiting, place 2` -> at the first answer `q one= \| q two=`. TC-CLV-002 tests only `queueText` | Medium (Must, REQ-CLV-002) | test | a page test (fake socket and DOM, or the stage-2 browser test): two waiting messages, one `chat_start`, the second still shows a place; then clear only the message that is answered (the user message before the started answer) and count the others down; or show the queue count from `chat_status.queue`. Owner decides the wording of place 1 (log, slice 1) |
| F2 | `templates/static/chat/workspace.js:73` and `api.js:46`: a task is saved without `due`, and IF-101 v6 says "a save without `due` clears it" (`items_api.py:88-91`): editing the text of a task removes its due time and its `recited` mark. The page also never shows or sets `due`, so no user can give a task the due time that REQ-CHA-019 recites | Medium | owner decision + test | (a) keep `due` on edit (`saveItem(kind, id, text, source, item.due)`) with a test in `api.test.mjs`/a page test; (b) owner: a due field in the Tasks tab (REQ-CLV-011 amendment) or due times only through the chat |
| F3 | `templates/static/chat/components.css:439` `.link-button.action { min-width: 32px }` outranks `messages.css:278` (`.link-button { min-width: 44px }` under `pointer: coarse`): with a touch screen the five answer actions are 32x44 px (mobile emulation, 360 px). REQ-CLV-016 AC-1: touch targets of 44 px or more | Medium (Must) | test | the stage-2 browser test of TC-CLV-016 (it does not exist; `ui/tools/chat_a11y.js` measures, but is manual): coarse pointer, 360 px, every visible control >= 44 px; then `min-width: 44px` for `.link-button.action` under `pointer: coarse` |
| F4 | IF-101 does not describe parts of the wire the page uses: socket events `chat_pipeline`, `audio_claim`, `audio_owner`, `audio_reload`, `audio_ended`, `character_ready`; REST `/api/chat/commands`, `/character-backgrounds.json`; the history is `{messages, older}` with `before` (`chat.js:298-309`, `chat_api.py:22`) while IF-101 says "list of messages, oldest first" with `limit` only. `audio_chunk` of IF-101 is not used by the page. The allow-list of TC-CLV-021 (`tests/js/multiuser.test.mjs:115-120`) is wider than the interface, so REQ-CLV-021 "only through IF-101 as specified" is not shown | Medium | amendment | IF-101 v12+: add the events and routes the page and the backend really share (or name a second interface for the voice/character events), the history shape with `before`/`older`; then TC-CLV-021 checks against a list taken from the contract text, not its own list |
| F5 | REQ-CLV-010: the page votes only `answer_quality` on answers (`panels-model.js:16-19`); no plus/minus on reactions or behaviours; the Score tab shows totals and ignores `series` (IF-101 v4, A-06: "score over time, per week") | Medium (Should) | owner decision | build the two missing vote places and a per-week list or curve from `series` (test-first), or amend REQ-CLV-010 / AC-18 to what is built |
| F6 | The page wiring has no test that fails on a defect: 12 mutants of `chat.js`, `workspace.js`, `task-card.js`, `app.js` survive (table above). TC-CLV-003, -004 (component) and the stage-2 browser checks TC-CLV-006, -013, -016, -018, -021 do not exist as specified; TC-CLV-023/-024 are covered by model and route tests only (TD-01/-02). `test_chat_mock_server.py` tests the mock server tool, not the page | Medium (checks outside their specification) | test or amendment | a page test layer on fakes (as `sound.js` got in N-1.3: fake socket, minimal DOM) for `chat.js`, `workspace.js`, `task-card.js` and the logout wiring of `app.js`, plus one stage-2 browser test in the image of D-141 against the mock server (positions, offline/draft, touch targets, no outside request, logout); or the owner amends `test-spec.md` to accept unit + checklist |
| F7 | `templates/static/chat/account.js:24-36`: the change of password is sent without `secureChannel` (`login.js:7`); over plain HTTP from a LAN address (reachable with `accounts_enabled` off, D-149 V-4) both passwords travel in clear before the server answers `403 insecure_channel`, which the page then shows as "failed" | Low (REQ-CLV-018; D-131) | test | a test in `logout.test.mjs`/`panels.test.mjs`: on `http://192.168.x.x` the form sends nothing and says why; then the same check as the login |
| F8 | `ui/tools/chat_mock_server.py:166` with `:146` and `:113`: `r_logout` calls `run_api`, whose `deliver()` asks the mock for the events of every token in `sids`, including the token that was just logged out -> `ApiError 401` -> HTTP 500. With a connected page (every real use of the stage `chat-with-login`) the page says "Logging out failed." while the session has ended. `test_chat_mock_server.py:141` passes because no socket is connected | Low (test tool; misleads the owner's hand test of REQ-CLV-022) | test | a mock server test with a connected socket of the same session; then pop the token from `sids` before `deliver()` (or skip dead tokens) |
| F9 | `ui/tools/chat_views_e2e.js:58` expects six workspace tabs; there are seven since 16393fa (Files), so the click-through reports a problem on a correct page | Low | – | update the tool when F6's browser test is written (or make it the browser test) |
| F10 | `specs/mia/architecture.sysml:206-207`: `chatPage` lists `index.html`, `app.js`, `chat.js`, `mood.js` only; `login.js`, `account.js`, `api.js`, `workspace.js`, `panels-model.js`, `chat-model.js`, `task-card*.js`, `composer.js`, `socket.js` are not in the model | Low | amendment | list the modules (or a folder) in the `@Implementation` of `chatPage` |
| F11 | Plan: `test-spec.md` has no `## Scenarios` (trace ERROR, M39); JS tests carry no marker that `trace_check` reads (15 WARN); TD-01 and TD-02 are still "proposed" and REQ-CLV-023/-024 "Draft" | Low (plan) | owner decision | confirm or change TD-01/-02 (a trigger, the browser harness, is met); scenarios for the 24 checks; a JS marker convention (same as F8 of N-1.3) |
| F12 | Commits: T-09 (16393fa) is not in this node's implementation log; 344484c mixes the page with N-2.1/N-4.2 code; 22d61b5 committed `mia.log` (later removed); the slices are 2 commits for 8 tasks | Info | – | note for the commit phase |
| F13 | `test_doc_check`: `test_chat_mock_server.py` 19 errors, `test_chat_page.py` 20, `test_files_api.py` 6 | Low | – | docstrings with `Example:` and Given/When/Then (as N-1.3 a804a30) |

Shared with the sibling reports and not repeated: N-1.3 N4 (browser `--network host` in `test_page_requests.py`), N6 (trace_check reads the first id of a marker only), F8 (scenarios, JS markers) of N-1.3; N-1.2's IF-111 findings.

## Accepted deviations
None yet. Candidates: REQ-CLV-007 and the phone/browser part of REQ-CLV-016 by checklist; REQ-CLV-020 evidence from the N-1.3 stack run; F6 if the owner accepts unit tests + checklist instead of the stage-2 browser checks.

## Manual checks for the owner (browser)
Start `bash tools/start_testing.sh start chat-with-login`, open `http://127.0.0.1:8686/?character=0`, log in as anna / pw-anna.
1. **Queue (F1):** send three messages quickly (a second browser as ben for the third): each shows its place; when the first answer starts, watch whether the others still show a place.
2. **Phone (REQ-CLV-007, -016, F3):** on a phone in the home network: chat as bottom sheet, collapse shows the caption; tap 👍 👎 🔊 ⓘ ↻ under an answer: are they easy to hit? Dark and light theme, reduced motion, a screen reader (TalkBack/VoiceOver) reads new answers.
3. **Logout (F8):** menu, Log out: today the mock stage says "Logging out failed."; a reload shows the login. On the real stack (`deploy/up.sh`) the same steps should log out at once.
4. **Task with a due time (F2):** only if due times are set by another route: edit the text of such a task and check whether MIA still recites it.
5. **Status card and Files (TD-01, TD-02):** on the real stack, `/review` a short question: the card updates in place, pause becomes resume, stop ends it, the card stays with the final figures; the Files tab lists the new file newest first and downloads it.

## What could not be checked
- Firefox and Safari (iOS), a real phone, a screen reader, reduced motion (only Chromium 156 headless).
- The status card and the Files tab in a browser (the mock server has no `task_status`, `pause`, `files`).
- REQ-CLV-018 in a browser from a LAN address (no second machine; unit tests only).
- The real backend behind the page in a browser (no model server allowed); the stack run of TC-VPB-005 was reused, not repeated.
- The CI stage log (none exists).

## Notes for Phase 7 (validation)
- Whether users read "Waiting, place 1" as "answered next" (wording decision of slice 1).
- Whether the score as totals is enough or users want to see it per week (F5).
- FB-01 moves the status card to a skills panel (next iteration); TD-01's reload part goes with it.
