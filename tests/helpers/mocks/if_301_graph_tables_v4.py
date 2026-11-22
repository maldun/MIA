"""Mock of IF-301 v4, the rule set of graphs (A-170, D-417, D-419; protected; changes by amendment together with the suite).
Complexity 1: a registry of two kinds and pure functions, nothing is stored. It does not import product code, so a consumer testing against it
(the save path of N-2.3, the runner of N-2.4.1, later EDIT and CONTEXT) sees the contract, not the implementation.

Operations (contract text: contracts/IF-301-graph-tables.md, section "What changes against v3"):
- kinds() -> {kind: {"rules": [...], "runs": bool}}, a copy
- rule_report(graph) -> [{"rule", "parts", "text"}], every broken rule of the graph's kind in the registry's order; [] when sound
- run_check(graph, given=None) -> {"status": "refused" | "ready", "broken": [{"kind", "rule", "parts", "text"} ...]}
Interpretations this mock fixes where the contract text is short: a connection ID that is not text is named by str(); the parts of rule 7 come in three
passes (loop-controlling steps, then data steps, then settings targets in the order their first settings connection appears); the cycle is the first one a
depth-first walk finds, steps in their listed order and connections in theirs, as `validate` of the document form does.
"""
import copy
import math

KINDS = {
    "workflow": {"rules": ["step_identity", "step_kind", "connection_endpoints", "duplicate_connection", "adjacency", "single_writer", "stop_limit", "cycle"],
                 "runs": True},
    "context": {"rules": ["step_identity", "connection_endpoints", "duplicate_connection"], "runs": False},
}
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
STEP_TYPES = ("data", "transform", "master")


def _text(value):
    return value if isinstance(value, str) else str(value)


def _data(item):
    data = item.get("data") if isinstance(item, dict) else None
    return data if isinstance(data, dict) else {}


def _type(step):
    return _data(step).get("type")


def _limit(value, whole):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if whole:
        return value >= 1 and (isinstance(value, int) or value.is_integer())
    return value > 0 and (isinstance(value, int) or math.isfinite(value))


def _stop_is_valid(stop):
    if not isinstance(stop, dict) or not ({"max_repetitions", "max_seconds"} & stop.keys()):
        return False
    return ("max_repetitions" not in stop or _limit(stop["max_repetitions"], True)) and ("max_seconds" not in stop or _limit(stop["max_seconds"], False))


def _find_cycle(ids, edges):
    following = {i: [] for i in ids}
    for e in edges:
        following[e["from"]].append(e["to"])
    state, path = {}, []
    for root in ids:
        if root in state:
            continue
        state[root] = 1
        path.append(root)
        walk = [iter(following[root])]
        while walk:
            for nxt in walk[-1]:
                if state.get(nxt) == 1:
                    return path[path.index(nxt):] + [nxt]
                if nxt not in state:
                    state[nxt] = 1
                    path.append(nxt)
                    walk.append(iter(following[nxt]))
                    break
            else:
                state[path.pop()] = 2
                walk.pop()
    return None


