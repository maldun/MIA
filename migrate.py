"""
Migration between the file storage and the database, and the library export and seed (REQ-SLY-007, REQ-SLY-009).

  python -m MIA.migrate files-to-db   --data DIR --database-url URL [--dry-run]
  python -m MIA.migrate db-to-files   --data DIR --database-url URL [--dry-run]
  python -m MIA.migrate library-export --data DIR --folder DIR [--dry-run]
  python -m MIA.migrate library-seed   --data DIR --folder DIR [--dry-run]

Each direction is one command and both use the same code (graph_store_transfer.move_store), so a round trip gives back the files. A second run
copies nothing; a target with a different history is a conflict, a record that put would refuse and a graph whose header names a missing step,
connection end or an unknown kind are named (exit code 1 for all) and nothing is written (REQ-SLY-016 to 021). Export and seed carry the graph
group and the library entries (REQ-SLY-009). The database side is opened only when it is needed,
so a file-only installation never imports a database driver. A missing source folder, a database that cannot be opened and a refused copy are
one line each with exit code 1, not a traceback.
"""
import argparse
import os
import sys

try:
    from .graph_store_transfer import move_store
    from .storage import StorageError
    from .storage_copy import copy_records, library_tables
    from .storage_files import FileBackend
except ImportError:  # used as plain script / in tests
    from graph_store_transfer import move_store
    from storage import StorageError
    from storage_copy import copy_records, library_tables
    from storage_files import FileBackend


class CannotOpen(Exception):
    """The database cannot be opened: no driver, or the server does not answer."""


def _open_postgres(url):
    try:
        try:
            from .storage_postgres import PostgresBackend
        except ImportError:
            from storage_postgres import PostgresBackend
        import psycopg
    except ImportError as err:
        raise CannotOpen("the database side needs psycopg 3 (requirements-db.txt): %s" % err) from None
    try:
        return PostgresBackend(url)
    except psycopg.OperationalError as err:
        raise CannotOpen(str(err).strip().splitlines()[0] if str(err).strip() else type(err).__name__) from None


def _parser():
    parser = argparse.ArgumentParser(prog="migrate", description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=("files-to-db", "db-to-files", "library-export", "library-seed", "lag", "sync"))
    parser.add_argument("--copy", help="the copy folder (lag, sync; G-V4.GRAPHSTORE.TRANSFER, REQ-SLY-039)")
    parser.add_argument("--data", required=True, help="the data folder of the file storage")
    parser.add_argument("--database-url", help="the PostgreSQL address (files-to-db, db-to-files)")
    parser.add_argument("--folder", help="the library folder (library-export, library-seed)")
    parser.add_argument("--dry-run", action="store_true", help="say what would be copied, write nothing")
    return parser


def main(argv=None, open_db=_open_postgres):
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command in ("lag", "sync"):            # STUB of Plan step 4: built in T-03 (REQ-SLY-039)
        print("%s: not built yet" % args.command)
        return 1
    needs = "folder" if args.command.startswith("library") else "database_url"
    if not getattr(args, needs):
        parser.error("%s needs --%s" % (args.command, needs.replace("_", "-")))
    source_folder = args.folder if args.command == "library-seed" else args.data
    if args.command != "db-to-files" and not os.path.isdir(source_folder):
        print("no such folder: %s" % source_folder)              # a typo would otherwise copy 0 records and say it worked (F10)
        return 1
    files = FileBackend(args.data)
    try:
        if args.command.startswith("library"):
            folder = FileBackend(args.folder)
            source, target = (files, folder) if args.command == "library-export" else (folder, files)
            counts = copy_records(source, _target(target, args.dry_run), library_tables())
        else:
            database = open_db(args.database_url)
            try:                                  # an open connection left behind is a ResourceWarning (F4) and a server slot
                source, target = (files, database) if args.command == "files-to-db" else (database, files)
                counts = move_store(source, _target(target, args.dry_run))
            finally:
                database.close()
    except CannotOpen as err:
        print("cannot open the database: %s" % err)
        return 1
    except StorageError as err:
        print(_explain(err))
        return 1
    print("%scopied %d records, skipped %d, added %d versions" % ("dry run: " if args.dry_run else "", counts["copied"], counts["skipped"], counts["added_versions"]))
    return 0


def _target(target, dry_run):
    return _Discard(target) if dry_run else target


def _explain(err):
    if err.rule == "move_refused":
        graphs = ["%s: %s" % (graph, ", ".join("%s %s" % (p["rule"], p["detail"]) for p in problems))
                  for graph, problems in err.detail["graphs"].items()]
        return "refused: %s (nothing was written)" % "; ".join(graphs)
    if err.code == "conflict":
        return "conflict: %s (nothing was written)" % (err.detail,)
    if err.code == "invalid":
        return "refused: %s/%s (%s: %s) (nothing was written)" % (err.detail["table"], err.detail["id"], err.rule, err.detail["detail"])
    return "error: %s" % err


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
