"""
Moving graphs between stores and keeping a copy in sync with the live store (G-V4.GRAPHSTORE.TRANSFER; REQ-SLY-016 to 039).

Built: move_store (T-01), lag, sync_store and copy_lock (T-03), move_graph and the side records (T-04), the older-set refusal (T-05; the
marker itself is the FileBackend's). The prototype's graph_store_move.py and graph_store_sync.py (prototype/g-v4, rounds 02 and 03) are the basis.

Stores are backends (storage_files.FileBackend, storage_postgres.PostgresBackend: versions, append, ids, remove, cut, close); a copy is always a
FileBackend, its root holds the aside folder, the lock and the format marker.

- move_store(source, target) -> {"copied", "skipped", "added_versions"}: every record of every table, each graph checked against the members found
  in the source first, members before headers (REQ-SLY-016 to 021). Refused: StorageError("invalid", rule="move_refused",
  detail={"graphs": {graph ID: [{"rule", "detail"}, ...]}}) with `unknown_member`, `unknown_endpoint` or `unknown_kind` items; nothing written.
- move_graph(source, target, graph_id) -> {"graphs": 1, "records": n}: the versions the target lacks, header last (REQ-SLY-031). A target whose
  history of the graph differs: StorageError("conflict", detail={"graph": graph_id}).
- lag(live, copy) -> {graph ID: {"live": n, "copy": m, "state": "behind" | "differs" | "copy_only" | "refused", "reason": text or None}}, only
  graphs that are not current (REQ-SLY-024).
- sync_store(live, copy) -> {"graphs": n, "records": n, "set_aside": {graph ID: {"versions": [...], "file": path relative to the copy, "reason"}}}
  (REQ-SLY-025 to 028, 038). Locked: StorageError("locked", detail={"lock": LOCK}).
- lag_summary(live, copy) -> {"graphs": n, "since": time or None}: the lag in IF-104 v2 terms (REQ-API-064, D-540).
- AutoSync(open_live, copy, name, log).run("start" | "stop") -> report: the sync as MIA runs it at start and orderly stop (REQ-API-062, 063);
  a live store that does not answer and a refused sync are one log line each, never an exception.
- An older set (no marker) with an unscoped record: StorageError("invalid", rule="older_format", detail={"table", "id", "conversion": CONVERSION_STEP})
  (REQ-SLY-034). A newer set: the FileBackend refuses to open it, StorageError("format", detail={"found": n, "known": FORMAT}) (REQ-SLY-035).
"""
import contextlib
import fcntl
import json
import os
import time

try:
    from . import graph_rule_set, graph_tables
    from .storage import StorageError, table_definitions
    from .storage_copy import GRAPH_GROUP, _check_entries, copy_records, ordered_tables
    from .storage_files import FORMAT, MARKER  # noqa: F401  named here too: the format of a set belongs to its moves (REQ-SLY-032)
except ImportError:  # used as plain script / in tests
    import graph_rule_set
    import graph_tables
    from storage import StorageError, table_definitions
    from storage_copy import GRAPH_GROUP, _check_entries, copy_records, ordered_tables
    from storage_files import FORMAT, MARKER  # noqa: F401

LOCK = "sync.lock"              # the lock file in the root of a copy (REQ-SLY-028)
ASIDE = "aside"                 # the aside folder in the root of a copy (REQ-SLY-026)
CONVERSION_STEP = "the conversion of G-V4.GRAPHSTORE.MIGRATION"   # named by the refusal of an older set (REQ-SLY-034)
HEADERS = "graphs"
MEMBER_TABLES = ("graph_nodes", "graph_edges", "context_nodes", "context_edges")


def _members(kind):
    """(node table, edge table), (node key, edge key) of `stored` in graph_tables.check_record, for a graph of this kind (REQ-GTB-026)."""
    if kind == "context":
        return ("context_nodes", "context_edges"), ("context_nodes", "context_edges")
    return ("graph_nodes", "graph_edges"), ("nodes", "edges")


