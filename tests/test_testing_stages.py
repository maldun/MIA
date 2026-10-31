"""
The test stages of tools/start_testing.sh (tools/testing_stages.d/): the stage full-app starts the compose stack through deploy/up.sh with exactly the
arguments it was given. Found by the owner on 2026-10-31: without MIA_GPU the stage passed an empty argument, and up.sh handed it to podman-compose as
its command ("invalid choice: ''"). The stage runs from a temporary copy next to a fake deploy/up.sh that records its arguments.
The owner's check A4 (D-154, D-157) ran against another checkout than the one meant: start and status say which folder and commit they serve,
and for a stage container that runs already the folder it really mounts, with a warning when that is not this checkout (R2, D-165).
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

    @unittest.skipUnless(shutil.which("git"), "needs git (the test image has none); runs on the host")
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


# A fake podman for a stage container that runs already: it renders the templates of _common.sh as podman does for a container that mounts
# FAKE_MOUNT on /opt/mia/MIA, with ":O" (an overlay: the source is podman's merge folder, the checkout is the lowerdir option) or as a plain bind.
FAKE_PODMAN = r"""#!/usr/bin/env bash
[ "$1 $2" = "image exists" ] && exit 0
if [ "$1" = inspect ]; then
    case "$3" in
        *State.Running*) echo true ;;
        *Mounts*) if [ "$FAKE_OVERLAY" = 1 ]; then printf 'lowerdir=%s\nupperdir=/s/upper\nworkdir=/s/work\nsource=/s/merge\n' "$FAKE_MOUNT"
                  else printf 'rbind\nsource=%s\n' "$FAKE_MOUNT"; fi ;;
    esac
    exit 0
fi
echo "unexpected: podman $*" >&2; exit 1
"""


class RunningContainerStage(unittest.TestCase):
    """start_testing.sh with the real stage chat-on-stub, whose container runs already (a fake podman on PATH), in a folder without git"""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        os.makedirs(os.path.join(self.root, "tools", "testing_stages.d"))
        os.makedirs(os.path.join(self.root, "bin"))
        shutil.copy(os.path.join(REPO, "tools", "start_testing.sh"), os.path.join(self.root, "tools", "start_testing.sh"))
        for name in ("_common.sh", "10-chat-on-stub.sh"):
            shutil.copy(os.path.join(STAGES, name), os.path.join(self.root, "tools", "testing_stages.d", name))
        podman = os.path.join(self.root, "bin", "podman")
        with open(podman, "w", encoding="utf-8") as fp:
            fp.write(FAKE_PODMAN)
        os.chmod(podman, 0o755)

    def script(self, command, mount, overlay):
        environment = dict(os.environ, MIA_TESTING_DIR=os.path.join(self.root, "state"), FAKE_MOUNT=mount, FAKE_OVERLAY="1" if overlay else "0",
                           PATH=os.path.join(self.root, "bin") + os.pathsep + os.environ.get("PATH", ""))
        args = [command, "chat-on-stub"] if command == "start" else [command]
        return subprocess.run(["bash", os.path.join(self.root, "tools", "start_testing.sh"), *args], env=environment, capture_output=True,
                              text=True, timeout=30).stdout

    def test_start_names_the_folder_a_running_stage_serves_and_warns_when_it_is_another_checkout(self):
        """R2 (D-165): start on a stage whose container runs already names the folder the container mounts and warns that it is not this checkout.

        Example: container started from /home/me/MIA (":O" mount), start in /tmp/abc -> "mia-test-chat-on-stub is running already,
        serving /home/me/MIA" and a WARNING naming /tmp/abc.
        """
        # Given: the stage's container runs already and mounts another checkout (overlay mount, as start_container makes it)
        other = "/home/someone/MIA"
        # When: the stage is started from this checkout
        started = self.script("start", other, overlay=True)
        # Then: the running line names the mounted folder, and a warning says it is not this checkout
        self.assertIn("mia-test-chat-on-stub is running already, serving %s" % other, started)
        self.assertIn("WARNING", started)
        self.assertIn("not this checkout %s" % self.root, started)

    def test_status_names_the_folder_a_running_stage_serves_and_warns_when_it_is_another_checkout(self):
        """R2 (D-165): status names the folder the running container mounts, with the same warning.

        Example: container from /home/me/MIA, status in /tmp/abc -> "running: http://..., serving /home/me/MIA" and a WARNING.
        """
        # Given: the stage's container runs and mounts another checkout
        other = "/home/someone/MIA"
        # When: the status is asked from this checkout
        status = self.script("status", other, overlay=True)
        # Then: the stage's line names the mounted folder, and a warning follows
        self.assertIn(", serving %s" % other, status)
        self.assertIn("not this checkout %s" % self.root, status)

    def test_a_running_stage_of_this_checkout_gives_no_warning(self):
        """A container that mounts this checkout (here as a plain bind) is named, without a warning, on start and on status.

        Example: container mounts /tmp/abc, start and status in /tmp/abc -> "serving /tmp/abc", no WARNING.
        """
        # Given: the stage's container runs and mounts this checkout
        # When: the stage is started and the status is asked
        started, status = self.script("start", self.root, overlay=False), self.script("status", self.root, overlay=False)
        # Then: both name this checkout as served, and neither warns
        self.assertIn("running already, serving %s" % self.root, started)
        self.assertIn(", serving %s" % self.root, status)
        self.assertNotIn("WARNING", started + status)


if __name__ == "__main__":
    unittest.main()
