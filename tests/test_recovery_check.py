"""tools/recovery_check.sh: kill the mia container in the middle of an answer, restart it, check the data (deploy-phase 3, recovery). A stub podman stands in."""
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                         # noqa: E402

# The container-side Python scripts start with "# role: NAME" in their first line; the stub answers by role and records every call.
PODMAN_STUB = r'''#!/bin/bash
echo "podman $*" >> "$STUB_LOG"
case "$1" in
  ps) echo "mia1" ;;
  kill|start) exit 0 ;;
  exec)
    case " $* " in *" pg_isready "*) exit "${STUB_DB_RC:-0}" ;; esac
    script="$(cat)"
    role="$(echo "$script" | head -1 | sed 's/^# role: //')"
    echo "role $role" >> "$STUB_LOG"
    case "$role" in
      chat) echo "done=True text='ok'" ;;
      long) echo "STREAMING"; sleep 30 ;;
      snapshot) echo "snapshot 3 files" ;;
      verify) echo "ok:   marker found"; echo "$STUB_VERIFY_LINE" ;;
    esac ;;
esac
exit 0
'''
CURL_STUB = "#!/bin/bash\nexit 0\n"


class Recovery(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bin = os.path.join(self.tmp.name, "bin")
        os.makedirs(self.bin)
        for name, text in (("podman", PODMAN_STUB), ("curl", CURL_STUB)):
            path = os.path.join(self.bin, name)
            with open(path, "w") as fp:
                fp.write(text)
            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.log = os.path.join(self.tmp.name, "calls.log")

    def read_log(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as fp:
            return fp.read().splitlines()

    def run_script(self, **extra):
        env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"], STUB_LOG=self.log, STUB_VERIFY_LINE="ok:   data intact", MIA_RECOVERY_WAIT="5")
        env.update(extra)
        done = subprocess.run(["bash", os.path.join(REPO, "tools", "recovery_check.sh")], capture_output=True, text=True, env=env, timeout=120, stdin=subprocess.DEVNULL)
        calls = self.read_log()
        return done, calls

    @mark.req("REQ-OPR-001")
    def test_it_kills_the_container_while_the_answer_streams_and_restarts_it_before_the_checks(self):
        """Given a running stack, When the script runs, Then the order is: marker chat, snapshot, long answer streaming, kill, start, checks, new chat; exit 0"""
        done, calls = self.run_script()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        roles = [c.split()[1] for c in calls if c.startswith("role ")]
        self.assertEqual(roles, ["chat", "snapshot", "long", "verify", "chat"], calls)
        kill = next(i for i, c in enumerate(calls) if c.startswith("podman kill"))
        start = next(i for i, c in enumerate(calls) if c.startswith("podman start"))
        self.assertLess(calls.index("role long"), kill)
        self.assertLess(kill, start)
        self.assertLess(start, calls.index("role verify"))
        self.assertIn("Recovery check OK", done.stdout)

    @mark.req("REQ-OPR-001")
    def test_a_failed_data_check_or_a_dead_database_makes_it_red(self):
        """Given a verify script that reports FAIL, and then a database that is not ready, When the script runs, Then it exits 1 and names the failure"""
        done, _ = self.run_script(STUB_VERIFY_LINE="FAIL: chat_log.jsonl line 9 is not JSON")
        self.assertEqual(done.returncode, 1)
        self.assertIn("chat_log.jsonl line 9", done.stdout)
        self.assertIn("Recovery check FAILED", done.stdout)
        done, _ = self.run_script(STUB_DB_RC="1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAIL: database", done.stdout)


if __name__ == "__main__":
    unittest.main()
