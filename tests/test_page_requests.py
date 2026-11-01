"""TC-VPB-004 (REQ-VPB-004, REQ-FE-026): a real browser loads the chat page, plays one voice line and every request of the session goes to the page's own host.
Stage 3 (D-141): the chat page from the stub server in the MIA image (tools/start_testing.sh, stage chat-on-stub, as tests/test_frontend_delivery.py),
headless Chromium in the image localhost/mia-browser (tests/browser/Containerfile) on loopback; the requests come from Chromium's performance log.
Skipped, never passed, where podman, one of the images or the stage is missing, or where the stage runs already (N5).
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


def own_stage(output):
    """True when the output of `start_testing.sh start chat-on-stub` says this run started the stage. A stage that runs already is never
    used (N5): its container name is shared by every checkout and a running stage keeps its old code, so the test would check another one"""
    if "running already" in output:
        raise unittest.SkipTest("the stage chat-on-stub runs already (another checkout or older code); stop it first: "
                                "bash tools/start_testing.sh stop chat-on-stub")
    if "started" in output:
        return True
    raise unittest.SkipTest("the stage does not start: " + output[-200:])


def browse(*args):
    """one session of the headless browser on the page (tests/browser/page_requests.py); returns its JSON {played, urls, console}"""
    with open(DRIVER, encoding="utf-8") as driver:
        run = subprocess.run(["podman", "run", "--rm", "-i", "--network", "host", BROWSER_IMAGE, "python", "-", PAGE, *args],
                             stdin=driver, capture_output=True, text=True, timeout=120)
    if run.returncode != 0:
        raise AssertionError("the browser run failed: " + run.stderr[-500:])
    return json.loads(run.stdout.strip().splitlines()[-1])


class StageUse(unittest.TestCase):
    def test_a_stage_that_runs_already_is_not_used(self):
        """N5: a stage that runs already may be another checkout's or carry older code, so the test skips (never passes) on it.

        Example: own_stage("mia-test-chat-on-stub is running already") -> SkipTest; own_stage("mia-test-chat-on-stub started (port 8685 ...)") -> True.
        """
        # Given: the outputs of a start that found the stage running and of a start that started it
        running = "== chat-on-stub\nmia-test-chat-on-stub is running already\n"
        started = "== chat-on-stub\nmia-test-chat-on-stub started (port 8685, logs: podman logs mia-test-chat-on-stub)\n"
        # When / Then: the running one is not used, the started one is
        with self.assertRaises(unittest.SkipTest):
            own_stage(running)
        self.assertTrue(own_stage(started))


class PageRequests(unittest.TestCase):
    session = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        if own_stage(stage("start").stdout):
            cls.addClassCleanup(stage, "stop")                    # only a stage this test started is stopped again
        cls.session = browse()
        cls.broken = browse("broken")                             # owner check A4 (D-154): a broken line, then a good one

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

    @mark.req("REQ-VPB-003", "REQ-VPB-001")
    def test_a_broken_line_gives_one_console_warning_and_the_next_line_plays(self):
        """TC-VPB-003 in a real browser (owner check A4, D-154): a text file uploaded as broken.wav is skipped with exactly one console
        warning that names its line, and the good line uploaded after it plays to its end.

        Example: played == ["error", "playing", "ended"]; console has one "MIA voice: line skipped, it could not be played: /audio/line-000007.wav".
        """
        # Given: a session in which a broken line and then a good line were uploaded (setUpClass)
        lines = [url for url in self.broken["urls"] if urlsplit(url).path.startswith("/audio/")]
        # When: the warnings of the voice are picked from the console
        warnings = [message for message in self.broken["console"] if "MIA voice: line skipped" in message]
        # Then: one warning for the first line, and the second line played to its end
        self.assertEqual(len(lines), 2)
        self.assertEqual(len(warnings), 1, self.broken["console"])
        self.assertIn(urlsplit(lines[0]).path, warnings[0])
        self.assertEqual(self.broken["played"], ["error", "playing", "ended"])

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
