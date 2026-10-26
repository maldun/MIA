"""
The Storage layer: the one door to the shared state (IF-102, REQ-SLY-002 to REQ-SLY-006, REQ-SLY-012).

Storage holds the rules and a backend holds the bytes, so the file backend and the PostgreSQL backend behave the same:
  - every put is a new immutable version, counted from 1 per record, with author and time; expected_version guards against a lost update
  - the tables, and whether a record may be deleted, come from the Graph tables (IF-301) and the Record tables (IF-302)
  - a document is validated by the table definitions before anything is written; a refused document consumes no version
  - subscribers are told after every write

A backend offers: versions(table, id) -> list of entries (oldest first), append(table, id, entry), ids(table), remove(table, id). It does not
know the rules. Records are never changed in place; only append and remove (of a deletable table) touch the data. A backend shared by several
instances also offers publish(event) and listen(callback): the notices of the other instances come through that channel, tagged with the origin.
"""
import copy
import threading
import uuid

try:
    from . import graph_tables, record_tables
    from .chat_log import utc_now
except ImportError:  # used as plain script / in tests
    import graph_tables
    import record_tables
    from chat_log import utc_now


class StorageError(Exception):
    """code: invalid | not_found | conflict | immutable | unknown_table; rule: the broken rule for code invalid; detail: the cycle, the current version ..."""

    def __init__(self, code, rule=None, detail=None):
        super().__init__("%s%s" % (code, ": %s" % rule if rule else ""))
        self.code, self.rule, self.detail = code, rule, detail


def table_definitions():
    tables = graph_tables.definitions()
    tables.update(record_tables.definitions())
    return tables


class Storage:
    def __init__(self, backend):
        self.backend = backend
        self.tables = table_definitions()
        self._lock = threading.Lock()
        self._listeners = {table: [] for table in self.tables}
        self._listening = False
        self._id = uuid.uuid4().hex             # tells the notices of this instance from those of the others

    def _check(self, table):
        if table not in self.tables:
            raise StorageError("unknown_table", detail=table)

    def _validate(self, table, doc):
        validator = graph_tables if table in graph_tables.TABLES else record_tables
        broken = validator.validate(table, doc)
        if broken:
            raise StorageError("invalid", rule=broken["rule"], detail=broken["detail"])

    def put(self, table, record_id, doc, author, expected_version=None):
        """Write a new version; returns {"version": n}."""
        self._check(table)
        self._validate(table, doc)
        with self._lock:                      # one writer at a time per process: the numbers of the versions have no gap
            current = len(self.backend.versions(table, record_id))
            if expected_version is not None and expected_version != current:
                raise StorageError("conflict", detail={"current": current})
            entry = {"id": record_id, "version": current + 1, "author": author, "time": utc_now(), "doc": copy.deepcopy(doc)}
            self.backend.append(table, record_id, entry)
        event = {"table": table, "id": record_id, "version": entry["version"], "author": author}
        self._dispatch(event)                   # the subscribers of this instance hear it at once ...
        if hasattr(self.backend, "publish"):    # ... the other instances of a shared database through its channel
            self.backend.publish(dict(event, origin=self._id))
        return {"version": entry["version"]}

    def _on_remote(self, event):
        if event.get("origin") != self._id:     # this instance has told its own subscribers already
            self._dispatch({k: v for k, v in event.items() if k != "origin"})

    def _dispatch(self, event):
        for listener in list(self._listeners.get(event["table"], ())):
            listener(dict(event))

    def get(self, table, record_id, version=None):
        self._check(table)
        versions = self.backend.versions(table, record_id)
        if not versions or (version is not None and not 1 <= version <= len(versions)):
            raise StorageError("not_found")
        return copy.deepcopy(versions[-1 if version is None else version - 1])

    def history(self, table, record_id):
        self._check(table)
        versions = self.backend.versions(table, record_id)
        if not versions:
            raise StorageError("not_found")
        return [{"version": v["version"], "author": v["author"], "time": v["time"]} for v in versions]

    def ids(self, table):
        self._check(table)
        return sorted(self.backend.ids(table))

    def delete(self, table, record_id, author):
        self._check(table)
        if not self.tables[table]["deletable"]:
            raise StorageError("immutable")
        if not self.backend.versions(table, record_id):
            raise StorageError("not_found")
        self.backend.remove(table, record_id)

    def subscribe(self, table, callback):
        """callback({"table", "id", "version", "author"}) after every write of the table; returns a function that unsubscribes."""
        self._check(table)
        if hasattr(self.backend, "listen") and not self._listening:
            self.backend.listen(self._on_remote)
            self._listening = True
        self._listeners[table].append(callback)

        def unsubscribe():
            if callback in self._listeners[table]:
                self._listeners[table].remove(callback)
        return unsubscribe
