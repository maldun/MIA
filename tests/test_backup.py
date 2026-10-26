"""Backup and restore of the database and the data folder (N-3.1 T-07): TC-SLY-008. Run with the python that has psycopg:  python tests/test_backup.py
Uses the throwaway database container of test_storage_postgres.py; skipped, never weakened, where it cannot start."""
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                                # noqa: E402
import test_storage_postgres as tp                                      # noqa: E402


def script(name, *args):
    return subprocess.run(["bash", os.path.join(ROOT, "tools", name), *args], capture_output=True, text=True)


class BackupRestore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = tp.start_database()
        cls.addClassCleanup(tp.stop_database)

    def setUp(self):
        from storage import Storage
        from storage_postgres import PostgresBackend
        self.base = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.base, True)
        self.backend = PostgresBackend(self.url)
        self.addCleanup(self.backend.close)
        self.backend._query("TRUNCATE records")
        self.store = Storage(self.backend)
        for n in range(50):
            self.store.put("tasks", "t%02d" % n, {"text": "task %d" % n}, "anna")
        self.store.put("tasks", "t00", {"text": "second version"}, "ben")
        self.data = os.path.join(self.base, "data")
        os.makedirs(os.path.join(self.data, "sub"))
        with open(os.path.join(self.data, "chat_log.jsonl"), "w", encoding="utf-8") as handle:
            handle.write('{"text": "Zoë ✓"}\n')
        with open(os.path.join(self.data, "sub", "preset.json"), "w") as handle:
            handle.write("{}")
        self.options = ["--db-container", tp.NAME, "--db-user", "postgres", "--db-name", "postgres", "--data", self.data]

    def snapshot(self):
        return self.backend._query("SELECT tbl, id, version, author, time, doc::text FROM records ORDER BY tbl, id, version")

    @mark.req("REQ-SLY-008")
    def test_wiped_database_and_data_folder_come_back_with_all_versions(self):
        """TC-SLY-008: 50 records with versions and the data folder; backup; wipe both; restore: the same records, the same files."""
        before = self.snapshot()
        self.assertEqual(len(before), 51)
        archive = os.path.join(self.base, "backup.tar.gz")
        done = script("backup.sh", archive, *self.options)
        self.assertEqual(done.returncode, 0, done.stderr)
        with tarfile.open(archive) as tar:
            self.assertEqual(sorted(n.lstrip("./") for n in tar.getnames() if n not in (".", "./")), ["data.tar", "db.dump"])
        self.backend._query("TRUNCATE records")
        shutil.rmtree(self.data)
        self.assertEqual(self.snapshot(), [])
        done = script("restore.sh", archive, *self.options)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.snapshot(), before)
        with open(os.path.join(self.data, "chat_log.jsonl"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), '{"text": "Zoë ✓"}\n')
        self.assertTrue(os.path.exists(os.path.join(self.data, "sub", "preset.json")))

    @mark.req("REQ-SLY-008")
    def test_a_restore_keeps_the_state_before_it_and_a_wrong_archive_changes_nothing(self):
        """The state before a restore is saved first; an archive that is not a backup is refused before anything is touched."""
        archive = os.path.join(self.base, "backup.tar.gz")
        self.assertEqual(script("backup.sh", archive, *self.options).returncode, 0)
        self.store.put("tasks", "new", {"text": "after the backup"}, "anna")
        done = script("restore.sh", archive, *self.options)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.store.ids("tasks").count("new"), 0)
        saved = [n for n in os.listdir(self.base) if n.startswith("mia-before-restore-")]
        self.assertEqual(len(saved), 1)
        junk = os.path.join(self.base, "junk.tar.gz")
        with tarfile.open(junk, "w:gz") as tar:
            tar.add(self.base + "/backup.tar.gz", arcname="other.txt")
        before = self.snapshot()
        self.assertNotEqual(script("restore.sh", junk, *self.options).returncode, 0)
        self.assertEqual(self.snapshot(), before)

    @mark.req("REQ-SLY-008")
    def test_missing_options_are_a_usage_error(self):
        self.assertNotEqual(script("backup.sh").returncode, 0)
        self.assertNotEqual(script("restore.sh", "x.tar.gz").returncode, 0)


if __name__ == "__main__":
    unittest.main()
