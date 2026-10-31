"""
The test stages of tools/start_testing.sh (tools/testing_stages.d/): the stage full-app starts the compose stack through deploy/up.sh with exactly the
arguments it was given. Found by the owner on 2026-10-31: without MIA_GPU the stage passed an empty argument, and up.sh handed it to podman-compose as
its command ("invalid choice: ''"). The stage runs from a temporary copy next to a fake deploy/up.sh that records its arguments.
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


if __name__ == "__main__":
    unittest.main()
