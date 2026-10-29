"""
tools/amendment_lib.sh, the shared part of the amendment scripts: it names the compared files, shows the diff, counts the lines, changes nothing without --do,
leaves identical files alone and creates a missing installed file only with --do.
Run: python tests/test_amendment_lib.py
"""
import os
import subprocess
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(REPO, "tools", "amendment_lib.sh")


class Lib(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for name, text in (("installed1", "a\nb\nc\n"), ("draft1", "a\nB\nc\nd\n"), ("installed2", "same\n"), ("draft2", "same\n")):
            with open(os.path.join(self.tmp.name, name), "w") as fp:
                fp.write(text)
        self.script = os.path.join(self.tmp.name, "apply.sh")
        t = self.tmp.name
        with open(self.script, "w") as fp:
            fp.write(f'set -eu\n. {LIB}\namendment_args "$@"\ncopy {t}/draft1 {t}/installed1\ncopy {t}/draft2 {t}/installed2\ncopy {t}/draft1 {t}/missing\nfinish\necho FINISHED\n')

    def run_script(self, *args):
        done = subprocess.run(["bash", self.script, *args], capture_output=True, text=True)
        return done.returncode, done.stdout

    def read(self, name):
        with open(os.path.join(self.tmp.name, name)) as fp:
            return fp.read()

    def test_look_only_names_the_files_shows_the_diff_and_changes_nothing(self):
        code, out = self.run_script()
        self.assertEqual(code, 0)
        self.assertIn("mode: look only", out)
        self.assertIn("installed1   <-   ", out)                                   # the compared files, installed <- draft
        self.assertIn("DIFFERS: +2 -1 lines", out)
        self.assertIn("-b", out)
        self.assertIn("+B", out)
        self.assertIn("unchanged (identical)", out)
        self.assertIn("MISSING: the installed file does not exist", out)
        self.assertIn("══ compared 3 file(s)", out)
        self.assertIn("2 file(s) differ: run again with --do", out)
        self.assertNotIn("FINISHED", out)                                           # stops before what follows finish: nothing after a look-only run
        self.assertEqual(self.read("installed1"), "a\nb\nc\n")
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "missing")))

    def test_do_installs_and_reports_what_it_did(self):
        code, out = self.run_script("--do")
        self.assertEqual(code, 0)
        self.assertIn("-> updated", out)
        self.assertIn("-> created", out)
        self.assertIn("FINISHED", out)
        self.assertEqual(self.read("installed1"), "a\nB\nc\nd\n")
        self.assertEqual(self.read("missing"), "a\nB\nc\nd\n")

    def test_after_the_install_everything_is_unchanged(self):
        self.run_script("--do")
        code, out = self.run_script()
        self.assertEqual(code, 0)
        self.assertIn("nothing to do", out)
        self.assertNotIn("DIFFERS", out)

    def test_a_long_diff_is_cut_unless_full(self):
        with open(os.path.join(self.tmp.name, "draft1"), "w") as fp:
            fp.write("".join("line %d\n" % i for i in range(300)))
        _, out = self.run_script()
        self.assertIn("cut after 60 lines", out)
        _, out = self.run_script("--full")
        self.assertNotIn("cut after", out)
        self.assertIn("line 299", out)

    def test_an_unknown_option_is_refused(self):
        code, out = self.run_script("--oops")
        self.assertEqual(code, 2)


    def test_report_shows_the_changes_readably_and_changes_nothing(self):                  # owner's wish 2026-10-29
        code, out = self.run_script("--report")
        self.assertEqual(code, 0)
        self.assertIn("mode: look only", out)
        self.assertIn("DIFFERS: +2 -1 lines", out)                                       # the header of the file stays
        self.assertIn("- 2: b", out)                                                     # a line that changed completely: the old and the new line, with their numbers
        self.assertIn("+ 2: B", out)
        self.assertIn("+ 4: d", out)
        self.assertNotIn("--- installed:", out)                                          # not the unified diff
        self.assertEqual(self.read("installed1"), "a\nb\nc\n")

    def test_report_with_do_still_installs(self):
        code, out = self.run_script("--report", "--do")
        self.assertEqual(self.read("installed1"), "a\nB\nc\nd\n")


    def test_color_forces_the_colours_even_when_the_output_is_not_a_terminal(self):
        _code, out = self.run_script("--report", "--color")
        self.assertIn("\x1b[", out)
        _code, plain = self.run_script("--report")
        self.assertNotIn("\x1b[", plain)                                                # a pipe or a file gets no escape codes


if __name__ == "__main__":
    unittest.main()
