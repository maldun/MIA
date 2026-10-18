"""
Tests for the chat page (templates/index.html and templates/static/chat/*): strict CSP, no inline code,
nothing from the internet, all referenced files exist. Run with the MIA virtualenv: python tests/test_chat_page.py
"""
import importlib
import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CHAT_STATIC = os.path.join(REPO, "templates", "static", "chat")

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


class ChatPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.web_app = importlib.import_module("MIA.web_app")
        cls.web_app.play_intro_sound = lambda: None
        cls.client = cls.web_app.app.test_client()
        cls.response = cls.client.get("/")
        cls.html = cls.response.get_data(as_text=True)

    def test_page_is_served(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertIn('id="panel"', self.html)

    def test_csp_header_is_strict(self):
        csp = self.response.headers["Content-Security-Policy"]
        self.assertIn("script-src 'self'", csp)
        self.assertIn("style-src 'self'", csp)
        self.assertNotIn("unsafe-inline", csp)
        self.assertNotIn("unsafe-eval", csp)
        self.assertEqual(self.response.headers["X-Content-Type-Options"], "nosniff")

    def test_no_inline_script_style_or_handlers(self):
        for script in re.findall(r"<script\b([^>]*)>", self.html):
            self.assertIn("src=", script)
        self.assertNotIn("<style", self.html)
        self.assertIsNone(re.search(r"\sstyle=", self.html))
        self.assertIsNone(re.search(r"\son[a-z]+=", self.html))

    def test_nothing_from_the_internet(self):
        self.assertIsNone(re.search(r"(?:src|href)=\"(?:https?:)?//", self.html))
        self.assertNotIn("cdn", self.html.lower())

    def test_referenced_static_files_exist_with_the_right_type(self):
        urls = re.findall(r"(?:src|href)=\"(/static/[^\"]+)\"", self.html)
        self.assertGreaterEqual(len(urls), 4)
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            expected = "text/css" if url.endswith(".css") else "javascript"
            self.assertIn(expected, response.headers["Content-Type"], url)
            self.assertIn("Content-Security-Policy", response.headers, url)

    def test_modules_import_only_existing_local_files(self):
        for name in os.listdir(CHAT_STATIC):
            if not name.endswith(".js"):
                continue
            with open(os.path.join(CHAT_STATIC, name), encoding="utf-8") as handle:
                source = handle.read()
            for target in re.findall(r"from\s+'(\.[^']+)'", source):
                self.assertTrue(os.path.exists(os.path.normpath(os.path.join(CHAT_STATIC, target))), f"{name}: {target}")

    def test_dictionaries_have_the_same_keys(self):
        with open(os.path.join(CHAT_STATIC, "i18n", "en.json"), encoding="utf-8") as handle:
            en = json.load(handle)
        with open(os.path.join(CHAT_STATIC, "i18n", "de.json"), encoding="utf-8") as handle:
            de = json.load(handle)
        self.assertEqual(set(en), set(de))
        keys = set(re.findall(r'data-i18n(?:-[a-z-]+)?="([^"]+)"', self.html))
        self.assertTrue(keys <= set(en), keys - set(en))

    def test_old_socket_events_still_work(self):
        wa = self.web_app
        client = wa.socketio.test_client(wa.app)
        client.emit("character_ready")
        client.disconnect()


if __name__ == "__main__":
    unittest.main()
