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
        for path in RUN_LOG_CODE:
            self.assertEqual(sorted(imported(path) & set(DRIVERS)), [], path)

    def test_the_events_of_a_run_are_appended_to_a_file_and_none_is_rewritten(self):
        with tempfile.TemporaryDirectory() as folder:
            log = RunLog(folder)
            first = log.start("lookup")
            first.event({"kind": "start", "seq": 1})
            first.finish("done", output="a")
            name = [n for n in os.listdir(folder) if n.startswith("runs-")][0]
            path = os.path.join(folder, name)
            with open(path, "rb") as handle:
                before = handle.read()
            second = log.start("lookup")
            second.event({"kind": "start", "seq": 1})
            second.finish("done", output="b")
            log.add_feedback(first.id, "thumb", 1)
            with open(path, "rb") as handle:
                after = handle.read()
            self.assertTrue(after.startswith(before))                         # what was written stays as it was
            self.assertGreater(len(after), len(before))
            self.assertEqual([r["id"] for r in log.read()], [first.id, second.id])


if __name__ == "__main__":
    unittest.main()
