# A-62: IF-101 describes the whole wire of the chat page (N-1.1 Verify F4, D-163)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The verification of N-1.1 (F4) found that the page and the Backend share more than IF-101 v13 names: the socket events `chat_pipeline`, `audio_claim`, `audio_owner`, `audio_reload`, `audio_ended`, `character_ready`; the routes `/api/chat/commands` and `/character-backgrounds.json`; the history on the wire is `{messages, older}` with `before`, not a bare list with `limit`. The allow-list of TC-CLV-021 was the test's own list, wider than the interface, so REQ-CLV-021 ("only through IF-101 as specified") was not shown. The owner decided (D-163) to amend IF-101 so that it describes the whole wire, and to build the allow-list from the contract. The same verification found a duplicate id: A-54's rate-limit case and the files case are both TC-IF-101-30.

## What changes
| File | Change (built from the INSTALLED file at install time) |
|---|---|
| `contracts/IF-101-chat-api.md` (protected) | the title goes one version up (the next one at install time: v14, or v15 when A-61 is installed first); a sentence on REST addresses; the `history` row says what the wire carries (`{messages, older}`, `before`, page size 50, at most 200); two operation rows, `commands` (`/api/chat/commands`) and `backgrounds` (`/character-backgrounds.json`); a table *REST addresses* with method, operation and input of every call the page makes (`save_item` is `POST /api/items`, `delete_item` `DELETE /api/items`, ...); four rows of the events table (`chat_status`, `chat_pipeline`, `audio_owner`, `audio_reload`); a table *Events (page to server)* (`chat_send`, `chat_stop`, `audio_claim`, `audio_ended`, `character_ready`); one row in the version history |
| `tests/acceptance/contract/test_if_101_chat_api.py` (protected) | A-54's case "the eleventh message of an account within a minute is rate limited" is renumbered TC-IF-101-30 -> **TC-IF-101-33** (TC-IF-101-30 stays the files case of v8/A-25; 31 is the failing task; 32 is taken by A-61 on branch v1-n33b) |
| `specs/mia/test-spec.md` | the row of that case: TC-IF-101-30 -> TC-IF-101-33 |
| `tests/acceptance/contract/test_if_101_chat_api.py` (D-167, N-2.1 R-1) | the second TC-IF-101-09 (v1: the ack with the stored message and the client id) becomes **TC-IF-101-20**, the id that was never given |
| `specs/mia/test-spec.md` (D-167) | the same row renumbered and moved after TC-IF-101-19; the missing rows TC-IF-101-21 to -29 are made at install time from the suite (first paragraph of each docstring and its `mark.req` requirements) and stand after it. Rows -30 (files, v8) and -31 (a failing task, v10) are added after -29 the same way (D-167) |
| `tests/helpers/contract.py` (protected, D-167, N-2.1 R-2) | the real adapter of IF-101: a refusal of `send` without a code is 500 `no_code` (and `rate_limited` is mapped to 429 by name), so the real side of TC-IF-101-33 fails when the Backend gives no code; built from the installed file (A-59, A-60 changed it). The IF-201 adapter (`_ChatTurnAdapter.send`) gets the same: `ServiceError("no_code")` (D-167); the install also runs the IF-201 suite |
| `tests/js/multiuser.test.mjs`, `tests/test_chat_views_browser.py` (not protected, from branch v1-n11b) | the set `PENDING_A62` is emptied: TC-CLV-021 (static scan of the page and the browser click-through) then allows exactly what the contract names |

Unchanged: the mock of IF-101 and the adapters (`tests/helpers/contract.py`): the new rows describe events and routes of the voice (N-1.3, N-2.5), the character (N-1.2) and the palette that the Python-level mock does not model; their behaviour is tested by the component tests `tests/test_audio_router.py` and `tests/test_chat_backend.py`. No contract case is added.

## How TC-CLV-021 reads the contract
`contractWire` (`tests/js/multiuser.test.mjs`) and `contract_wire` (`tests/test_chat_views_browser.py`) apply the same rules to the contract text: an operation `name(...)` is at `/api/<name>`; a name in brackets after it, (`chat_send`), and a name after the word *event* are socket events; an address in backquotes in the first column is a path (`/api/files/<name>` allows `/api/files/...`); the first column of every events table is an event. The Socket.IO client's own `connect`, `disconnect`, `connect_error` and, in the browser, the page's files, the character page and the socket transport are not operations and are allowed by name. Until A-62 is installed, the eight names of `PENDING_A62` are allowed in addition; both tests fail if the page uses anything else.

## Order with A-54, A-57 and A-61
- Built after A-54 and A-57 (both installed on goal/v1 at a262376).
- A-61 (N-3.3, branch v1-n33b) also raises IF-101 one version. Both scripts build the title as "installed version + 1" and add their version row after the last one, so either order works: A-61 then A-62 gives v14 = A-61, v15 = A-62; A-62 then A-61 gives v14 = A-62, v15 = A-61 (checked on scratch copies, both orders). TC-IF-101-32 (A-61) and TC-IF-101-33 (A-62) do not collide; A-61 inserts its test-spec row after the last TC-IF-101 row, which works with the renumbered row.
- A-54 copies whole files from `specs/mia/contract-drafts/`; if it is ever installed again, run this script with `--do` once more (its draft copy of the suite still says TC-IF-101-30 for the rate limit).

## Checked (scratch copies of v1-n11b, 2026-10-31)
- `bash tools/apply_amendment_a62.sh --do`: IF-101 suite in the image 62 tests OK, 2 skipped; JS tests 160 pass with `PENDING_A62` empty; `tests/test_chat_views_browser.py` 10 OK with `PENDING_A62` empty. A second run reports every file unchanged.
- A-61 first, then A-62 (and the reverse): titles v15, version rows in install order, TC-IF-101-32 and -33 both present; the IF-101 suite has one failure, the real side of A-61's TC-IF-101-32, which needs the code of branch v1-n33b (as A-61's note says).

- Re-checked after merging goal/v1 with A-59..A-61 installed (IF-101 v14): A-62 gives **v15**, the IF-101 suite 64 OK (2 skipped), JS 160 pass.

- Extended after D-167 and re-checked on a copy of v1-n11b merged with goal/v1 plus v1-n41b's files: A-62 then A-63 -> IF-101 v15, the IF-101 suite 64 OK (2 skipped), no duplicate id in the suite, rows TC-IF-101-20..29 in place, JS 160 pass; a second run of A-62 changes nothing; full `tests/test_*.py` see the N-1.1 log.

Install (on goal/v1 after the merge of v1-n11b): `bash tools/apply_amendment_a62.sh` (look), then `--do`, commit as "plan: A-62 installed".
