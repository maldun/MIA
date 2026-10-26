# Implementation log: API and accounts (N-2.1)

## T-01 Login, session, throttling, password, owner-only accounts, logout (2026-10-27, first slice)
| Requirement | What was built | Tests |
|---|---|---|
| REQ-API-003 login | `api_sessions.SessionService.login`: the right password opens a session (random token, in memory), a wrong one or an unknown account is `401 bad_credentials`; `whoami`, `change_password` (old password checked, 8 characters, the old one stops working) | `tests/test_api_sessions.py` (TC-API-003) |
| REQ-API-004 throttling | five failed logins of an account within 60 s, then `429 throttled` even for the right password; other accounts unaffected; free again after 60 s | TC-API-004 |
| REQ-API-005 no password stored | only `accounts.py` hashes (scrypt); a search of the storage and of the log output after ten logins finds no password | TC-API-005 |
| REQ-API-006 owner only | `create_account`: only the configured owner (`owner_account`); others `403 forbidden`; a taken name `409`; a weak password `422`; without an owner nobody | TC-API-006 |
| REQ-API-017, REQ-BE-077 logout | `logout(token)`: the session never authenticates again (`401 unauthenticated`), other sessions of the account stay; listeners drop the sockets of the session | TC-API-017; `tests/test_accounts_api.py` |
| web side | `accounts_api.py`: routes `/api/login`, `/api/whoami`, `/api/change_password`, `/api/logout`, `/api/accounts`; cookie `mia_session` (HttpOnly, SameSite=Strict, Secure on HTTPS, cleared at logout); `SocketSessions` + `guard_connect` / `forget_socket`: a socket without a session is refused with `unauthenticated`, the sockets of a session are disconnected at its logout | `tests/test_accounts_api.py` (11, with a real Flask-SocketIO app) |
| wiring | `web_app.py`: if `accounts_enabled` the blueprint is installed and the connect/disconnect handlers guard the sockets; keys `accounts_enabled` (false), `accounts_dir` (`data/db`), `owner_account` (empty) in the config and its example; `tools/accounts_cli.py create NAME` makes the first account (password asked for, never an argument) | `tests/test_accounts_cli.py`; an end-to-end run of the real `web_app` in the image: no session 401, login, socket accepted, foreign socket refused, logout drops the socket (script not kept: it rewrites `setup_cfg.json` for a moment) |

Tests that still pass: `test_config`, `test_accounts`, `test_chat_backend`, `test_chat_page`, `test_chat_mock_server`. New helper `tools/run_in_image.sh` runs test files in the MIA image.

## Findings and decisions needed
- **F-1: the rest of the Backend is not protected yet.** With `accounts_enabled` the login exists and the sockets need a session, but the REST routes of the old backend (chat API, presets, gestures, uploads) still use the editor token and open routes. Refusing every request without a session is T-02 (REQ-API-007). Therefore the switch is off by default and the page does not use the new login yet.
- **F-2: `/api/accounts` and `403 forbidden` are not in IF-101 v1/v2.** REQ-API-006 and REQ-BE-011 say that only the owner creates an account, but the wire contract has no operation for it. I added the route for the owner's tool and used `403 forbidden` (the contract lists 401, 404, 409, 422, 429, 503). Decide: keep it (then IF-101 gets `create_account` and 403 by amendment) or drop the route and leave account creation to `tools/accounts_cli.py` only.
- **F-3: the owner is a config value.** The documents do not say who the owner is; I took `owner_account` in `setup_cfg.json`.
- **F-4: sessions live in memory.** A restart of MIA logs everybody out; they never expire by time. Neither is in the requirements; say if a timeout is wanted.
- **F-5: the contract suite still skips the real provider.** `tests/helpers/contract.py` (protected) has `REAL_NOT_READY["IF-101"]`; an adapter that runs TC-IF-101-01, -02, -10 and -18 against `SessionService` needs an amendment like A-02 (the adapter would also have to raise the `ApiError` of the mocks' `errors.py`; `api_sessions.ApiError` has the same fields but is another class).
- The user-visible logout works against the mock server today; against the real backend it works after the page uses the real login (T-02/T-03).
