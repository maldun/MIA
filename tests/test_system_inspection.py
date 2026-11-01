"""
TC-MIA-020 (AC-20, CON-1, CON-3, CON-6): the repository as the system test reads it. The parts of AC-20 that other tests already hold are named, not
repeated: licence, paid-API packages and the web log (tools/check_free.py, tests/test_check_free.py, TC-OPR-009), Python 3.12
(tests/test_python_version.py, TC-API-011), Godot 4.6 with GL Compatibility (tests/test_character_stack.py, TC-CHV-013), no roles
(tests/test_accounts_wiring.py, TC-API-010). Here: the chat page without build step or framework, and the login page that says everything is
visible to all.   python tests/test_system_inspection.py
"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                          # noqa: E402


def read(*parts):
    with open(os.path.join(REPO, *parts), encoding="utf-8", errors="ignore") as fp:
        return fp.read()


class PlainPage(unittest.TestCase):
    """CON-3: the chat page is plain HTML, CSS and ES modules, no build step, no UI framework"""

    @mark.req("CON-3")
    def test_the_page_has_no_build_step(self):
        """TC-MIA-020 Given the static folder, When its package file and sources are read, Then it declares modules only: no scripts, no dependencies, no JSX or TypeScript"""
        package = json.loads(read("templates", "static", "package.json"))
        self.assertEqual(package.get("type"), "module")
        for key in ("scripts", "dependencies", "devDependencies"):
            self.assertNotIn(key, package)
        for root, _dirs, files in os.walk(os.path.join(REPO, "templates")):
            self.assertEqual([f for f in files if f.endswith((".jsx", ".tsx", ".ts", ".vue", ".svelte"))], [], root)
        for name in ("webpack.config.js", "vite.config.js", "rollup.config.js", "tsconfig.json"):
            self.assertFalse(os.path.exists(os.path.join(REPO, "templates", "static", name)), name)

    @mark.req("CON-3")
    def test_the_page_loads_its_code_as_modules_from_its_own_host(self):
        """TC-MIA-020 Given the chat page, When its script tags are read, Then the code is loaded as modules and from no other host"""
        html = read("templates", "index.html")
        scripts = re.findall(r"<script\b[^>]*>", html)
        self.assertTrue(scripts)
        for tag in scripts:
            self.assertIn('type="module"', tag)
            self.assertNotRegex(tag, r"src=\"https?://")


class TrustedUsers(unittest.TestCase):
    """CON-6: every user sees everything; the login page says so"""

    @mark.req("CON-6")
    def test_the_login_page_says_that_everything_is_visible_to_all(self):
        """TC-MIA-020 Given the login page, When its text is read, Then it says the conversation, memory and workflows are visible to all users"""
        html = read("templates", "index.html")
        self.assertIn('id="login-visible"', html)
        text = json.loads(read("templates", "static", "chat", "i18n", "en.json"))["login.visible"]
        for word in ("visible to all users", "conversation", "memory", "workflows"):
            self.assertIn(word, text)


if __name__ == "__main__":
    unittest.main()
