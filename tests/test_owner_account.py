"""The owner of the snapshots comes from `owner_account` in setup_cfg.json (G-V2.SNAPSHOT, REQ-WFM-066; owner decision 2026-11-19). Run with: python tests/test_owner_account.py"""
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import accounts                                           # noqa: E402
import constants                                          # noqa: E402
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402
from workflow_library import WorkflowLibrary, WorkflowLibraryError  # noqa: E402


class OwnerFromConfig(unittest.TestCase):
    def test_the_key_is_owner_account(self):
        self.assertEqual(constants.OWNER_ACCOUNT_KEY, "owner_account")

    def test_only_the_named_account_is_the_owner(self):
        is_owner = accounts.owner_check({"owner_account": "anna"})
        self.assertEqual((is_owner("anna"), is_owner("ben"), is_owner(""), is_owner(None)), (True, False, False, False))

    def test_without_a_usable_entry_nobody_is_the_owner(self):
        for cfg in ({}, {"owner_account": ""}, {"owner_account": None}, {"owner_account": 5}, {"owner_account": ["anna"]}):
            is_owner = accounts.owner_check(cfg)
            self.assertFalse(is_owner("anna"), cfg)
            self.assertFalse(is_owner(""), cfg)
            self.assertFalse(is_owner(None), cfg)

    def test_a_snapshot_of_the_real_library_follows_the_config(self):
        lib = WorkflowLibrary(Storage(FileBackend(tempfile.mkdtemp())), is_owner=accounts.owner_check({"owner_account": "anna"}))
        self.assertEqual(lib.snapshot("a", "anna")["author"], "anna")
        with self.assertRaises(WorkflowLibraryError) as caught:
            lib.snapshot("b", "ben")
        self.assertEqual(caught.exception.code, "forbidden")

    def test_the_app_gives_the_library_that_owner(self):
        """web_app.py cannot be imported in a test (it starts the service), so the line that builds the library is read as text"""
        text = open(os.path.join(os.path.dirname(HERE), "web_app.py"), encoding="utf-8").read()
        call = re.search(r"WorkflowLibrary\(([^\n]*)\)", text).group(1)
        self.assertIn("is_owner=accounts.owner_check(cfg)", call)


if __name__ == "__main__":
    unittest.main()
