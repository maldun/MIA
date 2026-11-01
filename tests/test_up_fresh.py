"""TC-OPR-001 / REQ-OPR-001
Run with: python tests/test_up_fresh.py
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


class FreshCheckout(unittest.TestCase):
    """The start of `deploy/up.sh` in a fresh checkout on a stub podman, a stub compose and a stub curl (the page answers at once); deploy/.env is what the owner wrote, or none."""

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
        for name, text in (("podman", PODMAN_STUB), ("compose", COMPOSE_STUB), ("curl", CURL_STUB)):
            path = os.path.join(root, "bin", name)
            with open(path, "w") as fp:
                fp.write(text)
            os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.log = os.path.join(root, "calls.log")

    def start(self, *args, accounts="anna"):
        """runs the start of deploy/up.sh (with the given arguments, e.g. db) without a terminal (OLLAMA_URL and SEARXNG_SECRET only from deploy/.env); gives (output, list of recorded calls)"""
        env = dict(os.environ, PATH=os.path.join(self.tmp.name, "bin") + os.pathsep + os.environ["PATH"], STUB_LOG=self.log,
                   STUB_ACCOUNTS=accounts, COMPOSE=os.path.join(self.tmp.name, "bin", "compose"))
        env.pop("OLLAMA_URL", None)
        env.pop("SEARXNG_SECRET", None)
        done = subprocess.run(["bash", os.path.join(self.tmp.name, "deploy", "up.sh"), *args], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              env=env, cwd=self.tmp.name, timeout=60)
        output = done.stdout + done.stderr
        self.assertEqual(done.returncode, 0, output)
        calls = open(self.log).read().splitlines() if os.path.exists(self.log) else []
        return output, calls

    def env_text(self):
        with open(self.env_file) as fp:
            return fp.read()

    def write_env(self, text):
        with open(self.env_file, "w") as fp:
            fp.write(text)

    @mark.req('REQ-OPR-001')
    def test_an_env_with_only_the_ollama_address_gets_the_searxng_secret(self):
        """TC-OPR-001: a fresh checkout whose one configuration file deploy/.env names only the Ollama address starts: up.sh adds the SearXNG secret and keeps the address.

        Example: .env "OLLAMA_URL=http://host.containers.internal:11434" -> after the start .env also has one SEARXNG_SECRET=<hex>
        """
        # Given: deploy/.env with only the address of an Ollama that runs already
        self.write_env("OLLAMA_URL=http://host.containers.internal:11434\n")
        # When: the stack starts
        output, calls = self.start()
        # Then: the address is kept and exactly one non-empty secret was added
        lines = self.env_text().splitlines()
        self.assertIn("OLLAMA_URL=http://host.containers.internal:11434", lines)
        self.assertEqual(len([line for line in lines if line.startswith("SEARXNG_SECRET=") and len(line) > len("SEARXNG_SECRET=")]), 1, lines)

    @mark.req('REQ-OPR-001')
    def test_an_ollama_address_starts_no_model_server_of_the_stack(self):
        """TC-OPR-001 (D-136): with OLLAMA_URL in deploy/.env the compose call has no ollama profile, so the stack pulls no model.

        Example: .env "OLLAMA_URL=..." -> the compose call does not contain "--profile ollama"
        """
        # Given: deploy/.env with only the address of an Ollama that runs already
        self.write_env("OLLAMA_URL=http://host.containers.internal:11434\n")
        # When: the stack starts
        output, calls = self.start()
        # Then: compose was called without the ollama profile
        compose = [call for call in calls if call.startswith("compose ")]
        self.assertTrue(compose, calls)
        self.assertNotIn("--profile ollama", compose[0])

    @mark.req('REQ-OPR-001')
    def test_a_checkout_without_env_gets_the_secret_once(self):
        """TC-OPR-001: without deploy/.env the first start writes the secret, and a second start does not write it again.

        Example: no .env, start twice -> one SEARXNG_SECRET line
        """
        # Given: a fresh checkout without deploy/.env (setUp)
        # When: the stack starts twice
        self.start()
        output, calls = self.start()
        # Then: the secret is in .env once
        lines = self.env_text().splitlines()
        self.assertEqual(len([line for line in lines if line.startswith("SEARXNG_SECRET=")]), 1, lines)

    @mark.req('REQ-OPR-001')
    def test_the_project_name_in_the_env_is_used(self):
        """TC-OPR-001: MIA_PROJECT in deploy/.env (README "Settings in .env") names the stack that up.sh works on, not only the environment variable.

        Example: .env "MIA_PROJECT=other" -> up.sh looks for the mia container of project other, never of mia
        """
        # Given: deploy/.env with another project name
        self.write_env("OLLAMA_URL=http://host.containers.internal:11434\nMIA_PROJECT=other\n")
        # When: the stack starts
        output, calls = self.start()
        # Then: the containers are looked for in the project other only
        lookups = [call for call in calls if call.startswith("podman ps ")]
        self.assertTrue(lookups, calls)
        self.assertTrue(all("label=com.docker.compose.project=other" in call for call in lookups), lookups)

    @mark.req('REQ-OPR-001')
    def test_the_marker_of_the_offer_gets_a_line_of_its_own(self):
        """TC-OPR-001, Verify finding F6: a hand-written .env without its last newline (secret already there) keeps its last line when up.sh adds the marker of the first-account offer.

        Example: .env "SEARXNG_SECRET=s\nOLLAMA_URL=http://h:11434" (no last newline), no account -> lines "OLLAMA_URL=http://h:11434" and "MIA_FIRST_ACCOUNT_OFFERED=1"
        """
        # Given: deploy/.env with the secret and an address on a last line without newline
        self.write_env("SEARXNG_SECRET=s\nOLLAMA_URL=http://host.containers.internal:11434")
        # When: the stack starts with no account, so the offer leaves its marker
        self.start(accounts="no accounts")
        # Then: the address and the marker are separate lines
        lines = self.env_text().splitlines()
        self.assertIn("OLLAMA_URL=http://host.containers.internal:11434", lines)
        self.assertIn("MIA_FIRST_ACCOUNT_OFFERED=1", lines)

    @mark.req('REQ-OPR-001')
    def test_the_database_password_gets_a_line_of_its_own(self):
        """TC-OPR-001, Verify finding F6: a hand-written .env without its last newline (secret already there) keeps its last line when up.sh db adds the database password.

        Example: .env "SEARXNG_SECRET=s\nOLLAMA_URL=http://h:11434" (no last newline), up.sh db -> lines "OLLAMA_URL=http://h:11434" and "POSTGRES_PASSWORD=<hex>"
        """
        # Given: deploy/.env with the secret and an address on a last line without newline
        self.write_env("SEARXNG_SECRET=s\nOLLAMA_URL=http://host.containers.internal:11434")
        # When: the stack starts with its database
        self.start("db")
        # Then: the address and the password are separate lines
        lines = self.env_text().splitlines()
        self.assertIn("OLLAMA_URL=http://host.containers.internal:11434", lines)
        self.assertTrue(any(line.startswith("POSTGRES_PASSWORD=") for line in lines), lines)

if __name__ == '__main__':
    unittest.main()
