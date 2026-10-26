# IF-101 – Chat, expression, audio and REST API, v1

Owner (provider): N-2 Backend (child N-2.1)   Consumers: N-1 Web Frontend   Decided by: N-0   Mock complexity: 3 (stream of events, queue, clock, small stores)   Suite: `tests/acceptance/contract/test_if_101_chat_api.py`

The wire between the browser and the server. v0 started from today's Socket.IO events (`web_app.py`, `chat_service.py`, `audio_router.py`); **v1 (amendment A-03, owner 2026-10-26)** adds what the views of N-1.1 need: the stored message in the acknowledgement, the session as a cookie, the own password, regenerate and speak again, votes and scores, the records of tasks, memos and memory, the trust of sources, the persona, the account of an answer and the character variant. Additions of v1 are marked **[v1]**, those of v0 **[new]** against today's code.

## Session
The server sets the session at `login` as a cookie `mia_session` (HttpOnly, SameSite=Strict, Secure on HTTPS) **[v1]**. The page keeps no token: REST calls and the socket carry the cookie. A request or a socket without a valid session is `401 unauthenticated` (a refused socket connection has the error message `unauthenticated`). The REST address of an operation is `/api/<operation>`; the socket events carry the same operations where noted.

## Operations and events
| Name | Input | Output | Notes |
|---|---|---|---|
| `login(user, password)` | account, password | session (cookie) | HTTPS or localhost only (CON-4); 5 failed logins per minute per account, then `429 throttled` even with the right password (REQ-BE-009) |
| `whoami(session)` **[v1]** | | `{"user"}` | the account of a kept session; the page asks after a reload |
| `logout(session)` **[v2]** | | `{"loggedOut": true}` | ends the session: the same cookie is `401 unauthenticated` afterwards and its sockets are closed; the cookie is cleared (`Max-Age=0`); 401 without a valid session (REQ-BE-077) |
| `change_password(session, old, new)` **[v1]** | the own password | `{"changed": true}` | `401 bad_credentials` if `old` is wrong; `422 weak_password` below 8 characters; the old password stops working (REQ-BE-011) |
| `connect(session)` | session | event `chat_status` first | `{busy, activity, model, profile, queue, mood}` as today |
| `send(session, text, client_id)` (`chat_send`) | text 1..4000 characters | ack `{"id", "position", "message"}` **[v1: message]** | `position` 1 = answered next; `message` is the stored message `{id, role, sender, text, created, client_id}`; 401 without session; 422 `empty_text`; 503 `queue_full` (5 waiting messages in all, 2 per user) |
| `stop(session)` (`chat_stop`) | | `{"stopped": bool}` | ends the running or next answer; no `chat_delta` after the ack |
| `history(session, limit)` (`/api/chat/history`) | | list of messages, oldest first | each with `id, role, sender, text, created`, and `client_id` if the sender gave one |
| `regenerate(session, message_id)` **[v1]** | id of the LAST answer | `{"position", "asked"}` | queued like a message; the new answer is a new message, the old one stays; 404 unknown id; 422 `not_the_last_answer`; 503 `queue_full` |
| `speak_again(session, message_id)` **[v1]** | id of any answer | `{"sentences": n}` | one `audio_chunk` per sentence to every connected page; 404 unknown id |
| `account(session, message_id)` **[v1]** | id of an answer | list of `{"seq", "plain"}` | the step-by-step account of the answer in order (from the run log, IF-401); 404 for a message that is not an answer |
| `vote(session, subject, category, value)` **[v1]** | subject = message id (answers) or a name; category in `answer_quality`, `reactions`, `character_behaviour`, `service`; value 1 or -1 | `{"stored": true, "score"}` | kept with user and time (REQ-BE-028); `422 invalid_vote` with rule `category` or `value`; 404 for an unknown answer |
| `score(session)` **[v1]** | | `{"overall", "categories", "votes"}` | sums per category and overall; the event `score` pushes the same after each vote |
| `items(session, kind)` **[v1]** | kind in `tasks`, `memos`, `memory` | list of `{id, text, author, created, source?}` | every user sees all records (CON-6) |
| `save_item(session, kind, id, text, source)` **[v1]** | id None = new | the stored record | memory needs a `source` (422 `invalid_item`, rule `source`); empty text 422; 404 unknown id; text comes back byte for byte (FR-28); event `item_changed` to the others |
| `delete_item(session, kind, id)` **[v1]** | | `{"deleted": true}` | any user may delete any record; 404 unknown id; event `item_changed` with `deleted: true` |
| `trust(session)` / `set_trust(session, source, value)` **[v1]** | source id, value 0..1 | `{"source", "old", "new"}` | event `trust_changed {source, old, new, author}`; 422 `invalid_trust`; 404 unknown source |
| `persona(session)` / `save_persona(session, doc)` **[v1]** | doc with `text` | the stored persona | event `persona_changed {author}`; 422 `invalid_persona` |
| `events(session)` | | events received since the last call | all events below |
| `settle()` | | | test adapter only: let the server finish all queued work (the mock runs it; the real adapter waits) |
| `advance_time(seconds)` | | | test adapter only: move the server clock (throttle window) |
| `run_with_variant(name)` **[v1]** | name or None | | test adapter only: the next answer comes from a workflow with that character variant |

