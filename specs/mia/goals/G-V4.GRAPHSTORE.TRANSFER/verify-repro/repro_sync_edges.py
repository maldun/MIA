"""Reproductions of the Verify findings V-1 to V-3 of G-V4.GRAPHSTORE.TRANSFER (files backend only, throw-away folders).
  <venv python> repro_sync_edges.py CHECKOUT
Prints one line per case; the expected lines of the branch at Verify (2026-11-27) are in verification-report.md."""
import os, sys, json, shutil, tempfile, copy as cp
W = os.path.abspath(sys.argv[1])
sys.path.insert(0, os.path.join(W, "tests", "helpers")); sys.path.insert(0, W)
import transfer_stores as ts                     # noqa: E402
from storage_files import FileBackend            # noqa: E402
from storage import StorageError                 # noqa: E402
import graph_store_transfer as gst               # noqa: E402

TMP = tempfile.mkdtemp(prefix="transfer-verify-")


def pair():
    d = tempfile.mkdtemp(dir=TMP)
    return FileBackend(os.path.join(d, "live")), FileBackend(os.path.join(d, "copy"))


def old_record(root):
    os.makedirs(os.path.join(root, "graph_nodes"), exist_ok=True)
    with open(os.path.join(root, "graph_nodes", "n1.json"), "w") as f:
        json.dump([{"id": "n1", "version": 1, "author": "a", "time": ts.STAMP, "doc": {}}], f)


try:
    # V-1: a whole-store move into a copy whose lock another process holds
    live, copy = pair(); ts.small_store(live)
    holder = ts.hold_lock(copy.root)
    try:
        try:
            print("V-1 move_store into a locked copy: written", gst.move_store(live, copy))
        except StorageError as e:
            print("V-1 move_store into a locked copy: refused", e.code, e.detail)
    finally:
        ts.kill(holder)

    # V-2a: a copy-only record of the graph group that no header names
    live, copy = pair(); ts.small_store(live); ts.equalize(live, copy)
    node = cp.deepcopy(live.versions("graph_nodes", sorted(live.ids("graph_nodes"))[0])[0]); node["id"] = "orphan.graph/x"
    copy.append("graph_nodes", "orphan.graph/x", node)
    ans = gst.sync_store(live, copy)
    print("V-2a sync:", ans, "lag after:", gst.lag(live, copy), "orphan still on the copy:", bool(copy.versions("graph_nodes", "orphan.graph/x")),
          "graph group equal:", ts.graph_group(live) == ts.graph_group(copy))

    # V-2b: a differing record of the graph group that no header names
    live, copy = pair(); ts.small_store(live); ts.equalize(live, copy)
    for store, author in ((live, "x"), (copy, "y")):
        n = cp.deepcopy(node); n["id"] = "lonely.g/z"; n["author"] = author; store.append("graph_nodes", "lonely.g/z", n)
    print("V-2b lag before the sync:", gst.lag(live, copy))
    try:
        print("V-2b sync:", gst.sync_store(live, copy))
    except StorageError as e:
        print("V-2b sync refused:", e.code, e.detail)

    # V-3: a sync into a copy that is an older set (no marker) with an unscoped record
    live, copy = pair(); ts.small_store(live); old_record(copy.root)
    try:
        ans = gst.sync_store(live, copy)
        print("V-3 sync into an older copy: written", ans, "marker now", copy.format())
    except StorageError as e:
        print("V-3 sync into an older copy: refused", e.code, e.rule, e.detail)
    try:
        gst.move_store(FileBackend(copy.root), FileBackend(tempfile.mkdtemp(dir=TMP)))
        print("V-3 move from it afterwards: written")
    except StorageError as e:
        print("V-3 move from it afterwards: refused", e.code, e.rule, e.detail)
finally:
    shutil.rmtree(TMP, True)
