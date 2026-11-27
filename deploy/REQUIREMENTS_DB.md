# Several MIA instances: shared state in a database (partly built)

**Status 2026-11-27: the shared storage layer and the `db` service are built; the graphs are the only state MIA keeps in the database so far.** One instance on the volume `mia-data` is still the default and the supported setup for everything else (chat history, chat log, feedback, presets, votes, accounts). What exists and what is still a plan is listed per stage below. Earlier: wanted again on 2026-10-24 (owner decisions D-4, D-9, D-11 of `specs/mia/review-log.md`: one shared MIA, a graph app on the database, PostgreSQL in a container); postponed on 2026-10-21.
**Decided:** several instances are **one shared MIA with one memory** (persona `mia` for all). Separate memories stay possible later through another `persona` value, but nothing is planned for it.

Decided 2026-10-21: a database container is wanted because **several MIA instances** will run in the future (other machines, other front ends). One instance on one volume works today and stays the default.

## Goal

- `store: "files"` (default, `setup_cfg*.json`): everything as before, no database, no new dependency.
- `store: "database"` + `MIA_DATABASE_URL` in the environment: the graphs (IF-104 v2) live in PostgreSQL; instances on different machines share them. Any other value of `store`, or `database` without the URL, stops the start (REQ-API-019, 020). The compose stack has a `db` service (profile `db`, volume `pgdata`, healthcheck) like `ollama`; `deploy/up.sh db` starts it and writes `POSTGRES_PASSWORD` and `MIA_DATABASE_URL` into `deploy/.env` once.
- Moving the records between files and the database is one command (`python -m MIA.migrate files-to-db`, run in the `mia` container, see item 7 of the design), reversible by `db-to-files`.
- Later (not built): the other stores below move behind the same layer, so a second instance shares history, logs and presets too.

## What MIA stores today

| store | where | how it is used | for several instances |
|---|---|---|---|
| graphs (workflows, skills, their changes) | Storage layer: files under `data/db`, or PostgreSQL with `store: "database"` | versioned records, IF-104 v2 | **shared** with the database: versions are numbered without gaps across instances, notices go to the other instances |
| votes, accounts, memory records, skill records, skill runs, workflow library | Storage layer, always the file backend in `data/db` (`accounts_dir`) | versioned records (IF-302) | the tables exist for both backends; only the wiring in `web_app.py` still uses the files |
| conversation history | `memories.json`, in memory in `Communicator._history`, written at shutdown | read at start, appended on every message | **the hard part**: two processes would overwrite each other; needs a decision (below) and writing on every message instead of at shutdown. The record table `history` exists, the Communicator does not use it yet |
| long-time history / summaries | `long_time_history.json` | rewritten when conversations are summarized | same, plus one summarizer at a time |
| chat log of the page | `data/chat_log.jsonl`, trimmed to `chat_log_max_messages` | append, read the last N, trim | easy: records of their own |
| feedback log | `data/feedback_log.jsonl` | append; read as examples for the next prompts | easy: records of their own |
| expression presets, gestures | one JSON file per name, atomic write (`preset_store.py`) | read all, write one, the editor has a token | the tables `presets` and `gestures` exist (versioned, last writer gets a conflict); the editor does not use them yet |
| moods | `moods.json` | small state with a timer | per persona |
| library of pipelines/skills | files in `library/`, index `library.sqlite` derived from them | content-addressed entries, status file | files stay the source (they are reviewed and in git); `migrate library-export` / `library-seed` copy them to and from the records |
| runs, web log | `data/runs/*.jsonl` | append-only logs | stay files per instance (logs of one machine) |
| editor/chat token, calibration, config | files / env | read at start | stay as they are (config, secrets) |
| 3D character, models | volumes | read only | stay files |

## Design (as built, unless marked "plan")

