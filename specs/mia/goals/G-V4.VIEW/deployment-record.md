# Deployment record: G-V4.VIEW → reference host (maldun's workstation)

**Kind:** subgoal (no version, no tag)   **Commit:** `goal/v4` @ 78d3e67f (VIEW merged at 34fb0534)   **Date:** 2026-11-26
**Goal:** G-V4.VIEW   **Deployed by:** Claude session mia-48, the owner chose each step (image, folder, data for the look)
**Artifact:** image `localhost/mia:g-v4-view`, id `7c8618d359c0f5307681c74e2ffd38ae8648a5ae419256257f9abcccb32ecd74`, base `python:3.12-slim@sha256:2b4f19da...`. Built on the target from the clean worktree with the build line of `deploy/build.sh` (`podman build --pull=never -f deploy/Containerfile`, plus `--network=host` and pip retries for the slow network); `build.sh` itself refuses anything but a tag, and a subgoal gets none (owner, 2026-11-26). Not tagged `:latest`, which stays RUN's branch build. Checked inside: psycopg 3.3.9, no `deploy/.env`, no `dist/`.
**Target:** Fedora (kernel 6.18), podman 5.7.1, host Ollama 0.40.5 (container `ollama`), loopback only. Host rebooted 2026-11-26 19:24; the stack was down before this deployment.
**Configuration:** started from the worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4` with copies of the machine's `deploy/.env` and `deploy/setup_cfg.local.json` (both git-ignored); always with `MIA_IMAGE=localhost/mia:g-v4-view`.

| Stack | Ports | Store | Data | Purpose |
|---|---|---|---|---|
| `mia` (live) | 8585, 8586 | files | the owner's volumes (no graphs; only the 16 presets) | runs the new image; stays on files until TRANSFER's gate (D-460) |
| `mia-view` (throwaway) | 8595, 8596 | files, then database (`MIA_CONFIG=./setup_cfg.view-db.json`, untracked) | own volumes and own PostgreSQL 16, seeded with the VIEW fixture graphs (`tests/helpers/graph_view_data.seed`: 6 graphs, 9 versions, the same in files and database) | the owner's look and the smoke checks (owner, 2026-11-26: the live store has no graphs) |

## Preflight
| Check | Result |
|---|---|
| `deploy/preflight.sh` | OK with `OLLAMA_URL=http://127.0.0.1:11434`; with `.env`'s value P1 fails (F-2). Warnings as for v0.2.1: no character page, no Kokoro voice, no voice lines, `sandbox_backend: none` |
| `preflight_agent.py` | P3 MP-light 38044be4f923, MP-full 001e5dafc3c7 = pins; PASS |
| GPU devices, ports, disk | ok (1533 GB free) |

## Smoke tests
| Test | Result |
|---|---|
| SMOKE-VIEW-001 `smoke_view_image.py` (TR-VIEW-016) | **green**, run by the owner 2026-11-26 against `mia-view` with `store: database` (`--user maldun --url https://localhost:8596 --image localhost/mia:g-v4-view`): `import psycopg` yes (3.3.9); `GET /api/v2/store` `{"store": "database", "reachable": true, "live_reachable": true, "shown": "live", "lag": {"graphs": 0, "since": null}}`; rc 0 |
| SMOKE-VIEW-002 `smoke_view_open_time.py` (TR-VIEW-017, measured) | `chain.fifty`, Firefox 157, five openings after one warm-up: 97, 100, 92, 122, 88 ms; median **97 ms**, range 88 to 122 ms |
| Stack | graph page 200 on 8586 and 8596; all five services up in both stacks |

## The owner's look (exit criterion), 2026-11-26
| Item | Result |
|---|---|
| Files: the six graphs listed and drawn; V-1 keyboard, V-2 drag then dark, V-8 log out then History and Previous, V-11 MIA stopped, `sample.broken` (TD-92), `chain.fifty` after `fit` | done, no finding reported; TD-92's trigger did not fire |
| Database: the same graphs listed and drawn | yes ("the same graphs show") |
| V-10 store stopped | MIA restarted while the database was still stopped did not come up (`failed to resolve host 'db'`); after `podman start` of the database and a restart of MIA it answered again. Both halves are V-3 (handed to TRANSFER), no new finding |
| Empty store (graph records deleted from `mia-view`'s database: 138 rows) | "the empty list shows fine" |

## Rollback
Previous image `localhost/mia:v0.2.1` (id `439429d0b8d5`). Command: in the main checkout, `MIA_IMAGE=localhost/mia:v0.2.1 deploy/up.sh rocm db down; MIA_IMAGE=localhost/mia:v0.2.1 deploy/up.sh rocm db up -d --no-build`; the data volumes stay. Tested for v0.2.1 on 2026-11-20; not tested again (no data format changed: the live store holds no graphs).

## Findings
| ID | Finding | Goes to |
|---|---|---|
| F-1 | `python -m MIA.migrate files-to-db --dry-run` on the live volume stops with a traceback (`AttributeError: 'str' object has no attribute 'get'` in `storage_copy._check_entries`): the file store keeps `presets` as plain documents, not version lists, and `migrate` copies every table without a choice. Its docstring promises one line and exit 1. Nothing was written | G-V4.GRAPHSTORE.TRANSFER (owner, 2026-11-26): a failing test there first, before the migration of the live store |
| F-2 | `deploy/preflight.sh` reads `OLLAMA_URL` from `deploy/.env` and checks it from the host; `http://host.containers.internal:11434` resolves only inside containers, so P1 fails although Ollama answers | deployment script defect: a check first, then the fix (open) |

## Known issues
- V-3 (TRANSFER): a PostgreSQL store does not reconnect; MIA does not start while the database is down. Seen again in V-10 above.
- `deploy/compose.yaml` defaults to `localhost/mia:latest`, which is RUN's branch build: every `deploy/up.sh` call needs `MIA_IMAGE=localhost/mia:g-v4-view` (or `v0.2.1`).
- `.containerignore` does not exclude `deploy/.env` or `dist/` (v0.2.1 F-1): copy `.env` into a worktree only after the build.
- Accepted deviations V-6, V-7, V-11, V-12, V-14; TD-91 to TD-95.

## Clean-up
- `mia-view`: removed after the owner's OK (`MIA_PROJECT=mia-view deploy/up.sh rocm db down` and its volumes).
- Image `localhost/mia-view-check:latest`: may go now that the smoke checks ran (V-15).
- Worktree files `deploy/.env`, `deploy/setup_cfg.local.json`, `deploy/setup_cfg.view-db.json`: not in git; the live stack runs from this worktree, so `.env` stays while it does.

## Validation hand-over
Validate runs in G-V5 (parked, D-386): VAL-VIEW-01, NFR-10, light and dark readability, the 220 px layers on large graphs. Ready: yes.
