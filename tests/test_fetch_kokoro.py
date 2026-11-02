"""tools/fetch_kokoro.sh: download of the Kokoro voice files, checked by hash. A file:// base stands in for GitHub; no network."""
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                          # noqa: E402

FILES = {"kokoro-v1.0.onnx": b"model bytes", "voices-v1.0.bin": b"voice bytes"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Fetch(unittest.TestCase):

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.dst = os.path.join(tempfile.mkdtemp(), "kokoro")
        for name, data in FILES.items():
            with open(os.path.join(self.src, name), "wb") as fp:
                fp.write(data)

    def run_script(self, **extra):
        env = dict(os.environ, MIA_KOKORO_BASE_URL="file://" + self.src, KOKORO_SHA_ONNX=sha(FILES["kokoro-v1.0.onnx"]), KOKORO_SHA_VOICES=sha(FILES["voices-v1.0.bin"]))
        env.update(extra)
        return subprocess.run(["bash", os.path.join(REPO, "tools", "fetch_kokoro.sh"), self.dst], capture_output=True, text=True, env=env)

    @mark.req("REQ-OPR-001")
    def test_it_downloads_both_files_and_a_second_run_downloads_nothing(self):
        """Given an empty folder, When the script runs twice, Then both files are there and the second run says they are in place"""
        first = self.run_script()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        for name, data in FILES.items():
            with open(os.path.join(self.dst, name), "rb") as fp:
                self.assertEqual(fp.read(), data)
        for name in FILES:                           # a changed source must not be fetched again
            with open(os.path.join(self.src, name), "wb") as fp:
                fp.write(b"other")
        second = self.run_script()
        self.assertEqual(second.returncode, 0)
        self.assertIn("in place", second.stdout)
        with open(os.path.join(self.dst, "voices-v1.0.bin"), "rb") as fp:
            self.assertEqual(fp.read(), FILES["voices-v1.0.bin"])

    @mark.req("REQ-OPR-001")
    def test_a_wrong_hash_stops_and_leaves_no_file(self):
        """Given a download whose hash differs, When the script runs, Then it exits 1 and the target holds no such file"""
        out = self.run_script(KOKORO_SHA_ONNX="0" * 64)
        self.assertEqual(out.returncode, 1)
        self.assertIn("hash", out.stdout + out.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.dst, "kokoro-v1.0.onnx")))


if __name__ == "__main__":
    unittest.main()
