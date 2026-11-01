# A-52: an HTTP stand-in of the model server (IF-103) for the container alone (N-2.1, D-147)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
REQ-API-013, AC-29: "the container starts alone against the mocks and serves the chat page" (TC-API-013, stage 3). The start of MIA (`__main__.py`: `install_lama.py` waits for the model server and pulls missing models, then `comm.calibrate()` sends one chat) needs a model server that speaks HTTP; the mock of IF-103 (`tests/helpers/mocks/if_103_model_server.py`) is an in-process object. Finding F-7 of the implementation, V-0 of the verification; D-147 (owner, 2026-10-31): an Ollama-shaped HTTP mock of IF-103 in the protected helpers and a stage-3 test that starts the mia image against it; the start behaviour of MIA does not change.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `tests/helpers/mocks/if_103_model_server_http.py` (new) | `specs/mia/contract-drafts/tests/helpers/mocks/if_103_model_server_http.py` | an Ollama-shaped HTTP server, standard library only, deterministic: `GET /`, `/api/version`, `/api/tags`, `/api/ps`; `POST /api/show`, `/api/pull`, `/api/chat` and `/api/generate` (NDJSON stream by default, one object with `"stream": false`; with `format` a JSON object with the schema's required keys, fixed values per type); `GET /_calls` lists the requests for the test. `make_server()` for in-process use, `python if_103_model_server_http.py --port 11434` as a process |

Unchanged: the contract `contracts/IF-103-model-server.md` (the stand-in speaks the wire shape of the external provider, Ollama, which the contract's operation `chat` wraps), the in-process mock, the suite `test_if_103_model_server.py`, `specs/mia/test-spec.md`.

Not protected, in the same work (branch v1-n21b): `tests/test_container_alone.py` (TC-API-013, stage 3) starts a pod published only on 127.0.0.1 with two containers of `localhost/mia:latest` as it is (never pulled): the stand-in (the installed file mounted read-only) and MIA with `deploy/setup_cfg.compose.json` (copied, `ollama_wait` 20 s) and `MIA_OLLAMA_HOST` on the stand-in; it waits until `/` answers, checks the chat page and that the start went through the stand-in, and removes the pod. It skips, never passes, without podman, the image or the installed stand-in. The TC-API-013 row of the node's `test-spec.md` names the stand-in.

## Checked on a scratch copy (not installed)
See the implementation log of N-2.1 (entry "A-52 and TC-API-013").

Install (on goal/v1 after the merge of v1-n21b): `bash tools/apply_amendment_a52.sh` (look), then `bash tools/apply_amendment_a52.sh --do`, commit as "plan: A-52 installed".
