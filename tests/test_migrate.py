"""The migration command (N-3.1 T-05, file side) and the library export and seed commands (T-04): each direction is one command. Run with: python tests/test_migrate.py"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

import migrate                                    # noqa: E402
from markers import mark                          # noqa: E402
from storage import Storage                       # noqa: E402
from storage_files import FileBackend             # noqa: E402

from test_storage_copy import LOOKUP, tree        # noqa: E402


class Migrate(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base, True)
        self.data, self.db = os.path.join(self.base, "data"), os.path.join(self.base, "db")
        store = Storage(FileBackend(self.data))
        store.put("workflows", "lookup", LOOKUP, "anna")
        store.put("memory", "m", {"text": "t", "source": "chat"}, "anna")
        self.open_db = lambda url: FileBackend(self.db)           # stands in for the PostgreSQL backend until T-06

    def run_command(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = migrate.main(list(argv), open_db=self.open_db)
        return code, out.getvalue()

    @mark.req("REQ-SLY-007")
    def test_files_to_db_and_back_in_one_command_each_gives_identical_files(self):
        """TC-SLY-007 (file side): the data folder, moved and moved back into an empty folder, is identical file by file."""
        code, text = self.run_command("files-to-db", "--data", self.data, "--database-url", "postgresql://x")
        self.assertEqual(code, 0)
        self.assertIn("copied 2", text)
        back = os.path.join(self.base, "back")
        self.assertEqual(self.run_command("db-to-files", "--data", back, "--database-url", "postgresql://x")[0], 0)
        self.assertEqual(tree(back), tree(self.data))

    @mark.req("REQ-SLY-007")
    def test_a_dry_run_writes_nothing_and_a_second_run_copies_nothing(self):
        code, text = self.run_command("files-to-db", "--data", self.data, "--database-url", "x", "--dry-run")
        self.assertEqual((code, os.path.exists(self.db)), (0, False))
        self.assertIn("dry run", text)
        self.run_command("files-to-db", "--data", self.data, "--database-url", "x")
        self.assertIn("copied 0", self.run_command("files-to-db", "--data", self.data, "--database-url", "x")[1])

    @mark.req("REQ-SLY-007")
    def test_a_conflict_is_reported_with_exit_code_1_and_changes_nothing(self):
        other = Storage(FileBackend(self.db))
        other.put("workflows", "lookup", dict(LOOKUP, note="other"), "carl")
        before = tree(self.db)
        code, text = self.run_command("files-to-db", "--data", self.data, "--database-url", "x")
        self.assertEqual(code, 1)
        self.assertIn("conflict", text)
        self.assertEqual(tree(self.db), before)

    @mark.req("REQ-SLY-009")
    def test_library_export_and_seed_are_one_command_each(self):
        """TC-SLY-009 through the command line: the library of a data folder into a folder and from it into an empty data folder."""
        export = os.path.join(self.base, "library")
        self.assertEqual(self.run_command("library-export", "--data", self.data, "--folder", export)[0], 0)
        fresh = os.path.join(self.base, "fresh")
        self.assertEqual(self.run_command("library-seed", "--data", fresh, "--folder", export)[0], 0)
        self.assertEqual(tree(os.path.join(fresh, "workflows")), tree(os.path.join(self.data, "workflows")))
        self.assertFalse(os.path.exists(os.path.join(fresh, "memory")))

    @mark.req("REQ-SLY-007")
    def test_a_missing_option_or_direction_is_a_usage_error(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            migrate.main(["files-to-db"], open_db=self.open_db)
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit):
            migrate.main(["sideways"], open_db=self.open_db)


if __name__ == "__main__":
    unittest.main()
