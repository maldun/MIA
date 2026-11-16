"""
The converted-skill tests (test_control_entries, test_converted_tools, test_core_converted, test_harness_converted) import MIA's code by its plain module names and register their node call on the plain
`common_operations`; the code that a transform runs does `from MIA import common_operations` first. After any other test has made the package `MIA` importable (checkout_copy.use(), `import MIA.x`) that import
succeeds and gives a second `common_operations` without the registered call: "no node call is registered", runs that end `failed`. These checks run the four modules in a fresh process after such a test (F-3 of
G-V3.REPORT: 12 failures that appeared only in a full run). Run with the MIA virtualenv: python tests/test_converted_isolation.py
"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FOUR = ["test_control_entries", "test_converted_tools", "test_core_converted", "test_harness_converted"]
POLLUTE = """
import os, sys, tempfile, unittest
link = tempfile.mkdtemp()
os.symlink(%(repo)r, os.path.join(link, "MIA"))
sys.path[:0] = [link, %(repo)r, %(tests)r, os.path.join(%(tests)r, "helpers")]
import MIA.common_operations
result = unittest.main(module=None, argv=["x"] + %(modules)r, exit=False, verbosity=0).result
sys.exit(0 if result.wasSuccessful() else 1)
"""


def run_in_fresh_process(code):
    """(exit code, last lines of the output) of a fresh Python that runs `code` from the tests folder"""
    done = subprocess.run([sys.executable, "-c", code], cwd=HERE, capture_output=True, text=True, timeout=300)
    return done.returncode, (done.stdout + done.stderr)[-600:]


class ConvertedTestsDoNotDependOnThePackageBeingImportable(unittest.TestCase):
    def test_the_four_modules_pass_after_the_package_was_imported(self):
        """F-3: the four converted-skill modules pass in a process in which the package MIA was imported before them.
        Example: `import MIA.common_operations` through a package link, then the four modules: 34 tests OK (before the fix: 11 failures, 1 error)."""
        # Given: a fresh process in which the package MIA is importable and was imported
        code = POLLUTE % {"repo": REPO, "tests": HERE, "modules": FOUR}
        # When: the four modules run in it
        status, output = run_in_fresh_process(code)
        # Then: they all pass
        self.assertEqual(status, 0, output)

    def test_the_four_modules_pass_after_the_character_integration_test(self):
        """F-3: the four modules pass in the same process after test_character_integration, which imports MIA.web_app (the module that polluted the full run).
        Example: test_character_integration, then the four modules, one process: OK (before the fix: 11 failures, 1 error)."""
        # Given: the test that imports the package, and the four modules, in one run
        code = "import sys, unittest; sys.path[:0] = [%r, %r]; r = unittest.main(module=None, argv=['x', 'test_character_integration'] + %r, exit=False, verbosity=0).result; sys.exit(0 if r.wasSuccessful() else 1)" % (HERE, os.path.join(HERE, "helpers"), FOUR)
        # When: they run in one fresh process
        status, output = run_in_fresh_process(code)
        # Then: they all pass
        self.assertEqual(status, 0, output)


if __name__ == "__main__":
    unittest.main()
