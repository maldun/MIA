"""
N-2.1 T-01 and T-02, the web side of the accounts (accounts_api.py):
 T-01  the routes of IF-101 (login, whoami, change_password, logout), the session cookie, the sockets of a session (REQ-API-003, -004, -017)
 T-02  every request needs a session except the page and its files and the login (REQ-API-007), a foreign origin is refused (REQ-API-007), a password only over a
       secure channel (REQ-API-008), the account of every change is recorded (REQ-API-009), no roles (REQ-API-010), calls of our own speech process carry a secret
Needs flask: run with the image:  bash tools/run_in_image.sh tests/test_accounts_api.py
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.join(HERE, "helpers", "mocks"))

from flask import Flask, jsonify, request             # noqa: E402

import accounts                                       # noqa: E402
import accounts_api as A                              # noqa: E402
import api_sessions as S                              # noqa: E402
from if_102_storage import StorageMock                # noqa: E402
from markers import mark                              # noqa: E402

LAN = {"REMOTE_ADDR": "192.168.1.50"}
LOCAL = {"REMOTE_ADDR": "127.0.0.1"}
ORIGIN = "https://mia.example"


class FakeSocketio:
    def __init__(self):
        self.dropped = []

    def disconnect(self, sid):
        self.dropped.append(sid)


def make_store():
    store = StorageMock()
    accounts.create(store, "anna", "pw-anna-1", "setup")
    accounts.create(store, "ben", "pw-ben-123", "setup")
    return store


def make_app(**options):
    """a Flask app with the accounts installed and a few stand-in routes: a shared data route, the page, a static file, an internal upload"""
    app = Flask(__name__)
    shared = {"persona": "calm"}

    @app.get("/")
    def page():
        return "page"

    @app.get("/static/chat/app.js")
    def static_file():
        return "js"

    @app.get("/api/data")
    def read():
        return jsonify(shared)

    @app.post("/api/data")
    def change():
        shared.update(request.get_json())
        return jsonify(shared)

    @app.post("/api/broken")
    def broken():
        return jsonify({"error": "invalid"}), 422

    @app.post("/upload")
    def upload():
        return "stored"

    settings = dict(open_paths=("/",), open_prefixes=("/static/",), internal_paths=("/upload",), internal_token="s3cret", allowed_origins=lambda: [ORIGIN], changes=A.ChangeLog(None))
    settings.update(options)
    service, sockets = A.install(app, FakeSocketio(), make_store(), **settings)
    return app, service, sockets, settings["changes"]


def login(client, user, password, **kw):
    return client.post("/api/login", json={"user": user, "password": password}, **kw)


class Routes(unittest.TestCase):
    def setUp(self):
        self.app, self.service, self.sockets, self.changes = make_app()
        self.client = self.app.test_client()

    @mark.req("REQ-API-003")
    def test_login_sets_the_session_cookie_and_whoami_knows_the_account(self):
        reply = login(self.client, "anna", "pw-anna-1")
        self.assertEqual((reply.status_code, reply.get_json()), (200, {"ok": True}))
        cookie = reply.headers["Set-Cookie"]
        self.assertIn("mia_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertNotIn("Secure", cookie)                                         # a plain http test request from localhost
        self.assertEqual(self.client.get("/api/whoami").get_json(), {"user": "anna"})
        self.assertIn("Secure", login(self.client, "anna", "pw-anna-1", base_url="https://mia.example").headers["Set-Cookie"])

    @mark.req("REQ-API-003", "REQ-API-004")
    def test_wrong_password_is_401_and_the_sixth_failure_is_429(self):
        for _ in range(5):
            reply = login(self.client, "anna", "wrong")
            self.assertEqual((reply.status_code, reply.get_json()), (401, {"error": "bad_credentials"}))
        self.assertEqual(login(self.client, "anna", "pw-anna-1").status_code, 429)
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

    def test_change_password(self):
        login(self.client, "ben", "pw-ben-123")
        self.assertEqual(self.client.post("/api/change_password", json={"old": "nope", "new": "long-enough-1"}).get_json(), {"error": "bad_credentials"})
        self.assertEqual(self.client.post("/api/change_password", json={"old": "pw-ben-123", "new": "short"}).status_code, 422)
        self.assertEqual(self.client.post("/api/change_password", json={"old": "pw-ben-123", "new": "long-enough-1"}).get_json(), {"changed": True})

    @mark.req("REQ-API-006")
    def test_there_is_no_way_to_create_an_account_over_the_web(self):
        """decided 2026-10-27: accounts are made by the owner on the machine (tools/accounts_cli.py), not by a request"""
        login(self.client, "anna", "pw-anna-1")
        self.assertEqual(self.client.post("/api/accounts", json={"name": "carl", "password": "pw-carl-123"}).status_code, 404)
        self.assertFalse(hasattr(self.service, "create_account"))


class EveryRequestAuthenticated(unittest.TestCase):
    def setUp(self):
        self.app, self.service, self.sockets, self.changes = make_app()
        self.client = self.app.test_client()

    @mark.req("REQ-API-007")
    def test_without_a_session_only_the_page_its_files_and_the_login_are_open(self):
        """TC-API-007"""
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/static/chat/app.js").status_code, 200)
        self.assertEqual(login(self.client, "anna", "wrong").status_code, 401)                        # reachable, and says no
        for method, path in (("get", "/api/data"), ("post", "/api/data"), ("get", "/api/whoami"), ("post", "/api/logout"), ("post", "/upload"), ("get", "/nothing-here")):
            reply = getattr(self.client, method)(path, json={})
            self.assertEqual((reply.status_code, reply.get_json()), (401, {"error": "unauthenticated"}), path)

    @mark.req("REQ-API-007")
    def test_with_a_session_the_request_goes_through(self):
        login(self.client, "anna", "pw-anna-1")
        self.assertEqual(self.client.get("/api/data").get_json(), {"persona": "calm"})

    @mark.req("REQ-API-007")
    def test_a_foreign_origin_is_refused_even_with_a_session(self):
        """TC-API-007"""
        login(self.client, "anna", "pw-anna-1")
        for method in ("get", "post"):
            reply = getattr(self.client, method)("/api/data", json={}, headers={"Origin": "https://evil.example"})
            self.assertEqual((reply.status_code, reply.get_json()), (403, {"error": "bad_origin"}), method)
        self.assertEqual(self.client.get("/api/data", headers={"Origin": ORIGIN}).status_code, 200)       # our own page
        self.assertEqual(self.client.get("/api/data").status_code, 200)                                    # no Origin header: not a browser page
        self.assertEqual(login(self.app.test_client(), "ben", "pw-ben-123", headers={"Origin": "https://evil.example"}).status_code, 403)   # also the login

    @mark.req("REQ-API-007")
    def test_the_speech_process_passes_with_the_secret_on_its_paths_only(self):
        self.assertEqual(self.client.post("/upload", headers={A.INTERNAL_HEADER: "s3cret"}).status_code, 200)
        self.assertEqual(self.client.post("/upload", headers={A.INTERNAL_HEADER: "guess"}).status_code, 401)
        self.assertEqual(self.client.get("/api/data", headers={A.INTERNAL_HEADER: "s3cret"}).status_code, 401)        # the secret opens nothing else

    def test_without_an_internal_token_configured_nothing_is_internal(self):
        app, *_ = make_app(internal_token=None)
        self.assertEqual(app.test_client().post("/upload", headers={A.INTERNAL_HEADER: ""}).status_code, 401)

    @mark.req("REQ-API-007")
    def test_the_socket_account_is_the_rate_limit_key(self):
        token = self.service.login("anna", "pw-anna-1")
        self.sockets.add(token, "sid1")
        self.sockets.add(self.service.login("anna", "pw-anna-1"), "sid2")
        self.assertEqual({self.sockets.account_of("sid1"), self.sockets.account_of("sid2")}, {"anna"})        # two devices of a user share one limit
        self.assertIsNone(self.sockets.account_of("nobody"))


class SecureChannel(unittest.TestCase):
    def setUp(self):
        self.app, self.service, self.sockets, self.changes = make_app()

    @mark.req("REQ-API-008")
    def test_a_password_over_plain_http_from_a_lan_address_is_refused(self):
        """TC-API-008"""
        client = self.app.test_client()
        reply = login(client, "anna", "pw-anna-1", environ_overrides=LAN)
        self.assertEqual((reply.status_code, reply.get_json()), (403, {"error": "insecure_channel"}))
        self.assertNotIn("Set-Cookie", reply.headers)
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=LOCAL).status_code, 200)                  # localhost may
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=LAN, base_url="https://mia.example").status_code, 200)   # https may
        self.assertEqual(client.post("/api/change_password", json={"old": "pw-anna-1", "new": "long-enough-1"}, environ_overrides=LAN).status_code, 403)

    @mark.req("REQ-API-008")
    def test_a_forwarded_https_counts_only_from_the_proxy_on_this_machine(self):
        client = self.app.test_client()
        headers = {"X-Forwarded-Proto": "https"}
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=LAN, headers=headers).status_code, 403)    # anybody can write that header
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=LOCAL, headers=headers).status_code, 200)

    def test_a_wrong_password_is_not_a_reason_to_hide_the_channel_error(self):
        self.assertEqual(login(self.app.test_client(), "anna", "wrong", environ_overrides=LAN).status_code, 403)


class Attribution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "changes.jsonl")
        self.app, self.service, self.sockets, self.changes = make_app(changes=A.ChangeLog(self.path))

    @mark.req("REQ-API-009")
    def test_every_change_of_a_scripted_session_carries_the_account(self):
        """TC-API-009: 100 %"""
        anna, ben = self.app.test_client(), self.app.test_client()
        login(anna, "anna", "pw-anna-1")
        login(ben, "ben", "pw-ben-123")
        script = [(anna, {"persona": "warm"}), (ben, {"persona": "dry"}), (anna, {"persona": "calm"}), (ben, {"x": 1}), (ben, {"y": 2})]
        for client, body in script:
            self.assertEqual(client.post("/api/data", json=body).status_code, 200)
        anna.get("/api/data")                                                       # a read is no change
        anna.post("/api/broken", json={})                                           # a refused change did not happen
        rows = [json.loads(line) for line in open(self.path)]
        self.assertEqual([r["account"] for r in rows], ["anna", "ben", "anna", "ben", "ben"])
        self.assertTrue(all(r["action"] == "POST" and r["target"] == "/api/data" and r["time"] for r in rows))
        self.assertEqual(self.changes.read(), rows)

    @mark.req("REQ-API-009")
    def test_login_and_logout_are_not_changes_of_shared_data(self):
        client = self.app.test_client()
        login(client, "anna", "pw-anna-1")
        client.post("/api/logout")
        self.assertFalse(os.path.exists(self.path))

    @mark.req("REQ-API-009")
    def test_a_socket_event_can_be_recorded_without_its_content(self):
        self.changes.record("anna", "chat_send", "")
        self.assertEqual([(r["account"], r["action"]) for r in self.changes.read()], [("anna", "chat_send")])


class Everyone(unittest.TestCase):
    @mark.req("REQ-API-010")
    def test_a_second_user_sees_and_changes_what_the_first_user_changed(self):
        """TC-API-010: no roles, no per-user data"""
        app, *_ = make_app()
        anna, ben = app.test_client(), app.test_client()
        login(anna, "anna", "pw-anna-1")
        login(ben, "ben", "pw-ben-123")
        anna.post("/api/data", json={"persona": "anna's persona"})
        self.assertEqual(ben.get("/api/data").get_json()["persona"], "anna's persona")
        ben.post("/api/data", json={"persona": "ben's persona"})
        self.assertEqual(anna.get("/api/data").get_json()["persona"], "ben's persona")


class Sockets(unittest.TestCase):
    @mark.req("REQ-API-017")
    def test_the_sockets_of_a_session_are_dropped_when_it_ends_and_only_those(self):
        app, service, sockets, _ = make_app()
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
        app, service, sockets, _ = make_app()
        self.assertFalse(sockets.accept("made-up", "sid1"))
        self.assertFalse(sockets.accept(None, "sid1"))
        token = service.login("anna", "pw-anna-1")
        self.assertTrue(sockets.accept(token, "sid2"))
        self.assertEqual(sockets.token_of("sid2"), token)


class Installed(unittest.TestCase):
    """install(): on a real Flask-SocketIO app, as web_app.py uses it"""

    def setUp(self):
        from flask_socketio import SocketIO
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        self.service, self.sockets = A.install(self.app, self.socketio, make_store(), allowed_origins=lambda: [ORIGIN])

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
