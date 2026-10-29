"""
The web side of the accounts (N-2.1 T-01 and T-02; IF-101: login, whoami, change_password, logout).

create_accounts_blueprint(service): the routes, with the session in the cookie `mia_session` (HttpOnly, SameSite=Strict, Secure on HTTPS; the page keeps no token).
install(app, socketio, store, ...): the routes plus the guard that every request passes (REQ-API-007):
  - a foreign `Origin` is refused (403 bad_origin), also with a session;
  - the page, its static files and the login are open; our own speech process passes the internal paths with a shared secret (header X-MIA-Internal);
    every other request needs a session (401 unauthenticated); the socket handshake is guarded by guard_connect;
  - a password (login, change_password) is accepted only over a secure channel: HTTPS, or a request from this machine (403 insecure_channel, REQ-API-008);
  - every successful change (POST, PUT, PATCH, DELETE) is written to the ChangeLog with the account (REQ-API-009); there are no roles (REQ-API-010).
SocketSessions: which sockets belong to which session; a socket without a valid session is refused, the sockets of a session that ends (logout) are disconnected
(REQ-API-017), and the account of a socket is the key of the message rate limit (REQ-API-007: per user).
Accounts are made on the machine with tools/accounts_cli.py; no request creates one.
"""
import hmac
import json
import os
import time

import ipaddress
import socket
import time

from flask import Blueprint, current_app, g, jsonify, request

try:
    from .api_sessions import ApiError, SessionService
    from .internal_auth import INTERNAL_HEADER
except ImportError:  # plain import (single test run as a script)
    from api_sessions import ApiError, SessionService
    from internal_auth import INTERNAL_HEADER

COOKIE = "mia_session"
PASSWORD_PATHS = ("/api/login", "/api/change_password")
NO_CHANGE_PATHS = ("/api/login", "/api/logout", "/api/change_password")       # not changes of shared data
LOOPBACK = ("127.0.0.1", "::1")


def _body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def create_accounts_blueprint(service, cookie=COOKIE):
    bp = Blueprint("accounts_api", __name__)

    def answer(call, status=200):
        try:
            return jsonify(call()), status
        except ApiError as err:
            body = {"error": err.code}
            if err.rule:
                body["rule"] = err.rule
            return jsonify(body), err.status

    def token():
        return request.cookies.get(cookie)

    @bp.post("/api/login")
    def login():
        data = _body()
        try:
            session = service.login(data.get("user"), data.get("password"))
        except ApiError as err:
            return jsonify({"error": err.code}), err.status
        response = jsonify({"ok": True})
        response.set_cookie(cookie, session, httponly=True, samesite="Strict", secure=https_here())
        return response

    @bp.get("/api/whoami")
    def whoami():
        return answer(lambda: service.whoami(token()))

    @bp.post("/api/logout")
    def logout():
        try:
            result = service.logout(token())
        except ApiError as err:
            return jsonify({"error": err.code}), err.status
        response = jsonify(result)
        response.set_cookie(cookie, "", max_age=0, httponly=True, samesite="Strict", secure=https_here())
        return response

    @bp.post("/api/change_password")
    def change_password():
        data = _body()
        return answer(lambda: service.change_password(token(), data.get("old"), data.get("new")))

    return bp


