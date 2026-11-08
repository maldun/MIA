"""
The Storage layer: the one door to the shared state (IF-102, REQ-SLY-002 to REQ-SLY-006, REQ-SLY-012).

Storage holds the rules and a backend holds the bytes, so the file backend and the PostgreSQL backend behave the same:
  - every put is a new immutable version, counted from 1 per record, with author and time; expected_version guards against a lost update
  - the tables, and whether a record may be deleted, come from the Graph tables (IF-301) and the Record tables (IF-302)
  - a document is validated by the table definitions before anything is written; a refused document consumes no version
  - subscribers are told after every write, a delete included (version None; D-158)

A backend offers: versions(table, id) -> list of entries (oldest first), append(table, id, entry), ids(table), remove(table, id). It does not
know the rules. Records are never changed in place; only append and remove (of a deletable table) touch the data. A backend shared by several
instances also offers publish(event) and listen(callback): the notices of the other instances come through that channel, tagged with the origin.
"""
import copy
import logging
import math
import threading
import uuid

try:
    from . import graph_tables, record_tables
    from .chat_log import utc_now
except ImportError:  # used as plain script / in tests
    import graph_tables
    import record_tables
    from chat_log import utc_now

log = logging.getLogger("storage")

class StorageError(Exception):
    """code: invalid | not_found | conflict | immutable | unknown_table; rule: the broken rule for code invalid; detail: the cycle, the current version ..."""

    def __init__(self, code, rule=None, detail=None):
        super().__init__("%s%s" % (code, ": %s" % rule if rule else ""))
        self.code, self.rule, self.detail = code, rule, detail


def table_definitions():
    tables = graph_tables.definitions()
    tables.update(graph_tables.record_definitions())
    tables.update(record_tables.definitions())
    return tables


def _unstorable(value):
    """What one backend would keep and another refuse, or None: a NUL character in a text (PostgreSQL refuses it, F9) and a number that is not
    finite (NaN, inf: JSON has no such number and PostgreSQL refuses it, R2). Keys are looked at too. Iterative: a document nested deeper than the
    recursion limit must be refused by a rule, not end in a RecursionError (F-15)."""
    todo = [value]
    while todo:
        value = todo.pop()
        if isinstance(value, str):
            if "\x00" in value:
                return "a NUL character"
        elif isinstance(value, float):
            if not math.isfinite(value):
                return "a number that is not finite"
        elif isinstance(value, dict):
            todo.extend([*value.keys(), *value.values()])
        elif isinstance(value, (list, tuple)):
            todo.extend(value)
    return None


def refuse_unstorable(*values):
    """Raises StorageError("invalid", "schema") for a value that not every backend can keep the same way, so all of them refuse it alike."""
    found = next((found for found in map(_unstorable, values) if found), None)
    if found:
        raise StorageError("invalid", rule="schema", detail=found)


def _copy(doc):
    """A copy the backend keeps. deepcopy recurses, so a document of a table without a depth rule that is nested a few hundred levels deep is
    refused here instead of raising a RecursionError (F-15)."""
    try:
        return copy.deepcopy(doc)
    except RecursionError:
        raise StorageError("invalid", rule="schema", detail="nested too deep") from None


def check_names(record_id, author):
    """The id of a record is text (R2: anything else was a TypeError of the backend), and neither the id nor the author holds what
    refuse_unstorable refuses."""
    if not isinstance(record_id, str):
        raise StorageError("invalid", rule="schema", detail="an id that is not text")
    refuse_unstorable(record_id, author)


def validate(table, doc):
    """Raises StorageError("invalid", rule, detail) for a document the table definitions refuse (REQ-SLY-004); put and the copies use it."""
    refuse_unstorable(doc)
    if table in graph_tables.RECORD_TABLES:         # the records of the graphs: put calls check_record again with what is stored
        broken = graph_tables.check_record(table, doc)
    else:
        validator = graph_tables if table in graph_tables.TABLES else record_tables
        try:
            broken = validator.validate(table, doc)
        except RecursionError:                      # the rules of the document tables recurse; a document this deep is refused, not raised (F-15)
            raise StorageError("invalid", rule="schema", detail="nested too deep") from None
    if broken:
        raise StorageError("invalid", rule=broken["rule"], detail=broken["detail"])