Events (server to every connected page):
| Event | Payload |
|---|---|
| `chat_message` | a complete message `{id, role, sender, text, created, client_id?}`; the user's own message is broadcast with `sender` = the account |
| `chat_start` | `{id, role: "assistant"}` |
| `variant` **[v1]** | `{name}` after `chat_start`: the character variant of the workflow that answers, or `null` (the chat's variant stays) |
| `chat_delta` | `{id, text}` cumulative: each text starts with the previous one |
| `audio_chunk` | `{id, index, sentence}`; one per sentence, `index` from 0, in order (the audio bytes follow on the audio route; see N-2.5) |
| `expression` | `{name}` a preset name of the mood map |
| `chat_done` | `{id, text, emotion, status}`; status `done` or `stopped`; text equals the last delta |
| `chat_error` | `{id?, message}` plain words |
| `score` **[v1]** | `{overall, categories, votes}` |
| `item_changed` **[v1]** | `{kind, id, author, deleted}` |
| `trust_changed` **[v1]** | `{source, old, new, author}` |
| `persona_changed` **[v1]** | `{author}` |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| wrong account or password | 401 `bad_credentials` | no session |
| request without session | 401 `unauthenticated` | nothing changed |
| too many failed logins | 429 `throttled` | right password works again after 60 s |
| empty text | 422 `empty_text` | nothing queued or stored |
| queue full | 503 `queue_full` | nothing queued; queued messages unaffected |
| unknown message, record or source | 404 `not_found` | nothing changed |
| a document or value the rules refuse | 422 with the code of the operation (`invalid_vote`, `invalid_item`, `invalid_trust`, `invalid_persona`, `weak_password`) | nothing stored |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| first text of an answer after the ack | at most 10 s on MP-light | NFR-7, REQ-BE-069 |
| failed logins before throttling | 5 per minute per account | FR-21, REQ-BE-009 |
| message text | 1..4000 characters | proposal, set in Plan |
| a change reaches the other pages | at most 5 s (`item_changed`, `trust_changed`, `persona_changed`, `score`) | FR-5, OPEN-5 |

## Golden examples
1. Typical: anna logs in, sends "hi" with client id `c-1`; the ack carries the stored message with `client_id: "c-1"`; ben's connection receives `chat_message` (sender anna), `chat_start`, deltas that grow, one `audio_chunk` per sentence, `chat_done`.
2. Failure: sixth wrong login within a minute is `429`, also with the right password; after 61 s it works. A vote with category `mood` is `422 invalid_vote` and stores nothing.
3. Edge: three messages sent without settling get positions 1, 2, 3; a fourth with queue length 3 is `503 queue_full`; `stop` right after `send` gives `chat_done` with status `stopped` and no delta. `regenerate` of an answer that is not the last is `422`.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft from today's events plus the HLS additions | – |
| v1 | 2026-10-26 | stored message and client id in the ack and the events; session as cookie; whoami, change_password, regenerate, speak_again, account, vote, score, items, save_item, delete_item, trust, set_trust, persona, save_persona; events variant, score, item_changed, trust_changed, persona_changed | A-03 |
| v2 | 2026-10-26 | `logout` | A-04 |
