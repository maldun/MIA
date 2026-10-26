"""
tools/accounts_cli.py: create, change a password, list; the password is asked for (twice), never an argument, and never stored.
Run: python tests/test_accounts_cli.py
"""
import argparse
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "tools"))

import accounts                                       # noqa: E402
import accounts_cli as C                              # noqa: E402
from storage import Storage                           # noqa: E402
from storage_files import FileBackend                 # noqa: E402


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = []

    def go(self, command, name, *passwords):
        answers = iter(passwords)
        return C.run(argparse.Namespace(command=command, name=name, dir=self.tmp.name), ask=lambda prompt: next(answers), show=self.out.append)

    def store(self):
        return Storage(FileBackend(self.tmp.name))

    def test_create_then_the_password_verifies_and_is_nowhere_in_the_files(self):
        self.assertEqual(self.go("create", "anna", "pw-anna-1", "pw-anna-1"), 0)
        self.assertTrue(accounts.verify(self.store(), "anna", "pw-anna-1"))
        self.assertFalse(accounts.verify(self.store(), "anna", "other-pw-1"))
        text = "".join(open(os.path.join(root, f)).read() for root, _, files in os.walk(self.tmp.name) for f in files)
        self.assertNotIn("pw-anna-1", text)
        self.assertEqual(json.loads(open(os.path.join(self.tmp.name, "accounts", "anna.json")).read())[0]["doc"]["algorithm"], "scrypt")

    def test_mistakes_change_nothing(self):
        self.assertEqual(self.go("create", "anna", "short", "short"), 1)
        self.assertEqual(self.go("create", "anna", "pw-anna-1", "pw-anna-2"), 1)
        self.assertEqual(self.store().ids("accounts"), [])
        self.go("create", "anna", "pw-anna-1", "pw-anna-1")
        self.assertEqual(self.go("create", "anna", "pw-anna-9", "pw-anna-9"), 1)                  # the name exists
        self.assertTrue(accounts.verify(self.store(), "anna", "pw-anna-1"))

    def test_password_and_list(self):
        self.go("create", "anna", "pw-anna-1", "pw-anna-1")
        self.assertEqual(self.go("password", "anna", "pw-anna-new", "pw-anna-new"), 0)
        self.assertTrue(accounts.verify(self.store(), "anna", "pw-anna-new"))
        self.assertFalse(accounts.verify(self.store(), "anna", "pw-anna-1"))
        self.out.clear()
        self.assertEqual(self.go("list", None), 0)
        self.assertEqual(self.out, ["anna"])


if __name__ == "__main__":
    unittest.main()
