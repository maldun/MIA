"""
Tests for ui/tools/character_pack.py: the 3D character as zip files that travel outside git. The zips are the same bytes for the same content, install checks the SHA-256 of the manifest, refuses unsafe zips
(paths outside the target, links, entries of another place, a huge size), replaces the web export in one step, keeps the Blender file that was there. Nothing here touches the real character.
Run with the MIA virtualenv: python tests/test_character_pack.py
"""
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("character_pack", os.path.join(REPO, "ui", "tools", "character_pack.py"))
CP = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CP)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.web = os.path.join(self.tmp, "godot", "build", "web")          # the "export" that is packed
        self.folder = os.path.join(self.tmp, "character")                   # ui/character with the manifest and the zips
        os.makedirs(os.path.join(self.web, "sub"))
        self.write(os.path.join(self.web, "index.html"), b"<html>one</html>")
        self.write(os.path.join(self.web, "index.pck"), os.urandom(5000))
        self.write(os.path.join(self.web, "sub", "a.js"), b"console.log(1)")
        self.write(os.path.join(self.web, "index.png.import"), b"editor metadata")
        os.makedirs(self.folder)
        self.blend = os.path.join(self.folder, "mia.blend")
        self.write(self.blend, b"BLENDER-v500" + os.urandom(3000))
        self.old_web = CP.WEB_DIR
        CP.WEB_DIR = self.web

    def tearDown(self):
        CP.WEB_DIR = self.old_web
        shutil.rmtree(self.tmp, ignore_errors=True)

    @staticmethod
    def write(path, data):
        with open(path, "wb") as fp:
            fp.write(data)

    def manifest(self):
        return json.load(open(os.path.join(self.folder, "manifest.json")))

    def other_machine(self):
        """a folder as it is after the downloads: the manifest (from git) and the zips (from the Drive), and an export folder that does not exist yet"""
        other = os.path.join(self.tmp, "other")
        shutil.copytree(self.folder, other, ignore=shutil.ignore_patterns("mia.blend", "mia.previous.blend"))
        return other, os.path.join(self.tmp, "other_godot", "build", "web")


class Packing(Base):
    def test_a_pack_has_a_manifest_entry_with_checksum_and_size(self):
        r = CP.pack("web", self.folder)
        entry = self.manifest()["web"]
        self.assertEqual((entry["version"], entry["file"], entry["files"]), (1, "mia-character-web-1.zip", 3))
        self.assertEqual(entry["sha256"], CP.sha256_file(os.path.join(self.folder, entry["file"])))
        self.assertEqual(entry["size"], os.path.getsize(os.path.join(self.folder, entry["file"])))
        self.assertEqual(r["note"], "new version")
        with zipfile.ZipFile(os.path.join(self.folder, entry["file"])) as zf:
            self.assertEqual(zf.namelist(), ["web/index.html", "web/index.pck", "web/sub/a.js"])          # no *.import: Godot's editor metadata

    def test_the_same_content_gives_the_same_bytes_and_the_same_version(self):
        first = CP.pack("web", self.folder)
        second = CP.pack("web", self.folder)
        self.assertEqual((second["note"], second["version"], second["sha256"]), ("unchanged", 1, first["sha256"]))
        self.assertEqual(sorted(f for f in os.listdir(self.folder) if f.endswith(".zip")), ["mia-character-web-1.zip"])

    def test_a_change_gives_a_new_version_and_a_new_file(self):
        CP.pack("web", self.folder)
        self.write(os.path.join(self.web, "index.html"), b"<html>two</html>")
        r = CP.pack("web", self.folder)
        self.assertEqual((r["note"], r["version"]), ("new version", 2))
        self.assertEqual(self.manifest()["web"]["file"], "mia-character-web-2.zip")
        self.assertTrue(os.path.exists(os.path.join(self.folder, "mia-character-web-1.zip")))       # the old one stays

    def test_the_source_pack_holds_only_the_blend(self):
        CP.pack("source", self.folder)
        with zipfile.ZipFile(os.path.join(self.folder, self.manifest()["source"]["file"])) as zf:
            self.assertEqual(zf.namelist(), ["mia.blend"])

    def test_an_install_stamp_is_not_packed(self):
        self.write(os.path.join(self.web, CP.STAMP), b"x")
        CP.pack("web", self.folder)
        with zipfile.ZipFile(os.path.join(self.folder, self.manifest()["web"]["file"])) as zf:
            self.assertNotIn("web/" + CP.STAMP, zf.namelist())

    def test_nothing_to_pack_is_an_error_that_says_what_to_do(self):
        shutil.rmtree(self.web)
        with self.assertRaisesRegex(CP.PackError, "setup_character.sh"):
            CP.pack("web", self.folder)
        os.remove(self.blend)
        with self.assertRaisesRegex(CP.PackError, "--blend"):
            CP.pack("source", self.folder)


