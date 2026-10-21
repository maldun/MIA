"""
The context graph of a run (ui/REQUIREMENTS_CORE.md 13c, 13d, 4b): the events of a run replayed into a graph, and views of it that fit a context budget.

  G1  replay() is a pure function from the events of a run to a graph: no clock, no network, no model, the same events give the same graph. The graph is never stored on its own; it is
      rebuilt from the log (CG11)
  G2  the shape follows the Co-Simulation Process Graph (4b): data nodes (question, plan, subtask, query, source, page, passage, claim, draft sentence, open slot) are never
      connected to each other; every connection passes through a process instance (the event that used the inputs and produced the outputs), whose identity is (ID, IID) =
      (actor, seq). Relations such as "supports" are derived from process instances (the verification), which carry who judged, in which style and how sure
  G3  every item has the seq of the event that made it, so everything can be traced back (provenance())
  G4  a view contracts sets of nodes into auxiliary nodes without changing the graph (hierarchy graph, PG16): loss-free, recursive, sets of at least two nodes; render() shows the
      graph at the granularity that fits a budget, expanding the parts that matter most (open slots, conflicts, unverified claims) first
  G5  a broken log is reported (problems), never turned into a wrong graph silently: unknown references create a placeholder node and a problem
"""
import hashlib
import json

try:
    from . import events as ev
except ImportError:  # used as plain script / in tests
    import events as ev

DATA, PROCESS = "data", "process"


