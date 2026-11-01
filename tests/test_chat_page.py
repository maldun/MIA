"""
Tests for the chat page (templates/index.html and templates/static/chat/*): strict CSP, no inline code,
nothing from the internet, all referenced files exist. Run with the MIA virtualenv: python tests/test_chat_page.py
"""
import gzip
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

import checkout_copy  # noqa: E402  (MIA from a temporary copy: nothing is written into the checkout, D-169)
_LINK_DIR = checkout_copy.use()


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
        """The backend serves the chat page (REQ-CLV-020).

        Example: GET / -> 200 with the element id="panel".
        """
        # Given / When: the page fetched in setUpClass
        # Then: it is there with its chat panel
        self.assertEqual(self.response.status_code, 200)
        self.assertIn('id="panel"', self.html)

    def test_csp_header_is_strict(self):
        """The page has a strict Content Security Policy: own scripts and styles only, no inline code, no eval (REQ-CLV-017).

        Example: "script-src 'self'" and "style-src 'self'" present, "unsafe-inline" and "unsafe-eval" absent, X-Content-Type-Options nosniff.
        """
        # Given: the headers of the page
        csp = self.response.headers["Content-Security-Policy"]
        # When / Then: the policy is strict
        self.assertIn("script-src 'self'", csp)
        self.assertIn("style-src 'self'", csp)
        self.assertNotIn("unsafe-inline", csp)
        self.assertNotIn("unsafe-eval", csp)
        self.assertEqual(self.response.headers["X-Content-Type-Options"], "nosniff")

    def test_no_inline_script_style_or_handlers(self):
        """The markup has no inline script, style element, style attribute or on... handler (the CSP would block them).

        Example: <script src="..."> only; no <style>, no style="...", no onclick="...".
        """
        # Given: the script tags of the page
        scripts = re.findall(r"<script\b([^>]*)>", self.html)
        # When / Then: each loads a file, and nothing inline is left
        for script in scripts:
            self.assertIn("src=", script)
        self.assertNotIn("<style", self.html)
        self.assertIsNone(re.search(r"\sstyle=", self.html))
        self.assertIsNone(re.search(r"\son[a-z]+=", self.html))

    def test_nothing_from_the_internet(self):
        """No src or href of the page points to another host, and no CDN is named (REQ-CLV-017).

        Example: src="//cdn.example/x.js" or href="https://..." -> found; /static/... -> fine.
        """
        # Given / When: the markup of the page
        # Then: no address with a host, no CDN
        self.assertIsNone(re.search(r"(?:src|href)=\"(?:https?:)?//", self.html))
        self.assertNotIn("cdn", self.html.lower())

    def test_referenced_static_files_exist_with_the_right_type(self):
        """Every /static/ file the page names is served with its type and the CSP header.

        Example: /static/chat/app.js -> 200, javascript; /static/chat/tokens.css -> 200, text/css.
        """
        # Given: the static addresses of the page (at least four)
        urls = re.findall(r"(?:src|href)=\"(/static/[^\"]+)\"", self.html)
        self.assertGreaterEqual(len(urls), 4)
        # When / Then: each is served with the right type and the policy
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            expected = "text/css" if url.endswith(".css") else "javascript"
            self.assertIn(expected, response.headers["Content-Type"], url)
            self.assertIn("Content-Security-Policy", response.headers, url)

    def test_modules_import_only_existing_local_files(self):
        """Every relative import of a page module names a file that exists (REQ-CLV-019: plain ES modules, no bundler).

        Example: app.js "from './chat.js'" -> templates/static/chat/chat.js exists.
        """
        # Given: the modules of the page
        for name in os.listdir(CHAT_STATIC):
            if not name.endswith(".js"):
                continue
            with open(os.path.join(CHAT_STATIC, name), encoding="utf-8") as handle:
                source = handle.read()
            # When / Then: every relative import exists
            for target in re.findall(r"from\s+'(\.[^']+)'", source):
                self.assertTrue(os.path.exists(os.path.normpath(os.path.join(CHAT_STATIC, target))), f"{name}: {target}")

    def test_dictionaries_have_the_same_keys(self):
        """The English and the German texts have the same keys, and every data-i18n key of the markup has a text.

        Example: "workspace.due" in en.json -> also in de.json; data-i18n="login.visible" -> in en.json.
        """
        # Given: both dictionaries
        with open(os.path.join(CHAT_STATIC, "i18n", "en.json"), encoding="utf-8") as handle:
            en = json.load(handle)
        with open(os.path.join(CHAT_STATIC, "i18n", "de.json"), encoding="utf-8") as handle:
            de = json.load(handle)
        # When: the keys of the markup are read
        keys = set(re.findall(r'data-i18n(?:-[a-z-]+)?="([^"]+)"', self.html))
        # Then: the same keys in both, and all of the markup's among them
        self.assertEqual(set(en), set(de))
        self.assertTrue(keys <= set(en), keys - set(en))

    def test_performance_budget_of_the_scripts(self):
        """The chat's own JavaScript (not the vendored libraries) stays under 100 KB gzipped.

        Example: the modules of templates/static/chat/ gzipped one by one, summed -> below 102400 bytes.
        """
        # Given / When: the gzipped size of every module, summed
        total = 0
        for name in os.listdir(CHAT_STATIC):
            if name.endswith(".js"):
                with open(os.path.join(CHAT_STATIC, name), "rb") as handle:
                    total += len(gzip.compress(handle.read()))
        # Then: under the budget
        self.assertLess(total, 100 * 1024, "chat scripts are %d bytes gzipped" % total)

    def test_no_leftovers_of_the_old_page(self):
        """Nothing of the old page is left: no md-block, no answer.html, no answerInput.

        Example: a module that still names "md-block" -> found.
        """
        # Given / When: every file of the page's folder
        for name in os.listdir(CHAT_STATIC):
            path = os.path.join(CHAT_STATIC, name)
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as handle:
                    source = handle.read()
                # Then: none names the old parts
                self.assertNotIn("md-block", source, name)
                self.assertNotIn("answer.html", source, name)
        self.assertNotIn("answerInput", self.html)
        self.assertFalse(os.path.exists(os.path.join(REPO, "templates", "static", "answer.html")))

    def test_the_log_and_the_page_do_not_use_the_old_answer_event(self):
        """The server no longer sends the old `answer` event nor handles the old `message` event.

        Example: web_app.py with "emit('answer'" -> found.
        """
        # Given: the source of the web app
        with open(os.path.join(REPO, "web_app.py"), encoding="utf-8") as handle:
            source = handle.read()
        # When / Then: the old events are gone
        self.assertNotIn("emit('answer'", source)
        self.assertNotIn("md-block", source)
        self.assertNotIn("@socketio.on('message')", source)

    def test_old_socket_events_still_work(self):
        """The character's `character_ready` is still taken by the server without an error.

        Example: a socket emits character_ready and disconnects -> no exception.
        """
        # Given: a socket of the test client
        wa = self.web_app
        client = wa.socketio.test_client(wa.app)
        # When / Then: the event goes through and the socket closes cleanly
        client.emit("character_ready")
        client.disconnect()


if __name__ == "__main__":
    unittest.main()
