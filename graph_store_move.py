"""Move the whole store of graphs between the live store and a set of files (PROTOTYPE CP2, G-V4.GRAPHSTORE.TRANSFER, FR-59).

move_store(source, target) -> {"graphs", "records", "versions_added", "skipped"}; source and target are backends (FileBackend, PostgresBackend).
- All or nothing per move: every graph of the source is checked first (its headers, its pinned step versions, the scoped IDs) and the target is compared with it; if one graph
  cannot be moved or conflicts with a different history in the target, the move is refused with the graphs named and nothing is written.
- Nothing is renumbered, authors and times are kept; moving again changes nothing; an interrupted move can be run again: the steps are written before the headers, so a graph
  appears in the target only when all its steps are there.
"""
try:
    from . import graph_tables
    from .storage import StorageError
    from .storage_copy import copy_records, _check_entries
except ImportError:
    import graph_tables
    from storage import StorageError
    from storage_copy import copy_records, _check_entries

MEMBER_TABLES = {"workflow": ("graph_nodes", "graph_edges"), "context": ("context_nodes", "context_edges")}
HEADER_TABLE = "graphs"
CHANGES_TABLE = "graph_changes"           # CP11 (FR-81): the record of changes belongs to the graph and moves with it; one record per version, id <graph id>/<version>
GRAPH_TABLES = ("graph_nodes", "graph_edges", "context_nodes", "context_edges", CHANGES_TABLE, HEADER_TABLE)


def change_ids(backend, graph_id):
    """the IDs of the records of changes of the graph that the backend has"""
    return [rid for rid in (("%s/%d" % (graph_id, e["version"])) for e in backend.versions(HEADER_TABLE, graph_id)) if backend.versions(CHANGES_TABLE, rid)]


def _problems(source, target, only=None):
    """{graph id: reason} of the graphs that cannot be moved or that conflict with the target (only those named, when `only` is given)."""
    found = {}
    for graph_id in (only if only is not None else source.ids(HEADER_TABLE)):
        entries = source.versions(HEADER_TABLE, graph_id)
        try:
            _check_entries(HEADER_TABLE, graph_id, entries)
            for entry in entries:
                data = entry["doc"]["data"]
                node_table, edge_table = MEMBER_TABLES[data["kind"]]
                stored = {("nodes" if data["kind"] == "workflow" else "context_nodes"): {}, ("edges" if data["kind"] == "workflow" else "context_edges"): {}}
                for key, table, name in (("nodes", node_table, "nodes" if data["kind"] == "workflow" else "context_nodes"), ("edges", edge_table, "edges" if data["kind"] == "workflow" else "context_edges")):
                    for member in data[key]:
                        versions = source.versions(table, member["id"])
                        _check_entries(table, member["id"], versions)
                        stored[name][member["id"]] = [v["version"] for v in versions]
                broken = graph_tables.check_record(HEADER_TABLE, entry["doc"], stored=stored, record_id=graph_id)
                if broken:
                    raise StorageError("invalid", rule=broken["rule"], detail=broken["detail"])
        except StorageError as err:
            found[graph_id] = "%s %s" % (err.rule or err.code, err.detail)
            continue
        have = target.versions(HEADER_TABLE, graph_id)
        if have != entries[:len(have)]:
            found[graph_id] = "conflict: the target has a different history of the graph"
            continue
        for entry in entries:                       # the record of a change with a different history in the target is a conflict of this graph too
            rid = "%s/%d" % (graph_id, entry["version"])
            wanted_c, there_c = source.versions(CHANGES_TABLE, rid), target.versions(CHANGES_TABLE, rid)
            if there_c != wanted_c[:len(there_c)]:
                found[graph_id] = "conflict: the target has a different record of the change of version %d" % entry["version"]
        for entry in entries:                       # a step or connection with a different history in the target is a conflict of this graph too
            data = entry["doc"]["data"]
            node_table, edge_table = MEMBER_TABLES[data["kind"]]
            for key, table in (("nodes", node_table), ("edges", edge_table)):
                for member in data[key]:
                    wanted, there = source.versions(table, member["id"]), target.versions(table, member["id"])
                    if there != wanted[:len(there)]:
                        found[graph_id] = "conflict: the target has a different history of %s" % member["id"]
    return found


def move_graph(source, target, graph_id):
    """One graph with all its steps and connections and all its versions, from the source to the target (after a change in the live store, the copy gets it at once).
    The same rules as move_store: checked first, a conflict or a graph that cannot be moved is refused with the graph named and nothing is written; repeatable."""
    problems = _problems(source, target, only=[graph_id])
    if problems:
        raise StorageError("invalid", rule="move_refused", detail={"graphs": problems})
    members = []
    for entry in source.versions(HEADER_TABLE, graph_id):
        data = entry["doc"]["data"]
        node_table, edge_table = MEMBER_TABLES[data["kind"]]
        for key, table in (("nodes", node_table), ("edges", edge_table)):
            for member in data[key]:
                if (table, member["id"]) not in members:
                    members.append((table, member["id"]))
    added = 0
    changes = [(CHANGES_TABLE, "%s/%d" % (graph_id, e["version"])) for e in source.versions(HEADER_TABLE, graph_id)]
    for table, record_id in members + changes + [(HEADER_TABLE, graph_id)]:           # the steps and the record of changes first, the header last
        wanted, have = source.versions(table, record_id), target.versions(table, record_id)
        for entry in wanted[len(have):]:
            target.append(table, record_id, entry)
            added += 1
    return {"graphs": 1, "records": added}


def move_store(source, target):
    problems = _problems(source, target)
    if problems:
        raise StorageError("invalid", rule="move_refused", detail={"graphs": problems})
    totals = {"graphs": len(source.ids(HEADER_TABLE)), "records": 0, "versions_added": 0, "skipped": 0}
    for tables in ((GRAPH_TABLES[:-1]), (HEADER_TABLE,)):            # the steps first, the headers last
        counts = copy_records(source, target, tables)
        totals["records"] += counts["copied"]
        totals["versions_added"] += counts["added_versions"]
        totals["skipped"] += counts["skipped"]
    return totals


def _open(spec):
    kind, _, rest = spec.partition(":")
    if kind == "files":
        try:
            from .storage_files import FileBackend
        except ImportError:
            from storage_files import FileBackend
        return FileBackend(rest)
    if kind == "postgres":
        try:
            from .storage_postgres import PostgresBackend
        except ImportError:
            from storage_postgres import PostgresBackend
        return PostgresBackend(rest)
    raise SystemExit("a store is files:<folder> or postgres:<url>")


if __name__ == "__main__":     # python graph_store_move.py files:/some/folder files:/other/folder   (or postgres:<url>)
    import json
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: graph_store_move.py <source> <target>   (files:<folder> | postgres:<url>)")
    try:
        print(json.dumps(move_store(_open(sys.argv[1]), _open(sys.argv[2]))))
    except StorageError as err:
        if err.rule == "move_refused":
            print("refused: nothing was moved. These graphs cannot be moved:")
            for graph, reason in err.detail["graphs"].items():
                print("  %s: %s" % (graph, reason))
        else:
            print("refused:", err.code, err.rule or "", json.dumps(err.detail))
        raise SystemExit(1)
