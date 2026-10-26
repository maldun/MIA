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
