# IF-101 – Chat, expression, audio and REST API, v0

Owner (provider): N-2 Backend (child N-2.1)   Consumers: N-1 Web Frontend   Decided by: N-0   Mock complexity: 3 (stream of events, queue, clock)   Suite: `tests/acceptance/contract/test_if_101_chat_api.py`

The wire between the browser and the server. Draft v0 starts from today's Socket.IO events (`web_app.py`, `chat_service.py`, `audio_router.py`) and adds what the approved HLS asks for; additions are marked **[new]**. The suite talks to an adapter with the methods below; for the real provider the adapter drives a Socket.IO client and a clock-injected server.

## Operations and events
| Name | Input | Output | Notes |
|---|---|---|---|
| `login(user, password)` **[new]** | account, password | session token | HTTPS or localhost only (CON-4); 5 failed logins per minute per account, then `429 throttled` even with the right password (REQ-BE-009) |
| `connect(session)` | session | event `chat_status` first | `{busy, activity, model, profile, queue, mood}` as today |
| `send(session, text, client_id)` (`chat_send`) | text 1..4000 characters | ack `{"id", "position"}` **[new: position]** | `position` 1 = answered next; 401 without session; 422 `empty_text`; 503 `queue_full` (5 waiting messages in all, or 2 waiting messages of this account) |
| `stop(session)` (`chat_stop`) | | `{"stopped": bool}` | ends the running or next answer; no `chat_delta` after the ack |
| `history(session, limit)` (`/api/chat/history`) | | list of messages, oldest first | each with `id, role, sender [new], text, created` |
| `events(session)` | | events received since the last call | `chat_message`, `chat_start`, `chat_delta`, `chat_done`, `chat_status`, `chat_error`, `expression`, `audio_chunk [new]` |
| `settle()` | | | test adapter only: let the server finish all queued work (the mock runs it; the real adapter waits) |
| `advance_time(seconds)` | | | test adapter only: move the server clock (throttle window) |

Events (server to every connected page):
| Event | Payload |
|---|---|
| `chat_message` | a complete message `{id, role, sender, text, created}`; the user's own message is broadcast with `sender` = the account **[new]** |
| `chat_start` | `{id, role: "assistant"}` |
| `chat_delta` | `{id, text}` cumulative: each text starts with the previous one |
| `audio_chunk` **[new]** | `{id, index, sentence}`; one per sentence, `index` from 0, in order (the audio bytes follow on the audio route; see N-2.5) |
| `expression` | `{name}` a preset name of the mood map |
| `chat_done` | `{id, text, emotion, status}`; status `done` or `stopped`; text equals the last delta |
| `chat_error` | `{id?, message}` plain words |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| wrong account or password | 401 `bad_credentials` | no session |
| request without session | 401 `unauthenticated` | nothing changed |
| too many failed logins | 429 `throttled` | right password works again after 60 s |
| empty text | 422 `empty_text` | nothing queued |
| queue full | 503 `queue_full` | nothing queued; queued messages unaffected |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| first text of an answer after the ack | at most 10 s on MP-light | NFR-7, REQ-BE-069 |
| failed logins before throttling | 5 per minute per account | FR-21, REQ-BE-009 |
| message text | 1..4000 characters | proposal, set in Plan |

## Golden examples
1. Typical: anna logs in, sends "hi"; ben's connection receives `chat_message` (sender anna), `chat_start`, deltas that grow, one `audio_chunk` per sentence, `chat_done`.
2. Failure: sixth wrong login within a minute is `429`, also with the right password; after 61 s it works.
3. Edge: three messages sent without settling get positions 1, 2, 3; a fourth with queue length 3 is `503 queue_full`; `stop` right after `send` gives `chat_done` with status `stopped` and no delta.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft from today's events plus the HLS additions | – |
