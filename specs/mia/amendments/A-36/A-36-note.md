# A-36: a JavaScript mock of IF-104 for the Graph app (N-5 Q-3, D-122)

Status: **proposed** (drafts for the owner to read and install; nothing protected is changed by the agent).

## Why
The test spec of N-5 sets TC-GA-002 to TC-GA-008 up as "unit test against the mock of IF-104". The installed mock (`tests/helpers/mocks/if_104_graph_api.py`) is an in-process Python object, the Graph app is a JavaScript page that speaks the HTTP routes of IF-104. The owner chose option (a) of Q-3 (D-122): a protected JavaScript mock, installed before N-5 T-02.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `contracts/IF-104-graph-api.md` | `specs/mia/amendments/A-36/IF-104-graph-api.md` | v1: a section "Wire (HTTP)" (route, request body and answer of each operation, the cookie `mia_session` of IF-101 v1, the error body `{"error", "rule"?, "detail"?}`), the mock and suite lines name the JavaScript twins; the operations, errors and golden examples are unchanged |
| `tests/helpers/mocks/if_104_graph_api.mjs` (new) | `specs/mia/contract-drafts/tests/helpers/mocks/if_104_graph_api.mjs` | `GraphApiMock`: a fake `fetch` on the routes (pass `mock.fetch` where the page expects `fetch`), answers real `Response` objects; `cookie` plays the browser's cookie jar (a login sets it; a made-up value or `credentials: 'omit'` gives 401); `requests` records every call (for TC-GA-005). Same accounts, tokens (`s1`, `s2`, ...), times, versions and diff as the Python mock, and its own copy of the graph rules (`violation`, the order of `graph_rules.py`); as the storage mock it checks the rules for `workflows` only |
| `tests/acceptance/contract/test_if_104_graph_api.test.mjs` (new) | `specs/mia/contract-drafts/tests/acceptance/contract/test_if_104_graph_api.test.mjs` | TC-IF-104-01 to -05 on the routes, against the mock (stage 1) and the real Backend (stage 2, skipped); TC-IF-104-03 also sends one request without the cookie |
| `tests/helpers/contract.mjs` | `specs/mia/contract-drafts/tests/helpers/contract.mjs` | `REAL_NOT_READY['IF-104']`: the real routes do not exist yet (N-2 serves them at its integration) |

## Checked on a scratch copy (not installed)
- `node --test tests/acceptance/contract/*.test.mjs` with the drafts laid over the installed files: 32 tests, 16 pass, 16 skipped (the `[real]` halves), 0 fail.
- Parity with the Python mock: the 17 graphs of a rule table give the same `violation` in `graph_rules.py` and the JavaScript copy, and a call sequence (save, save, diff, restore, history, read) gives the same answers in both mocks (key order ignored).

## Open for the owner
- The wire section is new interface text: the Backend (N-2) must serve these bodies. It follows the login of `accounts_api.py` (`{"ok": true}`, cookie, `{"error", "rule"}`).
- The Python and the JavaScript mock check the graph rules for `workflows` only (storage mock `VALIDATED`); the real storage checks `context_graphs` too (`tests/test_storage.py`). Left as it is here, since the JS mock is a twin of the Python one.
- The mock's copy of the graph rules is a test double, not the answer to N-5 Q-2 (a copy in the app), which stays open.

Install: `bash tools/apply_amendment_a36.sh` (look), then `bash tools/apply_amendment_a36.sh --do`.
