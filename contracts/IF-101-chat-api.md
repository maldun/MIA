# IF-101 – Chat, expression, audio and REST API, v6

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
| `vote(session, subject, category, value)` **[v1]** | subject = message id (answers) or a name; category in `answer_quality`, `reactions`, `character_behaviour`, `service`; value 1 or -1 | `{"stored": true, "score"}` | kept with user and time (REQ-BE-028); `422 invalid_vote` with rule `category` or `value`, or **[v5]** `subject` (a `character_behaviour` vote on a name that is not on the list of behaviours); 404 for an unknown answer |
| `score(session)` **[v1]** | | `{"overall", "categories", "votes", "series"}` **[v4: series]** | sums per category and overall; `series` = the same sums per ISO week of the vote's time, `[{"week": "YYYY-Www", "overall", "categories"}]`, oldest first, only weeks with a vote, so the sums of the weeks equal the totals (REQ-CLV-010); the event `score` pushes the same after each vote |
| `counters(session)` **[v5]** | | `{name: {"net", "votes", "chance", "reset_at"}}` for every behaviour of the list | the adaptation counters (REQ-BE-031, REQ-CHA-018): `net` = sum of the `character_behaviour` votes on that name since the last reset, `chance` = how likely the behaviour is shown at one opportunity (1.0, and at most 0.01 from a `net` of -5 or less; REQ-BE-030), `reset_at` = time of the last reset or `null`; every user sees them (CON-6) |
| `reset_counter(session, name)` **[v5]** | name of a behaviour | the counter of that name after the reset | back to the default rate, the votes stay stored and only later ones count; event `counters_changed {name, author}`; 404 `not_found` for a name that is not on the list |
| `items(session, kind)` **[v1]** | kind in `tasks`, `memos`, `memory` | list of `{id, text, author, created, source?, due?}` **[v6: due]** | every user sees all records (CON-6) |
| `save_item(session, kind, id, text, source, due)` **[v1]** | id None = new; `due` (optional, tasks only) **[v6]** | the stored record | `due` is a UTC time `YYYY-MM-DDTHH:MM:SSZ`: the chat agent says the task once at that time (REQ-CHA-019); a save without `due` clears it; any other format, or `due` on memos or memory, is 422 `invalid_item`, rule `due`; a change of the text with the same `due` does not make the chat say the task again, a new `due` does; memory needs a `source` (422 `invalid_item`, rule `source`); empty text 422; 404 unknown id; text comes back byte for byte (FR-28); event `item_changed` to the others |
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
| `score` **[v1]** | `{overall, categories, votes, series}` **[v4: series]** |
| `item_changed` **[v1]** | `{kind, id, author, deleted}` |
| `trust_changed` **[v1]** | `{source, old, new, author}` |
| `persona_changed` **[v1]** | `{author}` |
| `counters_changed` **[v5]** | `{name, author}` |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| wrong account or password | 401 `bad_credentials` | no session |
| request without session | 401 `unauthenticated` | nothing changed |
| request with an `Origin` that is not one of the server's own addresses **[v3]** | 403 `bad_origin` | nothing changed, also with a valid session |
| `login` or `change_password` over plain HTTP from an address other than the machine of the server **[v3]** | 403 `insecure_channel` | the password was not checked, no session, no cookie |
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
| v3 | 2026-10-27 | the errors `403 bad_origin` and `403 insecure_channel` (REQ-API-007, REQ-API-008, found in N-2.1 T-02); the title says v3 | A-05 |
| v4 | 2026-10-27 | `score` and the event `score` carry `series`, the sums per ISO week (owner: score over time "by time", per week) | A-06 |
| v5 | 2026-10-27 | `counters`, `reset_counter` and the event `counters_changed` (REQ-BE-030, REQ-BE-031); `invalid_vote` rule `subject`; `regenerate` of a known message that is not the last answer, a user message included, is `422 not_the_last_answer` (404 stays for an unknown id); the list of behaviours is the names of `character_behaviour`: `greet`, `idle`, `no`, `talk`, `yes` for the mock | A-08 |
| v6 | 2026-10-27 | `save_item` takes an optional `due` (tasks only) and `items` shows it; `invalid_item` gets the rule `due` (owner decision: recitation at the due time, REQ-CHA-019) | A-09 |
