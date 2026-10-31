"""TC-CHV-012 (REQ-CHV-012), TC-CHV-001 (REQ-CHV-001): a real browser records the requests of the chat page; the character iframe sends no request
over plain HTTP to a LAN name or with ?character=0, and does on a secure page (the control that the recording sees the iframe).
Stage 2: the chat page from the stub server in the MIA image (tools/start_testing.sh, stage chat-on-stub), headless Chromium in the image
localhost/mia-browser on the host network; the name mia-lan points to 127.0.0.1 inside the browser container, so the page is not a secure context.
Skipped, never passed, where podman, one of the images or the stage is missing, or where the stage runs already (N5).
Run on the host with: python3 tests/test_character_requests.py
"""

import json
import os
import shutil
import subprocess
import sys
import unittest
from urllib.parse import urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402
from test_page_requests import BROWSER_IMAGE, MIA_IMAGE, image_exists, own_stage, stage  # noqa: E402

INSECURE = "http://mia-lan:8685/"
OFF = "http://127.0.0.1:8685/?character=0"
SECURE = "http://127.0.0.1:8685/"
DRIVER = os.path.join(HERE, "browser", "character_requests.py")


def character_requests(urls):
    """the urls of the character (its path starts with /character/)"""
    return [url for url in urls if urlsplit(url).path.startswith("/character/")]


class CharacterRequests(unittest.TestCase):
    pages = None

    @classmethod
    def setUpClass(cls):
        if shutil.which("podman") is None or not image_exists(MIA_IMAGE) or not image_exists(BROWSER_IMAGE):
            raise unittest.SkipTest("podman or an image is missing (%s, %s)" % (MIA_IMAGE, BROWSER_IMAGE))
        if own_stage(stage("start").stdout):
            cls.addClassCleanup(stage, "stop")                    # only a stage this test started is stopped again
        with open(DRIVER, encoding="utf-8") as driver:
            run = subprocess.run(["podman", "run", "--rm", "-i", "--network", "host", "--add-host", "mia-lan:127.0.0.1", BROWSER_IMAGE,
                                  "python", "-", INSECURE, OFF, SECURE], stdin=driver, capture_output=True, text=True, timeout=180)
        if run.returncode != 0:
            raise AssertionError("the browser run failed: " + run.stderr[-500:])
        cls.pages = json.loads(run.stdout.strip().splitlines()[-1])

    @mark.req("REQ-CHV-012")
    def test_plain_http_to_a_lan_name_loads_no_character(self):
        """TC-CHV-012: over plain HTTP to a LAN name the page is no secure context and the character iframe sends no request.

        Example: http://mia-lan:8685/ -> secure False, character_requests(urls) == [], the iframe hidden without src.
        """
        # Given: the session of the page on the LAN name (setUpClass)
        page = self.pages[INSECURE]
        # When: the requests of the character are picked
        found = character_requests(page["urls"])
        # Then: the page is not a secure context and the character sent nothing
        self.assertFalse(page["secure"])
        self.assertEqual(found, [])
        self.assertIsNone(page["src"])
        self.assertTrue(page["hidden"])

    @mark.req("REQ-CHV-001")
    def test_character_off_loads_no_character(self):
        """TC-CHV-001: with ?character=0 the character iframe sends no request, also on a secure page.

        Example: http://127.0.0.1:8685/?character=0 -> character_requests(urls) == [], the iframe hidden without src.
        """
        # Given: the session of the page with ?character=0 (setUpClass)
        page = self.pages[OFF]
        # When: the requests of the character are picked
        found = character_requests(page["urls"])
        # Then: the character sent nothing
        self.assertEqual(found, [])
        self.assertIsNone(page["src"])
        self.assertTrue(page["hidden"])

    @mark.req("REQ-CHV-012")
    def test_a_secure_page_loads_the_character(self):
        """TC-CHV-012: on localhost (a secure context) the iframe gets its address and the recording sees its request.

        Example: http://127.0.0.1:8685/ -> secure True, src "/character/", character_requests(urls) == ["http://127.0.0.1:8685/character/", ...].
        """
        # Given: the session of the page on localhost (setUpClass)
        page = self.pages[SECURE]
        # When: the requests of the character are picked
        found = character_requests(page["urls"])
        # Then: the character loads
        self.assertTrue(page["secure"])
        self.assertEqual(page["src"], "/character/")
        self.assertIn(SECURE + "character/", found)

    def test_the_check_picks_only_character_requests(self):
        """TC-CHV-012: the check picks the urls under /character/ only.

        Example: ["http://h/", "http://h/character/", "http://h/character/index.wasm", "http://h/static/chat/character.js"] -> the two under /character/.
        """
        # Given: urls of the page, of the character and of the page's character.js
        urls = ["http://h/", "http://h/character/", "http://h/character/index.wasm", "http://h/static/chat/character.js"]
        # When: the character's urls are picked
        found = character_requests(urls)
        # Then: only the two under /character/ are left
        self.assertEqual(found, ["http://h/character/", "http://h/character/index.wasm"])


if __name__ == "__main__":
    unittest.main()
