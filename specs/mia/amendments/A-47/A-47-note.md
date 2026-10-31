# A-47: the smoke test of a fresh installation, SMOKE-MIA-001 / TC-OPR-001 (N-4.2 T-07, D-136)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
TC-OPR-001 (REQ-OPR-001) is SMOKE-MIA-001 ("fresh checkout, one configuration file, one command: compose stack up with all containers; the first account can be created; a chat message is answered"), and `tests/smoke/` is protected. D-136 (5): the test uses an Ollama that already runs (`OLLAMA_URL`) and never pulls the models.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `tests/smoke/smoke_fresh_install.py` (new) | `specs/mia/contract-drafts/tests/smoke/smoke_fresh_install.py` | stops with exit 2 (nothing started) when podman, podman-compose or git is missing, no Ollama answers at `OLLAMA_URL`, the Ollama lacks `version` or `version_light` of `deploy/setup_cfg.compose.json`, or an image of the stack is not on the machine; else: `git clone` of the committed HEAD into a temporary folder; the one configuration file `deploy/.env` (`OLLAMA_URL`, and for the test its own `MIA_PROJECT=mia-fresh`, `MIA_IMAGE=localhost/mia:fresh`, free loopback ports); the one command `deploy/up.sh db` without a terminal; then checks: the command succeeds, the page answers, the offer of the first account is printed once (REQ-OPR-002), the five services run (mia, graph, https, db, searxng), the database is ready, `accounts_cli.py create` makes an account (password on stdin), and a chat message sent over the socket inside the mia container gets text and `chat_done`. Removes its containers, volumes, image tag and checkout. Exit 0 green, 1 red, 2 cannot run |

Nothing else changes: the SMOKE-MIA-001 row of `specs/mia/test-spec.md` and the TC-OPR-001 row already say this. Reading for the owner to confirm: "one command" = `deploy/up.sh db` (the start with the database, REQ-OPR-001 "with its database"); the plain `deploy/up.sh` starts without the `db` service (T07-Q1 in the node's log).

## Checked on a scratch copy (not installed)
Run on a scratch clone of the branch with the draft laid into `tests/smoke/` (2026-10-31), with the host's Ollama (`gemma4:26b`, `gemma4:12b-it-qat` present) and the images on the machine:
- red on the old `deploy/up.sh` (bfbd327): 7 of 7 parts failed; `podman-compose` stops with "run deploy/up.sh, it makes .env", because `up.sh` wrote the SearXNG secret only when `.env` did not exist, and the README tells the owner to write `.env` first (`OLLAMA_URL`).
- green on the T-07 state: one command ok, page ok, offer once, 5 services, database ready, first account created, chat answered ("Hello there, master."); "SMOKE-MIA-001: green" (the image build used the layer cache). Afterwards no container, volume or image tag of `mia-fresh` was left; no ollama service was started and nothing was pulled.

Install: `bash tools/apply_amendment_a47.sh` (look), then `bash tools/apply_amendment_a47.sh --do`; it needs `podman-compose`, `git`, the models of `deploy/setup_cfg.compose.json` in the running Ollama and the images of the stack on the machine.
