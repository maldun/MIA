# A-51: the real provider of IF-104 in the Python contract suite (N-2.1 T-04)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
N-2.1 T-04 built the routes of IF-104 v1 (`graph_api.py`: `GET /api/{kind}`, `GET/PUT /api/{kind}/{id}`, `/history`, `/diff`, `/restore`) on the workflow library (IF-203) behind the guard and login of `accounts_api`, wired in `web_app.py`. TC-API-016 (REQ-API-016) is "the contract suite test_if_104_graph_api.py passes against the API and accounts (stage 2)"; its real side skips because `tests/helpers/contract.py` (protected) has no real provider for IF-104. No new decision of the owner is needed: this is the pattern of A-05 and A-07 for IF-101.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `tests/helpers/contract.py` | `specs/mia/amendments/A-51/graph_api_adapter.py` (the class), inserted by `tools/apply_amendment_a51.sh` | a class `_GraphApiAdapter` before `real_subject`: the real blueprint on the real `WorkflowLibrary` and the Storage layer (file backend, fresh folder), the accounts anna/ben of the mock, the real guard and login of `accounts_api`; the session token is the value of the cookie `mia_session`, every call is one HTTP request with it; error bodies become the mock's `ApiError` (status, code, rule, detail). `real_subject("IF-104")` returns it; the comment of IF-104 in `REAL_NOT_READY` names A-51 |

The script builds the new `contract.py` from the installed one at install time (it is shared by many amendments, lesson of A-42), refuses when an anchor is not found exactly once, and reports "unchanged" when the class is there already.

Unchanged: the contract `contracts/IF-104-graph-api.md`, the suites, the mocks, `specs/mia/test-spec.md` (the rows TC-IF-104-01 to -05 already say "1 (mock) and 2 (real)").

Not in A-51: the real side of the JavaScript suite `test_if_104_graph_api.test.mjs` (`REAL_NOT_READY['IF-104']` of `tests/helpers/contract.mjs`): it needs a running Backend that node can fetch from (a server process, the integration step of N-2 or the smoke stack), not an in-process adapter.

## Checked on a scratch copy (not installed)
A copy of branch v1-n21 with the script run `--do`: `test_if_104_graph_api.py` in the image 10 tests OK, 0 skipped (the five `_real` tests run); `test_if_101_chat_api.py` OK (3 skipped, as before), `test_if_203_workflow_library.py` OK. A mutation (the author of a save always "page") turns `test_the_author_is_the_session_account_real` red.

Install (on goal/v1 after the merge of v1-n21): `bash tools/apply_amendment_a51.sh` (look), then `bash tools/apply_amendment_a51.sh --do`, commit as "plan: A-51 installed".
