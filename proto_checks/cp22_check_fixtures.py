"""PROTOTYPE round 05: the graphs of kinds the editor cannot change, shared by cp22_check.py and cp23_check.py (importing a check would run it)."""


def ctx(gid):
    """the context graph of cp19 (copied: importing that module runs it)"""
    return {"id": gid, "kind": "context", "context_graph_id": "", "testbench_id": "", "description": "context graph of cp22",
            "nodes": [{"id": "claim", "data": {"type": "claim", "text": "water boils at 100 C"}}, {"id": "source", "data": {"type": "source", "url": "local:book-1"}}],
            "edges": [{"id": "e1", "from": "source", "to": "claim", "data": {"relation": "supports"}}]}

def put_unknown(backend, gid, kind, versions):
    """a graph of a kind the program does not know, written around the Storage layer (which refuses such a header, cp19's finding): as a newer store would hold it"""
    def put(table, rid, version, doc):
        backend.append(table, rid, {"id": rid, "version": version, "author": "newer", "time": "2026-11-27T12:00:0%dZ" % version, "doc": doc})
    put("graph_nodes", "%s/n1" % gid, 1, {"id": "%s/n1" % gid, "data": {"type": "step", "text": "one"}})
    put("graph_nodes", "%s/n2" % gid, 1, {"id": "%s/n2" % gid, "data": {"type": "step", "text": "two"}})
    for v in range(1, versions + 1):
        nodes = [{"id": "%s/n1" % gid, "version": 1}] + ([{"id": "%s/n2" % gid, "version": 1}] if v > 1 else [])
        put("graphs", gid, v, {"id": gid, "data": {"kind": kind, "context_graph_id": "", "testbench_id": "", "description": "a kind from a newer program", "nodes": nodes, "edges": []}})