class Installing(Base):
    def test_the_round_trip_gives_the_same_files(self):
        CP.pack("web", self.folder)
        other, target = self.other_machine()
        result = CP.install("web", other, web_dir=target)
        self.assertTrue(result["installed"])
        for rel in ("index.html", "index.pck", os.path.join("sub", "a.js")):
            self.assertEqual(open(os.path.join(target, rel), "rb").read(), open(os.path.join(self.web, rel), "rb").read(), rel)
        self.assertEqual(open(os.path.join(target, CP.STAMP)).read().strip(), self.manifest()["web"]["sha256"])

    def test_a_second_install_does_nothing_unless_forced(self):
        CP.pack("web", self.folder)
        other, target = self.other_machine()
        CP.install("web", other, web_dir=target)
        marker = os.path.join(target, "marker")
        self.write(marker, b"m")
        self.assertFalse(CP.install("web", other, web_dir=target)["installed"])
        self.assertTrue(os.path.exists(marker))
        self.assertTrue(CP.install("web", other, force=True, web_dir=target)["installed"])
        self.assertFalse(os.path.exists(marker))                      # replaced as a whole, nothing of the old folder is left

    def test_a_new_version_replaces_the_old_export_completely_and_leaves_no_temporary_folders(self):
        CP.pack("web", self.folder)
        other, target = self.other_machine()
        CP.install("web", other, web_dir=target)
        self.write(os.path.join(self.web, "sub", "a.js"), b"console.log(2)")
        os.remove(os.path.join(self.web, "index.html"))
        CP.pack("web", self.folder)
        shutil.copy(os.path.join(self.folder, "manifest.json"), other)
        shutil.copy(os.path.join(self.folder, "mia-character-web-2.zip"), other)
        CP.install("web", other, web_dir=target)
        self.assertFalse(os.path.exists(os.path.join(target, "index.html")))
        self.assertEqual(open(os.path.join(target, "sub", "a.js"), "rb").read(), b"console.log(2)")
        self.assertEqual(os.listdir(os.path.dirname(target)), ["web"])

    def test_a_missing_zip_says_which_file_to_get_and_where_to_put_it(self):
        CP.pack("web", self.folder)
        other, target = self.other_machine()
        os.remove(os.path.join(other, "mia-character-web-1.zip"))
        with self.assertRaises(CP.PackError) as caught:
            CP.install("web", other, web_dir=target)
        message = str(caught.exception)
        self.assertIn("mia-character-web-1.zip", message)
        self.assertIn(other, message)
        self.assertIn("Google Drive", message)
        self.assertFalse(os.path.exists(target))

    def test_no_manifest_entry_is_an_error(self):
        with self.assertRaisesRegex(CP.PackError, "no web pack"):
            CP.install("web", self.folder, web_dir=os.path.join(self.tmp, "t"))

    def test_a_changed_zip_is_refused_and_nothing_is_unpacked(self):
        CP.pack("web", self.folder)
        other, target = self.other_machine()
        path = os.path.join(other, "mia-character-web-1.zip")
        with open(path, "ab") as fp:
            fp.write(b"x")
        with self.assertRaisesRegex(CP.PackError, "not the file of the manifest"):
            CP.install("web", other, web_dir=target)
        self.assertFalse(os.path.exists(target))

    def test_the_blend_that_was_there_is_kept_as_previous(self):
        CP.pack("source", self.folder)
        other, _ = self.other_machine()
        mine = os.path.join(other, "mia.blend")
        self.write(mine, b"MY OWN VERSION")
        result = CP.install("source", other)
        self.assertTrue(result["installed"])
        self.assertEqual(open(os.path.join(other, "mia.previous.blend"), "rb").read(), b"MY OWN VERSION")
        self.assertEqual(open(mine, "rb").read(), open(self.blend, "rb").read())
        self.assertFalse(CP.install("source", other)["installed"])         # the same file again: nothing changes

    def test_a_clean_machine_gets_the_blend(self):
        CP.pack("source", self.folder)
        other, _ = self.other_machine()
        self.assertTrue(CP.install("source", other)["installed"])
        self.assertEqual(open(os.path.join(other, "mia.blend"), "rb").read(), open(self.blend, "rb").read())
        self.assertFalse(os.path.exists(os.path.join(other, "mia.previous.blend")))


