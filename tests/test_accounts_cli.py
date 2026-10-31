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
        """TC-API-005, TC-API-006: the owner creates an account on the machine; its password verifies, a wrong one does not, and no file holds the password (only its scrypt hash).

        Example: create anna, password pw-anna-1 twice -> exit 0; verify(anna, pw-anna-1) true; "pw-anna-1" in no file; algorithm scrypt.
        """
        # When: anna is created with the password typed twice
        self.assertEqual(self.go("create", "anna", "pw-anna-1", "pw-anna-1"), 0)
        # Then: the right password verifies, another does not
        self.assertTrue(accounts.verify(self.store(), "anna", "pw-anna-1"))
        self.assertFalse(accounts.verify(self.store(), "anna", "other-pw-1"))
        # Then: no file of the store holds the password, the record names scrypt
        text = "".join(open(os.path.join(root, f)).read() for root, _, files in os.walk(self.tmp.name) for f in files)
        self.assertNotIn("pw-anna-1", text)
        self.assertEqual(json.loads(open(os.path.join(self.tmp.name, "accounts", "anna.json")).read())[0]["doc"]["algorithm"], "scrypt")

    def test_mistakes_change_nothing(self):
        """A password that is too short, two passwords that differ or a name that exists already are refused (exit 1) and change nothing.

        Example: create anna short -> 1, no account; create anna again with pw-anna-9 -> 1, pw-anna-1 still verifies.
        """
        # When / Then: a short password and two different ones are refused, no account exists
        self.assertEqual(self.go("create", "anna", "short", "short"), 1)
        self.assertEqual(self.go("create", "anna", "pw-anna-1", "pw-anna-2"), 1)
        self.assertEqual(self.store().ids("accounts"), [])
        # Given: anna exists
        self.go("create", "anna", "pw-anna-1", "pw-anna-1")
        # When / Then: a second anna is refused and the first keeps her password
        self.assertEqual(self.go("create", "anna", "pw-anna-9", "pw-anna-9"), 1)                  # the name exists
        self.assertTrue(accounts.verify(self.store(), "anna", "pw-anna-1"))

    def test_password_and_list(self):
        """The owner changes a password (the old one stops working) and lists the accounts by name only.

        Example: password anna pw-anna-new -> 0, the new password verifies, pw-anna-1 does not; list -> ["anna"].
        """
        # Given: anna exists
        self.go("create", "anna", "pw-anna-1", "pw-anna-1")
        # When / Then: her password is changed, only the new one verifies
        self.assertEqual(self.go("password", "anna", "pw-anna-new", "pw-anna-new"), 0)
        self.assertTrue(accounts.verify(self.store(), "anna", "pw-anna-new"))
        self.assertFalse(accounts.verify(self.store(), "anna", "pw-anna-1"))
        # When / Then: the list shows her name and nothing else
        self.out.clear()
        self.assertEqual(self.go("list", None), 0)
        self.assertEqual(self.out, ["anna"])


if __name__ == "__main__":
    unittest.main()
