"""
Smoke check SMOKE-CORE-001 of G-V4.GRAPHSTORE.CORE (REQ-WFM-158, REQ-WFM-159, REQ-WFM-152; TR-CORE-003, TR-CORE-009): both graph kinds work on the
owner's two stores.

On the owner's host (Deploy): a new files directory (a temporary folder) and a new database `mia_smoke` on the owner's RUNNING PostgreSQL server.
On each store a workflow graph (tests/fixtures/graphs/sample.code, with its loop-controlling step) and a context graph (context.cp13) are saved under
throw-away IDs (`smoke-<random>`), changed twice (the description, then one step) by three accounts, and read. Green when each graph lists three
versions with its account and a time (present, not decreasing: TR-CORE-008) and each version reads back exactly as it was saved, on both stores.
Afterwards the directory is removed and the database `mia_smoke` is dropped by name. MIA's own database and files store are never written:
the database name of the server URL is replaced by `mia_smoke` (the check refuses any other target name), CREATE and DROP run on the server's
maintenance database `postgres`, and the files store is a new temporary folder.

The server: MIA's configuration names it as MIA_DATABASE_URL (deploy/.env, written by  deploy/up.sh db : postgresql://mia:<password>@db:5432/mia;
deploy/compose.yaml passes it to the mia container). The URL is taken from, in this order:
  --server URL  |  the environment variable MIA_SMOKE_DATABASE_URL  |  MIA_DATABASE_URL of the environment  |  MIA_DATABASE_URL in deploy/.env
The host `db` resolves inside the stack's network only (compose publishes no port of the database); on the host pass a URL that reaches the server.
Only the user, password, host and port of the URL are used.
Protected: change only through a plan amendment. Run:
  python tests/smoke/smoke_core_graphs.py [--server URL]        (exit 0 = green, 1 = red, 2 = cannot run)
"""
import argparse
import copy
import json
import os
import shutil
import sys
import tempfile
import urllib.parse
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, REPO)
FIXTURES = os.path.join(REPO, "tests", "fixtures", "graphs")
TARGET = "mia_smoke"                    # the only database this check creates, writes and drops (TR-CORE-009)
MAINTENANCE = "postgres"                # CREATE and DROP DATABASE run here, never in MIA's database
ACCOUNTS = ("smoke-ann", "smoke-bob", "smoke-cy")


def server_url(argument):
    """The URL of the owner's server and where it came from, or (None, reason)."""
    if argument:
        return argument, "--server"
    for name in ("MIA_SMOKE_DATABASE_URL", "MIA_DATABASE_URL"):
        if os.environ.get(name):
            return os.environ[name], "environment " + name
    env_file = os.path.join(REPO, "deploy", ".env")
    if os.path.exists(env_file):
        with open(env_file, encoding="utf-8") as f:
            for line in f:
                key, _, value = line.strip().partition("=")
                if key == "MIA_DATABASE_URL" and value:
                    return value, "deploy/.env"
    return None, "no server URL: give --server, MIA_SMOKE_DATABASE_URL or MIA_DATABASE_URL (deploy/up.sh db writes it to deploy/.env)"


def with_database(url, name):
    """The same server URL with the database `name` (path of the URL)."""
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, "/" + name, parts.query, parts.fragment))


def fixture(name):
    with open(os.path.join(FIXTURES, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def three_versions(graph, step_id, field, tag):
    """The graph under a throw-away ID, then its description changed, then one step's `field` changed: three versions as the caller sees them."""
    first = copy.deepcopy(graph)
    first["id"] = "smoke-%s-%s" % (tag, uuid.uuid4().hex[:8])
    second = copy.deepcopy(first)
    second["description"] = first["description"] + " (smoke change 1)"
    third = copy.deepcopy(second)
    step = next(n for n in third["nodes"] if n["id"] == step_id)
    step["data"][field] = "smoke change 2"
    return [first, second, third]


def check_graph(store, versions):
    """(ok, detail) for one graph on one store: saved three times by three accounts, three versions listed, each read back as saved."""
    import graph_model
    gid = versions[0]["id"]
    for n, (graph, account) in enumerate(zip(versions, ACCOUNTS), start=1):
        result = graph_model.GraphModel(store, author=account).save_graph(graph)
        if not result.saved or result.version != n:
            return False, "save %d: %s" % (n, (result,))
    model = graph_model.GraphModel(store)
    listed = model.graph_versions(gid)
    if [v["version"] for v in listed] != [1, 2, 3] or [v["author"] for v in listed] != list(ACCOUNTS):
        return False, "versions listed: %s" % [(v.get("version"), v.get("author")) for v in listed]
    times = [v.get("time") for v in listed]
    if not all(times) or times != sorted(times):
        return False, "times missing or decreasing: %s" % times
    for n, graph in enumerate(versions, start=1):
        read = model.read_graph(gid, n)
        if read != graph:
            return False, "version %d reads back differently" % n
    return True, "%s: 3 versions by %s, each read as saved" % (gid, ", ".join(ACCOUNTS))


def check_store(kind, store):
    results = []
    cases = (("workflow", three_versions(fixture("sample.code"), "var.in", "value", "wf")),
             ("context", three_versions(fixture("context.cp13"), "claim", "text", "ctx")))
    for name, versions in cases:
        try:
            ok, detail = check_graph(store, versions)
        except Exception as err:            # a part that raises is red with its reason, the other parts still run
            ok, detail = False, "%s: %s" % (type(err).__name__, str(err)[:120])
        results.append(("%s %s" % (kind, name), ok, detail))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--server", help="URL of the owner's running PostgreSQL server (its database part is replaced by mia_smoke)")
    parser.add_argument("--database", default=TARGET, help="the target database; anything but mia_smoke is refused")
    args = parser.parse_args(argv)
    if args.database != TARGET:
        print("cannot run: the target database must be exactly %s, not %r (TR-CORE-009)" % (TARGET, args.database))
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
    import storage
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
    root = tempfile.mkdtemp(prefix="mia-smoke-")
    backend = None
    try:
        results += check_store("files", storage.Storage(FileBackend(root)))
        try:
            backend = PostgresBackend(with_database(url, TARGET))
        except Exception as err:
            results.append(("postgres", False, "%s: %s" % (type(err).__name__, str(err)[:120])))
        else:
            results += check_store("postgres", storage.Storage(backend))
    finally:
        if backend is not None and hasattr(backend, "close"):
            backend.close()
        shutil.rmtree(root, ignore_errors=True)
        results.append(("files removed", not os.path.exists(root), root))
        try:
            with psycopg.connect(admin, autocommit=True, connect_timeout=5) as conn:
                conn.execute("DROP DATABASE IF EXISTS " + TARGET + " WITH (FORCE)")
                gone = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TARGET,)).fetchone() is None
            results.append(("%s dropped" % TARGET, gone, "by name on %s" % source))
        except psycopg.Error as err:
            results.append(("%s dropped" % TARGET, False, str(err).strip()[:160]))

    for name, ok, detail in results:
        print("%-18s %s  %s" % (name, "ok" if ok else "FAILED", detail))
    failed = sum(not ok for _, ok, _ in results)
    print("SMOKE-CORE-001:", "green" if not failed else "red (%d of %d parts failed)" % (failed, len(results)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
