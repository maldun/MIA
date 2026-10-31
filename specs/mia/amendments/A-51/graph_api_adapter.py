class _GraphApiAdapter:
    """IF-104 on the real routes of the Backend (amendment A-51, N-2.1 T-04): `graph_api.create_graph_blueprint` on the real WorkflowLibrary (IF-203) and the
    Storage layer with the file backend in a fresh folder, behind the real guard and login of `accounts_api` (the cookie `mia_session` of IF-104 v1). The
    session token of the suite is the value of that cookie; every call is one HTTP request of a client without a cookie jar that sends it. The adapter
    only turns the error body of a route into the error class of the mock; production code does not import from tests/."""

    ACCOUNTS = {"anna": "pw-anna", "ben": "pw-ben"}                  # the accounts of the mock, so that the same suite runs on both

    def __init__(self):
        import tempfile
        from urllib.parse import quote
        from errors import ApiError
        from flask import Flask
        from storage import Storage
        from storage_files import FileBackend
        from workflow_library import WorkflowLibrary
        import accounts
        import accounts_api
        from graph_api import create_graph_blueprint
        store = Storage(FileBackend(tempfile.mkdtemp()))
        for name, password in self.ACCOUNTS.items():
            accounts.create(store, name, password, "contract suite")
        app = Flask(__name__)
        accounts_api.install(app, _NoSockets(), store, allowed_origins=lambda: [])
        app.register_blueprint(create_graph_blueprint(WorkflowLibrary(store)))
        self._http, self._error, self._quote, self._cookie = app.test_client(use_cookies=False), ApiError, quote, accounts_api.COOKIE

    def _request(self, method, path, session=None, **kwargs):
        headers = {"Cookie": "%s=%s" % (self._cookie, session)} if session else {}
        got = getattr(self._http, method)(path, headers=headers, **kwargs)
        body = got.get_json(silent=True)
        if got.status_code >= 400:
            body = body if isinstance(body, dict) else {}
            raise self._error(got.status_code, body.get("error"), rule=body.get("rule"), detail=body.get("detail"))
        return got, body

    def _path(self, kind, record_id=None, action=None):
        return "/".join(["/api", self._quote(kind, safe="")] + [self._quote(part, safe="") for part in (record_id, action) if part is not None])

    def login(self, user, password):
        got, _ = self._request("post", "/api/login", json={"user": user, "password": password})
        return next(value.split("=", 1)[1].split(";", 1)[0] for value in got.headers.getlist("Set-Cookie") if value.startswith(self._cookie + "="))

    def list_ids(self, session, kind):
        return self._request("get", self._path(kind), session)[1]

    def read(self, session, kind, record_id, version=None):
        return self._request("get", self._path(kind, record_id), session, query_string={} if version is None else {"version": version})[1]

    def save(self, session, kind, record_id, doc, expected_version=None):
        body = {"doc": doc} if expected_version is None else {"doc": doc, "expected_version": expected_version}
        return self._request("put", self._path(kind, record_id), session, json=body)[1]

    def history(self, session, kind, record_id):
        return self._request("get", self._path(kind, record_id, "history"), session)[1]

    def diff(self, session, kind, record_id, a, b):
        return self._request("get", self._path(kind, record_id, "diff"), session, query_string={"a": a, "b": b})[1]

    def restore(self, session, kind, record_id, version):
        return self._request("post", self._path(kind, record_id, "restore"), session, json={"version": version})[1]


class _NoSockets:
    """the Socket.IO server that accounts_api.install expects; IF-104 has no sockets"""

    def disconnect(self, sid):
        pass


