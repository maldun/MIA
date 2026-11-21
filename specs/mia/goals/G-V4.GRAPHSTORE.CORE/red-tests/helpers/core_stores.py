"""Stores for the checks of G-V4.GRAPHSTORE.CORE (test requirements TR-CORE-001, -002, -003, -004, -007).

- fresh_backend(kind): a backend no other check has written to (TR-CORE-007): a new folder for `files`, a new database in one throw-away
  postgres:16 container per test process for `postgres` (TR-CORE-003). The image is never pulled; where podman, the image or psycopg 3 is
  missing the check is skipped with the reason (unittest.SkipTest), never passed.
- FailingBackend(backend, fail_at): counts the writes (`append`) and raises Interrupted instead of the write number `fail_at` (TR-CORE-001);
  `writes` is the number of writes done, so a check can show that the injector fired (TR-CORE-002). fail_at=None counts only.
- fixture_graph(name): a graph of tests/fixtures/graphs/ as the caller of the Workflow management sees it (TR-CORE-004).
Call stop_database() in tearDownModule."""
import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
FIXTURES = os.path.join(REPO, "tests", "fixtures", "graphs")
CONVERTED = ("behaviour.speech@1", "chat@1", "extract.llm@1", "extract.rules@1", "memory.write@5", "plan.free@1", "research.escalate@1",
             "review.abstract@1", "review.full@2", "review.keywords@2", "review.section@1", "review.summary@1", "summarize@1",
             "verify.computable@2", "verify.single@1")
KINDS = ("files", "postgres")
IMAGE = "docker.io/library/postgres:16"
CONTAINER = "mia-core-test-%d" % os.getpid()
_server = {}          # the URL of the running container, once it is up


class Interrupted(Exception):
    """The injected fault: the store fails at one write (TR-CORE-001)."""


def fixture_graph(name):
    with open(os.path.join(FIXTURES, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def converted_graphs():
    return [fixture_graph(name) for name in CONVERTED]


def _podman(*args):
    return subprocess.run(["podman", *args], capture_output=True, text=True, timeout=120)


def _server_url():
    """postgres:16 started once per process; SkipTest with the reason where it cannot run."""
    if "url" in _server:
        return _server["url"]
    if "skip" in _server:
        raise unittest.SkipTest(_server["skip"])
    try:
        import psycopg                                              # noqa: F401
    except ImportError:
        _server["skip"] = "psycopg 3 is not installed"
    else:
        if shutil.which("podman") is None:
            _server["skip"] = "podman is not available"
        elif _podman("image", "exists", IMAGE).returncode != 0:
            _server["skip"] = "the image %s is not on this host (it is never pulled)" % IMAGE
    if "skip" in _server:
        raise unittest.SkipTest(_server["skip"])
    import psycopg
    import time
    run = _podman("run", "-d", "--rm", "--name", CONTAINER, "-e", "POSTGRES_PASSWORD=test", "--tmpfs", "/var/lib/postgresql/data",
                  "-p", "127.0.0.1::5432", IMAGE)
    if run.returncode != 0:
        _server["skip"] = "the database container does not start: " + run.stderr.strip()[:100]
        raise unittest.SkipTest(_server["skip"])
    port = _podman("port", CONTAINER, "5432").stdout.strip().rsplit(":", 1)[-1]
    url = "postgresql://postgres:test@127.0.0.1:%s/postgres" % port
    for _ in range(60):
        try:
            psycopg.connect(url, connect_timeout=2).close()
            _server["url"] = url
            return url
        except psycopg.OperationalError:
            time.sleep(0.5)
    stop_database()
    _server["skip"] = "the database did not become ready in 30 s"
    raise unittest.SkipTest(_server["skip"])


def stop_database():
    if "url" in _server:
        _podman("rm", "-f", CONTAINER)
        del _server["url"]


def fresh_backend(kind, test=None):
    """A backend nobody has written to (TR-CORE-007). With `test` given, the folder is removed after that test."""
    if kind == "files":
        from storage_files import FileBackend
        root = tempfile.mkdtemp(prefix="core-")
        if test is not None:
            test.addCleanup(shutil.rmtree, root, True)
        return FileBackend(root)
    if kind == "postgres":
        import psycopg
        from storage_postgres import PostgresBackend
        url = _server_url()
        name = "core_" + uuid.uuid4().hex[:12]
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute("CREATE DATABASE " + name)
        backend = PostgresBackend(url.rsplit("/", 1)[0] + "/" + name)
        if test is not None and hasattr(backend, "close"):
            test.addCleanup(backend.close)
        return backend
    raise ValueError(kind)


class FailingBackend:
    """A backend that fails at the write number `fail_at` (1 = the first write) and counts the writes done before (TR-CORE-001, -002).
    Every other call goes to the wrapped backend unchanged."""

    def __init__(self, backend, fail_at=None):
        self.backend = backend
        self.fail_at = fail_at
        self.writes = 0
        self.fired = False

    def append(self, table, record_id, entry):
        if self.fail_at is not None and self.writes + 1 == self.fail_at:
            self.fired = True
            raise Interrupted("injected fault at write %d (%s %s)" % (self.fail_at, table, record_id))
        self.writes += 1
        return self.backend.append(table, record_id, entry)

    def __getattr__(self, name):
        return getattr(self.backend, name)


def version_counts(storage, tables=("graph_nodes", "graph_edges", "context_nodes", "context_edges", "graphs")):
    """{table: {record ID: number of versions}}: what a refused save must leave unchanged."""
    return {t: {i: len(storage.history(t, i)) for i in storage.ids(t)} for t in tables}


def changed(graph, **fields):
    """A deep copy of `graph` with header fields replaced."""
    g = copy.deepcopy(graph)
    g.update(fields)
    return g
