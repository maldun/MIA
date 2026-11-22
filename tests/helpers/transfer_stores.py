"""Stores and cases for the checks of G-V4.GRAPHSTORE.TRANSFER (test requirements TR-TRANSFER-002, -003, -004, -006, -011).

- sample_store(backend): the 15 converted skill graphs, `sample.code`, `context.cp13` (fixtures, unchanged) and `cp2.multi` with four versions saved
  by four accounts (TR-TRANSFER-003). small_store(backend): only `cp2.multi`, `sample.code`, `context.cp13` (TC-SLY-029, 036; owner, D-468).
- entries(backend): every record of every table with all its entries (author and time included): what a move must keep.
- equalize(source, target): the target gets the source's records, appended entry by entry, without the module under test (a plain copy).
- ac006(live, copy), ac007(live, copy): the accepted cases AC-006 and AC-007 (specs/mia/goals/G-V4/accepted-cases.md).
- damage_header(backend), add_broken(backend), add_alien(backend), add_cycle(backend): graphs written straight through the backend, around the
  checks of the graph model, as a damaged or foreign store would hold them.
- RecordingBackend(backend): logs every append as (table, record ID, version) (TC-SLY-019, TC-SLY-009).
- hold_lock(root): a separate process that holds the copy's lock until it is killed (TR-TRANSFER-006).
"""
import copy as _copy
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)
sys.path.insert(0, REPO)

from storage import Storage, table_definitions                     # noqa: E402
from graph_model import GraphModel                                  # noqa: E402
from core_stores import converted_graphs, fixture_graph             # noqa: E402

MULTI = "cp2.multi"
CODE = "sample.code"
CONTEXT = "context.cp13"
AUTHORS = ("owner", "author2", "author3", "author4")
STAMP = "2026-11-20T12:00:00Z"


def multi_graph(tool="tool.v1"):
    """cp2.multi: data -> processing step -> data; each version changes the processing step's tool, so each version changes one member."""
    return {"id": MULTI, "context_graph_id": "ctx", "testbench_id": "tb", "description": "several versions by several accounts",
            "nodes": [{"id": "var.in", "data": {"type": "data", "value": "x"}},
                      {"id": "step.write", "data": {"type": "transform", "toolbox_id": tool}},
                      {"id": "var.out", "data": {"type": "data"}}],
            "edges": [{"id": "e1", "from": "var.in", "to": "step.write", "data": {}},
                      {"id": "e2", "from": "step.write", "to": "var.out", "data": {}}]}


def save(backend, graph, author):
    result = GraphModel(Storage(backend), author=author).save_graph(graph)
    assert result.saved, result
    return result.version


def add_multi(backend):
    for k, author in enumerate(AUTHORS, start=1):
        save(backend, multi_graph("tool.v%d" % k), author)


def sample_store(backend):
    for graph in converted_graphs():
        save(backend, graph, "owner")
    save(backend, fixture_graph(CODE), "owner")
    save(backend, fixture_graph(CONTEXT), "owner")
    add_multi(backend)
    return backend


def small_store(backend):
    save(backend, fixture_graph(CODE), "owner")
    save(backend, fixture_graph(CONTEXT), "owner")
    add_multi(backend)
    return backend


def tables():
    """every table a store can hold, the graph group's side tables included where they are defined"""
    return sorted(table_definitions())


def entries(backend, only=None):
    """{table: {record ID: [entries]}} for every table that holds a record (author and time included)"""
    out = {}
    for table in only or tables():
        ids = sorted(backend.ids(table))
        if ids:
            out[table] = {i: backend.versions(table, i) for i in ids}
    return out


GRAPH_GROUP = ("graph_nodes", "graph_edges", "context_nodes", "context_edges", "skills", "graph_changes", "arrangements", "graphs")


def graph_group(backend):
    return entries(backend, [t for t in GRAPH_GROUP if t in table_definitions()])


def equalize(source, target):
    """the target gets the source's records entry by entry, members before headers, without the module under test"""
    for table in [t for t in GRAPH_GROUP if t in table_definitions()] + [t for t in tables() if t not in GRAPH_GROUP]:
        for record_id in source.ids(table):
            have = len(target.versions(table, record_id))
            for entry in source.versions(table, record_id)[have:]:
                target.append(table, record_id, entry)


