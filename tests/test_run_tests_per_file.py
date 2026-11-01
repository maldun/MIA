"""
tools/run_tests_per_file.py: the stage `unit` runs every test file in its own process. The web_app module of MIA is a singleton: the first test that imports it fixes its
configuration (accounts on or off, the account store), so tests with different configurations pass alone and fail together in one `unittest discover` process (found by the
first merge gate run of G-V1, D-182).   python tests/test_run_tests_per_file.py
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                          # noqa: E402

RUNNER = os.path.join(REPO, "tools", "run_tests_per_file.py")
# two files that share a module-level state through a tiny module both import, like the two configurations of web_app.py
SHARED = "STATE = {'accounts': None}\n"
FIRST = textwrap.dedent('''
    import sys, unittest
    sys.path.insert(0, %r)
    import shared
    shared.STATE['accounts'] = shared.STATE['accounts'] or 'off'
    class First(unittest.TestCase):
        def test_accounts_are_off(self):
            self.assertEqual(shared.STATE['accounts'], 'off')
    if __name__ == '__main__':
        unittest.main()
''')
SECOND = textwrap.dedent('''
    import sys, unittest
    sys.path.insert(0, %r)
    import shared
    shared.STATE['accounts'] = shared.STATE['accounts'] or 'on'
    class Second(unittest.TestCase):
        def test_accounts_are_on(self):
            self.assertEqual(shared.STATE['accounts'], 'on')
    if __name__ == '__main__':
        unittest.main()
''')
BROKEN = textwrap.dedent('''
    import unittest
    class Broken(unittest.TestCase):
        def test_fails(self):
            self.assertEqual(1, 2)
    if __name__ == '__main__':
        unittest.main()
''')


def folder(**files):
    tests = tempfile.mkdtemp()
    with open(os.path.join(tests, "shared.py"), "w") as fp:
        fp.write(SHARED)
    for name, body in files.items():
        with open(os.path.join(tests, name + ".py"), "w") as fp:
            fp.write(body % tests if "%r" in body else body)
    return tests


def run(tests, *args, **env):
    return subprocess.run([sys.executable, RUNNER, tests, *args], capture_output=True, text=True, env=dict(os.environ, **env))


class PerFile(unittest.TestCase):
    @mark.req("REQ-OPR-001")
    def test_two_files_that_fail_together_pass_in_their_own_processes(self):
        """Given two test files with different states of one shared module, When unittest discover runs them in one process, Then one fails; When the runner runs them, Then both pass"""
        tests = folder(test_a_first=FIRST, test_b_second=SECOND)
        together = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", tests, "-q"], capture_output=True, text=True)
        self.assertNotEqual(together.returncode, 0)
        alone = run(tests)
        self.assertEqual(alone.returncode, 0, alone.stdout + alone.stderr)
        self.assertIn("2 file(s)", alone.stdout)

    @mark.req("REQ-OPR-001")
    def test_a_failing_file_is_named_and_the_runner_exits_one(self):
        """Given one failing and one passing file, When the runner runs, Then it exits 1 and names the failing file with its last lines"""
        tests = folder(test_a_first=FIRST, test_z_broken=BROKEN)
        out = run(tests)
        self.assertEqual(out.returncode, 1)
        self.assertIn("test_z_broken.py", out.stdout)
        self.assertIn("AssertionError", out.stdout)
        self.assertIn("1 failed", out.stdout)

    @mark.req("REQ-OPR-001")
    def test_parallel_workers_give_the_same_verdict_and_a_pattern_selects_files(self):
        """Given three files, When run with two workers and a pattern for two of them, Then the verdict is the same and only those two run"""
        tests = folder(test_a_first=FIRST, test_b_second=SECOND, test_z_broken=BROKEN)
        every = run(tests, MIA_UNIT_JOBS="2")
        self.assertEqual(every.returncode, 1)
        self.assertIn("3 file(s)", every.stdout)
        two = run(tests, MIA_UNIT_PATTERN="test_[ab]_*.py", MIA_UNIT_JOBS="2")
        self.assertEqual(two.returncode, 0, two.stdout)
        self.assertIn("2 file(s)", two.stdout)

    @mark.req("REQ-OPR-001")
    def test_a_file_that_hangs_is_stopped_and_counted_as_failed(self):
        """Given a file that never ends, When the runner has a timeout, Then the file is stopped, named as timed out, and the exit code is 1"""
        tests = folder(test_hang="import time\ntime.sleep(60)\n")
        out = run(tests, MIA_UNIT_TIMEOUT="2")
        self.assertEqual(out.returncode, 1)
        self.assertIn("timed out", out.stdout)

    @mark.req("REQ-OPR-001")
    def test_a_file_without_tests_is_a_failure(self):
        """Given a file that defines no test, When the runner runs, Then it exits 1: a file that runs nothing is not a pass"""
        tests = folder(test_nothing="X = 1\n")
        self.assertEqual(run(tests).returncode, 1)

    @mark.req("REQ-OPR-001")
    def test_an_empty_folder_is_an_error_not_a_green_stage(self):
        """Given a folder without test files, When the runner runs, Then it exits 1: nothing run is not a pass"""
        out = run(tempfile.mkdtemp())
        self.assertEqual(out.returncode, 1)


if __name__ == "__main__":
    unittest.main()
