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

    def test_the_https_service_is_a_trusted_proxy_so_that_a_login_works_in_the_stack(self):
        """found 2026-10-29: MIA sees every connection from the podman network; without this the login is refused with insecure_channel on every way in"""
        with open(os.path.join(DEPLOY, "setup_cfg.compose.json"), encoding="utf-8") as fp:
            cfg = json.load(fp)
        self.assertEqual(cfg.get("trusted_proxies"), ["https"])

    def test_the_settings_of_one_machine_are_a_local_file_that_is_not_in_git(self):
        """owner's remark 2026-10-29: deploy/setup_cfg.compose.json is tracked and the same everywhere; the login and other settings of one machine go into setup_cfg.local.json"""
        with open(os.path.join(DEPLOY, "compose.yaml"), encoding="utf-8") as fp:
            self.assertIn("./setup_cfg.local.json:/opt/mia/MIA/setup_cfg.local.json", fp.read())
        with open(os.path.join(DEPLOY, ".gitignore"), encoding="utf-8") as fp:
            self.assertIn("setup_cfg.local.json", fp.read().split())
        with open(os.path.join(DEPLOY, "setup_cfg.compose.json"), encoding="utf-8") as fp:
            self.assertNotIn("accounts_enabled", json.load(fp))               # not a machine setting inside the tracked file

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
        shutil.copy(os.path.join(REPO, "config.py"), self.tmp.name)                    # up.sh owner writes the local file with it
        with open(os.path.join(self.deploy, ".env"), "w") as fp:                     # exists, so the script does not make a secret
            fp.write("SEARXNG_SECRET=test\n")
        self.bin = os.path.join(self.tmp.name, "bin")
        os.makedirs(self.bin)
        self.log = os.path.join(self.tmp.name, "podman.log")
        stub = os.path.join(self.bin, "podman")
        with open(stub, "w") as fp:
            fp.write('#!/bin/bash\necho "$@" >> %s\ncase "$1" in ps) [ -n "$STUB_CONTAINER" ] && echo "$STUB_CONTAINER";; exec) exit ${STUB_EXEC_EXIT:-0};; esac\nexit 0\n' % self.log)
        os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC)

    def run_up(self, *args, container="abc123", exec_exit="0"):
        env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"], STUB_CONTAINER=container, STUB_EXEC_EXIT=exec_exit)
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

    def test_owner_turns_the_login_on_in_the_local_file_and_leaves_the_tracked_config_alone(self):
        tracked = os.path.join(self.deploy, "setup_cfg.compose.json")
        with open(tracked, "rb") as fp:
            before = fp.read()
        done, _ = self.run_up("owner", "anna")
        self.assertEqual(done.returncode, 0, done.stderr)
        with open(os.path.join(self.deploy, "setup_cfg.local.json"), encoding="utf-8") as fp:
            self.assertTrue(json.load(fp)["accounts_enabled"])
        with open(tracked, "rb") as fp:
            self.assertEqual(fp.read(), before)                                       # the file that is in git is not touched
        self.assertIn("setup_cfg.local.json", done.stdout)
        self.assertIn("force-recreate mia", done.stdout)                               # what to do to apply it
        self.assertIn("https://localhost:8586", done.stdout)

    def test_a_failed_account_tool_turns_nothing_on(self):
        done, _ = self.run_up("owner", "anna", exec_exit="1")
        self.assertNotEqual(done.returncode, 0)
        local = os.path.join(self.deploy, "setup_cfg.local.json")
        if os.path.exists(local):
            with open(local, encoding="utf-8") as fp:
                self.assertNotIn("accounts_enabled", json.load(fp))

    def test_the_local_file_exists_after_any_call_so_that_the_mount_works(self):
        self.run_up("owner", "anna")
        with open(os.path.join(self.deploy, "setup_cfg.local.json"), encoding="utf-8") as fp:
            self.assertIsInstance(json.load(fp), dict)

if __name__ == "__main__":
    unittest.main()
