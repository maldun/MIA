"""Mock of IF-102, the storage interface of the Database (protected; changes by amendment together with the suite).
Complexity 2: an in-memory fake. It does not model transactions across tables, concurrent writers, backup or restore."""
import copy

try:
    from .errors import StorageError
    from . import graph_rules
except ImportError:  # plain import (single test run as a script)
    from errors import StorageError
    import graph_rules

TABLES = ("workflows", "context_graphs", "history", "memory", "votes", "tasks", "memos", "accounts", "presets", "gestures", "runs", "source_trust", "cases", "behaviours")
IMMUTABLE = ("workflows", "context_graphs")      # versioned records are never deleted
VALIDATED = ("workflows",)                       # graph rules are checked on write (TB-edit, second line of defence)


class StorageMock:
    def __init__(self):
        self._rows = {t: {} for t in TABLES}     # table -> id -> list of versions
        self._tick = 0
        self._listeners = {t: [] for t in TABLES}

    def _now(self):
        self._tick += 1
        return "2026-01-01T00:%02d:%02dZ" % (self._tick // 60, self._tick % 60)

    def _table(self, table):
        if table not in self._rows:
            raise StorageError("unknown_table", detail=table)
        return self._rows[table]

    def put(self, table, record_id, doc, author, expected_version=None):
        """Write a new version; returns {"version": n}. Versions count from 1 per record."""
        rows = self._table(table)
        versions = rows.get(record_id, [])
        if expected_version is not None and expected_version != len(versions):
            raise StorageError("conflict", detail={"current": len(versions)})
        if table in VALIDATED:
            broken = graph_rules.violation(doc)
            if broken:
                raise StorageError("invalid", rule=broken[0], detail=broken[1])
        entry = {"id": record_id, "version": len(versions) + 1, "author": author, "time": self._now(), "doc": copy.deepcopy(doc)}
        rows.setdefault(record_id, []).append(entry)
        for listener in list(self._listeners[table]):
            listener({"table": table, "id": record_id, "version": entry["version"], "author": author})
        return {"version": entry["version"]}

    def get(self, table, record_id, version=None):
        versions = self._table(table).get(record_id)
        if not versions or (version is not None and not 1 <= version <= len(versions)):
            raise StorageError("not_found")
        return copy.deepcopy(versions[-1 if version is None else version - 1])

    def history(self, table, record_id):
        versions = self._table(table).get(record_id)
        if not versions:
            raise StorageError("not_found")
        return [{"version": v["version"], "author": v["author"], "time": v["time"]} for v in versions]

    def ids(self, table):
        return sorted(self._table(table))

    def delete(self, table, record_id, author):
        rows = self._table(table)
        if table in IMMUTABLE:
            raise StorageError("immutable")
        if record_id not in rows:
            raise StorageError("not_found")
        del rows[record_id]

    def subscribe(self, table, callback):
        """callback({"table", "id", "version", "author"}) after every write; returns a function that unsubscribes."""
        self._table(table)
        self._listeners[table].append(callback)
        return lambda: self._listeners[table].remove(callback)
