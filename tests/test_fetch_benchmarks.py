"""Tests for tools/fetch_benchmarks.py with local files as the source (no network).
Run: python tests/test_fetch_benchmarks.py"""
import io, json, os, sys, tarfile, tempfile, unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import fetch_benchmarks as FB  # noqa: E402


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.src = self.tmp / "src"
        self.src.mkdir()

    def test_plain_file_is_kept_with_hash_and_manifest(self):
        (self.src / "a.json").write_text('{"x": 1}')
        sets = {"demo": ("note", [(self.src / "a.json").as_uri()])}
        rows = FB.fetch("demo", self.tmp / "out", sets)
        self.assertEqual((self.tmp / "out/demo/a.json").read_text(), '{"x": 1}')
        self.assertEqual(rows[0]["sha256"], FB.sha256(self.tmp / "out/demo/a.json"))
        self.assertEqual(json.loads((self.tmp / "out/MANIFEST.json").read_text())["demo"]["licence_note"], "note")

    def test_tarball_is_unpacked_and_escaping_path_refused(self):
        good, bad = self.src / "good.tar.gz", self.src / "bad.tar.gz"
        for path, member in ((good, "dir/f.txt"), (bad, "../escape.txt")):
            with tarfile.open(path, "w:gz") as t:
                info = tarfile.TarInfo(member)
                info.size = 2
                t.addfile(info, io.BytesIO(b"hi"))
        FB.fetch("g", self.tmp / "out", {"g": ("n", [good.as_uri()])})
        self.assertTrue((self.tmp / "out/g/dir/f.txt").exists())
        with self.assertRaises(Exception):
            FB.fetch("b", self.tmp / "out", {"b": ("n", [bad.as_uri()])})
        self.assertFalse((self.tmp / "out/escape.txt").exists())

    def test_unknown_set_is_refused(self):
        self.assertEqual(FB.main(["fetch", "nope"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=1)