class Graph:
    def __init__(self, run=None):
        self.run = run
        self.nodes = {}
        self.edges = []
        self.problems = []
        self.meta = {"strategy": None, "templates": [], "stop": None, "checkpoints": [], "budget": [], "escalations": [], "feedback": [], "conflicts": [], "question": None}
        self._claim_verdicts = {}

    # --- building (used by replay) ---
    def add(self, id_, cls, type_, seq, **attrs):
        node = self.nodes.get(id_)
        if node is None:
            node = {"id": id_, "cls": cls, "type": type_, "ID": attrs.pop("ID", None), "IID": attrs.pop("IID", None), "seq": seq, "attrs": {}, "status": attrs.pop("status", None)}
            self.nodes[id_] = node
        node["attrs"].update({k: v for k, v in attrs.items() if v is not None})
        return node

    def link(self, src, dst, kind, seq):
        edge = {"src": src, "dst": dst, "kind": kind, "seq": seq}
        if edge not in self.edges:
            self.edges.append(edge)

    # --- reading ---
    def data(self, type_=None):
        return [n for n in self.nodes.values() if n["cls"] == DATA and (type_ is None or n["type"] == type_)]

    def processes(self, type_=None):
        return [n for n in self.nodes.values() if n["cls"] == PROCESS and (type_ is None or n["type"] == type_)]

    def neighbours(self, id_, kind=None, direction=None):
        out = []
        for e in self.edges:
            if kind and e["kind"] != kind:
                continue
            if e["src"] == id_ and direction in (None, "out"):
                out.append(e["dst"])
            elif e["dst"] == id_ and direction in (None, "in"):
                out.append(e["src"])
        return out

    def claim_status(self, claim_id):
        """unverified | supported | contradicted | conflicting | not_found | superseded, from the verification processes and the conflicts"""
        node = self.nodes.get(claim_id)
        if node is None:
            return None
        if node["attrs"].get("placeholder"):
            return "unknown"                                        # G5: something an event refers to that no event made
        if node["attrs"].get("superseded_by"):
            return "superseded"
        verdicts = {v["verdict"] for v in self._claim_verdicts.get(claim_id, [])}
        if node["attrs"].get("in_conflict") and not node["attrs"].get("conflict_resolved"):
            return "conflicting"
        if "supported" in verdicts and "contradicted" in verdicts:
            return "conflicting"
        if "contradicted" in verdicts:
            return "contradicted"
        if "supported" in verdicts:
            return "supported"
        if verdicts == {"not_found"}:
            return "not_found"
        return "unverified"

    def relations(self, kind):
        """derived relations 'supports' | 'contradicts' as (passage, claim, process seq, judge, confidence); G2: they come from the verification processes"""
        wanted = {"supports": "supported", "contradicts": "contradicted"}[kind]
        out = []
        for claim_id, verdicts in self._claim_verdicts.items():
            for v in verdicts:
                if v["verdict"] == wanted:
                    out.append((v.get("passage"), claim_id, v["seq"], v["judge"], v["confidence"]))
        return sorted(out, key=lambda r: r[2])

    def open_slots(self):
        return [n for n in self.data("slot") if n["status"] == "open"]

    def cost_by_actor(self):
        """calls, seconds and tokens per actor from the model_call events"""
        table = {}
        for p in self.processes("model_call"):
            row = table.setdefault(p["attrs"].get("actor") or "?", {"calls": 0, "seconds": 0.0, "tokens_in": 0, "tokens_out": 0, "invalid": 0})
            row["calls"] += 1
            row["seconds"] = round(row["seconds"] + (p["attrs"].get("seconds") or 0.0), 3)
            row["tokens_in"] += p["attrs"].get("tokens_in") or 0
            row["tokens_out"] += p["attrs"].get("tokens_out") or 0
            row["invalid"] += 0 if p["attrs"].get("valid", True) else 1
        return table

    def provenance(self, node_id):
        """how a node came about (G3): [(node id, the process that produced it, [the ids it used])], from the node back to the question, nearest first"""
        steps, seen, queue = [], set(), [node_id]
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            producers = [e["src"] for e in self.edges if e["dst"] == current and e["kind"] == "produced"]
            for proc in producers:
                used = [e["src"] for e in self.edges if e["dst"] == proc and e["kind"] == "used"]
                steps.append((current, proc, used))
                queue.extend(used)
        return steps

    def explain(self, node_id):
        """the provenance as lines of text: what the node is, then each step back"""
        node = self.nodes.get(node_id)
        if node is None:
            return ["unknown node %s" % node_id]
        lines = [_describe(self, node)]
        for current, proc, used in self.provenance(node_id):
            p = self.nodes[proc]
            who = p["attrs"].get("actor") or p["ID"] or "?"
            extra = ""
            if p["type"] == "claim_verified":
                extra = " [%s, %s, %s]" % (p["attrs"].get("verdict"), p["attrs"].get("style"), _judge_text(p))
            lines.append("  %s <- %s by %s (event %s, round %s)%s from %s" % (current, p["type"], who, p["IID"], p["attrs"].get("round"), extra, ", ".join(used) or "nothing"))
        return lines

    def validate(self):
        """the rules of the model (PG19): problems of the graph itself"""
        problems = list(self.problems)
        for e in self.edges:
            for end in (e["src"], e["dst"]):
                if end not in self.nodes:
                    problems.append("edge %s -> %s: node %s does not exist" % (e["src"], e["dst"], end))
            a, b = self.nodes.get(e["src"]), self.nodes.get(e["dst"])
            if a and b and a["cls"] == DATA and b["cls"] == DATA:
                problems.append("data node %s is connected to data node %s without a process between" % (e["src"], e["dst"]))
        identities = {}
        for n in self.nodes.values():
            if n["cls"] == DATA and n["IID"] is not None:
                problems.append("data node %s has an instance id" % n["id"])
            key = (n["ID"], n["IID"], n["cls"])
            if n["cls"] == PROCESS and key in identities:
                problems.append("process %s repeats the identity %s" % (n["id"], key[:2]))
            identities[key] = n["id"]
        return problems

    def summary(self):
        counts = {}
        for n in self.nodes.values():
            counts[n["type"]] = counts.get(n["type"], 0) + 1
        return {"nodes": len(self.nodes), "edges": len(self.edges), "by_type": counts,
                "claims": {s: sum(1 for c in self.data("claim") if self.claim_status(c["id"]) == s) for s in ("supported", "contradicted", "conflicting", "not_found", "unverified", "superseded")},
                "open_slots": len(self.open_slots()), "problems": len(self.validate())}


