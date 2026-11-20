"""PROTOTYPE CP15 checks (not protected tests): no half-stored graph, whatever the write at which a save, a move or a sync is interrupted (NFR-16, measure HR-005 of the CORE high-level spec).
Every write position k = 1..n of each case is tried, nothing is sampled. Run: python proto_checks/cp15_check.py [files|postgres]"""
import copy, json, os, shutil, sys, tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO, os.path.join(REPO, "tests")]
os.chdir(REPO)
import graph_model, graph_store_move as move, graph_store_sync as sy
from storage import Storage, StorageError
from proto_checks.cp1_check import backend

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

class Counting:
    """the backend with a counter of writes (append and remove); `fail_at` makes the k-th write raise like a lost disk or connection"""
    def __init__(self, inner, fail_at=None): self.inner, self.fail_at, self.writes = inner, fail_at, 0
    def __getattr__(self, name):
        f = getattr(self.inner, name)
        if name not in ("append", "remove"): return f
        def counted(*a, **k):
            self.writes += 1
            if self.fail_at is not None and self.writes == self.fail_at: raise OSError("write %d failed" % self.writes)
            return f(*a, **k)
        return counted

def wf(gid, v="a"):
    return {"id": gid, "context_graph_id": "ctx", "testbench_id": "tb", "description": "cp15", "nodes": [{"id": "in", "data": {"type": "data", "value": v}}, {"id": "s1", "data": {"type": "transform", "toolbox_id": "tool." + v}}, {"id": "mid", "data": {"type": "data"}}, {"id": "loop", "data": {"type": "master", "toolbox_id": "control.loop", "stop": {"max_repetitions": 2}}}, {"id": "out", "data": {"type": "data"}}],
            "edges": [{"id": "e1", "from": "in", "to": "s1", "data": {}}, {"id": "e2", "from": "s1", "to": "mid", "data": {}}, {"id": "e3", "from": "mid", "to": "loop", "data": {}}, {"id": "e4", "from": "loop", "to": "out", "data": {}}]}
def cx(gid, v="a"):
    return {"id": gid, "kind": "context", "context_graph_id": "", "testbench_id": "", "description": "cp15", "nodes": [{"id": "claim", "data": {"type": "claim", "text": v}}, {"id": "source", "data": {"type": "source", "url": "u" + v}}, {"id": "note", "data": {"type": "note"}}],
            "edges": [{"id": "e1", "from": "source", "to": "claim", "data": {}}, {"id": "e2", "from": "claim", "to": "note", "data": {}}]}

def whole(be, gid, states):
    """True when the graph in `be` is one of `states` (graphs as the caller sees them, None = not there), every version of it is readable, and no header names a member that is not stored"""
    st = Storage(be); m = graph_model.GraphModel(st)
    if gid not in st.ids("graphs"):
        return None in states
    try:
        for v in st.history("graphs", gid): m.read_graph(gid, v["version"])
        return m.read_graph(gid) in states
    except StorageError:
        return False

def trial_save(be, gid, before, after, k):
    c = Counting(be, k); gm = graph_model.GraphModel(Storage(c), author="fi")
    try: gm.save_graph(after)
    except OSError: pass
    return c

