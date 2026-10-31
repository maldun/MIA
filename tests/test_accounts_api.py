"""
N-2.1 T-01 and T-02, the web side of the accounts (accounts_api.py):
 T-01  the routes of IF-101 (login, whoami, change_password, logout), the session cookie, the sockets of a session (REQ-API-003, -004, -017)
 T-02  every request needs a session except the page and its files and the login (REQ-API-007), a foreign origin is refused (REQ-API-007), a password only over a
       secure channel (REQ-API-008), the account of every change is recorded (REQ-API-009), no roles (REQ-API-010, tested on the real routes in tests/test_accounts_wiring.py), calls of our own speech process carry a secret
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
        """TC-API-003: a login sets the session cookie (HttpOnly, SameSite=Strict; Secure over HTTPS, not over plain HTTP from localhost) and whoami names the account.

        Example: POST /api/login anna, pw-anna-1 -> 200 {ok: true}, Set-Cookie mia_session=...; HttpOnly; SameSite=Strict; GET /api/whoami -> {user: anna}.
        """
        # When: anna logs in over plain HTTP from localhost
        reply = login(self.client, "anna", "pw-anna-1")
        self.assertEqual((reply.status_code, reply.get_json()), (200, {"ok": True}))
        # Then: the cookie is HttpOnly and strict, not Secure; whoami knows anna; over HTTPS the cookie is Secure
        cookie = reply.headers["Set-Cookie"]
        self.assertIn("mia_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertNotIn("Secure", cookie)                                         # a plain http test request from localhost
        self.assertEqual(self.client.get("/api/whoami").get_json(), {"user": "anna"})
        self.assertIn("Secure", login(self.client, "anna", "pw-anna-1", base_url="https://mia.example").headers["Set-Cookie"])

    @mark.req("REQ-API-003", "REQ-API-004")
    def test_wrong_password_is_401_and_the_sixth_failure_is_429(self):
        """TC-API-003, TC-API-004: a wrong password is 401 bad_credentials; after five failures the next login of the account is 429, also with the right password; another account still logs in.

        Example: 5 x login(anna, wrong) -> 401; login(anna, pw-anna-1) -> 429; login(ben, pw-ben-123) -> 200.
        """
        # Given / Then: five wrong logins of anna, each 401
        for _ in range(5):
            reply = login(self.client, "anna", "wrong")
            self.assertEqual((reply.status_code, reply.get_json()), (401, {"error": "bad_credentials"}))
        # When / Then: her right password is throttled, ben's login is not
        self.assertEqual(login(self.client, "anna", "pw-anna-1").status_code, 429)
        self.assertEqual(login(self.client, "ben", "pw-ben-123").status_code, 200)

    def test_a_bad_body_is_a_401_and_not_a_crash(self):
        """TC-API-003: a login body that is missing, empty, without a password, with values of the wrong type (a number, a list or an object as user, V-3) or not JSON is 401, never a 500.

        Example: POST /api/login {user: [anna], password: x} -> 401.
        """
        # When / Then: every bad JSON body is 401
        for body in (None, {}, {"user": "anna"}, {"user": 5, "password": [1]}, {"user": ["anna"], "password": "x"}, {"user": {}, "password": "x"}):     # V-3: a list or object as user
            self.assertEqual(self.client.post("/api/login", json=body).status_code, 401)
        # When / Then: a body that is not JSON is 401 too
        self.assertEqual(self.client.post("/api/login", data="not json", content_type="text/plain").status_code, 401)

    @mark.req("REQ-API-017", "REQ-BE-077")
    def test_logout_ends_the_session_clears_the_cookie_and_leaves_other_sessions(self):
        """TC-API-017: the logout answers {loggedOut: true}, clears the cookie, and the session is refused afterwards; another session of the same account stays.

        Example: POST /api/logout -> 200, Set-Cookie mia_session=; Max-Age=0; GET /api/whoami -> 401; the other browser -> {user: anna}.
        """
        # Given: anna logged in on two browsers
        other = self.app.test_client()
        login(other, "anna", "pw-anna-1")
        login(self.client, "anna", "pw-anna-1")
        # When: the first logs out
        reply = self.client.post("/api/logout")
        # Then: the cookie is cleared, the session refused, the other browser still in
        self.assertEqual((reply.status_code, reply.get_json()), (200, {"loggedOut": True}))
        self.assertIn("mia_session=;", reply.headers["Set-Cookie"])
        self.assertIn("Max-Age=0", reply.headers["Set-Cookie"])
        self.assertEqual(self.client.get("/api/whoami").status_code, 401)
        self.assertEqual(self.client.post("/api/logout").status_code, 401)
        self.assertEqual(other.get("/api/whoami").get_json(), {"user": "anna"})

    def test_the_old_cookie_does_not_come_back_after_the_logout(self):
        """TC-API-017: a cookie copied before the logout opens nothing afterwards.

        Example: anna's old mia_session value set in another browser after her logout -> GET /api/whoami 401.
        """
        # Given: anna's session cookie, then her logout
        login(self.client, "anna", "pw-anna-1")
        old = self.client.get_cookie("mia_session").value
        self.client.post("/api/logout")
        # When: another browser uses the old cookie
        thief = self.app.test_client()
        thief.set_cookie("mia_session", old)
        # Then: it is refused
        self.assertEqual(thief.get("/api/whoami").status_code, 401)

    def test_change_password(self):
        """TC-API-003: a user changes the own password over the route: a wrong old password is bad_credentials, a short new one 422, the right change {changed: true}.

        Example: POST /api/change_password {old: pw-ben-123, new: long-enough-1} -> {changed: true}.
        """
        # Given: ben's session
        login(self.client, "ben", "pw-ben-123")
        # When / Then: wrong old password, weak new one, then the right change
        self.assertEqual(self.client.post("/api/change_password", json={"old": "nope", "new": "long-enough-1"}).get_json(), {"error": "bad_credentials"})
        self.assertEqual(self.client.post("/api/change_password", json={"old": "pw-ben-123", "new": "short"}).status_code, 422)
        self.assertEqual(self.client.post("/api/change_password", json={"old": "pw-ben-123", "new": "long-enough-1"}).get_json(), {"changed": True})

    @mark.req("REQ-API-006")
    def test_there_is_no_way_to_create_an_account_over_the_web(self):
        """TC-API-006: accounts are made by the owner on the machine (tools/accounts_cli.py, decided 2026-10-27), not by a request; there is no route and no service operation for it.

        Example: POST /api/accounts {name: carl} with a session -> 404.
        """
        # Given: anna's session
        login(self.client, "anna", "pw-anna-1")
        # When / Then: the route does not exist and the service cannot create one
        self.assertEqual(self.client.post("/api/accounts", json={"name": "carl", "password": "pw-carl-123"}).status_code, 404)
        self.assertFalse(hasattr(self.service, "create_account"))


class EveryRequestAuthenticated(unittest.TestCase):
    def setUp(self):
        self.app, self.service, self.sockets, self.changes = make_app()
        self.client = self.app.test_client()

    @mark.req("REQ-API-007")
    def test_without_a_session_only_the_page_its_files_and_the_login_are_open(self):
        """TC-API-007: without a session only the page, its static files and the login answer; every other route, also an unknown one, is 401 unauthenticated.

        Example: GET / -> 200; GET /api/data -> 401 {error: unauthenticated}; GET /nothing-here -> 401.
        """
        # When / Then: the page, its file and the login are reachable
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/static/chat/app.js").status_code, 200)
        self.assertEqual(login(self.client, "anna", "wrong").status_code, 401)                        # reachable, and says no
        # When / Then: everything else is refused
        for method, path in (("get", "/api/data"), ("post", "/api/data"), ("get", "/api/whoami"), ("post", "/api/logout"), ("post", "/upload"), ("get", "/nothing-here")):
            reply = getattr(self.client, method)(path, json={})
            self.assertEqual((reply.status_code, reply.get_json()), (401, {"error": "unauthenticated"}), path)

    @mark.req("REQ-API-007")
    def test_with_a_session_the_request_goes_through(self):
        """TC-API-007: with a session a route answers.

        Example: anna logged in, GET /api/data -> {persona: calm}.
        """
        login(self.client, "anna", "pw-anna-1")
        self.assertEqual(self.client.get("/api/data").get_json(), {"persona": "calm"})

    @mark.req("REQ-API-007")
    def test_a_foreign_origin_is_refused_even_with_a_session(self):
        """TC-API-007: a request with a foreign Origin is 403 bad_origin even with a session, also the login; our own origin and no Origin header pass.

        Example: GET /api/data with Origin https://evil.example -> 403 {error: bad_origin}; with https://mia.example -> 200.
        """
        # Given: anna's session
        login(self.client, "anna", "pw-anna-1")
        # When / Then: a foreign origin is refused for reads and writes
        for method in ("get", "post"):
            reply = getattr(self.client, method)("/api/data", json={}, headers={"Origin": "https://evil.example"})
            self.assertEqual((reply.status_code, reply.get_json()), (403, {"error": "bad_origin"}), method)
        # When / Then: our own origin and a request without Origin pass; a foreign login is refused
        self.assertEqual(self.client.get("/api/data", headers={"Origin": ORIGIN}).status_code, 200)       # our own page
        self.assertEqual(self.client.get("/api/data").status_code, 200)                                    # no Origin header: not a browser page
        self.assertEqual(login(self.app.test_client(), "ben", "pw-ben-123", headers={"Origin": "https://evil.example"}).status_code, 403)   # also the login

    @mark.req("REQ-API-007")
    def test_the_speech_process_passes_with_the_secret_on_its_paths_only(self):
        """TC-API-007: our own speech process passes without a session with the internal secret, and only on its own paths.

        Example: POST /upload with X-MIA-Internal s3cret -> 200; with guess -> 401; GET /api/data with s3cret -> 401.
        """
        # When / Then: the right secret on /upload passes, a wrong one and another path do not
        self.assertEqual(self.client.post("/upload", headers={A.INTERNAL_HEADER: "s3cret"}).status_code, 200)
        self.assertEqual(self.client.post("/upload", headers={A.INTERNAL_HEADER: "guess"}).status_code, 401)
        self.assertEqual(self.client.get("/api/data", headers={A.INTERNAL_HEADER: "s3cret"}).status_code, 401)        # the secret opens nothing else

    def test_without_an_internal_token_configured_nothing_is_internal(self):
        """TC-API-007: without a configured secret no request counts as internal, also not one with an empty header.

        Example: internal_token None, POST /upload with an empty X-MIA-Internal -> 401.
        """
        app, *_ = make_app(internal_token=None)
        self.assertEqual(app.test_client().post("/upload", headers={A.INTERNAL_HEADER: ""}).status_code, 401)

    @mark.req("REQ-API-007")
    def test_the_socket_account_is_the_rate_limit_key(self):
        """TC-API-007: two sockets of the same account give the same account, which is the key of the message rate limit; an unknown socket has none.

        Example: sid1 and sid2 of anna's two sessions -> account_of both anna; account_of(nobody) -> None.
        """
        # Given: two sockets of two sessions of anna
        token = self.service.login("anna", "pw-anna-1")
        self.sockets.add(token, "sid1")
        self.sockets.add(self.service.login("anna", "pw-anna-1"), "sid2")
        # When / Then: both name anna, an unknown socket nobody
        self.assertEqual({self.sockets.account_of("sid1"), self.sockets.account_of("sid2")}, {"anna"})        # two devices of a user share one limit
        self.assertIsNone(self.sockets.account_of("nobody"))


class SecureChannel(unittest.TestCase):
    def setUp(self):
        self.app, self.service, self.sockets, self.changes = make_app()

    @mark.req("REQ-API-008")
    def test_a_password_over_plain_http_from_a_lan_address_is_refused(self):
        """TC-API-008: a password over plain HTTP from a LAN address is 403 insecure_channel and sets no cookie; from localhost or over HTTPS it is checked; the password change is guarded the same way.

        Example: login from 192.168.1.50 over http -> 403 {error: insecure_channel}; from 127.0.0.1 -> 200.
        """
        # Given: a browser
        client = self.app.test_client()
        # When / Then: plain HTTP from the LAN is refused without a cookie
        reply = login(client, "anna", "pw-anna-1", environ_overrides=LAN)
        self.assertEqual((reply.status_code, reply.get_json()), (403, {"error": "insecure_channel"}))
        self.assertNotIn("Set-Cookie", reply.headers)
        # When / Then: localhost and HTTPS may; a password change from the LAN over http may not
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=LOCAL).status_code, 200)                  # localhost may
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=LAN, base_url="https://mia.example").status_code, 200)   # https may
        self.assertEqual(client.post("/api/change_password", json={"old": "pw-anna-1", "new": "long-enough-1"}, environ_overrides=LAN).status_code, 403)

    @mark.req("REQ-API-008")
    def test_a_forwarded_https_counts_only_from_the_proxy_on_this_machine(self):
        """TC-API-008: X-Forwarded-Proto https counts only from this machine (the proxy), not from a LAN address that writes it itself.

        Example: login from 192.168.1.50 with X-Forwarded-Proto https -> 403; from 127.0.0.1 -> 200.
        """
        # Given: a browser and the header
        client = self.app.test_client()
        headers = {"X-Forwarded-Proto": "https"}
        # When / Then: from the LAN the header does not count, from localhost it does
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=LAN, headers=headers).status_code, 403)    # anybody can write that header
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=LOCAL, headers=headers).status_code, 200)

    def test_a_wrong_password_is_not_a_reason_to_hide_the_channel_error(self):
        """TC-API-008: over plain HTTP from the LAN the channel is refused before the password is checked, also a wrong one.

        Example: login(anna, wrong) from 192.168.1.50 over http -> 403, not 401.
        """
        self.assertEqual(login(self.app.test_client(), "anna", "wrong", environ_overrides=LAN).status_code, 403)


class TrustedProxy(unittest.TestCase):
    """found 2026-10-29 in the compose stack: MIA sees every connection from the podman network (the https service is 10.89.1.5, a connection to the published port is 10.89.1.4), never from
    127.0.0.1, so a login was refused with insecure_channel on every way in. The proxies whose X-Forwarded-Proto counts are named in the configuration (`trusted_proxies`: addresses,
    networks or host names); nothing is trusted by default"""
    PROXY = {"REMOTE_ADDR": "10.89.1.5"}
    OTHER = {"REMOTE_ADDR": "10.89.1.9"}
    HTTPS = {"X-Forwarded-Proto": "https"}

    def client(self, **options):
        return make_app(**options)[0].test_client()

    def test_nothing_is_trusted_by_default(self):
        """TC-API-008: without trusted_proxies the header X-Forwarded-Proto of the https service does not count.

        Example: login from 10.89.1.5 with X-Forwarded-Proto https, no trusted proxy -> 403.
        """
        self.assertEqual(login(self.client(), "anna", "pw-anna-1", environ_overrides=self.PROXY, headers=self.HTTPS).status_code, 403)

    def test_https_forwarded_by_a_trusted_proxy_counts(self):
        """TC-API-008: HTTPS forwarded by a proxy named in trusted_proxies counts as a secure channel.

        Example: trusted_proxies [10.89.1.5], login from 10.89.1.5 with X-Forwarded-Proto https -> 200.
        """
        # Given: the https service is trusted
        client = self.client(trusted_proxies=["10.89.1.5"])
        # When / Then: its forwarded HTTPS counts
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=self.PROXY, headers=self.HTTPS).status_code, 200)

    def test_the_header_from_any_other_address_does_not_and_a_trusted_proxy_without_it_does_not(self):
        """TC-API-008: the header from another address does not count, and the trusted proxy without it (or with http) is plain HTTP.

        Example: from 10.89.1.9 with https -> 403; from 10.89.1.5 without the header -> 403; with http -> 403.
        """
        # Given: one trusted proxy
        client = self.client(trusted_proxies=["10.89.1.5"])
        # When / Then: another sender, no header and http are all refused
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=self.OTHER, headers=self.HTTPS).status_code, 403)       # anybody can write the header
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=self.PROXY).status_code, 403)                            # plain http through the proxy
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=self.PROXY, headers={"X-Forwarded-Proto": "http"}).status_code, 403)

    def test_a_network_covers_its_addresses_and_only_those(self):
        """TC-API-008: a trusted network covers its addresses and no others.

        Example: trusted 10.89.1.0/24 -> from 10.89.1.9 200; from 10.89.2.5 403.
        """
        # Given: a trusted network
        client = self.client(trusted_proxies=["10.89.1.0/24"])
        # When / Then: an address inside counts, one outside does not
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=self.OTHER, headers=self.HTTPS).status_code, 200)
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides={"REMOTE_ADDR": "10.89.2.5"}, headers=self.HTTPS).status_code, 403)

    def test_a_host_name_is_resolved_to_the_addresses_of_that_container(self):
        """TC-API-008: a trusted host name stands for the addresses it resolves to, and the answer is kept for a while instead of resolving every request.

        Example: trusted [https] resolving to 10.89.1.5 -> from 10.89.1.5 200, from 10.89.1.9 403; at most 2 lookups.
        """
        # Given: a resolver that knows the https container
        asked = []

        def resolve(name):
            asked.append(name)
            return ["10.89.1.5"] if name == "https" else []
        client = self.client(trusted_proxies=["https"], resolve_host=resolve)
        # When / Then: its address counts, another does not, the name was resolved at most twice
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=self.PROXY, headers=self.HTTPS).status_code, 200)
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=self.OTHER, headers=self.HTTPS).status_code, 403)
        self.assertEqual(set(asked), {"https"})
        self.assertLessEqual(len(asked), 2)                                                           # the answer is kept for a short time, not asked for every request

    def test_a_name_that_does_not_resolve_trusts_nobody(self):
        """TC-API-008: a trusted name that cannot be resolved trusts nobody.

        Example: trusted [https], the lookup fails -> login from 10.89.1.5 with https 403.
        """
        # Given: a resolver that fails
        def resolve(name):
            raise OSError("no such host")
        client = self.client(trusted_proxies=["https"], resolve_host=resolve)
        # When / Then: the forwarded HTTPS does not count
        self.assertEqual(login(client, "anna", "pw-anna-1", environ_overrides=self.PROXY, headers=self.HTTPS).status_code, 403)

    def test_the_session_cookie_is_secure_behind_a_trusted_https_proxy(self):
        """TC-API-008: behind a trusted https proxy the session cookie is Secure.

        Example: login through 10.89.1.5 with X-Forwarded-Proto https -> Set-Cookie ...; Secure.
        """
        client = self.client(trusted_proxies=["10.89.1.5"])
        reply = login(client, "anna", "pw-anna-1", environ_overrides=self.PROXY, headers=self.HTTPS)
        self.assertIn("Secure", reply.headers["Set-Cookie"])


class Attribution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "changes.jsonl")
        self.app, self.service, self.sockets, self.changes = make_app(changes=A.ChangeLog(self.path))

    @mark.req("REQ-API-009")
    def test_every_change_of_a_scripted_session_carries_the_account(self):
        """TC-API-009: every change of a scripted session of two accounts is recorded with its account, action, route and time (100 %); a read and a refused change are not recorded.

        Example: anna, ben, anna, ben, ben POST /api/data -> rows anna, ben, anna, ben, ben; GET and a 422 add no row.
        """
        # Given: anna and ben logged in, five changes in turn
        anna, ben = self.app.test_client(), self.app.test_client()
        login(anna, "anna", "pw-anna-1")
        login(ben, "ben", "pw-ben-123")
        script = [(anna, {"persona": "warm"}), (ben, {"persona": "dry"}), (anna, {"persona": "calm"}), (ben, {"x": 1}), (ben, {"y": 2})]
        # When: the changes, a read and a refused change are sent
        for client, body in script:
            self.assertEqual(client.post("/api/data", json=body).status_code, 200)
        anna.get("/api/data")                                                       # a read is no change
        anna.post("/api/broken", json={})                                           # a refused change did not happen
        # Then: exactly the five changes are recorded with their accounts
        rows = [json.loads(line) for line in open(self.path)]
        self.assertEqual([r["account"] for r in rows], ["anna", "ben", "anna", "ben", "ben"])
        self.assertTrue(all(r["action"] == "POST" and r["target"] == "/api/data" and r["time"] for r in rows))
        self.assertEqual(self.changes.read(), rows)

    @mark.req("REQ-API-009")
    def test_login_and_logout_are_not_changes_of_shared_data(self):
        """TC-API-009: a login and a logout are not changes of shared data and write no line.

        Example: login and logout of anna -> no changes file.
        """
        # When: anna logs in and out
        client = self.app.test_client()
        login(client, "anna", "pw-anna-1")
        client.post("/api/logout")
        # Then: nothing is recorded
        self.assertFalse(os.path.exists(self.path))

    @mark.req("REQ-API-009")
    def test_a_socket_event_can_be_recorded_without_its_content(self):
        """TC-API-009: a socket event such as chat_send is recorded with its account and without its text.

        Example: record(anna, chat_send, "") -> one row (anna, chat_send).
        """
        self.changes.record("anna", "chat_send", "")
        self.assertEqual([(r["account"], r["action"]) for r in self.changes.read()], [("anna", "chat_send")])


class Sockets(unittest.TestCase):
    @mark.req("REQ-API-017")
    def test_the_sockets_of_a_session_are_dropped_when_it_ends_and_only_those(self):
        """TC-API-017: when a session ends its sockets are dropped, and only its own; a socket that left by itself is not dropped again.

        Example: sid1, sid2 of anna (sid2 left), sid3 of ben; anna logs out -> dropped [sid1]; sid3 stays ben's.
        """
        app, service, sockets, _ = make_app()
        # Given: three sockets of two sessions, one of them already gone
        token_a, token_b = service.login("anna", "pw-anna-1"), service.login("ben", "pw-ben-123")
        sockets.add(token_a, "sid1")
        sockets.add(token_a, "sid2")
        sockets.add(token_b, "sid3")
        sockets.remove("sid2")                                                    # a page that left by itself
        # When: anna's session ends
        service.logout(token_a)
        # Then: only her open socket is dropped
        self.assertEqual(sockets.socketio.dropped, ["sid1"])
        self.assertEqual(sockets.token_of("sid3"), token_b)
        self.assertIsNone(sockets.token_of("sid1"))

    def test_a_socket_without_a_valid_session_is_refused(self):
        """TC-API-007: a socket with a made-up session or none is refused; one with a valid session is accepted and remembered.

        Example: accept(made-up, sid1) -> False; accept(anna's token, sid2) -> True, token_of(sid2) is the token.
        """
        # When / Then: invalid sessions are refused
        app, service, sockets, _ = make_app()
        self.assertFalse(sockets.accept("made-up", "sid1"))
        self.assertFalse(sockets.accept(None, "sid1"))
        # When / Then: a valid one is accepted
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
        """TC-API-017: on a real Flask-SocketIO app a socket without a session is refused; with a session it connects and the logout closes it.

        Example: connect without cookie -> not connected; after login -> connected; POST /api/logout -> disconnected.
        """
        # When / Then: no session, no socket
        web = self.app.test_client()
        refused = self.socketio.test_client(self.app, flask_test_client=web)
        self.assertFalse(refused.is_connected())                                   # no session, no socket
        # When / Then: with anna's session the socket connects
        login(web, "anna", "pw-anna-1")
        sock = self.socketio.test_client(self.app, flask_test_client=web)
        self.assertTrue(sock.is_connected())
        # When / Then: the logout closes it
        web.post("/api/logout")
        self.assertFalse(sock.is_connected())                                      # the logout closed it
        self.assertEqual(self.sockets._by_sid, {})

    def test_a_socket_of_another_session_stays(self):
        """TC-API-017: the logout of one session closes only its sockets; the socket of another session of the same account stays.

        Example: two sessions of anna with a socket each, the first logs out -> its socket closed, the other connected.
        """
        # Given: two sessions of anna with a socket each
        a, b = self.app.test_client(), self.app.test_client()
        login(a, "anna", "pw-anna-1")
        login(b, "anna", "pw-anna-1")
        sa, sb = (self.socketio.test_client(self.app, flask_test_client=c) for c in (a, b))
        # When: the first logs out
        a.post("/api/logout")
        # Then: only its socket is closed
        self.assertFalse(sa.is_connected())
        self.assertTrue(sb.is_connected())


if __name__ == "__main__":
    unittest.main()