def _judge_text(proc):
    judge = proc["attrs"].get("judge") or {}
    conf = proc["attrs"].get("confidence")
    return "judge %s%s" % (judge.get("actor", "?"), "" if conf is None else ", confidence %.2f" % conf)


def _describe(graph, node):
    attrs = node["attrs"]
    text = attrs.get("text") or attrs.get("quote") or attrs.get("title") or attrs.get("goal") or attrs.get("target") or node["id"]
    status = graph.claim_status(node["id"]) if node["type"] == "claim" else node["status"]
    return "%s %s%s: %s" % (node["type"], node["id"].split(":", 1)[-1], " [%s]" % status if status else "", ev.excerpt(text, 120))


# --- replay -------------------------------------------------------------------------------------------------------------------------------

def _qid(text):
    return "query:" + hashlib.sha256(str(text).encode("utf-8", "replace")).hexdigest()[:12]


def replay(events, run=None):
    """the context graph of one run (G1). Events are read in the order of their seq; lifecycle events are ignored except run_start (the question)."""
    graph = Graph(run)
    for problem in ev.check_log(events):
        graph.problems.append("log: " + problem)
    procs = {}
    for event in sorted(events, key=lambda e: e.get("seq", 0)):
        seq = event.get("seq")
        if event.get("kind") == "run_start":
            question = (event.get("payload") or {}).get("question")
            if question:
                graph.meta["question"] = question
                graph.add("question", DATA, "question", seq, text=question)
            continue
        if event.get("kind") != "event":
            continue
        type_, payload = event.get("type"), event.get("payload") or {}
        proc_id = "proc:%s" % seq
        actor = event.get("actor") or event.get("node")
        proc = graph.add(proc_id, PROCESS, type_, seq, ID=actor or type_, IID=seq, actor=actor, round=event.get("round"), item=event.get("item"), subtask=payload.get("subtask"))
        procs[seq] = proc_id
        parent = event.get("parent")
        if parent in procs:
            graph.link(procs[parent], proc_id, "follows", seq)
        handler = _HANDLERS.get(type_)
        if handler is None:
            graph.problems.append("event %s: no handler for type %r" % (seq, type_))
            continue
        handler(graph, proc_id, seq, payload)
    _finish(graph)
    return graph


def _used(graph, proc, node_id, cls_type, seq, **attrs):
    """the process uses a node; a reference to something that was never made creates a placeholder and a problem (G5)"""
    if node_id not in graph.nodes:
        graph.problems.append("event %s refers to %s, which no earlier event made" % (seq, node_id))
        graph.add(node_id, DATA, cls_type, seq, status="unknown", placeholder=True, **attrs)
    graph.link(node_id, proc, "used", seq)


def _made(graph, proc, node_id, type_, seq, **attrs):
    graph.add(node_id, DATA, type_, seq, **attrs)
    graph.link(proc, node_id, "produced", seq)
    return graph.nodes[node_id]


def _subtask(graph, proc, subtask, seq):
    if subtask is None:
        return
    sid = "subtask:%s" % subtask
    if sid not in graph.nodes:
        graph.add(sid, DATA, "subtask", seq, status="implied")
    graph.link(sid, proc, "used", seq)


def _h_plan(graph, proc, seq, p):
    if "question" in graph.nodes:
        graph.link("question", proc, "used", seq)
    _made(graph, proc, "plan:%s" % seq, "plan", seq, origin=p.get("origin"), template=p.get("template"), checks=p.get("checks"), steps=p.get("subtasks"))
    for key, goal in (p.get("goals") or {}).items():
        node = _made(graph, proc, "subtask:%s" % key, "subtask", seq, goal=goal)
        node["status"] = "planned"


def _h_router(graph, proc, seq, p):
    graph.meta["strategy"] = p.get("strategy")
    graph.nodes[proc]["attrs"].update(strategy=p.get("strategy"), markers=p.get("markers"))


