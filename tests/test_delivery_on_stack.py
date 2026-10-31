"""TC-VPB-005 (REQ-VPB-005, REQ-FE-030): on the compose stack the chat page, its scripts and a voice line come from MIA's own server, and the
frontend has no container of its own.
Stage 3 (D-144): builds its own image tag of this checkout (localhost/mia:vpb005, never pulling, without network), starts deploy/compose.yaml under its own
project (mia-vpb005) on 127.0.0.1 only, with the Ollama that runs on the host (OLLAMA_URL, as tests/smoke/smoke_stack.py; never the stack's
ollama profile), loads the page over the stack's http front in headless Chromium (localhost/mia-browser, D-141, as tests/test_page_requests.py)
and removes what it started (containers, every volume of the project, also the anonymous ones, network, image tag). Skipped, never passed, without podman, podman-compose, an image or the
model server. Run on the host with: python3 tests/test_delivery_on_stack.py  (about a minute)"""
import json
import os
import re
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

PROJECT = "mia-vpb005"                       # its own project and tag: the owner's stack "mia" and the smoke tests are never touched
IMAGE = "localhost/mia:vpb005"
BROWSER_IMAGE = "localhost/mia-browser"
OLLAMA = os.environ.get("MIA_SMOKE_OLLAMA", "http://host.containers.internal:11434")    # the model server on the host, as the smoke tests
SERVICES = {"mia", "graph", "https", "searxng"}                                          # without the profiles ollama and db
DRIVER = os.path.join(HERE, "browser", "page_requests.py")
SOUND = "/static/chat/sound.js"
NO_NETWORK_SCHEMES = ("data", "blob")          # these never leave the browser


def run(*args, timeout=900, env=None, stdin=None, binary=False):
    return subprocess.run(list(args), cwd=ROOT, capture_output=True, text=not binary, timeout=timeout, env=env, stdin=stdin)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def fetch(url, tries=1):
    """the body of url (https without certificate check: Caddy's local CA), retried while the stack starts"""
    context = ssl.create_default_context()
    context.check_hostname, context.verify_mode = False, ssl.CERT_NONE
    for attempt in range(tries):
        try:
            return urllib.request.urlopen(url, timeout=5, context=context).read()
        except OSError:
            if attempt + 1 == tries:
                raise
            time.sleep(2)


def outside(urls, host):
    """the urls that would leave the host (host:port) of the page"""
    return [url for url in urls if urlsplit(url).scheme not in NO_NETWORK_SCHEMES and urlsplit(url).netloc != host]


def needed_images():
    """the images the stack runs from registries (https, searxng) and the base of the MIA image, by their pinned digests"""
    with open(os.path.join(ROOT, "deploy", "compose.yaml"), encoding="utf-8") as fp:
        stack = [i for i in re.findall(r"image: (docker\.io/\S+)", fp.read()) if "caddy" in i or "searxng" in i]
    with open(os.path.join(ROOT, "deploy", "Containerfile"), encoding="utf-8") as fp:
        base = re.findall(r"^FROM (\S+)", fp.read(), re.M)
    return stack + base + [BROWSER_IMAGE]


def cannot_run():
    """the reason this machine cannot run the test without pulling anything, or None"""
    if not all(shutil.which(tool) for tool in ("podman", "podman-compose")):
        return "podman and podman-compose are needed"
    absent = [image for image in needed_images() if run("podman", "image", "exists", image).returncode != 0]
    if absent:
        return "images missing (a test never pulls an image): %s" % absent
    try:
        urllib.request.urlopen(OLLAMA.replace("host.containers.internal", "127.0.0.1") + "/api/tags", timeout=5)
    except OSError:
        return "no model server answers at " + OLLAMA
    return None


def volumes_of(project):
    """the volumes of the project: those its containers mount (named and anonymous) and those that carry its label"""
    ids = run("podman", "ps", "-a", "-q", "--filter", "label=io.podman.compose.project=" + project).stdout.split()
    mounted = run("podman", "inspect", "--format", '{{range .Mounts}}{{if eq .Type "volume"}}{{.Name}} {{end}}{{end}}', *ids).stdout.split() if ids else []
    labelled = run("podman", "volume", "ls", "-q", "--filter", "label=io.podman.compose.project=" + project).stdout.split()
    return set(mounted) | set(labelled)