def graph_problems(source, graph_id, node_ids):
    """[{"rule", "detail"}, ...] of one graph of the source, [] when it can be moved (REQ-SLY-017, 018, 021).
    Every header version is checked with the member versions the source holds, and every connection it names with the steps the source holds
    (`node_ids`: {node table: set of IDs}). Structural record checks only, never the eight rules: a graph with a cycle is moved (D-460)."""
    problems, versions, checked, known = [], {}, set(), graph_rule_set.kinds()

    def add(problem):
        if problem and problem not in problems:
            problems.append(problem)
    for header in source.versions(HEADERS, graph_id):
        data = (header.get("doc") or {}).get("data") or {}
        if data.get("kind") not in known:          # a later MIA's kind is not half-carried (D-460); its member tables are not known either
            add({"rule": "unknown_kind", "detail": data.get("kind")})
            continue
        tables, keys = _members(data["kind"])
        stored = {key: {} for key in keys}
        for part, table, key in zip(("nodes", "edges"), tables, keys):
            for member in data.get(part) or []:
                if (table, member.get("id")) not in versions:
                    versions[table, member.get("id")] = source.versions(table, member.get("id"))
                stored[key][member.get("id")] = [e.get("version") for e in versions[table, member.get("id")]]
        add(graph_tables.check_record(HEADERS, header["doc"], stored=stored, record_id=graph_id))
        for member in data.get("edges") or []:
            name = (member.get("id"), member.get("version"))
            entry = next((e for e in versions[tables[1], name[0]] if e.get("version") == name[1]), None)
            if entry is not None and name not in checked:
                checked.add(name)
                add(graph_tables.check_record(tables[1], entry["doc"], stored={keys[0]: node_ids[tables[0]]}))
    return problems


def check_format(source):
    """A set of files without a marker that holds a step or connection with a plain ID (from before A-167) is refused before any write, naming
    the record and MIGRATION's conversion (REQ-SLY-034); with a marker or on the database such a record is only invalid (unscoped_id)."""
    if getattr(source, "root", None) is None or source.format() is not None:
        return
    for table in MEMBER_TABLES:
        for record_id in sorted(source.ids(table)):
            if "/" not in record_id:
                raise StorageError("invalid", rule="older_format", detail={"table": table, "id": record_id, "conversion": CONVERSION_STEP})


def check_graphs(source, graph_ids):
    """Raises StorageError("invalid", rule="move_refused") naming every graph that cannot be moved, with its problems (REQ-SLY-018, 021)."""
    node_ids = {table: set(source.ids(table)) for table in ("graph_nodes", "context_nodes")}
    found = {}
    for graph_id in graph_ids:
        problems = graph_problems(source, graph_id, node_ids)
        if problems:
            found[graph_id] = problems
    if found:
        raise StorageError("invalid", rule="move_refused", detail={"graphs": found})


class copy_lock:
    """`with copy_lock(root):` holds the copy's lock (an operating-system lock on <root>/sync.lock, released when the process ends); a second
    holder gets StorageError("locked", detail={"lock": LOCK}). The sync and a move into the copy take it (REQ-SLY-028). flock, not a lock file
    that exists or not: the system drops it with the process, so a killed sync never leaves the copy locked."""

    def __init__(self, root):
        self.root = root
        self.handle = None

    def __enter__(self):
        os.makedirs(self.root, exist_ok=True)
        self.handle = open(os.path.join(self.root, LOCK), "a")
        try:
            fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.handle.close()
            raise StorageError("locked", detail={"lock": LOCK}) from None
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        self.handle.close()
        return False


def move_store(source, target):
    """Every record of every table from the source to the target, unchanged (REQ-SLY-016); every graph checked first, nothing written when one is
    damaged (REQ-SLY-017, 018, 021); members before headers (REQ-SLY-019); records already there are skipped (REQ-SLY-020). copy_records keeps
    its own checks: a record with another history in the target is a conflict, a record put would refuse is invalid, both before any write."""
    check_format(source)
    check_graphs(source, source.ids(HEADERS))
    return copy_records(source, target, ordered_tables(table_definitions()))


def _lock_of(target):
    """the copy's lock for a files target (REQ-SLY-028); a database target has no copy lock"""
    root = getattr(target, "root", None)
    return copy_lock(root) if root else contextlib.nullcontext()


def move_graph(source, target, graph_id):
    """The versions of one graph, its members and its side records that the target lacks, header last (REQ-SLY-031, 030, 019); every other
    record untouched. The graph is checked first (REQ-SLY-021); a target holding versions of its own of any of these records is
    StorageError("conflict", detail={"graph": graph_id}); both before any write. A stop at any write leaves the target's graph at its last
    complete version, and a rerun appends the rest (REQ-SLY-029, 036)."""
    with _lock_of(target):
        check_format(source)
        check_graphs(source, [graph_id])
        plan = []
        for table, record_id in _graph_records(source, target, graph_id):
            have, wanted = target.versions(table, record_id), source.versions(table, record_id)
            if len(have) > _shared(have, wanted):
                raise StorageError("conflict", detail={"graph": graph_id})
            _check_entries(table, record_id, wanted)
            plan += [(table, record_id, entry) for entry in wanted[len(have):]]
        for table, record_id, entry in plan:
            target.append(table, record_id, entry)
        return {"graphs": 1, "records": len(plan)}


