"""The stage-2 browser check of speak again right after a stop (N-1.3, REQ-VPB-006, A-132 TD-11): TC-VPB-007, driver tests/browser/speak_again.py.
The real page on the IF-101 mock server (ui/tools/chat_mock_server.py, which since D-278 sends audio_reload {url, serial, message} after the speaker button and
serves a short wav, TR-VOICE-005) in its own container of the MIA image with `--network none`, and headless Chromium of localhost/mia-browser in that container's
network, as in tests/test_chat_views_browser.py (D-141). Container names are unique per run and removed afterwards. Skipped, never passed, where podman or one of
the images is missing.  Run on the host with: python3 tests/test_speak_again_browser.py"""
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

BROWSER_IMAGE = "localhost/mia-browser"
MIA_IMAGE = "localhost/mia:latest"
DRIVER = os.path.join(HERE, "browser", "speak_again.py")
BASE = "http://127.0.0.1:8686"


def image_exists(name):
    return subprocess.run(["podman", "image", "exists", name]).returncode == 0


def start_mock():
    """the mock server in a container of its own, without network; returns its name once the page answers"""
    name = "n13-speak-%s" % uuid.uuid4().hex[:8]
    subprocess.run(["podman", "run", "-d", "--name", name, "--user", "0:0", "--network", "none", "-e", "ANSWER_DELAY=1", "-e", "EVENT_GAP=0.05", "-e", "MOCK_VOICE=1",
                    "-v", "%s:/opt/mia/MIA:O" % ROOT, MIA_IMAGE, "python", "MIA/ui/tools/chat_mock_server.py"], check=True, capture_output=True)
    probe = "import urllib.request; urllib.request.urlopen('%s/')" % BASE
    for _ in range(60):
        if subprocess.run(["podman", "exec", name, "python", "-c", probe], capture_output=True).returncode == 0:
            return name
        time.sleep(0.5)
    logs = subprocess.run(["podman", "logs", name], capture_output=True, text=True).stdout[-500:]
    stop_mock(name)
    raise AssertionError("the mock server did not answer in 30 s: " + logs)


def stop_mock(name):
    subprocess.run(["podman", "rm", "-f", "-t", "0", name], capture_output=True)


def browse(container, *scenarios):
    """one run of the driver in the network of `container`; returns its JSON {scenario: result}"""
    with open(DRIVER, encoding="utf-8") as driver:
        run = subprocess.run(["podman", "run", "--rm", "-i", "--network", "container:" + container, BROWSER_IMAGE, "python", "-", BASE, *scenarios],
                             stdin=driver, capture_output=True, text=True, timeout=300)
    if run.returncode != 0:
        raise AssertionError("the browser run failed: " + run.stderr[-800:])
    return json.loads(run.stdout.strip().splitlines()[-1])


class SpeakAgainInBrowser(unittest.TestCase):
    results = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        container = start_mock()
        cls.addClassCleanup(stop_mock, container)
        cls.results = browse(container, "stop_then_button", "stop_then_late_line")

    @mark.req("REQ-VPB-006")
    def test_the_line_after_the_speaker_button_is_played_1_s_after_a_stop(self):
        """TC-VPB-007 (REQ-VPB-006): with a stop 1 s ago the line that follows the speaker button is loaded into the page's audio element.
        Example: Stop, 1 s later the speaker button; the mock sends audio_reload with url /mock/audio/line-000001.wav; the audio element is asked to play that url."""
        # Given the real page on the mock, an answer shown, the voice stopped
        # When the user presses Stop and, 1 s later, the speaker button (the mock answers with an audio_reload)
        result = self.results["stop_then_button"]
        played = result["played"]
        # Then the audio element of the page got the url of the line (the line did reach the page: the fault is its drop, not a missing event)
        self.assertEqual(result["reloads"], 1)
        self.assertEqual(len(played), 1, played)
        self.assertRegex(played[0], r"/mock/audio/line-\d{6}\.wav$")

    @mark.req("REQ-VPB-006")
    def test_a_line_without_the_button_is_still_dropped_1_s_after_a_stop(self):
        """TC-VPB-007 (REQ-VPB-006): without the button the late line of the stopped answer is still dropped, as before (REQ-VPB-002).
        Example: Stop, 1 s later an audio_reload without any button; the audio element is asked to play nothing."""
        # Given the real page on the mock, an answer shown, the voice stopped
        # When the user presses Stop and, 1 s later, an audio_reload arrives without the button
        result = self.results["stop_then_late_line"]
        # Then the line reached the page and the audio element was not asked to play it
        self.assertEqual(result["reloads"], 1)
        self.assertEqual(result["played"], [])


if __name__ == "__main__":
    unittest.main()