class HostileZips(Base):
    """a zip with the right checksum in the manifest (somebody changed the Drive file AND the manifest): the content is still checked"""

    def install_zip(self, kind, members, max_bytes=None):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as zf:
            for item in members:
                if isinstance(item, zipfile.ZipInfo):
                    zf.writestr(item, b"target")
                else:
                    zf.writestr(item, b"data")
        folder = os.path.join(self.tmp, "hostile")
        os.makedirs(folder, exist_ok=True)
        name = "mia-character-%s-1.zip" % kind
        self.write(os.path.join(folder, name), data.getvalue())
        CP.write_manifest(folder, {"format": 1, kind: {"version": 1, "file": name, "sha256": CP.sha256_file(os.path.join(folder, name)), "size": len(data.getvalue()), "files": len(members)}})
        old = CP.MAX_BYTES
        if max_bytes:
            CP.MAX_BYTES = max_bytes
        try:
            return CP.install(kind, folder, web_dir=os.path.join(self.tmp, "victim", "web"))
        finally:
            CP.MAX_BYTES = old

    def refused(self, kind, members, pattern, **kwargs):
        with self.assertRaisesRegex(CP.PackError, pattern):
            self.install_zip(kind, members, **kwargs)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "victim", "web")))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "evil.txt")))

    def test_paths_that_leave_the_target(self):
        self.refused("web", ["web/../../evil.txt"], "unsafe path")
        self.refused("web", ["../evil.txt"], "unsafe path")
        self.refused("web", ["/etc/evil.txt"], "unsafe path")
        self.refused("web", ["web\\..\\evil.txt"], "unsafe path")
        self.refused("web", ["C:/evil.txt"], "unsafe path")

    def test_entries_of_another_place(self):
        self.refused("web", ["web/ok.txt", "elsewhere/x.txt"], "outside web/")
        self.refused("source", ["mia.blend", "extra.txt"], "other than mia.blend")
        self.refused("source", ["sub/mia.blend"], "other than mia.blend")

    def test_links(self):
        link = zipfile.ZipInfo("web/link", (2000, 1, 1, 0, 0, 0))
        link.external_attr = (0o120777 << 16)
        self.refused("web", [link], "contains a link")

    def test_a_size_beyond_the_limit(self):
        self.refused("web", ["web/a.bin"], "unpack to", max_bytes=3)

    def test_an_empty_zip(self):
        self.refused("web", [], "empty")


class Commands(Base):
    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        old = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = CP.main(list(args))
        finally:
            sys.stdout, sys.stderr = old
        return code, out.getvalue(), err.getvalue()

    def test_pack_all_skips_the_source_when_there_is_no_blend(self):
        os.remove(self.blend)
        code, out, _ = self.run_main("pack", "all", "--folder", self.folder)
        self.assertEqual(code, 0)
        self.assertIn("source: skipped", out)
        self.assertIn("upload", out)
        self.assertIn("web", self.manifest())
        self.assertNotIn("source", self.manifest())

    def test_install_all_installs_the_web_pack_and_skips_a_missing_source(self):
        CP.pack("web", self.folder)
        CP.pack("source", self.folder)
        other, target = self.other_machine()
        os.remove(os.path.join(other, self.manifest()["source"]["file"]))
        CP.WEB_DIR = target
        code, out, err = self.run_main("install", "all", "--folder", other)
        self.assertEqual((code, err), (0, ""))
        self.assertIn("unpacked", out)
        self.assertIn("source: skipped", out)

    def test_errors_go_to_stderr_with_a_nonzero_code(self):
        code, out, err = self.run_main("install", "web", "--folder", self.folder)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("error:", err)

    def test_status_tells_what_is_where(self):
        CP.pack("web", self.folder)
        CP.pack("source", self.folder)
        _, out, _ = self.run_main("status", "--folder", self.folder)
        self.assertIn("web", out)
        self.assertIn("checksum matches", out)
        self.assertIn("same as the pack", out)
        os.remove(os.path.join(self.folder, self.manifest()["web"]["file"]))
        self.assertIn("not in the folder", "\n".join(CP.status(self.folder)))


if __name__ == "__main__":
    unittest.main()
