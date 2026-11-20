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
GRAPH_TABLES = ("graph_nodes", "graph_edges", "context_nodes", "context_edges", HEADER_TABLE)


def _problems(source, target):
    """{graph id: reason} of the graphs that cannot be moved or that conflict with the target."""
    found = {}
    for graph_id in source.ids(HEADER_TABLE):
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
            found[graph_id] = "conflict: the target has a different history"
    return found


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
        print("refused:", err.rule, json.dumps(err.detail))
        raise SystemExit(1)