class RuleSetV4Mock:
    """The provider of IF-301 v4 as the suite sees it."""

    def kinds(self):
        return copy.deepcopy(KINDS)

    def _kind(self, graph):
        if "kind" not in graph:
            return "workflow"
        kind = graph["kind"]
        return kind if isinstance(kind, str) and kind in KINDS else None

    def rule_report(self, graph):
        if not isinstance(graph, dict):
            return [{"rule": "step_identity", "parts": ["graph"], "text": TEXT["step_identity"]}]
        kind = self._kind(graph)
        if kind is None:
            return [{"rule": "unknown_kind", "parts": [_text(graph.get("kind"))], "text": TEXT["unknown_kind"]}]
        found = self._broken(graph)
        report = []
        for rule in KINDS[kind]["rules"]:
            if rule == "cycle" and (found["step_identity"] or found["connection_endpoints"]):
                continue
            parts = found[rule]
            if parts:
                report.append({"rule": rule, "parts": parts if rule == "cycle" else list(dict.fromkeys(parts)), "text": TEXT[rule]})
        return report

    def _broken(self, graph):
        nodes, edges = graph.get("nodes", []), graph.get("edges", [])
        found = {rule: [] for rule in KINDS["workflow"]["rules"]}
        if not isinstance(nodes, list):
            found["step_identity"].append("nodes")
            nodes = []
        if not isinstance(edges, list):
            found["connection_endpoints"].append("edges")
            edges = []
        seen, steps = set(), []
        for n in nodes:
            sid = n.get("id") if isinstance(n, dict) else n
            if not isinstance(n, dict) or not isinstance(sid, str) or not sid or sid in seen:
                found["step_identity"].append(_text(sid))
            if isinstance(n, dict) and isinstance(sid, str) and sid and sid not in seen:
                steps.append(n)
            if isinstance(sid, str):
                seen.add(sid)
        types = {n["id"]: _type(n) for n in steps}
        found["step_kind"] = [n["id"] for n in steps if _type(n) not in STEP_TYPES]
        valid = []
        seen_ids, seen_keys = set(), set()
        for e in edges:
            if not isinstance(e, dict) or not isinstance(e.get("from"), str) or not isinstance(e.get("to"), str) \
                    or e["from"] not in types or e["to"] not in types:
                found["connection_endpoints"].append(_text(e.get("id") if isinstance(e, dict) else e))
                if not isinstance(e, dict):
                    continue
            key = (e.get("from"), e.get("to"), _data(e).get("role"), _data(e).get("as"))
            if key in seen_keys or e.get("id") in seen_ids:
                found["duplicate_connection"].append(_text(e.get("id")))
            seen_keys.add(key)
            seen_ids.add(e.get("id"))
            if e.get("from") in types and e.get("to") in types:
                valid.append(e)
        found["adjacency"] = [_text(e.get("id")) for e in valid if (types[e["from"]] == "data") == (types[e["to"]] == "data")]
        writers = {}
        for e in valid:
            if types[e["to"]] == "data":
                writers.setdefault(e["to"], set()).add(e["from"])
        found["single_writer"] = [d for d, w in writers.items() if len(w) > 1]
        settings = {}
        for e in edges:
            if isinstance(e, dict) and _data(e).get("role") == "settings":
                settings.setdefault(e.get("to"), []).append(e.get("id"))
        found["stop_limit"] = ([n["id"] for n in steps if _type(n) == "master" and not _stop_is_valid(_data(n).get("stop"))]
                               + [n["id"] for n in steps if _type(n) == "data" and ({"stop", "session"} & set(_data(n)))]
                               + [_text(t) for t, ids in settings.items() if len(ids) > 1])
        found["cycle"] = _find_cycle([n["id"] for n in steps], valid) or []
        return found

    def run_check(self, graph, given=None):
        if isinstance(graph, dict):
            kind = self._kind(graph)
            if kind is None or not KINDS[kind]["runs"]:
                rule = "unknown_kind" if kind is None else "kind_cannot_run"
                return {"status": "refused", "broken": [{"kind": "kind", "rule": rule, "parts": [_text(graph.get("kind"))], "text": TEXT[rule]}]}
        broken = [dict({"kind": "rule"}, **r) for r in self.rule_report(graph)]
        if isinstance(graph, dict):
            broken += self._unsupplied(graph, set(given or ()))
        return {"status": "refused" if broken else "ready", "broken": broken}

    def _unsupplied(self, graph, given):
        nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
        edges = graph.get("edges") if isinstance(graph.get("edges"), list) else []
        steps = {n["id"]: n for n in nodes if isinstance(n, dict) and isinstance(n.get("id"), str) and n["id"]}
        valid = [e for e in edges if isinstance(e, dict) and e.get("from") in steps and e.get("to") in steps]
        written = {e["to"] for e in valid}
        found = []
        for e in valid:
            if _type(steps[e["to"]]) not in ("transform", "master") or _type(steps[e["from"]]) != "data":
                continue
            if _data(e).get("role") in ("settings", "order"):
                continue
            source = e["from"]
            if source not in written and _data(steps[source]).get("value") is None and source not in given:
                found.append({"kind": "input", "rule": "unsupplied_input", "step": e["to"], "input": source, "parts": [source],
                              "text": TEXT["unsupplied_input"]})
        return found
