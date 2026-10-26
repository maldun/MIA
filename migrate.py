"""
Migration between the file storage and the database, and the library export and seed (REQ-SLY-007, REQ-SLY-009).

  python -m MIA.migrate files-to-db   --data DIR --database-url URL [--dry-run]
  python -m MIA.migrate db-to-files   --data DIR --database-url URL [--dry-run]
  python -m MIA.migrate library-export --data DIR --folder DIR
  python -m MIA.migrate library-seed   --data DIR --folder DIR

Each direction is one command and both use the same code (storage_copy.copy_records), so a round trip gives back the files. A second run copies
nothing; a target with a different history is a conflict (exit code 1) and nothing is written. The database side is opened only when it is needed,
so a file-only installation never imports a database driver.
"""
import argparse
import sys

try:
    from .storage import Storage, StorageError, table_definitions
    from .storage_copy import copy_records, export_library, seed_library
    from .storage_files import FileBackend
except ImportError:  # used as plain script / in tests
    from storage import Storage, StorageError, table_definitions
    from storage_copy import copy_records, export_library, seed_library
    from storage_files import FileBackend


def _open_postgres(url):
    try:
        from .storage_postgres import PostgresBackend
    except ImportError:
        from storage_postgres import PostgresBackend
    return PostgresBackend(url)


def _parser():
    parser = argparse.ArgumentParser(prog="migrate", description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("files-to-db", "db-to-files", "library-export", "library-seed"))
    parser.add_argument("--data", required=True, help="the data folder of the file storage")
    parser.add_argument("--database-url", help="the PostgreSQL address (files-to-db, db-to-files)")
    parser.add_argument("--folder", help="the library folder (library-export, library-seed)")
    parser.add_argument("--dry-run", action="store_true", help="say what would be copied, write nothing")
    return parser


def main(argv=None, open_db=_open_postgres):
    parser = _parser()
    args = parser.parse_args(argv)
    needs = "folder" if args.command.startswith("library") else "database_url"
    if not getattr(args, needs):
        parser.error("%s needs --%s" % (args.command, needs.replace("_", "-")))
    files = FileBackend(args.data)
    try:
        if args.command == "library-export":
            counts = export_library(Storage(files), args.folder)
        elif args.command == "library-seed":
            counts = seed_library(Storage(files), args.folder)
        else:
            database = open_db(args.database_url)
            source, target = (files, database) if args.command == "files-to-db" else (database, files)
            if args.dry_run:
                counts = copy_records(source, _Discard(target), list(table_definitions()))
            else:
                counts = copy_records(source, target, list(table_definitions()))
    except StorageError as err:
        print("conflict: %s (nothing was written)" % (err.detail,) if err.code == "conflict" else "error: %s" % err)
        return 1
    print("%scopied %d records, skipped %d, added %d versions" % ("dry run: " if args.dry_run else "", counts["copied"], counts["skipped"], counts["added_versions"]))
    return 0


class _Discard:
    """A target that reads like the real one and writes nothing, for the dry run."""

    def __init__(self, target):
        self._target = target

    def versions(self, table, record_id):
        return self._target.versions(table, record_id)

    def append(self, table, record_id, entry):
        pass


if __name__ == "__main__":
    sys.exit(main())
