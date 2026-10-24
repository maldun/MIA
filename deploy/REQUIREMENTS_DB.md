# Several MIA instances: shared state in a database (plan, not built yet)

**Status 2026-10-24: wanted again** (owner decisions D-4, D-9, D-11 of `specs/mia/review-log.md`: one shared MIA, a graph app on the database, PostgreSQL in a container). Earlier status, 2026-10-21: postponed. Nothing of this is built; one instance on the volume `mia-data` is the supported setup. This file keeps the requirements and the design for later. Start with stage 0 when several instances are really needed.
**Decided:** several instances are **one shared MIA with one memory** (persona `mia` for all). Separate memories stay possible later through another `persona` value, but nothing is planned for it.

Decided 2026-10-21: a database container is wanted because **several MIA instances** will run in the future (other machines, other front ends). One instance on one volume works today and stays the default.

## Goal

- `storage: "files"` (default): everything as today, no database, no new dependency.
- `storage: "postgres"` + `database_url`: the state below lives in PostgreSQL; instances on different machines share it. The compose stack gets a `db` service (profile `db`, volume `pgdata`, healthcheck) like `ollama`; `DATABASE_URL` in `deploy/.env` uses an existing server instead (same pattern as `OLLAMA_URL`).
- Moving from files to the database is one command (`deploy/up.sh migrate`), reversible by an export.

## What MIA stores today

| store | where | how it is used | for several instances |
|---|---|---|---|
| conversation history | `memories.json`, in memory in `Communicator._history`, written at shutdown | read at start, appended on every message | **the hard part**: two processes would overwrite each other; needs a decision (below) and writing on every message instead of at shutdown |
| long-time history / summaries | `long_time_history.json` | rewritten when conversations are summarized | same, plus one summarizer at a time (row lock) |
| chat log of the page | `data/chat_log.jsonl`, trimmed to `chat_log_max_messages` | append, read the last N, trim | easy: an append-only table with an auto id |
| feedback log | `data/feedback_log.jsonl` | append; read as examples for the next prompts | easy: append-only table |
| expression presets, gestures | one JSON file per name, atomic write | read all, write one, the editor has a token | easy: key/value rows with a version number (last writer wins, version shown) |
| moods | `moods.json` | small state with a timer | per persona row |
| library of pipelines/skills | files in `library/`, index `library.sqlite` derived from them | content-addressed entries, status file | files stay the source (they are reviewed and in git); the index can be rebuilt per instance, so it stays local |
| runs, web log | `data/runs/*.jsonl` | append-only logs | table or stay files per instance (logs of one machine) |
| editor/chat token, calibration, config | files / env | read at start | stay as they are (config, secrets) |
| 3D character, models | volumes | read only | stay files |

## Design

1. **A small storage layer** (`storage.py`): one interface per store above (`ChatLog`, `Feedback`, `Histories`, `Presets`, `Gestures`, `Moods`) with the file implementation (today's code moved behind it, behaviour unchanged, tests unchanged) and a Postgres implementation. `Communicator`, `chat_log.py`, `preset_store.py` etc. get their store passed in; `config` picks it.
2. **Postgres**, not SQLite: SQLite on a shared volume is not safe across machines. Driver `psycopg` (3), only imported when `storage` is `postgres`; `requirements-db.txt` keeps the core file short.
3. **Namespaces**: every row has `persona` (default `mia`) and, where it matters, `instance_id`. Whether instances share one persona (one MIA, several front doors, one memory) or each have their own is a setting, not a code change: the namespace is a config value.
4. **Histories**: written after every exchange (not at shutdown), a message is a row `(persona, seq, role, content, created)`; the summarizer takes a row lock (`SELECT ... FOR UPDATE SKIP LOCKED`) so only one instance summarizes. The in-memory list is a cache reloaded when another instance has appended (cheap check of the last seq before each answer).
5. **Schema** by numbered SQL files in `deploy/db/` applied at start (table `schema_version`), no ORM.
6. **Compose**: `db` (postgres:16, profile `db`, volume `pgdata`, `POSTGRES_PASSWORD` in `.env` made by `up.sh`), MIA waits for it like for Ollama (`database_wait`). `up.sh backup|restore` use `pg_dump` and `psql` in the container.
7. **Migration**: `python -m MIA.migrate files-to-db` (and back) reads the file stores through the same interfaces, so both directions are the same code; `up.sh migrate` runs it in the container. Idempotent (rows keyed by their content/time), dry run first.

## Stages (each one is useful and tested on its own)

0. Storage interfaces with the file implementation only; all tests green, nothing changes for users.
1. Postgres for the append-only logs (chat log, feedback, web/run log) + compose `db` service + migrate for those.
2. Presets, gestures, moods.
3. Histories and summaries with the multi-instance rules (the part that needs the decision below and real concurrency tests with two processes).
4. Backup/restore, docs, a two-instance test stack in compose (`MIA_PROJECT` already allows a second stack).

## Tests

- Unit: the interface contract tests run against both implementations (same test, two backends); the Postgres one against a throwaway container (`postgres:16`, tmpfs), skipped without podman.
- Two MIA processes against one database: messages from both appear in order on both sides; one summary, not two.
- Migration: files → database → files gives identical files.

## Decisions

- **One shared MIA with one memory** (decided 2026-10-21): all instances use persona `mia`. Consequences for stage 3: the history is one sequence of messages for everybody, so two instances answering at the same moment must see each other's messages (reload when the last `seq` changed, before and after the model call) and an exchange is written as a unit. Open question for then: whether two simultaneous questions are answered one after the other (a lock per persona, simple) or in parallel (they would not see each other).
- Postgres is assumed. A different database works with the same layer, only the SQL files change.
- Postponed until several instances are needed. Until then nothing changes in the code; the migration of the files to the database is planned for the day it starts (`memories` and `calibration` commands of `deploy/up.sh` already move the old files into the volume).
