"""
tools/amendment_report.py: the readable preview of an amendment in the shell (the owner's wish of 2026-10-29): changed words marked inside the line, requirement files by requirement,
tables and code by line with numbers, long unchanged runs folded, the generated model block only counted; colours only when asked or on a terminal.
Run: python tests/test_amendment_report.py
"""
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))

import amendment_report as R  # noqa: E402

OLD_REQ = """# Requirements

### REQ-WFM-001 – Skills as tasks
- Text: The Workflow management shall perform each kind of work as a task.
- Status: Approved

### REQ-WFM-034 – Run mode
- Text: The Workflow management shall run a task with a hard cap of 600 seconds and no question.
- Acceptance criterion: AC-3: the run ends at the cap
- Status: Draft
- History: A-23 new

### REQ-WFM-040 – Gone soon
- Text: Old.
- Status: Draft
"""
NEW_REQ = """# Requirements

### REQ-WFM-001 – Skills as tasks
- Text: The Workflow management shall perform each kind of work as a task.
- Status: Approved

### REQ-WFM-034 – Run mode and caps
- Text: The Workflow management shall run a task with a hard cap of 1800 seconds and a question at the cap.
- Acceptance criterion: AC-3: the run ends at the cap
- Status: Draft
- History: A-23 new; A-27 reworded

### REQ-WFM-039 – Skills are extensions
- Text: A new requirement.
- Status: Draft
"""


class WordDiff(unittest.TestCase):
    def test_changed_words_are_marked_inside_the_line(self):
        self.assertEqual(R.word_diff("the cap is 600 s", "the cap is 1800 s"), "the cap is [-600-]{+1800+} s")
        self.assertEqual(R.word_diff("same text", "same text"), "same text")
        self.assertEqual(R.word_diff("a b c", "a c"), "a [-b -]c")
        self.assertEqual(R.word_diff("a c", "a b c"), "a {+b +}c")

    def test_colours_only_when_asked(self):
        self.assertNotIn("\x1b[", R.word_diff("a 1 b", "a 2 b"))
        self.assertIn("\x1b[", R.word_diff("a 1 b", "a 2 b", color=True))


class Requirements(unittest.TestCase):
    def setUp(self):
        self.out = R.report_text(OLD_REQ, NEW_REQ, "requirements.md")

    def test_a_changed_requirement_shows_its_changed_fields_with_the_changed_words(self):
        self.assertIn("REQ-WFM-034", self.out)
        self.assertIn("Run mode{+ and caps+}", self.out)                          # the title changed too
        self.assertIn("[-600-]{+1800+}", self.out)
        self.assertIn("History: A-23 new{+; A-27 reworded+}", self.out)

    def test_an_unchanged_field_and_an_unchanged_requirement_are_not_repeated(self):
        self.assertNotIn("REQ-WFM-001", self.out)
        self.assertNotIn("Acceptance criterion", self.out)

    def test_new_and_removed_requirements_are_named_as_such(self):
        self.assertRegex(self.out, r"\+ new\s+REQ-WFM-039")
        self.assertRegex(self.out, r"- removed\s+REQ-WFM-040")
        self.assertIn("A new requirement.", self.out)


class Rewritten(unittest.TestCase):
    """a sentence that was rewritten is shown as the old and the new text, not as a mosaic of marked words"""

    def test_a_small_change_stays_inline_and_a_rewrite_is_shown_as_two_lines(self):
        old = "- Text: The Workflow management shall run a task with a hard cap of 600 seconds and no question.\n"
        small = old.replace("600", "1800")
        out = R.report_text("### REQ-A-1 – T\n" + old, "### REQ-A-1 – T\n" + small, "N23-requirements.md")
        self.assertIn("[-600-]{+1800+}", out)
        rewritten = "- Text: At a cap of thirty minutes of work time the user decides whether to continue, to summarize or to stop; nothing else is asked.\n"
        out = R.report_text("### REQ-A-1 – T\n" + old, "### REQ-A-1 – T\n" + rewritten, "N23-requirements.md")
        self.assertNotIn("[-", out)
        self.assertRegex(out, r"(?m)^\s+- The Workflow management shall run a task")
        self.assertRegex(out, r"(?m)^\s+\+ At a cap of thirty minutes")

    def test_the_requirement_view_is_chosen_by_the_name_of_the_draft_too(self):
        out = R.report_text("### REQ-A-1 – T\n- Text: a\n", "### REQ-A-1 – T\n- Text: b\n", "specs/mia/amendments/A-27/N23-requirements.md")
        self.assertIn("REQ-A-1", out)
        self.assertIn("changed", out)


class Colours(unittest.TestCase):
    """the owner's wish of 2026-10-29: additions and removals colour coded, the key fields (Text, History, Acceptance criterion) highlighted"""
    REMOVED, ADDED, KEY = "\x1b[1;37;41m", "\x1b[1;30;42m", "\x1b[1;36m"

    def setUp(self):
        self.out = R.report_text(OLD_REQ, NEW_REQ, "requirements.md", color=True)

    def test_removed_words_are_red_and_added_words_green_with_a_background(self):
        self.assertIn(self.REMOVED + "[-600-]", self.out)
        self.assertIn(self.ADDED + "{+1800+}", self.out)

    def test_the_key_fields_are_highlighted_and_the_others_are_not(self):
        self.assertIn(self.KEY + "Text:", self.out)
        self.assertIn(self.KEY + "History:", self.out)
        self.assertNotIn(self.KEY + "Status:", self.out)
        self.assertNotIn(self.KEY + "Rationale:", self.out)
        out = R.report_text(OLD_REQ.replace("AC-3: the run ends at the cap", "AC-3: x"), NEW_REQ, "requirements.md", color=True)
        self.assertIn(self.KEY + "Acceptance criterion:", out)

    def test_new_and_removed_requirements_have_their_own_colours(self):
        self.assertIn("\x1b[1;32m+ new", self.out)
        self.assertIn("\x1b[1;31m- removed", self.out)

    def test_without_colours_nothing_is_painted(self):
        self.assertNotIn("\x1b[", R.report_text(OLD_REQ, NEW_REQ, "requirements.md", color=False))


