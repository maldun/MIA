"""Mock of IF-104, the workflow and graph API of the Backend for the Graph app (protected).
Complexity 2: a fake REST server as an in-process object on top of the storage mock. It does not model concurrent edits."""
try:
    from .errors import ApiError, StorageError
    from .if_102_storage import StorageMock
except ImportError:
    from errors import ApiError, StorageError
    from if_102_storage import StorageMock

KINDS = ("workflows", "context_graphs")
STATUS = {"not_found": 404, "conflict": 409, "invalid": 422, "immutable": 409, "unknown_table": 404}


class GraphApiMock:
    def __init__(self, accounts=None, storage=None):
        self.accounts = accounts or {"anna": "pw-anna", "ben": "pw-ben"}
        self.storage = storage or StorageMock()
        self._sessions = {}

    def login(self, user, password):
        """Returns a session token; 401 for a wrong account or password."""
        if self.accounts.get(user) != password:
            raise ApiError(401, "bad_credentials")
        token = "s%d" % (len(self._sessions) + 1)
        self._sessions[token] = user
        return token

    def _user(self, session):
        if session not in self._sessions:
            raise ApiError(401, "unauthenticated")
        return self._sessions[session]

    def _call(self, session, kind, fn):
        self._user(session)
        if kind not in KINDS:
            raise ApiError(404, "unknown_kind")
        try:
            return fn()
        except StorageError as err:
            raise ApiError(STATUS.get(err.code, 500), err.code, rule=err.rule, detail=err.detail)

    def list_ids(self, session, kind):
        return self._call(session, kind, lambda: self.storage.ids(kind))

    def read(self, session, kind, record_id, version=None):
        return self._call(session, kind, lambda: self.storage.get(kind, record_id, version))

    def save(self, session, kind, record_id, doc, expected_version=None):
        """Saves a new version as the logged-in user; 422 with the broken rule for an invalid graph."""
        author = self._user(session)
        return self._call(session, kind, lambda: self.storage.put(kind, record_id, doc, author, expected_version))

    def history(self, session, kind, record_id):
        return self._call(session, kind, lambda: self.storage.history(kind, record_id))

    def diff(self, session, kind, record_id, a, b):
        """Difference between two versions: node ids added, removed, changed; edges added and removed as 'from->to'."""
        def run():
            old, new = self.storage.get(kind, record_id, a)["doc"], self.storage.get(kind, record_id, b)["doc"]
            on = {n["id"]: n for n in old.get("nodes", [])}
            nn = {n["id"]: n for n in new.get("nodes", [])}
            oe = {"%s->%s" % (e["from"], e["to"]) for e in old.get("edges", [])}
            ne = {"%s->%s" % (e["from"], e["to"]) for e in new.get("edges", [])}
            return {"nodes_added": sorted(set(nn) - set(on)), "nodes_removed": sorted(set(on) - set(nn)),
                    "nodes_changed": sorted(i for i in set(on) & set(nn) if on[i] != nn[i]),
                    "edges_added": sorted(ne - oe), "edges_removed": sorted(oe - ne)}
        return self._call(session, kind, run)

    def restore(self, session, kind, record_id, version):
        """Saves the content of a former version as a new version; the former version stays."""
        author = self._user(session)
        return self._call(session, kind, lambda: self.storage.put(kind, record_id, self.storage.get(kind, record_id, version)["doc"], author))