def run(kind):
    be, stop = backend(kind)
    try:
        cases = {"first save of a workflow graph": (None, wf("W", "a")), "second save of a workflow graph (a step and the loop limit changed)": (wf("W", "a"), None),
                 "first save of a context graph": (None, cx("C", "a")), "second save of a context graph (a step changed)": (cx("C", "a"), None)}
        for name, (old, new) in cases.items():
            n_ok, n_total, rerun_ok, counted = 0, 0, 0, None
            # how many writes does the save take
            probe = f"P{abs(hash(name)) % 10**6}"; mk = (lambda g, gid: {**g, "id": gid})
            base_old = old and mk(old, probe); 
            if base_old: graph_model.GraphModel(Storage(be), author="seed").save_graph(base_old)
            target_new = mk(new, probe) if new else mk(copy.deepcopy(old), probe)
            if not new:
                tn = target_new["nodes"]; tn[0]["data"] = {**tn[0]["data"], **({"text": "b"} if tn[0]["data"]["type"] == "claim" else {"value": "b"})}
                if tn[1]["data"]["type"] == "master": tn[1]["data"]["stop"] = {"max_repetitions": 3}
                if "toolbox_id" in tn[1]["data"] and tn[1]["data"]["type"] == "transform": tn[1]["data"]["toolbox_id"] = "tool.b"
                if old.get("nodes", [])[3:]:
                    for nd in tn:
                        if nd["data"]["type"] == "master": nd["data"]["stop"] = {"max_repetitions": 3}
            c = Counting(be); graph_model.GraphModel(Storage(c), author="probe").save_graph(copy.deepcopy(target_new)) if not old else None
            if old:
                # measure on a scratch copy of the seed state so the probe does not change the real trial graph
                scratch = f"{probe}x"; graph_model.GraphModel(Storage(be), author="seed").save_graph(mk(old, scratch)); c = Counting(be); graph_model.GraphModel(Storage(c), author="probe").save_graph(mk(target_new, scratch))
            total = c.writes
            old_state = None if not old else graph_model.GraphModel(Storage(be)).read_graph(probe)
            # new graph as the caller sees it after a save: read back from a scratch id (same content)
            for k in range(1, total + 1):
                gid = f"{probe}.k{k}"
                if old: graph_model.GraphModel(Storage(be), author="seed").save_graph(mk(old, gid))
                before = None if not old else graph_model.GraphModel(Storage(be)).read_graph(gid)
                cc = Counting(be, k); gm = graph_model.GraphModel(Storage(cc), author="fi")
                try: gm.save_graph(mk(target_new, gid))
                except OSError: pass
                full_new = mk(target_new, gid)
                got_whole = whole(be, gid, [before, {**full_new, **({"kind": "context"} if "kind" in full_new else {})}] if before else [None, {**full_new, **({"kind": "context"} if "kind" in full_new else {})}])
                n_ok += bool(got_whole); n_total += 1
                gm.save_graph(mk(target_new, gid)); rerun_ok += whole(be, gid, [full_new])
            check(f"NFR-16 {name}: interrupted after each of its {total} writes, the graph is entirely as before or entirely new, and a repeated save finishes it", n_ok == n_total == rerun_ok and total > 0, f"{n_ok}/{n_total} whole, {rerun_ok}/{n_total} finished")
        # refused saves write nothing
        st = Storage(be); gm = graph_model.GraphModel(st, author="r")
        cyc = wf("R1"); cyc["edges"].append({"id": "e9", "from": "out", "to": "in", "data": {}}); two = wf("R2"); two["nodes"].append({"id": "s2", "data": {"type": "transform", "toolbox_id": "t"}}); two["edges"].append({"id": "e9", "from": "s2", "to": "mid", "data": {}})
        bad = {"cycle": cyc, "two writers": two, "unknown kind of step": {**wf("R3"), "nodes": wf("R3")["nodes"] + [{"id": "x", "data": {"type": "wizard"}}]}, "context graph with a missing end": {**cx("R4"), "edges": [{"id": "e1", "from": "claim", "to": "zz", "data": {}}]}}
        count = lambda: {t: sum(len(st.history(t, i)) for i in st.ids(t)) for t in ("graph_nodes", "graph_edges", "context_nodes", "context_edges", "graphs")}
        n0 = count(); res = {k: gm.save_graph(g) for k, g in bad.items()}
        check("NFR-16 a refused save (a cycle, two writers, an unknown kind of step, a context connection to a missing step) writes no record and counts no version", all(not r.saved for r in res.values()) and n0 == count(), json.dumps({k: [r.saved, r.named, r.rule] for k, r in res.items()}))
        # a refused change of a stored graph leaves its versions as they were
        gm.save_graph(wf("S")); v0 = [v["version"] for v in gm.graph_versions("S")]; n1 = count()
        worse = wf("S"); worse["edges"].append({"id": "e9", "from": "out", "to": "in", "data": {}}); r = gm.save_graph(worse)
        check("NFR-16 a refused change of a stored graph leaves its versions and records as they were", not r.saved and [v["version"] for v in gm.graph_versions("S")] == v0 and n1 == count() and gm.read_graph("S") == wf("S"))
        # ---- interrupted move and sync, at every write
        src = Storage(be)
        mv_total = None
        for label, setup in (("one-graph move of a workflow graph with three versions", "wf"), ("one-graph move of a context graph with two versions", "cx")):
            gid = "MV" + setup; model = graph_model.GraphModel(src, author="mv")
            g1 = wf(gid, "a") if setup == "wf" else cx(gid, "a"); model.save_graph(g1)
            g2 = copy.deepcopy(g1); g2["nodes"][0]["data"].update({"value": "b"} if setup == "wf" else {"text": "b"}); model.save_graph(g2)
            if setup == "wf": g3 = copy.deepcopy(g2); g3["nodes"][1]["data"]["toolbox_id"] = "tool.c"; model.save_graph(g3)
            probe_t = tempfile.mkdtemp(); from storage_files import FileBackend
            pc = Counting(FileBackend(probe_t)); move.move_graph(be, pc, gid); total = pc.writes
            ok = fin = 0
            for k in range(1, total + 1):
                tgt = FileBackend(tempfile.mkdtemp()); tc = Counting(tgt, k)
                try: move.move_graph(be, tc, gid)
                except OSError: pass
                listed = tgt.ids("graphs")
                whole_t = (not listed) or (graph_model.GraphModel(Storage(tgt)).read_graph(gid, len(tgt.versions("graphs", gid))) == graph_model.GraphModel(src).read_graph(gid, len(tgt.versions("graphs", gid))))
                ok += bool(whole_t); move.move_graph(be, tgt, gid); fin += snapshot_equal(be, tgt, gid)
            check(f"NFR-16 {label}: interrupted after each of its {total} writes, the target lists the graph only when all its members are there, and the move run again finishes", ok == fin == total and total > 0, f"{ok}/{total}, {fin}/{total}")
        # sync with a differing graph on the copy: aside file, removal and move, interrupted at each write of the copy
        live = FileBackend(tempfile.mkdtemp()); model = graph_model.GraphModel(Storage(live), author="live"); a = wf("SY", "a"); model.save_graph(a); b = copy.deepcopy(a); b["nodes"][0]["data"]["value"] = "live"; model.save_graph(b)
        base = FileBackend(tempfile.mkdtemp()); move.move_graph(live, base, "SY")
        cm = graph_model.GraphModel(Storage(base), author="copy"); cb = copy.deepcopy(a); cb["nodes"][0]["data"]["value"] = "copy only"; cm.save_graph(cb)
        probe_c = Counting(FileBackend(tempfile.mkdtemp())); shutil.rmtree(probe_c.inner.root); shutil.copytree(base.root, probe_c.inner.root); sy.sync_store(live, probe_c, tempfile.mkdtemp()); total = probe_c.writes
        ok = fin = partial = 0
        for k in range(1, total + 1):
            work = FileBackend(tempfile.mkdtemp()); shutil.rmtree(work.root); shutil.copytree(base.root, work.root); aside = tempfile.mkdtemp()
            try: sy.sync_store(live, Counting(work, k), aside)
            except OSError: pass
            st_w = Storage(work); listed = "SY" in st_w.ids("graphs")
            lm = graph_model.GraphModel(Storage(live))
            states = [graph_model.GraphModel(Storage(base)).read_graph("SY")] + [lm.read_graph("SY", v["version"]) for v in lm.graph_versions("SY")]     # as before, or any complete version of the live history
            ok += bool((not listed) or whole(work, "SY", states))
            strict = (not listed) or whole(work, "SY", [states[0], states[-1]]); partial += (not strict)
            sy.sync_store(live, work, aside); fin += snapshot_equal(live, work, "SY")
        check(f"NFR-16 a sync that must set a differing graph aside, remove it and move it again: interrupted after each of its {total} writes, the copy lists the graph only as before or as a complete version of the live history (all members stored, readable), and the sync run again finishes", ok == fin == total and total > 0, f"{ok}/{total} whole, {fin}/{total} finished; at {partial} of {total} positions the copy held an earlier complete version of the live history, neither the old copy nor the final state (FINDING for the wording of NFR-16)")
    finally:
        stop()

def snapshot_equal(a, b, gid):
    return a.versions("graphs", gid) == b.versions("graphs", gid) and all(a.versions(t, i) == b.versions(t, i) for t in ("graph_nodes", "graph_edges", "context_nodes", "context_edges") for i in a.ids(t) if i.startswith(gid + "/"))

kind = sys.argv[1] if len(sys.argv) > 1 else "files"
run(kind)
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed (%s)" % (len(results), len(failed), kind))
sys.exit(1 if failed else 0)
