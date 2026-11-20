"""One-way sync from the live store to a copy (PROTOTYPE CP3, G-V4.GRAPHSTORE.TRANSFER, FR-93, NFR-16).

lag(live, copy)        per graph: how many versions the copy lacks, and whether its history differs; shown before a sync
sync_store(live, copy, aside)   the copy equals the live store afterwards. The live store wins: a graph whose history on the copy differs (versions only the copy has, or
                        a different history) is first written to a file in the `aside` folder, named in the answer, and only then replaced; a graph that exists only on the
                        copy is set aside the same way. Nothing is lost, repeatable, a graph is entirely as before or entirely new (the aside file is written first, the
                        header of a graph leaves the copy first and arrives last, as in graph_store_move).
AutoSync(live, copy, aside)    a context manager: syncs when it is entered (MIA starts) and when it is left (an orderly stop); a live store that cannot be reached
                        is reported and never keeps MIA from starting or stopping.
python graph_store_sync.py <live> <copy> [--aside <folder>] [--lag]
"""
import json
import os
import time

try:
    from .storage import StorageError
    from . import graph_store_move as move
except ImportError:
    from storage import StorageError
    import graph_store_move as move

HEADER = move.HEADER_TABLE


def _members(backend, graph_id):
    """(table, record id) of every step and connection any version of the graph pins, in that backend"""
    found = []
    for entry in backend.versions(HEADER, graph_id):
        data = entry["doc"]["data"]
        node_table, edge_table = move.MEMBER_TABLES[data["kind"]]
        for key, table in (("nodes", node_table), ("edges", edge_table)):
            for member in data[key]:
                if (table, member["id"]) not in found:
                    found.append((table, member["id"]))
    return found


def lag(live, copy):
    """{graph id: {"live": n, "copy": m, "state": current | behind | differs | copy_only | refused, "reason": text}} for every graph of either store"""
    problems = move._problems(live, copy)
    out = {}
    for graph_id in live.ids(HEADER):
        there, here = live.versions(HEADER, graph_id), copy.versions(HEADER, graph_id)
        row = {"live": len(there), "copy": len(here)}
        reason = problems.get(graph_id)
        if reason and reason.startswith("conflict"):
            row.update(state="differs", reason=reason)
        elif reason:
            row.update(state="refused", reason=reason)
        elif len(here) > len(there):
            row.update(state="differs", reason="the copy has versions the live store does not have")
        else:
            row["state"] = "current" if len(here) == len(there) else "behind"
        out[graph_id] = row
    for graph_id in copy.ids(HEADER):
        if graph_id not in out:
            out[graph_id] = {"live": 0, "copy": len(copy.versions(HEADER, graph_id)), "state": "copy_only", "reason": "the graph exists only on the copy"}
    return out


def _set_aside(copy, graph_id, folder, stamp):
    """writes everything the copy holds of the graph to a file, durably, and returns {"file", "versions"} (the versions only the copy has, or all of them when the histories differ)"""
    os.makedirs(folder, exist_ok=True)
    name = "%s__%s.json" % (graph_id.replace("/", "_"), stamp)
    path = os.path.join(folder, name)
    n = 1
    while os.path.exists(path):                                            # two set-asides in one second never overwrite each other
        n += 1
        path = os.path.join(folder, "%s__%s_%d.json" % (graph_id.replace("/", "_"), stamp, n))
    members = {"%s|%s" % key: copy.versions(*key) for key in _members(copy, graph_id)}
    members.update({"%s|%s" % (move.CHANGES_TABLE, rid): copy.versions(move.CHANGES_TABLE, rid) for rid in move.change_ids(copy, graph_id)})      # the record of changes goes with the graph
    doc = {"graph": graph_id, "set_aside_at": stamp, "reason": "the live store won", "header": copy.versions(HEADER, graph_id), "members": members}
    tmp = path + ".part"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return path, doc


def _remove_from(copy, graph_id):
    members = _members(copy, graph_id) + [(move.CHANGES_TABLE, rid) for rid in move.change_ids(copy, graph_id)]
    copy.remove(HEADER, graph_id)                                          # the header first: a graph is never listed with missing steps
    for table, record_id in members:
        copy.remove(table, record_id)


