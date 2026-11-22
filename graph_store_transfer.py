"""
Moving graphs between stores and keeping a copy in sync with the live store (G-V4.GRAPHSTORE.TRANSFER; REQ-SLY-016 to 039).

STUB of Plan step 4: the signatures and answers the red acceptance tests are written against; every function answers "nothing done", so the
checks fail by assertion. Implement replaces the bodies (plan.md, T-01 to T-05); the prototype's graph_store_move.py and graph_store_sync.py
(prototype/g-v4, rounds 02 and 03) are the basis.

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

FORMAT = 1                      # the format of a set of files this code writes and reads (REQ-SLY-032)
MARKER = "mia-store.json"       # the format marker in the root of a set of files
LOCK = "sync.lock"              # the lock file in the root of a copy (REQ-SLY-028)
ASIDE = "aside"                 # the aside folder in the root of a copy (REQ-SLY-026)
CONVERSION_STEP = "the conversion of G-V4.GRAPHSTORE.MIGRATION"   # named by the refusal of an older set (REQ-SLY-034)
# The graph group (REQ-SLY-025, 030): members first, headers last; VIEW's side tables where they are defined.
GRAPH_GROUP = ("graph_nodes", "graph_edges", "context_nodes", "context_edges", "skills", "graph_changes", "arrangements", "graphs")


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
    return {"copied": 0, "skipped": 0, "added_versions": 0}


def move_graph(source, target, graph_id):
    return {"graphs": 1, "records": 0}


def lag(live, copy):
    return {}


def sync_store(live, copy):
    return {"graphs": 0, "records": 0, "set_aside": {}}
