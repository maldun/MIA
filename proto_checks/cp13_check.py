"""PROTOTYPE CP13/CP14 checks (not protected tests): one stored truth for workflow graphs AND context graphs (FR-57), a step belongs to one graph, also across the two kinds (FR-60),
the measures HR-003 and HR-004 of the CORE high-level spec. Run: python proto_checks/cp13_check.py [files|postgres]"""
import copy, json, os, sys, tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [REPO, os.path.join(REPO, "tests")]
os.chdir(REPO)
import graph_model, graph_tables
from storage import Storage, StorageError
from proto_checks.cp1_check import backend, converted
from proto_checks.make_sample_store import add_code

results = []
def check(name, ok, note=""):
    results.append((name, bool(ok), note)); print(("PASS " if ok else "FAIL ") + name + (" - " + note if note else ""))

def ctx(gid, extra=None):
    """a context graph: its steps are categories (text), its connections relate them"""
    g = {"id": gid, "kind": "context", "context_graph_id": "", "testbench_id": "", "description": "context graph of cp13",
         "nodes": [{"id": "claim", "data": {"type": "claim", "text": "water boils at 100 C"}}, {"id": "source", "data": {"type": "source", "url": "local:book-1"}}, {"id": "step.write", "data": {"type": "note", "text": "ctx"}}],
         "edges": [{"id": "e1", "from": "source", "to": "claim", "data": {"relation": "supports"}}, {"id": "e2", "from": "claim", "to": "step.write", "data": {}}]}
    if extra: g.update(extra)
    return g

