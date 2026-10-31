"""
N-2.1, TC-API-013 (REQ-API-013, AC-29; D-147, amendment A-52): the mia container starts alone against the mocks of its neighbours and serves the chat page.
Stage 3. A pod published only on 127.0.0.1 holds two containers of the image localhost/mia:latest as it is (never pulled): the HTTP stand-in of the model
server (tests/helpers/mocks/if_103_model_server_http.py, mounted read-only) and MIA with deploy/setup_cfg.compose.json and MIA_OLLAMA_HOST on the stand-in.
The pod is removed afterwards. Skipped, never passed, without podman, the image or the installed stand-in.  Run on the host: python3 tests/test_container_alone.py
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

IMAGE = os.environ.get("MIA_IMAGE", "localhost/mia:latest")
STAND_IN = os.path.join(HERE, "helpers", "mocks", "if_103_model_server_http.py")
CONFIG = os.path.join(REPO, "deploy", "setup_cfg.compose.json")
MODEL_PORT = 11434
OLLAMA_WAIT = 20          # seconds MIA waits for the model server before it gives up (the compose file says 600)
PAGE_WAIT = 180           # seconds until the page must be served


def sh(*args, timeout=120):
    return subprocess.run(list(args), capture_output=True, text=True, timeout=timeout)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def cannot_run():
    """the reason this test cannot run here, or None"""
    if shutil.which("podman") is None:
        return "podman is not available"
    if sh("podman", "image", "exists", IMAGE).returncode != 0:
        return "the image %s does not exist (it is never pulled)" % IMAGE
    if not os.path.exists(STAND_IN):
        return "the stand-in of the model server is not installed (amendment A-52: bash tools/apply_amendment_a52.sh --do)"
    return None


def running(name):
    return sh("podman", "inspect", "-f", "{{.State.Running}}", name).stdout.strip() == "true"


def wait_for_page(url, container, seconds=PAGE_WAIT):
    """the body of url as soon as it answers; fails when the container stops first or the time is up"""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        try:
            return urllib.request.urlopen(url, timeout=3).read().decode("utf-8")
        except OSError:
            if not running(container):
                raise AssertionError("the mia container stopped before the page was served")
            time.sleep(1)
    raise AssertionError("the page was not served within %d s" % seconds)


class ContainerAlone(unittest.TestCase):
    """the mia image alone, its model server the HTTP stand-in of IF-103"""

    @classmethod
    def setUpClass(cls):
        reason = cannot_run()
        if reason:
            raise unittest.SkipTest(reason)
        folder = tempfile.mkdtemp()
        cls.addClassCleanup(shutil.rmtree, folder, True)
        with open(CONFIG, encoding="utf-8") as fp:
            cfg = json.load(fp)
        cfg["ollama_wait"] = OLLAMA_WAIT
        config = os.path.join(folder, "setup_cfg.json")
        with open(config, "w", encoding="utf-8") as fp:
            json.dump(cfg, fp)
        cls.pod = "mia-alone-test-%d" % os.getpid()
        cls.model, cls.mia = cls.pod + "-model", cls.pod + "-mia"
        port = free_port()
        cls.addClassCleanup(sh, "podman", "pod", "rm", "-f", "-t", "2", cls.pod)
        made = sh("podman", "pod", "create", "--name", cls.pod, "-p", "127.0.0.1:%d:8585" % port)
        if made.returncode != 0:
            raise AssertionError("the pod does not start: " + made.stderr[-300:])
        sh("podman", "run", "-d", "--rm", "--init", "--pod", cls.pod, "--name", cls.model, "-v", STAND_IN + ":/stand_in.py:ro,z",
           IMAGE, "python", "/stand_in.py", "--host", "127.0.0.1", "--port", str(MODEL_PORT))
        sh("podman", "run", "-d", "--rm", "--init", "--pod", cls.pod, "--name", cls.mia, "-e", "MIA_OLLAMA_HOST=http://127.0.0.1:%d" % MODEL_PORT,
           "-v", config + ":/opt/mia/MIA/setup_cfg.json:ro,z", IMAGE)
        cls.page = wait_for_page("http://127.0.0.1:%d/" % port, cls.mia)

    def calls_of_the_stand_in(self):
        """the requests the stand-in has seen, [{"method", "path", "model"}]"""
        out = sh("podman", "exec", self.model, "python", "-c",
                 "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:%d/_calls').read().decode())" % MODEL_PORT)
        return json.loads(out.stdout)

    @mark.req("REQ-API-013")
    def test_the_container_alone_serves_the_chat_page(self):
        """TC-API-013: the page that the container serves on / is the chat page.

        Example: GET / -> 200 with the title MIA, the message list and the composer.
        """
        # Given: the mia container started alone, its model server the stand-in
        page = self.page
        # When: the chat page's parts are looked up
        parts = [part for part in ("<title>MIA</title>", 'id="messages"', 'id="composer"') if part in page]
        # Then: all three are there
        self.assertEqual(parts, ["<title>MIA</title>", 'id="messages"', 'id="composer"'])

    @mark.req("REQ-API-013")
    def test_the_start_went_through_the_stand_in(self):
        """TC-API-013: MIA's start talked to the stand-in (the model list, then the calibration chat), so no other model server was used.

        Example: calls [GET /api/tags, POST /api/chat] -> both paths are there.
        """
        # Given: the stand-in after the start of MIA
        calls = self.calls_of_the_stand_in()
        # When: the paths are collected
        paths = {call["path"] for call in calls}
        # Then: the model list and a chat were asked for
        self.assertIn("/api/tags", paths)
        self.assertIn("/api/chat", paths)


if __name__ == "__main__":
    unittest.main()
