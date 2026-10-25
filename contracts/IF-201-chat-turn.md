# IF-201 – Chat turn service, v0

Owner (provider): N-2.2 Chat agent   Consumers: N-2.1 API and accounts   Decided by: N-2   Mock complexity: 3 (queue, event stream)   Suite: `tests/acceptance/contract/test_if_201_chat_turn.py`

The call from the gateway to the chat agent. Authentication, sessions and the wire format (IF-101) stay in N-2.1; the chat agent receives an account name it can trust. Python calls; draft v0.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `send(account, text, client_id=None)` | account name, text of 1..4000 characters | `{"id", "position"}` | position 1 = answered next |
| `stop()` | | `{"stopped": bool}` | ends the running or next answer |
| `history(limit=50)` | | messages oldest first, each `{id, role, sender, text, created}` | |
| `status()` | | `{"busy", "queue"}` | |
| `subscribe(callback)` | | a function that unsubscribes | `callback({"event", "payload"})` for `chat_message`, `chat_start`, `chat_delta`, `audio_chunk`, `expression`, `chat_done`, `chat_status`; same payloads as IF-101 |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| empty or blank text, or more than 4000 characters | `ServiceError("empty_text")` | nothing queued |
| queue full (5 waiting messages in all) or 2 waiting messages of this account | `ServiceError("queue_full")` | nothing queued |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| first `chat_delta` after the ack on MP-light | at most 10 s | NFR-7 |

## Golden examples
1. Typical: `send("anna","hi")` gives position 1; a subscriber sees `chat_message` (sender anna), `chat_start`, growing `chat_delta`, one `audio_chunk` per sentence, `chat_done`.
2. Failure: blank text is `empty_text`; a full queue is `queue_full` and the queued messages are unaffected.
3. Edge: `stop()` right after `send` ends the answer with status `stopped` and no delta; `stop()` with nothing running is `{"stopped": false}`.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | 8 |
