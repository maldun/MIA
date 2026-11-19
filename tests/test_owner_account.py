"""The owner of the snapshots is the account named by `owner_account` in setup_cfg.json; without a usable entry it is the first account made (G-V2.SNAPSHOT,
REQ-WFM-066; owner decisions 2026-11-19). Run with: python tests/test_owner_account.py"""
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import accounts                                           # noqa: E402
import storage as storage_module                          # noqa: E402
import constants                                          # noqa: E402
from storage import Storage                               # noqa: E402
from storage_files import FileBackend                     # noqa: E402
from workflow_library import WorkflowLibrary, WorkflowLibraryError  # noqa: E402


def store_with(*names):
    """a file storage with these accounts, made one after the other with a clock that moves one second per write"""
    store = Storage(FileBackend(tempfile.mkdtemp()))
    ticks = iter("2026-11-19T10:00:%02dZ" % n for n in range(60))
    with mock.patch.object(storage_module, "utc_now", lambda: next(ticks)):
        for name in names:
            accounts.create(store, name, "pw-" + name, "cli")
    return store


class OwnerFromConfig(unittest.TestCase):
    def test_the_key_is_owner_account(self):
        self.assertEqual(constants.OWNER_ACCOUNT_KEY, "owner_account")

    def test_the_account_named_in_the_config_is_the_owner(self):
        is_owner = accounts.owner_check({"owner_account": "ben"}, store_with("anna", "ben"))
        self.assertEqual((is_owner("ben"), is_owner("anna"), is_owner(""), is_owner(None)), (True, False, False, False))

    def test_without_a_usable_entry_the_first_account_made_is_the_owner(self):
        store = store_with("zoe", "anna", "ben")          # not the first by name: the first by time
        for cfg in ({}, {"owner_account": ""}, {"owner_account": None}, {"owner_account": 5}, {"owner_account": ["zoe"]}):
            is_owner = accounts.owner_check(cfg, store)
            self.assertEqual((is_owner("zoe"), is_owner("anna"), is_owner("ben"), is_owner(""), is_owner(None)), (True, False, False, False, False), cfg)

    def test_the_owner_is_found_at_the_time_of_the_call(self):
        store = store_with()
        is_owner = accounts.owner_check({}, store)
        self.assertFalse(is_owner("anna"))                  # no account yet: nobody
        accounts.create(store, "anna", "pw", "cli")
        self.assertTrue(is_owner("anna"))                   # the app was not restarted
        accounts.create(store, "ben", "pw", "cli")
        self.assertFalse(is_owner("ben"))                   # a later account never takes over

    def test_a_named_account_that_does_not_exist_is_still_the_only_owner(self):
        is_owner = accounts.owner_check({"owner_account": "typo"}, store_with("anna"))
        self.assertEqual((is_owner("typo"), is_owner("anna")), (True, False))      # the setting is explicit; it does not fall back

    def test_a_snapshot_of_the_real_library_follows_the_default_and_the_setting(self):
        store = store_with("anna", "ben")
        for cfg, owner, other in (({}, "anna", "ben"), ({"owner_account": "ben"}, "ben", "anna")):
            lib = WorkflowLibrary(store, is_owner=accounts.owner_check(cfg, store))
            self.assertEqual(lib.snapshot("s-" + owner, owner)["author"], owner)
            with self.assertRaises(WorkflowLibraryError) as caught:
                lib.snapshot("x-" + other, other)
            self.assertEqual(caught.exception.code, "forbidden")

    def test_the_app_gives_the_library_that_owner(self):
        """web_app.py cannot be imported in a test (it starts the service), so the line that builds the library is read as text"""
        text = open(os.path.join(os.path.dirname(HERE), "web_app.py"), encoding="utf-8").read()
        call = re.search(r"WorkflowLibrary\(([^\n]*)\)", text).group(1)
        self.assertIn("is_owner=accounts.owner_check(cfg, _votes_store)", call)


if __name__ == "__main__":
    unittest.main()
