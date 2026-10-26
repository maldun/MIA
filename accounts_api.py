"""
The web side of login and logout (N-2.1 T-01; IF-101: login, whoami, change_password, logout; accounts for the owner).

create_accounts_blueprint(service): the routes, with the session in the cookie `mia_session` (HttpOnly, SameSite=Strict, Secure on HTTPS; the page keeps no token).
SocketSessions(service, socketio): which sockets belong to which session; a socket without a valid session is refused, and the sockets of a session that ends
(logout) are disconnected (REQ-API-017). The decisions are those of api_sessions.py; this module only turns them into HTTP and Socket.IO.

Not here (N-2.1 T-02): refusing every other request without a session. Until then this is registered only when the config switches accounts on (web_app.py).
"""
from flask import Blueprint, jsonify, request

try:
    from .api_sessions import ApiError
except ImportError:  # plain import (single test run as a script)
    from api_sessions import ApiError

COOKIE = "mia_session"


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
        response.set_cookie(cookie, session, httponly=True, samesite="Strict", secure=request.is_secure)
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
        response.set_cookie(cookie, "", max_age=0, httponly=True, samesite="Strict", secure=request.is_secure)
        return response

    @bp.post("/api/change_password")
    def change_password():
        data = _body()
        return answer(lambda: service.change_password(token(), data.get("old"), data.get("new")))

    @bp.post("/api/accounts")
    def create_account():
        data = _body()
        return answer(lambda: service.create_account(token(), data.get("name"), data.get("password")))

    return bp


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

    def _drop(self, token):
        for sid in [s for s, t in self._by_sid.items() if t == token]:
            del self._by_sid[sid]
            getattr(self.socketio, "server", self.socketio).disconnect(sid)          # Flask-SocketIO keeps the python-socketio server in .server


def install(app, socketio, store, owner=None):
    """registers the routes on the Flask app and returns (service, sockets); web_app.py calls guard_connect / forget_socket from its connect and disconnect handlers"""
    try:
        from .api_sessions import SessionService
    except ImportError:
        from api_sessions import SessionService
    service = SessionService(store, owner=owner)
    app.register_blueprint(create_accounts_blueprint(service))
    return service, SocketSessions(service, socketio)


def guard_connect(sockets, cookie=COOKIE):
    """in the connect handler: a socket without a valid session is refused with the message `unauthenticated` (IF-101); the sid is remembered for the logout"""
    from socketio.exceptions import ConnectionRefusedError as Refused
    if not sockets.accept(request.cookies.get(cookie), request.sid):
        raise Refused("unauthenticated")


def forget_socket(sockets):
    """in the disconnect handler"""
    sockets.remove(request.sid)