def new_multi_version(backend, value, author="elsewhere"):
    graph = GraphModel(Storage(backend), author=author).read_graph(MULTI)
    next(n for n in graph["nodes"] if n["id"] == "var.in")["data"]["value"] = value
    return save(backend, graph, author)


def new_code_version(backend, value, author):
    graph = GraphModel(Storage(backend), author=author).read_graph(CODE)
    next(n for n in graph["nodes"] if n["id"] == "var.in")["data"]["value"] = value
    return save(backend, graph, author)


def ac006(live, copy):
    """AC-006: live and copy equal, then two new live versions of cp2.multi: live 6, copy 4"""
    sample_store(live)
    equalize(live, copy)
    new_multi_version(live, "a")
    new_multi_version(live, "b")


def ac007(live, copy, with_store=True):
    """AC-007: sample.code equal at version 1 on both; a version 2 only on the copy, a different version 2 in the live store"""
    if with_store:
        sample_store(live)
        equalize(live, copy)
    new_code_version(copy, "only on the copy", "copy-writer")
    new_code_version(live, "live version", "elsewhere")


def _raw(backend, table, record_id, doc, version=1, author="foreign"):
    backend.append(table, record_id, {"id": record_id, "version": version, "author": author, "time": STAMP, "doc": doc})


def damage_header(backend):
    """a new header version of cp2.multi that names a version of `step.write` the store does not hold; returns that member ID and version"""
    member = MULTI + "/step.write"
    missing = len(backend.versions("graph_nodes", member)) + 1
    last = backend.versions("graphs", MULTI)[-1]
    doc = _copy.deepcopy(last["doc"])
    for item in doc["data"]["nodes"]:
        if item["id"] == member:
            item["version"] = missing
    _raw(backend, "graphs", MULTI, doc, version=last["version"] + 1)
    return member, missing


def add_broken(backend):
    """sample.broken: a connection e2 to a step var.gone that does not exist (as the prototype's make_sample_store --broken)"""
    g = "sample.broken"
    steps = {"var.in": {"type": "data", "value": "x"}, "step.a": {"type": "transform", "toolbox_id": "tool.a"}}
    for local, data in steps.items():
        _raw(backend, "graph_nodes", "%s/%s" % (g, local), {"id": "%s/%s" % (g, local), "data": data})
    for local, a, b in (("e1", "var.in", "step.a"), ("e2", "step.a", "var.gone")):
        _raw(backend, "graph_edges", "%s/%s" % (g, local), {"id": "%s/%s" % (g, local), "from": "%s/%s" % (g, a), "to": "%s/%s" % (g, b), "data": {}})
    _raw(backend, "graphs", g, {"id": g, "data": {"kind": "workflow", "context_graph_id": "ctx", "testbench_id": "tb", "description": "broken",
                                                  "nodes": [{"id": "%s/%s" % (g, k), "version": 1} for k in steps],
                                                  "edges": [{"id": "%s/e1" % g, "version": 1}, {"id": "%s/e2" % g, "version": 1}]}})
    return g, "%s/e2" % g


def add_alien(backend, graph_id="alien"):
    """a graph of kind `swarm`, which the registry of kinds does not know"""
    node = "%s/x" % graph_id
    _raw(backend, "graph_nodes", node, {"id": node, "data": {"type": "data"}})
    _raw(backend, "graphs", graph_id, {"id": graph_id, "data": {"kind": "swarm", "context_graph_id": "ctx", "testbench_id": "tb",
                                                                "description": "a later kind", "nodes": [{"id": node, "version": 1}], "edges": []}})
    return graph_id


def add_cycle(backend, graph_id="cyc"):
    """a graph whose records are sound but that breaks the cycle rule: d1 -> t1 -> d1"""
    d1, t1 = "%s/d1" % graph_id, "%s/t1" % graph_id
    _raw(backend, "graph_nodes", d1, {"id": d1, "data": {"type": "data"}})
    _raw(backend, "graph_nodes", t1, {"id": t1, "data": {"type": "transform", "toolbox_id": "tool.t"}})
    for local, a, b in (("e1", d1, t1), ("e2", t1, d1)):
        cid = "%s/%s" % (graph_id, local)
        _raw(backend, "graph_edges", cid, {"id": cid, "from": a, "to": b, "data": {}})
    _raw(backend, "graphs", graph_id, {"id": graph_id, "data": {"kind": "workflow", "context_graph_id": "ctx", "testbench_id": "tb",
                                                                "description": "a cycle", "nodes": [{"id": d1, "version": 1}, {"id": t1, "version": 1}],
                                                                "edges": [{"id": "%s/e1" % graph_id, "version": 1}, {"id": "%s/e2" % graph_id, "version": 1}]}})
    return graph_id


