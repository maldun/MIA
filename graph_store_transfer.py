"""
Moving graphs between stores and keeping a copy in sync with the live store (G-V4.GRAPHSTORE.TRANSFER; REQ-SLY-016 to 039).

Built so far: move_store (T-01). The other functions are still the stubs of Plan step 4 and answer "nothing done" (T-03 to T-05); the
prototype's graph_store_move.py and graph_store_sync.py (prototype/g-v4, rounds 02 and 03) are the basis.

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
- An older set (no marker) with an unscoped record: StorageError("invalid", rule="older_format", detail={"table", "id", "conversion": CONVERSION_STEP})
  (REQ-SLY-034). A newer set: the FileBackend refuses to open it, StorageError("format", detail={"found": n, "known": FORMAT}) (REQ-SLY-035).
"""
try:
    from . import graph_rule_set, graph_tables
    from .storage import StorageError, table_definitions
    from .storage_copy import GRAPH_GROUP, copy_records, ordered_tables  # noqa: F401  GRAPH_GROUP: the group's write order, named here too
except ImportError:  # used as plain script / in tests
    import graph_rule_set
    import graph_tables
    from storage import StorageError, table_definitions
    from storage_copy import GRAPH_GROUP, copy_records, ordered_tables  # noqa: F401

FORMAT = 1                     # the format of a set of files this code writes and reads (REQ-SLY-032)
MARKER = "mia-store.json"       # the format marker in the root of a set of files
LOCK = "sync.lock"              # the lock file in the root of a copy (REQ-SLY-028)
ASIDE = "aside"                 # the aside folder in the root of a copy (REQ-SLY-026)
CONVERSION_STEP = "the conversion of G-V4.GRAPHSTORE.MIGRATION"   # named by the refusal of an older set (REQ-SLY-034)
HEADERS = "graphs"


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
    holder gets StorageError("locked", detail={"lock": LOCK}). The sync and a move into the copy take it (REQ-SLY-028). STUB: locks nothing."""

    def __init__(self, root):
        self.root = root

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def move_store(source, target):
    """Every record of every table from the source to the target, unchanged (REQ-SLY-016); every graph checked first, nothing written when one is
    damaged (REQ-SLY-017, 018, 021); members before headers (REQ-SLY-019); records already there are skipped (REQ-SLY-020). copy_records keeps
    its own checks: a record with another history in the target is a conflict, a record put would refuse is invalid, both before any write."""
    check_graphs(source, source.ids(HEADERS))
    return copy_records(source, target, ordered_tables(table_definitions()))


def move_graph(source, target, graph_id):
    return {"graphs": 1, "records": 0}


def lag(live, copy):
    return {}


def sync_store(live, copy):
    return {"graphs": 0, "records": 0, "set_aside": {}}
