"""
Smoke test of the compose stack on the owner's workstation (specs/mia/test-spec.md: SMOKE-MIA-003; node N-4.2: TC-OPR-007, REQ-OPR-007; A-37, A-46, D-127, D-133).

Part 1, each container alone against the mocks of its neighbours:
  mia    the Python contract suites of tests/acceptance/contract inside the mia image (the mocks of tests/helpers run in the same image)
  db     postgres:16 alone (tests/test_storage_postgres.py starts it, on loopback, and runs the storage suite against it)
  graph  the graph container alone: every file it serves equals graph_app/, and the JavaScript contract suite of IF-104 passes on the host (node) (D-133)
Part 2, all together: deploy/compose.yaml with the db profile under its own project name, one configuration file; every service runs, the https front
answers on / (mia) and on /graph/ (graph), the database is ready. The model server is the one that runs on the host already (OLLAMA_URL, as deploy/README.md
describes; MIA_SMOKE_OLLAMA changes it): the stack's own ollama profile is not started, since MIA would pull its models into an empty one.

Builds its own image tag (localhost/mia:smoke) and project (mia-smoke), publishes only on 127.0.0.1, removes what it started. Protected: change only through a
plan amendment. Run on the workstation with the MIA virtualenv (psycopg of requirements-db.txt):
  python tests/smoke/smoke_stack.py        (exit 0 = green, 1 = red, 2 = cannot run)
"""
import os
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
IMAGE = "localhost/mia:smoke"
PROJECT = "mia-smoke"
GRAPH_FILES = ("index.html", "app.js", "graph-view.js", "graph.css")
SERVICES = ("mia", "graph", "https", "db", "searxng")
OLLAMA = os.environ.get("MIA_SMOKE_OLLAMA", "http://host.containers.internal:11434")


def run(*args, timeout=900, env=None):
    return subprocess.run(list(args), cwd=REPO, capture_output=True, text=True, timeout=timeout, env=env)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def fetch(url, tries=180):
    """the body of url (https without certificate check: Caddy's local CA), retried while the stack starts"""
    context = ssl.create_default_context()
    context.check_hostname, context.verify_mode = False, ssl.CERT_NONE
    for _ in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=5, context=context).read()
        except OSError:
            time.sleep(1)
    raise AssertionError("no answer from " + url)


def mia_alone():
    result = run("podman", "run", "--rm", "--init", "--user", "0", "-v", REPO + ":/work:z", "-w", "/work", IMAGE,
                 "python", "-m", "unittest", "discover", "-s", "tests/acceptance/contract", "-p", "test_*.py")
    return result.returncode == 0, result.stderr[-300:]


def db_alone():
    result = run(sys.executable, "tests/test_storage_postgres.py")
    return result.returncode == 0 and "skipped" not in result.stderr, result.stderr[-300:]


def graph_alone():
    name, port = "mia-smoke-graph-%d" % os.getpid(), free_port()
    started = run("podman", "run", "-d", "--rm", "--name", name, "-p", "127.0.0.1:%d:8587" % port, IMAGE,
                  "python", "-m", "http.server", "8587", "--directory", "/opt/mia/MIA/graph_app")
    if started.returncode != 0:
        return False, started.stderr[-300:]
    try:
        for path in GRAPH_FILES:
            with open(os.path.join(REPO, "graph_app", path), "rb") as fp:
                if fetch("http://127.0.0.1:%d/%s" % (port, path)) != fp.read():
                    return False, "graph serves another " + path
    finally:
        run("podman", "rm", "-f", name)
    suite = run("node", "--test", "tests/acceptance/contract/test_if_104_graph_api.test.mjs")
    return suite.returncode == 0, suite.stdout[-300:]


def all_together():
    https_port = free_port()
    env = dict(os.environ, MIA_IMAGE=IMAGE, MIA_PORT=str(free_port()), MIA_HTTPS_PORT=str(https_port), MIA_BIND="127.0.0.1",
               POSTGRES_PASSWORD=secrets.token_hex(12), SEARXNG_SECRET=secrets.token_hex(16), OLLAMA_URL=OLLAMA, MIA_DATABASE_URL="")
    compose = ("podman", "compose", "-p", PROJECT, "-f", "deploy/compose.yaml", "--profile", "db")
    local = os.path.join(REPO, "deploy", "setup_cfg.local.json")
    made_local = not os.path.exists(local)
    if made_local:
        with open(local, "w", encoding="utf-8") as fp:
            fp.write("{}\n")
    try:
        up = run(*compose, "up", "-d", env=env)
        if up.returncode != 0:
            return False, up.stderr[-300:]
        try:
            page = fetch("https://127.0.0.1:%d/" % https_port)
            graph = fetch("https://127.0.0.1:%d/graph/" % https_port)
        except AssertionError as error:
            return False, str(error)
        with open(os.path.join(REPO, "graph_app", "index.html"), "rb") as fp:
            if graph != fp.read() or not page:
                return False, "the https front does not route / and /graph/"
        for _ in range(30):
            if run("podman", "exec", PROJECT + "_db_1", "pg_isready", "-U", "mia", "-d", "mia").returncode == 0:
                break
            time.sleep(1)
        else:
            return False, "the database is not ready"
        running = run("podman", "ps", "--filter", "label=io.podman.compose.project=" + PROJECT, "--format", "{{.Names}}").stdout.split()
        missing = [s for s in SERVICES if not any(n.startswith("%s_%s_" % (PROJECT, s)) for n in running)]
        return not missing, "not running: %s" % missing if missing else "all %d services run" % len(SERVICES)
    finally:
        run(*compose, "down", "-v", env=env)
        if made_local:
            os.remove(local)


def main():
    if not all(shutil.which(tool) for tool in ("podman", "podman-compose", "node")):
        print("cannot run: podman, podman-compose and node are needed")
        return 2
    try:
        urllib.request.urlopen(OLLAMA.replace("host.containers.internal", "127.0.0.1") + "/api/tags", timeout=5)
    except OSError:
        print("cannot run: no model server answers at", OLLAMA)
        return 2
    built = run("podman", "build", "-q", "-t", IMAGE, "-f", "deploy/Containerfile", ".", timeout=1800)
    if built.returncode != 0:
        print("cannot run: the image does not build:", built.stderr[-300:])
        return 2
    failed = 0
    try:
        for part in (mia_alone, db_alone, graph_alone, all_together):
            ok, detail = part()
            failed += not ok
            print("%-12s %s  %s" % (part.__name__, "ok" if ok else "FAILED", " ".join(detail.split())[-160:]))
    finally:
        run("podman", "rmi", "-f", IMAGE)
    print("SMOKE-MIA-003:", "green" if not failed else "red (%d of 4 parts failed)" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