class ChangeLog:
    """who changed what (REQ-API-009): one JSON line {time, account, action, target} per change; the content of a change is not written (it can hold private text).
    With path None nothing is written to disk and only the list in memory is kept (tests)."""

    def __init__(self, path, clock=time.time):
        self.path, self._clock, self._rows = path, clock, []

    def record(self, account, action, target):
        row = {"time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self._clock())), "account": account, "action": action, "target": target}
        self._rows.append(row)
        if self.path:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as fp:
                fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    def read(self):
        return list(self._rows)


class ProxyTrust:
    """the proxies whose X-Forwarded-Proto counts (config `trusted_proxies`): addresses, networks (10.89.1.0/24) or host names, which are resolved to the addresses of that container
    (in the compose stack the https service is `https`) and kept for `ttl` seconds. Nothing is trusted by default; a name that does not resolve trusts nobody."""

    def __init__(self, entries=(), resolve=None, ttl=30.0, clock=time.monotonic):
        self._networks, self._names = [], []
        for entry in entries:
            try:
                self._networks.append(ipaddress.ip_network(str(entry), strict=False))
            except ValueError:
                self._names.append(str(entry))
        self._resolve = resolve or (lambda name: socket.gethostbyname_ex(name)[2])
        self._ttl, self._clock = ttl, clock
        self._known, self._until = set(), 0.0

    def _addresses(self):
        if self._names and self._clock() >= self._until:
            found = set()
            for name in self._names:
                try:
                    found.update(self._resolve(name))
                except (OSError, ValueError):
                    pass
            self._known, self._until = found, self._clock() + self._ttl
        return self._known

    def trusts(self, address):
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            return False
        if any(ip in network for network in self._networks):
            return True
        return any(ip == ipaddress.ip_address(known) for known in self._addresses())


def secure_channel():
    """a password may arrive over HTTPS, or from this machine; X-Forwarded-Proto counts only when the proxy that sets it runs on this machine or is named in `trusted_proxies`"""
    if request.is_secure or request.remote_addr in LOOPBACK:
        return True
    return False


def _forwarded_https():
    if request.headers.get("X-Forwarded-Proto", "").lower() != "https":
        return False
    if request.remote_addr in LOOPBACK:
        return True
    trust = current_app.config.get("MIA_PROXY_TRUST")
    return bool(trust and trust.trusts(request.remote_addr))


def https_here():
    """true for a request that came over HTTPS, directly or through a trusted proxy: the session cookie is then marked Secure"""
    return request.is_secure or _forwarded_https()


def install_guard(app, service, cookie=COOKIE, open_paths=("/",), open_prefixes=("/static/",), internal_paths=(), internal_token=None, allowed_origins=lambda: [], changes=None, trusted_proxies=(), resolve_host=None):
    app.config["MIA_PROXY_TRUST"] = ProxyTrust(trusted_proxies, resolve_host)
    @app.before_request
    def guard():
        path = request.path
        if path.startswith("/socket.io/"):
            return None                                                 # the handshake is guarded by guard_connect
        origin = request.headers.get("Origin")
        if origin and origin not in allowed_origins():
            return jsonify({"error": "bad_origin"}), 403
        if path in PASSWORD_PATHS and request.method == "POST" and not (secure_channel() or _forwarded_https()):
            return jsonify({"error": "insecure_channel"}), 403
        if path in internal_paths and internal_token:
            if hmac.compare_digest(request.headers.get(INTERNAL_HEADER, ""), internal_token):
                return None
        if path == "/api/login" or path in open_paths or any(path.startswith(p) for p in open_prefixes):
            return None
        account = service.user_of(request.cookies.get(cookie))
        if account is None:
            return jsonify({"error": "unauthenticated"}), 401
        g.account = account
        return None

    @app.after_request
    def attribute(response):
        account = getattr(g, "account", None)
        if changes is not None and account and request.method in ("POST", "PUT", "PATCH", "DELETE") and 200 <= response.status_code < 300 and request.path not in NO_CHANGE_PATHS:
            changes.record(account, request.method, request.path)
        return response


class SocketSessions:
    def __init__(self, service, socketio):
        self.service, self.socketio = service, socketio
        self._by_sid = {}                       # sid -> session token
        service.on_end(self._drop)

    def accept(self, token, sid):
        """a socket connects with the session cookie: False for no or an unknown session (the caller refuses the connection with 'unauthenticated')"""
        if not token or self.service.user_of(token) is None:
            return False
        self.add(token, sid)
        return True

    def add(self, token, sid):
        self._by_sid[sid] = token

    def remove(self, sid):
        self._by_sid.pop(sid, None)

    def token_of(self, sid):
        return self._by_sid.get(sid)

    def account_of(self, sid):
        """the account behind a socket: the key of the message rate limit, so two devices of a user share one limit"""
        token = self._by_sid.get(sid)
        return self.service.user_of(token) if token else None

    def _drop(self, token):
        for sid in [s for s, t in self._by_sid.items() if t == token]:
            del self._by_sid[sid]
            getattr(self.socketio, "server", self.socketio).disconnect(sid)          # Flask-SocketIO keeps the python-socketio server in .server


def install(app, socketio, store, **guard_options):
    """registers the routes and the guard on the Flask app and returns (service, sockets); web_app.py calls guard_connect / forget_socket from its connect and
    disconnect handlers. guard_options: see install_guard."""
    service = SessionService(store)
    app.register_blueprint(create_accounts_blueprint(service))
    install_guard(app, service, **guard_options)
    return service, SocketSessions(service, socketio)


def guard_connect(sockets, cookie=COOKIE):
    """in the connect handler: a socket without a valid session is refused with the message `unauthenticated` (IF-101); the sid is remembered for the logout"""
    from socketio.exceptions import ConnectionRefusedError as Refused
    if not sockets.accept(request.cookies.get(cookie), request.sid):
        raise Refused("unauthenticated")


def forget_socket(sockets):
    """in the disconnect handler"""
    sockets.remove(request.sid)
