"""
Copying records between backends: library export and seed (REQ-SLY-009) and the migration between files and the database (REQ-SLY-007).

All three are one operation: the raw version lists (with author and time) of the chosen tables go from one backend to another. Nothing is validated
or renumbered, so a copy is identical to its source. The operation is idempotent: a record that is already there with the same versions is skipped;
a target that has only the first versions of the source gets the missing ones; a target with a different history is a conflict, and the whole copy
is refused before the first write (two passes), so a half copy cannot happen.
"""
try:
    from .storage import StorageError, table_definitions
    from .storage_files import FileBackend
except ImportError:  # used as plain script / in tests
    from storage import StorageError, table_definitions
    from storage_files import FileBackend

LIBRARY_TABLES = ("workflows", "context_graphs")


def copy_records(source, target, tables):
    """Returns {"copied": records new in the target, "skipped": records already equal, "added_versions": versions appended to existing records}."""
    known = table_definitions()
    for table in tables:
        if table not in known:
            raise StorageError("unknown_table", detail=table)
    plan, counts = [], {"copied": 0, "skipped": 0, "added_versions": 0}
    for table in tables:
        for record_id in source.ids(table):
            wanted, have = source.versions(table, record_id), target.versions(table, record_id)
            if have != wanted[:len(have)]:
                raise StorageError("conflict", detail={"table": table, "id": record_id})
            if len(have) == len(wanted):
                counts["skipped"] += 1
                continue
            if have:
                counts["added_versions"] += len(wanted) - len(have)
            else:
                counts["copied"] += 1
            plan.append((table, record_id, wanted[len(have):]))
    for table, record_id, entries in plan:
        for entry in entries:
            target.append(table, record_id, entry)
    return counts


def export_library(store, folder):
    """The workflows and context graphs of the store as files in a folder (the file backend format)."""
    return copy_records(store.backend, FileBackend(folder), LIBRARY_TABLES)


def seed_library(store, folder):
    """The library of a folder into the store; an existing library with other versions is a conflict."""
    return copy_records(FileBackend(folder), store.backend, LIBRARY_TABLES)
