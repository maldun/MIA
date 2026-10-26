"""Accounts with a salted slow password hash (N-3.1 T-03): TC-SLY-005. Run with: python tests/test_accounts.py"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

import accounts                                  # noqa: E402
from markers import mark                         # noqa: E402
from storage import Storage                      # noqa: E402
from storage_files import FileBackend            # noqa: E402


def dump(folder):
    """Every byte stored under the folder, as one text."""
    out = []
    for root, _, files in os.walk(folder):
        for name in files:
            with open(os.path.join(root, name), encoding="utf-8") as handle:
                out.append(handle.read())
    return "\n".join(out)


class Accounts(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store = Storage(FileBackend(self.dir))

    @mark.req("REQ-SLY-005")
    def test_the_dump_has_no_password_and_equal_passwords_give_different_hashes(self):
        """TC-SLY-005: two accounts with the same password; the right one verifies, a wrong one does not."""
        accounts.create(self.store, "anna", "correct horse", "owner")
        accounts.create(self.store, "ben", "correct horse", "owner")
        self.assertNotIn("correct horse", dump(self.dir))
        self.assertNotEqual(self.store.get("accounts", "anna")["doc"]["hash"], self.store.get("accounts", "ben")["doc"]["hash"])
        self.assertTrue(accounts.verify(self.store, "anna", "correct horse"))
        self.assertFalse(accounts.verify(self.store, "anna", "wrong"))
        self.assertFalse(accounts.verify(self.store, "nobody", "correct horse"))

    @mark.req("REQ-SLY-005")
    def test_the_hash_is_scrypt_with_recorded_parameters(self):
        """The slow hash comes from the standard library and its parameters are stored with it, so they can be raised later."""
        accounts.create(self.store, "anna", "pw", "owner")
        doc = self.store.get("accounts", "anna")["doc"]
        self.assertEqual((doc["algorithm"], doc["n"], doc["r"], doc["p"]), ("scrypt", accounts.N, accounts.R, accounts.P))
        self.assertGreaterEqual(doc["n"], 2 ** 14)

    @mark.req("REQ-SLY-005")
    def test_a_password_change_is_a_new_version_and_the_old_password_stops_working(self):
        accounts.create(self.store, "anna", "old", "owner")
        accounts.set_password(self.store, "anna", "new", "anna")
        self.assertEqual(self.store.get("accounts", "anna")["version"], 2)
        self.assertTrue(accounts.verify(self.store, "anna", "new"))
        self.assertFalse(accounts.verify(self.store, "anna", "old"))
        self.assertNotIn("old", dump(self.dir).replace("owner", ""))

    @mark.req("REQ-SLY-005")
    def test_an_empty_password_or_name_is_refused_and_a_duplicate_account_too(self):
        for name, password in (("", "pw"), ("anna", ""), ("anna", None)):
            with self.subTest(name=name, password=password), self.assertRaises(ValueError):
                accounts.create(self.store, name, password, "owner")
        accounts.create(self.store, "anna", "pw", "owner")
        with self.assertRaises(ValueError):
            accounts.create(self.store, "anna", "other", "owner")
        self.assertTrue(accounts.verify(self.store, "anna", "pw"))

    @mark.req("REQ-SLY-005")
    def test_non_ascii_passwords_work(self):
        accounts.create(self.store, "zoë", "pässwörd ✓", "owner")
        self.assertTrue(accounts.verify(self.store, "zoë", "pässwörd ✓"))
        self.assertFalse(accounts.verify(self.store, "zoë", "passwoerd"))


if __name__ == "__main__":
    unittest.main()
