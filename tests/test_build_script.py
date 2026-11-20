"""deploy/build.sh TAG: builds the mia image only from a clean checkout of exactly that tag (deploy gap of v0.2.1, amendment A-BUILD).
Run with: python tests/test_build_script.py
A fake podman on PATH records its calls, so no image is built.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SCRIPT = os.path.join(REPO, "deploy", "build.sh")

FAKE_PODMAN = """#!/bin/bash
echo "$@" >> "$CALLS"
case "$1" in
  image) echo "sha256:abc123" ;;
esac
"""


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


class BuildScript(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(os.path.join(self.repo, "deploy"))
        for name in ("build.sh", "Containerfile"):
            src = SCRIPT if name == "build.sh" else os.path.join(REPO, "deploy", name)
            if os.path.exists(src):
                shutil.copy(src, os.path.join(self.repo, "deploy", name))
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-qm", "x")
        git(self.repo, "tag", "v9.9.9")
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        fake = os.path.join(self.bin, "podman")
        with open(fake, "w") as fp:
            fp.write(FAKE_PODMAN)
        os.chmod(fake, 0o755)
        self.calls = os.path.join(self.tmp, "calls")

    def run_build(self, *args):
        env = {**os.environ, "PATH": self.bin + os.pathsep + os.environ["PATH"], "CALLS": self.calls}
        return subprocess.run(["bash", os.path.join(self.repo, "deploy", "build.sh"), *args], cwd=self.repo, env=env, capture_output=True, text=True)

    def podman_calls(self):
        if not os.path.exists(self.calls):
            return []
        with open(self.calls) as fp:
            return fp.read().splitlines()

    def test_builds_from_tag_without_pull(self):
        res = self.run_build("v9.9.9")
        self.assertEqual(res.returncode, 0, res.stderr)
        calls = self.podman_calls()
        build = [c for c in calls if c.startswith("build")]
        self.assertEqual(len(build), 1)
        self.assertIn("--pull=never", build[0])
        self.assertIn("localhost/mia:v9.9.9", build[0])
        self.assertTrue(any(c.startswith("tag") and "localhost/mia:latest" in c for c in calls))
        self.assertIn("sha256:abc123", res.stdout)

    def test_refuses_without_tag_argument(self):
        res = self.run_build()
        self.assertNotEqual(res.returncode, 0)
        self.assertEqual(self.podman_calls(), [])

    def test_refuses_when_head_is_not_the_tag(self):
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "later")
        res = self.run_build("v9.9.9")
        self.assertNotEqual(res.returncode, 0)
        self.assertEqual(self.podman_calls(), [])

    def test_refuses_dirty_tree(self):
        with open(os.path.join(self.repo, "deploy", "Containerfile"), "a") as fp:
            fp.write("# change\n")
        res = self.run_build("v9.9.9")
        self.assertNotEqual(res.returncode, 0)
        self.assertEqual(self.podman_calls(), [])


if __name__ == "__main__":
    unittest.main()