def run(kind):
    be, stop = backend(kind)
    try:
        st = Storage(be); m = graph_model.GraphModel(st, author="cp13")
        # ---- FR-57 for a context graph: saved, changed twice, read, listed
        c = ctx("ctx.one"); r1 = m.save_graph(c)
        c2 = copy.deepcopy(c); c2["nodes"][0]["data"]["text"] = "water boils at 100 C at sea level"; m2 = graph_model.GraphModel(st, author="second"); r2 = m2.save_graph(c2)
        c3 = copy.deepcopy(c2); c3["nodes"].append({"id": "extra", "data": {"type": "person", "name": "A"}}); c3["edges"].append({"id": "e3", "from": "extra", "to": "claim", "data": {}}); r3 = graph_model.GraphModel(st, author="third").save_graph(c3)
        versions = m.graph_versions("ctx.one")
        check("FR-57 a context graph is saved and changed twice: three versions, who and when, newest returned", [r1.saved, r2.saved, r3.saved] == [True] * 3 and [v["version"] for v in versions] == [1, 2, 3] and [v["author"] for v in versions] == ["cp13", "second", "third"] and all(v["time"] for v in versions) and m.read_graph("ctx.one") == {**c3})
        check("FR-57 no version of a context graph has disappeared: each is read as it was saved", m.read_graph("ctx.one", 1) == c and m.read_graph("ctx.one", 2) == c2, "")
        check("FR-57 the stored header says the kind and the context graph is listed with the workflow graphs", st.get("graphs", "ctx.one")["doc"]["data"]["kind"] == "context" and "ctx.one" in st.ids("graphs") and not any(i.startswith("ctx.one/") for i in st.ids("graph_nodes")))
        check("FR-57 the steps and connections of a context graph are in the context tables, scoped by the graph", sorted(st.ids("context_nodes")) == ["ctx.one/claim", "ctx.one/extra", "ctx.one/source", "ctx.one/step.write"] and sorted(st.ids("context_edges")) == ["ctx.one/e1", "ctx.one/e2", "ctx.one/e3"])
        check("FR-57 saving the same context graph again makes no new version", m.save_graph(c3).version == 3 and len(m.graph_versions("ctx.one")) == 3)
        # ---- FR-60 for a context graph, and across the two kinds
        h = m.step_history("ctx.one", "claim")
        check("FR-60 the history of a context step lists only its own changes (one change, two versions)", [x["version"] for x in h] == [1, 2], json.dumps(h))
        w = {"id": "wf.one", "context_graph_id": "ctx.one", "testbench_id": "tb", "description": "wf", "nodes": [{"id": "var.in", "data": {"type": "data", "value": "x"}}, {"id": "step.write", "data": {"type": "transform", "toolbox_id": "tool.a"}}, {"id": "var.out", "data": {"type": "data"}}],
             "edges": [{"id": "e1", "from": "var.in", "to": "step.write", "data": {}}, {"id": "e2", "from": "step.write", "to": "var.out", "data": {}}]}
        m.save_graph(w); before_ctx = {t: {i: st.history(t, i) for i in st.ids(t)} for t in ("context_nodes", "context_edges")}
        w2 = copy.deepcopy(w); w2["nodes"][1]["data"]["toolbox_id"] = "tool.b"; m.save_graph(w2)
        after_ctx = {t: {i: st.history(t, i) for i in st.ids(t)} for t in ("context_nodes", "context_edges")}
        check("FR-60 a step with the same local name `step.write` in a workflow graph and in a context graph: changing one leaves the other and its history untouched", before_ctx == after_ctx and [x["version"] for x in m.step_history("ctx.one", "step.write")] == [1] and [x["version"] for x in m.step_history("wf.one", "step.write")] == [1, 2])
        # ---- refusals write nothing
        n_before = {t: len(st.ids(t)) for t in ("context_nodes", "context_edges", "graphs")}
        bad = {"dup": {**ctx("ctx.bad1"), "nodes": ctx("x")["nodes"] + [{"id": "claim", "data": {"type": "claim"}}]},
               "missing end": {**ctx("ctx.bad2"), "edges": [{"id": "e1", "from": "claim", "to": "nowhere", "data": {}}]},
               "empty type": {**ctx("ctx.bad3"), "nodes": [{"id": "claim", "data": {"type": ""}}], "edges": []},
               "no type": {**ctx("ctx.bad4"), "nodes": [{"id": "claim", "data": {"text": "x"}}], "edges": []},
               "unknown kind": {**ctx("ctx.bad5"), "kind": "swarm"}}
        refused = {k: graph_model.GraphModel(st, author="x").save_graph(g) for k, g in bad.items()}
        check("NFR-16 refused context graphs (a step twice, a connection to a missing step, a step without a type, an unknown kind) write nothing", all(not r.saved for r in refused.values()) and n_before == {t: len(st.ids(t)) for t in ("context_nodes", "context_edges", "graphs")}, json.dumps({k: [r.named, r.rule, r.detail] for k, r in refused.items()}))
        try: st.put("context_nodes", "loose", {"id": "loose", "data": {"type": "claim"}}, "x"); loose = None
        except StorageError as e: loose = e.rule
        try: st.put("graphs", "ctx.mixed", {"id": "ctx.mixed", "data": {"kind": "context", "context_graph_id": "", "testbench_id": "", "description": "", "nodes": [{"id": "other.graph/claim", "version": 1}], "edges": []}}, "x"); mixed = None
        except StorageError as e: mixed = e.rule
        check("FR-60 the storage refuses a context step without a graph in its ID, and a header that names a step of another graph", loose == "unscoped_id" and mixed in ("unscoped_id", "unknown_member"), "%s %s" % (loose, mixed))
        # ---- FR-57 for workflow graphs of every kind of step, 15 converted + the loop graph
        for gr in converted(): m.save_graph(gr)
        add_code(be)
        gids = [i for i in st.ids("graphs") if i not in ("ctx.one", "wf.one")]
        ok = True
        for gid in gids:
            g1 = m.read_graph(gid); g2 = copy.deepcopy(g1)
            for n in g2["nodes"]:
                if n["data"]["type"] == "data": n["data"]["value"] = "v2"; break
            for who in ("a", "b"):
                g2["nodes"][0]["data"]["value"] = who
                graph_model.GraphModel(st, author=who).save_graph(g2) if g2["nodes"][0]["data"]["type"] == "data" else None
            vs = m.graph_versions(gid)
            ok &= [v["version"] for v in vs] == list(range(1, len(vs) + 1)) and all(v["author"] and v["time"] for v in vs)
        kinds = {n["data"]["type"] for gid in gids for n in m.read_graph(gid)["nodes"]}
        check("FR-57 graphs with data, processing and loop-controlling steps: versions run 1 to n with who and when, nothing missing (%d graphs)" % len(gids), ok and {"data", "transform", "master"} <= kinds, str(sorted(kinds)))
        return not [n for n, o, _ in results if not o]
    finally:
        stop()

kind = sys.argv[1] if len(sys.argv) > 1 else "files"
run(kind)
failed = [n for n, ok, _ in results if not ok]
print("\n%d checks, %d failed (%s)" % (len(results), len(failed), kind))
sys.exit(1 if failed else 0)
