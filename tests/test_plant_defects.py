"""tools/plant_defects.py: plant each deliberate defect, run the checks, restore, and say which defect no check caught.
Run with: python tests/test_plant_defects.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(os.path.dirname(HERE), "tools", "plant_defects.py")

MODULE = "def answer():\n    return 1\n"
CHECK = """import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import m

class Answer(unittest.TestCase):
    def test_TC_X_001_the_answer(self):
        self.assertEqual(m.answer(), 1)

if __name__ == "__main__":
    unittest.main()
"""


class PlantDefects(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="plant-")
        self.addCleanup(shutil.rmtree, self.root, True)
        with open(os.path.join(self.root, "m.py"), "w") as f:
            f.write(MODULE)
        os.makedirs(os.path.join(self.root, "tests"))
        with open(os.path.join(self.root, "tests", "check_m.py"), "w") as f:
            f.write(CHECK)

    def plant(self, defects):
        path = os.path.join(self.root, "defects.json")
        with open(path, "w") as f:
            json.dump(defects, f)
        return subprocess.run([sys.executable, TOOL, path, "--root", self.root], capture_output=True, text=True, timeout=120)

    def defect(self, name, new, old="    return 1\n"):
        return {"name": name, "file": "m.py", "old": old, "new": new, "checks": ["tests/check_m.py"]}

    def test_a_caught_defect_names_its_failing_check_and_the_file_is_restored(self):
        """Example: return 1 -> return 2 is caught by test_TC_X_001_the_answer; m.py is byte for byte as before; exit 0."""
        done = self.plant([self.defect("wrong answer", "    return 2\n")])
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("| wrong answer | test_TC_X_001_the_answer |", done.stdout)
        with open(os.path.join(self.root, "m.py")) as f:
            self.assertEqual(f.read(), MODULE)

    def test_a_defect_no_check_catches_is_named_and_the_exit_code_is_1(self):
        """Example: a change with no effect -> "NOT CAUGHT", exit 1."""
        done = self.plant([self.defect("no effect", "    return 1  # same\n")])
        self.assertEqual(done.returncode, 1, done.stdout + done.stderr)
        self.assertIn("| no effect | NOT CAUGHT |", done.stdout)

    def test_a_same_size_defect_is_not_hidden_by_old_bytecode(self):
        """The finding of TRANSFER T-06: a restore in the same second with the same size left stale bytecode.
        Example: the check ran once (bytecode of the right code exists), then 1 -> 2 (same size) is planted twice in a row: caught both times."""
        subprocess.run([sys.executable, os.path.join(self.root, "tests", "check_m.py")], capture_output=True, timeout=60)
        done = self.plant([self.defect("first", "    return 2\n"), self.defect("second", "    return 3\n")])
        self.assertIn("| first | test_TC_X_001_the_answer |", done.stdout)
        self.assertIn("| second | test_TC_X_001_the_answer |", done.stdout)
        # and after the run the right code runs again
        after = subprocess.run([sys.executable, os.path.join(self.root, "tests", "check_m.py")], capture_output=True, text=True, timeout=60)
        self.assertEqual(after.returncode, 0, after.stderr)

    def test_an_old_text_that_is_not_found_once_is_refused_and_nothing_is_planted(self):
        """Example: old text missing -> "old text found 0 times", exit 2, m.py unchanged."""
        done = self.plant([self.defect("missing", "x", old="return 7")])
        self.assertEqual(done.returncode, 2, done.stdout + done.stderr)
        self.assertIn("old text found 0 times", done.stdout + done.stderr)
        with open(os.path.join(self.root, "m.py")) as f:
            self.assertEqual(f.read(), MODULE)


if __name__ == "__main__":
    unittest.main()