1. **One storage layer** (`storage.py`, IF-102): one generic store of versioned records for all tables (the tables come from IF-301 and IF-302), not one interface per store. Every put is a new immutable version with author and time; `expected_version` guards against a lost update; a refused document takes no version; subscribers are told after every write. A backend only holds the bytes: `storage_files.py` (`FileBackend`) and `storage_postgres.py` (`PostgresBackend`) behave the same.
2. **Postgres**, not SQLite: SQLite on a shared volume is not safe across machines. Driver `psycopg` (3), only imported when `store` is `database`; `requirements-db.txt` keeps the core file short.
3. **Several instances**: the PostgreSQL backend sends notices through LISTEN/NOTIFY on the channel `mia_changes`, tagged with the instance, so each instance hears the writes of the others (and reconnects when the server drops it). The primary key `(tbl, id, version)` makes the loser of two simultaneous writes get a conflict. **Plan:** namespaces by `persona` (and `instance_id` where it matters) for the histories.
4. **Plan, histories**: written after every exchange (not at shutdown), one record per message; only one instance summarizes at a time; the in-memory list is a cache reloaded when another instance has appended (cheap check of the last version before each answer).
5. **Schema**: numbered SQL files in `deploy/db/` (today `001_records.sql`: table `schema_version` and one table `records` for all record versions), no ORM. The `db` service applies them when it creates its data volume (`docker-entrypoint-initdb.d`), not at every start: a later schema file needs a migration step of its own.
6. **Compose**: `db` (postgres:16 by digest, profile `db`, volume `pgdata`, `POSTGRES_PASSWORD` in `.env` made by `up.sh db`). `deploy/up.sh backup|restore` also save and restore the database when the `db` service runs (`tools/backup.sh`, `tools/restore.sh`: `pg_dump` and `psql` in the container; see `deploy/README.md`).
7. **Migration**: `python -m MIA.migrate files-to-db` (and `db-to-files`) copies the records through the same layer, so both directions are the same code (`migrate.py`, `storage_copy.py`); `library-export` and `library-seed` copy the library. There is no `up.sh migrate`; with the database running (`deploy/up.sh db`), it runs in the container through the compose pass-through of `up.sh`:
   `deploy/up.sh exec mia sh -c 'python -m MIA.migrate files-to-db --data MIA/data/db --database-url "$MIA_DATABASE_URL" --dry-run'`
   (drop `--dry-run` to write). Idempotent (a second run copies nothing; a conflict writes nothing).

8. **Moving and syncing** (G-V4.GRAPHSTORE.TRANSFER, merged 2026-11-27, `graph_store_transfer.py`, REQ-SLY-016 to 039): a whole store or one graph moves between files and the database, each graph checked before anything is written; a files copy of the live store is kept current by `python -m MIA.migrate lag` and `sync` (`--copy <folder>`, live store by `--data` or `--database-url`), and MIA can sync it at start and orderly stop (AutoSync, REQ-API-062, 063). One sync at a time (a lock in the copy); the copy's own changes are set aside, never lost.

## Stages (each one is useful and tested on its own)

| Stage | What | State 2026-11-27 |
|---|---|---|
| 0 | Storage layer with the file backend; all tests green, nothing changes for users | **done** (`storage.py`, `storage_files.py`) |
| 1 | PostgreSQL backend + compose `db` service + migrate | **done** for the records (`storage_postgres.py`, `deploy/db/`, `migrate.py`); only the graphs use the database. The append-only logs (chat log, feedback) are still files |
| 2 | Presets, gestures, moods | **open**: the record tables `presets` and `gestures` exist, the editor and `moods.py` still use files |
| 3 | Histories and summaries with the multi-instance rules | **open** (needs the decision below and real concurrency tests with two processes) |
| 4 | Backup/restore, docs, a two-instance test stack in compose | backup/restore and docs **done**; the two-instance stack (`MIA_PROJECT` allows a second stack) **open** |

## Tests

- Unit: the IF-102 contract suite runs against both backends (`tests/test_storage_postgres.py` against a throwaway postgres:16 on tmpfs, skipped without podman, the image or psycopg 3; `tools/contract_postgres.sh`). It includes two instances on one database: a write or delete on one is heard on the other, and two writers of the same record never share a version.
- Migration: `tests/test_migrate.py` (files → database → files).
- Plan, stage 3: two MIA processes against one database: messages from both appear in order on both sides; one summary, not two.

## Decisions

- **One shared MIA with one memory** (decided 2026-10-21): all instances use persona `mia`. Consequences for stage 3: the history is one sequence of messages for everybody, so two instances answering at the same moment must see each other's messages (reload when the last version changed, before and after the model call) and an exchange is written as a unit. Open question for then: whether two simultaneous questions are answered one after the other (a lock per persona, simple) or in parallel (they would not see each other).
- Postgres is assumed. A different database works with the same layer, only the backend and the SQL files change.
- One generic table of record versions instead of one table per store (as built, N-3.1, REQ-SLY-001): the rules stay in `storage.py`, the backends stay small, and a new record table needs no schema change.
- Stages 2 to 4 wait until several instances are really needed; the `memories` and `calibration` commands of `deploy/up.sh` already move the old files into the volume.
