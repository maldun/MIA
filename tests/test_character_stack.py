"""The technology of the Character view (N-1.2 T-04): TC-CHV-011, TC-CHV-013, TC-CHV-014. Run with the MIA virtualenv: python tests/test_character_stack.py"""
import importlib
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
GODOT = os.path.join(REPO, "ui", "godot")
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)


def gd_code(path):
    """The lines of a GDScript file without comments and without the contents of strings that are not addresses."""
    with open(path, encoding="utf-8") as handle:
        return [line.split("#", 1)[0] for line in handle]


class Technology(unittest.TestCase):
    @mark.req("REQ-CHV-013")
    def test_godot_4_6_1_with_the_compatibility_renderer(self):
        """TC-CHV-013 (AC-20): the project says 4.6 and GL Compatibility for the desktop and for mobile, and the export templates are pinned to 4.6.1.

        Godot writes only major.minor into project.godot; the exact 4.6.1 comes from the export templates named in ui/README.md.
        Example: project.godot with features ("4.6", "GL Compatibility") and README with Godot_v4.6.1-stable_export_templates.tpz -> passes.
        """
        # Given: the project file and the setup text of the character
        with open(os.path.join(GODOT, "project.godot"), encoding="utf-8") as handle:
            text = handle.read()
        with open(os.path.join(REPO, "ui", "README.md"), encoding="utf-8") as handle:
            readme = handle.read()
        # When / Then: the version and the renderer are the ones of REQ-CHV-013
        self.assertIn("Godot 4.6.1", readme)
        self.assertIn("Godot_v4.6.1-stable_export_templates.tpz", readme)
        self.assertIn("export_templates/4.6.1.stable/", readme)
        self.assertIn('config/features=PackedStringArray("4.6", "GL Compatibility")', text)
        self.assertIn('renderer/rendering_method="gl_compatibility"', text)
        self.assertIn('renderer/rendering_method.mobile="gl_compatibility"', text)

    @mark.req("REQ-CHV-013")
    def test_only_gdscript_and_no_bundler_files(self):
        """TC-CHV-013: GDScript only (no C# project), and no bundler or package files next to the character.

        Example: ui/godot with .gd, .tscn and .json files only -> no .cs/.csproj/.sln and no package.json or bundler config.
        """
        # Given / When: the names of all files of the Godot project
        names = {name for _, _, files in os.walk(GODOT) if ".godot" not in _ for name in files}
        # Then: none of them belongs to C# or a bundler
        self.assertEqual(sorted(n for n in names if n.endswith((".cs", ".csproj", ".sln"))), [])
        self.assertEqual(sorted(n for n in names if n in ("package.json", "webpack.config.js", "vite.config.js", "rollup.config.js")), [])

    @mark.req("REQ-CHV-011")
    def test_the_godot_code_names_no_address_outside_the_host(self):
        """TC-CHV-011: every request of the character goes to the origin of the page (window.location.origin) or a relative path.

        Example: preset_api.gd builds its urls from window.location.origin -> no "http://..." or "https://..." outside comments, found == [].
        """
        # Given: the code lines of the top-level GDScript files, without comments
        # When: every http(s) address in them is collected
        found = []
        for name in sorted(os.listdir(GODOT)):
            if name.endswith(".gd"):
                for number, line in enumerate(gd_code(os.path.join(GODOT, name)), 1):
                    for match in re.finditer(r"https?://[A-Za-z0-9.-]+", line):
                        found.append("%s:%d %s" % (name, number, match.group(0)))
        # Then: there is none
        self.assertEqual(found, [])

    @mark.req("REQ-CHV-011")
    def test_the_export_presets_load_nothing_from_a_remote_shell(self):
        """TC-CHV-011: the web export presets name no http(s) address, so the exported page loads no shell or script from elsewhere.

        Example: export_presets.cfg with html/head_include="" -> re.findall(address) == [].
        """
        # Given: the export presets
        with open(os.path.join(GODOT, "export_presets.cfg"), encoding="utf-8") as handle:
            text = handle.read()
        # When / Then: they contain no address
        self.assertEqual(re.findall(r"https?://[A-Za-z0-9.-]+", text), [])


class Delivery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.web_app = importlib.import_module("MIA.web_app")
        cls.web_app.play_intro_sound = lambda: None
        cls.client = cls.web_app.app.test_client()

    @mark.req("REQ-CHV-014")
    def test_the_backend_serves_the_export_files_with_the_right_types(self):
        """TC-CHV-014: static files of the export folder come from the backend, wasm with its MIME type, without caching.

        Example: GET /character/index.wasm -> 200, Content-Type application/wasm, Cache-Control no-cache; /character/../web_app.py -> 404.
        """
        # Given: an export folder with an html, a wasm and a pck file, used by the backend
        folder = tempfile.mkdtemp()
        for name, data in (("index.html", b"<html></html>"), ("index.wasm", b"\0asm\x01\0\0\0"), ("index.pck", b"GDPC")):
            with open(os.path.join(folder, name), "wb") as handle:
                handle.write(data)
        original = self.web_app.CHARACTER_FOLDER
        self.web_app.CHARACTER_FOLDER = folder
        self.addCleanup(setattr, self.web_app, "CHARACTER_FOLDER", original)
        # When: each file is requested / Then: it comes with its type and without caching
        for name, mime in (("index.html", "text/html"), ("index.wasm", "application/wasm"), ("index.pck", None)):
            response = self.client.get("/character/" + name)
            self.assertEqual(response.status_code, 200, name)
            self.assertEqual(response.headers["Cache-Control"], "no-cache")
            if mime:
                self.assertTrue(response.headers["Content-Type"].startswith(mime), (name, response.headers["Content-Type"]))
        # Then: a path out of the folder is refused
        self.assertEqual(self.client.get("/character/../web_app.py").status_code, 404)

    @mark.req("REQ-CHV-014")
    def test_without_a_build_the_backend_says_so_and_the_chat_page_still_loads(self):
        """TC-CHV-014: without an export the backend answers 404 with "not built", and the chat page itself still loads.

        Example: CHARACTER_FOLDER missing -> GET /character/index.html 404 "...not built..."; GET / 200.
        """
        # Given: the backend with an export folder that does not exist
        original = self.web_app.CHARACTER_FOLDER
        self.web_app.CHARACTER_FOLDER = os.path.join(tempfile.mkdtemp(), "missing")
        self.addCleanup(setattr, self.web_app, "CHARACTER_FOLDER", original)
        # When: the character is requested
        response = self.client.get("/character/index.html")
        # Then: it says it is not built, and the chat page loads
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"not built", response.data)
        self.assertEqual(self.client.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
