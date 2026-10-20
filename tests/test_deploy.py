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


if __name__ == "__main__":
    unittest.main()
