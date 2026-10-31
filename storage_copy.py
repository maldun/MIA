"""
Copying records between backends: library export and seed (REQ-SLY-009) and the migration between files and the database (REQ-SLY-007).

All three are one operation: the raw version lists (with author and time) of the chosen tables go from one backend to another. Nothing is
renumbered, so a copy is identical to its source. What put would refuse is refused here too (finding F1): every document is validated by the table
definitions (REQ-SLY-004), and the versions of a record must be its own and run 1..n without a gap (REQ-SLY-003), because get reads a version by
its position. The operation is idempotent: a record that is already there with the same versions is skipped; a target that has only the first
versions of the source gets the missing ones. A target with a different history is a conflict and a refused record is `invalid`; either way the
whole copy is refused before the first write (two passes), so a half copy cannot happen.
"""
try:
    from .storage import StorageError, table_definitions, validate
    from .storage_files import FileBackend
except ImportError:  # used as plain script / in tests
    from storage import StorageError, table_definitions, validate
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
            _check_entries(table, record_id, wanted)
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


def _check_entries(table, record_id, entries):
    """Raises StorageError("invalid") with the table and id of the record when its versions could not have come from put."""
    def refuse(rule, detail):
        raise StorageError("invalid", rule=rule, detail={"table": table, "id": record_id, "detail": detail})
    for number, entry in enumerate(entries, 1):
        if entry.get("id") != record_id:
            refuse("id", entry.get("id"))
        if entry.get("version") != number:
            refuse("versions", [e.get("version") for e in entries])
        try:
            validate(table, entry.get("doc"))
        except StorageError as err:
            refuse(err.rule, err.detail)


def export_library(store, folder):
    """The workflows and context graphs of the store as files in a folder (the file backend format)."""
    return copy_records(store.backend, FileBackend(folder), LIBRARY_TABLES)


def seed_library(store, folder):
    """The library of a folder into the store; an existing library with other versions is a conflict."""
    return copy_records(FileBackend(folder), store.backend, LIBRARY_TABLES)
