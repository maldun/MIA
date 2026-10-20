"""
SearXNG for MIA's web search (tools/searxng/run.sh creates the container `mia-searxng`): is it running, and, if the user wants it (`"searxng_autostart": true` in setup_cfg.json), start the container that run.sh
made. Nothing is created or removed here; only an existing container is started. Without autostart MIA says what to do. The search itself needs none of this: the search tool falls back to the next backend when
SearXNG does not answer (and says so); this module is for finding out *why* SearXNG is not used.
"""
import shutil
import subprocess
import time

try:
    from . import web_tools
except ImportError:  # used as plain script / in tests
    import web_tools

CONTAINER = "mia-searxng"
START_HELP = "tools/searxng/run.sh start (or: podman start %s)" % CONTAINER


def wanted(cfg):
    return "searxng" in cfg.get("search_backends", ["searxng", "duckduckgo"])


def probe(cfg, get=None, timeout=2.0):
    """{"url", "reachable", "detail"}: does anything answer HTTP at the address of SearXNG"""
    import requests
    url = web_tools.searxng_url(cfg)
    try:
        response = (get or requests.get)(url + "/healthz", timeout=timeout)
        return {"url": url, "reachable": True, "detail": "answered with HTTP %s" % getattr(response, "status_code", "?")}
    except Exception as exc:
        return {"url": url, "reachable": False, "detail": "%s: %s" % (type(exc).__name__, str(exc)[:160])}


def start_container(run=None, which=None, timeout=30):
    """(ok, detail): `podman start mia-searxng` (or docker); a container that does not exist is not created"""
    engine = (which or shutil.which)("podman") or (which or shutil.which)("docker")
    if not engine:
        return False, "neither podman nor docker is installed"
    try:
        done = (run or subprocess.run)([engine, "start", CONTAINER], capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        return False, "%s: %s" % (type(exc).__name__, exc)
    if done.returncode != 0:
        return False, (done.stderr or done.stdout or "exit code %s" % done.returncode).strip()[:200]
    return True, "started %s" % CONTAINER


def ensure_searxng(cfg, get=None, run=None, which=None, sleep=time.sleep, waits=10):
    """{"wanted", "reachable", "started", "message"}: probe; if SearXNG is not running and `searxng_autostart` is set, start the container and wait (up to `waits` seconds) until it answers"""
    if not wanted(cfg):
        return {"wanted": False, "reachable": None, "started": False, "message": "SearXNG is not among the search backends"}
    state = probe(cfg, get)
    if state["reachable"]:
        return {"wanted": True, "reachable": True, "started": False, "message": "SearXNG answers at %s" % state["url"]}
    if not cfg.get("searxng_autostart", False):
        return {"wanted": True, "reachable": False, "started": False,
                "message": "SearXNG does not answer at %s (%s): searches use the next backend. Start it with %s, or set \"searxng_autostart\": true in setup_cfg.json" % (state["url"], state["detail"], START_HELP)}
    ok, detail = start_container(run, which)
    if not ok:
        return {"wanted": True, "reachable": False, "started": False, "message": "SearXNG does not answer at %s and could not be started (%s). Create it with tools/searxng/run.sh start" % (state["url"], detail)}
    for _ in range(max(1, waits)):
        sleep(1)
        state = probe(cfg, get)
        if state["reachable"]:
            return {"wanted": True, "reachable": True, "started": True, "message": "SearXNG was not running; the container %s was started and answers at %s" % (CONTAINER, state["url"])}
    return {"wanted": True, "reachable": False, "started": True, "message": "the container %s was started but SearXNG does not answer at %s yet" % (CONTAINER, state["url"])}
