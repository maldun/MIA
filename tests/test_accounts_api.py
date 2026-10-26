"""
N-2.1 T-01, the web side of login and logout (accounts_api.py): the routes of IF-101 (login, whoami, change_password, logout, accounts), the session cookie
(HttpOnly, SameSite=Strict, Secure on HTTPS, cleared at logout), and the sockets of a session that are dropped when it ends (REQ-API-017).
Needs flask: run with the MIA virtualenv / the image:  python tests/test_accounts_api.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.join(HERE, "helpers", "mocks"))

from flask import Flask                               # noqa: E402

import accounts                                       # noqa: E402
import accounts_api as A                              # noqa: E402
import api_sessions as S                              # noqa: E402
from if_102_storage import StorageMock                # noqa: E402
from markers import mark                              # noqa: E402


class FakeSocketio:
    def __init__(self):
        self.dropped = []

    def disconnect(self, sid):
        self.dropped.append(sid)


def make_app():
    store = StorageMock()
    accounts.create(store, "anna", "pw-anna-1", "setup")
    accounts.create(store, "ben", "pw-ben-123", "setup")
    service = S.SessionService(store, owner="anna")
    sockets = A.SocketSessions(service, FakeSocketio())
    app = Flask(__name__)
    app.register_blueprint(A.create_accounts_blueprint(service))
    return app, service, sockets


def login(client, user, password, **kw):
    return client.post("/api/login", json={"user": user, "password": password}, **kw)


class Routes(unittest.TestCase):
    def setUp(self):
        self.app, self.service, self.sockets = make_app()
        self.client = self.app.test_client()

    @mark.req("REQ-API-003")
    def test_login_sets_the_session_cookie_and_whoami_knows_the_account(self):
        reply = login(self.client, "anna", "pw-anna-1")
        self.assertEqual((reply.status_code, reply.get_json()), (200, {"ok": True}))
        cookie = reply.headers["Set-Cookie"]
        self.assertIn("mia_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertNotIn("Secure", cookie)                                         # a plain http test request
        self.assertEqual(self.client.get("/api/whoami").get_json(), {"user": "anna"})
        self.assertIn("Secure", login(self.client, "anna", "pw-anna-1", base_url="https://mia.example").headers["Set-Cookie"])

    @mark.req("REQ-API-003", "REQ-API-004")
    def test_wrong_password_is_401_and_the_sixth_failure_is_429(self):
        for _ in range(5):
            reply = login(self.client, "anna", "wrong")
            self.assertEqual((reply.status_code, reply.get_json()), (401, {"error": "bad_credentials"}))
        self.assertEqual((login(self.client, "anna", "pw-anna-1").status_code, ), (429,))
        self.assertEqual(login(self.client, "ben", "pw-ben-123").status_code, 200)

    def test_a_bad_body_is_a_401_and_not_a_crash(self):
        for body in (None, {}, {"user": "anna"}, {"user": 5, "password": [1]}):
            self.assertEqual(self.client.post("/api/login", json=body).status_code, 401)
        self.assertEqual(self.client.post("/api/login", data="not json", content_type="text/plain").status_code, 401)

    @mark.req("REQ-API-017", "REQ-BE-077")
    def test_logout_ends_the_session_clears_the_cookie_and_leaves_other_sessions(self):
        other = self.app.test_client()
        login(other, "anna", "pw-anna-1")
        login(self.client, "anna", "pw-anna-1")
        reply = self.client.post("/api/logout")
        self.assertEqual((reply.status_code, reply.get_json()), (200, {"loggedOut": True}))
        self.assertIn("mia_session=;", reply.headers["Set-Cookie"])
        self.assertIn("Max-Age=0", reply.headers["Set-Cookie"])
        self.assertEqual(self.client.get("/api/whoami").status_code, 401)
        self.assertEqual(self.client.post("/api/logout").status_code, 401)
        self.assertEqual(other.get("/api/whoami").get_json(), {"user": "anna"})

    def test_the_old_cookie_does_not_come_back_after_the_logout(self):
        login(self.client, "anna", "pw-anna-1")
        old = self.client.get_cookie("mia_session").value
        self.client.post("/api/logout")
        thief = self.app.test_client()
        thief.set_cookie("mia_session", old)
        self.assertEqual(thief.get("/api/whoami").status_code, 401)

    def test_change_password_and_owner_only_accounts(self):
        login(self.client, "ben", "pw-ben-123")
        self.assertEqual(self.client.post("/api/change_password", json={"old": "nope", "new": "long-enough-1"}).get_json(), {"error": "bad_credentials"})
        self.assertEqual(self.client.post("/api/change_password", json={"old": "pw-ben-123", "new": "short"}).status_code, 422)
        self.assertEqual(self.client.post("/api/change_password", json={"old": "pw-ben-123", "new": "long-enough-1"}).get_json(), {"changed": True})
        self.assertEqual(self.client.post("/api/accounts", json={"name": "carl", "password": "pw-carl-123"}).status_code, 403)
        owner = self.app.test_client()
        login(owner, "anna", "pw-anna-1")
        self.assertEqual(owner.post("/api/accounts", json={"name": "carl", "password": "pw-carl-123"}).status_code, 200)
        self.assertEqual(login(self.app.test_client(), "carl", "pw-carl-123").status_code, 200)

    @mark.req("REQ-API-003")
    def test_without_a_session_the_account_routes_are_401(self):
        for method, path in (("get", "/api/whoami"), ("post", "/api/logout"), ("post", "/api/change_password"), ("post", "/api/accounts")):
            self.assertEqual(getattr(self.client, method)(path, json={}).status_code, 401, path)


class Sockets(unittest.TestCase):
    @mark.req("REQ-API-017")
    def test_the_sockets_of_a_session_are_dropped_when_it_ends_and_only_those(self):
        app, service, sockets = make_app()
        token_a, token_b = service.login("anna", "pw-anna-1"), service.login("ben", "pw-ben-123")
        sockets.add(token_a, "sid1")
        sockets.add(token_a, "sid2")
        sockets.add(token_b, "sid3")
        sockets.remove("sid2")                                                    # a page that left by itself
        service.logout(token_a)
        self.assertEqual(sockets.socketio.dropped, ["sid1"])
        self.assertEqual(sockets.token_of("sid3"), token_b)
        self.assertIsNone(sockets.token_of("sid1"))

    def test_a_socket_without_a_valid_session_is_refused(self):
        app, service, sockets = make_app()
        self.assertFalse(sockets.accept("made-up", "sid1"))
        self.assertFalse(sockets.accept(None, "sid1"))
        token = service.login("anna", "pw-anna-1")
        self.assertTrue(sockets.accept(token, "sid2"))
        self.assertEqual(sockets.token_of("sid2"), token)


class Installed(unittest.TestCase):
    """install(): the blueprint and the socket guard on a real Flask-SocketIO app, as web_app.py uses them"""

    def setUp(self):
        from flask_socketio import SocketIO
        self.store = StorageMock()
        accounts.create(self.store, "anna", "pw-anna-1", "setup")
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        self.service, self.sockets = A.install(self.app, self.socketio, self.store, owner="anna")

        @self.socketio.on("connect")
        def connect(_auth=None):
            A.guard_connect(self.sockets)

        @self.socketio.on("disconnect")
        def disconnect(_reason=None):
            A.forget_socket(self.sockets)

    @mark.req("REQ-API-017", "REQ-BE-008")
    def test_a_socket_needs_a_session_and_is_dropped_at_the_logout(self):
        web = self.app.test_client()
        refused = self.socketio.test_client(self.app, flask_test_client=web)
        self.assertFalse(refused.is_connected())                                   # no session, no socket
        login(web, "anna", "pw-anna-1")
        sock = self.socketio.test_client(self.app, flask_test_client=web)
        self.assertTrue(sock.is_connected())
        web.post("/api/logout")
        self.assertFalse(sock.is_connected())                                      # the logout closed it
        self.assertEqual(self.sockets._by_sid, {})

    def test_a_socket_of_another_session_stays(self):
        a, b = self.app.test_client(), self.app.test_client()
        login(a, "anna", "pw-anna-1")
        login(b, "anna", "pw-anna-1")
        sa, sb = (self.socketio.test_client(self.app, flask_test_client=c) for c in (a, b))
        a.post("/api/logout")
        self.assertFalse(sa.is_connected())
        self.assertTrue(sb.is_connected())


if __name__ == "__main__":
    unittest.main()