def take_down(compose, env):
    """stops the stack and removes every volume it had; `down -v` keeps the anonymous volumes of the searxng image (VOLUME /etc/searxng
    /var/cache/searxng), so they are recorded before and removed after it. A volume left raises, an error of the class (M1, D-148)."""
    volumes = volumes_of(PROJECT)
    run(*compose, "down", "-v", env=env)
    if volumes:
        run("podman", "volume", "rm", "-f", *sorted(volumes))
    left = sorted(v for v in volumes | volumes_of(PROJECT) if run("podman", "volume", "exists", v).returncode == 0)
    if left:
        raise AssertionError("volumes of %s left after the test: %s" % (PROJECT, left))


class DeliveryOnStack(unittest.TestCase):
    session = None

    @classmethod
    def setUpClass(cls):
        reason = cannot_run()
        if reason:
            raise unittest.SkipTest(reason)
        cls.port, cls.https_port = free_port(), free_port()
        cls.host = "127.0.0.1:%d" % cls.port
        cls.page = "http://%s/?character=0" % cls.host
        empty = tempfile.mkdtemp(prefix="mia-vpb005-")                # the character's web export is not needed (?character=0)
        cls.addClassCleanup(shutil.rmtree, empty, ignore_errors=True)
        env = dict(os.environ, MIA_IMAGE=IMAGE, MIA_PORT=str(cls.port), MIA_HTTPS_PORT=str(cls.https_port), MIA_BIND="127.0.0.1",
                   SEARXNG_SECRET=secrets.token_hex(16), OLLAMA_URL=OLLAMA, MIA_DATABASE_URL="", MIA_CHARACTER_DIR=empty)
        local = os.path.join(ROOT, "deploy", "setup_cfg.local.json")
        if not os.path.exists(local):
            with open(local, "w", encoding="utf-8") as fp:
                fp.write("{}\n")
            cls.addClassCleanup(os.remove, local)
        cls.addClassCleanup(run, "podman", "rmi", "-f", IMAGE)
        # no network in the build (M2, D-148): a layer missing in the cache (pip install after a change of requirements.txt) fails, never downloads
        built = run("podman", "build", "--pull=never", "--network", "none", "-q", "-t", IMAGE, "-f", "deploy/Containerfile", ".", timeout=1800)
        if built.returncode != 0:
            raise AssertionError("the image does not build without network (a layer not in the cache?): " + built.stderr[-300:])
        compose = ("podman-compose", "-p", PROJECT, "-f", "deploy/compose.yaml")
        cls.addClassCleanup(run, "podman", "network", "rm", "-f", PROJECT + "_default")
        cls.addClassCleanup(take_down, compose, env)
        up = run(*compose, "up", "-d", "--no-build", env=env)
        if up.returncode != 0:
            raise AssertionError("the stack does not start: " + up.stderr[-300:])
        fetch("http://%s/" % cls.host, tries=300)                       # MIA answers after it has reached the model server
        cls.served = {path: fetch("http://%s%s" % (cls.host, path)) for path in ("/", SOUND)}
        cls.served_https = fetch("https://127.0.0.1:%d%s" % (cls.https_port, SOUND), tries=30)
        names = run("podman", "ps", "--filter", "label=io.podman.compose.project=" + PROJECT, "--format", "{{.Names}}").stdout.split()
        cls.services = {name[len(PROJECT) + 1:].rsplit("_", 1)[0] for name in names}
        mia = next(name for name in names if name.startswith(PROJECT + "_mia_"))
        cls.in_container = run("podman", "exec", mia, "cat", "/opt/mia/MIA/templates" + SOUND, binary=True).stdout
        with open(DRIVER, "rb") as driver:
            browser = run("podman", "run", "--rm", "-i", "--network", "host", BROWSER_IMAGE, "python", "-", cls.page, stdin=driver, timeout=180, binary=True)
        if browser.returncode != 0:
            raise AssertionError("the browser run failed: " + browser.stderr[-500:].decode("utf-8", "replace"))
        cls.session = json.loads(browser.stdout.decode("utf-8").strip().splitlines()[-1])

    @mark.req("REQ-VPB-005", "REQ-FE-030")
    def test_every_request_of_the_page_goes_to_the_stack(self):
        """TC-VPB-005: in a browser session on the stack (page, scripts, socket, one voice line) no request leaves the stack's own host.

        Example: the page, /static/chat/sound.js, the socket and /audio/line-000001.wav all at 127.0.0.1:PORT -> outside(urls, host) == [].
        """
        # Given: the browser session on the stack's page (setUpClass)
        urls = self.session["urls"]
        # When: the urls that leave the stack's host are picked
        found = outside(urls, self.host)
        # Then: there are none
        self.assertEqual(found, [])

    @mark.req("REQ-VPB-005", "REQ-FE-030")
    def test_the_page_its_scripts_and_a_voice_line_come_from_the_stack(self):
        """TC-VPB-005: the session has the page, the voice player and a voice line, all from the stack, and the line was played to its end.

        Example: urls contain http://127.0.0.1:PORT/?character=0, http://127.0.0.1:PORT/static/chat/sound.js and one /audio/ url; played contains "ended".
        """
        # Given: the session of setUpClass
        urls = self.session["urls"]
        # When: the voice lines are looked up
        lines = [url for url in urls if urlsplit(url).path.startswith("/audio/") and urlsplit(url).netloc == self.host]
        # Then: the page, the voice player and at least one line came from the stack, and a line played to its end
        self.assertIn(self.page, urls)
        self.assertIn("http://" + self.host + SOUND, urls)
        self.assertGreaterEqual(len(lines), 1)
        self.assertIn("ended", self.session["played"])

    @mark.req("REQ-VPB-005", "REQ-FE-030")
    def test_the_scripts_are_the_files_of_the_backend_container(self):
        """TC-VPB-005: the voice player that both fronts of the stack serve is the file inside the mia container (the backend).

        Example: sound.js over http and over https == /opt/mia/MIA/templates/static/chat/sound.js in the mia container.
        """
        # Given: sound.js as the stack served it and as the mia container holds it (setUpClass)
        inside = self.in_container
        # When: the served copies are compared with it
        same = (self.served[SOUND] == inside, self.served_https == inside)
        # Then: both are the backend's file, and the page is there too
        self.assertIn(b"class VoicePlayer", inside)
        self.assertEqual(same, (True, True))
        self.assertIn(b"<title>MIA</title>", self.served["/"])

    @mark.req("REQ-VPB-005", "REQ-FE-030")
    def test_the_frontend_has_no_container_of_its_own(self):
        """TC-VPB-005: the stack runs exactly its services; none of them is a frontend.

        Example: running services of the project == {"mia", "graph", "https", "searxng"}.
        """
        # Given: the services of the project that run (setUpClass)
        running = self.services
        # When: they are compared with the services of the stack
        extra = running - SERVICES
        # Then: every service runs and there is no other one
        self.assertEqual(running, SERVICES)
        self.assertEqual(extra, set())


class CheckItself(unittest.TestCase):
    def test_the_check_finds_an_outside_request(self):
        """TC-VPB-005: the check itself sees a request to another host and ignores data: and blob: urls.

        Example: ["http://127.0.0.1:8585/", "https://cdn.example.org/x.js", "data:,", "blob:http://127.0.0.1:8585/1"] -> ["https://cdn.example.org/x.js"].
        """
        # Given: urls of the page's host, of another host, and two that never leave the browser
        urls = ["http://127.0.0.1:8585/", "https://cdn.example.org/x.js", "data:,", "blob:http://127.0.0.1:8585/1"]
        # When: the outside ones are picked
        found = outside(urls, "127.0.0.1:8585")
        # Then: only the other host is left
        self.assertEqual(found, ["https://cdn.example.org/x.js"])


if __name__ == "__main__":
    unittest.main()
