"""Graphs and stand-ins for the checks of G-V4.GRAPHAPI.RULES (test requirements TR-RULES-002, -003, -004, -006, -007).

- step(), data(), transform(), master(), connection(), graph(): small graphs in the stored form, written out in each check (TR-RULES-002).
- TEXT: the fixed sentence of each rule, word for word from IF-301 v4 (A-170, D-419).
- converted_skills(): the 15 skill graphs, built at test time from skills/*.md and library/ (TR-RULES-004); fails when fewer than 15 are built.
- old_document_as_graph(doc): a document of the five older rules in the stored form, as prototype round 04 did (cp17_check.to_graph, D-424).
- check_route(graph): the stand-in of the editor's check route of IF-104 v2: it answers with the rule report (D-416 (2)); a wiring check only (TR-RULES-007).
"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = HERE
while not os.path.exists(os.path.join(REPO, "storage.py")):
    REPO = os.path.dirname(REPO)

TEXT = {
    "step_identity": "a step has an empty name or a name used twice",
    "step_kind": "a step is not a data, processing or loop-controlling step",
    "connection_endpoints": "a connection leads to or from a step that does not exist",
    "duplicate_connection": "the same connection is there twice",
    "adjacency": "a connection joins two data steps or two steps that are not data",
    "single_writer": "a piece of data is written by more than one step",
    "stop_limit": "a session setting is wrong: a data step holds a stop or session setting, a step has more than one settings connection, "
                  "or a loop-controlling step has no valid stop limit",
    "cycle": "the steps run in a circle",
    "unknown_kind": "the program does not know this kind of graph",
    "kind_cannot_run": "a graph of this kind cannot run",
    "unsupplied_input": "an input of the step has no writer, no start value in the graph and no value given with the run",
}
WORKFLOW_RULES = ["step_identity", "step_kind", "connection_endpoints", "duplicate_connection", "adjacency", "single_writer", "stop_limit", "cycle"]
CONTEXT_RULES = ["step_identity", "connection_endpoints", "duplicate_connection"]
SKILL_COUNT = 15


def step(step_id, step_type, **fields):
    return {"id": step_id, "data": dict(type=step_type, **fields)}


def data(step_id, **fields):
    return step(step_id, "data", **fields)


def transform(step_id):
    return step(step_id, "transform", toolbox_id=step_id.lower())


def master(step_id, stop=None):
    fields = {"toolbox_id": step_id.lower()}
    if stop is not None:
        fields["stop"] = stop
    return step(step_id, "master", **fields)


def connection(conn_id, start, end, **fields):
    return {"id": conn_id, "from": start, "to": end, "data": dict(fields)}


def graph(nodes, edges, kind=None, graph_id="g"):
    """a graph in the stored form with the header fields the Workflow management keeps; `kind` None leaves the field out"""
    g = {"id": graph_id, "context_graph_id": "ctx", "testbench_id": "", "description": "a RULES check graph", "nodes": nodes, "edges": edges}
    if kind is not None:
        g["kind"] = kind
    return g


def item(rule, parts):
    """one item of a rule report, with its fixed sentence"""
    return {"rule": rule, "parts": list(parts), "text": TEXT[rule]}


def ac017():
    """the graph of AC-017: a cycle d1 -> t1 -> d1 and a second writer t2 -> d1"""
    return graph([data("d1"), transform("t1"), transform("t2")],
                 [connection("e1", "d1", "t1"), connection("e2", "t1", "d1"), connection("e3", "t2", "d1")])


def converted_skills():
    """[(skill file name, graph)] for every skill, built as the prototype's converted() does (TR-RULES-004)"""
    import sys
    sys.path.insert(0, REPO)
    import pipeline_graph
    from library import Library
    from skill_converter import _latest_nodes
    from skill_store import load_skill
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        nodes, lib, out = _latest_nodes("library/nodes"), Library("library"), []
        for path in sorted(glob.glob("skills/*.md")):
            skill = load_skill(path)
            found = pipeline_graph.convert({k: v for k, v in lib.resolve(skill["pipeline"], "pipeline").items() if not k.startswith("_")}, nodes, 300)
            out.append((os.path.basename(path), pipeline_graph.bind_skill(found["graph"], nodes, skill, None)))
    finally:
        os.chdir(cwd)
    if len(out) < SKILL_COUNT:
        raise AssertionError("only %d converted skill graphs, expected %d (TR-RULES-004)" % (len(out), SKILL_COUNT))
    return out


def converted_skill(name):
    return dict(converted_skills())[name]


def old_document_as_graph(document):
    """a document of the older rules (kind process|data, session, stop max_cycles) in the stored form: a session process becomes a master with
    max_cycles read as max_repetitions, another process a transform, connections numbered e1, e2, ... (prototype round 04, cp17_check.to_graph, D-424)"""
    nodes = []
    for n in document["nodes"]:
        kind = n.get("kind")
        if kind == "process":
            fields = {"type": "master" if n.get("session") else "transform"}
            if n.get("session"):
                stop = n.get("stop")
                fields["stop"] = {("max_repetitions" if k == "max_cycles" else k): v for k, v in stop.items()} if isinstance(stop, dict) else stop
        else:
            fields = {"type": kind}
        nodes.append({"id": n.get("id"), "data": fields})
    edges = [{"id": "e%d" % i, "from": e["from"], "to": e["to"], "data": {}} for i, e in enumerate(document["edges"], 1)]
    return {"nodes": nodes, "edges": edges}


def check_route(graph_to_check):
    """stand-in of the check route of IF-104 v2 (D-416 (2)): the route answers with the IF-301 v4 rule report of the working copy"""
    from graph_rule_set import rule_report
    return rule_report(graph_to_check)
