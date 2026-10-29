"""Tests for the compose files in deploy/: the config only names options of setup_cfg.example.json and sets the container switches, up.sh is valid bash."""
import json
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(REPO, "deploy")
sys.path.insert(0, REPO)


class DeployTests(unittest.TestCase):
    def test_config_options_exist_in_the_example(self):
        example = json.load(open(os.path.join(REPO, "setup_cfg.example.json"), encoding="utf-8"))
        cfg = json.load(open(os.path.join(DEPLOY, "setup_cfg.compose.json"), encoding="utf-8"))
        self.assertEqual(set(cfg) - set(example), set())
        self.assertIs(cfg["ollama_managed"], False)
        self.assertEqual(cfg["ollama_host"], "http://ollama:11434")
        self.assertEqual(cfg["sandbox_backend"], "none")
        self.assertTrue(cfg["searxng_url"].startswith("http://searxng:"))
        self.assertFalse(cfg["searxng_autostart"])
        self.assertTrue(os.path.isabs(cfg["history_file"]))

    def test_up_script_is_valid_bash(self):
        done = subprocess.run(["bash", "-n", os.path.join(DEPLOY, "up.sh")], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_compose_files_name_the_services(self):
        text = open(os.path.join(DEPLOY, "compose.yaml"), encoding="utf-8").read()
        for service in ("mia:", "https:", "ollama:", "searxng:"):
            self.assertIn("\n  " + service, text)
        self.assertNotIn("ollama:\n    ports", text)          # Ollama is not published
        self.assertIn("/dev/kfd", open(os.path.join(DEPLOY, "compose.rocm.yaml"), encoding="utf-8").read())

    def test_caddy_proxies_to_mia(self):
        text = open(os.path.join(DEPLOY, "Caddyfile"), encoding="utf-8").read()
        self.assertIn("reverse_proxy mia:8585", text)
        self.assertIn("tls internal", text)

    def test_secrets_stay_out_of_git(self):
        self.assertIn(".env", open(os.path.join(DEPLOY, ".gitignore"), encoding="utf-8").read())



class OwnerCommand(unittest.TestCase):
    """`deploy/up.sh owner NAME` makes the first (owner) account inside the running MIA container: the long path of the account tool is not for the owner to remember (owner's wish 2026-10-29).
    The test puts a stub `podman` on the path that only records what it is asked, so nothing real runs."""

    def setUp(self):
        import shutil
        import stat
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.deploy = os.path.join(self.tmp.name, "deploy")
        os.makedirs(self.deploy)
        for name in ("up.sh", "setup_cfg.compose.json"):
            shutil.copy(os.path.join(REPO, "deploy", name), self.deploy)
        with open(os.path.join(self.deploy, ".env"), "w") as fp:                     # exists, so the script does not make a secret
            fp.write("SEARXNG_SECRET=test\n")
        self.bin = os.path.join(self.tmp.name, "bin")
        os.makedirs(self.bin)
        self.log = os.path.join(self.tmp.name, "podman.log")
        stub = os.path.join(self.bin, "podman")
        with open(stub, "w") as fp:
            fp.write('#!/bin/bash\necho "$@" >> %s\ncase "$1" in ps) [ -n "$STUB_CONTAINER" ] && echo "$STUB_CONTAINER";; esac\nexit 0\n' % self.log)
        os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC)

    def run_up(self, *args, container="abc123"):
        env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"], STUB_CONTAINER=container)
        done = subprocess.run(["bash", os.path.join(self.deploy, "up.sh"), *args], capture_output=True, text=True, env=env)
        calls = open(self.log).read().splitlines() if os.path.exists(self.log) else []
        return done, calls

    def test_owner_runs_the_account_tool_in_the_mia_container_with_a_terminal(self):
        done, calls = self.run_up("owner", "anna")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(any(c.startswith("exec -it abc123 python /opt/mia/MIA/tools/accounts_cli.py create anna --dir /opt/mia/MIA/data/db") for c in calls), calls)

    def test_a_missing_or_odd_name_is_refused_before_anything_runs(self):
        for args in (("owner",), ("owner", "bad name"), ("owner", "../x"), ("owner", "a;b")):
            done, calls = self.run_up(*args)
            self.assertNotEqual(done.returncode, 0, args)
            self.assertIn("usage: deploy/up.sh owner NAME", done.stdout + done.stderr)
            self.assertFalse(any(c.startswith("exec") for c in calls), args)

    def test_without_a_running_container_it_says_how_to_start_the_stack(self):
        done, calls = self.run_up("owner", "anna", container="")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("MIA container not found", done.stdout + done.stderr)

    def test_it_reminds_to_turn_the_login_on_when_the_config_does_not(self):
        done, _ = self.run_up("owner", "anna")
        self.assertIn('"accounts_enabled": true', done.stdout)                      # the compose config of the repository does not have it
        with open(os.path.join(self.deploy, "setup_cfg.compose.json"), encoding="utf-8") as fp:
            text = fp.read()
        with open(os.path.join(self.deploy, "setup_cfg.compose.json"), "w", encoding="utf-8") as fp:
            fp.write(text.replace("{", '{\n  "accounts_enabled": true,', 1))
        done, _ = self.run_up("owner", "anna")
        self.assertNotIn("is not turned on", done.stdout)


if __name__ == "__main__":
    unittest.main()