def _h_query(graph, proc, seq, p):
    _subtask(graph, proc, p.get("subtask"), seq)
    _made(graph, proc, _qid(p["query"]), "query", seq, text=p["query"], backend=p.get("backend"), purpose=p.get("purpose"), subtask=p.get("subtask"))


def _h_source_found(graph, proc, seq, p):
    if p.get("query"):
        qid = _qid(p["query"])
        if qid in graph.nodes:
            graph.link(qid, proc, "used", seq)
    node = _made(graph, proc, "source:%s" % p["ref"], "source", seq, title=p.get("title"), date=p.get("date"), source_class=p.get("source_class"), trust=p.get("trust"),
                 backend=p.get("backend"), rank=p.get("rank"))
    node["status"] = node["status"] or "found"


def _h_source_dropped(graph, proc, seq, p):
    sid = "source:%s" % p["ref"]
    _used(graph, proc, sid, "source", seq)
    graph.nodes[sid]["status"] = "dropped"
    graph.nodes[sid]["attrs"].update(drop_reason=p.get("reason"), drop_stage=p.get("stage"), drop_detail=p.get("detail"))
    graph.nodes[proc]["attrs"].update(reason=p.get("reason"), stage=p.get("stage"))


def _h_page(graph, proc, seq, p):
    sid = "source:%s" % p["ref"]
    _used(graph, proc, sid, "source", seq)
    _made(graph, proc, "page:%s" % p["hash"], "page", seq, bytes=p.get("bytes"), truncated=p.get("truncated"), status_code=p.get("status"), ref=p["ref"])
    if graph.nodes[sid]["status"] in (None, "found"):
        graph.nodes[sid]["status"] = "fetched"


def _h_passage(graph, proc, seq, p):
    sid = "source:%s" % p["source"]
    _used(graph, proc, sid, "source", seq)
    _subtask(graph, proc, p.get("subtask"), seq)
    node = _made(graph, proc, "passage:%s" % p["id"], "passage", seq, quote=p["quote"], start=p.get("start"), end=p.get("end"), subtask=p.get("subtask"), source=p["source"])
    node["status"] = "anchored" if p["anchor_ok"] else "unanchored"


def _h_claim(graph, proc, seq, p):
    for pid in p.get("passages") or []:
        _used(graph, proc, "passage:%s" % pid, "passage", seq)
    _subtask(graph, proc, p.get("subtask"), seq)
    _made(graph, proc, "claim:%s" % p["id"], "claim", seq, text=p["text"], subtask=p.get("subtask"), by=p.get("by"))


def _h_verified(graph, proc, seq, p):
    cid = "claim:%s" % p["claim"]
    _used(graph, proc, cid, "claim", seq)
    passage = None
    if p.get("passage"):
        passage = "passage:%s" % p["passage"]
        _used(graph, proc, passage, "passage", seq)
    graph.nodes[proc]["attrs"].update(verdict=p["verdict"], style=p.get("style"), judge=p.get("judge"), confidence=p.get("confidence"))
    graph._claim_verdicts.setdefault(cid, []).append({"verdict": p["verdict"], "passage": passage, "seq": seq, "judge": p.get("judge"), "confidence": p.get("confidence"), "style": p.get("style")})


def _h_conflict(graph, proc, seq, p):
    ids = ["claim:%s" % c for c in p["claims"]]
    for cid in ids:
        _used(graph, proc, cid, "claim", seq)
    winner = "claim:%s" % p["winner"] if p.get("winner") else None
    for cid in ids:
        node = graph.nodes[cid]
        node["attrs"]["in_conflict"] = True
        if p["resolution"] == "newer_source" and winner:
            if cid == winner:
                node["attrs"]["conflict_resolved"] = True
            else:
                node["attrs"]["superseded_by"] = winner
                node["attrs"]["conflict_resolved"] = True
    graph.nodes[proc]["attrs"].update(rule=p.get("rule"), resolution=p["resolution"], winner=winner)
    graph.meta["conflicts"].append({"seq": seq, "claims": ids, "rule": p.get("rule"), "resolution": p["resolution"], "winner": winner})


