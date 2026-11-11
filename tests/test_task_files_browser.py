"""The stage-2 browser checks of the Files tab (N-1.1; TD-02): TC-CLV-024 (REQ-CLV-024). The status card (TC-CLV-023) is retired by G-V3.PANEL T-10; the Skill run view is checked in tests/acceptance/test_skill_run_view_browser.py.
The real page on the IF-101 mock server (ui/tools/chat_mock_server.py, with one older file in the volume) in its own container of the MIA image with
`--network none`, headless Chromium of localhost/mia-browser in that container's network (tests/browser/Containerfile, D-141), one run of
tests/browser/task_files.py. Skipped, never passed, where podman or one of the images is missing.  Run on the host with: python3 tests/test_task_files_browser.py"""
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
DRIVER = os.path.join(HERE, "browser", "task_files.py")
BASE = "http://127.0.0.1:8686"


def image_exists(name):
    return subprocess.run(["podman", "image", "exists", name]).returncode == 0


def start_mock():
    """the mock server in a container of its own, without network; returns its name once the page answers"""
    name = "n11-tasks-%s" % uuid.uuid4().hex[:8]
    subprocess.run(["podman", "run", "-d", "--name", name, "--user", "0:0", "--network", "none", "-e", "ANSWER_DELAY=1", "-e", "EVENT_GAP=0.05",
                    "-e", "MOCK_SEED_FILES=1", "-v", "%s:/opt/mia/MIA:O" % ROOT, MIA_IMAGE, "python", "MIA/ui/tools/chat_mock_server.py"],
                   check=True, capture_output=True)
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
                             stdin=driver, capture_output=True, text=True, timeout=400)
    if run.returncode != 0:
        raise AssertionError("the browser run failed: " + run.stderr[-800:])
    return json.loads(run.stdout.strip().splitlines()[-1])


class FilesInBrowser(unittest.TestCase):
    results = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        cls.results = {}
        for scenario in ("files",):                 # a fresh mock for each: the report of one review is a file in the volume of the next
            container = start_mock()
            cls.addClassCleanup(stop_mock, container)
            cls.results.update(browse(container, scenario))

    @mark.req("REQ-CLV-024")
    def test_the_files_list_is_drawn_with_download_links_and_redrawn_after_files_changed(self):
        """TC-CLV-024 (TD-02): the Files tab lists the volume with a link to /api/files/<name> each; a file stored by a task appears at the top
        without a reload (event files_changed) and the older one follows; the link downloads as an attachment.

        Example: [notes-older.txt] -> task ends -> [review-contract.md, notes-older.txt], href /api/files/review-contract.md, status 200.
        """
        # Given: the run with the Files tab open while a task stored its report
        files = self.results["files"]
        # When / Then: before, the older file only
        self.assertEqual([f["name"] for f in files["before"]], ["notes-older.txt"])
        self.assertEqual(files["before"][0]["href"], "/api/files/notes-older.txt")
        # and after the event: newest first, no reload, each entry a download link
        self.assertTrue(files["redrawn"] and files["not_reloaded"])
        self.assertEqual([f["name"] for f in files["after"]], ["review-contract.md", "notes-older.txt"])
        self.assertEqual([f["href"] for f in files["after"]], ["/api/files/review-contract.md", "/api/files/notes-older.txt"])
        self.assertTrue(all(f["download"] for f in files["after"]))
        self.assertEqual(files["download"]["status"], 200)
        self.assertIn("attachment", files["download"]["disposition"])
        self.assertEqual(files["download"]["body"], "# the report\n")

    @mark.req("REQ-CLV-024")
    def test_the_files_tab_offers_no_way_to_delete(self):
        """TC-CLV-024 (TD-02): the tab has no button or control at all, so no delete.

        Example: controls == [] with two files listed.
        """
        # Given: the Files tab with two files
        files = self.results["files"]
        # When / Then: it has no control that could delete
        self.assertEqual(len(files["after"]), 2)
        self.assertEqual(files["controls"], [])


if __name__ == "__main__":
    unittest.main()
