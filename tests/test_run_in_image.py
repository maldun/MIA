"""
F17 of the N-2.4.1 verification, D-132: the scripts that run the checkout in the MIA image mount it with the shared SELinux label (:z, not :Z, which relabels
the folder for one container and locks out the runs in parallel and the other worktrees: "Permission denied"), and run_in_image.sh starts an init process
(--init, so that a killed child is reaped and test_shutdown sees it gone). Run with: python tests/test_run_in_image.py
"""
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = ("tools/run_in_image.sh", "tools/check_accounts_real.sh")


def mounts(path):
    return re.findall(r'-v "\$PWD:/work:(\w+)"', open(os.path.join(REPO, path), encoding="utf-8").read())


class RunInImageTests(unittest.TestCase):
    def test_the_checkout_is_mounted_with_the_shared_label(self):
        """F17: every mount of the checkout is labelled shared (:z), so parallel runs do not lock each other out.

        Example: tools/run_in_image.sh -> ["z"]; tools/check_accounts_real.sh -> ["z"]
        """
        for path in SCRIPTS:
            # Given: a script that mounts the checkout, When: its mounts are read
            found = mounts(path)
            # Then: there is one, and it is shared
            self.assertEqual(found, ["z"], path)

    def test_the_tests_run_with_an_init_process(self):
        """D-132: run_in_image.sh starts the container with --init.

        Example: the podman run line of tools/run_in_image.sh contains --init
        """
        # Given: the script, When: its podman run line is read
        line = next(l for l in open(os.path.join(REPO, "tools/run_in_image.sh"), encoding="utf-8") if "podman run" in l and not l.lstrip().startswith("#"))
        # Then: it has --init
        self.assertIn("--init", line)


if __name__ == "__main__":
    unittest.main()
