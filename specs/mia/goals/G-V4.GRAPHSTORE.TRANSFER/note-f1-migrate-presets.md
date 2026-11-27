# Note for G-V4.GRAPHSTORE.TRANSFER: F-1 of G-V4.VIEW's Deploy – `migrate files-to-db` stops on `presets`

**From:** G-V4.VIEW Deploy, 2026-11-26 (`specs/mia/goals/G-V4.VIEW/deployment-record.md`, Findings). **Handed to TRANSFER by the owner** (questionnaire, D-503): TRANSFER moves the whole store between files and the database without loss (its statement), so the move must run on the owner's real data volume. **Not fixed yet; nothing was written by the failing run.**

## What happened
On the owner's host, in the running container of the live stack (image `localhost/mia:g-v4-view`, `goal/v4` @ 78d3e67f):

```
python -m MIA.migrate files-to-db --data /opt/mia/MIA/data --database-url "$MIA_DATABASE_URL" --dry-run
...
  File "/opt/mia/MIA/storage_copy.py", line 31, in copy_records
    _check_entries(table, record_id, wanted)
  File "/opt/mia/MIA/storage_copy.py", line 53, in _check_entries
    if entry.get("id") != record_id:
AttributeError: 'str' object has no attribute 'get'
```

The module docstring of `migrate.py` promises that a refused copy is one line with exit code 1, not a traceback.

## Cause (read, not yet proven by a test)
- The live data volume holds 16 records in `presets` (the character's expressions: `no`, `yes`, `happy`, ..., `shocked`), and nothing else the storage layer knows (0 graphs).
- Each preset file is **one plain object** (`{"name": "no", "description": ..., "weights": ..., "bones": ..., "gesture": ..., "speaking": ..., "tags": ..., "source": ..., "updated": ...}`), not a list of versions. Something writes these files directly, outside `put`.
- `FileBackend.versions` (`storage_files.py:23`) returns whatever JSON the file holds; `migrate files-to-db` copies every table of `table_definitions()` (`migrate.py:77`, no choice of tables); `_check_entries` (`storage_copy.py:48`) iterates the object, gets its keys as strings, and calls `.get` on them.

## What TRANSFER has to decide and do
1. **Failing test first** (CLAUDE.md: every finding gets a test): a file store with one record in the shape above, then `migrate files-to-db --dry-run` (and `copy_records`): today a traceback.
2. Then one of (an owner decision; it touches N-3.1 storage and IF-302, so possibly an amendment):
   - the copy refuses such a record with one line naming `presets/<id>` and exit 1, nothing written (what the docstring promises);
   - and/or the preset files get the stored form (a version list), written by whoever writes them today, with a one-time conversion of the existing 16;
   - and/or `migrate` copies only chosen tables (`--tables`), so the graph tables can move alone.
3. Before TRANSFER's gate (D-460) moves the live store to the database: a dry run on a copy of the owner's real volume, not only on fixtures.

## Related
- V-3 (also handed to TRANSFER): a PostgreSQL store never reconnects, and MIA does not start while the database is down; seen again in VIEW's Deploy (V-10 step).
- F-2 of the same Deploy (`deploy/preflight.sh` checks the container-side `OLLAMA_URL` from the host) is not TRANSFER's.
