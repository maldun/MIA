"""TC-VPB-004 (REQ-VPB-004, REQ-FE-026): a real browser loads the chat page, plays one voice line and every request of the session goes to the page's own host.
Stage 3 (D-141): the chat page from the stub server in the MIA image (tools/start_testing.sh, stage chat-on-stub, as tests/test_frontend_delivery.py),
headless Chromium in the image localhost/mia-browser (tests/browser/Containerfile) on loopback; the requests come from Chromium's performance log.
Skipped, never passed, where podman, one of the images or the stage is missing.
Run on the host with: python3 tests/test_page_requests.py"""
import json
import os
import shutil
import subprocess
import sys
import unittest
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

PAGE = "http://127.0.0.1:8685/?character=0"
OWN_HOST = "127.0.0.1:8685"
BROWSER_IMAGE = "localhost/mia-browser"
MIA_IMAGE = "localhost/mia:latest"
DRIVER = os.path.join(HERE, "browser", "page_requests.py")
NO_NETWORK_SCHEMES = ("data", "blob")          # these never leave the browser


def image_exists(name):
    return subprocess.run(["podman", "image", "exists", name]).returncode == 0


def stage(command):
    return subprocess.run(["bash", os.path.join(ROOT, "tools", "start_testing.sh"), command, "chat-on-stub"], capture_output=True, text=True)


def outside(urls):
    """the urls that would leave the page's host"""
    return [url for url in urls if urlsplit(url).scheme not in NO_NETWORK_SCHEMES and urlsplit(url).netloc != OWN_HOST]


class PageRequests(unittest.TestCase):
    session = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        start = stage("start")
        if "started" in start.stdout:
            cls.addClassCleanup(stage, "stop")                    # only a stage this test started is stopped again
        elif "running already" not in start.stdout:
            raise unittest.SkipTest("the stage does not start: " + start.stdout[-200:])
        with open(DRIVER, encoding="utf-8") as driver:
            run = subprocess.run(["podman", "run", "--rm", "-i", "--network", "host", BROWSER_IMAGE, "python", "-", PAGE],
                                 stdin=driver, capture_output=True, text=True, timeout=120)
        if run.returncode != 0:
            raise AssertionError("the browser run failed: " + run.stderr[-500:])
        cls.session = json.loads(run.stdout.strip().splitlines()[-1])

    @mark.req("REQ-VPB-004", "REQ-FE-026")
    def test_every_request_of_a_session_goes_to_the_page_host(self):
        """TC-VPB-004: no request of a session with the chat page and one voice line leaves the page's host.

        Example: the page, its scripts, the socket and /audio/line-000001.wav all at 127.0.0.1:8685 -> outside(urls) == [].
        """
        # Given: a session of the browser on the chat page with one voice line (setUpClass)
        urls = self.session["urls"]
        # When: the urls that leave the page's host are picked
        found = outside(urls)
        # Then: there are none
        self.assertEqual(found, [])

    @mark.req("REQ-VPB-004")
    def test_the_session_covers_the_page_the_voice_player_and_a_line(self):
        """TC-VPB-004: the recorded session is not empty: it has the page, sound.js and the voice line, and the line was played.

        Example: urls contain PAGE and http://127.0.0.1:8685/static/chat/sound.js and one /audio/ url; played contains "ended".
        """
        # Given: the session of setUpClass
        urls = self.session["urls"]
        # When: the requests of the page and the voice are looked up
        lines = [url for url in urls if urlsplit(url).path.startswith("/audio/")]
        # Then: all of them are there and the line played to its end
        self.assertIn(PAGE, urls)
        self.assertIn("http://127.0.0.1:8685/static/chat/sound.js", urls)
        self.assertEqual(len(lines), 1)
        self.assertIn("ended", self.session["played"])

    @mark.req("REQ-VPB-004")
    def test_the_page_reports_no_blocked_request(self):
        """TC-VPB-004: the browser console shows no violation of the page's Content Security Policy.

        Example: console messages without "Content Security Policy" -> [].
        """
        # Given: the console messages of the session
        console = self.session["console"]
        # When: the messages about the Content Security Policy are picked
        blocked = [message for message in console if "Content Security Policy" in message]
        # Then: there are none
        self.assertEqual(blocked, [])

    def test_the_check_finds_an_outside_request(self):
        """TC-VPB-004: the check itself sees a request to another host and ignores data: and blob: urls.

        Example: ["http://127.0.0.1:8685/", "https://cdn.example.org/x.js", "data:,", "blob:http://127.0.0.1:8685/1"] -> ["https://cdn.example.org/x.js"].
        """
        # Given: urls of the own host, of another host, and two that never leave the browser
        urls = ["http://127.0.0.1:8685/", "https://cdn.example.org/x.js", "data:,", "blob:http://127.0.0.1:8685/1"]
        # When: the outside ones are picked
        found = outside(urls)
        # Then: only the other host is left
        self.assertEqual(found, ["https://cdn.example.org/x.js"])

if __name__ == "__main__":
    unittest.main()