def _h_slot_opened(graph, proc, seq, p):
    _subtask(graph, proc, p.get("subtask"), seq)
    node = _made(graph, proc, "slot:%s" % p["subtask"], "slot", seq, target=p["target"], why=p.get("why"), subtask=p["subtask"])
    node["status"] = "open"


def _h_slot_closed(graph, proc, seq, p):
    sid = "slot:%s" % p["subtask"]
    _used(graph, proc, sid, "slot", seq)
    graph.nodes[sid]["status"] = "closed"
    if p.get("by_claim"):
        _used(graph, proc, "claim:%s" % p["by_claim"], "claim", seq)
        graph.nodes[sid]["attrs"]["closed_by"] = "claim:%s" % p["by_claim"]


def _h_draft(graph, proc, seq, p):
    for cid in p.get("claims") or []:
        _used(graph, proc, "claim:%s" % cid, "claim", seq)
    _made(graph, proc, "draft:" + ev.digest(p["text"])[2:], "draft", seq, text=p["text"])


def _h_check(graph, proc, seq, p):
    target = p.get("target")
    for prefix in ("passage", "claim", "source", "slot"):
        if target and "%s:%s" % (prefix, target) in graph.nodes:
            graph.link("%s:%s" % (prefix, target), proc, "used", seq)
            if p["result"] == "fail":
                graph.nodes["%s:%s" % (prefix, target)]["attrs"].setdefault("checks_failed", []).append(p["name"])
            break
    graph.nodes[proc]["attrs"].update(name=p["name"], result=p["result"], target=target)


def _h_template(graph, proc, seq, p):
    graph.meta["templates"].append({"template": p["template"], "version": p["version"], "class": p["problem_class"], "test_passed": p.get("test_passed"), "seq": seq})
    graph.nodes[proc]["attrs"].update(template=p["template"], version=p["version"])


def _h_escalation(graph, proc, seq, p):
    graph.meta["escalations"].append({"from": p["from"], "to": p["to"], "trigger": p["trigger"], "seq": seq})
    graph.nodes[proc]["attrs"].update(**{"from": p["from"], "to": p["to"], "trigger": p["trigger"]})


def _h_budget(graph, proc, seq, p):
    graph.meta["budget"].append({"name": p["name"], "used": p["used"], "limit": p["limit"], "seq": seq})
    graph.nodes[proc]["attrs"].update(name=p["name"], used=p["used"], limit=p["limit"])


def _h_checkpoint(graph, proc, seq, p):
    graph.meta["checkpoints"].append({"sources_checked": p["sources_checked"], "decision": p["decision"], "seq": seq})
    graph.nodes[proc]["attrs"].update(sources_checked=p["sources_checked"], decision=p["decision"])


def _h_stop(graph, proc, seq, p):
    graph.meta["stop"] = {"reason": p["reason"], "limit": p.get("limit"), "detail": p.get("detail"), "seq": seq}
    graph.nodes[proc]["attrs"].update(reason=p["reason"], limit=p.get("limit"))


def _h_model_call(graph, proc, seq, p):
    graph.nodes[proc]["attrs"].update(model=p.get("model"), digest=p.get("digest"), seconds=p.get("seconds"), tokens_in=p.get("tokens_in"), tokens_out=p.get("tokens_out"),
                                      valid=p.get("valid"), attempt=p.get("attempt"), prompt_hash=p.get("prompt_hash"), response_hash=p.get("response_hash"), schema=p.get("schema"))


def _h_feedback(graph, proc, seq, p):
    graph.meta["feedback"].append({"kind": p["kind"], "value": p.get("value"), "claim": p.get("claim"), "seq": seq})
    if p.get("claim"):
        _used(graph, proc, "claim:%s" % p["claim"], "claim", seq)
    graph.nodes[proc]["attrs"].update(kind=p["kind"], value=p.get("value"))


def _h_log_error(graph, proc, seq, p):
    graph.problems.append("event %s was refused when it was written: %s (%s)" % (seq, p.get("problem"), p.get("original_type")))