def _named_ids(table, doc):
    """The IDs a record of the graphs names, as ([node IDs], [edge IDs]): an edge's two ends, a header's members. A malformed record names none
    (check_record refuses it before it looks at what is stored)."""
    try:
        if table in ("graph_edges", "context_edges"):
            return [doc["from"], doc["to"]], []
        if table == "graphs":
            return [m["id"] for m in doc["data"]["nodes"]], [m["id"] for m in doc["data"]["edges"]]
    except (KeyError, TypeError):
        pass
    return [], []


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

    def put(self, table, record_id, doc, author, expected_version=None):
        """Write a new version; returns {"version": n}."""
        self._check(table)
        check_names(record_id, author)
        validate(table, doc)
        with self._lock:                      # one writer at a time per process: the numbers of the versions have no gap
            self._check_graph_record(table, record_id, doc)
            current = len(self.backend.versions(table, record_id))
            if expected_version is not None and expected_version != current:
                raise StorageError("conflict", detail={"current": current})
            entry = {"id": record_id, "version": current + 1, "author": author, "time": utc_now(), "doc": _copy(doc)}
            self.backend.append(table, record_id, entry)
        self._tell({"table": table, "id": record_id, "version": entry["version"], "author": author})
        return {"version": entry["version"]}

    def _check_graph_record(self, table, record_id, doc):
        """A record of the graphs must name what is stored (REQ-GTB-019, REQ-GTB-020): the checks need only the versions of the IDs it names. Refused
        before the version number is taken, so a refused edit changes nothing (REQ-GTB-016)."""
        if table not in graph_tables.RECORD_TABLES:
            return
        node_ids, edge_ids = _named_ids(table, doc)
        # a context edge or header looks in the context tables, everything else in the workflow tables (REQ-GTB-025, REQ-GTB-026)
        context = table == "context_edges" or (table == "graphs" and doc["data"]["kind"] == "context")
        names = ("context_nodes", "context_edges") if context else ("nodes", "edges")
        tables = ("context_nodes", "context_edges") if context else ("graph_nodes", "graph_edges")
        stored = {names[0]: {i: [v["version"] for v in self.backend.versions(tables[0], i)] for i in node_ids if isinstance(i, str)},
                  names[1]: {i: [v["version"] for v in self.backend.versions(tables[1], i)] for i in edge_ids if isinstance(i, str)}}
        stored = {kind: {i: versions for i, versions in found.items() if versions} for kind, found in stored.items()}
        broken = graph_tables.check_record(table, doc, stored=stored, record_id=record_id)
        if broken:
            raise StorageError("invalid", rule=broken["rule"], detail=broken["detail"])

    def _tell(self, event):
        self._dispatch(event)                   # the subscribers of this instance hear it at once ...
        if hasattr(self.backend, "publish"):    # ... the other instances of a shared database through its channel
            self.backend.publish(dict(event, origin=self._id))

    def _on_remote(self, event):
        if event.get("origin") != self._id:     # this instance has told its own subscribers already
            self._dispatch({k: v for k, v in event.items() if k != "origin"})

    def _dispatch(self, event):
        for listener in list(self._listeners.get(event["table"], ())):
            try:
                listener(dict(event))
            except Exception:                   # one bad subscriber must not stop the others, the write or the listener thread (F2)
                log.exception("a subscriber of %s failed", event["table"])

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
        self._tell({"table": table, "id": record_id, "version": None, "author": author})

    def categories(self):
        """The vote categories, in their order (IF-102, D-162): the consumers ask the storage instead of importing the list of IF-302."""
        return list(record_tables.CATEGORIES)

    def subscribe(self, table, callback):
        """callback({"table", "id", "version", "author"}) after every write of the table, a delete with version None; returns a function that
        unsubscribes."""
        self._check(table)
        if hasattr(self.backend, "listen") and not self._listening:
            self.backend.listen(self._on_remote)
            self._listening = True
        self._listeners[table].append(callback)

        def unsubscribe():
            if callback in self._listeners[table]:
                self._listeners[table].remove(callback)
        return unsubscribe
