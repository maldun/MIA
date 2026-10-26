# IF-201 – Chat turn service, v1

Owner (provider): N-2.2 Chat agent   Consumers: N-2.1 API and accounts   Decided by: N-2   Mock complexity: 3 (queue, event stream)   Suite: `tests/acceptance/contract/test_if_201_chat_turn.py`

The call from the gateway to the chat agent. Authentication, sessions and the wire format (IF-101) stay in N-2.1; the chat agent receives an account name it can trust. Python calls. **v1 (amendment A-06)** adds the operations on answers and votes that IF-101 v1 needs from the chat agent; the records of tasks, memos and memory, the trust of sources and the persona are not part of it: the API reaches them through the Database (IF-102).

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `send(account, text, client_id=None)` | account name, text of 1..4000 characters | `{"id", "position"}` | position 1 = answered next |
| `stop()` | | `{"stopped": bool}` | ends the running or next answer |
| `history(limit=50)` | | messages oldest first, each `{id, role, sender, text, created}` | |
| `status()` | | `{"busy", "queue"}` | |
| `regenerate(account, message_id)` **[v1]** | id of the LAST answer | `{"position", "asked"}` | queued like a message; the new answer is a new message, the old one stays |
| `speak_again(message_id)` **[v1]** | id of any answer | `{"sentences": n}` | one `audio_chunk` per sentence to the subscribers |
| `account(message_id)` **[v1]** | id of an answer | list of `{"seq", "plain"}` | the step-by-step account in order (from the run log, IF-401) |
| `vote(account, subject, category, value)` **[v1]** | subject = message id (answers) or a name; category in `answer_quality`, `reactions`, `character_behaviour`, `service`; value 1 or -1 | `{"stored": true, "score"}` | kept with account and time (REQ-BE-028); the event `score` follows |
| `score()` **[v1]** | | `{"overall", "categories", "votes", "series"}` | as in IF-101 v4: `series` = sums per ISO week (`YYYY-Www`), oldest first |
| `subscribe(callback)` | | a function that unsubscribes | `callback({"event", "payload"})` for `chat_message`, `chat_start`, `chat_delta`, `audio_chunk`, `expression`, `chat_done`, `chat_status`, `variant`, `score`; same payloads as IF-101 |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| empty or blank text, or more than 4000 characters | `ServiceError("empty_text")` | nothing queued |
| queue full (5 waiting messages in all) or 2 waiting messages of this account | `ServiceError("queue_full")` | nothing queued |
| unknown message id, or an id that is no answer **[v1]** | `ServiceError("not_found")` | nothing changed |
| `regenerate` of an answer that is not the last **[v1]** | `ServiceError("not_the_last_answer")` | nothing queued |
| a vote with a wrong category or value **[v1]** | `ServiceError("invalid_vote", rule="category" or "value")` | the vote is not stored, the score is unchanged |

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
| v1 | 2026-10-27 | regenerate, speak_again, account, vote, score; events variant and score; errors not_found, not_the_last_answer, invalid_vote; the ack stays `{id, position}` | A-06 |