_HANDLERS = {"plan_made": _h_plan, "router_decision": _h_router, "query_issued": _h_query, "source_found": _h_source_found, "source_dropped": _h_source_dropped,
             "page_fetched": _h_page, "passage_extracted": _h_passage, "claim_made": _h_claim, "claim_verified": _h_verified, "conflict_found": _h_conflict,
             "slot_opened": _h_slot_opened, "slot_closed": _h_slot_closed, "draft_sentence": _h_draft, "check_run": _h_check, "template_used": _h_template,
             "escalation": _h_escalation, "budget_spent": _h_budget, "checkpoint": _h_checkpoint, "stop_decision": _h_stop, "model_call": _h_model_call,
             "user_feedback": _h_feedback, "log_error": _h_log_error}


def _finish(graph):
    for cid in [n["id"] for n in graph.data("claim")]:
        graph.nodes[cid]["status"] = graph.claim_status(cid)


def replay_run(record):
    """the graph of a run record of run_log.RunLog.read()"""
    return replay(record.get("events") or [], run=record.get("id"))


# --- views: levels of granularity (G4, PG16) -------------------------------------------------------------------------------------------------

class View:
    """an overlay on a graph: groups of nodes contracted into auxiliary nodes. The graph is not changed; a group has at least two members; groups can be inside groups;
    expand() undoes a contraction; only the last state of the view needs to be kept."""

    def __init__(self, graph):
        self.graph = graph
        self.groups = {}                    # id -> {"name", "members": [ids]}
        self.parent = {}                    # member id -> group id
        self._counter = 0

    def contract(self, name, members):
        members = [m for m in dict.fromkeys(members) if m in self.graph.nodes or m in self.groups]
        if len(members) < 2:
            raise ValueError("a group needs at least two members")
        for m in members:
            if m in self.parent:
                raise ValueError("%s is already inside %s; contract that group instead" % (m, self.parent[m]))
        self._counter += 1
        gid = "group:%d" % self._counter
        self.groups[gid] = {"name": name, "members": members}
        for m in members:
            self.parent[m] = gid
        return gid

    def expand(self, gid):
        group = self.groups.pop(gid)
        outer = self.parent.pop(gid, None)
        for m in group["members"]:
            if outer:
                self.parent[m] = outer
            else:
                self.parent.pop(m, None)
        if outer:
            members = self.groups[outer]["members"]
            self.groups[outer]["members"] = [x for x in members if x != gid] + group["members"]

    def top(self):
        """the visible nodes and groups: those inside no group"""
        ids = [i for i in list(self.groups) + list(self.graph.nodes) if i not in self.parent]          # groups first: they are the overview
        return ids

    def leaves(self, gid):
        out = []
        for m in self.groups[gid]["members"]:
            out.extend(self.leaves(m) if m in self.groups else [m])
        return out

    def quotient_edges(self):
        """the edges between the visible nodes and groups (loss-free: the members are in groups)"""
        def visible(i):
            while i in self.parent:
                i = self.parent[i]
            return i
        edges = []
        for e in self.graph.edges:
            a, b = visible(e["src"]), visible(e["dst"])
            if a != b and (a, b, e["kind"]) not in edges:
                edges.append((a, b, e["kind"]))
        return edges


def default_view(graph):
    """one group per subtask (its nodes and processes), one for the dropped sources, one for the model calls; groups of at least two nodes"""
    view = View(graph)
    by_subtask = {}
    for node in graph.nodes.values():
        sub = node["attrs"].get("subtask")
        if sub is not None and node["type"] != "subtask":
            by_subtask.setdefault(str(sub), []).append(node["id"])
    for sub, ids in sorted(by_subtask.items()):
        sid = "subtask:%s" % sub
        members = ([sid] if sid in graph.nodes else []) + ids
        if len(members) >= 2:
            view.contract("subtask %s" % sub, members)
    dropped = [n["id"] for n in graph.data("source") if n["status"] == "dropped" and n["id"] not in view.parent]
    if len(dropped) >= 2:
        view.contract("dropped sources", dropped)
    calls = [n["id"] for n in graph.processes("model_call") if n["id"] not in view.parent]
    if len(calls) >= 2:
        view.contract("model calls", calls)
    return view