def _shared(have, wanted):
    """how many of the first entries of `have` equal those of `wanted` (author and time included)"""
    n = 0
    for a, b in zip(have, wanted):
        if a != b:
            break
        n += 1
    return n


def _side_records(stores, graph_id):
    """VIEW's side records of the graph where their tables are defined (REQ-SLY-030): one record of changes per header version
    (`<graph>/<version>`, absent for a version kept without one) and the arrangement (`<graph>`)"""
    defined, out = table_definitions(), []
    if "graph_changes" in defined:
        newest = max(len(store.versions(HEADERS, graph_id)) for store in stores)
        out += [("graph_changes", "%s/%d" % (graph_id, version)) for version in range(1, newest + 1)]
    if "arrangements" in defined:
        out.append(("arrangements", graph_id))
    return out


def _graph_records(live, copy, graph_id):
    """[(table, record ID)] of the graph: its members named by any header version in either store, its side records, the header last"""
    found = []
    for store in (copy, live):
        for header in store.versions(HEADERS, graph_id):
            data = (header.get("doc") or {}).get("data") or {}
            tables, _ = _members(data.get("kind"))
            for part, table in zip(("nodes", "edges"), tables):
                for member in data.get(part) or []:
                    if (table, member.get("id")) not in found:
                        found.append((table, member.get("id")))
    return found + _side_records((live, copy), graph_id) + [(HEADERS, graph_id)]


def _state(live, copy, graph_id):
    """(state, {(table, record ID): (copy entries, live entries, shared count)}) of one graph that the live store can give: current, behind, differs, copy_only"""
    records = {}
    for key in _graph_records(live, copy, graph_id):
        have, wanted = copy.versions(*key), live.versions(*key)
        records[key] = (have, wanted, _shared(have, wanted))
    if not live.versions(HEADERS, graph_id):
        return "copy_only", records
    if any(len(have) > shared for have, _, shared in records.values()):
        return "differs", records
    if any(len(wanted) > len(have) for have, wanted, _ in records.values()):
        return "behind", records
    return "current", records


def _graphs(live, copy):
    return sorted(set(live.ids(HEADERS)) | set(copy.ids(HEADERS)))


def lag(live, copy):
    """Every graph that is not current on the copy, with its header versions in both stores, its state and its reason (REQ-SLY-024): behind
    (the copy lacks live versions), differs (the copy holds versions of the graph or a member the live store does not), copy_only, refused (the
    live store's graph cannot be moved, reason: its rules, REQ-SLY-021)."""
    node_ids = {table: set(live.ids(table)) for table in ("graph_nodes", "context_nodes")}
    out = {}
    for graph_id in _graphs(live, copy):
        row = {"live": len(live.versions(HEADERS, graph_id)), "copy": len(copy.versions(HEADERS, graph_id)), "reason": None}
        problems = graph_problems(live, graph_id, node_ids) if row["live"] else []
        if problems:
            row.update(state="refused", reason=", ".join(p["rule"] for p in problems))
        else:
            row["state"] = _state(live, copy, graph_id)[0]
        if row["state"] != "current":
            out[graph_id] = row
    return out


def _aside_path(copy, graph_id, stamp):
    """a path under the aside folder, relative to the copy (REQ-SLY-027), that no earlier aside file uses"""
    base = "%s/%s__%s" % (ASIDE, graph_id.replace("/", "_"), stamp)
    path, n = base + ".json", 1
    while os.path.exists(os.path.join(copy.root, path)):
        n += 1
        path = "%s_%d.json" % (base, n)
    return path


def _set_aside(copy, graph_id, records, state):
    """Writes the copy's versions of the graph and its members that the live store does not hold to one aside file, durably (REQ-SLY-026), and
    returns what the answer names of it (REQ-SLY-027)."""
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    reason = "the live store won" if state == "differs" else "the graph exists only on the copy"
    header = records[HEADERS, graph_id]
    doc = {"graph": graph_id, "set_aside_at": stamp, "reason": reason, "header": header[0][header[2]:],
           "members": {"%s|%s" % key: have[shared:] for key, (have, _, shared) in records.items() if key[0] != HEADERS and len(have) > shared}}
    path = _aside_path(copy, graph_id, stamp)
    copy.put_file(path, json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True))
    return {"versions": [e["version"] for e in doc["header"]], "file": path, "reason": reason}


