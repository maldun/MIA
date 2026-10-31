"""TC-OPR-002 / REQ-OPR-002
Run with: python tests/test_first_account_up.py
"""

import os
import pty
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

PODMAN_STUB = r'''#!/bin/bash
echo "podman $*" >> "$STUB_LOG"
case "$1" in
  ps) echo "mia1" ;;
  exec) case " $* " in *" list "*) echo "$STUB_ACCOUNTS" ;; esac ;;
esac
exit 0
'''
COMPOSE_STUB = r'''#!/bin/bash
echo "compose $*" >> "$STUB_LOG"
exit 0
'''
CURL_STUB = r'''#!/bin/bash
exit 0
'''
OFFER_LINE = "No account yet. Make the owner account when you like:  deploy/up.sh owner NAME"
MARKER = "MIA_FIRST_ACCOUNT_OFFERED=1"
CREATE = "podman exec -it mia1 python /opt/mia/MIA/tools/accounts_cli.py create anna --dir /opt/mia/MIA/data/db"


class FirstAccountAtStart(unittest.TestCase):
    """The start of `deploy/up.sh` on a stub podman, a stub compose and a stub curl (the page answers at once); the stub podman lists $STUB_ACCOUNTS."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = self.tmp.name
        os.makedirs(os.path.join(root, "deploy"))
        os.makedirs(os.path.join(root, "bin"))
        shutil.copy(os.path.join(REPO, "deploy", "up.sh"), os.path.join(root, "deploy"))
        shutil.copy(os.path.join(REPO, "deploy", "setup_cfg.compose.json"), os.path.join(root, "deploy"))
        shutil.copy(os.path.join(REPO, "config.py"), root)
        self.env_file = os.path.join(root, "deploy", ".env")
        with open(self.env_file, "w") as fp:
            fp.write("SEARXNG_SECRET=test\n")
        for name, text in (("podman", PODMAN_STUB), ("compose", COMPOSE_STUB), ("curl", CURL_STUB)):
            path = os.path.join(root, "bin", name)
            with open(path, "w") as fp:
                fp.write(text)
            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.log = os.path.join(root, "calls.log")

    def start(self, accounts="no accounts", answer=None):
        """runs the start of deploy/up.sh; answer None = no terminal, else the text typed on a terminal; gives (output, list of recorded calls)"""
        env = dict(os.environ, PATH=os.path.join(self.tmp.name, "bin") + os.pathsep + os.environ["PATH"], STUB_LOG=self.log,
                   STUB_ACCOUNTS=accounts, COMPOSE=os.path.join(self.tmp.name, "bin", "compose"),
                   OLLAMA_URL="http://host.containers.internal:11434")
        cmd = ["bash", os.path.join(self.tmp.name, "deploy", "up.sh")]
        if answer is None:
            done = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, env=env, cwd=self.tmp.name, timeout=60)
            output = done.stdout + done.stderr
        else:
            master, slave = pty.openpty()
            os.write(master, (answer + "\n").encode())
            done = subprocess.run(cmd, stdin=slave, capture_output=True, text=True, env=env, cwd=self.tmp.name, timeout=60)
            os.close(slave)
            os.close(master)
            output = done.stdout + done.stderr
        self.assertEqual(done.returncode, 0, output)
        calls = open(self.log).read().splitlines() if os.path.exists(self.log) else []
        return output, calls

    def env_text(self):
        with open(self.env_file) as fp:
            return fp.read()

    @mark.req('REQ-OPR-002')
    def test_the_first_start_without_a_terminal_prints_the_offer_once(self):
        """TC-OPR-002: the first start of deploy/up.sh without a terminal and without an account prints the line with the owner command once and writes the marker into .env (D-136).

        Example: no account, no terminal -> OFFER_LINE once in the output, MIA_FIRST_ACCOUNT_OFFERED=1 in deploy/.env
        """
        # Given: a stack without an account (the default of start)
        # When: the stack starts without a terminal
        output, calls = self.start()
        # Then: the offer is printed once and the marker is in .env
        self.assertEqual(output.count(OFFER_LINE), 1, output)
        self.assertIn(MARKER, self.env_text().splitlines())

    @mark.req('REQ-OPR-002')
    def test_the_second_start_does_not_offer_again(self):
        """TC-OPR-002: after the first offer a later start of deploy/up.sh offers nothing, even without an account (D-136).

        Example: start, start again -> the second output has no offer, the marker is in .env once
        """
        # Given: the first start has offered the account
        self.start()
        # When: the stack starts again
        output, calls = self.start()
        # Then: no offer, and the marker is not written twice
        self.assertNotIn(OFFER_LINE, output)
        self.assertNotIn("Name (empty = later)", output)
        self.assertEqual(self.env_text().splitlines().count(MARKER), 1)

    @mark.req('REQ-OPR-002')
    def test_a_name_typed_on_a_terminal_makes_the_owner_account(self):
        """TC-OPR-002: on a terminal the first start asks for the owner's name and makes the account as deploy/up.sh owner does.

        Example: answer "anna" on a terminal -> podman exec -it mia1 ... accounts_cli.py create anna --dir /opt/mia/MIA/data/db
        """
        # Given: a stack without an account (the default of start)
        # When: the stack starts on a terminal and the owner types a name
        output, calls = self.start(answer="anna")
        # Then: the question was asked, the account tool created the account and the marker is in .env
        self.assertIn("Name (empty = later)", output)
        self.assertIn(CREATE, calls)
        self.assertIn(MARKER, self.env_text().splitlines())

    @mark.req('REQ-OPR-002')
    def test_no_offer_when_an_account_exists(self):
        """TC-OPR-002: a first start with an account offers nothing and leaves no marker.

        Example: the stub lists anna -> no offer, no marker in .env
        """
        # Given: a stack whose file store lists the account anna
        # When: the stack starts
        output, calls = self.start(accounts="anna")
        # Then: no offer and no marker
        self.assertNotIn(OFFER_LINE, output)
        self.assertNotIn(MARKER, self.env_text())

if __name__ == '__main__':
    unittest.main()
