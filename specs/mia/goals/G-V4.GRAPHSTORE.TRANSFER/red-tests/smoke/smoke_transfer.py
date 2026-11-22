"""
Smoke check SMOKE-TRANSFER-001 of G-V4.GRAPHSTORE.TRANSFER (REQ-SLY-016, REQ-SLY-025, REQ-SLY-026; HR-004, HR-006; TR-TRANSFER-003, -007):
move and sync on the owner's running PostgreSQL server, throw-away stores only.

On the owner's host (Deploy): a new folder with the sample store (tests/fixtures/graphs, as transfer_stores builds it), a new database `mia_smoke`
on the owner's RUNNING PostgreSQL server (started only with his yes), and a second new folder. The store is moved to `mia_smoke` and back to the
second folder; then one version of sample.code is added only on that folder and a different one in `mia_smoke`, and two versions of cp2.multi in
`mia_smoke`; the lag is asked and the sync run with `mia_smoke` as the live store and the second folder as the copy. Green when the round trip
gives equal histories, the lag names exactly cp2.multi (behind) and sample.code (differs), and after the sync the copy's graph group equals
`mia_smoke`'s and the answer names one aside file that exists. Afterwards both folders are removed and `mia_smoke` is dropped by name. MIA's own
database and files store are never written: the server URL's database part is replaced by `mia_smoke` (any other target name is refused),
CREATE and DROP run on the maintenance database `postgres`.

The server URL is found as SMOKE-CORE-001 finds it (smoke_core_graphs.server_url): --server URL | MIA_SMOKE_DATABASE_URL | MIA_DATABASE_URL |
MIA_DATABASE_URL in deploy/.env. Protected: change only through a plan amendment. Run:
  python tests/smoke/smoke_transfer.py [--server URL]        (exit 0 = green, 1 = red, 2 = cannot run)
"""
import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
for path in (REPO, os.path.join(REPO, "tests", "helpers"), os.path.join(REPO, "tests", "smoke"), HERE):
    if path not in sys.path:
        sys.path.insert(0, path)

from smoke_core_graphs import MAINTENANCE, TARGET, server_url, with_database      # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--server", help="URL of the owner's running PostgreSQL server (its database part is replaced by mia_smoke)")
    parser.add_argument("--database", default=TARGET, help="the target database; anything but mia_smoke is refused")
    args = parser.parse_args(argv)
    if args.database != TARGET:
        print("cannot run: the target database must be exactly %s, not %r (TR-TRANSFER-007)" % (TARGET, args.database))
        return 2
    url, source = server_url(args.server)
    if url is None:
        print("cannot run:", source)
        return 2
    try:
        import psycopg
    except ImportError:
        print("cannot run: psycopg 3 is not installed")
        return 2
    import graph_store_transfer as transfer
    import transfer_stores as ts
    from storage_files import FileBackend
    from storage_postgres import PostgresBackend

    admin = with_database(url, MAINTENANCE)
    try:
        with psycopg.connect(admin, autocommit=True, connect_timeout=5) as conn:
            if conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET,)).fetchone():
                print("cannot run: the database %s exists already (an earlier run?); drop it by hand first" % TARGET)
                return 2
            conn.execute("CREATE DATABASE " + TARGET)
    except psycopg.OperationalError as err:
        print("cannot run: the server (%s) does not answer: %s" % (source, str(err).strip()[:160]))
        return 2

    results = []
    first, second = tempfile.mkdtemp(prefix="mia-smoke-"), tempfile.mkdtemp(prefix="mia-smoke-")
    database = None
    try:
        start = ts.sample_store(FileBackend(first))
        database = PostgresBackend(with_database(url, TARGET))
        copy = FileBackend(second)
        transfer.move_store(start, database)
        transfer.move_store(database, copy)
        results.append(("the round trip files -> mia_smoke -> files keeps every history", ts.entries(copy) == ts.entries(start)))
        ts.ac007(database, copy, with_store=False)
        ts.new_multi_version(database, "smoke a")
        ts.new_multi_version(database, "smoke b")
        lag = transfer.lag(database, copy)
        results.append(("the lag names cp2.multi behind and sample.code differing, nothing else",
                        {g: v["state"] for g, v in lag.items()} == {ts.MULTI: "behind", ts.CODE: "differs"}))
        answer = transfer.sync_store(database, copy)
        aside = answer.get("set_aside", {}).get(ts.CODE, {}).get("file")
        results.append(("after the sync the copy equals mia_smoke", ts.graph_group(copy) == ts.graph_group(database)))
        results.append(("the sync names one aside file that exists", sorted(answer.get("set_aside", {})) == [ts.CODE]
                        and aside is not None and os.path.isfile(os.path.join(second, aside))))
    except Exception as err:                    # a crash is red, with its reason
        results.append(("the smoke run finished: %s: %s" % (type(err).__name__, str(err)[:160]), False))
    finally:
        if database is not None:
            database.close()
        shutil.rmtree(first, True)
        shutil.rmtree(second, True)
        with psycopg.connect(admin, autocommit=True, connect_timeout=5) as conn:
            conn.execute("DROP DATABASE IF EXISTS " + TARGET)
    for name, ok in results:
        print("%s  %s" % ("PASS" if ok else "FAIL", name))
    return 0 if results and all(ok for _, ok in results) else 1


if __name__ == "__main__":
    sys.exit(main())
