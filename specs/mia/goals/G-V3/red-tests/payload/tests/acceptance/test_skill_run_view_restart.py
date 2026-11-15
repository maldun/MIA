"""
Acceptance test of the Skill run view across a reload and a restart of the real backend (N-1.1, G-V3.PANEL): TC-CLV-038 (REQ-CLV-038, TR-PANEL-004) with the real web application behind
ui/tools/real_backend_stub.py (accounts on, a fake model), its file storage in a folder that is mounted read-write into the container, and headless Chromium of localhost/mia-browser.
The run record and the account are written into that folder before the first start with the code of the repository; the restart is a stop and a new start of the container, not a reset
of an object in the running process. Skipped, never passed, where podman or an image is missing. Run with: python tests/acceptance/test_skill_run_view_restart.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("MIA_ROOT") or os.path.dirname(os.path.dirname(HERE))      # MIA_ROOT: the checkout that is mounted into the container
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

from markers import mark  # noqa: E402

BROWSER_IMAGE = "localhost/mia-browser"
MIA_IMAGE = "localhost/mia:latest"
DRIVER = os.path.join(os.path.dirname(HERE), "browser", "skill_run_restart.py")
BASE = "http://127.0.0.1:8686"
RUN = {"run": "r1", "skill": "review", "skill_version": "1", "account": "anna", "started": "2026-11-08T10:00:00Z", "ended": "2026-11-08T10:05:00Z", "state": "done",
       "phases": [{"name": "screening", "state": "done"}], "budget": {"seconds": {"used": 40, "limit": 600}}, "counts": {"found": 12, "read": 4},
       "answers": [{"text": "canary", "time": "2026-11-08T10:00:05Z"}], "result": "Four of six works report lower cost.", "material": [], "files": [], "elements": []}


def image_exists(name):
    return subprocess.run(["podman", "image", "exists", name]).returncode == 0


def podman(*args):
    return subprocess.run(["podman", *args], capture_output=True, text=True)


def wait_for_page(name):
    probe = "import urllib.request; urllib.request.urlopen('%s/')" % BASE
    for _ in range(60):
        if podman("exec", name, "python", "-c", probe).returncode == 0:
            return
        time.sleep(0.5)
    raise AssertionError("the backend did not answer in 30 s: " + podman("logs", name).stdout[-500:])


def browse(container):
    """one run of the driver in the network of `container`; returns its JSON {"first": view, "reloaded": view}"""
    with open(DRIVER, encoding="utf-8") as driver:
        run = subprocess.run(["podman", "run", "--rm", "-i", "--network", "container:" + container, BROWSER_IMAGE, "python", "-", BASE],
                             stdin=driver, capture_output=True, text=True, timeout=300)
    if run.returncode != 0:
        raise AssertionError("the browser run failed: " + run.stderr[-800:])
    return json.loads(run.stdout.strip().splitlines()[-1])


class SkillRunViewAfterRestart(unittest.TestCase):
    @mark.req("REQ-CLV-038")
    def test_the_view_shows_the_same_run_after_a_reload_and_after_a_restart_of_the_backend(self):
        """TC-CLV-038: a finished run with its final figures is shown again after the page is reloaded and after the backend process is stopped and started anew on the same data.
        Example: run r1 of review, counts found 12 and read 4, is shown with the same header, state and figures three times."""
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            self.skipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        # Given: a finished run with final figures, stored through the file storage in a folder that the container mounts, and the account that logs in
        data = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, data, True)
        os.chmod(data, 0o777)
        import accounts
        from storage import Storage
        from storage_files import FileBackend
        store = Storage(FileBackend(data))
        accounts.create(store, "anna", "pw-anna-1234", "test")
        store.put("skill_runs", RUN["run"], RUN, "anna")
        name = "g-v3-restart-%s" % uuid.uuid4().hex[:8]
        started = podman("run", "-d", "--name", name, "--user", "0:0", "--network", "none", "-e", "MIA_STUB_DATA=/data", "-v", "%s:/opt/mia/MIA:O" % ROOT,
                         "-v", "%s:/data:z" % data, MIA_IMAGE, "python", "MIA/ui/tools/real_backend_stub.py")
        self.assertEqual(started.returncode, 0, started.stderr)
        self.addCleanup(podman, "rm", "-f", "-t", "0", name)
        wait_for_page(name)
        # When: the page is loaded and reloaded; the backend process is stopped and started anew; the page is loaded again
        before = browse(name)
        podman("stop", "-t", "2", name)
        podman("start", name)
        wait_for_page(name)
        after = browse(name)
        # Then: the view shows the same run with the same figures each time
        views = [before["first"], before["reloaded"], after["first"], after["reloaded"]]
        for view in views:
            self.assertNotIn("error", view, view)
            self.assertIsNotNone(view["header"], "the Skill run view is not on the page")
            self.assertIn("review", view["header"].lower())
            self.assertEqual(view["state"].lower(), "done")
            self.assertEqual([c.split()[-1] for c in view["counts"]], ["12", "4"])
            self.assertIn("Four of six works report lower cost.", view["result"])
        self.assertEqual(views[0], views[1])
        self.assertEqual(views[0], views[2])
        self.assertEqual(views[0], views[3])


if __name__ == "__main__":
    unittest.main()
