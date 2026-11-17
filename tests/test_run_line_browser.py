"""The stage-2 browser check of the live status line (N-1.1, REQ-CLV-053, 054, A-158): TC-CLV-053, driver tests/browser/run_line.py.
The real page on the chat stub server (ui/tools/chat_stub_server.py with a scripted skill run: say `run`) in its own container of the MIA image with `--network none`,
and headless Chromium of localhost/mia-browser in that container's network, as in tests/test_speak_again_browser.py. Skipped, never passed, where podman or one of the
images is missing.  Run on the host with: python3 tests/test_run_line_browser.py"""
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
DRIVER = os.path.join(HERE, "browser", "run_line.py")
BASE = "http://127.0.0.1:8685"


def image_exists(name):
    return subprocess.run(["podman", "image", "exists", name]).returncode == 0


def start_stub():
    """the stub server in a container of its own, without network; returns its name once the page answers"""
    name = "a158-stub-%s" % uuid.uuid4().hex[:8]
    subprocess.run(["podman", "run", "-d", "--name", name, "--user", "0:0", "--network", "none", "-v", "%s:/opt/mia/MIA:O" % ROOT, MIA_IMAGE,
                    "python", "MIA/ui/tools/chat_stub_server.py"], check=True, capture_output=True)
    probe = "import urllib.request; urllib.request.urlopen('%s/')" % BASE
    for _ in range(80):
        if subprocess.run(["podman", "exec", name, "python", "-c", probe], capture_output=True).returncode == 0:
            return name
        time.sleep(0.5)
    logs = subprocess.run(["podman", "logs", name], capture_output=True, text=True).stdout[-500:]
    stop_stub(name)
    raise AssertionError("the stub server did not answer in 40 s: " + logs)


def stop_stub(name):
    subprocess.run(["podman", "rm", "-f", "-t", "0", name], capture_output=True)


def browse(container, *scenarios):
    """one run of the driver in the network of `container`; returns its JSON {scenario: result}"""
    with open(DRIVER, encoding="utf-8") as driver:
        run = subprocess.run(["podman", "run", "--rm", "-i", "--network", "container:" + container, BROWSER_IMAGE, "python", "-", BASE, *scenarios],
                             stdin=driver, capture_output=True, text=True, timeout=300)
    if run.returncode != 0:
        raise AssertionError("the browser run failed: " + run.stderr[-800:])
    return json.loads(run.stdout.strip().splitlines()[-1])


class LiveLineInBrowser(unittest.TestCase):
    samples = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        container = start_stub()
        cls.addClassCleanup(stop_stub, container)
        cls.samples = browse(container, "live_line")["live_line"]

    @mark.req("REQ-CLV-053")
    def test_the_line_is_always_the_last_element_and_shows_the_phases_in_place(self):
        """TC-CLV-053 (REQ-CLV-053): while the run works the status line is the last element of the chat, also after a second message, and shows the phases one after the other.
        Example: collect, rank, Waiting for your answer (the page translates it), rank, report; the line holds the run link."""
        # Given the real page on the stub, a run started by `run` and a second message sent 3 s later
        shown = [s for s in self.samples if s["line"] is not None]
        # Then the line was seen, was the last element of the chat whenever it was there, and held the link of the run
        self.assertTrue(shown, self.samples)
        self.assertTrue(all(s["lineIsLast"] for s in shown), shown)
        self.assertTrue(all(s["link"] == "#run=r-demo" for s in shown), shown)
        # And the texts came in the order of the run, each shown in place (one line at a time)
        texts = [s["line"] for i, s in enumerate(shown) if i == 0 or shown[i - 1]["line"] != s["line"]]
        self.assertEqual(texts[:3], ["collect", "rank", "Waiting for your answer"], texts)
        self.assertIn("report", texts)

    @mark.req("REQ-CLV-054")
    def test_the_line_is_gone_when_the_end_message_is_last(self):
        """TC-CLV-053 (REQ-CLV-054): at the end of the run no line is left and the end message with the run link is the last row.
        Example: the last sample has no line and its last row holds "Skill run view"."""
        # Given the same run
        last = self.samples[-1]
        # Then no line is left and the last row is the end message
        self.assertIsNone(last["line"], self.samples[-3:])
        self.assertIn("Skill run view", last["lastRow"])


if __name__ == "__main__":
    unittest.main()
