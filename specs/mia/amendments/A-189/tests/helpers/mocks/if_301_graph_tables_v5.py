"""Mock of IF-301 v5, the loader of graphs (A-187, D-473, D-475; protected; changes by amendment together with the suite).
Complexity 1: `load` is a pure function of networkx and the stored form, so the mock and the real operation are the same function by contract (the suite
shows they agree). Everything of v4 comes from RuleSetV4Mock. networkx is imported inside `load`, so the module imports where it is not installed yet.

load(graph) -> networkx.MultiDiGraph (contract text: contracts/IF-301-graph-tables.md, section "What changes against v4"):
- node key: the step ID; attributes `data` (a deep copy; {} when the step's data is not a dict) and `position` (index in `nodes`)
- edge from `from` to `to`, key: the connection ID; attributes `data` (a deep copy, {} likewise) and `position` (index in `edges`)
- graph attributes: every field of the stored form but `nodes` and `edges`; `kind` = "workflow" when none is named
- a step is well-formed when it is a dict with a non-empty text ID that no earlier step has; a connection when it is a dict with a non-empty text ID that no
  earlier connection has and `from` and `to` name well-formed steps; the others are left out, nothing raises, a non-graph input gives an empty graph
"""
import copy

from if_301_graph_tables_v4 import RuleSetV4Mock, _text


def _id(item):
    value = item.get("id") if isinstance(item, dict) else None
    return value if isinstance(value, str) and value else None


def _data(item):
    data = item.get("data")
    return copy.deepcopy(data) if isinstance(data, dict) else {}


class LoaderV5Mock(RuleSetV4Mock):
    def _broken(self, graph):
        """v5 (A-189, D-483): rule 3 also names a connection whose ID is not a non-empty text, in the order of the connections; `load` leaves it out."""
        found = super()._broken(graph)
        nodes, edges = graph.get("nodes", []), graph.get("edges", [])
        if not isinstance(edges, list):
            return found
        steps, seen = set(), set()
        for n in nodes if isinstance(nodes, list) else []:
            sid = n.get("id") if isinstance(n, dict) else n
            if isinstance(n, dict) and isinstance(sid, str) and sid and sid not in seen:
                steps.add(sid)
            if isinstance(sid, str):
                seen.add(sid)

        def known(end):
            return isinstance(end, str) and end in steps
        found["connection_endpoints"] = [_text(e.get("id") if isinstance(e, dict) else e) for e in edges
                                         if not isinstance(e, dict) or _id(e) is None or not known(e.get("from")) or not known(e.get("to"))]
        return found

    def load(self, graph):
        import networkx
        loaded = networkx.MultiDiGraph()
        if not isinstance(graph, dict):
            return loaded
        loaded.graph.update({k: copy.deepcopy(v) for k, v in graph.items() if k not in ("nodes", "edges")})
        loaded.graph.setdefault("kind", "workflow")
        nodes, edges = graph.get("nodes"), graph.get("edges")
        for position, step in enumerate(nodes if isinstance(nodes, list) else []):
            step_id = _id(step)
            if step_id is not None and step_id not in loaded:
                loaded.add_node(step_id, data=_data(step), position=position)
        seen = set()
        for position, edge in enumerate(edges if isinstance(edges, list) else []):
            edge_id = _id(edge)
            if edge_id is None or edge_id in seen:
                continue
            seen.add(edge_id)
            start, end = edge.get("from"), edge.get("to")
            if isinstance(start, str) and isinstance(end, str) and start in loaded and end in loaded:
                loaded.add_edge(start, end, key=edge_id, data=_data(edge), position=position)
        return loaded