def headers_complete(backend):
    """the graphs whose newest header names a member version the store does not hold: [] when every graph is complete"""
    broken = []
    for graph_id in backend.ids("graphs"):
        data = backend.versions("graphs", graph_id)[-1]["doc"]["data"]
        tables = ("context_nodes", "context_edges") if data.get("kind") == "context" else ("graph_nodes", "graph_edges")
        for key, table in zip(("nodes", "edges"), tables):
            for item in data[key]:
                if item["version"] > len(backend.versions(table, item["id"])):
                    broken.append(graph_id)
    return sorted(set(broken))


class RecordingBackend:
    """logs every append as (table, record ID, version); everything else goes to the wrapped backend"""

    def __init__(self, backend):
        self.backend = backend
        self.log = []

    def append(self, table, record_id, entry):
        self.log.append((table, record_id, entry["version"]))
        return self.backend.append(table, record_id, entry)

    def __getattr__(self, name):
        return getattr(self.backend, name)


class WriteLog:
    """logs every write by kind, as FailingBackend counts them: ("append" | "remove" | "cut" | "file", name) (TR-TRANSFER-004)"""

    def __init__(self, backend):
        self.backend = backend
        self.log = []

    def append(self, table, record_id, entry):
        self.log.append(("append", "%s|%s" % (table, record_id)))
        return self.backend.append(table, record_id, entry)

    def remove(self, table, record_id):
        self.log.append(("remove", "%s|%s" % (table, record_id)))
        return self.backend.remove(table, record_id)

    def cut(self, table, record_id, version):
        self.log.append(("cut", "%s|%s" % (table, record_id)))
        return self.backend.cut(table, record_id, version)

    def put_file(self, path, text):
        self.log.append(("file", path))
        return self.backend.put_file(path, text)

    def __getattr__(self, name):
        return getattr(self.backend, name)


def clone_folder(backend, test):
    """a FileBackend on a copy of `backend`'s folder: the same entries, times included, for one more run from the same start"""
    import shutil
    import tempfile
    from storage_files import FileBackend
    root = tempfile.mkdtemp(prefix="transfer-")
    test.addCleanup(shutil.rmtree, root, True)
    shutil.copytree(backend.root, root, dirs_exist_ok=True)
    return FileBackend(root)


def members_before_headers(log, backend):
    """the header versions in `log` that name a member version written later or not at all: [] when the order is right"""
    position = {(t, i, v): n for n, (t, i, v) in enumerate(log)}
    late = []
    for n, (table, graph_id, version) in enumerate(log):
        if table != "graphs":
            continue
        data = backend.versions("graphs", graph_id)[version - 1]["doc"]["data"]
        tables = ("context_nodes", "context_edges") if data.get("kind") == "context" else ("graph_nodes", "graph_edges")
        for key, member_table in zip(("nodes", "edges"), tables):
            for item in data[key]:
                at = position.get((member_table, item["id"], item["version"]))
                if at is not None and at > n:
                    late.append((graph_id, version, item["id"], item["version"]))
    return late


def hold_lock(root):
    """a separate process that takes the copy's lock as the sync does and waits; returns the process once the lock is held (TR-TRANSFER-006)"""
    code = ("import sys, time; sys.path.insert(0, %r); import graph_store_transfer as t\n"
            "with t.copy_lock(%r):\n    print('held', flush=True)\n    time.sleep(600)\n") % (REPO, root)
    proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
    line = proc.stdout.readline().strip()
    if line != "held":
        proc.kill()
        raise AssertionError("the lock holder did not start: %r" % line)
    return proc


def kill(proc):
    proc.kill()
    proc.wait(timeout=10)
    time.sleep(0.1)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)