def _line(graph, node):
    attrs = node["attrs"]
    if node["cls"] == PROCESS:
        extra = {"claim_verified": " %s (%s)" % (attrs.get("verdict"), _judge_text(node)), "model_call": " %.1fs" % (attrs.get("seconds") or 0.0)}.get(node["type"], "")
        return "- %s by %s%s" % (node["type"], node["ID"], extra)
    return "- " + _describe(graph, node)


def _weight(graph, ids):
    """how much a group needs attention: open slots and conflicts count most, then unverified claims"""
    score = 0
    for i in ids:
        node = graph.nodes.get(i)
        if not node:
            continue
        if node["type"] == "slot" and node["status"] == "open":
            score += 5
        elif node["type"] == "claim":
            status = graph.claim_status(i)
            score += {"conflicting": 5, "contradicted": 4, "unverified": 2, "not_found": 2}.get(status, 0)
        elif node["type"] == "passage" and node["status"] == "unanchored":
            score += 1
    return score


def render(view, budget_tokens=800, focus=None):
    """the view as text within about budget_tokens (4 characters a token): the groups that need attention most are expanded first (PG16, CG3); focus: a group id, or the name of a
    group, that is expanded first. Returns (text, expanded group ids)"""
    graph, limit = view.graph, budget_tokens * 4
    expanded = []

    def lines_of(i, depth):
        pad = "  " * depth
        if i in view.groups:
            g = view.groups[i]
            leaves = view.leaves(i)
            kinds = {}
            for leaf in leaves:
                n = graph.nodes[leaf]
                if n["cls"] == DATA:
                    kinds[n["type"]] = kinds.get(n["type"], 0) + 1
            head = "%s[%s] %s: %s" % (pad, "-" if i in expanded else "+", g["name"], ", ".join("%d %s" % (c, t) for t, c in sorted(kinds.items())) or "%d nodes" % len(leaves))
            open_n = sum(1 for leaf in leaves if graph.nodes[leaf]["type"] == "slot" and graph.nodes[leaf]["status"] == "open")
            if open_n:
                head += " (%d open)" % open_n
            if i not in expanded:
                return [head]
            body = []
            for m in g["members"]:
                body.extend(lines_of(m, depth + 1))
            return [head] + body
        return [pad + _line(graph, graph.nodes[i])]

    def text():
        out = []
        if graph.meta.get("question"):
            out.append("Question: " + graph.meta["question"])
        for i in view.top():
            if i == "question":
                continue
            out.extend(lines_of(i, 0))
        return "\n".join(out)

    def collapsed():
        return [g for g in view.groups if g not in expanded and _visible_group(view, g, expanded)]

    if focus:
        target = focus if focus in view.groups else next((g for g, v in view.groups.items() if v["name"] == focus), None)
        if target:
            expanded.append(target)
    while True:
        candidates = sorted(collapsed(), key=lambda g: (-_weight(graph, view.leaves(g)), g))
        if not candidates:
            break
        expanded.append(candidates[0])                       # strictly best first: a less important group never takes the room of the most important one
        if len(text()) > limit:
            expanded.pop()
            break
    result = text()
    while len(result) > limit and expanded:                  # the focus alone may be too big: shrink from the last expanded
        expanded.pop()
        result = text()
    if len(result) > limit:                                  # even the collapsed view is too big: cut it and say so
        kept, total = [], 0
        lines = result.split("\n")
        for line in lines:
            if total + len(line) + 1 > max(limit - 40, 0):
                break
            kept.append(line)
            total += len(line) + 1
        result = "\n".join(kept + ["… (%d more lines)" % (len(lines) - len(kept))])
        result = result[:limit] if len(result) > limit else result
    return result, list(expanded)


def _visible_group(view, gid, expanded):
    """a group can be expanded when it is on the top level or inside an expanded group"""
    parent = view.parent.get(gid)
    return parent is None or parent in expanded
