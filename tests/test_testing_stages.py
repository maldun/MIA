"""
The test stages of tools/start_testing.sh (tools/testing_stages.d/): the stage full-app starts the compose stack through deploy/up.sh with exactly the
arguments it was given. Found by the owner on 2026-10-31: without MIA_GPU the stage passed an empty argument, and up.sh handed it to podman-compose as
its command ("invalid choice: ''"). The stage runs from a temporary copy next to a fake deploy/up.sh that records its arguments.
The owner's check A4 (D-154, D-157) ran against another checkout than the one meant: start and status say which folder and commit they serve.
Run with: python3 tests/test_testing_stages.py
"""
import os
import shutil
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGES = os.path.join(REPO, "tools", "testing_stages.d")
FAKE_UP = '#!/usr/bin/env bash\nprintf "%s|%s\\n" "$#" "$*" > "$(dirname "$0")/up.args"\n'


class FullAppStage(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.root, "tools", "testing_stages.d"))
        os.makedirs(os.path.join(self.root, "deploy"))
        for name in ("_common.sh", "20-full-app.sh"):
            shutil.copy(os.path.join(STAGES, name), os.path.join(self.root, "tools", "testing_stages.d", name))
        up = os.path.join(self.root, "deploy", "up.sh")
        with open(up, "w", encoding="utf-8") as fp:
            fp.write(FAKE_UP)
        os.chmod(up, 0o755)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def start(self, **env):
        environment = {k: v for k, v in os.environ.items() if k != "MIA_GPU"}
        environment.update(env, MIA_TESTING_DIR=os.path.join(self.root, "state"))
        subprocess.run(["bash", os.path.join(self.root, "tools", "testing_stages.d", "20-full-app.sh"), "start"], env=environment, check=True,
                       capture_output=True, timeout=30)
        with open(os.path.join(self.root, "deploy", "up.args"), encoding="utf-8") as fp:
            return fp.read().strip()

    def test_without_a_gpu_up_sh_gets_no_argument(self):
        """The owner's finding (2026-10-31): without MIA_GPU the stage calls up.sh with no argument at all, not with an empty one.

        Example: MIA_GPU unset -> up.sh sees 0 arguments
        """
        # Given: the stage next to a fake up.sh, When: it starts without MIA_GPU
        recorded = self.start()
        # Then: up.sh got no argument
        self.assertEqual(recorded, "0|")

    def test_with_a_gpu_up_sh_gets_it_as_its_one_argument(self):
        """MIA_GPU (rocm or nvidia) is passed to up.sh as its one argument.

        Example: MIA_GPU=rocm -> up.sh sees 1 argument, rocm
        """
        # Given: the stage next to a fake up.sh, When: it starts with MIA_GPU=rocm
        recorded = self.start(MIA_GPU="rocm")
        # Then: up.sh got exactly that argument
        self.assertEqual(recorded, "1|rocm")



DUMMY_STAGE = """#!/usr/bin/env bash
case "${1:-}" in
    describe) echo "a stage that does nothing" ;;
    available|auto) exit 0 ;;
    start) echo "dummy started" ;;
    stop) echo "dummy stopped" ;;
    status) echo "stopped" ;;
esac
"""


class ServedCheckout(unittest.TestCase):
    """start_testing.sh in a temporary git checkout on the branch goal/x with one dummy stage"""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "tools", "testing_stages.d"))
        shutil.copy(os.path.join(REPO, "tools", "start_testing.sh"), os.path.join(self.root, "tools", "start_testing.sh"))
        with open(os.path.join(self.root, "tools", "testing_stages.d", "10-dummy.sh"), "w", encoding="utf-8") as fp:
            fp.write(DUMMY_STAGE)

    def git(self, *args):
        return subprocess.run(["git", "-C", self.root, *args], check=True, capture_output=True, text=True).stdout.strip()

    def script(self, *args):
        environment = dict(os.environ, MIA_TESTING_DIR=os.path.join(self.root, "state"))
        return subprocess.run(["bash", os.path.join(self.root, "tools", "start_testing.sh"), *args], env=environment, capture_output=True,
                              text=True, timeout=30).stdout

    def commit(self):
        self.git("init", "-q", "-b", "goal/x")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-q", "-m", "x")
        return self.git("rev-parse", "--short", "HEAD")

    def test_start_and_status_say_which_folder_and_commit_they_serve(self):
        """A4 (D-157): start and status name the folder, the short commit and the branch of the checkout the stages serve.

        Example: a checkout /tmp/abc on goal/x at 1a2b3c4 -> "serving /tmp/abc at 1a2b3c4 (goal/x)" in the output of start and of status.
        """
        # Given: the script in a git checkout on the branch goal/x
        short = self.commit()
        expected = "serving %s at %s (goal/x)" % (self.root, short)
        # When: a stage is started and the status is asked
        started, status = self.script("start", "dummy"), self.script("status")
        # Then: both say which checkout they serve
        self.assertIn(expected, started)
        self.assertIn(expected, status)

    def test_a_folder_that_is_no_git_checkout_is_named_as_such(self):
        """A copy of the tree without git (e.g. git archive) is still named, and said to be no checkout.

        Example: /tmp/abc without .git -> "serving /tmp/abc (not a git checkout)".
        """
        # Given: the script in a folder without git
        # When: the status is asked
        status = self.script("status")
        # Then: the folder is named and said to be no checkout
        self.assertIn("serving %s (not a git checkout)" % self.root, status)


if __name__ == "__main__":
    unittest.main()
