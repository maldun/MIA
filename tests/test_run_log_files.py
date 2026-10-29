"""
TC-LOG-005 (REQ-LOG-005, reworded by A-28): the Run log keeps the events of a run as append-only files in its own folder and imports no database driver. Inspection of the code of the
Run log (run_log.py, events.py, run_explain.py, reproduce.py) and a check of the files. Run: python tests/test_run_log_files.py
"""
import ast
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from run_log import RunLog  # noqa: E402

RUN_LOG_CODE = ("run_log.py", "events.py", "run_explain.py", "reproduce.py")
DRIVERS = ("psycopg", "psycopg2", "asyncpg", "pg8000", "sqlalchemy", "sqlite3", "pymysql", "mysql", "redis", "pymongo")


def imported(path):
    with open(os.path.join(REPO, path), encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])
    return names


class RunLogFiles(unittest.TestCase):
    def test_the_code_of_the_run_log_imports_no_database_driver(self):
        """TC-LOG-005: none of the four files of the Run log imports a database driver.
        Example: run_log.py, events.py, run_explain.py and reproduce.py import none of psycopg, sqlite3, sqlalchemy ... ."""
        # Given the four files of the Run log, when their imports are read, then none is a database driver
        for path in RUN_LOG_CODE:
            self.assertEqual(sorted(imported(path) & set(DRIVERS)), [], path)

    def test_the_events_of_a_run_are_appended_to_a_file_and_none_is_rewritten(self):
        """TC-LOG-005 (A-28): a finished run, a second run and a feedback line only add to the end of the monthly file.
        Example: after run one the file has N bytes; after run two and a thumb for run one the first N bytes are the same and the file is longer."""
        with tempfile.TemporaryDirectory() as folder:
            # Given a log with one finished run, and the bytes of its file
            log = RunLog(folder)
            first = log.start("lookup")
            first.event({"kind": "start", "seq": 1})
            first.finish("done", output="a")
            name = [n for n in os.listdir(folder) if n.startswith("runs-")][0]
            path = os.path.join(folder, name)
            with open(path, "rb") as handle:
                before = handle.read()
            # When a second run and a feedback line for the first are written
            second = log.start("lookup")
            second.event({"kind": "start", "seq": 1})
            second.finish("done", output="b")
            log.add_feedback(first.id, "thumb", 1)
            with open(path, "rb") as handle:
                after = handle.read()
            # Then what was written stays as it was, and both runs read back in order
            self.assertTrue(after.startswith(before))
            self.assertGreater(len(after), len(before))
            self.assertEqual([r["id"] for r in log.read()], [first.id, second.id])


if __name__ == "__main__":
    unittest.main()
