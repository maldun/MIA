# IF-103 – Model server (chat completion with structured output), v0

Provider: external, Ollama (`ext:ollama`)   Owner: N-2 Backend (the consumer that depends on it)   Consumers: N-2.4   Decided by: N-0   Mock complexity: 3 (scripted replies, errors)   Suite: `tests/acceptance/contract/test_if_103_model_server.py`

Draft v0, from `FakeModel.chat(messages, schema, model, profile, options)` of `tests/test_pipeline.py` and the Ollama client of `ollama_remote.py`. Model pins MP-light and MP-full are in `specs/number-gate/eval-spec.md`. Everything in a reply is **untrusted** (model output); the Backend validates it against the schema.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `chat(messages, schema=None, model="MP-light", options=None)` | list of `{role, content}`; optional JSON schema of the reply; `options` such as `num_ctx`, `temperature`, `seed` | `{"message": text or dict, "model", "tokens_in", "tokens_out"}` | with a schema the message is a dict that matches it |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| server not running | `ModelServerError("unreachable")` | no partial result |
| no answer within the timeout | `ModelServerError("timeout")` | no partial result |
| the reply does not match the schema | `ModelServerError("bad_output")` with the raw text in `detail` | the consumer may retry |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| input size | at most half of `num_ctx` (8192) = 4096 tokens | NFR-2, REQ-BE-062 |
| one request at a time | the server queues a second request | CON-2 |

## Golden examples
1. Typical: `chat([{"role":"user","content":"2+2?"}])` returns a text message with token counts.
2. Failure: server down gives `unreachable`; a scripted reply `"not json"` with a schema gives `bad_output`.
3. Edge: an empty message list is a caller error (`ValueError`), not a model error; a real-provider run needs the model server up (stage 2).

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | – |
