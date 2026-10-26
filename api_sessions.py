"""
Login, session, throttling, own password and logout of the Backend (N-2.1 T-01: REQ-API-003 to -005 and -017, REQ-BE-077).

Framework free: the web layer (web_app.py) calls these methods and turns an ApiError into its status and `{"error": code}`. The operations and errors are those of
IF-101 (contracts/IF-101-chat-api.md): login, whoami, change_password, logout. Accounts live in the storage interface (IF-102) through accounts.py; a session
is a random token kept in memory only, so a restart logs everybody out (the page then asks for the login again).

Creating an account is not an operation of this service or of IF-101 (decision of the owner, 2026-10-27): the owner makes accounts on the machine with
tools/accounts_cli.py, so no request can create one (REQ-API-006).
"""
import secrets
import time

try:
    from . import accounts
except ImportError:  # plain import (single test run as a script)
    import accounts

MAX_FAILED_LOGINS = 5            # per account within THROTTLE_SECONDS (REQ-BE-009)
THROTTLE_SECONDS = 60
MIN_PASSWORD = 8                 # characters (IF-101, change_password)


class ApiError(Exception):
    """The errors of IF-101: status 401 unauthenticated / bad_credentials, 422 weak_password, 429 throttled."""

    def __init__(self, status, code, rule=None):
        super().__init__("%s %s%s" % (status, code, ": %s" % rule if rule else ""))
        self.status, self.code, self.rule = status, code, rule


class SessionService:
    def __init__(self, store, clock=time.time):
        """store: a provider of IF-102 (accounts table)"""
        self.store, self._clock = store, clock
        self._sessions = {}                 # token -> account
        self._failed = {}                   # account -> times of the failed logins
        self._listeners = []                # called with the token of a session that ended

    # -- login and sessions --
    def login(self, user, password):
        now = self._clock()
        recent = [t for t in self._failed.get(user, []) if now - t < THROTTLE_SECONDS]
        self._failed[user] = recent
        if len(recent) >= MAX_FAILED_LOGINS:
            raise ApiError(429, "throttled")                      # also for the right password: the attacker learns nothing
        if not isinstance(user, str) or not accounts.verify(self.store, user, password):
            self._failed.setdefault(user if isinstance(user, str) else "", []).append(now)
            raise ApiError(401, "bad_credentials")
        token = secrets.token_urlsafe(32)
        self._sessions[token] = user
        return token

    def user_of(self, token):
        """the account of a session, or None; for the other layers (the socket, the REST calls)"""
        return self._sessions.get(token)

    def _user(self, token):
        user = self._sessions.get(token)
        if user is None:
            raise ApiError(401, "unauthenticated")
        return user

    def whoami(self, token):
        return {"user": self._user(token)}

    def logout(self, token):
        """REQ-API-017: the session ends; it never authenticates again. Listeners (the socket layer) drop what belongs to it. Other sessions of the account stay."""
        self._user(token)
        del self._sessions[token]
        for listener in list(self._listeners):
            listener(token)
        return {"loggedOut": True}

    def on_end(self, listener):
        self._listeners.append(listener)

    # -- passwords and accounts --
    def change_password(self, token, old, new):
        user = self._user(token)
        if not accounts.verify(self.store, user, old):
            raise ApiError(401, "bad_credentials")
        self._check_new(new)
        accounts.set_password(self.store, user, new, user)
        return {"changed": True}

    @staticmethod
    def _check_new(password):
        if not isinstance(password, str) or len(password) < MIN_PASSWORD:
            raise ApiError(422, "weak_password")