def _cut_back(copy, records):
    """Cuts every record of the graph back to the versions the live store shares, the header first, so the copy lists the graph at its last
    shared version, complete, at every step (REQ-SLY-038); a graph without a shared version leaves header first."""
    for (table, record_id), (have, _, shared) in sorted(records.items(), key=lambda item: item[0][0] != HEADERS):
        if len(have) > shared:
            copy.cut(table, record_id, shared)


def _refuse_other_conflicts(live, copy, handled):
    """A record of the graph group outside every graph whose history on the copy is not the start of the live one: refused before any write."""
    for table in [t for t in GRAPH_GROUP if t in table_definitions()]:
        for record_id in live.ids(table):
            have = copy.versions(table, record_id)
            if (table, record_id) not in handled and have != live.versions(table, record_id)[:len(have)]:
                raise StorageError("conflict", detail={"table": table, "id": record_id})


def sync_store(live, copy):
    """Makes the copy's graph group equal the live store's (REQ-SLY-025); the live store wins. Under the copy's lock (REQ-SLY-028), after every
    graph of the live store is checked (REQ-SLY-021): each graph that differs or exists only on the copy is written to an aside file first
    (REQ-SLY-026, 027), then cut back (REQ-SLY-038); then the live versions the copy lacks follow, members before headers (REQ-SLY-019).
    "graphs" counts the graphs that were not current, "records" the versions appended."""
    with copy_lock(copy.root):
        check_format(live)
        check_graphs(live, live.ids(HEADERS))
        states = {graph_id: _state(live, copy, graph_id) for graph_id in _graphs(live, copy)}
        states = {graph_id: found for graph_id, found in states.items() if found[0] != "current"}
        _refuse_other_conflicts(live, copy, {key for _, records in states.values() for key in records})
        answer = {"graphs": len(states), "records": 0, "set_aside": {}}
        for graph_id, (state, records) in sorted(states.items()):
            if state in ("differs", "copy_only"):
                answer["set_aside"][graph_id] = _set_aside(copy, graph_id, records, state)
                _cut_back(copy, records)
        tables = [t for t in GRAPH_GROUP if t in table_definitions()]
        answer["records"] = sum(len(live.versions(t, i)) - len(copy.versions(t, i)) for t in tables for i in live.ids(t))
        copy_records(live, copy, tables)
        return answer


def lag_summary(live, copy):
    """`graphs`: the graphs not current on the copy; `since`: the time of the oldest header version the live store has and the copy lacks, None
    when there is none (REQ-API-064). Headers only: the lag is counted by graph (REQ-SLY-024), members of one save carry the same second (D-540)."""
    rows = lag(live, copy)
    times = []
    for graph_id in rows:
        have = copy.versions(HEADERS, graph_id)
        missing = [entry for k, entry in enumerate(live.versions(HEADERS, graph_id)) if k >= len(have) or have[k] != entry]
        if missing:
            times.append(missing[0]["time"])
    return {"graphs": len(rows), "since": min(times) if times else None}


# a live store that cannot be reached: the system's errors and the database driver's, named so psycopg stays optional
UNREACHABLE = ("OperationalError", "InterfaceError", "AdminShutdown", "ConnectionTimeout")


def _unreachable(error):
    return isinstance(error, (OSError, TimeoutError)) or type(error).__name__ in UNREACHABLE


class AutoSync:
    """The sync MIA runs at its start and at an orderly stop while `autosync` is on (REQ-API-062). `open_live()` gives the live store and may
    fail when it does not answer; `name` names it in the log (REQ-API-063); `log(line)` takes one line per run. A refused sync (move_refused,
    older_format, conflict, locked) leaves the copy as it is and is logged as well: MIA goes on with the copy either way."""

    def __init__(self, open_live, copy, name, log):
        self.open_live, self.copy, self.name, self.log = open_live, copy, name, log

    def run(self, when):
        try:
            report = sync_store(self.open_live(), self.copy)
            self.log("AutoSync at %s: %d graph(s), %d record(s) from the live store %s to the copy" % (when, report["graphs"], report["records"], self.name))
        except StorageError as err:
            report = {"refused": err.rule or err.code, "detail": err.detail}
            self.log("AutoSync at %s: refused (%s %s), the copy stays as it is" % (when, report["refused"], err.detail))
        except Exception as err:
            if not _unreachable(err):
                raise
            report = {"unreachable": self.name}
            self.log("AutoSync at %s: the live store %s does not answer (%s), sync not run" % (when, self.name, type(err).__name__))
        return report
