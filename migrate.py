"""
Migration between the file storage and the database, and the library export and seed (REQ-SLY-007, REQ-SLY-009).

  python -m MIA.migrate files-to-db   --data DIR --database-url URL [--dry-run]
  python -m MIA.migrate db-to-files   --data DIR --database-url URL [--dry-run]
  python -m MIA.migrate library-export --data DIR --folder DIR [--dry-run]
  python -m MIA.migrate library-seed   --data DIR --folder DIR [--dry-run]
  python -m MIA.migrate lag            --data DIR | --database-url URL  --copy DIR
  python -m MIA.migrate sync           --data DIR | --database-url URL  --copy DIR

Each direction is one command and both use the same code (graph_store_transfer.move_store), so a round trip gives back the files. A second run
copies nothing; a target with a different history is a conflict, a record that put would refuse and a graph whose header names a missing step,
connection end or an unknown kind are named (exit code 1 for all) and nothing is written (REQ-SLY-016 to 021). Export and seed carry the graph
group and the library entries (REQ-SLY-009). The database side is opened only when it is needed,
so a file-only installation never imports a database driver. A missing source folder, a database that cannot be opened and a refused copy are
one line each with exit code 1, not a traceback.

lag and sync keep a copy folder in step with the live store (the data folder, or the database when an address is given; REQ-SLY-039): lag prints
one line per graph that is not current, sync brings the copy to the live store, names what it set aside and is refused while another sync holds
the copy's lock (REQ-SLY-024 to 028). They may run while MIA runs.
"""
import argparse
import os
import sys

try:
    from .graph_store_transfer import lag, move_store, sync_store
    from .storage import StorageError
    from .storage_copy import copy_records, library_tables
    from .storage_files import FileBackend
except ImportError:  # used as plain script / in tests
    from graph_store_transfer import lag, move_store, sync_store
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
    parser.add_argument("--data", help="the data folder of the file storage (lag, sync: the live store when no --database-url is given)")
    parser.add_argument("--database-url", help="the PostgreSQL address (files-to-db, db-to-files; lag, sync: the live store)")
    parser.add_argument("--folder", help="the library folder (library-export, library-seed)")
    parser.add_argument("--dry-run", action="store_true", help="say what would be copied, write nothing")
    return parser


def main(argv=None, open_db=_open_postgres):
    try:
        return _run(argv, open_db)
    except StorageError as err:            # a set of a newer format is refused when it is opened (REQ-SLY-035): one line, not a traceback
        if err.code != "format":
            raise
        print(_explain(err))
        return 1


def _run(argv, open_db):
    parser = _parser()
    args = parser.parse_args(argv)
    if args.command in ("lag", "sync"):
        return _copy_command(parser, args, open_db)
    if not args.data:
        parser.error("%s needs --data" % args.command)
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


def _copy_command(parser, args, open_db):
    """lag or sync of the copy folder against the live store (REQ-SLY-039)"""
    if not args.copy or not (args.data or args.database_url):
        parser.error("%s needs --copy and the live store (--data or --database-url)" % args.command)
    if not args.database_url and not os.path.isdir(args.data):
        print("no such folder: %s" % args.data)
        return 1
    copy = FileBackend(args.copy)
    try:
        live = open_db(args.database_url) if args.database_url else FileBackend(args.data)
    except CannotOpen as err:
        print("cannot open the database: %s" % err)
        return 1
    try:
        if args.command == "lag":
            for graph_id, row in sorted(lag(live, copy).items()):
                print(("%-40s live %-3d copy %-3d %s %s" % (graph_id, row["live"], row["copy"], row["state"], row["reason"] or "")).rstrip())
            return 0
        answer = sync_store(live, copy)
    except StorageError as err:
        print(_explain(err))
        return 1
    finally:
        live.close()
    print("synced %d records, set aside %d graphs" % (answer["records"], len(answer["set_aside"])))
    for graph_id, named in sorted(answer["set_aside"].items()):     # named to the owner (REQ-SLY-027): which versions, in which file
        print("  %s: versions %s set aside in %s (%s)" % (graph_id, named["versions"], os.path.join(args.copy, named["file"]), named["reason"]))
    return 0


def _target(target, dry_run):
    return _Discard(target) if dry_run else target


def _explain(err):
    if err.code == "format":
        return "refused: a set of files has format %d, this MIA knows format %d (nothing was written)" % (err.detail["found"], err.detail["known"])
    if err.rule == "older_format":
        return "refused: %s/%s has an ID from before scoped IDs; convert the set first with %s (nothing was written)" % (
            err.detail["table"], err.detail["id"], err.detail["conversion"])
    if err.code == "locked":
        return "refused: another sync or move holds the copy's lock %s (nothing was written)" % err.detail["lock"]
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