def _clear_orphans(live, copy):
    """an interrupted sync can leave steps of a graph on the copy whose header is gone (it was removed first); steps with a history that is not the live one are dropped
    (a set-aside file with them was written before the header left), so the graph can be moved again"""
    for graph_id in live.ids(HEADER):
        if copy.versions(HEADER, graph_id):
            continue
        for table, record_id in _members(live, graph_id):
            there, wanted = copy.versions(table, record_id), live.versions(table, record_id)
            if there and there != wanted[:len(there)]:
                copy.remove(table, record_id)


def sync_store(live, copy, aside, now=None):
    """returns {"graphs", "records", "set_aside": {graph: {"file", "versions"}}}; refuses (nothing written) when a graph of the live store cannot be moved"""
    states = lag(live, copy)
    refused = {g: r["reason"] for g, r in states.items() if r["state"] == "refused"}
    if refused:
        raise StorageError("invalid", rule="move_refused", detail={"graphs": refused})
    _clear_orphans(live, copy)
    states = lag(live, copy)
    stamp = now or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    result = {"graphs": len(live.ids(HEADER)), "records": 0, "set_aside": {}}
    for graph_id, row in sorted(states.items()):
        if row["state"] in ("differs", "copy_only"):
            path, doc = _set_aside(copy, graph_id, aside, stamp)
            ours = [e["version"] for e in doc["header"]]
            theirs = [e["version"] for e in live.versions(HEADER, graph_id)] if row["state"] == "differs" else []
            same = 0
            for a, b in zip(doc["header"], live.versions(HEADER, graph_id) if row["state"] == "differs" else []):
                if a != b:
                    break
                same += 1
            result["set_aside"][graph_id] = {"file": path, "versions": ours[same:] or ours, "reason": row["reason"]}
            _remove_from(copy, graph_id)
    for graph_id in live.ids(HEADER):
        if states[graph_id]["state"] != "current":
            result["records"] += move.move_graph(live, copy, graph_id)["records"]
    return result


class AutoSync:
    """MIA starts: sync; MIA stops in an orderly way: sync. `reports` says what happened at each point; a live store that cannot be reached is a report, not a failure."""
    def __init__(self, live, copy, aside):
        self.live, self.copy, self.aside, self.reports = live, copy, aside, []

    def run(self, when):
        try:
            self.reports.append({"when": when, **sync_store(self.live, self.copy, self.aside)})
        except StorageError as error:
            self.reports.append({"when": when, "refused": error.detail})
        except Exception as error:                                         # noqa: BLE001 - an unreachable live store is told, a bug is not hidden
            if isinstance(error, (OSError, ConnectionError, TimeoutError)) or type(error).__name__ in ("OperationalError", "InterfaceError", "AdminShutdown", "ConnectionTimeout"):
                self.reports.append({"when": when, "unreachable": "the live store cannot be reached: %s works on the copy as it is" % when})
            else:
                raise
        return self.reports[-1]

    def __enter__(self):
        self.run("start")
        return self

    def __exit__(self, *exc):
        self.run("stop")
        return False


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="one-way sync from the live store to a copy; the live store wins")
    ap.add_argument("live"); ap.add_argument("copy")
    ap.add_argument("--aside", default="sync-aside", help="where the versions only the copy has are written before they are replaced")
    ap.add_argument("--lag", action="store_true", help="only show how far the copy lags")
    a = ap.parse_args()
    live, copy = move._open(a.live), move._open(a.copy)
    if a.lag:
        for g, r in sorted(lag(live, copy).items()):
            print("%-40s live %-3d copy %-3d %s %s" % (g, r["live"], r["copy"], r["state"], r.get("reason", "")))
        raise SystemExit(0)
    try:
        out = sync_store(live, copy, a.aside)
    except StorageError as err:
        print("refused: nothing was synced. These graphs cannot be moved:")
        for graph, reason in err.detail["graphs"].items():
            print("  %s: %s" % (graph, reason))
        raise SystemExit(1)
    print(json.dumps(out, indent=1))
