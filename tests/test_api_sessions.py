"""
N-2.1 T-01, the logic of login, session, throttling, password and logout (framework free): TC-API-003 login, TC-API-004 throttling, TC-API-005 no password stored or logged,
TC-API-006 no account by request, TC-API-017 logout. Runs on the mock of IF-102 and a fake clock.
Run: python tests/test_api_sessions.py
"""
import io
import json
import logging
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.join(HERE, "helpers", "mocks"))

import accounts                                       # noqa: E402
import api_sessions as S                              # noqa: E402
from if_102_storage import StorageMock                # noqa: E402
from markers import mark                              # noqa: E402


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def error_of(call):
    try:
        call()
    except S.ApiError as err:
        return err
    raise AssertionError("no ApiError raised")


class Sessions(unittest.TestCase):
    def setUp(self):
        self.store, self.clock = StorageMock(), Clock()
        for name, password in (("anna", "pw-anna-1"), ("ben", "pw-ben-123")):
            accounts.create(self.store, name, password, "setup")
        self.api = S.SessionService(self.store, clock=self.clock)

    @mark.req("REQ-API-003")
    def test_the_right_password_opens_a_session_and_a_wrong_one_does_not(self):
        """TC-API-003"""
        token = self.api.login("anna", "pw-anna-1")
        self.assertTrue(token)
        self.assertNotEqual(token, self.api.login("anna", "pw-anna-1"))             # every login is its own session
        for user, password in (("anna", "wrong"), ("nobody", "pw-anna-1"), ("anna", None)):
            err = error_of(lambda: self.api.login(user, password))
            self.assertEqual((err.status, err.code), (401, "bad_credentials"))       # an unknown account and a wrong password look the same

    @mark.req("REQ-API-004")
    def test_the_sixth_failed_login_in_a_minute_is_refused_even_with_the_right_password(self):
        """TC-API-004"""
        for _ in range(5):
            self.assertEqual(error_of(lambda: self.api.login("anna", "wrong")).status, 401)
        err = error_of(lambda: self.api.login("anna", "pw-anna-1"))
        self.assertEqual((err.status, err.code), (429, "throttled"))
        self.assertTrue(self.api.login("ben", "pw-ben-123"))                         # another account is not affected
        self.clock.now += 61
        self.assertTrue(self.api.login("anna", "pw-anna-1"))

    @mark.req("REQ-API-005")
    def test_no_password_is_stored_or_logged_after_ten_logins(self):
        """TC-API-005"""
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.DEBUG)
        self.addCleanup(logging.getLogger().removeHandler, handler)
        for i in range(10):
            self.api.login("anna", "pw-anna-1")
            error_of(lambda: self.api.login("ben", "wrong-password-%d" % i)) if i < 4 else self.api.login("ben", "pw-ben-123")
        stored = json.dumps([self.store.get("accounts", n) for n in self.store.ids("accounts")])
        for secret in ("pw-anna-1", "pw-ben-123", "wrong-password"):
            self.assertNotIn(secret, stored)
            self.assertNotIn(secret, stream.getvalue())

    @mark.req("REQ-API-006")
    def test_the_service_has_no_way_to_create_an_account(self):
        """TC-API-006: accounts are made by the owner on the machine (tools/accounts_cli.py), a request cannot create one"""
        self.assertFalse(hasattr(self.api, "create_account"))
        self.assertNotIn("carl", self.store.ids("accounts"))

    @mark.req("REQ-API-003")
    def test_whoami_and_the_own_password(self):
        token = self.api.login("ben", "pw-ben-123")
        self.assertEqual(self.api.whoami(token), {"user": "ben"})
        self.assertEqual(error_of(lambda: self.api.whoami("made-up")).status, 401)
        self.assertEqual(error_of(lambda: self.api.change_password(token, "wrong", "long-enough-1")).code, "bad_credentials")
        self.assertEqual(error_of(lambda: self.api.change_password(token, "pw-ben-123", "short")).code, "weak_password")
        self.assertEqual(self.api.change_password(token, "pw-ben-123", "long-enough-1"), {"changed": True})
        self.assertEqual(error_of(lambda: self.api.login("ben", "pw-ben-123")).status, 401)                    # the old password stops working
        self.assertTrue(self.api.login("ben", "long-enough-1"))

    @mark.req("REQ-API-017", "REQ-BE-077")
    def test_after_the_logout_the_same_session_is_refused(self):
        """TC-API-017"""
        first, second = self.api.login("anna", "pw-anna-1"), self.api.login("anna", "pw-anna-1")
        self.assertEqual(self.api.logout(first), {"loggedOut": True})
        for call in (lambda: self.api.whoami(first), lambda: self.api.logout(first), lambda: self.api.change_password(first, "pw-anna-1", "long-enough-1")):
            err = error_of(call)
            self.assertEqual((err.status, err.code), (401, "unauthenticated"))
        self.assertEqual(self.api.whoami(second), {"user": "anna"})                  # another session of the account is not touched
        self.assertTrue(self.api.login("anna", "pw-anna-1"))                         # and the account still works

    @mark.req("REQ-API-017")
    def test_the_sockets_of_the_session_are_dropped_by_the_listener(self):
        ended = []
        self.api.on_end(ended.append)
        token = self.api.login("anna", "pw-anna-1")
        self.api.logout(token)
        self.assertEqual(ended, [token])
        error_of(lambda: self.api.logout(token))
        self.assertEqual(ended, [token])                                              # a refused logout drops nothing twice

    def test_user_of_gives_the_account_to_the_other_layers(self):
        token = self.api.login("ben", "pw-ben-123")
        self.assertEqual(self.api.user_of(token), "ben")
        self.api.logout(token)
        self.assertIsNone(self.api.user_of(token))


if __name__ == "__main__":
    unittest.main()
