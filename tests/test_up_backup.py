"""TC-OPR-005 / REQ-OPR-005
Run with: python tests/test_up_backup.py
"""

import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                         # noqa: E402

PODMAN_STUB = r'''#!/bin/bash
echo "podman $*" >> "$STUB_LOG"
case "$1" in
  ps) case " $* " in *service=db*) [ -n "$STUB_DB" ] && echo "$STUB_DB";; *) echo "mia1";; esac ;;
  cp) case "$2" in mia1:*) echo volume > "$3/history.json";; esac ;;
esac
exit 0
'''
TOOL_STUB = r'''#!/bin/bash
echo "$(basename "$0") $*" >> "$STUB_LOG"
exit 0
'''


class UpBackup(unittest.TestCase):
    """`deploy/up.sh backup|restore` on a stub podman and stub tools/backup.sh and tools/restore.sh that only record their arguments."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = self.tmp.name
        os.makedirs(os.path.join(root, "deploy"))
        os.makedirs(os.path.join(root, "tools"))
        os.makedirs(os.path.join(root, "bin"))
        shutil.copy(os.path.join(REPO, "deploy", "up.sh"), os.path.join(root, "deploy"))
        with open(os.path.join(root, "deploy", ".env"), "w") as fp:
            fp.write("SEARXNG_SECRET=test\n")
        for path, text in ((os.path.join(root, "bin", "podman"), PODMAN_STUB),
                           (os.path.join(root, "tools", "backup.sh"), TOOL_STUB),
                           (os.path.join(root, "tools", "restore.sh"), TOOL_STUB)):
            with open(path, "w") as fp:
                fp.write(text)
            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.log = os.path.join(root, "calls.log")

    def run_up(self, *args, db="mia_db_1"):
        """runs deploy/up.sh in the temporary folder; gives (completed process, list of recorded calls)"""
        env = dict(os.environ, PATH=os.path.join(self.tmp.name, "bin") + os.pathsep + os.environ["PATH"], STUB_LOG=self.log, STUB_DB=db)
        done = subprocess.run(["bash", os.path.join(self.tmp.name, "deploy", "up.sh"), *args], capture_output=True, text=True, env=env, cwd=self.tmp.name)
        calls = open(self.log).read().splitlines() if os.path.exists(self.log) else []
        return done, calls

    def archive(self, name, members):
        """a .tar.gz in the temporary folder holding the given member names (each with a short text)"""
        path = os.path.join(self.tmp.name, name)
        src = os.path.join(self.tmp.name, "src-" + name)
        os.makedirs(src)
        for member in members:
            with open(os.path.join(src, member), "w") as fp:
                fp.write("x\n")
        with tarfile.open(path, "w:gz") as tar:
            for member in members:
                tar.add(os.path.join(src, member), arcname=member)
        return path

    @mark.req('REQ-OPR-005')
    def test_backup_with_the_db_service_calls_the_backup_tool_with_the_database_and_the_volume(self):
        """TC-OPR-005: with a db container the stack's backup command makes one archive of the database and the data volume (D-133).

        Example: up.sh backup out.tar.gz, db mia_db_1 -> backup.sh out.tar.gz --db-container mia_db_1 --db-user mia --db-name mia --data <copy of the volume>
        """
        # Given: a stack with a db container (the default of run_up)
        out = os.path.join(self.tmp.name, "out.tar.gz")
        # When: the backup command runs
        done, calls = self.run_up("backup", out)
        # Then: backup.sh is called once with the archive, the database and a data folder
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        tool = [c for c in calls if c.startswith("backup.sh ")]
        self.assertEqual(len(tool), 1, calls)
        self.assertIn("backup.sh %s --db-container mia_db_1 --db-user mia --db-name mia --data " % out, tool[0])

    @mark.req('REQ-OPR-005')
    def test_backup_without_the_db_service_keeps_the_volume_archive(self):
        """TC-OPR-005: without a db container the backup command archives the data volume as before, without the database tool.

        Example: up.sh backup out.tar.gz, no db -> out.tar.gz holds history.json, backup.sh not called
        """
        # Given: a stack without a db container
        out = os.path.join(self.tmp.name, "out.tar.gz")
        # When: the backup command runs
        done, calls = self.run_up("backup", out, db="")
        # Then: the archive holds the volume's file and the database tool is not called
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertFalse(any(c.startswith("backup.sh") for c in calls), calls)
        with tarfile.open(out) as tar:
            self.assertIn("./history.json", tar.getnames())

    @mark.req('REQ-OPR-005')
    def test_restore_of_a_database_archive_calls_the_restore_tool_with_the_database(self):
        """TC-OPR-005: an archive with db.dump is restored by restore.sh into the db container and the data volume.

        Example: up.sh restore new.tar.gz (db.dump, data.tar) -> restore.sh new.tar.gz --db-container mia_db_1 --db-user mia --db-name mia --data <folder>
        """
        # Given: an archive made by tools/backup.sh
        new = self.archive("new.tar.gz", ["db.dump", "data.tar"])
        # When: the restore command runs
        done, calls = self.run_up("restore", new)
        # Then: restore.sh is called once with the archive and the database, and the data goes back into the mia container
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        tool = [c for c in calls if c.startswith("restore.sh ")]
        self.assertEqual(len(tool), 1, calls)
        self.assertIn("restore.sh %s --db-container mia_db_1 --db-user mia --db-name mia --data " % new, tool[0])
        self.assertTrue(any(c.startswith("podman cp ") and c.endswith("mia1:/opt/mia/MIA/data/") for c in calls), calls)

    @mark.req('REQ-OPR-005')
    def test_restore_still_accepts_an_old_volume_archive(self):
        """TC-OPR-005: an old archive of the data volume alone is restored as before, and the database is left alone.

        Example: up.sh restore old.tar.gz (history.json only) -> files copied into mia, restore.sh not called
        """
        # Given: an old archive of the volume
        old = self.archive("old.tar.gz", ["history.json"])
        # When: the restore command runs
        done, calls = self.run_up("restore", old)
        # Then: the files go back into the mia container and the database tool is not called
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertFalse(any(c.startswith("restore.sh") for c in calls), calls)
        self.assertTrue(any(c.startswith("podman cp ") and c.endswith("mia1:/opt/mia/MIA/data/") for c in calls), calls)

    @mark.req('REQ-OPR-005')
    def test_a_database_archive_without_the_db_service_is_refused(self):
        """TC-OPR-005: an archive with a database is refused when the stack runs without db, and nothing is copied.

        Example: up.sh restore new.tar.gz, no db -> exit 1, message names deploy/up.sh db
        """
        # Given: an archive with a database and a stack without db
        new = self.archive("new.tar.gz", ["db.dump", "data.tar"])
        # When: the restore command runs
        done, calls = self.run_up("restore", new, db="")
        # Then: it stops with a hint and copies nothing
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("deploy/up.sh db", done.stdout + done.stderr)
        self.assertFalse(any(c.startswith("podman cp ") and c.endswith("mia1:/opt/mia/MIA/data/") for c in calls), calls)

if __name__ == "__main__":
    unittest.main()
