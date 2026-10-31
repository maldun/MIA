# A-54: IF-101 v12, a message over the rate limit is `429 rate_limited` (N-2.1, D-149)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
Verify finding V-5 of N-2.1: REQ-API-007's acceptance criterion said "the rate limit value is set in Plan"; the code used `chat_rate_per_minute` (default 10 per 60 s) and refused without a code; IF-101 had no rate-limit error. D-149 (owner, 2026-10-31): the limit is fixed at 10 messages per 60 s (a setting) in the requirement, and IF-101 gets the refusal `429 rate_limited` by amendment, test-first.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `contracts/IF-101-chat-api.md` | `specs/mia/amendments/A-54/IF-101-chat-api.md` | v12: the `send` row names 429 `rate_limited` (10 messages per 60 s per account, all its connections together); a row of the error table (nothing queued or stored, other accounts not affected, taken again when the oldest of the last 10 is older than 60 s); title and version line |
| `tests/helpers/mocks/if_101_chat_api.py` | `specs/mia/contract-drafts/tests/helpers/mocks/if_101_chat_api.py` | `RATE_LIMIT, RATE_SECONDS = 10, 60`; `send` counts the messages of the account on the mock's clock and raises `ApiError(429, "rate_limited")` after the empty-text check, before the queue check (the order of `chat_service.py`) |
| `tests/acceptance/contract/test_if_101_chat_api.py` | `specs/mia/contract-drafts/tests/acceptance/contract/test_if_101_chat_api.py` | TC-IF-101-30 (mock and real): ten messages of anna pass, the 11th is 429 `rate_limited` and not stored, ben still sends |
| `specs/mia/test-spec.md` | made by `tools/apply_amendment_a54.sh` from the installed file | the row of TC-IF-101-30 after the one of TC-IF-101-19 |

Unchanged: `tests/helpers/contract.py` (its adapter maps the code of a refused `chat_send` to its status already, 429 for `rate_limited`). The real side: `chat_service.py` answers the refusal with `"code": "rate_limited"` (branch v1-n21b, `tests/test_chat_backend.py`, red first).

## Checked on a scratch copy (not installed)
A copy of branch v1-n21b with `tools/apply_amendment_a54.sh --do`: the IF-101 suite in the image 62 tests OK, 3 skipped (as before; the two new ones run). Red: the new suite with the old mock: 1 failure (the mock side of TC-IF-101-30). With the new mock `test_chat_page`, `test_chat_mock_server`, `test_api_events`, `test_accounts_wiring` pass.
Note: the real side of TC-IF-101-30 cannot fail on a missing code (the adapter defaults to 429 `rate_limited` when the refusal has no code); the code itself is checked by `tests/test_chat_backend.py` and `tests/test_accounts_wiring.py`.

Install (on goal/v1 after the merge of v1-n21b): `bash tools/apply_amendment_a54.sh` (look), then `bash tools/apply_amendment_a54.sh --do`, commit as "plan: A-54 installed".
