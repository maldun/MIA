"""The stage-2 browser checks of the status card and the Files tab (N-1.1; TD-01, TD-02): TC-CLV-023 (REQ-CLV-023) and TC-CLV-024 (REQ-CLV-024).
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


class TaskCardAndFilesInBrowser(unittest.TestCase):
    results = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        cls.results = {}
        for scenario in ("card", "files"):                 # a fresh mock for each: the report of one review is a file in the volume of the next
            container = start_mock()
            cls.addClassCleanup(stop_mock, container)
            cls.results.update(browse(container, scenario))

    @mark.req("REQ-CLV-023")
    def test_a_task_status_draws_one_card_with_its_figures_that_fits_a_phone(self):
        """TC-CLV-023 (TD-01): a task_status of the mock draws one card with the phase, the state and the figures it carries, without
        horizontal scrolling at 360 px, with Pause and Stop.

        Example: /review with {phase: working, budget: {seconds: {used: 0}}} -> one card, state running, text has "working" and the seconds, buttons Pause, Stop.
        """
        # Given: the phone run that started a /review of the mock
        card = self.results["card"]
        self.assertTrue(card["appeared"])
        # When: the first card is read
        cards = card["first"]
        # Then: exactly one, running, with phase and figure, readable without sideways scrolling, with its two buttons
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["state"], "running")
        self.assertIn("working", cards[0]["text"])
        self.assertRegex(cards[0]["text"], r"\d+(\.\d)? s")
        self.assertTrue(cards[0]["fits"])
        self.assertEqual(cards[0]["buttons"], ["Pause", "Stop"])

    @mark.req("REQ-CLV-023")
    def test_pause_and_resume_send_one_request_each_and_change_the_same_card(self):
        """TC-CLV-023 (TD-01): Pause sends one pause request and the same card shows Resume; Resume sends one resume request and the card runs again.

        Example: card m1 running -> Pause -> m1 paused, buttons Resume, Stop -> Resume -> m1 running; requests /api/pause and /api/resume once each.
        """
        # Given: the run that paused and resumed the task
        card = self.results["card"]
        first, paused, resumed = card["first"], card["after_pause"], card["after_resume"]
        # When / Then: the same card (one node, the same id) changed state in place, with one request for each button
        self.assertTrue(card["paused"] and card["resumed"])
        self.assertEqual([len(first), len(paused), len(resumed)], [1, 1, 1])
        self.assertEqual({first[0]["id"], paused[0]["id"], resumed[0]["id"]}, {first[0]["id"]})
        self.assertEqual(paused[0]["state"], "paused")
        self.assertEqual(paused[0]["buttons"], ["Resume", "Stop"])
        self.assertEqual(resumed[0]["state"], "running")
        self.assertEqual([url.rsplit("/", 1)[1] for url in card["posts"]], ["pause", "resume"])

    @mark.req("REQ-CLV-023")
    def test_a_finished_card_stays_with_its_figures_and_a_late_status_does_not_change_it(self):
        """TC-CLV-023 (TD-01): when the task ends the card stays with its figures and loses its buttons; a task_status that comes after done
        (the real handler of the page is called) changes nothing; Stop ends a second task on its own card.

        Example: done -> state done, buttons [], same text after a late status {phase: late}; second /review -> two cards, Stop -> the second is done.
        """
        # Given: the run that ended the task, sent a late status and stopped a second task
        card = self.results["card"]
        # When / Then: the finished card kept its figures without buttons, the late status left it as it was
        self.assertTrue(card["done"])
        done = card["after_done"][0]
        self.assertEqual(done["state"], "done")
        self.assertEqual(done["buttons"], [])
        self.assertRegex(done["text"], r"\d+(\.\d)? s")
        self.assertEqual(card["after_late"], card["after_done"])
        self.assertNotIn("late", card["after_late"][0]["text"])
        # and the second task has its own card that Stop ended, the first one untouched
        self.assertTrue(card["second_appeared"] and card["stopped"])
        self.assertEqual(len(card["after_stop"]), 2)
        self.assertNotEqual(card["after_stop"][1]["id"], done["id"])
        self.assertEqual(card["after_stop"][1]["state"], "done")
        self.assertEqual(card["after_stop"][0], done)

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
