"""The stage-2 browser checks of the chat and login views (N-1.1; D-163 F3, F6): TC-CLV-016 (touch targets, layout), more scenarios below.
The real page on the IF-101 mock server (ui/tools/chat_mock_server.py) in its own container of the MIA image with `--network none`, and headless
Chromium of localhost/mia-browser (tests/browser/Containerfile, D-141) in that container's network: loopback only, nothing else reachable.
The container names are unique per run (never a stage of tools/start_testing.sh), both are removed afterwards. Skipped, never passed, where
podman or one of the images is missing.  Run on the host with: python3 tests/test_chat_views_browser.py"""
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
DRIVER = os.path.join(HERE, "browser", "chat_views.py")
BASE = "http://127.0.0.1:8686"
TOUCH_PX = 44                                  # REQ-CLV-016 AC-1


def image_exists(name):
    return subprocess.run(["podman", "image", "exists", name]).returncode == 0


def start_mock():
    """the mock server in a container of its own, without network; returns its name once the page answers"""
    name = "n11-views-%s" % uuid.uuid4().hex[:8]
    subprocess.run(["podman", "run", "-d", "--name", name, "--user", "0:0", "--network", "none", "-e", "ANSWER_DELAY=1", "-e", "EVENT_GAP=0.05",
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


def too_small(controls, least=TOUCH_PX):
    """the controls narrower or lower than `least` px"""
    return [c for c in controls if c["w"] < least or c["h"] < least]


class TouchTargetRule(unittest.TestCase):
    def test_the_rule_finds_a_narrow_control(self):
        """The check itself: a control of 32 x 44 px is too small, 44 x 44 is not.

        Example: [{"name": "up", "w": 32, "h": 44}, {"name": "send", "w": 44, "h": 44}] -> only "up".
        """
        # Given: one narrow and one big enough control
        controls = [{"name": "up", "w": 32, "h": 44}, {"name": "send", "w": 44, "h": 44}]
        # When: the small ones are picked
        found = too_small(controls)
        # Then: only the narrow one
        self.assertEqual([c["name"] for c in found], ["up"])


class ChatViewsInBrowser(unittest.TestCase):
    results = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        container = start_mock()
        cls.addClassCleanup(stop_mock, container)
        cls.results = browse(container, "touch", "layout")

    @mark.req("REQ-CLV-016")
    def test_every_visible_control_on_a_phone_is_44_px_or_more(self):
        """TC-CLV-016 (F3): with a coarse pointer at 360 px every visible control, the five answer actions included, is at least 44 x 44 px.

        Example: speak, up, down, how, regenerate 32 x 44 px -> too small; 44 x 44 px -> [].
        """
        # Given: the chat on a phone with one written answer
        touch = self.results["touch"]
        self.assertTrue(touch["coarse"], "the browser does not emulate a coarse pointer")
        self.assertEqual(touch["width"], 360)
        self.assertTrue({"speak", "up", "down", "how", "regenerate"} <= set(touch["actions"]), touch["actions"])
        # When: the controls below 44 px are picked
        found = too_small(touch["controls"])
        # Then: there are none
        self.assertEqual(found, [])

    @mark.req("REQ-CLV-016")
    def test_no_viewport_scrolls_sideways_in_either_theme(self):
        """TC-CLV-016: at 360, 768 and 1440 px, in the dark and the light theme, the page is never wider than the window.

        Example: {"dark-360": {"sideways": false}, ..., "light-1440": {"sideways": false}} -> [].
        """
        # Given: the six measurements of the layout run
        layout = self.results["layout"]
        # When: the ones that scroll sideways or show another theme are picked
        wrong = [key for key, value in layout.items() if value["sideways"] or value["theme"] != key.split("-")[0]]
        # Then: all six were measured and none is wrong
        self.assertEqual(len(layout), 6)
        self.assertEqual(wrong, [])


if __name__ == "__main__":
    unittest.main()
