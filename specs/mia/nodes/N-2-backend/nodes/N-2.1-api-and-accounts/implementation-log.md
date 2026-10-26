# Implementation log: API and accounts (N-2.1)

Owner decisions of 2026-10-27 on the first slice: T-02 next; accounts are created from the command line only (no route, no `403 forbidden`, no `owner_account`: whoever has the machine is the owner); sessions need no timeout.

## T-01 Login, session, throttling, password, logout (first slice)
| Requirement | What was built | Tests |
|---|---|---|
| REQ-API-003 login | `api_sessions.SessionService.login`: the right password opens a session (random token, in memory), a wrong one or an unknown account is `401 bad_credentials`; `whoami`, `change_password` (old password checked, 8 characters, the old one stops working) | `tests/test_api_sessions.py` (TC-API-003) |
| REQ-API-004 throttling | five failed logins of an account within 60 s, then `429 throttled` even for the right password; other accounts unaffected; free again after 60 s | TC-API-004 |
| REQ-API-005 no password stored | only `accounts.py` hashes (scrypt); a search of the storage and of the log output after ten logins finds no password | TC-API-005 |
| REQ-API-006 accounts | the service has no way to create one; `tools/accounts_cli.py create NAME` on the machine (password asked for twice, never an argument) | TC-API-006 (the service has no `create_account`; `POST /api/accounts` is 404), `tests/test_accounts_cli.py` |
| REQ-API-017, REQ-BE-077 logout | `logout(token)`: the session never authenticates again (`401 unauthenticated`), other sessions of the account stay; listeners drop the sockets of the session | TC-API-017 |
| web side | `accounts_api.py`: `/api/login`, `/api/whoami`, `/api/change_password`, `/api/logout`; cookie `mia_session` (HttpOnly, SameSite=Strict, Secure on HTTPS, cleared at logout); `SocketSessions` + `guard_connect` / `forget_socket`: a socket without a session is refused with `unauthenticated`, the sockets of a session are disconnected at its logout | `tests/test_accounts_api.py` (with a real Flask-SocketIO app) |

## T-02 Authenticated requests, secure channel, attribution, everything visible
| Requirement | What was built | Tests |
|---|---|---|
| REQ-API-007 every request authenticated | `accounts_api.install_guard` (a `before_request`): open without a session are the page `/`, `/static/` and `/api/login`; every other path, also an unknown one, is `401 unauthenticated`; the socket handshake has its own guard. A foreign `Origin` header is `403 bad_origin`, also with a session (a request without `Origin` is not a browser page and passes). The message rate limit (`chat_rate_per_minute`) is now per account, not per connection: two devices of a user share one limit | TC-API-007 |
| REQ-API-007 our own processes | the speech process posts the audio to `/upload`, the scheduler calls `/time`: `internal_auth.py` makes a random secret at start (`MIA_INTERNAL_TOKEN`, inherited by the speech process, which `__main__` starts after importing `web_app`); `play_media.play_sound` and `time_update_trigger` send it in `X-MIA-Internal`; the guard lets exactly those two paths pass with it, nothing else | `tests/test_internal_auth.py`, TC-API-007 |
| REQ-API-008 secure channel | `POST /api/login` and `/api/change_password` are `403 insecure_channel` unless the request is HTTPS or comes from this machine (127.0.0.1 or ::1); `X-Forwarded-Proto: https` counts only from this machine (the socat proxy of `https_port` and `tailscale serve` run here) | TC-API-008 |
| REQ-API-009 attribution | `accounts_api.ChangeLog`: every successful POST, PUT, PATCH or DELETE after the guard, and every `chat_send`, becomes one line `{time, account, action, target}` in `data/changes.jsonl` (config key `changes_log`); the content is not written; login, logout and the password are not changes of shared data; refused requests are not recorded | TC-API-009 |
| REQ-API-010 everything visible | the guard makes no decision per account, there are no roles; two users read and change the same data | TC-API-010 |

Tests that pass: `test_internal_auth` (3), `test_accounts_api` (24), `test_api_sessions` (8), `test_accounts_cli` (3), and unchanged `test_config`, `test_accounts`, `test_chat_backend`, `test_chat_page`, `test_chat_mock_server`. An end-to-end run of the real `web_app` in the image (config with `accounts_enabled`): page open; history, presets and upload 401; upload with the secret reaches the route; foreign origin 403; plain-HTTP login from a LAN address 403; login; history 200; socket accepted; a chat message is recorded with the account and without its text; logout drops the socket. (The script is not kept: it rewrites `setup_cfg.json` for a moment.) New helper `tools/run_in_image.sh` runs test files in the MIA image.

## Switching it on
In `setup_cfg.json`: `"accounts_enabled": true`; make the first account with `python3 tools/accounts_cli.py create NAME`; restart MIA. Off by default (`false`).

## Findings
- **F-1: with the switch on, the old pages need the session too.** The character page (`/character/`), backgrounds and audio files are behind the guard (they hold the owner's data); the chat page loads and shows the login, after the login it reloads. The Godot editor in the browser and the gesture editor therefore work after a login in the same browser. Not tried in a browser.
- **F-2: the codes `403 bad_origin` and `403 insecure_channel` are not in IF-101.** The contract lists 401, 404, 409, 422, 429, 503. The page shows a generic error for them; the login page already warns about plain HTTP on its own (`login.insecure`). Add them to IF-101 by amendment if the contract should name them.
- **F-3: change attribution is a log file, not a column.** The old stores (presets, gestures, persona file, chat log) have no author field; REQ-API-009 is met at the API: who made which change on which path. With the database (N-3) the author goes into the record itself (`put(..., author)`); then this log is only the audit trail.
- **F-4: sessions live in memory** (decided: no timeout). A restart of MIA logs everybody out.
- **F-5: the contract suite still skips the real provider.** `tests/helpers/contract.py` (protected) has `REAL_NOT_READY["IF-101"]`; running TC-IF-101-01, -02, -10 and -18 against `SessionService` needs an amendment like A-02, and its `ApiError` must be the one of the mocks' `errors.py` (same fields, another class).
- **F-6: not yet in the real backend:** the other operations of IF-101 v1 (regenerate, speak again, votes, score, records, trust, persona, account of an answer, variant) belong to T-03 and the other N-2 nodes; the page copes with their absence.
- The logout button works against the mock server today; against the real backend it works as soon as `accounts_enabled` is on.
