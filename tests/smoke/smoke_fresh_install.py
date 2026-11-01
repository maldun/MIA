"""
Smoke test of a fresh installation on the owner's workstation (specs/mia/test-spec.md: SMOKE-MIA-001; node N-4.2: TC-OPR-001, REQ-OPR-001, REQ-OPR-002; A-47, D-136).

A fresh checkout (git clone of the committed HEAD into a temporary folder), one configuration file (deploy/.env, as deploy/README.md describes it: the address of the
Ollama that runs already, and for this test its own project name, ports and image tag), one command:  deploy/up.sh db  (without a terminal). Then:
  - the command succeeds, the page answers, and the offer of the first account is printed once (REQ-OPR-002),
  - every container of the stack runs (mia, graph, https, db, searxng) and the database is ready,
  - the first account can be created (accounts_cli.py in the mia container, the password on stdin),
  - a chat message is answered (a socket client inside the mia container: chat_send, then chat_delta with text and chat_done).
The model server is the one on the host (OLLAMA_URL, MIA_SMOKE_OLLAMA changes it); the test never pulls a model or an image: it stops (exit 2) when a model of
deploy/setup_cfg.compose.json or an image of the stack is missing (D-136). Publishes only on 127.0.0.1; removes its containers, volumes, image tag and checkout.
Protected: change only through a plan amendment. Run on the workstation:
  python tests/smoke/smoke_fresh_install.py        (exit 0 = green, 1 = red, 2 = cannot run)
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
IMAGE = "localhost/mia:fresh"
PROJECT = "mia-fresh"
SERVICES = ("mia", "graph", "https", "db", "searxng")
IMAGES = ("docker.io/library/caddy:2", "docker.io/library/postgres:16", "docker.io/searxng/searxng:latest", "docker.io/library/python:3.12-slim")
OLLAMA = os.environ.get("MIA_SMOKE_OLLAMA", "http://host.containers.internal:11434")
OFFER = "deploy/up.sh owner NAME"
CHAT = r'''
import socketio, sys, time
got = {"text": "", "done": False, "error": None}
client = socketio.Client()
client.on("chat_delta", lambda data: got.update(text=data.get("text", "")))
client.on("chat_done", lambda *_: got.update(done=True))
client.on("chat_error", lambda data: got.update(error=data))
client.connect("http://127.0.0.1:8585", transports=["polling"], wait_timeout=20)
ack = client.call("chat_send", {"id": "smoke-fresh-1", "text": "Say hello in one short sentence."}, timeout=20)
deadline = time.time() + 600
while not (got["done"] or got["error"]) and time.time() < deadline:
    time.sleep(0.5)
client.disconnect()
print("ack=%s done=%s error=%s text=%r" % (ack, got["done"], got["error"], got["text"][:60]))
sys.exit(0 if got["done"] and got["text"].strip() and not got["error"] else 1)
'''


def run(*args, cwd=REPO, timeout=900, text_in=None, env=None):
    """stdin is text_in, or nothing (no terminal)"""
    return subprocess.run(list(args), cwd=cwd, input=text_in if text_in is not None else "", capture_output=True, text=True, timeout=timeout, env=env)


def page_ready(port, seconds=900):
    """MIA's page answers on loopback (it starts after MIA has reached the model server)"""
    for _ in range(seconds // 2):
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/" % port, timeout=2)
            return True
        except OSError:
            time.sleep(2)
    return False


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def cannot_run():
    """the reason this machine cannot run the test without pulling anything, or None"""
    if not all(shutil.which(tool) for tool in ("podman", "podman-compose", "git")):
        return "podman, podman-compose and git are needed"
    try:
        tags = json.load(urllib.request.urlopen(OLLAMA.replace("host.containers.internal", "127.0.0.1") + "/api/tags", timeout=5))
    except OSError:
        return "no model server answers at " + OLLAMA
    with open(os.path.join(REPO, "deploy", "setup_cfg.compose.json"), encoding="utf-8") as fp:
        cfg = json.load(fp)
    held = {m["name"] for m in tags.get("models", [])}
    missing = [m for m in (cfg["version"], cfg["version_light"]) if m not in held]
    if missing:
        return "the model server lacks %s (a test never pulls a model)" % missing
    absent = [image for image in IMAGES if run("podman", "image", "exists", image).returncode != 0]
    return "images missing (a test never pulls an image): %s" % absent if absent else None


def container(service):
    names = run("podman", "ps", "--filter", "label=io.podman.compose.project=" + PROJECT, "--format", "{{.Names}}").stdout.split()
    return next((n for n in names if n.startswith("%s_%s_" % (PROJECT, service))), None)


def check_stack(started, port):
    """the parts of SMOKE-MIA-001 after the one command; a list of (name, ok, detail)"""
    out = started.stdout + started.stderr
    results = [("one command", started.returncode == 0, " ".join(out.split())[-160:]),
               ("page", started.returncode == 0 and page_ready(port), "http://127.0.0.1:%d/" % port),
               ("offer once", out.count(OFFER) == 1, "offer lines: %d" % out.count(OFFER))]
    missing = [s for s in SERVICES if container(s) is None]
    results.append(("all containers", not missing, "not running: %s" % missing if missing else "%d services" % len(SERVICES)))
    db = container("db")
    ready = False
    for _ in range(30 if db else 0):
        if run("podman", "exec", db, "pg_isready", "-U", "mia", "-d", "mia").returncode == 0:
            ready = True
            break
        time.sleep(1)
    results.append(("database", ready, db or "no db container"))
    mia = container("mia")
    if mia is None:
        return results + [("first account", False, "no mia container"), ("chat", False, "no mia container")]
    made = run("podman", "exec", "-i", mia, "python", "/opt/mia/MIA/tools/accounts_cli.py", "create", "smoke", "--dir", "/opt/mia/MIA/data/db",
               text_in="pw-smoke-12345\npw-smoke-12345\n", timeout=60)
    results.append(("first account", "created: smoke" in made.stdout, (made.stdout + made.stderr)[-160:]))
    chat = run("podman", "exec", "-i", mia, "python", "-", text_in=CHAT, timeout=700)
    results.append(("chat", chat.returncode == 0, (chat.stdout + chat.stderr)[-160:]))
    return results


def main():
    reason = cannot_run()
    if reason:
        print("cannot run:", reason)
        return 2
    tmp = tempfile.mkdtemp(prefix="mia-fresh-")
    checkout = os.path.join(tmp, "MIA")
    cloned = run("git", "clone", "--quiet", REPO, checkout)
    if cloned.returncode != 0:
        print("cannot run: git clone failed:", cloned.stderr[-200:])
        shutil.rmtree(tmp, ignore_errors=True)
        return 2
    port = free_port()
    with open(os.path.join(checkout, "deploy", ".env"), "w", encoding="utf-8") as fp:
        fp.write("OLLAMA_URL=%s\nMIA_PROJECT=%s\nMIA_IMAGE=%s\nMIA_PORT=%d\nMIA_HTTPS_PORT=%d\nMIA_BIND=127.0.0.1\n"
                 % (OLLAMA, PROJECT, IMAGE, port, free_port()))
    up = os.path.join(checkout, "deploy", "up.sh")
    # the project name also in the environment: whatever up.sh reads, this test never touches the owner's stack "mia"
    env = {k: v for k, v in os.environ.items() if k not in ("OLLAMA_URL", "MIA_IMAGE", "MIA_PORT", "MIA_HTTPS_PORT", "MIA_BIND", "COMPOSE")}
    env["MIA_PROJECT"] = PROJECT
    try:
        results = check_stack(run("bash", up, "db", cwd=checkout, timeout=2400, env=env), port)
    finally:
        run("bash", up, "db", "down", "-v", cwd=checkout, env=env)
        run("podman", "rmi", "-f", IMAGE)
        shutil.rmtree(tmp, ignore_errors=True)
    for name, ok, detail in results:
        print("%-15s %s  %s" % (name, "ok" if ok else "FAILED", detail))
    failed = sum(not ok for _, ok, _ in results)
    print("SMOKE-MIA-001:", "green" if not failed else "red (%d of %d parts failed)" % (failed, len(results)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