class FromGit(unittest.TestCase):
    """--git COMMIT: what an installed amendment (or any commit) changed, in the same readable form"""

    def test_the_files_of_a_commit_are_shown_one_after_the_other(self):
        with tempfile.TemporaryDirectory() as tmp:
            def git(*args):
                return subprocess.run(["git", "-C", tmp, "-c", "user.email=a@b", "-c", "user.name=t", *args], capture_output=True, text=True, check=True).stdout
            git("init", "-q")
            os.makedirs(os.path.join(tmp, "specs"))
            with open(os.path.join(tmp, "specs", "requirements.md"), "w") as fp:
                fp.write(OLD_REQ)
            with open(os.path.join(tmp, "notes.md"), "w") as fp:
                fp.write("cap 600 s\n")
            git("add", "-A")
            git("commit", "-q", "-m", "one")
            with open(os.path.join(tmp, "specs", "requirements.md"), "w") as fp:
                fp.write(NEW_REQ)
            with open(os.path.join(tmp, "notes.md"), "w") as fp:
                fp.write("cap 1800 s\n")
            with open(os.path.join(tmp, "added.txt"), "w") as fp:
                fp.write("hello\n")
            git("add", "-A")
            git("commit", "-q", "-m", "two")
            done = subprocess.run([sys.executable, os.path.join(REPO, "tools", "amendment_report.py"), "--git", "HEAD", "--repo", tmp, "--color", "never"], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("specs/requirements.md", done.stdout)
            self.assertIn("~ changed  REQ-WFM-034", done.stdout)
            self.assertIn("cap [-600-]{+1800+} s", done.stdout)
            self.assertRegex(done.stdout, r"added.txt.*\n.*new file")


class Lines(unittest.TestCase):
    def test_a_changed_line_has_its_number_and_the_changed_words(self):
        old = "".join("line %d\n" % i for i in range(1, 31))
        new = old.replace("line 15\n", "line 15 has 1800 seconds\n").replace("line 25\n", "")
        out = R.report_text(old, new, "notes.md", context=1)
        self.assertRegex(out, r"~\s+15: line 15\{\+ has 1800 seconds\+\}")
        self.assertRegex(out, r"-\s+25: line 25")
        self.assertIn("unchanged lines", out)                                   # the long runs between the hunks are folded
        self.assertNotIn("line 5\n", out)

    def test_a_table_row_is_shown_as_a_line_with_the_changed_cell_marked(self):
        old = "| a | b |\n|---|---|\n| `x` | cap 600 s |\n"
        new = "| a | b |\n|---|---|\n| `x` | cap 1800 s |\n"
        self.assertIn("| `x` | cap [-600-]{+1800+} s |", R.report_text(old, new, "IF-101.md"))

    def test_identical_text_says_so_and_a_missing_installed_file_says_new(self):
        self.assertEqual(R.report_text("a\n", "a\n", "x.md").strip(), "no difference")
        out = R.report_text(None, "# Title\nline\n", "deferred.md")
        self.assertIn("new file", out)
        self.assertIn("2 lines", out)
        self.assertIn("# Title", out)


class Model(unittest.TestCase):
    def test_the_generated_block_of_the_model_is_only_counted(self):
        head = "package X {\n  part a;\n"
        gen_old = "// BEGIN GENERATED: node requirements\nreq 1\nreq 2\n// END GENERATED: node requirements\n"
        gen_new = "// BEGIN GENERATED: node requirements\nreq 1\nreq 2 changed\nreq 3\n// END GENERATED: node requirements\n"
        out = R.report_text(head + gen_old + "}\n", head.replace("part a", "part b") + gen_new + "}\n", "architecture.sysml")
        self.assertIn("generated block", out)
        self.assertIn("+2 -1", out)
        self.assertNotIn("req 3", out)                                          # not listed line by line
        self.assertIn("part [-a-]{+b+}", out)                                   # the hand-written part is shown


class CommandLine(unittest.TestCase):
    def test_the_command_reads_two_files_and_prints_the_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = os.path.join(tmp, "installed.md"), os.path.join(tmp, "draft.md")
            open(old, "w").write("cap 600 s\n")
            open(new, "w").write("cap 1800 s\n")
            done = subprocess.run([sys.executable, os.path.join(REPO, "tools", "amendment_report.py"), old, new, "--color", "never"], capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("cap [-600-]{+1800+} s", done.stdout)
            missing = subprocess.run([sys.executable, os.path.join(REPO, "tools", "amendment_report.py"), os.path.join(tmp, "nope"), new, "--color", "never"], capture_output=True, text=True)
            self.assertIn("new file", missing.stdout)


if __name__ == "__main__":
    unittest.main()
