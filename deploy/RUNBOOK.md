# Runbook: MIA (compose stack)

REQ-OPR-006. For the owner who runs MIA on the workstation (Fedora, podman, one GPU). Reviewed at every release and after every incident; the walkthrough of TC-OPR-006 is run once on a clean machine and every deviation is fixed here. Details of each command: `deploy/README.md`.

## Start and stop
- Where: `deploy/compose.yaml` with the services `mia` (backend and page), `graph` (the graph page), `https` (Caddy, the only port that may face the network), `searxng` (web search), `db` (PostgreSQL, with `db`), and `ollama` only when `deploy/.env` names no `OLLAMA_URL`.
- Configuration: one file of this machine, `deploy/.env` (not in git; `OLLAMA_URL`, ports, `MIA_BIND`, `MIA_PROJECT`); the tracked `deploy/setup_cfg.compose.json` and its local overlay `deploy/setup_cfg.local.json` (the login). Data: the volume `mia_mia-data` (histories, accounts in `data/db`, presets, logs) and, with `db`, the volume `mia_pgdata` of PostgreSQL (the prefix is `MIA_PROJECT`).
- Start: `deploy/up.sh db` (AMD: `deploy/up.sh rocm db`). The first start adds the SearXNG secret and the database password to `deploy/.env` and offers the owner account once (`deploy/up.sh owner NAME` later).
- Stop: `deploy/up.sh db down` (volumes stay). Restart MIA alone: `deploy/up.sh db restart mia`.
- Health check: `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8585/` gives 200; `podman ps --filter label=io.podman.compose.project=mia` lists every service as up.
- Fresh-install check (TC-OPR-001, SMOKE-MIA-001): `python tests/smoke/smoke_fresh_install.py` after the commit to be checked. It uses the Ollama that runs already (`OLLAMA_URL`, default `http://host.containers.internal:11434`) and never pulls the models or images: when a model of `setup_cfg.compose.json` or an image of the stack is missing it stops with exit 2. Pull what is missing yourself first, never inside a test.

## Files a fresh checkout lacks
Three files are git-ignored and do not come with a checkout; MIA runs without them (the chat answers; no character, no voice), so a fresh install works before they are there (D-139):
- `ui/godot/assets/mia.vrm`, the character model: made by `ui/tools/export_character.sh` from the VRoid source, or copied from an existing install.
- `voice/models/kokoro/kokoro-v1.0.onnx` and `voices-v1.0.bin`, the Kokoro voice: from https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 (README.md, "Kokoro TTS").

## Update of the model pins
The pins are `MP-light` and `MP-full` in `specs/mia/eval-spec.md` (name, digest, quantization, options); `version` and `version_light` of `deploy/setup_cfg.compose.json` name the same models. A new model or a new digest of the same name is a plan amendment and needs a new eval baseline.
1. Read the digests the server holds: `curl -s http://127.0.0.1:11434/api/tags` (or `podman exec ollama ollama list`) and compare them with `eval-spec.md`.
2. To change a pin: write the amendment (new pin line), then pull the model by hand (`podman exec ollama ollama pull NAME`), record its digest, and run the baselines of the affected suites (`python tools/eval.py run <suite> --repeats 3`, see `ui/README.md`).
3. Change `version` / `version_light` only together with the amendment; restart MIA (`deploy/up.sh db restart mia`).
4. Images: the floating images are pinned by digest in the compose files (`ollama`, `searxng`, `caddy`, D-127). To update one: pull the tag by hand, read the digest with `podman image inspect --format '{{.Digest}}' IMAGE`, replace the digest in the compose file, run `tests/test_runbook.py` and the stack smoke tests.

## Backup and restore
- What: everything in the data volume and, with the `db` service, the database, in one archive (REQ-OPR-005).
- Backup: `deploy/up.sh backup [file.tar.gz]` (MIA is stopped while it copies). With the database running (`deploy/up.sh db`) the archive holds `db.dump` and `data.tar` (made by `tools/backup.sh`); without it, the volume alone.
- Restore: `deploy/up.sh restore file.tar.gz`. It first saves the current state (`mia-before-restore-...`: next to the archive for one with a database, else in the current folder). An archive with a database needs the `db` service running; an old archive of the volume alone still restores.
- Restore test: once per quarter restore the newest archive into a second stack (`MIA_PROJECT=mia-restore` in a copy of the checkout) and open the page. Last restore test: <date>.

## Kinds of maintenance
| Kind | What | Schedule | Owner |
|---|---|---|---|
| Corrective | fix defects found in operation (each becomes a failing test first) | as found | owner |
| Adaptive | follow Fedora, podman, Python and image updates; re-pin the image digests | monthly | owner |
| Perfective | improvements users asked for (feedback items) | per iteration | owner |
| Preventive | dependency upgrades (`tools/check_free.py` after each), removal of dead code | each quarter | owner |

## Incidents
| Date | What happened | Cause | Fix (test first) | Finding routed to |
|---|---|---|---|---|

## Retirement plan
- Trigger: no use for six months, a model or runtime that can no longer be run, or a replacement.
- Steps: tell the users; export their data (`deploy/up.sh backup`); write the freeze record: the commit, the image digests of every service (`podman image inspect --format '{{.Digest}}'`), the model digests of `MP-light` and `MP-full` (`/api/tags`) and the configuration; save the images (`podman save`) and the models next to the archive; freeze the stack with these digests (the compose files keep the pins) and test a cold start from the saved images on a clean machine; then `deploy/up.sh db down` and keep the archive.
