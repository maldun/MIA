"""
Per-machine settings of the stack (owner's remark 2026-10-29): deploy/setup_cfg.compose.json is tracked and is the same everywhere; what belongs to one machine (the login, for example) goes into
setup_cfg.local.json next to it, which is NOT in git and wins over the tracked file key by key. config.load(path) reads both. Run: python tests/test_config_local.py
"""
import json
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

import config  # noqa: E402


class LocalOverlay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.main = os.path.join(self.tmp.name, "setup_cfg.json")
        self.local = os.path.join(self.tmp.name, "setup_cfg.local.json")
        self.write(self.main, {"accounts_enabled": False, "port": 8585, "public_hosts": [], "nested": {"a": 1}})

    def write(self, path, doc):
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(doc, fp)

    def test_without_a_local_file_the_configuration_is_the_main_file(self):
        self.assertEqual(config.load(self.main), {"accounts_enabled": False, "port": 8585, "public_hosts": [], "nested": {"a": 1}})

    def test_the_local_file_wins_key_by_key_and_the_other_keys_stay(self):
        self.write(self.local, {"accounts_enabled": True, "public_hosts": ["mia.example"]})
        found = config.load(self.main)
        self.assertEqual((found["accounts_enabled"], found["public_hosts"], found["port"]), (True, ["mia.example"], 8585))

    def test_an_object_in_the_local_file_replaces_the_whole_object(self):
        self.write(self.local, {"nested": {"b": 2}})
        self.assertEqual(config.load(self.main)["nested"], {"b": 2})                      # shallow: what the file says is what holds, no hidden mixing

    def test_an_empty_local_file_changes_nothing_and_a_broken_one_is_named(self):
        self.write(self.local, {})
        self.assertEqual(config.load(self.main)["port"], 8585)
        with open(self.local, "w", encoding="utf-8") as fp:
            fp.write("{ not json")
        with self.assertRaises(ValueError) as caught:
            config.load(self.main)
        self.assertIn("setup_cfg.local.json", str(caught.exception))                      # a typo in the override must not be ignored silently
        with open(self.local, "w", encoding="utf-8") as fp:
            fp.write("[1, 2]")
        with self.assertRaises(ValueError):
            config.load(self.main)

    def test_set_local_writes_the_key_and_keeps_the_others(self):
        self.write(self.local, {"public_hosts": ["mia.example"]})
        config.set_local(self.main, "accounts_enabled", True)
        with open(self.local, encoding="utf-8") as fp:
            self.assertEqual(json.load(fp), {"public_hosts": ["mia.example"], "accounts_enabled": True})
        config.set_local(self.main, "accounts_enabled", True)                              # idempotent
        self.assertTrue(config.load(self.main)["accounts_enabled"])
        os.remove(self.local)
        config.set_local(self.main, "accounts_enabled", True)                              # the file is made when it is missing
        self.assertTrue(os.path.exists(self.local))


if __name__ == "__main__":
    unittest.main()
