"""
N-2.1, the stage-3 step container-alone of amendment A-64 (D-169): tools/container_alone.sh runs TC-API-013 and counts a skip as a failure,
like the step contract-postgres of A-59. The test itself is replaced by a fake python that prints what unittest would print.
Run: python tests/test_container_alone_step.py
"""
import os
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

STEP = os.path.join(REPO, "tools", "container_alone.sh")


def run_step_with(summary, code):
    """runs the step with a fake python that prints `summary` on stderr (as unittest does) and exits with `code`; returns (exit code, output)"""
    folder = tempfile.mkdtemp()
    fake = os.path.join(folder, "python")
    with open(fake, "w") as fp:
        fp.write("#!/bin/sh\necho 'Ran 2 tests in 1.0s' >&2\necho '' >&2\necho '%s' >&2\nexit %d\n" % (summary, code))
    os.chmod(fake, stat.S_IRWXU)
    done = subprocess.run(["bash", STEP], capture_output=True, text=True, env=dict(os.environ, MIA_STEP_PYTHON=fake), timeout=60)
    return done.returncode, done.stdout + done.stderr


class ContainerAloneStep(unittest.TestCase):
    @mark.req("REQ-API-013")
    def test_a_skip_of_tc_api_013_fails_the_step(self):
        """A-64 (D-169): without podman or the image TC-API-013 skips; the stage step then fails instead of passing without evidence.

        Example: the test prints "OK (skipped=2)" and exits 0 -> the step exits 1 and says the test was skipped.
        """
        # When: the test skips
        code, out = run_step_with("OK (skipped=2)", 0)
        # Then: the step fails and says why
        self.assertEqual(code, 1, out)
        self.assertIn("skipped", out)

    @mark.req("REQ-API-013")
    def test_the_step_passes_and_fails_with_the_test(self):
        """A-64 (D-169): a test that ran passes the step; a failing test fails it.

        Example: "OK" with exit 0 -> step 0; "FAILED (failures=1)" with exit 1 -> step 1.
        """
        # When / Then: the test passed
        self.assertEqual(run_step_with("OK", 0)[0], 0)
        # When / Then: the test failed
        self.assertEqual(run_step_with("FAILED (failures=1)", 1)[0], 1)


if __name__ == "__main__":
    unittest.main()
